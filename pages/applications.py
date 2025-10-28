# CareerSphere/pages/applications.py

import streamlit as st
import pandas as pd
from database import execute_query

def applications_page():
    # --- Access Control ---
    if not st.session_state.get('logged_in'):
        st.error("Access Denied. Please login.")
        st.stop()

    conn = st.session_state['db_conn']
    db_type = st.session_state['db_type']
    role = st.session_state['user_role']
    user_id = st.session_state['user_id']
    
    st.title("📑 Application Management")
    st.markdown("---")
    
    if role == 'recruiter':
        recruiter_application_review(conn, db_type, user_id)
    elif role == 'student':
        student_application_tracking(conn, db_type, user_id)
    else:
        st.error("Admins should use the Analytics page for application stats.")

# --- Recruiter Functions ---
def recruiter_application_review(conn, db_type, recruiter_id):
    st.header("Review & Update Applicant Status (Update)")

    # 1. Select the job to review
    job_query = "SELECT id, title FROM jobs WHERE recruiter_id = %s" if db_type == 'mysql' else "SELECT id, title FROM jobs WHERE recruiter_id = ?"
    jobs = execute_query(conn, job_query, (recruiter_id,), fetch=True)
    
    if not jobs:
        st.info("You must post a job before reviewing applications.")
        st.stop()
        
    job_options = {job['title']: job['id'] for job in jobs}
    selected_title = st.selectbox("Select Job Posting to Review", list(job_options.keys()))
    selected_job_id = job_options[selected_title]
    
    st.markdown("---")
    
    # 2. Fetch applicants for the selected job
    applicants_query = """
    SELECT 
        a.id AS app_id, s.full_name, s.roll_no, s.branch, s.cgpa, a.status, s.resume_url
    FROM applications a
    JOIN students s ON a.student_id = s.id
    WHERE a.job_id = %s
    ORDER BY a.applied_at DESC
    """ if db_type == 'mysql' else """
    SELECT 
        a.id AS app_id, s.full_name, s.roll_no, s.branch, s.cgpa, a.status, s.resume_url
    FROM applications a
    JOIN students s ON a.student_id = s.id
    WHERE a.job_id = ?
    ORDER BY a.applied_at DESC
    """
    
    applicants = execute_query(conn, applicants_query, (selected_job_id,), fetch=True)
    
    if applicants:
        st.subheader(f"Applicants for {selected_title}")
        applicants_df = pd.DataFrame(applicants).rename(columns={'app_id': 'App ID'})
        st.dataframe(applicants_df, use_container_width=True, hide_index=True)
        
        # 3. Update Status Form
        with st.form("status_update_form"):
            app_id = st.number_input("Application ID to Update", min_value=1, step=1)
            new_status = st.radio("New Status", ['applied', 'shortlisted', 'rejected', 'accepted'])
            update_button = st.form_submit_button("Update Status", type="secondary")

            if update_button:
                update_query = "UPDATE applications SET status = %s WHERE id = %s" if db_type == 'mysql' else "UPDATE applications SET status = ? WHERE id = ?"
                update_params = (new_status, app_id)

                if execute_query(conn, update_query, update_params, commit=True) is not None:
                    st.success(f"Application {app_id} status updated to **{new_status.upper()}**!")
                    st.rerun()
                else:
                    st.error("Failed to update status. Check Application ID.")
    else:
        st.info("No applications received for this job yet.")

# --- Student Functions ---
def student_application_tracking(conn, db_type, student_id):
    st.header("Your Application Status (Read)")
    
    tracking_query = """
    SELECT 
        j.title as job_title, c.name as company, a.applied_at, a.status 
    FROM applications a
    JOIN jobs j ON a.job_id = j.id
    JOIN companies c ON j.company_id = c.id
    WHERE a.student_id = %s
    ORDER BY a.applied_at DESC
    """ if db_type == 'mysql' else """
    SELECT 
        j.title as job_title, c.name as company, a.applied_at, a.status 
    FROM applications a
    JOIN jobs j ON a.job_id = j.id
    JOIN companies c ON j.company_id = c.id
    WHERE a.student_id = ?
    ORDER BY a.applied_at DESC
    """
    
    applications = execute_query(conn, tracking_query, (student_id,), fetch=True)
    
    if applications:
        app_df = pd.DataFrame(applications)
        st.dataframe(app_df, use_container_width=True)
        st.info("Status Legend: Applied $\rightarrow$ Shortlisted $\rightarrow$ Accepted/Rejected")
    else:
        st.info("You have not submitted any job applications yet.")

applications_page()