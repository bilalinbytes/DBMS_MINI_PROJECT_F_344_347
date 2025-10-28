# CareerSphere/pages/admin_dashboard.py (INTEGRATED VERSION with Analytics Tab)

import streamlit as st
import pandas as pd
from database import execute_query

# --- ANALYTICS TAB CONTENT (Moved from analytics.py) ---
def analytics_tab(conn, db_type):
    st.subheader("📊 System Analytics & DBMS Verification")
    st.caption("Data-Driven Insights and DBMS Feature Checks (Stored Procedures, Triggers)")
    st.markdown("---")

    # --- 1. Stored Procedure Verification ---
    st.header("Stored Procedure Check: Application Count")
    
    jobs_query = "SELECT id, title FROM jobs"
    jobs = execute_query(conn, jobs_query, fetch=True)
    
    if jobs:
        # Map job titles to IDs
        job_options = {job['title']: job['id'] for job in jobs}
        selected_title = st.selectbox("Select a Job to Check Application Count", list(job_options.keys()))
        selected_job_id = job_options[selected_title]

        if st.button("Run Stored Procedure"):
            if db_type == 'mysql':
                # MySQL Stored Procedure Call
                try:
                    # NOTE: This part assumes your 'database.py' manages the cursor correctly
                    # For mysql.connector, you often need to fetch the result from the next object
                    cursor = conn.cursor()
                    cursor.callproc('get_application_count', (selected_job_id, 0)) # 0 is placeholder for OUT param
                    
                    # Retrieve the result set (which contains the OUT variable value)
                    # Iterate through the stored results, usually the last one has the OUT param
                    total_apps = None
                    for result in cursor.stored_results():
                        data = result.fetchone()
                        if data and 'total_apps' in data:
                            total_apps = data['total_apps']
                        elif data and isinstance(data, tuple) and len(data) > 0: # Basic tuple check if dict wasn't returned
                             total_apps = data[0]

                    if total_apps is not None:
                        st.success(f"✅ **Stored Procedure Verified:** Job '{selected_title}' (ID: {selected_job_id}) has **{total_apps}** applications.")
                    else:
                         st.warning("Stored Procedure ran, but could not retrieve application count result.")
                    
                    cursor.close()
                except Exception as e:
                    st.error(f"Failed to execute Stored Procedure: {e}. Ensure DDL_DML.sql was run correctly.")
            else:
                # SQLite fallback: directly execute the logic
                count_query = "SELECT COUNT(*) FROM applications WHERE job_id = ?"
                result = execute_query(conn, count_query, (selected_job_id,), fetch=True)
                total_apps = result[0][0] if result and result[0] else 0
                st.info(f"Using SQLite Fallback Logic: Job '{selected_title}' (ID: {selected_job_id}) has **{total_apps}** applications.")
    else:
        st.info("No jobs available to check.")

    st.markdown("---")

    # --- 2. Streamlit Charts: Application Status Distribution ---
    st.header("Application Status Distribution")

    status_query = "SELECT status, COUNT(*) as count FROM applications GROUP BY status"
    status_data = execute_query(conn, status_query, fetch=True)
    
    if status_data:
        # Handle tuple-based data from execute_query if it doesn't return dicts
        if isinstance(status_data[0], tuple):
            status_df = pd.DataFrame(status_data, columns=['status', 'count'])
        else:
            status_df = pd.DataFrame(status_data)

        st.bar_chart(status_df, x='status', y='count')
        st.dataframe(status_df, use_container_width=True)
    else:
        st.info("No applications submitted yet to generate charts.")
        
    st.markdown("---")

    # --- 3. Streamlit Charts: Student CGPA Distribution ---
    st.header("Student Profile CGPA Distribution")
    cgpa_query = "SELECT cgpa FROM students WHERE cgpa IS NOT NULL"
    cgpa_data = execute_query(conn, cgpa_query, fetch=True)

    if cgpa_data:
        # Extract CGPA values, handling potential Decimal/None types
        cgpa_list = [float(d.get('cgpa')) for d in cgpa_data if d.get('cgpa') is not None]
        if cgpa_list:
            cgpa_df = pd.DataFrame({'CGPA': cgpa_list})
            # Use st.bar_chart for histograms in Streamlit (it handles binning)
            st.bar_chart(cgpa_df, y='CGPA')
        else:
            st.info("CGPA data found, but all values are null or invalid.")
    else:
        st.info("No student CGPA data available yet.")


