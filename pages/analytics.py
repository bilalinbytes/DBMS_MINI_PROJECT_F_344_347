import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from database import execute_query

# ==========================================================
# CAREERSPHERE ANALYTICS PAGE
# Shows DBMS feature verification, stored procedures, charts
# ==========================================================

def analytics_page():
    # --- Access Control ---
    if not st.session_state.get('logged_in') or st.session_state.get('user_role') != 'admin':
        st.error("Access Denied. Only Admin can view analytics.")
        st.stop()

    conn = st.session_state['db_conn']
    db_type = st.session_state['db_type']
    
    st.title("📊 System Analytics & DBMS Verification")
    st.subheader("Data-Driven Insights for CareerSphere")
    st.markdown("---")

    # ==========================================================
    # 1️⃣ Stored Procedure Verification: get_application_count
    # ==========================================================
    st.header("Stored Procedure Check: Application Count")
    
    # Fetch jobs to populate dropdown
    jobs_query = "SELECT id, title FROM jobs"
    jobs = execute_query(conn, jobs_query, fetch=True)
    
    if jobs:
        job_options = {job['title']: job['id'] for job in jobs}
        selected_title = st.selectbox("Select a Job to Check Application Count", list(job_options.keys()))
        selected_job_id = job_options[selected_title]

        if st.button("Run Stored Procedure"):
            if db_type == 'mysql':
                try:
                    # ✅ Run MySQL stored procedure
                    cursor = conn.cursor(dictionary=True)
                    cursor.callproc('get_application_count', (selected_job_id, 0))  # IN, OUT
                    # Fetch result
                    result = next(cursor.stored_results()).fetchone()
                    total_apps = result.get('total_apps', 0) if isinstance(result, dict) else result[0]
                    st.success(f"✅ **Stored Procedure Verified:** Job '{selected_title}' (ID: {selected_job_id}) has **{total_apps}** applications.")
                    cursor.close()
                except Exception as e:
                    st.error(f"❌ Failed to execute Stored Procedure: {e}")
                    st.info("Hint: Ensure the procedure 'get_application_count' is created in your database.")
            else:
                # SQLite fallback: emulate logic directly
                count_query = "SELECT COUNT(*) as total FROM applications WHERE job_id = ?"
                result = execute_query(conn, count_query, (selected_job_id,), fetch=True)
                total_apps = result[0]['total'] if isinstance(result[0], dict) else result[0][0]
                st.info(f"Using SQLite fallback: Job '{selected_title}' (ID: {selected_job_id}) has **{total_apps}** applications.")
    else:
        st.info("No jobs available to check application count.")
    
    st.markdown("---")

    # ==========================================================
    # 2️⃣ Application Status Distribution (Trigger Visualization)
    # ==========================================================
    st.header("📈 Application Status Distribution")

    status_query = "SELECT status, COUNT(*) AS count FROM applications GROUP BY status"
    status_data = execute_query(conn, status_query, fetch=True)
    
    if status_data:
        # Convert to DataFrame for Streamlit
        status_df = pd.DataFrame(status_data)
        st.bar_chart(status_df, x='status', y='count', use_container_width=True)
        st.dataframe(status_df, use_container_width=True)
        
        # Optional Pie Chart (looks great for demos)
        st.subheader("📊 Pie Chart Representation")
        fig, ax = plt.subplots()
        ax.pie(status_df['count'], labels=status_df['status'], autopct='%1.1f%%', startangle=90)
        ax.set_title("Application Status Breakdown")
        st.pyplot(fig)
    else:
        st.info("No applications submitted yet to generate charts.")
    
    st.markdown("---")

    # ==========================================================
    # 3️⃣ Student CGPA Distribution (Histogram + Metric)
    # ==========================================================
    st.header("🎓 Student CGPA Distribution")
    cgpa_query = "SELECT cgpa FROM students WHERE cgpa IS NOT NULL"
    cgpa_data = execute_query(conn, cgpa_query, fetch=True)

    if cgpa_data:
        # Extract valid CGPA values
        cgpa_list = [float(d.get('cgpa')) for d in cgpa_data if d.get('cgpa') is not None]

        if cgpa_list:
            fig, ax = plt.subplots()
            ax.hist(cgpa_list, bins=10, color='#2b83ba', edgecolor='white')
            ax.set_title("Student CGPA Distribution")
            ax.set_xlabel("CGPA")
            ax.set_ylabel("Number of Students")
            st.pyplot(fig)

            avg_cgpa = sum(cgpa_list) / len(cgpa_list)
            st.metric("Average CGPA", f"{avg_cgpa:.2f}")
        else:
            st.info("CGPA data found, but all values are null or invalid.")
    else:
        st.info("No student CGPA data available yet.")
    
    st.markdown("---")

    # ==========================================================
    # 4️⃣ Optional: Trigger Verification (Audit Logs)
    # ==========================================================
    st.header("🧾 Trigger Verification Logs")
    logs_query = "SELECT created_at, action, entity, user_email FROM audit_logs ORDER BY created_at DESC LIMIT 10"
    logs = execute_query(conn, logs_query, fetch=True)
    
    if logs:
        st.dataframe(pd.DataFrame(logs), use_container_width=True)
        st.success("✅ Triggers Verified — System automatically records activity in 'audit_logs'.")
    else:
        st.info("No trigger activity yet. Try registering a user or posting a job.")

# Run the page
analytics_page()
