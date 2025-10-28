# # CareerSphere/pages/register.py (FINAL, ROBUST VERSION)

# import streamlit as st
# # Import both DB functions as they are needed for the safeguard logic
# from database import execute_query, get_db_connection 
# # Import specific database error classes if possible for precise error handling

# # --- CRITICAL: SESSION STATE CHECK AND DB INITIALIZATION SAFEGUARD ---
# # This ensures that db_conn exists even if Streamlit runs this page directly 
# # or if there's a multi-page routing issue.
# if 'db_conn' not in st.session_state or st.session_state.get('db_conn') is None:
#     try:
#         st.info("Initializing database connection from register page...")
#         st.session_state['db_conn'], st.session_state['db_type'] = get_db_connection()
        
#     except ImportError:
#         st.error("Error: The 'database.py' file is missing. Cannot register users.")
#         st.stop()
#     except Exception as e:
#         st.error(f"Error connecting to database. Please check configuration. Details: {e}")
#         st.session_state['db_conn'] = None
#         st.session_state['db_type'] = 'error'
#         st.stop() 

# # --- UTILITY FUNCTION FOR CLEANUP ---
# def cleanup_user(conn, db_type, email):
#     """Deletes the newly created user from the 'users' table if the subsequent
#     role-specific insert fails (to prevent orphaned records).
#     """
#     st.warning("Attempting to clean up partial user record...")
#     delete_query = "DELETE FROM users WHERE email = %s" if db_type == 'mysql' else "DELETE FROM users WHERE email = ?"
#     execute_query(conn, delete_query, (email,), commit=True)


# def register_user(email, password, role, profile_data=None):
#     conn = st.session_state['db_conn'] 
#     db_type = st.session_state['db_type']
    
#     # --- 1. Insert into users table (with robust error handling) ---
#     try:
#         user_insert_query = "INSERT INTO users (email, password, role) VALUES (%s, %s, %s)" if db_type == 'mysql' else "INSERT INTO users (email, password, role) VALUES (?, ?, ?)"
#         user_params = (email, password, role)
#         execute_query(conn, user_insert_query, user_params, commit=True)

#     except Exception as e:
#         error_message = str(e).lower()
#         if 'duplicate entry' in error_message or 'unique constraint' in error_message:
#             st.error("Registration failed: The email address is already in use. Please use a different email.")
#         else:
#             st.error(f"Registration failed due to a database error. Details: {e}")
#             st.exception(e) 
#         return False
    
#     # --- 2. Get the ID of the newly inserted user (FIXED FOR NONE/EMPTY LIST) ---
    
#     new_user_id = None # Initialize as None
    
#     if db_type == 'mysql':
#         user_id_query = "SELECT LAST_INSERT_ID() as id"
#         result = execute_query(conn, user_id_query, fetch=True)
        
#         # 🟢 SAFE CHECK: Check if result is not None and not empty
#         if result and len(result) > 0: 
#             new_user_id = result[0]['id']
        
#     elif db_type == 'sqlite':
#         user_id_query = "SELECT id FROM users WHERE email = ? ORDER BY id DESC LIMIT 1"
#         result = execute_query(conn, user_id_query, (email,), fetch=True)
        
#         # 🟢 SAFE CHECK: Check if result is not None and not empty
#         if result and len(result) > 0:
#             new_user_id = result[0]['id']
            
#     else:
#         st.error(f"Unsupported database type for getting user ID: {db_type}")
#         return False

    
#     # --- Check if ID retrieval was successful ---
#     if new_user_id is None:
#         st.error("Critical error: Could not retrieve new user ID after insertion. Rolling back registration.")
#         cleanup_user(conn, db_type, email)
#         return False
    
#     # --- 3. Insert into role-specific table ---
#     try:
#         if role == 'student':
#             student_insert_query = "INSERT INTO students (id, roll_no, full_name, branch) VALUES (%s, %s, %s, %s)" if db_type == 'mysql' else "INSERT INTO students (id, roll_no, full_name, branch) VALUES (?, ?, ?, ?)"
#             student_params = (new_user_id, profile_data['roll_no'], profile_data['full_name'], profile_data['branch'])
#             execute_query(conn, student_insert_query, student_params, commit=True)
#             st.success("Student registration complete! Please log in.")
#             return True
        
#         elif role == 'recruiter':
#             recruiter_insert_query = "INSERT INTO recruiters (id, company_name) VALUES (%s, %s)" if db_type == 'mysql' else "INSERT INTO recruiters (id, company_name) VALUES (?, ?)"
#             recruiter_params = (new_user_id, profile_data['company_name'])
#             execute_query(conn, recruiter_insert_query, recruiter_params, commit=True)
#             st.success("Recruiter account created. **Pending Admin Approval.** You may log in now.")
#             return True
        
