# Data Readiness Desk: Under-the-Hood Architecture

This document details the low-level technical mechanics, API flows, data engineering pipelines, and security configurations that run the **Data Readiness Desk** application natively on the Databricks Serverless platform.

---

## 1. Application Bootstrapping & Client Authentication

The application is deployed as a native Databricks App (harnessing containerized serverless compute) and utilizes the Python-native Streamlit framework.

### WorkspaceClient Initialization
Inside the Databricks App runtime container, Databricks automatically injects environment variables containing secure OAuth 2.0 credentials for a dedicated Service Principal created for the app.
When `WorkspaceClient()` is instantiated in `get_workspace_client()`, the SDK reads these variables to automatically authenticate against the workspace without requiring any hardcoded API tokens:

```python
# From src/app.py
@st.cache_resource
def get_workspace_client() -> Optional[WorkspaceClient]:
    try:
        return WorkspaceClient()  # Auto-resolves OAuth SP credentials
    except Exception as e:
        ...
```

### Programmatic SQL Warehouse Discovery
Instead of hardcoding a SQL Warehouse ID (which is brittle and varies across environments), the app dynamically scans the workspace's endpoints on boot. It calls `w.warehouses.list()` and captures the first endpoint in an active (`RUNNING` or `STARTING`) or idle (`STOPPED`) state.
*On Databricks Free Edition, this resolves to the single, cost-managed `Serverless Starter Warehouse` of size 2X-Small.*

```python
# From src/app.py
for wh in w.warehouses.list():
    if wh.state.name in ["RUNNING", "STARTING", "STOPPED"]:
        return wh.id
```

---

## 2. Self-Initializing Data Pipeline (Delta Engine)

To guarantee zero setup overhead, the app automatically deploys and runs its own Delta Lake pipeline if it detects that the target tables are missing in Unity Catalog.

```
       [ App Boot ]
            │
            ▼
 [ Query Schema Catalog ] ──(Exists?)──> [ YES ] ──> Load Data
            │                                            ▲
         [ NO ]                                          │
            │                                            │
            ▼                                            │
   [ Execute Pipeline ] ─────────────────────────────────┘
 (CREATE TABLE AS SELECT ...)
```

### Schema Discovery
The app checks if the gold validated table exists by running a metadata search query against the read-only catalog schema:
```sql
SELECT 1 
FROM workspace.information_schema.tables 
WHERE table_schema='default' AND table_name='gold_flagged_facilities' 
LIMIT 1
```

### The ELT Compilation Query
If the table is missing, the app triggers a large-scale `CREATE TABLE AS SELECT` (CTAS) query. It reads 10,088 raw rows from the Delta Sharing catalog and processes them in parallel across serverless SQL nodes:

*   **Rule 1 (ICU Beds Missing)**: Identifies facilities claiming intensive care but listing null capacity.
*   **Rule 2 (Emergency Doctor Deficit)**: Flags trauma centers listing zero active doctor counts.
*   **Rule 3 (Surgical Support Deficit)**: Flags surgical claims that completely omit anesthesiologist or ventilation equipment.
*   **Rule 4 (Data Desert Alert)**: Flags facilities devoid of structured core fields.
*   **Weighted Scoring**: Merges these boolean results into a `trust_score` (100 base score with weighted deductions).

---

## 3. Synchronous Query Execution & Polling

Because standard SQL queries (especially CTAS statements) run asynchronously over the Databricks SQL REST API, the application employs a **synchronous polling loop** to prevent race conditions.

If the app executed `CREATE TABLE` and immediately sent `SELECT *`, the `SELECT` would execute while table creation was still in a `RUNNING` state, resulting in a fatal `TABLE_OR_VIEW_NOT_FOUND` error.

### The Polling Loop Mechanics
When `run_sql_statement()` is called, it issues the query, retrieves a unique `statement_id`, and blocks Python execution. It polls the Databricks Statement Execution API every **1 second**, checking the execution state:

```python
# From src/app.py
statement_id = response.statement_id
state = response.status.state.name

while state in ["PENDING", "RUNNING"]:
    time.sleep(1)
    status_resp = w.statement_execution.get_statement(statement_id=statement_id)
    state = status_resp.status.state.name
    if state == "SUCCEEDED":
        return status_resp
```

