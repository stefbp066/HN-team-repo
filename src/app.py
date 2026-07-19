import streamlit as st
import pandas as pd
import plotly.express as px
import time
import json
from typing import Optional, Any, Tuple, List
from databricks.sdk import WorkspaceClient
# Helper to parse messy JSON-like strings safely
def parse_messy_list(raw_text: str) -> List[str]:
    if not raw_text or raw_text == "NULL" or raw_text.strip() == "":
        return []
    # Attempt parsing as a real JSON array
    try:
        parsed = json.loads(raw_text)
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if item]
    except Exception:
        pass
    # Fallback parsing: strip brackets, split on commas, strip quotes
    cleaned = raw_text.strip("[]' \"")
    # Simple regex to split by commas outside quotes
    items = [item.strip().strip("'\" ") for item in re.split(r',(?=(?:[^\'\"]*\'[^\']*\')*[^\']*$)', cleaned)]
    return [item for item in items if item]

# Helper to filter out descriptive junk from actual medical capabilities
def clean_and_split_capabilities(items: List[str]) -> Tuple[List[str], List[str]]:
    capabilities = []
    descriptions = []
    noise_keywords = [
        "located in", "established in", "partnership with", "operating since", 
        "years in healthcare", "private, paid", "sanchalit", "trust sanchalit", 
        "operating for", "established by"
    ]
    
    for item in items:
        item_lower = item.lower()
        # If it has descriptive keywords or is a long sentence (> 90 chars), classify as historical description
        if any(kw in item_lower for kw in noise_keywords) or len(item) > 90:
            descriptions.append(item)
        else:
            capabilities.append(item)
    return capabilities, descriptions

