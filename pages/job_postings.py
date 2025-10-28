# CareerSphere/pages/job_postings.py (UPDATED)

import streamlit as st
import pandas as pd
from database import execute_query

def job_postings_page():
    # --- Access Control ---
    if not st.session_state.get('logged_in'):
        st.error("Access Denied. Please login.")
        st.stop()

    conn = st.session_state['db_conn']
    db_type = st.session_state['db_type']
    role = st.session_state['user_role']
    user_id = st.session_state['user_id']
    
    st.title("💼 Job Postings & Application")
    st.markdown("---")
    
    if role == 'recruiter':
        recruiter_job_management(conn, db_type, user_id)
    elif role == 'student':
        student_job_application(conn, db_type, user_id)
    else:
        st.info("Admins view job stats on the Analytics page.")

# --- Recruiter Functions (Create Job) ---
def recruiter_job_management(conn, db_type, recruiter_id):
    st.header("Post a New Job (Create)")
    
    # ... (Recruiter Company ID setup remains the same)
    
    # Get Recruiter's Company ID
    company_name_query = "SELECT company_name FROM recruiters WHERE id = %s" if db_type == 'mysql' else "SELECT company_name FROM recruiters WHERE id = ?"
    company_name_data = execute_query(conn, company_name_query, (recruiter_id,), fetch=True)
    
    if not company_name_data:
        st.error("Recruiter profile incomplete. Cannot post jobs.")
        return
        
    company_name = company_name_data[0]['company_name']
    
    # Fetch or Create Company ID
    company_check_query = "SELECT id FROM companies WHERE name = %s" if db_type == 'mysql' else "SELECT id FROM companies WHERE name = ?"
    company_id_data = execute_query(conn, company_check_query, (company_name,), fetch=True)
    
    if not company_id_data:
        insert_company_query = "INSERT INTO companies (name) VALUES (%s)" if db_type == 'mysql' else "INSERT INTO companies (name) VALUES (?)"
        execute_query(conn, insert_company_query, (company_name,), commit=True)
        # Re-fetch the ID after insertion
        company_id = execute_query(conn, company_check_query, (company_name,), fetch=True)[0]['id']
    else:
        company_id = company_id_data[0]['id']

    st.info(f"Posting job under company: **{company_name}**")

    with st.form("new_job_form"):
        title = st.text_input("Job Title")
        location = st.text_input("Location")
        # Critical field for recruiter shortlisting logic
        eligibility = st.text_area("Eligibility Criteria (e.g., CGPA > 7.5, Branch: CSE/IT, Skills: Python, SQL)", height=100)
        description = st.text_area("Job Description", height=200)
        
        submit_button = st.form_submit_button("Post Job", type="primary")

        if submit_button:
            insert_query = """
            INSERT INTO jobs (recruiter_id, company_id, title, location, eligibility, description) 
            VALUES (%s, %s, %s, %s, %s, %s)
            """ if db_type == 'mysql' else """
            INSERT INTO jobs (recruiter_id, company_id, title, location, eligibility, description) 
            VALUES (?, ?, ?, ?, ?, ?)
            """
            insert_params = (recruiter_id, company_id, title, location, eligibility, description)
            
            if execute_query(conn, insert_query, insert_params, commit=True) is not None:
                st.success(f"Job '{title}' posted successfully! (Trigger logged the action)")
            else:
                st.error("Failed to post job.")

# --- Student Functions (View and Apply) ---
def student_job_application(conn, db_type, student_id):
    st.header("Available Jobs (Read & Apply)")

    # Join job postings with companies
    jobs_query = """
    SELECT 
        j.id, j.title, c.name as company, j.location, j.eligibility, 
        CASE WHEN a.student_id IS NOT NULL THEN 'Applied' ELSE 'Not Applied' END as application_status
    FROM jobs j
    JOIN companies c ON j.company_id = c.id
    LEFT JOIN applications a ON j.id = a.job_id AND a.student_id = %s
    ORDER BY j.created_at DESC
    """ if db_type == 'mysql' else """
    SELECT 
        j.id, j.title, c.name as company, j.location, j.eligibility, 
        CASE WHEN a.student_id IS NOT NULL THEN 'Applied' ELSE 'Not Applied' END as application_status
    FROM jobs j
    JOIN companies c ON j.company_id = c.id
    LEFT JOIN applications a ON j.id = a.job_id AND a.student_id = ?
    ORDER BY j.created_at DESC
    """
    
    available_jobs = execute_query(conn, jobs_query, (student_id,), fetch=True)
    
    if available_jobs:
        jobs_df = pd.DataFrame(available_jobs).rename(columns={'id': 'Job ID'})
        st.dataframe(jobs_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        st.subheader("Apply for a Job")
        
        # Fetch full student profile for eligibility check
        profile_query = "SELECT cgpa, skills FROM students WHERE id = %s" if db_type == 'mysql' else "SELECT cgpa, skills FROM students WHERE id = ?"
        student_profile_data = execute_query(conn, profile_query, (student_id,), fetch=True)
        
        is_profile_ready = student_profile_data and student_profile_data[0].get('cgpa') and student_profile_data[0].get('skills')
        
        if not is_profile_ready:
            st.error("⚠️ **CRITICAL:** Your **CGPA** and **Skills** must be set on the Student Dashboard before you can apply.")
        
        with st.form("apply_form"):
            job_ids = jobs_df['Job ID'].tolist()
            if not job_ids:
                st.warning("No jobs available to apply.")
                st.stop()
                
            job_to_apply = st.selectbox("Select Job ID to Apply", job_ids)
            
            # Display criteria for the selected job
            selected_job = jobs_df[jobs_df['Job ID'] == job_to_apply].iloc[0]
            st.info(f"Criteria for **{selected_job.title}**: {selected_job.eligibility}")
            
            apply_button = st.form_submit_button("Submit Application", type="primary", disabled=not is_profile_ready)
            
            if apply_button:
                # Check if already applied
                check_query = "SELECT id FROM applications WHERE job_id = %s AND student_id = %s" if db_type == 'mysql' else "SELECT id FROM applications WHERE job_id = ? AND student_id = ?"
                already_applied = execute_query(conn, check_query, (job_to_apply, student_id), fetch=True)
                
                if already_applied:
                    st.warning("You have already applied for this job.")
                else:
                    apply_query = "INSERT INTO applications (job_id, student_id) VALUES (%s, %s)" if db_type == 'mysql' else "INSERT INTO applications (job_id, student_id) VALUES (?, ?)"
                    apply_params = (job_to_apply, student_id)
                    
                    if execute_query(conn, apply_query, apply_params, commit=True) is not None:
                        st.success(f"Application submitted successfully for Job ID {job_to_apply}! Recruiter can now view your full profile.")
                        st.rerun()
                    else:
                        st.error("Failed to submit application.")
    else:
        st.info("No job postings are available at the moment.")

job_postings_page()