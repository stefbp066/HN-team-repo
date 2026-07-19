import streamlit as st
import pandas as pd
import plotly.express as px
import time
from databricks.sdk import WorkspaceClient

# Set up Streamlit page config
st.set_page_config(
    page_title="India Healthcare Data Readiness Desk",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Databricks Workspace Client
@st.cache_resource
def get_workspace_client():
    try:
        # Programmatically reads local env variables when running inside Databricks App
        return WorkspaceClient()
    except Exception as e:
        st.error(f"Failed to authenticate with Databricks SDK: {e}")
        return None

# Discover the SQL Warehouse ID programmatically
@st.cache_data
def get_warehouse_id():
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
def run_sql_statement(w, warehouse_id, sql_query):
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

# Helper to fetch query results into a DataFrame
def run_sql_query(w, warehouse_id, sql_query):
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
def initialize_gold_table(w, warehouse_id):
    # Check if table exists
    check_query = "SELECT 1 FROM workspace.information_schema.tables WHERE table_schema='default' AND table_name='gold_flagged_facilities' LIMIT 1"
    df = run_sql_query(w, warehouse_id, check_query)
    
    if df.empty:
        st.info("🔄 First time launch: Ingesting and building Gold Validation Table inside Databricks default schema...")
        
        # Complete pipeline query running on Serverless SQL Warehouses
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
        """
        run_sql_statement(w, warehouse_id, setup_query)
        st.success("✅ Gold Table Initialized successfully!")

# Load Data from Gold Table
@st.cache_data
def load_gold_data(warehouse_id):
    w = get_workspace_client()
    if not w or not warehouse_id:
        return pd.DataFrame()
    
    initialize_gold_table(w, warehouse_id)
    query = "SELECT * FROM workspace.default.gold_flagged_facilities"
    df = run_sql_query(w, warehouse_id, query)
    
    if not df.empty:
        # Cast data types correctly
        df['trust_score'] = pd.to_numeric(df['trust_score'], errors='coerce').fillna(100).astype(int)
        df['flag_icu_no_capacity'] = pd.to_numeric(df['flag_icu_no_capacity'], errors='coerce').fillna(0).astype(int)
        df['flag_emergency_no_doctors'] = pd.to_numeric(df['flag_emergency_no_doctors'], errors='coerce').fillna(0).astype(int)
        df['flag_surgery_no_anesthesia'] = pd.to_numeric(df['flag_surgery_no_anesthesia'], errors='coerce').fillna(0).astype(int)
        df['flag_data_desert'] = pd.to_numeric(df['flag_data_desert'], errors='coerce').fillna(0).astype(int)
    return df

# Main logic
w = get_workspace_client()
warehouse_id = get_warehouse_id()

if not w or not warehouse_id:
    st.error("🔌 Unable to connect to Databricks SQL Serverless Compute. Ensure your app is deployed on Databricks or you are configured locally.")
else:
    # Title Section
    st.title("🏥 India Healthcare Data Readiness Desk")
    st.markdown("### *Trust Layer & Contradiction Validation Pipeline for 10k Facility Records*")
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
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # DETAIL INSPECTOR AND ACTION PANEL
        st.subheader("🔍 Selected Facility Deep Audit & Traceability")
        
        # Allow user to pick a facility ID
        search_options = df_display['unique_id'].tolist()
        if search_options:
            selected_id = st.selectbox("Choose Facility Unique ID to Audit:", search_options)
            
            # Fetch single selected record details
            facility = df[df['unique_id'] == selected_id].iloc[0]
            
            d_col1, d_col2 = st.columns(2)
            
            with d_col1:
                st.markdown(f"### {facility['name']}")
                st.markdown(f"**📍 Location**: {facility['address_city']}, {facility['address_stateOrRegion']}")
                st.markdown(f"**🛡️ Computed Trust Score**: `{facility['trust_score']}/100`")
                st.markdown(f"**📊 Current Status**: `{facility['review_status']}`")
                
                st.markdown("#### Structured Claims:")
                st.write(f"- 🛌 **Bed Capacity Claim**: `{facility['capacity'] or 'NULL'}`")
                st.write(f"- 🩺 **Doctors Count**: `{facility['numberDoctors'] or 'NULL'}`")
                st.write(f"- 🔬 **Equipment Claimed**: `{facility['equipment'] or 'NULL'}`")
                st.write(f"- 🏥 **Capabilities Stated**: `{facility['capability'] or 'NULL'}`")
                st.write(f"- 💉 **Procedures Listed**: `{facility['procedure'] or 'NULL'}`")
                
            with d_col2:
                st.markdown("#### 📄 Raw Facility Description (Unstructured Note):")
                st.info(facility['description'] if facility['description'] else "No description available.")
                
                # Render active flags clearly
                st.markdown("#### ⚠️ Active Trust Warnings:")
                active_flags = False
                if facility['flag_icu_no_capacity'] == 1:
                    st.error("🚨 **ICU Bed Mismatch**: Facility claims ICU capability/notes but lists 0 or NULL bed capacity!")
                    active_flags = True
                if facility['flag_emergency_no_doctors'] == 1:
                    st.error("🚨 **Emergency Mismatch**: Facility claims emergency/trauma but lists 0 or NULL doctors!")
                    active_flags = True
                if facility['flag_surgery_no_anesthesia'] == 1:
                    st.error("🚨 **Anesthesia Gap**: Complex surgeries/procedures are listed but no Anesthesia or Ventilator equipment found!")
                    active_flags = True
                if facility['flag_data_desert'] == 1:
                    st.warning("⚠️ **Data Desert Alert**: No structural metrics (established year, capacity, doctors) available for validation.")
                    active_flags = True
                    
                if not active_flags:
                    st.success("✅ **Clean Record**: No contradictions detected by the automated data readiness pipeline.")

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
