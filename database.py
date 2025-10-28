# CareerSphere/database.py (FINALIZED)

import streamlit as st
import mysql.connector
import sqlite3
# Note: pandas import kept just in case, though not used in these functions
import pandas as pd 

# MySQL Credentials
MYSQL_HOST = "localhost"
MYSQL_USER = "root"
MYSQL_PASSWORD = "bilal@1234"
MYSQL_DATABASE = "cs"

# SQLite File
SQLITE_DB = "cs.db"

def get_db_connection():
    """Attempts MySQL connection, falls back to SQLite."""
    # 1. Try MySQL Connection
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        if conn.is_connected():
            st.success("✅ Connected to MySQL Database.")
            return conn, 'mysql'
    except mysql.connector.Error as e:
        st.warning(f"⚠️ MySQL Connection failed: {e}. Falling back to SQLite.")

    # 2. Fallback to SQLite
    try:
        # check_same_thread=False is necessary for Streamlit's threading model
        conn = sqlite3.connect(SQLITE_DB, check_same_thread=False)
        st.info("ℹ️ Connected to SQLite Database.")
        create_sqlite_tables(conn)
        return conn, 'sqlite'
    except Exception as e:
        st.error(f"❌ SQLite Connection failed: {e}")
        return None, None

def create_sqlite_tables(conn):
    """Initializes a basic schema for SQLite fallback."""
    cursor = conn.cursor()
    
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY,
        roll_no TEXT UNIQUE,
        full_name TEXT,
        branch TEXT,
        cgpa REAL,
        skills TEXT,
        internships TEXT,
        hackathons TEXT,
        projects TEXT,
        certificates TEXT,
        resume_url TEXT,
        coding_profiles TEXT,
        FOREIGN KEY (id) REFERENCES users(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS recruiters (
        id INTEGER PRIMARY KEY,
        company_name TEXT,
        is_approved INTEGER DEFAULT 0,
        FOREIGN KEY (id) REFERENCES users(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    );
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recruiter_id INTEGER,
        company_id INTEGER,
        title TEXT NOT NULL,
        location TEXT,
        eligibility TEXT,
        description TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (recruiter_id) REFERENCES recruiters(id) ON DELETE CASCADE,
        FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER,
        student_id INTEGER,
        status TEXT DEFAULT 'applied',
        applied_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        action TEXT,
        entity TEXT,
        entity_id INTEGER,
        user_email TEXT
    );
    """)
    conn.commit()

def execute_query(conn, query, params=(), fetch=False, commit=False):
    """General function to execute SQL queries."""
    if conn is None:
        return None
        
    try:
        # ✅ FIX: Use isinstance() to check the connection type correctly
        # This resolves the AttributeError: 'CMySQLConnection' object has no attribute 'client_library'
        if isinstance(conn, mysql.connector.MySQLConnection) or isinstance(conn, mysql.connector.CMySQLConnection):
            # This block is for MySQL
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params)
            if commit:
                conn.commit()
            if fetch:
                result = cursor.fetchall()
                cursor.close()
                return result if result is not None else [] 
            cursor.close()
            return True
        
        elif isinstance(conn, sqlite3.Connection):
            # This block is for SQLite
            # SQLite uses '?' placeholders, so replace MySQL's '%s' if found
            if '%' in query:
                query = query.replace('%s', '?')
                
            cursor = conn.cursor()
            cursor.execute(query, params)
            if commit:
                conn.commit()
            if fetch:
                # Get column names for dictionary-like fetch
                columns = [desc[0] for desc in cursor.description]
                data = [dict(zip(columns, row)) for row in cursor.fetchall()]
                return data 
            return True

    except Exception as e:
        # Re-raise the exception to be handled by the calling function (e.g., register.py)
        # This allows register.py to catch specific errors like 'Duplicate Entry'
        raise e 
        
    return None