This ensures absolute data and schema readiness before the Streamlit frontend attempts to load or render the records.

---

## 4. Strict Schema Type Enforcement

Because the raw shared dataset is unstructured and contains inconsistent null representations (e.g., empty strings, `None` objects, and raw text representations of numeric metrics), the application enforces a strict, type-safe schema on load.

Before feeding the resulting pandas DataFrame (`df_raw`) into Plotly charts or Streamlit tables, the `load_gold_data()` function executes explicit PEP-aligned casting:

```python
# From src/app.py
# Enforce string typings
df['unique_id'] = df['unique_id'].astype(str)
df['name'] = df['name'].fillna("Unknown").astype(str)

# Cast text values to safe, numeric types
df['numberDoctors'] = pd.to_numeric(df['numberDoctors'], errors='coerce').fillna(0).astype(int)
df['capacity'] = pd.to_numeric(df['capacity'], errors='coerce').fillna(0).astype(int)

# Cast flags to strict binary integers
df['flag_icu_no_capacity'] = pd.to_numeric(df['flag_icu_no_capacity'], errors='coerce').fillna(0).astype(int)
df['trust_score'] = pd.to_numeric(df['trust_score'], errors='coerce').fillna(100).astype(int)
```

**Why this is crucial**: If a column has mixed float, string, and NaN values, Plotly's rendering engine and Streamlit's data table components will crash due to serialization exceptions. Casting to strict types guarantees absolute UI stability during live demos.

---

## 5. Human-in-the-Loop ACID Writebacks

The "Decision Desk" feature allows reviewers to audit, approve, or flag records and persist notes directly back to the database.

```
 [ Reviewer Clicks Approve ]
              │
              ▼
   [ Escape User Input ]  ──> Replace single quotes with double single quotes (SQL injection shield).
              │
              ▼
   [ Execute SQL UPDATE ] ──> UPDATE workspace.default.gold_flagged_facilities SET review_status='APPROVED' ...
              │
              ▼
   [ Evict Memory Cache ] ──> st.cache_data.clear()
              │
              ▼
   [ Trigger Page Rerun ] ──> st.rerun() ──> UI pulls fresh clean state from Delta Lake.
```

### ACID-Compliant Writebacks
When a user clicks "Approve" or "Flag", the app executes a direct SQL `UPDATE` statement on the Delta table. Because Delta Lake supports full ACID transactions, the table is locked, updated, and committed safely, guaranteeing that no state is lost.

### String Escaping (SQL Injection Protection)
Because notes are inputted as free text, the app escapes single quotes to prevent syntax compilation breaks and malicious SQL injections:
```python
escaped_notes = reviewer_notes.replace("'", "''")
```

### Cache Eviction and Rerun
To keep performance lightning-fast, the main dataset is cached in memory using `@st.cache_data`. When a writeback succeeds, we evict this memory cache via `st.cache_data.clear()` and trigger a browser page refresh with `st.rerun()`. This forces the app to pull the newly committed state from Delta Lake.

---

## 6. Security & Privilege Architecture

The app's permissions are tightly scoped to satisfy Databricks' administrative security guidelines. It operates as a restricted system Service Principal (`edc29524-5306-48d2-9403-edfd461ab62f`) and holds only the precise privileges needed for its pipelines:

1.  **`USE CATALOG` on Catalog `databricks_virtue_foundation_dataset_dais_2026`**: Grants the principal metadata exposure to the shared catalog.
2.  **`USE SCHEMA` & `SELECT` on Schema `databricks_virtue_foundation_dataset_dais_2026.virtue_foundation_dataset`**: Grants metadata and read-only access to query the 10,088 raw records.
3.  **`USE CATALOG` on Catalog `workspace`**: Allows the principal to target the workspace-managed space.
4.  **`USE SCHEMA`, `CREATE TABLE`, `SELECT`, `MODIFY` on Schema `workspace.default`**: Grants full rights to initialize, read, and writeback audit overrides on the target Gold Delta table.
