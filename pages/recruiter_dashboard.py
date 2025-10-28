# CareerSphere/pages/recruiter_dashboard.py (UPDATED with NumPy Fix)

import streamlit as st
import pandas as pd
from database import execute_query
import re 

def recruiter_dashboard():
    # --- Access Control ---
    if not st.session_state.get('logged_in') or st.session_state.get('user_role') != 'recruiter':
        st.error("Access Denied. Please login as a Recruiter.")
        st.stop()

    conn = st.session_state['db_conn']
    db_type = st.session_state['db_type']
    recruiter_id = st.session_state['user_id']

    st.title("🧑‍💼 Recruiter Dashboard")
    st.subheader(f"Welcome, {st.session_state['user_email']}!")
    
    # Check for admin approval 
    approval_query = "SELECT is_approved FROM recruiters WHERE id = %s" if db_type == 'mysql' else "SELECT is_approved FROM recruiters WHERE id = ?"
    is_approved_data = execute_query(conn, approval_query, (recruiter_id,), fetch=True)
    
    # Safely get approval status, assuming default unapproved if data is missing
    is_approved_status = 1 
    if is_approved_data:
        # Check if the result is a dictionary or a tuple/list and extract the value
        if isinstance(is_approved_data[0], dict):
            is_approved_status = is_approved_data[0].get('is_approved', 0)
        elif isinstance(is_approved_data[0], (list, tuple)) and len(is_approved_data[0]) > 0:
             is_approved_status = is_approved_data[0][0]
    
    if is_approved_status == 0:
        st.warning("⚠️ Your recruiter account is pending Admin approval. You cannot post jobs yet.")
    
    st.markdown("---")

    # --- Metrics Overview (Simplified) ---
    job_count_query = "SELECT COUNT(*) as total_jobs FROM jobs WHERE recruiter_id = %s" if db_type == 'mysql' else "SELECT COUNT(*) as total_jobs FROM jobs WHERE recruiter_id = ?"
    app_count_query = """
    SELECT COUNT(a.id) as total_apps 
    FROM applications a
    JOIN jobs j ON a.job_id = j.id
    WHERE j.recruiter_id = %s
    """ if db_type == 'mysql' else """
    SELECT COUNT(a.id) as total_apps 
    FROM applications a
    JOIN jobs j ON a.job_id = j.id
    WHERE j.recruiter_id = ?
    """
    
    total_jobs_data = execute_query(conn, job_count_query, (recruiter_id,), fetch=True)
    total_apps_data = execute_query(conn, app_count_query, (recruiter_id,), fetch=True)

    # Use .get() for safe dictionary access, handling potential tuple conversion from non-MySQL DBs
    def safe_get(data, key):
        if data and isinstance(data[0], dict):
            return data[0].get(key, 0)
        elif data and isinstance(data[0], (list, tuple)) and len(data[0]) > 0:
            # Fallback for tuple/list results (e.g., SQLite without explicit dict cursor)
            return data[0][0] 
        return 0

    total_jobs = safe_get(total_jobs_data, 'total_jobs')
    total_apps = safe_get(total_apps_data, 'total_apps')


    col1, col2, col3 = st.columns(3)
    col1.metric("Active Job Posts", total_jobs)
    col2.metric("Total Applications Received", total_apps)
    col3.page_link("pages/job_postings.py", label="Post New Job", icon="➕")

    st.markdown("---")

    # --- Manage Job Postings (Read & Delete) ---
    st.header("Your Job Postings (View/Delete)")
    
    # ... (job_list_query remains the same)
    job_list_query = """
    SELECT j.id, j.title, c.name as company, j.location, j.eligibility, 
            COUNT(a.id) as applicants, j.created_at
    FROM jobs j
    JOIN recruiters r ON j.recruiter_id = r.id
    JOIN companies c ON j.company_id = c.id
    LEFT JOIN applications a ON j.id = a.job_id
    WHERE j.recruiter_id = %s
    GROUP BY j.id, j.title, c.name, j.location, j.eligibility, j.created_at
    ORDER BY j.created_at DESC
    """ if db_type == 'mysql' else """
    SELECT j.id, j.title, c.name as company, j.location, j.eligibility, 
    (SELECT COUNT(*) FROM applications WHERE job_id = j.id) as applicants, j.created_at
    FROM jobs j
    JOIN recruiters r ON j.recruiter_id = r.id
    JOIN companies c ON j.company_id = c.id
    WHERE j.recruiter_id = ?
    ORDER BY j.created_at DESC
    """
    
    job_posts = execute_query(conn, job_list_query, (recruiter_id,), fetch=True)
    
    if job_posts:
        # Ensure the list of dictionaries can be converted to a DataFrame safely
        job_df = pd.DataFrame(job_posts)
        job_options = {job['title']: job['id'] for job in job_posts}
        st.dataframe(job_df, use_container_width=True)

        st.page_link("pages/applications.py", label="Review Applicants & Change Status", icon="🔍")

        # --- Job Deletion (Delete) ---
        st.subheader("Delete Job Posting")
        with st.form("delete_job_form"):
            job_to_delete_numpy = st.selectbox("Select Job ID to Delete", job_df['id'].tolist())
            delete_button = st.form_submit_button("Permanently Delete Job", type="secondary")
            
            if delete_button:
                # CRITICAL FIX: Convert numpy type to standard Python int for the query
                job_to_delete = int(job_to_delete_numpy)
                
                # ON DELETE CASCADE handles applications
                delete_query = "DELETE FROM jobs WHERE id = %s AND recruiter_id = %s" if db_type == 'mysql' else "DELETE FROM jobs WHERE id = ? AND recruiter_id = ?"
                delete_params = (job_to_delete, recruiter_id)
                
                if execute_query(conn, delete_query, delete_params, commit=True) is not None:
                    st.success(f"Job ID {job_to_delete} deleted successfully!")
                    st.rerun()
                else:
                    st.error("Failed to delete job. Check ID.")
    else:
        st.info("You haven't posted any jobs yet.")
    
    st.markdown("---")
    
    # --- Applicant Shortlisting Feature (Advanced View) ---
    st.header("🔍 Applicant Shortlisting Tool (Matching Logic)")
    
    if job_posts:
        shortlist_job_title = st.selectbox("Select a Job for Shortlisting Analysis", job_df['title'].tolist(), key='shortlist_job_select')
        
        # Select the ID from the DataFrame (this results in a NumPy type)
        selected_job_id_numpy = job_df[job_df['title'] == shortlist_job_title]['id'].iloc[0]
        
        # CRITICAL FIX: Convert the numpy type to a standard Python integer
        selected_job_id = int(selected_job_id_numpy)


        # Fetch applicants with full profile data
        shortlist_query = """
        SELECT 
            s.full_name, s.cgpa, s.branch, s.skills, s.projects, s.internships, s.hackathons, 
            a.status, a.applied_at
        FROM applications a
        JOIN students s ON a.student_id = s.id
        WHERE a.job_id = %s
        """ if db_type == 'mysql' else """
        SELECT 
            s.full_name, s.cgpa, s.branch, s.skills, s.projects, s.internships, s.hackathons, 
            a.status, a.applied_at
        FROM applications a
        JOIN students s ON a.student_id = s.id
        WHERE a.job_id = ?
        """
        
        applicants_data = execute_query(conn, shortlist_query, (selected_job_id,), fetch=True)
        
        if applicants_data:
            applicants_df = pd.DataFrame(applicants_data)
            
            # --- Simple Matching Logic ---
            def calculate_match_score(row, job_eligibility):
                score = 0
                
                # Ensure CGPA is treated as float for comparison
                cgpa_val = float(row['cgpa']) if row['cgpa'] is not None else 0.0

                # 1. CGPA Check
                cgpa_req_match = re.search(r'CGPA\s*>\s*(\d+(\.\d+)?)', job_eligibility, re.IGNORECASE)
                if cgpa_req_match and cgpa_val > 0.0:
                    required_cgpa = float(cgpa_req_match.group(1))
                    if cgpa_val >= required_cgpa:
                        score += 10 # High score for meeting strict requirement
                    # Add proportional score even if slightly below
                    score += max(0, (cgpa_val - required_cgpa) * 5)
                
                # 2. Skills Check (Keyword match)
                required_skills = [skill.strip().lower() for skill in re.split(r',|/|and', job_eligibility) if len(skill) > 2 and not re.search(r'\d', skill)]
                applicant_skills = [skill.strip().lower() for skill in (row['skills'] or '').split(',')]
                
                skill_matches = len(set(required_skills) & set(applicant_skills))
                score += skill_matches * 5
                
                # 3. Project/Hackathon Experience (Presence check)
                if row['projects'] and len(row['projects']) > 10:
                    score += 5
                if row['internships'] and len(row['internships']) > 10:
                    score += 5
                if row['hackathons'] and len(row['hackathons']) > 10: # Added hackathons check
                    score += 5

                return round(score, 1)

            # Get eligibility for the selected job (for scoring)
            job_eligibility_query = "SELECT eligibility FROM jobs WHERE id = %s" if db_type == 'mysql' else "SELECT eligibility FROM jobs WHERE id = ?"
            job_eligibility = execute_query(conn, job_eligibility_query, (selected_job_id,), fetch=True)[0]['eligibility']

            applicants_df['Match Score'] = applicants_df.apply(lambda row: calculate_match_score(row, job_eligibility), axis=1)
            
            # Sort by Match Score
            applicants_df = applicants_df.sort_values(by='Match Score', ascending=False)
            
            st.success(f"Showing {len(applicants_df)} applicants, sorted by best match score.")
            st.dataframe(applicants_df[['full_name', 'Match Score', 'cgpa', 'branch', 'skills', 'status', 'applied_at']], use_container_width=True)
            st.caption("Match Score: Calculated based on CGPA, skills, and project experience relative to the job's Eligibility text.")

        else:
            st.info("No applicants for this job yet.")


recruiter_dashboard()