#         else:
#             st.error(f"Internal error: Unsupported role '{role}'.")
#             return False

#     except Exception as e:
#         # 4. Rollback/Cleanup if role-specific insert failed
#         st.error(f"Failed to complete profile for role {role} due to a database error. Cleaning up...")
#         st.exception(e)
#         cleanup_user(conn, db_type, email)
#         return False
        
#     return False

# # --- Streamlit Page Logic ---
# def register_page():
#     st.title("✍️ Register New Account")
    
#     if st.session_state.get('logged_in'):
#         st.info("You must log out to register a new account.")
#         return

#     selected_role = st.selectbox("I am registering as a...", ["student", "recruiter"], index=0)

#     st.markdown("---")
#     st.subheader("Account Details")
#     email = st.text_input("Email", key="reg_email")
#     password = st.text_input("Password (min 6 characters)", type="password", key="reg_password")
#     confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm_password")

#     st.markdown("---")
#     st.subheader(f"{selected_role.capitalize()} Profile Details")

#     profile_data = {}
#     if selected_role == 'student':
#         profile_data['full_name'] = st.text_input("Full Name")
#         profile_data['roll_no'] = st.text_input("University Roll Number")
#         profile_data['branch'] = st.text_input("Branch/Department (e.g., CSE)")
        
#     elif selected_role == 'recruiter':
#         profile_data['company_name'] = st.text_input("Company Name")

#     st.markdown("---")

#     if st.button("Register", type="primary"):
#         # Basic input validation
#         if password != confirm_password:
#             st.error("Passwords do not match.")
#         elif len(password) < 6:
#             st.error("Password must be at least 6 characters.")
#         elif not email:
#             st.error("Email cannot be empty.")
#         elif selected_role == 'student' and (not profile_data['full_name'] or not profile_data['roll_no'] or not profile_data['branch']):
#             st.error("Student: Please fill in your name, roll number, and branch.")
#         elif selected_role == 'recruiter' and not profile_data['company_name']:
#             st.error("Recruiter: Please fill in your company name.")
#         else:
#             # All checks pass - attempt registration
#             register_user(email, password, selected_role, profile_data)

# register_page()
# CareerSphere/pages/register.py (FINAL, ROBUST VERSION with ADMIN)

import streamlit as st
# Import both DB functions as they are needed for the safeguard logic
from database import execute_query, get_db_connection 
# Import specific database error classes if possible for precise error handling

# --- CRITICAL: SESSION STATE CHECK AND DB INITIALIZATION SAFEGUARD ---
# This ensures that db_conn exists even if Streamlit runs this page directly 
# or if there's a multi-page routing issue.
if 'db_conn' not in st.session_state or st.session_state.get('db_conn') is None:
    try:
        st.info("Initializing database connection from register page...")
        st.session_state['db_conn'], st.session_state['db_type'] = get_db_connection()
        
    except ImportError:
        st.error("Error: The 'database.py' file is missing. Cannot register users.")
        st.stop()
    except Exception as e:
        st.error(f"Error connecting to database. Please check configuration. Details: {e}")
        st.session_state['db_conn'] = None
        st.session_state['db_type'] = 'error'
        st.stop() 

# --- UTILITY FUNCTION FOR CLEANUP ---
def cleanup_user(conn, db_type, email):
    """Deletes the newly created user from the 'users' table if the subsequent
    role-specific insert fails (to prevent orphaned records).
    """
    st.warning("Attempting to clean up partial user record...")
    delete_query = "DELETE FROM users WHERE email = %s" if db_type == 'mysql' else "DELETE FROM users WHERE email = ?"
    execute_query(conn, delete_query, (email,), commit=True)


