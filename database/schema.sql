BEGIN;

SET LOCAL search_path = public, pg_catalog;

DROP TABLE IF EXISTS departments CASCADE;
CREATE TABLE departments (
    department_id INTEGER PRIMARY KEY,
    department_name TEXT NOT NULL,
    department_head INTEGER NOT NULL
);

DROP TABLE IF EXISTS locations CASCADE;
CREATE TABLE locations (
    location_id INTEGER PRIMARY KEY,
    location_name TEXT NOT NULL,
    address TEXT,
    city TEXT,
    state TEXT,
    postal_code TEXT,
    location_type TEXT NOT NULL CHECK (location_type IN ('HQ', 'Regional Office', 'Retail Banking'))
);

DROP TABLE IF EXISTS teams CASCADE;
CREATE TABLE teams (
    team_id INTEGER PRIMARY KEY,
    team_name TEXT NOT NULL,
    department_id INTEGER NOT NULL REFERENCES departments (department_id),
    team_lead INTEGER NOT NULL
);

DROP TABLE IF EXISTS positions CASCADE;
CREATE TABLE positions (
    position_id INTEGER PRIMARY KEY,
    position_title TEXT NOT NULL,
    department_id INTEGER NOT NULL REFERENCES departments (department_id),
    department_name TEXT NOT NULL,
    seniority_level TEXT CHECK (seniority_level IN ('Entry', 'Intermediate', 'Senior', 'Manager', 'Director', 'Executive')),
    description TEXT
);

DROP TABLE IF EXISTS employees CASCADE;
CREATE TABLE employees (
    employee_id INTEGER PRIMARY KEY,
    employee_fname TEXT NOT NULL,
    employee_lname TEXT NOT NULL,
    location_id INTEGER NOT NULL REFERENCES locations (location_id),
    department_id INTEGER REFERENCES departments (department_id),
    team_id INTEGER REFERENCES teams (team_id),
    supervisor_id INTEGER NOT NULL REFERENCES employees (employee_id) DEFERRABLE INITIALLY DEFERRED,
    position_id INTEGER NOT NULL REFERENCES positions (position_id),
    seniority_level TEXT CHECK (seniority_level IN ('Entry', 'Intermediate', 'Senior', 'Manager', 'Director', 'Executive')),
    hire_date TIMESTAMP NOT NULL,
    role_start_date TIMESTAMP NOT NULL,
    employment_status TEXT NOT NULL CHECK (employment_status IN ('Active', 'Leave', 'Terminated')),
    work_arrangement TEXT CHECK (work_arrangement IN ('Remote', 'Hybrid', 'On-site'))
);

ALTER TABLE departments
    ADD CONSTRAINT departments_head_fkey
    FOREIGN KEY (department_head) REFERENCES employees (employee_id)
    DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE teams
    ADD CONSTRAINT teams_lead_fkey
    FOREIGN KEY (team_lead) REFERENCES employees (employee_id)
    DEFERRABLE INITIALLY DEFERRED;

DROP TABLE IF EXISTS employee_history CASCADE;
CREATE TABLE employee_history (
    entry_id INTEGER PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees (employee_id),
    position_id INTEGER NOT NULL REFERENCES positions (position_id),
    department_id INTEGER NOT NULL REFERENCES departments (department_id),
    location_id INTEGER NOT NULL REFERENCES locations (location_id),
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP,
    is_current BOOLEAN NOT NULL DEFAULT FALSE,
    change_reason TEXT
);

DROP TABLE IF EXISTS employee_training CASCADE;
CREATE TABLE employee_training (
    training_id INTEGER PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees (employee_id),
    program_name TEXT NOT NULL,
    program_category TEXT NOT NULL,
    training_type TEXT NOT NULL,
    provider TEXT,
    is_mandatory BOOLEAN NOT NULL,
    assigned_date TIMESTAMP NOT NULL,
    start_date TIMESTAMP,
    due_date TIMESTAMP,
    completion_date TIMESTAMP,
    completion_status TEXT NOT NULL CHECK (completion_status IN ('Not started', 'In progress', 'Completed', 'Withdrawn', 'Expired')),
    estimated_hours DOUBLE PRECISION CHECK (estimated_hours >= 0),
    actual_hours DOUBLE PRECISION CHECK (actual_hours >= 0),
    assessment_score DOUBLE PRECISION CHECK (assessment_score BETWEEN 0 AND 100),
    certification_awarded BOOLEAN NOT NULL,
    certification_expiry TIMESTAMP,
    employee_feedback TEXT,
    manager_notes TEXT
);

DROP TABLE IF EXISTS email_accounts CASCADE;
CREATE TABLE email_accounts (
    employee_id INTEGER NOT NULL REFERENCES employees (employee_id),
    email_address TEXT PRIMARY KEY
);

