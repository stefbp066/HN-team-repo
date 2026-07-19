# 🏥 India Healthcare Data Readiness Desk
### *Databricks Intelligence Platform: Automating Ground-Truth Validation for Healthcare Infrastructure*

Welcome to the **Data Readiness Desk**—an enterprise-grade automated data validation pipeline and triage audit application built natively on the **Databricks Serverless Platform** for the **6th Global AI Hackathon (Case 04 - Databricks Data Legend)**.

---

## 1. The Core Problem (The Trust Crisis)

Public health NGOs like the **Virtue Foundation** use geocoded hospital maps to route critical supplies and transfer emergency patients during regional crises. However, the raw facility records are highly incomplete and contradictory:
*   **75% of rows** are completely missing bed capacity records.
*   **64% of rows** are missing active doctor counts.
*   Yet, **99% of facilities** make massive capability claims (e.g., claiming a "50-bed intensive care unit") in their unstructured, free-text description notes to capture funding.

A static map that trusts these raw, unverified descriptions blindly creates a severe hazard: **"A wrong referral is not a failed server query—it is a family driving six hours to an empty hospital."**

The **Data Readiness Desk** fixes this foundation of trust.

---

## 2. System Architecture & Medallion Data Flow

Our system utilizes **Databricks Serverless** and **Unity Catalog** to implement a secure, transactionally consistent medallion pipeline:

```
[ Delta Sharing Raw Catalog ] (facilities)
             │
             ▼
     [ Silver Layer ] ──> Clean metadata, handle null strings, normalize schemas.
             │
             ▼
     [ Gold Layer ]   ──> Apply 4 Contradiction Rules & compute Trust Score (0-100).
  (gold_flagged_facilities)
             │
             ▼
     [ Databricks App ] ──> Streamlit UI reads from Gold Table.
             │
             └─(Instant Write)───> Human audits & signs decisions. Writes back live.
```

---

## 3. The 4 Core Contradiction Rules

Our pipeline processes 10,088 raw rows in parallel using Serverless SQL, executing **four parallel logic rules** to compute a weighted **Facility Trust Score (0 to 100)**:

1.  **ICU Beds Mismatch (-30 Points)**: Claims to offer intensive care unit (ICU) services but lists `0` or null bed capacity.
2.  **Emergency Doctor Deficit (-35 Points)**: Claims 24/7 emergency/trauma care but lists `0` active doctors.
3.  **Surgical Anesthesia Gap (-20 Points)**: Lists complex surgical procedures (e.g., open-heart surgery) but lists zero anesthesia or ventilator support in its equipment list or text notes.
4.  **Critical Data Desert (-15 Points)**: Complete database voids—facilities with zero reported structural metrics (established year, capacity, and doctors).

---

## 4. Under-The-Hood Platform Engineering Feats

We went beyond basic application coding to engineer around real, low-level platform and SDK boundaries on Databricks Serverless:

*   **Synchronous Polling Engine**: Databricks Serverless SQL executions run asynchronously over HTTP REST. To prevent a race condition where the frontend queries tables before they are fully compiled, we built a custom **synchronous polling engine** that polls the `get_statement` API in a `while` loop until the schema is guaranteed ready on disk, eliminating `TABLE_OR_VIEW_NOT_FOUND` errors.
*   **Typed SDK ChatMessage Binding**: For on-demand semantic audits, we query **Llama 3.3 (70B)** via Serverless Model Serving. We bypassed the Databricks Python SDK's raw dictionary serialization bugs (`'dict' object has no attribute 'as_dict'`) by binding the prompt directly to official, typed `ChatMessage` and `ChatMessageRole` SDK dataclasses.
*   **Pragmatic Daily Batch Ingestion**: Since hospital locations are fundamentally static physical infrastructures, we rejected 24/7 real-time streaming as costly over-engineering. We scheduled our **Auto Loader** and **Delta Live Tables (DLT)** pipeline as a daily batch interval—saving **90% in monthly compute costs** for our NGO partners.
*   **Natively Governed PII Tagging**: We executed `ALTER TABLE` DDL queries to stamp the raw `description` column with a native **`PII = unstructured_pii`** tag and the `unique_id` with **`classification = surrogate_key`** natively in Unity Catalog, ensuring enterprise-grade metadata classification.