def register_user(email, password, role, profile_data=None):
    conn = st.session_state['db_conn'] 
    db_type = st.session_state['db_type']
    
    # --- 1. Insert into users table (with robust error handling) ---
    try:
        user_insert_query = "INSERT INTO users (email, password, role) VALUES (%s, %s, %s)" if db_type == 'mysql' else "INSERT INTO users (email, password, role) VALUES (?, ?, ?)"
        user_params = (email, password, role)
        execute_query(conn, user_insert_query, user_params, commit=True)

    except Exception as e:
        error_message = str(e).lower()
        if 'duplicate entry' in error_message or 'unique constraint' in error_message:
            st.error("Registration failed: The email address is already in use. Please use a different email.")
        else:
            st.error(f"Registration failed due to a database error. Details: {e}")
            st.exception(e) 
        return False
    
    # --- 2. Get the ID of the newly inserted user ---
    
    new_user_id = None # Initialize as None
    
    if db_type == 'mysql':
        user_id_query = "SELECT LAST_INSERT_ID() as id"
        result = execute_query(conn, user_id_query, fetch=True)
        
        # 🟢 SAFE CHECK: Check if result is not None and not empty
        if result and len(result) > 0: 
            new_user_id = result[0]['id']
        
    elif db_type == 'sqlite':
        user_id_query = "SELECT id FROM users WHERE email = ? ORDER BY id DESC LIMIT 1"
        result = execute_query(conn, user_id_query, (email,), fetch=True)
        
        # 🟢 SAFE CHECK: Check if result is not None and not empty
        if result and len(result) > 0:
            new_user_id = result[0]['id']
            
    else:
        st.error(f"Unsupported database type for getting user ID: {db_type}")
        cleanup_user(conn, db_type, email)
        return False

    
    # --- Check if ID retrieval was successful ---
    if new_user_id is None:
        st.error("Critical error: Could not retrieve new user ID after insertion. Rolling back registration.")
        cleanup_user(conn, db_type, email)
        return False
    
    # --- 3. Insert into role-specific table (Admin logic added) ---
    try:
        if role == 'student':
            student_insert_query = "INSERT INTO students (id, roll_no, full_name, branch) VALUES (%s, %s, %s, %s)" if db_type == 'mysql' else "INSERT INTO students (id, roll_no, full_name, branch) VALUES (?, ?, ?, ?)"
            student_params = (new_user_id, profile_data['roll_no'], profile_data['full_name'], profile_data['branch'])
            execute_query(conn, student_insert_query, student_params, commit=True)
            st.success("Student registration complete! Please log in.")
            return True
        
        elif role == 'recruiter':
            recruiter_insert_query = "INSERT INTO recruiters (id, company_name) VALUES (%s, %s)" if db_type == 'mysql' else "INSERT INTO recruiters (id, company_name) VALUES (?, ?)"
            recruiter_params = (new_user_id, profile_data['company_name'])
            execute_query(conn, recruiter_insert_query, recruiter_params, commit=True)
            st.success("Recruiter account created. **Pending Admin Approval.** You may log in now.")
            return True
            
        elif role == 'admin':
            # Assuming 'admins' table structure is (id, department)
            admin_insert_query = "INSERT INTO admins (id, department) VALUES (%s, %s)" if db_type == 'mysql' else "INSERT INTO admins (id, department) VALUES (?, ?)"
            admin_params = (new_user_id, profile_data['department'])
            execute_query(conn, admin_insert_query, admin_params, commit=True)
            st.success(f"Admin registration complete for department: {profile_data['department']}! Please log in.")
            return True
        
        else:
            st.error(f"Internal error: Unsupported role '{role}'.")
            return False

    except Exception as e:
        # 4. Rollback/Cleanup if role-specific insert failed
        st.error(f"Failed to complete profile for role {role} due to a database error. Cleaning up...")
        st.exception(e)
        cleanup_user(conn, db_type, email)
        return False
        
    return False

# --- Streamlit Page Logic ---
def register_page():
    st.title("✍️ Register New Account")
    
    if st.session_state.get('logged_in'):
        st.info("You must log out to register a new account.")
        return

    # Updated role selection to include 'admin'
    selected_role = st.selectbox("I am registering as a...", ["student", "recruiter", "admin"], index=0)

    st.markdown("---")
    st.subheader("Account Details")
    email = st.text_input("Email", key="reg_email")
    password = st.text_input("Password (min 6 characters)", type="password", key="reg_password")
    confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm_password")

    st.markdown("---")
    st.subheader(f"{selected_role.capitalize()} Profile Details")

    profile_data = {}
    if selected_role == 'student':
        profile_data['full_name'] = st.text_input("Full Name")
        profile_data['roll_no'] = st.text_input("University Roll Number")
        profile_data['branch'] = st.text_input("Branch/Department (e.g., CSE)")
        
    elif selected_role == 'recruiter':
        profile_data['company_name'] = st.text_input("Company Name")

    # Admin input fields added
    elif selected_role == 'admin':
        # Admin profiles typically need a name/identifier or department
        profile_data['department'] = st.text_input("Admin Department (e.g., Placement Cell, HOD)")

    st.markdown("---")

    if st.button("Register", type="primary"):
        # Basic input validation
        if password != confirm_password:
            st.error("Passwords do not match.")
        elif len(password) < 6:
            st.error("Password must be at least 6 characters.")
        elif not email:
            st.error("Email cannot be empty.")
        
        # Role-specific validation checks
        elif selected_role == 'student' and (not profile_data.get('full_name') or not profile_data.get('roll_no') or not profile_data.get('branch')):
            st.error("Student: Please fill in your name, roll number, and branch.")
        elif selected_role == 'recruiter' and not profile_data.get('company_name'):
            st.error("Recruiter: Please fill in your company name.")
        elif selected_role == 'admin' and not profile_data.get('department'):
            st.error("Admin: Please fill in your department.")
            
        else:
            # All checks pass - attempt registration
            register_user(email, password, selected_role, profile_data)

register_page()