# Enterprise Productionization Blueprint: Data Readiness Desk

This document serves as the strategic architectural roadmap to transition the **Data Readiness Desk** from a hackathon prototype on Databricks Free Edition into an enterprise-grade, high-volume production platform on AWS or Azure Databricks Premium/Enterprise.

---

## 1. High-Volume Ingestion & Orchestration (Bronze to Silver)

In a production scenario, data does not arrive as a static 10k table. Healthcare facilities continuously submit logs, spreadsheets, and web updates to cloud object storage (S3 / ADLS).

```
 [ Dirty CSV/JSON Stream ] ──> [ S3 Bucket / Raw Ingest ]
                                        │
                                        ▼
                             [ Databricks Auto Loader ] ──> Schema Inference & Evolution
                                        │
                                        ▼
                             [ Delta Live Tables (DLT) ] ──> Managed Silver Delta Lake
```

### The Ingestion Pipeline
1.  **Databricks Auto Loader**: Use Auto Loader (`cloudFiles` format) inside a PySpark stream to continuously discover and ingest incoming CSV/JSON records from S3. Auto Loader handles schema inference, schema evolution, and bad-record rescue automatically.
2.  **Delta Live Tables (DLT)**: Build the Bronze-to-Silver stream inside a DLT pipeline. DLT automatically manages table dependencies, performance tuning, and infrastructure scale-up/down.

---

## 2. Enterprise Data Quality Guardrails (DLT Expectations)

Our current gold validation pipeline uses basic SQL query conditions inside Streamlit. For production, we must decouple data quality rules from the application layer and enforce them natively at the database engine level.

### Delta Live Tables Expectations
We can replace our hardcoded SQL checks with native **DLT Expectations**. This allows us to declare data quality constraints and dictate what happens to records when they violate those rules:

```python
import dlt

@dlt.table(
    name="silver_clean_facilities",
    comment="Cleaned facility records with enforced schema expectations"
)
@dlt.expect_or_drop("valid_doctor_count", "CAST(numberDoctors AS INT) >= 0 OR numberDoctors IS NULL")
@dlt.expect_or_fail("has_unique_id", "unique_id IS NOT NULL")
def silver_clean_facilities():
    return dlt.read_stream("bronze_raw_facilities")
```

### Advanced Contradiction Triage (Gold Expectation Rules)
For contradiction routing, we can declare **quarantine rules** that tag records for the human-in-the-loop audit desk without blocking clean data from proceeding:

```python
@dlt.table(
    name="gold_triage_queue"
)
def gold_triage_queue():
    return dlt.read("silver_clean_facilities").select(
        "*",
        # Compute contradiction flags natively in DLT
        ((dlt.col("capability").like("%ICU%") & (dlt.col("capacity") <= 0))).alias("flag_icu_no_capacity")
    )
```

---

## 3. Scaled AI Auditing (Serverless Batch Inference)

Instead of on-demand UI queries, we can scale our semantic LLM contradiction checks to run in high-volume batches over millions of rows during off-peak hours.

### PySpark LLM Batch Processing
Using Databricks SQL native `ai_query()` or PySpark pandas UDFs calling Databricks Foundation Model APIs (e.g., Llama 3 70B), we can execute parallel semantic audits at scale:

```sql
CREATE OR REPLACE TABLE workspace.default.gold_triage_queue_ai AS
SELECT
  *,
  -- Call serverless LLM to audit free-text description vs stated capability
  ai_query(
    'databricks-meta-llama-3-1-70b-instruct',
    CONCAT(
      'Audit this facility description: "', description, 
      '" against stated capabilities: "', capability, 
      '". Is there a logical contradiction? Respond only with "YES" or "NO" and a 1-sentence reason.'
    )
  ) as ai_audit_response
FROM workspace.default.gold_triage_queue
WHERE trust_score < 80 -- Target compute budget only on high-risk records
```

### MLflow 3 Tracing and Cost Guardrails
To prevent runaway AI expenses, we configure **MLflow 3 Tracing** to track the latency, token inputs, token outputs, and estimated costs of every serverless LLM execution:
*   Set maximum token budget policies on serving endpoints.
*   Log model inputs/outputs for drift and hallucinations auditing.

---

## 4. Security, Access Controls & Governance (Guardrailing)

Databricks Unity Catalog provides fine-grained, identity-based security to enforce row and column-level boundaries, completely shielding sensitive metrics from unauthorized eyeballs.

```
                  [ Public Health Planner (Assam Region) ]
                                     │
                                     ▼
                      [ Unity Catalog Row Filter ]
                                     │
                                     ▼
                [ SELECT * FROM gold_flagged_facilities ]
                  ↳ Automatically rewrites to:
                    WHERE address_stateOrRegion = 'Assam'
```

