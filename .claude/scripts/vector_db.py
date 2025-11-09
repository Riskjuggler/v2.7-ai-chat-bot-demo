#!/usr/bin/env python3
"""
Vector Database for Semantic Search (WU09)

Provides vector similarity search over work units and agent reviews using:
- Primary: sqlite-vss extension (native vector operations)
- Fallback: SQLite FTS5 + Python cosine similarity

Features:
- Import embeddings from WU08 output (.claude/embeddings/*.json)
- Similarity search using cosine distance
- Automatic fallback to FTS5 if sqlite-vss unavailable
- Efficient binary storage (BLOB) for embeddings

Usage:
    # Initialize and import embeddings
    python3 vector_db.py --import .claude/embeddings

    # Search for similar documents
    python3 vector_db.py --search "background test execution" --limit 5

    # Check mode (vss or FTS5)
    python3 vector_db.py --check-mode

Author: WU09 - Vector Database Setup
"""

import argparse
import json
import logging
import sqlite3
import struct
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Import error handler for retry logic on connection errors
try:
    from error_handler import retry_on_transient_error
except ImportError:
    # Fallback if error_handler not available
    def retry_on_transient_error(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

# ============================================================================
# Logging Configuration
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('VectorDB')


# ============================================================================
# Vector Database Class
# ============================================================================

class VectorDB:
    """Vector database for semantic search over documents"""

    def __init__(self, db_path: str = ".claude/vector_db.sqlite"):
        """
        Initialize vector database

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path).resolve()
        self.conn = None
        self.use_vss = False
        self.schema_path = Path(__file__).parent.parent / "schemas" / "vector-db.sql"

        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Connect and initialize
        self.connect()
        self.initialize_schema()

    def connect(self):
        """Establish database connection"""
        try:
            self.conn = sqlite3.connect(str(self.db_path))
            self.conn.row_factory = sqlite3.Row
            logger.info(f"Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def _detect_sqlite_vss(self) -> bool:
        """
        Detect if sqlite-vss extension is available

        Returns:
            True if sqlite-vss is loadable and functional
        """
        try:
            # Try to enable extension loading
            self.conn.enable_load_extension(True)

            # Try to load vss0 extension
            try:
                self.conn.load_extension("vss0")
            except sqlite3.OperationalError:
                # Try alternative extension name
                self.conn.load_extension("vector0")

            # Verify extension works
            cursor = self.conn.execute("SELECT vss_version()")
            version = cursor.fetchone()[0]
            logger.info(f"sqlite-vss extension loaded successfully (version: {version})")
            return True

        except (sqlite3.OperationalError, AttributeError) as e:
            logger.warning(f"sqlite-vss not available: {e}")
            logger.warning("Falling back to FTS5 + Python cosine similarity")
            return False

    def initialize_schema(self):
        """
        Create database schema

        - Always creates base tables and FTS5 index
        - Optionally creates vss_embeddings if sqlite-vss available
        """
        try:
            # Detect sqlite-vss availability
            self.use_vss = self._detect_sqlite_vss()

            # Load and execute base schema
            if self.schema_path.exists():
                schema_sql = self.schema_path.read_text()
                self.conn.executescript(schema_sql)
                logger.info("Base schema created successfully")
            else:
                logger.warning(f"Schema file not found: {self.schema_path}")
                self._create_minimal_schema()

            # Create vss_embeddings table if extension available
            if self.use_vss:
                try:
                    self.conn.execute("""
                        CREATE VIRTUAL TABLE IF NOT EXISTS vss_embeddings USING vss0(
                            embedding(1536)
                        )
                    """)
                    self.conn.commit()
                    logger.info("sqlite-vss virtual table created")
                except sqlite3.Error as e:
                    logger.warning(f"Failed to create vss table: {e}")
                    self.use_vss = False

            self.conn.commit()
            mode = "sqlite-vss" if self.use_vss else "FTS5 fallback"
            logger.info(f"Schema initialized in {mode} mode")

        except sqlite3.Error as e:
            logger.error(f"Schema initialization failed: {e}")
            raise

    def _create_minimal_schema(self):
        """Create minimal schema if schema file not found"""
        logger.info("Creating minimal schema from embedded SQL")

        schema = """
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            path TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS embeddings (
            document_id TEXT PRIMARY KEY,
            embedding BLOB NOT NULL,
            model TEXT NOT NULL,
            provider TEXT NOT NULL,
            dimensions INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(type);
        CREATE INDEX IF NOT EXISTS idx_documents_created ON documents(created_at);
        """

        self.conn.executescript(schema)

    def import_embeddings(self, embeddings_dir: Path) -> Tuple[int, int]:
        """
        Import embeddings from WU08 output directory

        Args:
            embeddings_dir: Path to directory containing *.json embedding files

        Returns:
            Tuple of (successful_count, failed_count)
        """
        embeddings_dir = Path(embeddings_dir).resolve()

        if not embeddings_dir.exists():
            logger.error(f"Embeddings directory not found: {embeddings_dir}")
            return 0, 0

        # Find all JSON files
        embedding_files = list(embeddings_dir.glob("*.json"))
        if not embedding_files:
            logger.warning(f"No embedding files found in {embeddings_dir}")
            return 0, 0

        logger.info(f"Found {len(embedding_files)} embedding files to import")

        successful = 0
        failed = 0

        for embedding_file in embedding_files:
            try:
                # Load embedding JSON
                with open(embedding_file, 'r') as f:
                    data = json.load(f)

                # Extract fields
                document_id = data['document_id']
                document_type = data['document_type']
                document_path = data['document_path']
                embedding = data['embedding']
                model = data['model']
                provider = data['provider']
                dimensions = data['dimensions']
                created_at = data['timestamp']

                # Load document content (strip YAML frontmatter if present)
                content = self._load_document_content(Path(document_path))

                # Insert document
                self.conn.execute("""
                    INSERT OR REPLACE INTO documents (id, type, path, content, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (document_id, document_type, str(document_path), content, created_at, created_at))

                # Convert embedding to binary BLOB
                embedding_blob = self._embedding_to_blob(embedding)

                # Insert embedding
                self.conn.execute("""
                    INSERT OR REPLACE INTO embeddings (document_id, embedding, model, provider, dimensions, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (document_id, embedding_blob, model, provider, dimensions, created_at))

                # Insert into vss_embeddings if available
                if self.use_vss:
                    try:
                        # Get rowid for the document
                        cursor = self.conn.execute("SELECT rowid FROM documents WHERE id = ?", (document_id,))
                        rowid = cursor.fetchone()[0]

                        # Insert into vss table (rowid must match documents table)
                        self.conn.execute("""
                            INSERT OR REPLACE INTO vss_embeddings (rowid, embedding)
                            VALUES (?, ?)
                        """, (rowid, embedding_blob))

                    except sqlite3.Error as e:
                        logger.warning(f"Failed to insert into vss_embeddings for {document_id}: {e}")

                successful += 1
                logger.debug(f"Imported {document_id}")

            except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
                logger.error(f"Failed to import {embedding_file.name}: {e}")
                failed += 1
                continue

        self.conn.commit()
        logger.info(f"Import complete: {successful} successful, {failed} failed")
        return successful, failed

    def _load_document_content(self, document_path: Path) -> str:
        """
        Load document content, stripping YAML frontmatter

        Args:
            document_path: Path to document file

        Returns:
            Document content without frontmatter
        """
        try:
            content = document_path.read_text()

            # Strip YAML frontmatter if present
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    content = parts[2].strip()

            return content

        except Exception as e:
            logger.warning(f"Failed to load content from {document_path}: {e}")
            return ""

    def _embedding_to_blob(self, embedding: List[float]) -> bytes:
        """
        Convert embedding list to binary BLOB

        Args:
            embedding: List of 1536 floats

        Returns:
            Binary representation (1536 * 4 = 6144 bytes)
        """
        # Pack as 1536 floats (4 bytes each)
        return struct.pack(f'{len(embedding)}f', *embedding)

    def _blob_to_embedding(self, blob: bytes) -> List[float]:
        """
        Convert binary BLOB to embedding list

        Args:
            blob: Binary representation from database

        Returns:
            List of floats
        """
        count = len(blob) // 4  # 4 bytes per float
        return list(struct.unpack(f'{count}f', blob))

    @retry_on_transient_error(max_attempts=3, base_delay=1.0)
    def search_similar(self, query_embedding: List[float], limit: int = 10,
                      document_type: Optional[str] = None) -> List[Dict]:
        """
        Search for similar documents using cosine similarity.
        Automatically retries on transient database connection errors.

        Args:
            query_embedding: Query vector (1536 floats)
            limit: Maximum number of results to return
            document_type: Optional filter ('work_unit' or 'agent_review')

        Returns:
            List of dicts with 'id', 'type', 'path', 'similarity', 'content'
        """
        if self.use_vss:
            return self._search_vss(query_embedding, limit, document_type)
        else:
            return self._search_fallback(query_embedding, limit, document_type)

    def _search_vss(self, query_embedding: List[float], limit: int,
                   document_type: Optional[str]) -> List[Dict]:
        """
        Search using sqlite-vss extension

        Args:
            query_embedding: Query vector
            limit: Result limit
            document_type: Optional type filter

        Returns:
            Ranked results with similarity scores
        """
        try:
            # Convert query to blob
            query_blob = self._embedding_to_blob(query_embedding)

            # Build query with optional type filter
            type_filter = ""
            params = [query_blob, limit]

            if document_type:
                type_filter = "AND d.type = ?"
                params.append(document_type)

            # Execute vss search
            query_sql = f"""
                SELECT
                    d.id,
                    d.type,
                    d.path,
                    d.content,
                    vss.distance
                FROM vss_embeddings vss
                JOIN documents d ON d.rowid = vss.rowid
                WHERE vss_search(vss.embedding, ?)
                {type_filter}
                LIMIT ?
            """

            cursor = self.conn.execute(query_sql, params)
            rows = cursor.fetchall()

            # Convert to result dicts (lower distance = higher similarity)
            results = []
            for row in rows:
                results.append({
                    'id': row['id'],
                    'type': row['type'],
                    'path': row['path'],
                    'content': row['content'][:500],  # Truncate for display
                    'similarity': 1.0 - row['distance'],  # Convert distance to similarity
                    'distance': row['distance']
                })

            return results

        except sqlite3.Error as e:
            logger.error(f"VSS search failed: {e}")
            return []

    def _search_fallback(self, query_embedding: List[float], limit: int,
                        document_type: Optional[str]) -> List[Dict]:
        """
        Fallback search using FTS5 + Python cosine similarity

        Args:
            query_embedding: Query vector
            limit: Result limit
            document_type: Optional type filter

        Returns:
            Ranked results with similarity scores
        """
        try:
            # Get all embeddings (or filter by type)
            type_filter = ""
            params = []

            if document_type:
                type_filter = "WHERE d.type = ?"
                params.append(document_type)

            query_sql = f"""
                SELECT d.id, d.type, d.path, d.content, e.embedding
                FROM documents d
                JOIN embeddings e ON e.document_id = d.id
                {type_filter}
            """

            cursor = self.conn.execute(query_sql, params)
            rows = cursor.fetchall()

            # Compute cosine similarity for each
            results = []
            for row in rows:
                doc_embedding = self._blob_to_embedding(row['embedding'])
                similarity = self._cosine_similarity(query_embedding, doc_embedding)

                results.append({
                    'id': row['id'],
                    'type': row['type'],
                    'path': row['path'],
                    'content': row['content'][:500],  # Truncate for display
                    'similarity': similarity
                })

            # Sort by similarity (descending) and limit
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:limit]

        except sqlite3.Error as e:
            logger.error(f"Fallback search failed: {e}")
            return []

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Similarity score between -1 and 1 (1 = identical)
        """
        if len(vec1) != len(vec2):
            raise ValueError(f"Vector dimension mismatch: {len(vec1)} != {len(vec2)}")

        # Dot product
        dot_product = sum(a * b for a, b in zip(vec1, vec2))

        # Magnitudes
        mag1 = sum(a * a for a in vec1) ** 0.5
        mag2 = sum(b * b for b in vec2) ** 0.5

        # Avoid division by zero
        if mag1 == 0 or mag2 == 0:
            return 0.0

        return dot_product / (mag1 * mag2)

    def get_document(self, document_id: str) -> Optional[Dict]:
        """
        Retrieve document by ID

        Args:
            document_id: Document identifier

        Returns:
            Dict with document data, or None if not found
        """
        try:
            cursor = self.conn.execute("""
                SELECT d.id, d.type, d.path, d.content, d.created_at,
                       e.model, e.provider, e.dimensions
                FROM documents d
                JOIN embeddings e ON e.document_id = d.id
                WHERE d.id = ?
            """, (document_id,))

            row = cursor.fetchone()
            if row:
                return {
                    'id': row['id'],
                    'type': row['type'],
                    'path': row['path'],
                    'content': row['content'],
                    'created_at': row['created_at'],
                    'model': row['model'],
                    'provider': row['provider'],
                    'dimensions': row['dimensions']
                }
            return None

        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve document {document_id}: {e}")
            return None

    def get_stats(self) -> Dict:
        """
        Get database statistics

        Returns:
            Dict with counts and mode information
        """
        try:
            # Document counts
            cursor = self.conn.execute("SELECT COUNT(*) FROM documents")
            doc_count = cursor.fetchone()[0]

            cursor = self.conn.execute("SELECT COUNT(*) FROM embeddings")
            emb_count = cursor.fetchone()[0]

            # Type breakdown
            cursor = self.conn.execute("""
                SELECT type, COUNT(*) as count
                FROM documents
                GROUP BY type
            """)
            type_counts = {row['type']: row['count'] for row in cursor.fetchall()}

            # Database size
            db_size_mb = self.db_path.stat().st_size / (1024 * 1024)

            return {
                'mode': 'sqlite-vss' if self.use_vss else 'FTS5 fallback',
                'documents': doc_count,
                'embeddings': emb_count,
                'type_breakdown': type_counts,
                'database_size_mb': round(db_size_mb, 2)
            }

        except (sqlite3.Error, OSError) as e:
            logger.error(f"Failed to get stats: {e}")
            return {}

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """Command-line interface"""
    parser = argparse.ArgumentParser(
        description='Vector Database for Semantic Search (WU09)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Import embeddings from WU08
  %(prog)s --import .claude/embeddings

  # Search for similar documents
  %(prog)s --search "background test execution" --limit 5

  # Get database statistics
  %(prog)s --stats

  # Check mode (vss or FTS5)
  %(prog)s --check-mode
        """
    )

    parser.add_argument('--db', default='.claude/vector_db.sqlite',
                       help='Path to SQLite database (default: .claude/vector_db.sqlite)')
    parser.add_argument('--import', dest='import_dir', metavar='DIR',
                       help='Import embeddings from directory')
    parser.add_argument('--search', metavar='QUERY',
                       help='Search query (requires --embedding or uses dummy)')
    parser.add_argument('--embedding', metavar='FILE',
                       help='Path to JSON file with query embedding')
    parser.add_argument('--limit', type=int, default=10,
                       help='Maximum number of search results (default: 10)')
    parser.add_argument('--type', choices=['work_unit', 'agent_review'],
                       help='Filter results by document type')
    parser.add_argument('--stats', action='store_true',
                       help='Show database statistics')
    parser.add_argument('--check-mode', action='store_true',
                       help='Check which mode is active (vss or FTS5)')
    parser.add_argument('--get', metavar='DOC_ID',
                       help='Retrieve document by ID')

    args = parser.parse_args()

    # Initialize database
    db = VectorDB(db_path=args.db)

    try:
        # Import embeddings
        if args.import_dir:
            successful, failed = db.import_embeddings(Path(args.import_dir))
            print(f"Import complete: {successful} successful, {failed} failed")
            return 0

        # Show statistics
        if args.stats:
            stats = db.get_stats()
            print("Database Statistics:")
            print(f"  Mode: {stats['mode']}")
            print(f"  Documents: {stats['documents']}")
            print(f"  Embeddings: {stats['embeddings']}")
            print(f"  Type breakdown: {stats['type_breakdown']}")
            print(f"  Database size: {stats['database_size_mb']} MB")
            return 0

        # Check mode
        if args.check_mode:
            mode = "sqlite-vss" if db.use_vss else "FTS5 fallback"
            print(f"Mode: {mode}")
            return 0

        # Get document
        if args.get:
            doc = db.get_document(args.get)
            if doc:
                print(f"Document: {doc['id']}")
                print(f"  Type: {doc['type']}")
                print(f"  Path: {doc['path']}")
                print(f"  Model: {doc['model']}")
                print(f"  Provider: {doc['provider']}")
                print(f"  Content preview: {doc['content'][:200]}...")
            else:
                print(f"Document not found: {args.get}")
            return 0

        # Search (requires embedding or uses dummy for testing)
        if args.search:
            if args.embedding:
                # Load query embedding from file
                with open(args.embedding, 'r') as f:
                    data = json.load(f)
                    query_embedding = data['embedding']
            else:
                # Use dummy embedding (all zeros) for testing
                print("WARNING: Using dummy embedding (all zeros) - results may not be meaningful")
                query_embedding = [0.0] * 1536

            results = db.search_similar(query_embedding, limit=args.limit, document_type=args.type)

            print(f"Search results for: {args.search}")
            print(f"Found {len(results)} results\n")

            for i, result in enumerate(results, 1):
                print(f"{i}. {result['id']} (similarity: {result['similarity']:.3f})")
                print(f"   Type: {result['type']}")
                print(f"   Path: {result['path']}")
                print(f"   Content: {result['content'][:150]}...")
                print()

            return 0

        # No action specified
        parser.print_help()
        return 1

    finally:
        db.close()


if __name__ == '__main__':
    sys.exit(main())
