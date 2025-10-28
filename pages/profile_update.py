# CareerSphere/pages/profile_update.py

import streamlit as st
import pandas as pd
from database import execute_query

def profile_update_page():
    # --- Access Control ---
    if not st.session_state.get('logged_in'):
        st.error("Access Denied. Please login.")
        st.stop()
        
    role = st.session_state['user_role']
    conn = st.session_state['db_conn']
    db_type = st.session_state['db_type']
    
    if role == 'student':
        # Student view: Edit own profile
        st.title("📝 Update Your Extended Profile")
        st.subheader("Internships, Hackathons, Certificates, and Links")
        
        # Fetch current data for TEXT fields
        profile_query = "SELECT internships, hackathons, certificates, resume_url, coding_profiles FROM students WHERE id = %s" if db_type == 'mysql' else "SELECT internships, hackathons, certificates, resume_url, coding_profiles FROM students WHERE id = ?"
        current_data = execute_query(conn, profile_query, (st.session_state['user_id'],), fetch=True)
        
        if not current_data:
             st.warning("Please complete initial registration via the student dashboard first.")
             st.stop()
        
        current_data = current_data[0]

        with st.form("extra_curricular_form"):
            internships = st.text_area("Internships (List Company, Role, Duration)", value=current_data.get('internships', ''), height=150)
            hackathons = st.text_area("Hackathons/Projects (List relevant projects, awards)", value=current_data.get('hackathons', ''), height=150)
            certificates = st.text_area("Certificates/Courses (List platform and course name)", value=current_data.get('certificates', ''), height=150)
            resume_url = st.text_input("Resume Link (Google Drive/GitHub)", value=current_data.get('resume_url', ''))
            coding_profiles = st.text_area("Coding Profiles Links (e.g., LeetCode, HackerRank)", value=current_data.get('coding_profiles', ''))
            
            submit_button = st.form_submit_button("Save Extended Profile", type="primary")

            if submit_button:
                update_query = """
                UPDATE students 
                SET internships = %s, hackathons = %s, certificates = %s, resume_url = %s, coding_profiles = %s
                WHERE id = %s
                """ if db_type == 'mysql' else """
                UPDATE students 
                SET internships = ?, hackathons = ?, certificates = ?, resume_url = ?, coding_profiles = ?
                WHERE id = ?
                """
                update_params = (internships, hackathons, certificates, resume_url, coding_profiles, st.session_state['user_id'])
                
                if execute_query(conn, update_query, update_params, commit=True) is not None:
                    st.success("Extended profile details saved successfully!")
                else:
                    st.error("Failed to save profile.")

    elif role == 'admin':
        # Admin view: Manage (Approve/Block) Recruiters
        st.title("👥 Admin User Management")
        st.subheader("Approve Recruiter Accounts")

        # Fetch all recruiters
        recruiter_query = "SELECT u.id, u.email, r.company_name, r.is_approved FROM users u JOIN recruiters r ON u.id = r.id"
        recruiters = execute_query(conn, recruiter_query, fetch=True)
        
        if recruiters:
            st.dataframe(pd.DataFrame(recruiters), use_container_width=True)
            
            # Form for approval/blocking
            with st.form("recruiter_action_form"):
                rec_ids = [r['id'] for r in recruiters]
                if not rec_ids:
                    st.info("No recruiters to manage.")
                    st.stop()
                    
                rec_id = st.selectbox("Recruiter User ID to Act On", rec_ids)
                action = st.radio("Action", ["Approve", "Block"])
                action_button = st.form_submit_button(f"{action} Recruiter", type="secondary")

                if action_button:
                    is_approved = 1 if action == "Approve" else 0
                    action_query = "UPDATE recruiters SET is_approved = %s WHERE id = %s" if db_type == 'mysql' else "UPDATE recruiters SET is_approved = ? WHERE id = ?"
                    action_params = (is_approved, rec_id)

                    if execute_query(conn, action_query, action_params, commit=True) is not None:
                        st.success(f"Recruiter ID {rec_id} has been **{action}d** successfully!")
                        st.rerun()
                    else:
                        st.error("Action failed. Check ID.")
        else:
            st.info("No recruiter accounts found.")

    else:
        st.error("Only Students and Admins can use this page for profile management.")

profile_update_page()