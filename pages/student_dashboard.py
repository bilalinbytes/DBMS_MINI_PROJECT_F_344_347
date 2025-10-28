# CareerSphere/pages/student_dashboard.py (FINALIZED: Fixed Decimal Type Error)

import streamlit as st
import pandas as pd
from database import execute_query
from database import get_db_connection # Ensure this is imported if you use the safeguard

# --- CRITICAL: DB INITIALIZATION SAFEGUARD (Ensure connection exists) ---
if 'db_conn' not in st.session_state or st.session_state.get('db_conn') is None:
    try:
        # Assuming get_db_connection is correctly implemented in database.py
        st.session_state['db_conn'], st.session_state['db_type'] = get_db_connection()
    except Exception:
        pass # Let the dashboard function handle the stop if connection fails


def student_dashboard():
    # --- Access Control ---
    if not st.session_state.get('logged_in') or st.session_state.get('user_role') != 'student':
        st.error("Access Denied. Please login as a Student.")
        st.stop()
        
    if st.session_state['db_conn'] is None:
        st.error("Database connection failed. Please contact the administrator.")
        st.stop()

    conn = st.session_state['db_conn']
    db_type = st.session_state['db_type']
    student_id = st.session_state['user_id']
    
    st.title("🧑‍🎓 Student Dashboard & Core Profile")
    st.subheader(f"Welcome, {st.session_state['user_email']}!")
    st.markdown("---")

    # --- Fetch Current Profile Data ---
    profile_query = """
    SELECT s.roll_no, s.full_name, s.branch, s.cgpa, s.skills, s.projects
    FROM students s
    WHERE s.id = %s
    """ if db_type == 'mysql' else """
    SELECT s.roll_no, s.full_name, s.branch, s.cgpa, s.skills, s.projects
    FROM students s
    WHERE s.id = ?
    """
    
    current_data = execute_query(conn, profile_query, (student_id,), fetch=True)
    
    if not current_data:
        st.error("Profile data not found. Please re-register or contact support.")
        st.stop()
        
    current_data = current_data[0]

    # --- Pre-process CGPA value from database ---
    # CRITICAL FIX: Convert Decimal type (from MySQL) to float for Streamlit widgets
    cgpa_value = current_data.get('cgpa')
    if cgpa_value is not None:
        cgpa_display_value = float(cgpa_value)
    else:
        cgpa_display_value = 0.0
    
    # --- Metrics Overview ---
    st.header("Profile Summary")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Current CGPA", f"{cgpa_display_value or 'N/A'}")
    col2.metric("Branch", current_data['branch'] or 'N/A')
    col3.page_link("pages/job_postings.py", label="View Jobs", icon="💼")

    st.markdown("---")

    # --- Core Profile Update Form (CREATE/UPDATE for core fields) ---
    st.header("Update Core Profile")
    st.caption("These fields are crucial for eligibility and shortlisting.")

    with st.form("core_profile_form"):
        # Display registered fields (read-only)
        st.text_input("Roll Number (Read Only)", value=current_data['roll_no'], disabled=True)
        
        # Updatable core fields
        full_name = st.text_input("Full Name", value=current_data.get('full_name', ''))
        branch = st.text_input("Branch/Department", value=current_data.get('branch', ''))
        
        cgpa = st.number_input(
            "CGPA (out of 10)", 
            min_value=0.0, 
            max_value=10.0, 
            # Use the pre-processed float value here
            value=cgpa_display_value,
            step=0.1,
            format="%.2f" # Ensure the format is set for consistency
        )
        
        skills = st.text_area(
            "Key Skills (e.g., Python, SQL, React, AWS)", 
            value=current_data.get('skills', ''), 
            height=100
        )
        
        projects = st.text_area(
            "Major Projects/Theses (Summarize key tech stacks)", 
            value=current_data.get('projects', ''), 
            height=150
        )

        # The submit button is correctly included, resolving the other warning
        submit_button = st.form_submit_button("Save Core Profile", type="primary")

        if submit_button:
            update_query = """
            UPDATE students 
            SET full_name = %s, branch = %s, cgpa = %s, skills = %s, projects = %s
            WHERE id = %s
            """ if db_type == 'mysql' else """
            UPDATE students 
            SET full_name = ?, branch = ?, cgpa = ?, skills = ?, projects = ?
            WHERE id = ?
            """
            update_params = (full_name, branch, cgpa, skills, projects, student_id)
            
            try:
                if execute_query(conn, update_query, update_params, commit=True):
                    st.success("Core profile updated successfully!")
                    st.rerun()
                else:
                    st.error("Failed to save profile. Check database connection/permissions.")
            except Exception as e:
                 st.error(f"Database update error: {e}")


student_dashboard()