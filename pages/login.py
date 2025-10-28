# CareerSphere/login.py (FINALIZED WITH LOGOUT BUTTON)

import streamlit as st
from database import execute_query
# NOTE: If you haven't implemented the DB safeguard from previous steps, 
# you'll need to import get_db_connection here as well.

def logout_page_action():
    """Clears session state for logout and reruns."""
    st.session_state['logged_in'] = False
    st.session_state['user_role'] = None
    st.session_state['user_id'] = None
    st.session_state['user_email'] = None
    st.success("Logged out successfully! Redirecting...")
    st.rerun()

def login_page():
    st.title("🔑 User Login")
    
    if st.session_state.get('logged_in'):
        # --- LOGOUT SECTION ---
        st.info(f"You are already logged in as **{st.session_state['user_role'].upper()}**.")
        
        # Add the Logout button
        if st.button("Logout", key="login_page_logout_btn"):
            logout_page_action()
            
        # Stop the rest of the login form from rendering
        return 

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login", type="primary"):
        if email and password:
            # Safely check for db_conn before use
            if 'db_conn' not in st.session_state or st.session_state['db_conn'] is None:
                st.error("Database connection not established. Cannot log in.")
                return

            conn = st.session_state['db_conn']
            db_type = st.session_state['db_type']
            
            # Simple password check (In production, use hashing like bcrypt)
            query = "SELECT id, email, role FROM users WHERE email = %s AND password = %s" if db_type == 'mysql' else "SELECT id, email, role FROM users WHERE email = ? AND password = ?"
            params = (email, password)
            
            user_data = execute_query(conn, query, params, fetch=True)
            
            if user_data:
                user = user_data[0]
                st.session_state['logged_in'] = True
                st.session_state['user_role'] = user['role']
                st.session_state['user_id'] = user['id']
                st.session_state['user_email'] = user['email']
                st.success(f"Login successful as {user['role'].upper()}! Redirecting...")
                
                # Rerun to update the sidebar and navigate to the dashboard
                st.rerun()

            else:
                st.error("Invalid email or password.")
        else:
            st.warning("Please enter both email and password.")

login_page()