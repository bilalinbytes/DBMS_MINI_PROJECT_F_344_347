-----
# 🎓 CareerSphere: Campus Placement Portal

CareerSphere is a modern, web-based platform designed to streamline and centralize the campus placement process. It connects students, recruiters, and administrators in a unified environment, managing everything from student profile creation and job applications to recruiter approvals and system analytics.

## ✨ Features

  * **Role-Based Authentication:** Secure login for **Admin**, **Student**, and **Recruiter** roles.
  * **Student Management:**
      * Detailed profile creation (CGPA, skills, projects, certifications).
      * View and apply to relevant job postings.
      * Track application status (Applied, Shortlisted, Accepted, Rejected).
  * **Recruiter Workflow:**
      * Recruiter account approval handled by the Admin.
      * Create, view, and manage job postings.
      * Review and update applicant status.
  * **Admin Control:**
      * Approve/Reject new recruiter accounts.
      * System-wide analytics and user management.
  * **Database Flexibility:** Designed to work seamlessly with **MySQL** (for production/robust testing) and **SQLite** (for quick local development/fallback).

## 🚀 Getting Started

Follow these steps to get your CareerSphere application running locally.

### Prerequisites

1. **Python 3.x**
2. **MySQL Server** (If using MySQL mode)
3. **Required Python Libraries:**
    ```bash
    pip install streamlit mysql-connector-python pandas
    ```

### Installation and Setup

1. **Clone the Repository (or ensure you have the project files):**
    ```bash
    # Assuming your project directory is named DBMS_PROJECT
    cd DBMS_PROJECT
    ```

2. **Configure Database Connection:**

    Open **`database.py`** and ensure the connection details match your MySQL setup (or rely on the default SQLite fallback).

    ```python
    # CareerSphere/database.py snippet
    MYSQL_HOST = "localhost"
    MYSQL_USER = "root"
    MYSQL_PASSWORD = "your_mysql_password"  # <-- UPDATE THIS
    MYSQL_DATABASE = "careersphere"
    ```

3. **Run the Application:**
    ```bash
    streamlit run app.py
    ```

4. **Initialize the Database Schema:**

    Once the app opens in your browser, click the **"Initialize Database Schema (Run DDL_DML.sql)"** button. This executes all table creations, triggers, stored procedures, and initial demo data (including the default users).

## 🔑 Default Credentials

Use these accounts to test the application's different roles immediately after initialization:

| Role | Email | Password | Status |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@cs.edu` | `admin` | Fully Approved |
| **Student** | `student@cs.edu` | `student` | Initial Profile (Alice Smith) |
| **Recruiter** | `recruiter@corp.com` | `recruiter` | Approved |

## 📁 Project Structure

````

DBMS_PROJECT/
├── pages/
│   ├── admin_dashboard.py
│   ├── analytics.py
│   ├── applications.py
│   ├── job_postings.py
│   ├── login.py
│   ├── profile_update.py
│   ├── recruiter_dashboard.py
│   ├── register.py
│   └── student_dashboard.py
├── app.py                     # Main application entry point
├── database.py                # Database connection and query utility (MySQL/SQLite)
├── DDL_DML.sql                # Complete schema definition, procedures, triggers, and demo data
└── style.css                  # Custom Streamlit styling

```

## 🛠️ Key Technologies

  * **Frontend/App Framework:** Streamlit  
  * **Backend Database:** MySQL (Primary) and SQLite (Fallback)  
  * **Language:** Python  
  * **Database Features Utilized:**
      * Stored Procedures (`register_student_proc`, `get_application_count`)
      * Triggers (`after_user_insert`, audit logging)
      * Transactions (Atomicity for registration)
      * Foreign Keys and Constraints (`ON DELETE CASCADE`, `UNIQUE`)

## 🤝 Contribution

This project was developed as a comprehensive solution for a Database Management System (DBMS) project. For further development or academic use, please feel free to fork the repository.

---

### 👨‍💻 Made By:
**SRN PES2UG23CS344** and **PES2UG23CS347**

-----
```

---

