-- ===============================================================
--  SECTION 1: DATABASE CREATION  (DDL)
-- ===============================================================
-- DDL = Data Definition Language → used to define structure of the database.

CREATE DATABASE IF NOT EXISTS cs;        -- Creates database if not already present
USE cs;                                  -- Selects 'cs' database to work with


-- ===============================================================
--  SECTION 2: DROP OLD TABLES (DDL)
-- ===============================================================
-- Removes existing tables to avoid duplicate creation when re-running script.
DROP TABLE IF EXISTS audit_logs, applications, jobs, companies, recruiters, students, admins, users;


-- ===============================================================
--  SECTION 3: TABLE CREATION (DDL)
-- ===============================================================
-- DDL commands define structure of all project tables.

-- 1️ USERS TABLE - stores all registered users with their role
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,                 -- Unique ID for each user
    email VARCHAR(255) UNIQUE NOT NULL,                -- Email for login
    password VARCHAR(255) NOT NULL,                    -- Password for login
    role ENUM('student','recruiter','admin') NOT NULL  -- Role type
);

-- 2️ STUDENTS TABLE - holds student academic and personal info
CREATE TABLE students (
    id INT PRIMARY KEY,                                -- Links to users.id
    roll_no VARCHAR(50) UNIQUE,                        -- University roll number
    full_name VARCHAR(255),
    branch VARCHAR(100),
    cgpa DECIMAL(3,2),
    skills TEXT,
    internships TEXT,
    hackathons TEXT,
    projects TEXT,
    certificates TEXT,
    resume_url TEXT,
    coding_profiles TEXT,
    FOREIGN KEY (id) REFERENCES users(id) ON DELETE CASCADE
);

-- 3️ RECRUITERS TABLE - stores recruiter info (company, approval)
CREATE TABLE recruiters (
    id INT PRIMARY KEY,                                -- Linked with users.id
    company_name VARCHAR(255),
    is_approved BOOLEAN DEFAULT 0,                     -- 0 = pending, 1 = approved
    FOREIGN KEY (id) REFERENCES users(id) ON DELETE CASCADE
);

-- 4️ COMPANIES TABLE - stores unique company names
CREATE TABLE companies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL
);

-- 5️ JOBS TABLE - stores job postings made by recruiters
CREATE TABLE jobs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    recruiter_id INT,
    company_id INT,
    title VARCHAR(255) NOT NULL,                       -- Job title
    location VARCHAR(255),
    eligibility VARCHAR(255),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,    -- Time job was created
    FOREIGN KEY (recruiter_id) REFERENCES recruiters(id) ON DELETE CASCADE,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 6️ APPLICATIONS TABLE - links students and jobs
CREATE TABLE applications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    job_id INT,
    student_id INT,
    status ENUM('applied', 'shortlisted', 'rejected', 'accepted') DEFAULT 'applied',
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

-- 7  AUDIT LOGS TABLE - automatically records events (via triggers)
CREATE TABLE audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    action VARCHAR(255),          -- e.g., INSERT / STATUS UPDATED
    entity VARCHAR(255),          -- table name (users/jobs/applications)
    entity_id INT,                -- record ID
    user_email VARCHAR(255)       -- user who performed action
);

-- 8️ ADMINS TABLE - stores department info for admin users
CREATE TABLE admins (
    id INT PRIMARY KEY,                                -- Linked with users.id
    department VARCHAR(255) NOT NULL,                  -- e.g. Placement Cell
    FOREIGN KEY (id) REFERENCES users(id) ON DELETE CASCADE
);


-- ===============================================================
--  SECTION 4: TRIGGERS (Automation) 
-- ===============================================================
-- TRIGGERS = Auto actions that run when specific events happen in tables.
-- Purpose: Automatically log actions in the 'audit_logs' table.

DELIMITER $$

--  Trigger 1: Runs automatically when a new user registers
CREATE TRIGGER trg_user_insert
AFTER INSERT ON users
FOR EACH ROW
BEGIN
    -- Logs new user registration in audit_logs
    INSERT INTO audit_logs (action, entity, entity_id, user_email)
    VALUES ('INSERT', 'users', NEW.id, NEW.email);
END$$

-- Trigger 2: Runs when a recruiter posts a new job
CREATE TRIGGER trg_job_insert
AFTER INSERT ON jobs
FOR EACH ROW
BEGIN
    -- Logs job posting details (who posted and what job)
    INSERT INTO audit_logs (action, entity, entity_id, user_email)
    VALUES ('INSERT', 'jobs', NEW.id,
            (SELECT email FROM users WHERE id = (SELECT id FROM recruiters WHERE id = NEW.recruiter_id)));
END$$