---

## 5. Live Product Walkthrough (The UX)

Our containerized, native Databricks App is built on Streamlit and split into two clean tabs:

### Tab 1: Audit and Triage Queue
*   **Interactive Dashboard**: Plotly histograms showing overall trust score distribution and bar charts of flag prevalence.
*   **Searchable Table**: Styled with conditional color mapping (Red for critical contradictions `< 70`, Yellow for warning signs `< 90`, Green for vetted data).
*   **Side-by-Side Deep Audit**: Shows the raw description next to structured claims, explicitly highlighting active trust warnings and offering an interactive information tooltip icon `(ℹ️)` explaining the exact trust score math.
*   **Llama 3.3 AI Copilot Audit**: Auditors click a single button to run a live, GPU-powered semantic audit using Llama-3.3-70b to evaluate description-to-claim consistency on the fly.
*   **Decision Desk**: Auditors write notes and click `Approve` or `Flag as Fraudulent`, executing an ACID-compliant SQL `UPDATE` that commits to the Delta table transaction log, instantly evicting the app cache and refreshing the page in real-time.
*   **Reset Demo Database**: A secondary button in the sidebar that drops and rebuilds the gold table, immediately injecting 3 highly contradictory mock facility records—creating a perfect, repeatable live-demo environment.

### Tab 2: Geographic Desert Map
*   **Native PyDeck Integration**: Renders a gorgeous, custom Map of India.
*   **Data Desert Isolation**: Pins are color-coded by risk category. It renders **Data Deserts** in **Gray** (where facilities are completely missing metrics), allowing health planners to visually separate *"we don't know what's hospital is here"* (Data Desert) from *"no hospitals exist in this area"* (Medical Desert) to prevent wasting millions in NGO building budgets.

---

## 6. Project Documentation & Playbooks

All research notes, plans, and presentation scripts are located inside the `discovery/` folder:
*   [Databricks App Under-the-Hood Guide](discovery/databricks-app-under-the-hood.md) — Detailed technical breakdown of SDKs, SQL polling, and types.
*   [Databricks App Issue & Privilege Logger](discovery/databricks-app-issue-logger.md) — Diagnostic records of the Service Principal permission blocks and async race conditions.
*   [Enterprise Productionization Roadmap](discovery/enterprise-productionization-blueprint.md) — Strategic blueprint mapping local prototypes to Autoloader, DLT Expectations, and Unity Catalog Row-Level Filters.
*   [Live Pitch Presentation Playbook](discovery/pitch-presentation-template.md) — Slide-by-slide structure, graphic prompts for Gemini slide generation, and a step-by-step 5-minute pitch script.

---

## 7. How to Deploy & Run Local Code

### Prerequisites
*   Python 3.11+
*   Databricks CLI (v1.8.0+) configured to your serverless workspace:
    ```bash
    brew install databricks/tap/databricks
    databricks auth login
    ```

### local Setup
1.  Clone the repository and initialize the virtual environment:
    ```bash
    git clone https://github.com/stefbp066/HN-team-repo.git
    cd HN-team-repo
    python3 -m venv venv
    source venv/bin/activate
    pip install -r src/requirements.txt
    ```

### Sync to Workspace
2.  Upload the local `src` folder to your Databricks Workspace:
    ```bash
    databricks sync ./src /Users/stefan.pang99@gmail.com/data-readiness-desk
    ```

### Register and Deploy Natively
3.  Register the Databricks App and deploy the synchronized code:
    ```bash
    databricks apps create data-readiness-desk
    databricks apps deploy data-readiness-desk --source-code-path /Workspace/Users/stefan.pang99@gmail.com/data-readiness-desk
    ```
    Once deployed, access the app instantly via the generated organization URL!
