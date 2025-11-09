-- Vector Database Schema for WU09
-- Purpose: Store document embeddings for semantic search
-- Strategy: sqlite-vss (preferred) with FTS5 fallback

-- ============================================================================
-- Core Tables
-- ============================================================================

-- Documents table: Stores metadata and full content
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,              -- Document ID (e.g., "WU00-A", "vision-plan-2025-11-01-1700")
    type TEXT NOT NULL,               -- Document type: 'work_unit' or 'agent_review'
    path TEXT NOT NULL,               -- Absolute file path
    content TEXT NOT NULL,            -- Full document content (YAML frontmatter stripped)
    created_at TEXT NOT NULL,         -- ISO 8601 timestamp (from embedding metadata)
    updated_at TEXT NOT NULL          -- ISO 8601 timestamp (for future updates)
);

-- Embeddings table: Stores vector embeddings
CREATE TABLE IF NOT EXISTS embeddings (
    document_id TEXT PRIMARY KEY,     -- Links to documents.id
    embedding BLOB NOT NULL,          -- 1536 floats stored as binary (6144 bytes)
    model TEXT NOT NULL,              -- Model name (e.g., "nomic-embed-text-v1.5")
    provider TEXT NOT NULL,           -- Provider: "lm_studio", "openai", or "dry-run"
    dimensions INTEGER NOT NULL,      -- Always 1536 for current model
    created_at TEXT NOT NULL,         -- ISO 8601 timestamp
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- ============================================================================
-- FTS5 Fallback (Always Created)
-- ============================================================================

-- Full-text search virtual table (fallback when sqlite-vss unavailable)
CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
    id UNINDEXED,                     -- Don't index ID (use for retrieval only)
    content,                          -- Index full content for text search
    content=documents,                -- Pull content from documents table
    content_rowid=rowid               -- Link to documents.rowid
);

-- Triggers to keep FTS5 index synchronized with documents table
CREATE TRIGGER IF NOT EXISTS documents_fts_insert AFTER INSERT ON documents BEGIN
    INSERT INTO documents_fts(rowid, id, content) VALUES (new.rowid, new.id, new.content);
END;

CREATE TRIGGER IF NOT EXISTS documents_fts_update AFTER UPDATE ON documents BEGIN
    UPDATE documents_fts SET content = new.content WHERE rowid = old.rowid;
END;

CREATE TRIGGER IF NOT EXISTS documents_fts_delete AFTER DELETE ON documents BEGIN
    DELETE FROM documents_fts WHERE rowid = old.rowid;
END;

-- ============================================================================
-- Indices for Performance
-- ============================================================================

-- Index on document type for filtering
CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(type);

-- Index on creation date for temporal queries
CREATE INDEX IF NOT EXISTS idx_documents_created ON documents(created_at);

-- ============================================================================
-- sqlite-vss Integration (Optional)
-- ============================================================================

-- NOTE: The following table is created dynamically at runtime if sqlite-vss is available
-- It cannot be created via this SQL file due to extension loading requirements

-- CREATE VIRTUAL TABLE IF NOT EXISTS vss_embeddings USING vss0(
--     embedding(1536)
-- );

-- This table will be created by VectorDB.initialize_schema() if:
-- 1. sqlite-vss extension is loadable
-- 2. vss_version() function is accessible

-- ============================================================================
-- Usage Notes
-- ============================================================================

-- FTS5 Fallback Search Pattern:
--   1. Use documents_fts to find candidate documents via text search
--   2. Load embeddings for candidates
--   3. Compute cosine similarity in Python
--   4. Rank by similarity score
--   5. Return top K results

-- sqlite-vss Search Pattern:
--   1. Use vss_embeddings.vss_search() for K-nearest neighbors
--   2. Join with documents table for metadata
--   3. Return ranked results directly from SQL

-- Storage Efficiency:
--   - JSON embedding: ~14KB per document
--   - Binary BLOB: ~6KB per document (1536 floats * 4 bytes)
--   - Space savings: ~57%

-- ============================================================================