--  Trigger 3: Runs when recruiter updates application status
CREATE TRIGGER trg_application_status_update
AFTER UPDATE ON applications
FOR EACH ROW
BEGIN
    -- Logs status changes like shortlisted/rejected/accepted
    INSERT INTO audit_logs (action, entity, entity_id, user_email)
    VALUES (CONCAT('STATUS ', NEW.status), 'applications', NEW.id,
            (SELECT email FROM users WHERE id = NEW.student_id));
END$$

DELIMITER ;


-- ===============================================================
-- SECTION 5: STORED PROCEDURES (Reusable Tasks)
-- ===============================================================
-- PROCEDURES = Predefined SQL tasks that can be called any time.

DELIMITER $$

--  Procedure 1: register_user
CREATE PROCEDURE register_user (
    IN p_email VARCHAR(255),
    IN p_password VARCHAR(255),
    IN p_role ENUM('student','recruiter','admin')
)
BEGIN
    -- Adds a new user entry (used during registration)
    INSERT INTO users (email, password, role)
    VALUES (p_email, p_password, p_role);
END$$

--  Procedure 2: add_job
CREATE PROCEDURE add_job (
    IN p_recruiter_id INT,
    IN p_company_id INT,
    IN p_title VARCHAR(255),
    IN p_location VARCHAR(255),
    IN p_eligibility VARCHAR(255),
    IN p_description TEXT
)
BEGIN
    -- Adds a new job listing (used when recruiter posts a job)
    INSERT INTO jobs (recruiter_id, company_id, title, location, eligibility, description)
    VALUES (p_recruiter_id, p_company_id, p_title, p_location, p_eligibility, p_description);
END$$

--  Procedure 3: get_application_count
CREATE PROCEDURE get_application_count (
    IN p_job_id INT,
    OUT total_apps INT
)
BEGIN
    -- Counts total number of students who applied for a job
    SELECT COUNT(*) INTO total_apps FROM applications WHERE job_id = p_job_id;
    -- Returns result as a display value
    SELECT total_apps AS total_apps;
END$$

DELIMITER ;


-- ===============================================================
--  SECTION 6: FUNCTION (Single Return Value)
-- ===============================================================
-- FUNCTION = Executes a query and returns one value.

DELIMITER $$
CREATE FUNCTION get_student_name(p_student_id INT)
RETURNS VARCHAR(255)
DETERMINISTIC
BEGIN
    DECLARE result VARCHAR(255);
    -- Fetches student name for given ID
    SELECT full_name INTO result FROM students WHERE id = p_student_id;
    RETURN result; -- Returns name back
END$$
DELIMITER ;


-- ===============================================================
--  SECTION 7: SAMPLE DATA (DML)
-- ===============================================================
-- DML = Data Manipulation Language → used to insert data in tables.

-- USERS
INSERT INTO users (email, password, role) VALUES
('mohammedbilal96654@gmail.com', 'bilal@1234', 'student'),
('nawaz@gmail.com', '9739240', 'student'),
('recruiter1@gmail.com', 'rec123', 'recruiter'),
('admin1@gmail.com', 'admin123', 'admin');

-- STUDENTS
INSERT INTO students (id, roll_no, full_name, branch, cgpa)
VALUES
(1, 'PES2UG23CS344', 'Mohammed Bilal', 'CSE', 8.2),
(2, 'PES2UG23CS345', 'Nawaz Ahmed', 'ISE', 7.9);

-- RECRUITER
INSERT INTO recruiters (id, company_name, is_approved)
VALUES (3, 'Infosys', 1);

-- ADMIN
INSERT INTO admins (id, department)
VALUES (4, 'Placement Cell');

-- COMPANIES
INSERT INTO companies (name) VALUES ('Infosys'), ('TCS'), ('Google');

-- JOBS
INSERT INTO jobs (recruiter_id, company_id, title, location, eligibility, description)
VALUES
(3, 1, 'Software Engineer Intern', 'Bangalore', 'CGPA > 7.0', 'Work on backend APIs.'),
(3, 2, 'Frontend Developer', 'Chennai', 'CGPA > 6.5', 'Build UI components.');

-- APPLICATIONS
INSERT INTO applications (job_id, student_id, status)
VALUES
(1, 1, 'applied'),
(1, 2, 'shortlisted'),
(2, 1, 'applied');


-- ===============================================================
-- 🔍 SECTION 8: TEST COMMANDS (To show in Viva)
-- ===============================================================
-- Run these to demonstrate each DBMS feature live.

-- DML Proof → View Data
SELECT * FROM users;
SELECT * FROM applications;

-- TRIGGER Proof → Check logs auto created
SELECT * FROM audit_logs;

-- PROCEDURE Proof → Call stored procedure
CALL get_application_count(1, @total);
SELECT @total AS total_applications;

-- FUNCTION Proof → Call user-defined function
SELECT get_student_name(1) AS Student_Name;

-- DDL Proof → Verify structure
SHOW TABLES;