# Helper to call Databricks Foundation Model Serving for semantic auditing
def run_ai_audit(w: WorkspaceClient, description: str, capability: str) -> str:
    try:
        # Prompt for Llama-3 semantic contradiction check
        prompt = (
            f"You are an expert healthcare data quality auditor. Analyze the following unstructured facility description "
            f"and verify if it logically contradicts the stated capabilities of the facility.\n\n"
            f"Description: {description}\n"
            f"Stated Capabilities: {capability}\n\n"
            f"Analyze carefully. If the description lacks details, that is a gap, not a contradiction. "
            f"If the description directly claims services/infrastructure (like an ICU or Trauma Center) "
            f"but the capability fields do not list them, or vice versa, flag it as a contradiction.\n\n"
            f"Respond in exactly this format:\n"
            f"VERDICT: [CONTRADICTION DETECTED or NO CONTRADICTION DETECTED]\n"
            f"REASON: [Your 1-sentence reason]"
        )
        
        response = w.serving_endpoints.query(
            name="databricks-meta-llama-3-1-70b-instruct",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Parse choices safely
        if response and hasattr(response, 'choices') and response.choices:
            return response.choices[0].message.content
        elif response and 'choices' in response:
            return response['choices'][0]['message']['content']
        return str(response)
    except Exception as e:
        return f"Databricks Serving Error: {e}"

# Helper to render clean columns of bullet points in Streamlit
def render_list_in_cols(items: List[str], title_if_empty: str = "No entries listed."):
    if not items:
        st.write(f"*{title_if_empty}*")
        return
    
    # Split list into 2 columns for a tighter, cleaner layout
    col_a, col_b = st.columns(2)
    half = (len(items) + 1) // 2
    
    with col_a:
        for item in items[:half]:
            st.markdown(f"- {item}")
    with col_b:
        for item in items[half:]:
            st.markdown(f"- {item}")



# Set up Streamlit page config
st.set_page_config(
    page_title="India Healthcare Data Readiness Desk",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Databricks Workspace Client
@st.cache_resource
def get_workspace_client() -> Optional[WorkspaceClient]:
    try:
        # Programmatically reads local env variables when running inside Databricks App
        return WorkspaceClient()
    except Exception as e:
        st.error(f"Failed to authenticate with Databricks SDK: {e}")
        return None

# Discover the SQL Warehouse ID programmatically
@st.cache_data
def get_warehouse_id() -> Optional[str]:
    w = get_workspace_client()
    if not w:
        return None
    try:
        # Fetch first available SQL warehouse
        for wh in w.warehouses.list():
            if wh.state.name in ["RUNNING", "STARTING", "STOPPED"]:
                return wh.id
    except Exception as e:
        st.sidebar.error(f"Error finding SQL Warehouse: {e}")
    return None

# Helper to run any SQL statement with synchronous polling
def run_sql_statement(w: WorkspaceClient, warehouse_id: str, sql_query: str) -> Optional[Any]:
    try:
        response = w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=sql_query
        )
        
        # Poll statement status to avoid asynchronous race conditions
        statement_id = response.statement_id
        state = response.status.state.name
        
        while state in ["PENDING", "RUNNING"]:
            time.sleep(1)
            status_resp = w.statement_execution.get_statement(statement_id=statement_id)
            state = status_resp.status.state.name
            if state == "SUCCEEDED":
                return status_resp
            elif state in ["FAILED", "CANCELED"]:
                error_msg = status_resp.status.error.message if status_resp.status.error else "Unknown error"
                raise Exception(f"Statement failed with state {state}: {error_msg}")
                
        return response
    except Exception as e:
        st.error(f"SQL Execution Error: {e}")
        return None

# Helper to fetch query results into a DataFrame with type safety
def run_sql_query(w: WorkspaceClient, warehouse_id: str, sql_query: str) -> pd.DataFrame:
    response = run_sql_statement(w, warehouse_id, sql_query)
    if not response or not response.manifest or not response.manifest.schema:
        return pd.DataFrame()
    
    columns = [col.name for col in response.manifest.schema.columns]
    rows = []
    if response.result and response.result.data_array:
        rows.extend(response.result.data_array)
        
    next_chunk = response.result.next_chunk_index if response.result else None
    statement_id = response.statement_id
    
    while next_chunk:
        try:
            chunk_resp = w.statement_execution.get_statement_result_chunk(
                statement_id=statement_id,
                chunk_index=next_chunk
            )
            if chunk_resp.data_array:
                rows.extend(chunk_resp.data_array)
            next_chunk = chunk_resp.next_chunk_index if chunk_resp else None
        except Exception:
            break
            
    return pd.DataFrame(rows, columns=columns)

# Self-initialize the Gold Table on Databricks if not exists
def initialize_gold_table(w: WorkspaceClient, warehouse_id: str) -> None:
    # Check if table exists
    check_query = "SELECT 1 FROM workspace.information_schema.tables WHERE table_schema='default' AND table_name='gold_flagged_facilities' LIMIT 1"
    df = run_sql_query(w, warehouse_id, check_query)
    
    if df.empty:
        st.info("🔄 First time launch: Ingesting and building Gold Validation Table inside Databricks default schema...")
        
        # Complete pipeline query running on Serverless SQL Warehouses + Inject Mock Contradictions for Demo
        setup_query = """
        CREATE TABLE IF NOT EXISTS workspace.default.gold_flagged_facilities AS
        SELECT
          unique_id,
          name,
          address_city,
          address_stateOrRegion,
          description,
          capability,
          procedure,
          equipment,
          numberDoctors,
          capacity,
          latitude,
          longitude,
          
          -- Contradiction Rule 1: Claimed ICU but missing bed capacity
          CASE
            WHEN (capability ILIKE '%ICU%' OR description ILIKE '%ICU%') 
                 AND (capacity IS NULL OR capacity = '0' OR capacity = '') THEN 1
            ELSE 0
          END as flag_icu_no_capacity,

          -- Contradiction Rule 2: Claimed emergency/trauma but zero/null doctors
          CASE
            WHEN (capability ILIKE '%emergency%' OR capability ILIKE '%trauma%') 
                 AND (numberDoctors IS NULL OR numberDoctors = '0' OR numberDoctors = '') THEN 1
            ELSE 0
          END as flag_emergency_no_doctors,

          -- Contradiction Rule 3: Surgical procedures claimed but no anesthesia support mentioned
          CASE
            WHEN (procedure ILIKE '%surgery%' OR capability ILIKE '%surgery%') 
                 AND (equipment NOT ILIKE '%anesthe%' AND equipment NOT ILIKE '%ventilator%' AND description NOT ILIKE '%anesthe%') THEN 1
            ELSE 0
          END as flag_surgery_no_anesthesia,

          -- Contradiction Rule 4: Critical Data Desert (completely empty meta metrics)
          CASE
            WHEN capacity IS NULL AND numberDoctors IS NULL AND yearEstablished IS NULL THEN 1
            ELSE 0
          END as flag_data_desert,

          -- Compute a Weighted Trust Score (0 - 100)
          100 - (
            (CASE WHEN (capability ILIKE '%ICU%' OR description ILIKE '%ICU%') AND (capacity IS NULL OR capacity = '0' OR capacity = '') THEN 30 ELSE 0 END) +
            (CASE WHEN (capability ILIKE '%emergency%' OR capability ILIKE '%trauma%') AND (numberDoctors IS NULL OR numberDoctors = '0' OR numberDoctors = '') THEN 35 ELSE 0 END) +
            (CASE WHEN (procedure ILIKE '%surgery%' OR capability ILIKE '%surgery%') AND (equipment NOT ILIKE '%anesthe%' AND equipment NOT ILIKE '%ventilator%' AND description NOT ILIKE '%anesthe%') THEN 20 ELSE 0 END) +
            (CASE WHEN capacity IS NULL AND numberDoctors IS NULL AND yearEstablished IS NULL THEN 15 ELSE 0 END)
          ) as trust_score,

          'PENDING' as review_status,
          CAST(NULL as string) as reviewer_notes
        FROM databricks_virtue_foundation_dataset_dais_2026.virtue_foundation_dataset.facilities
        
        UNION ALL
        
        -- Injected Mock Contradiction 1: ICU Beds Mismatch
        SELECT
          'MOCK-ICU-BED-FAIL' as unique_id,
          'Fake Apollo Super-Specialty ICU Center' as name,
          'Delhi' as address_city,
          'Delhi' as address_stateOrRegion,
          'Leading private facility boasting a massive, world-class 50-bed Intensive Care Unit (ICU) with around-the-clock intensive care services, state-of-the-art life support, and highly qualified cardiologists.' as description,
          'ICU, Cardiology, Emergency' as capability,
          'ICU Admission, Ventilation' as procedure,
          'Defibrillator, ECG' as equipment,
          '12' as numberDoctors,
          '0' as capacity, -- CONTRADICTION: Claims 50 ICU beds but capacity is 0!
          28.6139 as latitude,
          77.2090 as longitude,
          1 as flag_icu_no_capacity,
          0 as flag_emergency_no_doctors,
          0 as flag_surgery_no_anesthesia,
          0 as flag_data_desert,
          70 as trust_score,
          'PENDING' as review_status,
          CAST(NULL as string) as reviewer_notes
          
        UNION ALL
        
        -- Injected Mock Contradiction 2: Emergency Care No Doctors
        SELECT
          'MOCK-EMERG-DOC-FAIL' as unique_id,
          'Patna 24/7 Trauma and Acute Emergency Center' as name,
          'Patna' as address_city,
          'Bihar' as address_stateOrRegion,
          'A prominent regional trauma center offering 24/7 emergency surgeries, disaster response units, and acute triage. Ready to handle major road accidents, fractures, and cardiac arrests at any hour of the night.' as description,
          'Emergency Care, Trauma Surgery, Triage' as capability,
          'Triage, Fracture Splinting' as procedure,
          'Oxygen Cylinders, Stretcher' as equipment,
          '0' as numberDoctors, -- CONTRADICTION: 24/7 emergency trauma but 0 doctors!
          '15' as capacity,
          25.5941 as latitude,
          85.1376 as longitude,
          0 as flag_icu_no_capacity,
          1 as flag_emergency_no_doctors,
          0 as flag_surgery_no_anesthesia,
          0 as flag_data_desert,
          65 as trust_score,
          'PENDING' as review_status,
          CAST(NULL as string) as reviewer_notes
          
        UNION ALL
        
        -- Injected Mock Contradiction 3: Surgery No Anesthesia Support
        SELECT
          'MOCK-SURG-ANES-FAIL' as unique_id,
          'Jaipur Royal General and Open-Heart Surgery Clinic' as name,
          'Jaipur' as address_city,
          'Rajasthan' as address_stateOrRegion,
          'Boutique private surgical clinic specializing in complex open-heart surgeries, tumor removals, and orthopedic bypass operations. Fully equipped operation theaters available.' as description,
          'Cardio-thoracic Surgery, General Surgery' as capability,
          'Coronary Artery Bypass, Appendectomy' as procedure,
          'Scalpels, Surgical Lamps, Forceps' as equipment, -- CONTRADICTION: Major open-heart surgery but no anesthesia or ventilator!
          '5' as numberDoctors,
          '10' as capacity,
          26.9124 as latitude,
          75.7873 as longitude,
          0 as flag_icu_no_capacity,
          0 as flag_emergency_no_doctors,
          1 as flag_surgery_no_anesthesia,
          0 as flag_data_desert,
          80 as trust_score,
          'PENDING' as review_status,
          CAST(NULL as string) as reviewer_notes
        """
        run_sql_statement(w, warehouse_id, setup_query)
        st.success("✅ Gold Table Initialized successfully!")

# Load Data from Gold Table with Strict Type Enforcement and Schema Castings
@st.cache_data
def load_gold_data(warehouse_id: str) -> pd.DataFrame:
    w = get_workspace_client()
    if not w or not warehouse_id:
        return pd.DataFrame()
    
    initialize_gold_table(w, warehouse_id)
    query = "SELECT * FROM workspace.default.gold_flagged_facilities"
    df = run_sql_query(w, warehouse_id, query)
    
    if not df.empty:
        # Enforce strict pandas data types and schema handling to avoid type mismatches during Streamlit rendering
        df['unique_id'] = df['unique_id'].astype(str)
        df['name'] = df['name'].fillna("Unknown").astype(str)
        df['address_city'] = df['address_city'].fillna("Unknown").astype(str)
        df['address_stateOrRegion'] = df['address_stateOrRegion'].fillna("Unknown").astype(str)
        df['description'] = df['description'].fillna("").astype(str)
        df['capability'] = df['capability'].fillna("").astype(str)
        df['procedure'] = df['procedure'].fillna("").astype(str)
        df['equipment'] = df['equipment'].fillna("").astype(str)
        
        # Convert meta strings to numeric types with safe NaN/None handling
        df['numberDoctors'] = pd.to_numeric(df['numberDoctors'], errors='coerce').fillna(0).astype(int)
        df['capacity'] = pd.to_numeric(df['capacity'], errors='coerce').fillna(0).astype(int)
        
        # Strict validation flags casting (Integer boolean mapping)
        df['flag_icu_no_capacity'] = pd.to_numeric(df['flag_icu_no_capacity'], errors='coerce').fillna(0).astype(int)
        df['flag_emergency_no_doctors'] = pd.to_numeric(df['flag_emergency_no_doctors'], errors='coerce').fillna(0).astype(int)
        df['flag_surgery_no_anesthesia'] = pd.to_numeric(df['flag_surgery_no_anesthesia'], errors='coerce').fillna(0).astype(int)
        df['flag_data_desert'] = pd.to_numeric(df['flag_data_desert'], errors='coerce').fillna(0).astype(int)
        
        # Trust score evaluation casting
        df['trust_score'] = pd.to_numeric(df['trust_score'], errors='coerce').fillna(100).astype(int)
        
        # Triage status and text notes casting
        df['review_status'] = df['review_status'].fillna("PENDING").astype(str)
        df['reviewer_notes'] = df['reviewer_notes'].fillna("").astype(str)
        
        # Geo-casting for maps
        if 'latitude' in df.columns and 'longitude' in df.columns:
            df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
            df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
        
    return df

# Main logic
w = get_workspace_client()
warehouse_id = get_warehouse_id()

if not w or not warehouse_id:
    st.error("🔌 Unable to connect to Databricks SQL Serverless Compute. Ensure your app is deployed on Databricks or you are configured locally.")
else:
    # Title Section
    st.title("🏥 India Healthcare Data Readiness Desk")
    st.markdown("### *Databricks Intelligence Platform: Automating Ground-Truth Validation for Healthcare Infrastructure*")
    st.markdown("---")

    # Load and cache main data
    df_raw = load_gold_data(warehouse_id)
    
    if df_raw.empty:
        st.warning("⚠️ No records loaded. Verify your Shared Catalog access or SQL Warehouse status.")
    else:
        # SIDEBAR FILTERS
        st.sidebar.header("🔍 Filters")
        
        # Region filter
        regions = sorted(list(df_raw['address_stateOrRegion'].dropna().unique()))
        selected_region = st.sidebar.selectbox("Select State / Region", ["All"] + regions)
        
        # Status Filter
        status_filter = st.sidebar.radio("Review Status", ["All", "PENDING", "APPROVED", "FLAGGED"])
        
        # Slider for Trust Score
        score_range = st.sidebar.slider("Trust Score Range", 0, 100, (0, 100))
        
        # Filter checkboxes for specific flags
        st.sidebar.subheader("Filter by flag:")
        icu_flag = st.sidebar.checkbox("ICU Claim Conflict")
        emergency_flag = st.sidebar.checkbox("Emergency Claim Conflict")
        anesthesia_flag = st.sidebar.checkbox("Surgical Anesthesia Conflict")
        desert_flag = st.sidebar.checkbox("Critical Data Desert")
        
        # Reset Demo Database button
        st.sidebar.markdown("---")
        st.sidebar.subheader("🛠️ Demo Management")
        if st.sidebar.button("⚠️ Reset Demo Database", use_container_width=True, type="secondary"):
            with st.spinner("Dropping table and resetting demo state..."):
                run_sql_statement(w, warehouse_id, "DROP TABLE IF EXISTS workspace.default.gold_flagged_facilities")
                st.cache_data.clear()
            st.sidebar.success("Database Reset! Refreshing page...")
            st.rerun()
        
        # Apply filters
        df = df_raw.copy()
        if selected_region != "All":
            df = df[df['address_stateOrRegion'] == selected_region]
        if status_filter != "All":
            df = df[df['review_status'] == status_filter]
            
        df = df[(df['trust_score'] >= score_range[0]) & (df['trust_score'] <= score_range[1])]
        
        if icu_flag:
            df = df[df['flag_icu_no_capacity'] == 1]
        if emergency_flag:
            df = df[df['flag_emergency_no_doctors'] == 1]
        if anesthesia_flag:
            df = df[df['flag_surgery_no_anesthesia'] == 1]
        if desert_flag:
            df = df[df['flag_data_desert'] == 1]

        # METRICS DASHBOARD ROW
        col1, col2, col3, col4 = st.columns(4)
        
        total_rec = len(df)
        pending_rec = len(df[df['review_status'] == 'PENDING'])
        approved_rec = len(df[df['review_status'] == 'APPROVED'])
        flagged_rec = len(df[df['review_status'] == 'FLAGGED'])
        
        with col1:
            st.metric("📋 Total Records (Filtered)", f"{total_rec:,}")
        with col2:
            st.metric("⏳ Pending Triage", f"{pending_rec:,}", delta=f"{pending_rec} remaining", delta_color="inverse")
        with col3:
            st.metric("✅ Approved Data", f"{approved_rec:,}")
        with col4:
            st.metric("🔴 Flagged Contradictions", f"{flagged_rec:,}")

        st.markdown("---")
        
        # --- TAB LAYOUT (No Emojis) ---
        tab_queue, tab_map = st.tabs(["Audit and Triage Queue", "Geographic Desert Map"])
        
        with tab_queue:
            # PLOTS & CHARTS PANEL
            c_left, c_right = st.columns(2)
        
            with c_left:
                st.subheader("Trust Score Distribution")
                fig_hist = px.histogram(df, x="trust_score", nbins=20, labels={'trust_score': 'Trust Score'}, 
                                        color_discrete_sequence=['#1f77b4'], title="Facility Trust Assessment Profile")
                st.plotly_chart(fig_hist, use_container_width=True)
            
            with c_right:
                st.subheader("Flag Prevalence")
                flag_counts = pd.DataFrame({
                    'Flag Type': ['ICU Beds Missing', 'Emergency No Doctors', 'Surgical No Anesthesia', 'Data Desert'],
                    'Count': [
                        df['flag_icu_no_capacity'].sum(),
                        df['flag_emergency_no_doctors'].sum(),
                        df['flag_surgery_no_anesthesia'].sum(),
                        df['flag_data_desert'].sum()
                    ]
                })
                fig_bar = px.bar(flag_counts, x="Flag Type", y="Count", color="Flag Type",
                                 title="Prevalence of Contradictions Found",
                                 color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig_bar, use_container_width=True)

            st.markdown("---")

            # TRIAGE QUEUE & WORKFLOW
            st.subheader("🚨 The Triage Queue (Sorted by lowest trust)")
        
            # Display search-ready list of messy/flagged facilities
            df_display = df[['unique_id', 'name', 'address_city', 'address_stateOrRegion', 'trust_score', 'review_status']].sort_values(by='trust_score')
        
            def color_trust_score(val):
                if val < 70:
                    return 'background-color: #ffcccc; color: #990000; font-weight: bold'
                elif val < 90:
                    return 'background-color: #fff4cc; color: #886600'
                return 'background-color: #ccffcc; color: #006600'
            
            styled_df = df_display.style.map(color_trust_score, subset=['trust_score'])
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
            st.markdown("---")
        
            # DETAIL INSPECTOR AND ACTION PANEL
            st.subheader("🔍 Selected Facility Deep Audit & Traceability")
        
            # Allow user to pick a facility ID
            search_options = df_display['unique_id'].tolist()
            if search_options:
                selected_id = st.selectbox("Choose Facility Unique ID to Audit:", search_options)
            
                # Fetch single selected record details
                facility = df[df['unique_id'] == selected_id].iloc[0]
            
                # FULL ROW: Key Identification
                st.markdown(f"### {facility['name']}")
                st.markdown(f"**Location**: {facility['address_city']}, {facility['address_stateOrRegion']}")
                st.markdown(
                    f"**Computed Trust Score**: `{facility['trust_score']}/100` "
                    f'<span title="Base 100. Deductions: ICU missing beds (-30), Trauma missing doctors (-35), Surgery missing anesthesia (-20), Complete Data Desert (-15).">ℹ️</span>',
                    unsafe_allow_html=True
                )
                st.markdown(f"**Current Status**: `{facility['review_status']}`")
                st.markdown("<br>", unsafe_allow_html=True)
            
                # TWO COLUMNS: Unstructured Notes vs Warnings
                d_col1, d_col2 = st.columns(2)
            
                with d_col1:
                    st.markdown("#### Raw Facility Description (Unstructured Note):")
                    st.info(facility['description'] if facility['description'] else "No description available.")
                
                with d_col2:
                    # Render active flags clearly without emojis in the title
                    st.markdown("#### Active Trust Warnings:")
                    active_flags = False
                    if facility['flag_icu_no_capacity'] == 1:
                        st.error("ICU Bed Mismatch: Facility claims ICU capability/notes but lists 0 or NULL bed capacity.")
                        active_flags = True
                    if facility['flag_emergency_no_doctors'] == 1:
                        st.error("Emergency Mismatch: Facility claims emergency/trauma but lists 0 or NULL doctors.")
                        active_flags = True
                    if facility['flag_surgery_no_anesthesia'] == 1:
                        st.error("Anesthesia Gap: Complex surgeries/procedures are listed but no Anesthesia or Ventilator equipment found.")
                        active_flags = True
                    if facility['flag_data_desert'] == 1:
                        st.warning("Data Desert Alert: No structural metrics (established year, capacity, doctors) available for validation.")
                        active_flags = True
                    
                    if not active_flags:
                        st.success("Clean Record: No contradictions detected by the automated data readiness pipeline.")

                # FULL ROW: Structured Claims with Expanders and On-The-Fly Cleaning
                st.markdown("---")
                st.markdown("#### Structured Claims:")
                st.write(f"- **Bed Capacity Claim**: `{facility['capacity'] or 'NULL'}`")
                st.write(f"- **Doctors Count**: `{facility['numberDoctors'] or 'NULL'}`")
            
                # Parse lists
                raw_capabilities = parse_messy_list(facility['capability'])
                raw_procedures = parse_messy_list(facility['procedure'])
                raw_equipment = parse_messy_list(facility['equipment'])
            
                # Separate descriptive junk from true capabilities
                vetted_capabilities, history_descriptions = clean_and_split_capabilities(raw_capabilities)
            
                with st.expander("View Services & Capabilities (Cleaned)"):
                    if vetted_capabilities:
                        render_list_in_cols(vetted_capabilities)
                    if history_descriptions:
                        st.markdown("<br>**Facility Descriptive & Historical Context:**", unsafe_allow_html=True)
                        for desc in history_descriptions:
                            st.info(desc)
                    
                with st.expander("View Procedures Listed"):
                    render_list_in_cols(raw_procedures, "No procedures listed.")
                
                with st.expander("View Equipment Claimed"):
                    render_list_in_cols(raw_equipment, "No equipment listed.")

                st.markdown("---")
            
                # THE DECISION DESK (Human-In-The-Loop Writeback)
                st.subheader("✍️ The Decision Desk (Lakebase Persistence)")
            
                current_notes = facility['reviewer_notes'] if pd.notna(facility['reviewer_notes']) else ""
                reviewer_notes = st.text_area("Write Reviewer Notes & Audit Evidence Here:", value=current_notes)
            
                act_col1, act_col2, act_col3 = st.columns(3)
            
                with act_col1:
                    if st.button("✅ Approve Facility Data", use_container_width=True):
                        # SQL Update Query
                        escaped_notes = reviewer_notes.replace("'", "''")
                        update_query = f"UPDATE workspace.default.gold_flagged_facilities SET review_status = 'APPROVED', reviewer_notes = '{escaped_notes}' WHERE unique_id = '{selected_id}'"
                        with st.spinner("Writing back to Unity Catalog..."):
                            run_sql_statement(w, warehouse_id, update_query)
                        st.success("Facility data approved successfully!")
                        st.cache_data.clear() # Clear cache to refresh values instantly on reload
                        st.rerun()
                    
                with act_col2:
                    if st.button("🔴 Flag as Suspicious / Fraudulent", use_container_width=True):
                        escaped_notes = reviewer_notes.replace("'", "''")
                        update_query = f"UPDATE workspace.default.gold_flagged_facilities SET review_status = 'FLAGGED', reviewer_notes = '{escaped_notes}' WHERE unique_id = '{selected_id}'"
                        with st.spinner("Flagging record..."):
                            run_sql_statement(w, warehouse_id, update_query)
                        st.error("Facility flagged for review!")
                        st.cache_data.clear()
                        st.rerun()
                    
                with act_col3:
                    if st.button("📝 Save Internal Notes Only", use_container_width=True):
                        escaped_notes = reviewer_notes.replace("'", "''")
                        update_query = f"UPDATE workspace.default.gold_flagged_facilities SET reviewer_notes = '{escaped_notes}' WHERE unique_id = '{selected_id}'"
                        with st.spinner("Saving note..."):
                            run_sql_statement(w, warehouse_id, update_query)
                        st.success("Reviewer notes saved successfully!")
                        st.cache_data.clear()
                        st.rerun()
            else:
                st.info("No records matching the current filters are available in the Triage Queue.")

        with tab_map:
            st.subheader("High-Risk Vulnerability Map")
            st.markdown("Visualizing computed trust scores and Data Deserts across India to aid public health planners.")
            
            if 'latitude' in df.columns and 'longitude' in df.columns:
                # Drop rows without coords
                df_map = df.dropna(subset=['latitude', 'longitude'])
                
                if not df_map.empty:
                    # Define strict hex colors for native Streamlit Map
                    def get_map_color(row):
                        if row['flag_data_desert'] == 1:
                            return '#808080' # Gray (Data Desert)
                        elif row['review_status'] == 'FLAGGED':
                            return '#000000' # Black (Flagged)
                        elif row['trust_score'] < 70:
                            return '#FF4B4B' # Red (High Risk)
                        elif row['review_status'] == 'APPROVED':
                            return '#00CC96' # Green (Approved)
                        else:
                            return '#1f77b4' # Blue (Normal)
                            
                    df_map['color'] = df_map.apply(get_map_color, axis=1)
                    
                    # Render Streamlit Native Map - 100% immune to Mapbox CDN/firewall blocks
                    st.map(
                        df_map, 
                        latitude="latitude", 
                        longitude="longitude", 
                        color="color", 
                        size=25,
                        use_container_width=True
                    )
                else:
                    st.warning("No coordinates available for the filtered subset.")
            else:
                st.error("Latitude and Longitude coordinates not available in the current dataset schema.")