DROP TABLE IF EXISTS email_records CASCADE;
CREATE TABLE email_records (
    email_id INTEGER PRIMARY KEY,
    thread_id INTEGER NOT NULL,
    sender_id INTEGER NOT NULL REFERENCES employees (employee_id),
    sent_at TIMESTAMP NOT NULL,
    subject TEXT,
    body TEXT NOT NULL,
    reply_to_id INTEGER REFERENCES email_records (email_id) DEFERRABLE INITIALLY DEFERRED,
    has_attachments BOOLEAN NOT NULL DEFAULT FALSE,
    is_internal BOOLEAN NOT NULL DEFAULT TRUE
);

DROP TABLE IF EXISTS email_recipients CASCADE;
CREATE TABLE email_recipients (
    email_id INTEGER NOT NULL REFERENCES email_records (email_id),
    recipient_id INTEGER NOT NULL REFERENCES employees (employee_id),
    recipient_type TEXT NOT NULL CHECK (recipient_type IN ('to', 'cc', 'bcc')),
    PRIMARY KEY (email_id, recipient_id, recipient_type)
);

DROP TABLE IF EXISTS projects CASCADE;
CREATE TABLE projects (
    project_id INTEGER PRIMARY KEY,
    supervisor_id INTEGER REFERENCES employees (employee_id),
    project_name TEXT NOT NULL,
    type TEXT,
    description TEXT,
    start_date TIMESTAMP NOT NULL,
    target_end_date TIMESTAMP,
    actual_end_date TIMESTAMP,
    status TEXT NOT NULL CHECK (status IN ('Planned', 'Active', 'Suspended', 'Complete', 'Cancelled'))
);

DROP TABLE IF EXISTS project_tasks CASCADE;
CREATE TABLE project_tasks (
    task_id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects (project_id),
    employee_id INTEGER REFERENCES employees (employee_id),
    title TEXT NOT NULL,
    description TEXT,
    priority TEXT NOT NULL CHECK (priority IN ('Low', 'Medium', 'High', 'Critical')),
    complexity TEXT CHECK (complexity IN ('Low', 'Medium', 'High')),
    created_date DATE NOT NULL,
    start_date DATE,
    due_date DATE,
    complete_date DATE,
    task_status TEXT NOT NULL CHECK (task_status IN ('Not Started', 'In Progress', 'Suspended', 'Complete', 'Cancelled')),
    estimated_hours DOUBLE PRECISION CHECK (estimated_hours >= 0),
    actual_hours DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK (actual_hours >= 0),
    revision_count INTEGER NOT NULL DEFAULT 0 CHECK (revision_count >= 0)
);

DROP TABLE IF EXISTS employee_goals CASCADE;
CREATE TABLE employee_goals (
    goal_id INTEGER PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees (employee_id),
    goal_description TEXT NOT NULL,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    complete_status TEXT CHECK (complete_status IN ('Not Started', 'In Progress', 'Completed', 'Cancelled')),
    complete_desc TEXT
);

DROP TABLE IF EXISTS performance_reviews CASCADE;
CREATE TABLE performance_reviews (
    review_id INTEGER PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees (employee_id),
    reviewer_id INTEGER NOT NULL REFERENCES employees (employee_id),
    review_period TEXT NOT NULL,
    task_completion_pct DOUBLE PRECISION CHECK (task_completion_pct BETWEEN 0 AND 100),
    goal_completion_pct DOUBLE PRECISION CHECK (goal_completion_pct BETWEEN 0 AND 100),
    rating_work_quality DOUBLE PRECISION CHECK (rating_work_quality BETWEEN 1 AND 5),
    comments_work_quality TEXT,
    rating_time_mgmt DOUBLE PRECISION CHECK (rating_time_mgmt BETWEEN 1 AND 5),
    comments_time_mgmt TEXT,
    rating_comm DOUBLE PRECISION CHECK (rating_comm BETWEEN 1 AND 5),
    comments_comm TEXT,
    rating_adapt DOUBLE PRECISION CHECK (rating_adapt BETWEEN 1 AND 5),
    comments_adapt TEXT,
    rating_overall DOUBLE PRECISION CHECK (rating_overall BETWEEN 1 AND 5),
    comments_overall TEXT,
    development_areas TEXT
);

DROP TABLE IF EXISTS feedback_survey_data CASCADE;
CREATE TABLE feedback_survey_data (
    survey_id INTEGER PRIMARY KEY,
    subject_employee_id INTEGER NOT NULL REFERENCES employees (employee_id),
    reviewer_id INTEGER REFERENCES employees (employee_id),
    reviewer_relationship TEXT NOT NULL CHECK (reviewer_relationship IN ('Peer', 'Stakeholder', 'Other')),
    survey_date TIMESTAMP NOT NULL,
    project_id INTEGER REFERENCES projects (project_id),
    competency TEXT NOT NULL,
    rating DOUBLE PRECISION CHECK (rating BETWEEN 1 AND 5),
    feedback_text TEXT,
    feedback_period TEXT,
    visibility_level TEXT NOT NULL CHECK (visibility_level IN ('Manager', 'HR', 'Employee'))
);

