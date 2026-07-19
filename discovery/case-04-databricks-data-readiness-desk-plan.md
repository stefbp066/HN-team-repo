# Databricks Architecture & Implementation Plan: Data Readiness Desk

This document serves as the discovery record, design rationale, and technical implementation guide for **Case 04 - Databricks Data Legend (Challenge Brief)**.

---

## 1. Executive Summary & Design Rationale

During the architecture phase, we analyzed the four potential mission tracks provided in the brief. Our goal was to select a track that maximized Data Engineering (DE) impact, ensured ease of evaluation during judging, and presented a highly persuasive solution quality.

### Comparison of Mission Tracks

| Track | Target Audience | Primary Workload | DE Complexity | Evaluation Ease | Competitor Density (Est.) |
|---|---|---|---|---|---|
| **Referral Copilot** | Patient / Coordinator | RAG & Vector Search | Low | Easy | **70%** (Chatbot bloodbath) |
| **Facility Trust Desk** | Internal Teams | Text Citation Extractor | Medium | Easy | High |
| **Medical Desert Planner** | Public Health Planner | Spatial Aggregation & Map | High | Hard | 20% (High risk on UI/Math) |
| **Data Readiness Desk** | Data Librarian / Auditor | Automated Data Quality | **High** | **Medium (Strong Narrative)** | **10%** (Under-tapped niche) |

### Why We Chose the "Data Readiness Desk"

1. **Avoid the Chatbot Bloodbath**: ~70% of contestants will build standard RAG chatbots (Referral Copilot). Differentiating a generic LLM-lookup wrapper is difficult.
2. **Play to Hard Data Engineering Strengths**: This track attacks the **root problem**: the data itself is messy ("garbage in, garbage out"). Building robust cleaning and automated contradiction validation pipelines showcases deep DE skills (Delta Lake, serverless SQL, ACID compliance, data lineage).
3. **The "Aha!" Demo Narrative**: Planners can instantly see high-leverage contradictions (e.g., claiming Level 1 Trauma but listing zero doctors). Surfacing these in a dedicated review queue with direct Unity Catalog writebacks creates a highly memorable human-in-the-loop product story.

---

## 2. Infrastructure & Workspace Constraints

* **Platform**: Optimized for **Databricks Free Edition** (the new AWS-backed, Serverless-only tier).
* **Natively Supported Features**: 
  * Serverless compute is mandatory.
  * Native Databricks Apps (up to 3 Streamlit/Dash applications per account).
  * Unity Catalog Metastore (1 per workspace).
  * AI Search endpoints (Vector Search).
* **Bypassed Infrastructure**: Officially skipped heavyweight Terraform setups to minimize unnecessary configuration overhead on restricted free-tier resources.

---

## 3. Data Architecture (Medallion Flow)

Our pipeline consumes directly from the shared Delta Sharing Catalog (`databricks_virtue_foundation_dataset_dais_2026`) and transforms records into a secure, validated Gold Delta table.

```
 [ Delta Sharing Catalog ] 
 (virtue_foundation_dataset.facilities)
           │
           ▼
     [ Silver Layer ] ──> Clean data types, cast metrics, normalize NULLs.
           │
           ▼
     [ Gold Layer ]   ──> Apply Dual-Layer Validation Rules (SQL + LLM).
   (gold_flagged_facilities)
           │
           ▼
     [ Databricks App ] ──> Streamlit UI reads from Gold Table.
           │
           └─(Update)───> Human reviewer approves/flags. SQL updates Delta Table.
```

### Ingestion & Source Data
* **Catalogs**: Read directly from the shared catalog: `databricks_virtue_foundation_dataset_dais_2026.virtue_foundation_dataset.facilities`.
* **Dataset Size**: 10,088 records representing Indian healthcare facilities.
* **Messiness**: Highly sparse structured metrics (`numberDoctors` at 36.4% coverage, `capacity` beds at 25.2% coverage) mixed with rich, contradictory unstructured description notes.

---

## 4. Automated Contradiction Engine (The Logic)

We established **four core data quality validation rules** combining hard SQL constraints with semantic parsing:

1. **flag_icu_no_capacity (ICU Beds Missing)**
   * *Condition*: Facility explicitly claims `ICU` capabilities or mentions `ICU` in description, but bed `capacity` is `0`, empty, or `NULL`.
   * *Impact Penalty*: Deduct 30 points from Trust Score.
2. **flag_emergency_no_doctors (Emergency Doctor Deficit)**
   * *Condition*: Facility claims `emergency` or `trauma` care, but `numberDoctors` is `0`, empty, or `NULL`.
   * *Impact Penalty*: Deduct 35 points from Trust Score.
3. **flag_surgery_no_anesthesia (Surgical Support Deficit)**
   * *Condition*: Complex surgical `procedures` are listed, but no reference to `anesthe` (Anesthesiologist/Anesthesia) or `ventilator` is present in the `equipment` or description notes.
   * *Impact Penalty*: Deduct 20 points from Trust Score.
4. **flag_data_desert (Critical Meta Deficit)**
   * *Condition*: All key planning fields (`capacity`, `numberDoctors`, `yearEstablished`) are completely missing.
   * *Impact Penalty*: Deduct 15 points from Trust Score.

### Trust Score Formula
The baseline trust score is **100**. For every active contradiction flag, we deduct the respective penalty, routing records with low scores (`trust_score < 70`) to the top of the human planner's triage queue.

---

## 5. Native Databricks App Architecture

The app is built in Python using the Streamlit framework and deployed as a secure, native Databricks App.

* **Database Connection**: Utilizes the `databricks-sdk` to connect to Databricks Serverless SQL. It programmatically discovers the workspace's default SQL Warehouse ID, avoiding hardcoded values.
* **Self-Initialization**: On app boot, if the target gold table does not exist, the app automatically executes a massive PySpark/SQL ELT statement to initialize, clean, and populate `workspace.default.gold_flagged_facilities`.
* **Interactive Dashboard**: Draws Plotly histograms showing overall trust score distribution and bar charts of flag prevalence.
* **Side-by-Side Audit**: Renders the raw unstructured facility text next to structured claims, explicitly highlighting active trust warnings (e.g., matching missing doctor alerts).
* **Lakebase Persistence**: Incorporates an actionable decision desk. When a human auditor enters notes and clicks `Approve`, `Flag as Fraudulent`, or `Save Note`, the app executes an ACID-compliant SQL `UPDATE` statement back to the Unity Catalog Delta table. The cache is cleared instantly (`st.cache_data.clear()`), updating the Triage Queue in real-time.

---

## 6. Pipeline Quality Evaluation Strategy

Without a ground truth label dataset, pipeline quality is assessed through three metrics:
1. **Rule Coverage Check**: Verifies that the SQL engine catches 100% of mathematically predictable database conflicts.
2. **LLM Determinism Checks**: Take a stratified sample of 50 records (25 known good, 25 known bad). Execute the semantic verification prompts 3 times and log the traces using **MLflow 3 Tracing** to prove a consistency threshold of `>95%`.
3. **High-Leverage Impact Score**: Tracks the active reduction of flagged entries (e.g., "Total flagged entries remaining") to demonstrate the downstream clean data output rate of the audit desk.
