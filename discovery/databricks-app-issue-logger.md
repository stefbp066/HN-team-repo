# Databricks App Issue & Privilege Logger

This document records technical issues, privilege assessments, and operational workarounds encountered during the development and deployment of the **Data Readiness Desk** on Databricks Free Edition.

---

## 1. App Service Principal Privilege Assessment

When a native Databricks App is deployed, it runs under a dedicated, system-generated **Service Principal (SA)** rather than the personal user account of the deployer.

*   **App Service Principal ID**: `edc29524-5306-48d2-9403-edfd461ab62f`
*   **App Service Principal Name**: `app-5q6f75 data-readiness-desk`

### Default Privileges (Before Fix)
By default, the system-created App Service Principal has a highly restricted sandbox footprint:
1.  **Read/Write isolated space**: Restricted to app-internal storage.
2.  **No Catalog Access**: Cannot traverse any metadata catalog including standard `workspace` or external `databricks_virtue_foundation_dataset_dais_2026`.
3.  **No Schema Access**: Cannot query, write to, or create tables in default workspace databases (like `workspace.default`).

### Minimum Required Privileges (After Fix)
To function correctly, the App Service Principal must be granted the following privileges. These were applied by executing the following commands via our warehouse:

| Securable Object | Privilege Granted | Reason |
|---|---|---|
| **Catalog** `databricks_virtue_foundation_dataset_dais_2026` | `USE CATALOG` | Allows the App to see and traverse the Delta Sharing shared catalog. |
| **Schema** `databricks_virtue_foundation_dataset_dais_2026.virtue_foundation_dataset` | `SELECT` | Grants read access to the source table containing 10,088 messy records. |
| **Catalog** `workspace` | `USE CATALOG` | Allows the App to target the workspace-managed catalog. |
| **Schema** `workspace.default` | `USE SCHEMA`, `CREATE TABLE`, `SELECT`, `MODIFY` | Allows the App to automatically compile the Silver/Gold tables and persist user review status changes. |

---

## 2. Resolved Technical Issues

### Issue #01: Automated Ingestion Privilege Block
*   **Severity**: 🔴 Critical
*   **Symptom**: App showed warning `No records loaded. Verify your Shared Catalog access or SQL Warehouse status.` Logs indicated:
    ```
    [INSUFFICIENT_PERMISSIONS] Insufficient privileges: User does not have USE CATALOG on Catalog 'databricks_virtue_foundation_dataset_dais_2026'. SQLSTATE: 42501
    ```
*   **Root Cause**: The App Service Principal was executing the initialization statement `CREATE TABLE IF NOT EXISTS workspace.default.gold_flagged_facilities AS SELECT ... FROM databricks_virtue_foundation_dataset_dais_2026...` but had no access rights to either the source catalog or the destination default schema.
*   **Resolution**: Executed five SQL `GRANT` statements from an admin session to assign catalog-level `USE` and table-level `SELECT/MODIFY` rights to the `edc29524-5306-48d2-9403-edfd461ab62f` service principal.

---

### Issue #02: SQL Execution Race Condition (Asynchronous CTAS)
*   **Severity**: 🟡 Medium
*   **Symptom**: First load of the app threw:
    ```
    [TABLE_OR_VIEW_NOT_FOUND] The table or view `workspace`.`default`.`gold_flagged_facilities` cannot be found. SQLSTATE: 42P01
    ```
*   **Root Cause**: In Databricks, SQL statement execution via `execute_statement` runs **asynchronously** for long-running queries (like `CREATE TABLE AS SELECT`). The API returned `PENDING/RUNNING` and Python immediately proceeded to run `SELECT * FROM workspace.default.gold_flagged_facilities` before the warehouse finished writing the table schema on disk.
*   **Resolution**: 
    1. Imported `time`.
    2. Refactored `run_sql_statement` helper in `src/app.py` to synchronously poll the statement execution status until the state transitions out of `PENDING` and `RUNNING`.
    3. Guarantees that execution only returns to Streamlit once the table is fully created and populated (`SUCCEEDED` status).
