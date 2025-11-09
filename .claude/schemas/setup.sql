-- SQLite Database Schema for Work Unit Tracking
-- Created: 2025-10-03
-- Purpose: Queryable history for work units, decisions, and metrics

-- Work units tracking
CREATE TABLE IF NOT EXISTS work_units (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    objective TEXT NOT NULL,
    success_criteria TEXT,
    expected_files TEXT,
    expected_file_count INTEGER,
    actual_files TEXT,
    actual_file_count INTEGER,
    validation_command TEXT,
    validation_result TEXT,
    status TEXT DEFAULT 'planned',  -- planned, in_progress, complete, abandoned
    assessor_review_file TEXT,
    qa_review_file TEXT,
    tattletale_review_file TEXT,
    assessor_status TEXT,  -- APPROVED, NEEDS REVISION, REJECTED
    qa_status TEXT,
    tattletale_status TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT,
    notes TEXT
);

-- Work unit sessions (for multi-session units)
CREATE TABLE IF NOT EXISTS work_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_unit_id INTEGER,
    started_at TEXT,
    ended_at TEXT,
    notes TEXT,
    context_snapshot TEXT,
    FOREIGN KEY (work_unit_id) REFERENCES work_units(id)
);

-- Decisions log
CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    title TEXT NOT NULL,
    context TEXT,
    options_considered TEXT,
    decision TEXT,
    rationale TEXT,
    category TEXT,  -- architecture, interface, scope, quality, technical
    work_unit_id INTEGER,
    impact TEXT,
    validation TEXT,
    status TEXT DEFAULT 'proposed',  -- proposed, approved, implemented, reconsidered
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (work_unit_id) REFERENCES work_units(id)
);

-- Quality metrics
CREATE TABLE IF NOT EXISTS quality_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    work_unit_id INTEGER,
    tests_passing INTEGER,
    tests_total INTEGER,
    coverage_percent REAL,
    phase TEXT,
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (work_unit_id) REFERENCES work_units(id)
);

-- Agent reviews summary
CREATE TABLE IF NOT EXISTS agent_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_unit_id INTEGER,
    agent_type TEXT NOT NULL,  -- assessor, qa, tattletale
    review_file TEXT NOT NULL,
    finding_summary TEXT,
    recommendation TEXT,  -- APPROVE, REVISE, REJECT
    critical_issues TEXT,
    major_issues TEXT,
    minor_issues TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (work_unit_id) REFERENCES work_units(id)
);

-- Scope tracking
CREATE TABLE IF NOT EXISTS scope_variance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_unit_id INTEGER,
    checkpoint TEXT,  -- 25%, 50%, 75%, 100%
    expected_files INTEGER,
    actual_files INTEGER,
    variance_percent REAL,
    alert_level TEXT,  -- green, yellow, red
    action_taken TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (work_unit_id) REFERENCES work_units(id)
);

-- Session context snapshots
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    objective TEXT,
    files_modified TEXT,
    decisions_made TEXT,
    next_actions TEXT,
    work_units_completed INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_work_units_status ON work_units(status);
CREATE INDEX IF NOT EXISTS idx_work_units_date ON work_units(date);
CREATE INDEX IF NOT EXISTS idx_decisions_category ON decisions(category);
CREATE INDEX IF NOT EXISTS idx_decisions_work_unit ON decisions(work_unit_id);
CREATE INDEX IF NOT EXISTS idx_agent_reviews_work_unit ON agent_reviews(work_unit_id);
CREATE INDEX IF NOT EXISTS idx_agent_reviews_agent_type ON agent_reviews(agent_type);
CREATE INDEX IF NOT EXISTS idx_quality_metrics_work_unit ON quality_metrics(work_unit_id);

-- Useful views for common queries

-- Work unit summary view
CREATE VIEW IF NOT EXISTS v_work_unit_summary AS
SELECT
    w.id,
    w.date,
    w.objective,
    w.status,
    w.expected_file_count,
    w.actual_file_count,
    CASE
        WHEN w.actual_file_count IS NOT NULL AND w.expected_file_count > 0
        THEN ROUND(((w.actual_file_count * 100.0 / w.expected_file_count) - 100), 1)
        ELSE NULL
    END as scope_variance_percent,
    w.assessor_status,
    w.qa_status,
    w.tattletale_status,
    w.created_at,
    w.completed_at
FROM work_units w;

-- Agent review compliance view
CREATE VIEW IF NOT EXISTS v_agent_compliance AS
SELECT
    COUNT(*) as total_work_units,
    SUM(CASE WHEN assessor_status IS NOT NULL THEN 1 ELSE 0 END) as with_assessor,
    SUM(CASE WHEN qa_status IS NOT NULL THEN 1 ELSE 0 END) as with_qa,
    SUM(CASE WHEN tattletale_status IS NOT NULL THEN 1 ELSE 0 END) as with_tattletale,
    ROUND(100.0 * SUM(CASE WHEN assessor_status IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) as assessor_compliance_pct,
    ROUND(100.0 * SUM(CASE WHEN qa_status IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) as qa_compliance_pct,
    ROUND(100.0 * SUM(CASE WHEN tattletale_status IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) as tattletale_compliance_pct
FROM work_units
WHERE status IN ('complete', 'in_progress');

-- Scope creep analysis view
CREATE VIEW IF NOT EXISTS v_scope_creep AS
SELECT
    w.id,
    w.objective,
    w.expected_file_count,
    w.actual_file_count,
    ROUND(((w.actual_file_count * 100.0 / w.expected_file_count) - 100), 1) as variance_pct,
    CASE
        WHEN w.actual_file_count IS NULL THEN 'incomplete'
        WHEN ((w.actual_file_count * 100.0 / w.expected_file_count) - 100) < 25 THEN 'green'
        WHEN ((w.actual_file_count * 100.0 / w.expected_file_count) - 100) < 50 THEN 'yellow'
        ELSE 'red'
    END as alert_level
FROM work_units w
WHERE w.status = 'complete' AND w.expected_file_count > 0;
