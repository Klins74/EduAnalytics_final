-- Create Metabase metadata database
CREATE DATABASE metabase;
CREATE USER metabase WITH PASSWORD 'metabase_password';
GRANT ALL PRIVILEGES ON DATABASE metabase TO metabase;

-- Create Superset metadata database  
CREATE DATABASE superset;
CREATE USER superset WITH PASSWORD 'superset_password';
GRANT ALL PRIVILEGES ON DATABASE superset TO superset;

-- Grant read access to EduAnalytics data for BI tools
GRANT CONNECT ON DATABASE eduanalytics TO metabase;
GRANT CONNECT ON DATABASE eduanalytics TO superset;

-- Switch to eduanalytics database and grant schema access
\c eduanalytics;

-- Grant usage on schema
GRANT USAGE ON SCHEMA public TO metabase;
GRANT USAGE ON SCHEMA public TO superset;

-- Grant select on all existing tables
GRANT SELECT ON ALL TABLES IN SCHEMA public TO metabase;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO superset;

-- Grant select on future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO metabase;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO superset;

-- Create read-only views for analytics
CREATE OR REPLACE VIEW analytics_course_metrics AS
SELECT 
    c.id as course_id,
    c.name as course_name,
    c.code as course_code,
    COUNT(DISTINCT e.id) as total_enrollments,
    COUNT(DISTINCT a.id) as total_assignments,
    COUNT(DISTINCT s.id) as total_submissions,
    AVG(g.score) as avg_score,
    COUNT(DISTINCT CASE WHEN s.status = 'submitted' THEN s.id END) as on_time_submissions,
    COUNT(DISTINCT CASE WHEN s.status = 'late' THEN s.id END) as late_submissions,
    c.created_at,
    c.updated_at
FROM courses c
LEFT JOIN enrollments e ON c.id = e.course_id
LEFT JOIN assignments a ON c.id = a.course_id
LEFT JOIN submissions s ON a.id = s.assignment_id
LEFT JOIN grades g ON s.id = g.submission_id
GROUP BY c.id, c.name, c.code, c.created_at, c.updated_at;

CREATE OR REPLACE VIEW analytics_student_performance AS
SELECT 
    u.id as student_id,
    u.email as student_email,
    u.first_name,
    u.last_name,
    c.id as course_id,
    c.name as course_name,
    COUNT(DISTINCT s.id) as total_submissions,
    AVG(g.score) as avg_score,
    COUNT(DISTINCT CASE WHEN s.status = 'submitted' THEN s.id END) as on_time_submissions,
    COUNT(DISTINCT CASE WHEN s.status = 'late' THEN s.id END) as late_submissions,
    COUNT(DISTINCT CASE WHEN g.score >= 80 THEN g.id END) as high_scores,
    MAX(s.submitted_at) as last_submission_date
FROM users u
JOIN enrollments e ON u.id = e.user_id
JOIN courses c ON e.course_id = c.id
LEFT JOIN assignments a ON c.id = a.course_id
LEFT JOIN submissions s ON a.id = s.assignment_id AND s.student_id = u.id
LEFT JOIN grades g ON s.id = g.submission_id
WHERE u.role = 'student'
GROUP BY u.id, u.email, u.first_name, u.last_name, c.id, c.name;

CREATE OR REPLACE VIEW analytics_assignment_stats AS
SELECT 
    a.id as assignment_id,
    a.title as assignment_title,
    a.assignment_type,
    c.id as course_id,
    c.name as course_name,
    a.due_date,
    COUNT(DISTINCT s.id) as total_submissions,
    COUNT(DISTINCT CASE WHEN s.status = 'submitted' THEN s.id END) as on_time_submissions,
    COUNT(DISTINCT CASE WHEN s.status = 'late' THEN s.id END) as late_submissions,
    AVG(g.score) as avg_score,
    MIN(g.score) as min_score,
    MAX(g.score) as max_score,
    COUNT(DISTINCT CASE WHEN g.score >= 80 THEN g.id END) as high_scores,
    COUNT(DISTINCT CASE WHEN g.score < 60 THEN g.id END) as low_scores
FROM assignments a
JOIN courses c ON a.course_id = c.id
LEFT JOIN submissions s ON a.id = s.assignment_id
LEFT JOIN grades g ON s.id = g.submission_id
GROUP BY a.id, a.title, a.assignment_type, c.id, c.name, a.due_date;

-- Grant access to views
GRANT SELECT ON analytics_course_metrics TO metabase;
GRANT SELECT ON analytics_course_metrics TO superset;
GRANT SELECT ON analytics_student_performance TO metabase;
GRANT SELECT ON analytics_student_performance TO superset;
GRANT SELECT ON analytics_assignment_stats TO metabase;
GRANT SELECT ON analytics_assignment_stats TO superset;
