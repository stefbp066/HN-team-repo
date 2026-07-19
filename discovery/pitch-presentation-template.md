# Live Pitch Presentation Playbook: Data Readiness Desk
*(5-Minute Global AI Hackathon Pitch Outline & Slide Generator Prompt)*

This document contains your slide-by-slide structure, core talking points, step-by-step live-demo script, and **detailed graphic specifications** for generating a high-impact, professional slide deck.

---

## Brand Design & Visual Theme: "The Trust Layer Blueprint"

*   **Primary Corporate Color**: Deep Space Navy (`#0C1B33`) — Represents security, Unity Catalog governance, and enterprise-grade infrastructure.
*   **Contradiction Accent Color**: Alert Terracotta/Orange (`#FF3621`) — Represents Databricks, warning flags, and critical data discrepancies.
*   **Verified Health Accent Color**: Mint Green (`#00CC96`) — Represents clean data, vetted facilities, and trusted metrics.
*   **Supporting Backgrounds**: Ice Blue White (`#F7F9FC`) for light slides, and Charcoal Obsidian (`#111827`) for dark impact slides (e.g., Title/Conclusion).
*   **Typography**: Bold geometric sans-serif (e.g., Inter, Montserrat) for headings, highly legible clean sans-serif for body.

---

## Slide 1: Title & Hook (The Trust Crisis)
*   **Slide Title**: Data Readiness Desk: Fixing the Foundation of Trust in Global Healthcare Maps
*   **Your Script (The Problem)**:
    > "In public health, a wrong query is not a failed server request—it is a family driving six hours to an empty hospital that claimed to have an ICU. Out of 10,000 healthcare records shared by the Virtue Foundation, only 25% have bed capacity records, and only 36% list doctor counts. Yet, 99% make massive capability claims in free-text descriptions. 
    > 
    > While 90% of hackathon teams today built basic RAG chatbots to query this messy, unverified data, we built the Trust Layer to fix it. Because garbage in is garbage out. We present the Data Readiness Desk."
*   **Visual Layout & Graphic Elements**:
    *   **Background**: Full-bleed Dark Obsidian (`#111827`).
    *   **Layout**: Left-aligned, high-contrast, oversized white typography for the main title, with key warning text highlighted in Terracotta Orange (`#FF3621`).
    *   **Main Graphic (Right Side)**: A high-impact 3D abstract visualization of a map grid breaking apart or cracking under a hospital location pin, with a "Data Integrity Gap" warning overlay (representing the trust crisis).
    *   **Icon Elements**: Shield icon merging with a location marker.

---

## Slide 2: The Core Engineering Solution (Under the Hood)
*   **Slide Title**: A Medallion Data Quality Pipeline on Databricks Serverless
*   **Your Script (The Architecture)**:
    > "We built a self-initializing medallion architecture inside Databricks using Unity Catalog and Serverless SQL. 
    > 
    > Our system consumes from the shared Delta Sharing Catalog, automatically standardizes sparse structures in our Silver Layer, and compiles a Gold table. In the Gold layer, we run a dual-validation engine executing four hard contradiction logic rules and a weighted trust score to bubble up high-risk, conflicting records directly to the triage desk."
*   **Visual Layout & Graphic Elements**:
    *   **Background**: Ice Blue White (`#F7F9FC`).
    *   **Layout**: 3-stage horizontal split chevron diagram representing the Medallion flow (Bronze -> Silver -> Gold).
    *   **Main Graphic (Horizontal Flow Diagram)**:
        1.  **Bronze (Left)**: Icon of unstructured text data with a connection arrow. Label: `Delta Sharing Raw Catalog`.
        2.  **Silver (Center)**: Icon of databases cleaning. Label: `Structure Normalization & Type Casts (Pandas/SQL)`.
        3.  **Gold (Right)**: Glowing Mint Green block. Label: `Automated Contradiction Validation Engine`.
    *   **Arrow overlays**: Transition lines marked with "ACID Transactions" and "Serverless Compute".

---

## Slide 3: The 4 Core Contradiction Rules
*   **Slide Title**: Algorithmic Integrity Over Manual Audits
*   **Talking Points**:
    *   **Rule 1: ICU Beds Mismatch (-30 points)**: Claims ICU services in notes, but lists `0` or null capacity beds in database.
    *   **Rule 2: Emergency Doctor Deficit (-35 points)**: Claims 24/7 trauma/emergency, but lists `0` active doctors.
    *   **Rule 3: Surgical Anesthesia Gap (-20 points)**: Lists complex surgical procedures, but completely lacks anesthesia or ventilator equipment in text.
    *   **Rule 4: Data Desert Alert (-15 points)**: Facilities that are complete metadata voids, having zero structured metrics.
*   **Visual Layout & Graphic Elements**:
    *   **Background**: Ice Blue White (`#F7F9FC`).
    *   **Layout**: 2x2 grid card layout. Each card represents one rule.
    *   **Card Styling**: Clean white card bodies with thin gray borders. High-contrast large number indicators for penalties (e.g., `-35` in oversized bold red text inside the Emergency card).
    *   **Visual Indicators**:
        *   Card 1 (ICU): Intensive care bed icon crossed out.
        *   Card 2 (Emergency): Doctor stethoscope icon crossed out.
        *   Card 3 (Surgical): Operation lamp icon next to a warning triangle.
        *   Card 4 (Desert): Empty sand dune silhouette or grid-dot void.

