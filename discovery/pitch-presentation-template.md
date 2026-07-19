# Live Pitch Presentation Playbook: Data Readiness Desk
*(5-Minute Global AI Hackathon Pitch Outline & Demo Script)*

This document provides your slide-by-slide structure, core talking points, and step-by-step live-demo playbook to win over the judges during your final presentation.

---

## Slide 1: The Hook (The Trust Crisis)
*   **Slide Title**: Data Readiness Desk: Fixing the Foundation of Trust in Global Healthcare Maps
*   **Your Script (The Problem)**:
    > "In public health, a wrong query is not a failed server request—it is a family driving six hours to an empty hospital that claimed to have an ICU. Out of 10,000 healthcare records shared by the Virtue Foundation, only 25% have bed capacity records, and only 36% list doctor counts. Yet, 99% make massive capability claims in free-text descriptions. 
    > 
    > While 90% of hackathon teams today built basic RAG chatbots to query this messy, unverified data, **we built the Trust Layer to fix it**. Because garbage in is garbage out. We present the Data Readiness Desk."

---

## Slide 2: The Core Engineering Solution (Under the Hood)
*   **Slide Title**: A Medallion Data Quality Pipeline on Databricks Serverless
*   **Your Script (The Architecture)**:
    > "We built a self-initializing medallion architecture inside Databricks using Unity Catalog and Serverless SQL. 
    > 
    > Our system consumes from the shared Delta Sharing Catalog, automatically standardizes sparse structures in our Silver Layer, and compiles a Gold table. In the Gold layer, we run a dual-validation engine executing **four hard contradiction logic rules** and a **weighted trust score (0 to 100)** to bubble up high-risk, conflicting records directly to the triage desk."

---

## Slide 3: The 4 Core Contradiction Rules
*   **Slide Title**: Algorithmic Integrity Over Manual Audits
*   **Talking Points**:
    *   **Rule 1: ICU Beds Mismatch (-30 points)**: Claims ICU services in notes, but lists `0` or null capacity beds in database.
    *   **Rule 2: Emergency Doctor Deficit (-35 points)**: Claims 24/7 trauma/emergency, but lists `0` active doctors.
    *   **Rule 3: Surgical Anesthesia Gap (-20 points)**: Lists complex surgical procedures, but completely lacks anesthesia or ventilator equipment in text.
    *   **Rule 4: Data Desert Alert (-15 points)**: Facilities that are complete metadata voids, having zero structured metrics.

---

## Slide 4: Live Demo Playbook (The "Aha!" Moment)
*   **Slide Title**: Live Product Walkthrough
*   **DEMO ACTIONS (Run these live!)**:

1.  **Step 1: Open the App & Show the Dashboard**
    *   *Show*: The key metrics cards, the Trust Score Distribution chart, and the Flag Prevalence bar chart.
    *   *Say*: *"Our native Databricks App presents a clean, live executive dashboard of the 10,000 facilities. The charts show us exactly where our data quality is weakest."*
2.  **Step 2: Show the Triage Queue & Open a Mock Example**
    *   *Show*: Sort the table by lowest trust score. Find and select **`MOCK-EMERG-DOC-FAIL`** (`Patna 24/7 Trauma and Acute Emergency Center`).
    *   *Say*: *"Let's look at this critical triage case Patna 24/7 Trauma Center. It has a Trust Score of only 65/100. Our pipeline flagged it under Active Trust Warnings because they claim 'emergency surgeries' in unstructured text, but list ZERO active doctors! This is a massive, life-threatening contradiction."*
3.  **Step 3: Trigger the Databricks AI Audit (The Ultimate Flex!)**
    *   *Action*: Click the button: **🤖 Run Live AI Contradiction Audit**.
    *   *Show*: The spinner runs, then shows Llama 3 70B's exact semantic verdict.
    *   *Say*: *"If an auditor is unsure, they don't guess. They click this button, launching a serverless query to Llama-3-70B on Databricks to semantically cross-examine the text against stated capabilities on-demand."*
4.  **Step 4: Resolve the Triage Case (ACID Persistence)**
    *   *Action*: Write *"Flagged as fraudulent: claims 24/7 trauma but has 0 doctors. Re-verified via AI audit."* in the text area, and click **🔴 Flag as Suspicious / Fraudulent**.
    *   *Show*: The page refreshes, Patna Patna Center disappears from the PENDING queue, and the "Flagged Contradictions" metric on top increments by 1.
    *   *Say*: *"With one click, our writeback commits an ACID-compliant UPDATE statement directly back to Delta Lake in Unity Catalog. The cache evicts and updates our global registry in real-time."*
5.  **Step 5: Show the Geographic Desert Map**
    *   *Action*: Click the **Geographic Desert Map** tab.
    *   *Show*: Scroll and hover over the map pins across India.
    *   *Say*: *"Finally, we help planners isolate 'Medical Deserts' (no hospitals) from 'Data Deserts' (no trust). Gray pins indicate Data Deserts—places where planners cannot make decisions because they have no trustworthy metrics. This is how data becomes action."*

---

## Slide 5: Enterprise Scaling Rationale
*   **Slide Title**: Scaling to Enterprise Production
*   **Your Script (The Future)**:
    > "Our design is 100% ready to scale. To productionize this across global healthcare networks:
    > 1. We replace static loads with **Databricks Auto Loader** and streaming **Delta Live Tables (DLT)** for continuous, real-time ingestion.
    > 2. We move UI validations to **DLT Expectations** to reject or quarantine bad records before they hit the warehouse.
    > 3. We implement **Unity Catalog Row-Level Security** to restrict regional coordinators to their state's records, and mask contact fields automatically.
    > 4. We bundle everything with **Databricks Asset Bundles (DAB)** for automated dev-to-prod CI/CD."

---

## Slide 6: Conclusion (Coordination is Care)
*   **Slide Title**: Turning Messy Data Into Actions We Can Defend
*   **Your Script**:
    > "A Wrong Query on our app is not a bug—it is a family saved from driving hours to an unstaffed facility. By creating this secure, auditable trust layer on Databricks, we are turning 10,000 messy facility records into decisions planners can defend.
    > 
    > That is how coordination becomes care. Thank you."