DROP TABLE IF EXISTS manager_notes CASCADE;
CREATE TABLE manager_notes (
    note_id INTEGER PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees (employee_id),
    supervisor_id INTEGER NOT NULL REFERENCES employees (employee_id),
    recorded_date TIMESTAMP NOT NULL,
    observed_date TIMESTAMP,
    observation_type TEXT CHECK (observation_type IN ('Achievement', 'Development', 'Concern', 'General')),
    related_project_id INTEGER REFERENCES projects (project_id),
    observation_text TEXT NOT NULL,
    follow_up_date TIMESTAMP,
    follow_up_status TEXT CHECK (follow_up_status IN ('Pending', 'Completed'))
);

DROP TABLE IF EXISTS recognition_logs CASCADE;
CREATE TABLE recognition_logs ();

DROP TABLE IF EXISTS q12_questions CASCADE;
CREATE TABLE q12_questions (
    id TEXT PRIMARY KEY,
    text TEXT NOT NULL,
    element TEXT,
    engagement_need TEXT,
    engagement_desc TEXT
);

DROP TABLE IF EXISTS q12_groups CASCADE;
CREATE TABLE q12_groups (
    group_id INTEGER PRIMARY KEY,
    group_name TEXT NOT NULL,
    group_type TEXT NOT NULL CHECK (group_type IN ('Department', 'Team', 'Manager', 'Location', 'Company')),
    department_id INTEGER REFERENCES departments (department_id),
    team_id INTEGER REFERENCES teams (team_id),
    manager_id INTEGER REFERENCES employees (employee_id)
);

DROP TABLE IF EXISTS q12_surveys CASCADE;
CREATE TABLE q12_surveys (
    survey_id INTEGER PRIMARY KEY,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    reporting_period TEXT NOT NULL,
    eligible_employees INTEGER NOT NULL CHECK (eligible_employees >= 0),
    respondent_count INTEGER NOT NULL CHECK (respondent_count >= 0)
);

DROP TABLE IF EXISTS q12_results CASCADE;
CREATE TABLE q12_results (
    survey_id INTEGER NOT NULL REFERENCES q12_surveys (survey_id),
    group_id INTEGER NOT NULL REFERENCES q12_groups (group_id),
    question_id TEXT NOT NULL REFERENCES q12_questions (id),
    response_count INTEGER CHECK (response_count >= 0),
    mean_score DOUBLE PRECISION CHECK (mean_score BETWEEN 1 AND 5),
    top_box_pct DOUBLE PRECISION CHECK (top_box_pct BETWEEN 0 AND 100),
    score_1_count INTEGER CHECK (score_1_count >= 0),
    score_2_count INTEGER CHECK (score_2_count >= 0),
    score_3_count INTEGER CHECK (score_3_count >= 0),
    score_4_count INTEGER CHECK (score_4_count >= 0),
    score_5_count INTEGER CHECK (score_5_count >= 0),
    benchmark_pct DOUBLE PRECISION CHECK (benchmark_pct BETWEEN 0 AND 100),
    is_suppressed BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (survey_id, group_id, question_id)
);

DROP TABLE IF EXISTS self_assessments CASCADE;
CREATE TABLE self_assessments (
    assessment_id INTEGER PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees (employee_id),
    review_period TEXT NOT NULL,
    major_accomplishments TEXT,
    challenges_encountered TEXT,
    goal_reflections TEXT,
    skills_developed TEXT,
    areas_for_improvement TEXT,
    career_interests TEXT,
    requested_support TEXT,
    submission_date TIMESTAMP NOT NULL
);

CREATE INDEX employees_department_idx ON employees (department_id);
CREATE INDEX employees_team_idx ON employees (team_id);
CREATE INDEX employees_supervisor_idx ON employees (supervisor_id);
CREATE INDEX employee_history_employee_idx ON employee_history (employee_id);
CREATE INDEX employee_training_employee_idx ON employee_training (employee_id);
CREATE INDEX email_accounts_employee_idx ON email_accounts (employee_id);
CREATE INDEX email_records_sender_idx ON email_records (sender_id);
CREATE INDEX email_records_thread_idx ON email_records (thread_id);
CREATE INDEX email_recipients_recipient_idx ON email_recipients (recipient_id);
CREATE INDEX project_tasks_project_idx ON project_tasks (project_id);
CREATE INDEX project_tasks_employee_idx ON project_tasks (employee_id);
CREATE INDEX employee_goals_employee_period_idx ON employee_goals (employee_id, end_date);
CREATE INDEX performance_reviews_employee_period_idx ON performance_reviews (employee_id, review_period);
CREATE INDEX feedback_subject_idx ON feedback_survey_data (subject_employee_id);
CREATE INDEX manager_notes_employee_idx ON manager_notes (employee_id);
CREATE INDEX q12_results_group_idx ON q12_results (group_id);
CREATE INDEX self_assessments_employee_period_idx ON self_assessments (employee_id, review_period);

COMMIT;
