-- Command Pattern Database Schema
-- Tracks command history, pattern statistics, and safe-listed commands

-- Command history table
-- Records every command classification with metadata
CREATE TABLE IF NOT EXISTS command_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    command TEXT NOT NULL,                    -- Original command text
    command_hash TEXT NOT NULL,               -- Normalized hash for pattern matching
    risk_level TEXT NOT NULL,                 -- tier1_safe, tier2_review, tier3_block
    risk_score REAL NOT NULL,                 -- Confidence score 0.0-1.0
    matched_patterns TEXT,                    -- JSON array of matched pattern descriptions
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    approved BOOLEAN DEFAULT NULL             -- NULL=pending, 1=approved, 0=rejected
);

-- Pattern statistics table
-- Tracks reliability of individual patterns
CREATE TABLE IF NOT EXISTS pattern_stats (
    pattern TEXT PRIMARY KEY,                 -- Pattern identifier
    total_count INTEGER DEFAULT 0,            -- Total times pattern matched
    approval_count INTEGER DEFAULT 0,         -- Times user approved
    rejection_count INTEGER DEFAULT 0,        -- Times user rejected
    last_seen DATETIME                        -- Last time pattern matched
);

-- Safe-listed commands
-- Commands that have been approved N times and are auto-approved
CREATE TABLE IF NOT EXISTS safe_list (
    command_hash TEXT PRIMARY KEY,            -- Normalized command hash
    command_template TEXT NOT NULL,           -- Human-readable template
    approval_count INTEGER DEFAULT 0,         -- Number of approvals
    added_date DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indices for performance
CREATE INDEX IF NOT EXISTS idx_command_hash ON command_history(command_hash);
CREATE INDEX IF NOT EXISTS idx_timestamp ON command_history(timestamp);
CREATE INDEX IF NOT EXISTS idx_risk_level ON command_history(risk_level);
CREATE INDEX IF NOT EXISTS idx_approved ON command_history(approved);
