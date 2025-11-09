#!/usr/bin/env python3
"""
Memory Query Interface (WU10)

Natural language query interface for semantic search over work units and
agent reviews. Provides interactive CLI with configurable similarity thresholds
and result ranking.

Features:
- Natural language queries using LM Studio embeddings
- Similarity-based ranking of results
- Configurable threshold filtering
- Document type filtering (work_unit, agent_review)
- Interactive mode for continuous querying
- Result export functionality

Usage:
    # Basic query
    python3 query_memory.py --query "background test execution"

    # With threshold and type filter
    python3 query_memory.py --query "P0 issues" --threshold 0.8 --type agent_review

    # Interactive mode
    python3 query_memory.py --interactive

Author: WU10 - Memory Query Interface
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from fallback_embedding_client import FallbackEmbeddingClient
from vector_db import VectorDB

# ============================================================================
# Logging Configuration
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('MemoryQuery')


# ============================================================================
# Query Interface Class
# ============================================================================

class MemoryQueryInterface:
    """Interactive query interface for semantic search"""

    def __init__(
        self,
        db_path: str = ".claude/vector_db.sqlite",
        threshold: float = 0.7,
        context_length: int = 300
    ):
        """
        Initialize query interface

        Args:
            db_path: Path to vector database
            threshold: Minimum similarity threshold (0.0-1.0)
            context_length: Length of context snippets in characters
        """
        self.threshold = threshold
        self.context_length = context_length

        # Initialize vector database
        logger.info(f"Connecting to vector database: {db_path}")
        self.db = VectorDB(db_path=db_path)

        # Initialize fallback embedding client (WU11: graceful degradation)
        logger.info("Initializing fallback embedding client")
        self.client = FallbackEmbeddingClient(db_path=db_path)

        # Check database has documents
        stats = self.db.get_stats()
        if stats.get('documents', 0) == 0:
            logger.warning("Vector database is empty. Run 'python3 vector_db.py --import .claude/embeddings' first")

        # Store last results for interactive mode
        self.last_results = []

    def generate_query_embedding(self, query: str) -> tuple:
        """
        Generate embedding for query text with fallback support

        Args:
            query: Natural language query

        Returns:
            Tuple of (embedding_vector, provider_used)
            Returns (None, 'keyword') if all embedding providers fail
        """
        try:
            logger.debug(f"Generating embedding for query: {query[:50]}...")
            embedding, provider = self.client.generate_embedding(query)
            return embedding, provider
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            return None, 'failed'

    def search(
        self,
        query: str,
        limit: int = 10,
        document_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Search for documents matching query with fallback support (WU11)

        Args:
            query: Natural language query
            limit: Maximum number of results
            document_type: Optional type filter ('work_unit' or 'agent_review')

        Returns:
            List of result dicts with similarity scores
        """
        # Generate query embedding with fallback
        query_embedding, provider = self.generate_query_embedding(query)

        # Tier 3 fallback: Use keyword search if no embedding available
        if query_embedding is None and provider == 'keyword':
            logger.info("Using keyword search (Tier 3 fallback)")
            results = self.client.keyword_search(
                query=query,
                limit=limit,
                document_type=document_type
            )

            # Apply threshold filtering to keyword results
            filtered_results = [
                result for result in results
                if result.get('similarity', 0.0) >= self.threshold
            ]

            logger.info(f"Found {len(filtered_results)} results above threshold {self.threshold}")
            return filtered_results[:limit]

        # Tier 1 or 2: Use embedding-based search
        if query_embedding is None:
            logger.error("Cannot perform search without query embedding")
            return []

        # Perform similarity search
        logger.debug(f"Searching for similar documents (limit={limit}, type={document_type}, provider={provider})")
        try:
            results = self.db.search_similar(
                query_embedding=query_embedding,
                limit=limit * 2,  # Get more results for filtering
                document_type=document_type
            )
        except ValueError as e:
            if "Vector dimension mismatch" in str(e):
                logger.error(
                    "Embedding dimension mismatch detected. "
                    "Database embeddings have different dimensions than query embedding. "
                    "This usually means embeddings were generated with a different model. "
                    "Regenerate embeddings with: python3 .claude/scripts/generate_embeddings.py"
                )
            else:
                logger.error(f"Search failed: {e}")
            return []

        # Apply threshold filtering
        filtered_results = [
            result for result in results
            if result.get('similarity', 0.0) >= self.threshold
        ]

        # Limit to requested count
        filtered_results = filtered_results[:limit]

        logger.info(f"Found {len(filtered_results)} results above threshold {self.threshold}")
        return filtered_results

    def format_result(self, index: int, result: Dict) -> str:
        """
        Format a single search result for display

        Args:
            index: Result number (1-indexed)
            result: Result dict from search

        Returns:
            Formatted string for terminal output
        """
        # Extract fields
        doc_id = result.get('id', 'unknown')
        doc_type = result.get('type', 'unknown')
        doc_path = result.get('path', 'unknown')
        similarity = result.get('similarity', 0.0)
        content = result.get('content', '')

        # Create context snippet
        snippet = self._create_snippet(content, self.context_length)

        # Type badge
        type_badge = {
            'work_unit': 'work_unit',
            'agent_review': 'agent_review'
        }.get(doc_type, doc_type)

        # Format output
        separator = "━" * 60
        output = f"\n{separator}\n"
        output += f"[{index}] {doc_id} (similarity: {similarity:.3f})\n"
        output += f"    Type: {type_badge} | Path: {doc_path}\n\n"
        output += f"    {snippet}\n"

        return output

    def _create_snippet(self, content: str, max_length: int) -> str:
        """
        Create a context snippet from document content

        Args:
            content: Full document content
            max_length: Maximum snippet length

        Returns:
            Formatted snippet with ellipsis if truncated
        """
        if not content:
            return "[No content available]"

        # Remove extra whitespace
        content = ' '.join(content.split())

        # Truncate if necessary
        if len(content) > max_length:
            # Try to break at word boundary
            truncated = content[:max_length]
            last_space = truncated.rfind(' ')
            if last_space > max_length * 0.8:  # At least 80% of desired length
                truncated = truncated[:last_space]
            return f"...{truncated}..."
        else:
            return content

    def display_results(self, query: str, results: List[Dict]):
        """
        Display search results to terminal

        Args:
            query: Original query string
            results: List of result dicts
        """
        print(f"\nQuery: \"{query}\"")
        print(f"Found {len(results)} results (threshold: {self.threshold:.2f})\n")

        if not results:
            print("No results found above threshold.")
            print("Try lowering the threshold with --threshold or use a different query.")
            return

        for i, result in enumerate(results, 1):
            print(self.format_result(i, result))

        print("━" * 60)

    def get_full_document(self, result_index: int) -> Optional[str]:
        """
        Retrieve full document content by result index

        Args:
            result_index: 1-indexed result number from last search

        Returns:
            Full document content, or None if not found
        """
        if not self.last_results:
            logger.error("No results available")
            return None

        if result_index < 1 or result_index > len(self.last_results):
            logger.error(f"Invalid result index: {result_index}")
            return None

        result = self.last_results[result_index - 1]
        doc_id = result.get('id')

        # Get full document from database
        doc = self.db.get_document(doc_id)
        if doc:
            return doc.get('content', '')
        else:
            logger.error(f"Document not found: {doc_id}")
            return None

    def export_results(self, results: List[Dict], output_file: Path) -> bool:
        """
        Export search results to JSON file

        Args:
            results: List of result dicts
            output_file: Output file path

        Returns:
            True if export successful
        """
        try:
            data = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'threshold': self.threshold,
                'result_count': len(results),
                'results': results
            }

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Exported {len(results)} results to {output_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to export results: {e}")
            return False

    def interactive_mode(self):
        """
        Run interactive query session

        Commands:
            q <query>      - Search with new query
            t <threshold>  - Adjust similarity threshold
            v <number>     - View full document
            e <file>       - Export results to file
            h              - Show help
            quit           - Exit
        """
        print("\n" + "=" * 60)
        print("Memory Query Interface - Interactive Mode")
        print("=" * 60)
        print("\nCommands:")
        print("  q <query>      - Search with new query")
        print("  t <threshold>  - Adjust similarity threshold (0.0-1.0)")
        print("  v <number>     - View full document by result number")
        print("  e <file>       - Export results to JSON file")
        print("  h              - Show this help")
        print("  quit           - Exit interactive mode")
        print("\n" + "=" * 60 + "\n")

        current_query = None

        while True:
            try:
                # Prompt
                user_input = input("query> ").strip()

                if not user_input:
                    continue

                # Parse command
                parts = user_input.split(maxsplit=1)
                command = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""

                # Handle commands
                if command == 'quit' or command == 'q' and not args:
                    print("Exiting interactive mode.")
                    break

                elif command == 'q':
                    # New query
                    if not args:
                        print("Usage: q <query>")
                        continue

                    current_query = args
                    results = self.search(current_query)
                    self.last_results = results
                    self.display_results(current_query, results)

                elif command == 't':
                    # Adjust threshold
                    if not args:
                        print(f"Current threshold: {self.threshold:.2f}")
                        print("Usage: t <threshold> (0.0-1.0)")
                        continue

                    try:
                        new_threshold = float(args)
                        if new_threshold < 0.0 or new_threshold > 1.0:
                            print("Threshold must be between 0.0 and 1.0")
                            continue

                        self.threshold = new_threshold
                        print(f"Threshold updated to {self.threshold:.2f}")

                        # Re-search if we have a query
                        if current_query:
                            print(f"Re-searching with new threshold...")
                            results = self.search(current_query)
                            self.last_results = results
                            self.display_results(current_query, results)

                    except ValueError:
                        print("Invalid threshold value. Must be a number between 0.0 and 1.0")

                elif command == 'v':
                    # View full document
                    if not args:
                        print("Usage: v <number>")
                        continue

                    try:
                        result_num = int(args)
                        content = self.get_full_document(result_num)

                        if content:
                            print("\n" + "=" * 60)
                            print(f"Document #{result_num} - Full Content")
                            print("=" * 60)
                            print(content)
                            print("=" * 60 + "\n")
                        else:
                            print(f"Could not retrieve document #{result_num}")

                    except ValueError:
                        print("Invalid result number. Must be an integer.")

                elif command == 'e':
                    # Export results
                    if not args:
                        print("Usage: e <file>")
                        continue

                    if not self.last_results:
                        print("No results to export. Run a query first.")
                        continue

                    output_path = Path(args).resolve()
                    if self.export_results(self.last_results, output_path):
                        print(f"Results exported to {output_path}")
                    else:
                        print("Export failed. Check logs for details.")

                elif command == 'h':
                    # Show help
                    print("\nCommands:")
                    print("  q <query>      - Search with new query")
                    print("  t <threshold>  - Adjust similarity threshold (0.0-1.0)")
                    print("  v <number>     - View full document by result number")
                    print("  e <file>       - Export results to JSON file")
                    print("  h              - Show this help")
                    print("  quit           - Exit interactive mode\n")

                else:
                    print(f"Unknown command: {command}")
                    print("Type 'h' for help or 'quit' to exit")

            except KeyboardInterrupt:
                print("\n\nExiting interactive mode.")
                break
            except EOFError:
                print("\n\nExiting interactive mode.")
                break
            except Exception as e:
                logger.error(f"Error in interactive mode: {e}")
                print(f"Error: {e}")

    def close(self):
        """Clean up resources"""
        if self.db:
            self.db.close()


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """Command-line interface"""
    parser = argparse.ArgumentParser(
        description='Memory Query Interface for Semantic Search (WU10)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic query
  %(prog)s --query "background test execution"

  # With threshold and limit
  %(prog)s --query "P0 issues" --threshold 0.8 --limit 5

  # Filter by document type
  %(prog)s --query "implementation" --type work_unit

  # Interactive mode
  %(prog)s --interactive

  # Custom database location
  %(prog)s --db /path/to/vector_db.sqlite --query "testing"
        """
    )

    parser.add_argument('--db', default='.claude/vector_db.sqlite',
                       help='Path to vector database (default: .claude/vector_db.sqlite)')
    parser.add_argument('--query', metavar='TEXT',
                       help='Natural language query')
    parser.add_argument('--threshold', type=float, default=0.7,
                       help='Minimum similarity threshold 0.0-1.0 (default: 0.7)')
    parser.add_argument('--limit', type=int, default=10,
                       help='Maximum number of results (default: 10)')
    parser.add_argument('--type', choices=['work_unit', 'agent_review'],
                       help='Filter by document type')
    parser.add_argument('--context-length', type=int, default=300,
                       help='Length of context snippets (default: 300)')
    parser.add_argument('--interactive', action='store_true',
                       help='Launch interactive query session')
    parser.add_argument('--export', metavar='FILE',
                       help='Export results to JSON file')

    args = parser.parse_args()

    # Validate threshold
    if not 0.0 <= args.threshold <= 1.0:
        parser.error("Threshold must be between 0.0 and 1.0")

    # Initialize interface
    try:
        interface = MemoryQueryInterface(
            db_path=args.db,
            threshold=args.threshold,
            context_length=args.context_length
        )
    except Exception as e:
        logger.error(f"Failed to initialize query interface: {e}")
        return 1

    try:
        # Interactive mode
        if args.interactive:
            interface.interactive_mode()
            return 0

        # Single query mode
        if args.query:
            results = interface.search(
                query=args.query,
                limit=args.limit,
                document_type=args.type
            )

            interface.display_results(args.query, results)

            # Export if requested
            if args.export:
                export_path = Path(args.export).resolve()
                if interface.export_results(results, export_path):
                    print(f"\nResults exported to {export_path}")
                else:
                    print("\nExport failed. Check logs for details.")
                    return 1

            return 0

        # No action specified
        parser.print_help()
        return 1

    finally:
        interface.close()


if __name__ == '__main__':
    sys.exit(main())