---

## Slide 4: Live Demo Playbook (The "Aha!" Moment)
*   **Slide Title**: Live Product Walkthrough
*   **DEMO ACTIONS (Run these live!)**:
    1.  **Step 1: Open the App & Show the Dashboard**
        *   *Say*: *"Our native Databricks App presents a clean, live executive dashboard of the 10,000 facilities. The charts show us exactly where our data quality is weakest."*
    2.  **Step 2: Show the Triage Queue & Open a Mock Example**
        *   *Say*: *"Let's look at this critical triage case Patna 24/7 Trauma Center. It has a Trust Score of only 65/100. Our pipeline flagged it under Active Trust Warnings because they claim 'emergency surgeries' in unstructured text, but list ZERO active doctors! This is a massive, life-threatening contradiction."*
    3.  **Step 3: Trigger the Databricks AI Audit (The Ultimate Flex!)**
        *   *Say*: *"If an auditor is unsure, they don't guess. They click this button, launching a serverless query to Llama-3-70B on Databricks to semantically cross-examine the text against stated capabilities on-demand."*
    4.  **Step 4: Resolve the Triage Case (ACID Persistence)**
        *   *Say*: *"With one click, our writeback commits an ACID-compliant UPDATE statement directly back to Delta Lake in Unity Catalog. The cache evicts and updates our global registry in real-time."*
    5.  **Step 5: Show the Geographic Desert Map**
        *   *Say*: *"Finally, we help planners isolate 'Medical Deserts' (no hospitals) from 'Data Deserts' (no trust). Gray pins indicate Data Deserts—places where planners cannot make decisions because they have no trustworthy metrics. This is how data becomes action."*
*   **Visual Layout & Graphic Elements**:
    *   **Background**: Ice Blue White (`#F7F9FC`).
    *   **Layout**: Left side shows a clean mockup frame of the Streamlit App interface. Right side lists the 5 high-impact bulleted steps of the demo script.
    *   **Graphics**: A visual callout bubble pointing to the **"🤖 Run Live AI Contradiction Audit"** button on the mockup, highlighted in glowing Databricks Orange (`#FF3621`) to emphasize the AI element.

---

## Slide 5: Enterprise Scaling Rationale (GCP to Databricks Architecture)
*   **Slide Title**: Unified Lakehouse Streaming: Scaling to Enterprise Production
*   **Your Script (The Future)**:
    > "Planners need real-time data streaming to coordinate emergency hospital bed allocations during a crisis. If you come from a Google Cloud background, you are likely used to Pub/Sub, Dataflow, and BigQuery. In Databricks, we achieve the exact same real-time streaming capability, but unified under a single, highly simplified SQL and Delta Lake architecture.
    > 
    > Instead of setting up Pub/Sub topics, we use **Databricks Auto Loader** to stream incoming CSVs/JSONs directly from cloud buckets. Instead of complex Apache Beam pipelines in Dataflow, we use **Delta Live Tables (DLT)**. With DLT, we write standard SQL queries marked with `STREAMING TABLE`. Databricks handles the cluster auto-scaling, state-checkpointing, and data-quality Expectations natively. 
    > 
    > This is the power of a Unified Lakehouse—unifying batch and streaming under one governed database."
*   **Visual Layout & Graphic Elements**:
    *   **Background**: Ice Blue White (`#F7F9FC`).
    *   **Layout**: Split-screen design. Left side shows GCP's three-part streaming stack; Right side shows Databricks' Unified Streaming Stack, highlighting code reduction and ease of governance.
    *   **Main Graphic (GCP vs Databricks Flow)**:
        *   *Left Box (The Old Way - GCP)*: 
            `[Pub/Sub (Queue)]` ──> `[Dataflow (Beam Compute)]` ──> `[BigQuery (Warehouse)]`
            *(Note overlay: 'Complex, dual-engine codebase, high maintenance overhead')*
        *   *Right Box (The Lakehouse Way - Databricks)*:
            `[S3 Bucket]` ──> `[Auto Loader]` ──> `[Delta Live Tables (DLT)]` ──> `[Unity Catalog Delta Lake]`
            *(Note overlay: 'Single unified SQL codebase, managed auto-scaling, embedded quality checks')*
    *   **Color Accents**: Use Terracotta Orange (`#FF3621`) for the Databricks box to make the solution pop.

---

## Slide 6: Conclusion (Coordination is Care)
*   **Slide Title**: Turning Messy Data Into Actions We Can Defend
*   **Your Script**:
    > "A Wrong Query on our app is not a bug—it is a family saved from driving hours to an unstaffed facility. By creating this secure, auditable trust layer on Databricks, we are turning 10,000 messy facility records into decisions planners can defend.
    > 
    > That is how coordination becomes care. Thank you."
*   **Visual Layout & Graphic Elements**:
    *   **Background**: Deep Obsidian Dark (`#111827`).
    *   **Layout**: Center-aligned, massive, clean typography with high emotional impact.
    *   **Main Graphic**: A glowing, crisp, unified Map of India silhouette composed of clean Mint Green (`#00CC96`) location pins, with the central overlay slogan: `Coordination is Care` in bold white letters.
    *   **Footer**: Small logos of Databricks and the Virtue Foundation to close the deck.