### Row-Level Security (RLS)
We can protect records dynamically based on the region of the logged-in planner using a **Row Filter Function**:

```sql
-- 1. Create the filter function
CREATE FUNCTION workspace.default.region_filter(region STRING)
RETURN IS_ACCOUNT_GROUP_MEMBER('Admins') 
       OR region = CURRENT_USER(); -- Restricts users to only their assigned state

-- 2. Bind the filter to the gold table
ALTER TABLE workspace.default.gold_flagged_facilities 
SET ROW FILTER workspace.default.region_filter ON (address_stateOrRegion);
```

### Column-Level Masking
To guard sensitive patient/facility contact details (e.g., direct phone numbers) from general planners while keeping them available to coordinators, we declare a **Column Mask**:

```sql
CREATE FUNCTION workspace.default.phone_mask(phone STRING)
RETURN CASE 
         WHEN IS_ACCOUNT_GROUP_MEMBER('Coordinators') THEN phone
         ELSE 'XXX-XXX-XXXX' -- Mask for all other users
       END;

ALTER TABLE workspace.default.gold_flagged_facilities 
ALTER COLUMN phone_numbers SET MASK workspace.default.phone_mask;
```

---

## 5. Multi-Environment CI/CD (Asset Bundles)

Production pipelines and Databricks Apps must never be manually synced or updated in production workspaces. We must manage and deploy everything as Code.

### Databricks Asset Bundles (DAB)
We package our app, configuration files, and DLT pipelines into a declarative **Databricks Asset Bundle** managed via `databricks.yml`:

```yaml
bundle:
  name: data-readiness-desk-bundle

targets:
  dev:
    workspace:
      host: https://dbc-dev-workspace.cloud.databricks.com
  prod:
    workspace:
      host: https://dbc-prod-workspace.cloud.databricks.com

resources:
  apps:
    data-readiness-desk:
      name: "data-readiness-desk"
      source_code_path: "./src"
```

### CI/CD Deployment Flow
1.  **Code Commit**: Developer pushes code to `main` branch on GitHub.
2.  **GitHub Actions**: Triggers a deployment workflow.
3.  **Validation**: GitHub runs unit tests and lints code.
4.  **DAB Deploy**: Runs `databricks bundle deploy --target prod` using a secure CI/CD Service Principal, pushing the new container image and updating Unity Catalog Delta schemas without human intervention.

---

## 6. Hybrid Operational/Analytical Decoupling (OLTP vs OLAP)

A core architectural boundary in Databricks Delta Lake (OLAP) is that it is not designed to replace globally distributed, high-concurrency, sub-millisecond transactional databases (OLTP) like GCP Spanner or PostgreSQL.

### Current Prototype State (Low Concurrency)
For our hackathon scale, writing back directly to Delta Lake in Unity Catalog is highly efficient. Delta Lake's transaction log guarantees full **ACID compliance** via Optimistic Concurrency Control (OCC). Since only a few data librarians are triaging the queue, Delta Lake handles the low-concurrency updates perfectly without external database dependencies.

### Enterprise Scaling State (High Concurrency / Real-time OLTP Decoupling)
If this application scales to **10,000+ concurrent global medical planners** requiring sub-millisecond read/write latency, direct writebacks to Delta Lake would cause lock-contention and slower write latencies. 

In this case, we decouple the architecture using an **Operational Data Store (ODS)**:

```
 [ Databricks App UI ] ────(Instant Write)───> [ Operational DB (e.g., Spanner / Postgres) ]
           │                                                      │
     (Federated Read)                                        (CDC Stream)
           │                                                      │
           ▼                                                      ▼
 [ Lakehouse Federation ] <──(Real-time Queries)─── [ Delta Lake / Unity Catalog ]
```

1.  **Direct Writeback to OLTP**: The Streamlit App commits human decisions and reviewer notes instantly to an external, high-concurrency OLTP database (such as Spanner or Azure CosmosDB) for millisecond latency.
2.  **Change Data Capture (CDC) Sync**: A continuous streaming pipeline (using Databricks Auto Loader or Debezium) streams the updates from the OLTP database back into the Delta Lake Gold table to keep analytics updated.
3.  **Lakehouse Federation**: We configure **Databricks Lakehouse Federation** on Unity Catalog. This allows Databricks SQL compute to query and join Delta tables with the external Spanner/Postgres tables in real-time, on-demand, without moving data, providing a complete **Hybrid Transactional/Analytical Processing (HTAP)** framework.
