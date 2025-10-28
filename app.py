# CareerSphere/app.py (CORRECTED)

import streamlit as st
import os

# --- PAGE CONFIGURATION & CSS ---
st.set_page_config(
    page_title="CareerSphere - Placement Portal",
    page_icon="🎓",
    layout="wide",
)

def load_css(file_name):
    """Loads custom CSS file."""
    # Using os.path.dirname(__file__) ensures the path is relative to app.py
    css_path = os.path.join(os.path.dirname(__file__), file_name)
    try:
        with open(css_path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"CSS file '{file_name}' not found. Check path.")

# Load the custom CSS file
load_css('style.css') # Load is relative to the current script directory

# --- CORE DB INITIALIZATION FIX ---
# This ensures db_conn and db_type are ALWAYS in st.session_state before any page runs.
try:
    # Ensure 'database.py' is in the root 'dbms_project' directory
    from database import get_db_connection
    if 'db_conn' not in st.session_state or st.session_state['db_conn'] is None:
        st.session_state['db_conn'], st.session_state['db_type'] = get_db_connection()
    from database import execute_query # Ensure this function is available globally
except ImportError:
    st.error("Could not find 'database.py'. Please ensure it's in the CareerSphere directory.")
    st.stop()
except Exception as e:
    st.error(f"Error during initial database connection: {e}")
    # Set safe defaults if connection completely fails
    if 'db_conn' not in st.session_state:
        st.session_state['db_conn'] = None
        st.session_state['db_type'] = 'error'

# --- SESSION STATE MANAGEMENT ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'user_role' not in st.session_state: st.session_state['user_role'] = None
if 'user_id' not in st.session_state: st.session_state['user_id'] = None
if 'user_email' not in st.session_state: st.session_state['user_email'] = None

# --- LOGOUT FUNCTION ---
def logout():
    """Clears session state for logout."""
    st.session_state['logged_in'] = False
    st.session_state['user_role'] = None
    st.session_state['user_id'] = None
    st.session_state['user_email'] = None
    st.success("Logged out successfully!")
    # NOTE: st.rerun() will restart the script, reloading the current page or the main page.
    st.rerun()

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("🎓 CareerSphere")
    
    if st.session_state['logged_in']:
        st.success(f"Logged in as: **{st.session_state['user_role'].upper()}**")
        
        st.markdown("---")
        
        # Dynamic Navigation based on Role
        if st.session_state['user_role'] == 'student':
            st.page_link("pages/student_dashboard.py", label="🧑‍🎓 Student Dashboard")
            st.page_link("pages/job_postings.py", label="💼 View & Apply Jobs")
            st.page_link("pages/applications.py", label="📑 Application Tracking")
            st.page_link("pages/profile_update.py", label="📝 Extended Profile")
            
        elif st.session_state['user_role'] == 'recruiter':
            st.page_link("pages/recruiter_dashboard.py", label="🧑‍💼 Recruiter Dashboard")
            st.page_link("pages/job_postings.py", label="➕ Post New Job")
            st.page_link("pages/applications.py", label="🔍 Review Applicants")
            
        elif st.session_state['user_role'] == 'admin':
            st.page_link("pages/admin_dashboard.py", label="🧑‍🏫 Admin Dashboard")
            st.page_link("pages/profile_update.py", label="👥 Manage Users")
            st.page_link("pages/analytics.py", label="📊 System Analytics")

        st.markdown("---")
        if st.button("Logout", key="sidebar_logout"):
            logout()
    else:
        # ✅ CORRECTED PATH: Must include 'pages/' since the file is in that folder.
        st.page_link("pages/login.py", label="🔑 Login")
        st.page_link("pages/register.py", label="✍️ Register New Account")
        
# --- MAIN PAGE CONTENT ---
if not st.session_state['logged_in']:
    st.title("Welcome to CareerSphere 🌐")
    st.subheader("Your Ultimate Campus Placement Portal")
    st.markdown("""
        Use the sidebar to **Login** or **Register** to access job postings, manage profiles, 
        and streamline the placement process.
        
        **Default Credentials to Test:**
        - **Admin:** `admin@cs.edu` / `admin`
        - **Student:** `student@cs.edu` / `student`
        - **Recruiter:** `recruiter@corp.com` / `recruiter`
    """)

# If logged in, the main content of the dashboard pages will be displayed based on the link clicked.