# --- MAIN ADMIN DASHBOARD ---
def admin_dashboard():
    # --- Access Control ---
    if not st.session_state.get('logged_in') or st.session_state.get('user_role') != 'admin':
        st.error("Access Denied. Please login as an Admin.")
        st.stop()

    conn = st.session_state['db_conn']
    db_type = st.session_state['db_type']
    
    st.title("🧑‍🏫 Admin Dashboard")
    st.subheader("System Overview and Management")
    st.markdown("---")

    # Create tabs for better organization
    dashboard_tab, analytics_tab_btn, user_tab = st.tabs(["Overview & Metrics", "Analytics & DBMS Check", "User Management"])

    # --- Overview & Metrics Tab ---
    with dashboard_tab:
        st.header("Key System Metrics")
        
        # Get Counts (Optimized for both DB types)
        metrics_query = """
        SELECT
            (SELECT COUNT(*) FROM users WHERE role='student') AS total_students,
            (SELECT COUNT(*) FROM users WHERE role='recruiter') AS total_recruiters,
            (SELECT COUNT(*) FROM jobs) AS total_jobs,
            (SELECT COUNT(*) FROM applications) AS total_applications
        """
        
        metrics = {}
        if db_type == 'sqlite': # SQLite requires separate queries
            # Use a safe way to get the count result
            metrics['total_students'] = execute_query(conn, "SELECT COUNT(*) FROM users WHERE role='student'")[0][0]
            metrics['total_recruiters'] = execute_query(conn, "SELECT COUNT(*) FROM users WHERE role='recruiter'")[0][0]
            metrics['total_jobs'] = execute_query(conn, "SELECT COUNT(*) FROM jobs")[0][0] if execute_query(conn, "SELECT COUNT(*) FROM jobs") else 0
            metrics['total_applications'] = execute_query(conn, "SELECT COUNT(*) FROM applications")[0][0] if execute_query(conn, "SELECT COUNT(*) FROM applications") else 0
        else: # MySQL
            metrics_data = execute_query(conn, metrics_query, fetch=True)
            if metrics_data:
                 metrics = metrics_data[0]


        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Students", metrics.get('total_students', 0))
        col2.metric("Recruiters", metrics.get('total_recruiters', 0))
        col3.metric("Jobs Posted", metrics.get('total_jobs', 0))
        col4.metric("Applications", metrics.get('total_applications', 0))
        
        st.markdown("---")

        # 2. View Audit Logs (Trigger Verification)
        st.subheader("System Audit Logs (Trigger Check)")
        audit_query = "SELECT created_at, action, entity, entity_id, user_email FROM audit_logs ORDER BY created_at DESC LIMIT 10"
        logs = execute_query(conn, audit_query, fetch=True)
        
        if logs:
            st.dataframe(pd.DataFrame(logs), use_container_width=True)
            st.info("✅ **Trigger Verified:** The log above shows actions recorded automatically (e.g., job creation).")
        else:
            st.info("No audit logs yet. Try posting a job as a recruiter to test the trigger!")

    # --- Analytics & DBMS Check Tab ---
    with analytics_tab_btn:
        analytics_tab(conn, db_type) # Call the integrated analytics function

    # --- User Management Tab (Placeholder) ---
    with user_tab:
        st.header("User Management")
        st.info("Use this tab to approve new recruiters or block inactive users.")
        # Placeholder for future User Management UI/Logic
        
        # 1. Manage Recruiters (Approve/Block)
        st.button("Go to Recruiter Approval Interface (Future Feature)", key="manage_rec", disabled=True)
        st.button("Manage Students (Future Feature)", key="manage_student", disabled=True)

admin_dashboard()