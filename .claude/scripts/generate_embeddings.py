#!/usr/bin/env python3
"""
Embedding Generation Script

Batch processes work units and agent reviews to generate embeddings
using LM Studio (primary) with OpenAI fallback.
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

try:
    from tqdm import tqdm
except ImportError:
    print("ERROR: tqdm library not installed. Run: pip install tqdm")
    sys.exit(1)

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from lm_studio_client import LMStudioClient


class EmbeddingGenerator:
    """Batch embedding generation for work units and agent reviews"""

    def __init__(
        self,
        provider: str = 'lm_studio',
        batch_size: int = 10,
        output_dir: Optional[Path] = None,
        log_dir: Optional[Path] = None,
        dry_run: bool = False
    ):
        """
        Initialize embedding generator

        Args:
            provider: 'lm_studio' or 'openai'
            batch_size: Number of documents per batch
            output_dir: Directory for embedding output
            log_dir: Directory for logs
            dry_run: If True, don't actually generate embeddings
        """
        self.provider = provider
        self.batch_size = batch_size
        self.dry_run = dry_run

        # Set up directories
        project_root = Path(__file__).parent.parent.parent
        self.output_dir = output_dir or project_root / '.claude' / 'embeddings'
        self.log_dir = log_dir or project_root / '.claude' / 'logs'

        # Create directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Set up logging
        self._setup_logging()

        # Initialize client
        if not dry_run:
            self.client = LMStudioClient()
            if provider == 'openai':
                # Force OpenAI fallback
                self.client.use_fallback = True
                if not self.client.openai_api_key:
                    raise ValueError("OPENAI_API_KEY not set for OpenAI provider")
            else:
                # Verify LM Studio is available
                if not self.client.check_health():
                    self.logger.warning("LM Studio not available - will use OpenAI fallback if configured")
        else:
            self.client = None

        # Statistics
        self.stats = {
            'total_documents': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }

    def _setup_logging(self):
        """Configure logging"""
        log_file = self.log_dir / 'embedding_generation.log'

        self.logger = logging.getLogger('EmbeddingGenerator')
        self.logger.setLevel(logging.INFO)

        # File handler
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)

        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        self.logger.addHandler(fh)
        self.logger.addHandler(ch)

    def discover_documents(self) -> List[Dict]:
        """
        Discover all work units and agent reviews

        Returns:
            List of document metadata dicts
        """
        documents = []
        project_root = Path(__file__).parent.parent.parent

        # Discover work units
        work_units_dir = project_root / '.claude' / 'work-units'
        if work_units_dir.exists():
            for wu_file in work_units_dir.glob('*.md'):
                documents.append({
                    'id': wu_file.stem,
                    'type': 'work_unit',
                    'path': wu_file,
                    'content': None  # Loaded on demand
                })

        # Discover agent reviews
        reviews_dir = project_root / '.claude' / 'agent-reviews'
        if reviews_dir.exists():
            for review_file in reviews_dir.glob('*.md'):
                documents.append({
                    'id': review_file.stem,
                    'type': 'agent_review',
                    'path': review_file,
                    'content': None
                })

        self.logger.info(f"Discovered {len(documents)} documents "
                        f"({sum(1 for d in documents if d['type'] == 'work_unit')} work units, "
                        f"{sum(1 for d in documents if d['type'] == 'agent_review')} reviews)")

        return documents

    def load_document_content(self, document: Dict) -> str:
        """
        Load document content from file

        Args:
            document: Document metadata dict

        Returns:
            Document text content
        """
        try:
            with open(document['path'], 'r', encoding='utf-8') as f:
                content = f.read()

            # Strip YAML frontmatter if present
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    content = parts[2].strip()

            return content

        except Exception as e:
            self.logger.error(f"Failed to load {document['path']}: {e}")
            return ""

    def generate_embedding_for_document(self, document: Dict) -> Optional[List[float]]:
        """
        Generate embedding for a single document

        Args:
            document: Document metadata dict

        Returns:
            Embedding vector, or None if failed
        """
        if self.dry_run:
            # Return fake embedding for dry run
            return [0.0] * 1536

        # Load content if not already loaded
        if document['content'] is None:
            document['content'] = self.load_document_content(document)

        if not document['content']:
            self.logger.warning(f"Empty content for {document['id']}")
            return None

        # Generate embedding
        try:
            embedding = self.client.generate_embedding(document['content'])
            return embedding
        except Exception as e:
            self.logger.error(f"Failed to generate embedding for {document['id']}: {e}")
            return None

    def save_embedding(
        self,
        document: Dict,
        embedding: List[float],
        model_name: str
    ) -> bool:
        """
        Save embedding to disk

        Args:
            document: Document metadata dict
            embedding: Embedding vector
            model_name: Model used to generate embedding

        Returns:
            True if saved successfully
        """
        output_file = self.output_dir / f"{document['id']}.json"

        try:
            # Determine provider
            if self.dry_run:
                provider = 'dry-run'
            elif self.client.use_fallback:
                provider = 'openai'
            else:
                provider = 'lm_studio'

            data = {
                'document_id': document['id'],
                'document_type': document['type'],
                'document_path': str(document['path']),
                'embedding': embedding,
                'model': model_name,
                'provider': provider,
                'dimensions': len(embedding),
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            return True

        except Exception as e:
            self.logger.error(f"Failed to save embedding for {document['id']}: {e}")
            return False

    def process_batch(self, documents: List[Dict]) -> Tuple[int, int]:
        """
        Process a batch of documents

        Args:
            documents: List of document metadata dicts

        Returns:
            Tuple of (successful_count, failed_count)
        """
        successful = 0
        failed = 0

        for document in tqdm(documents, desc="Processing batch", leave=False):
            # Check if embedding already exists
            output_file = self.output_dir / f"{document['id']}.json"
            if output_file.exists():
                self.logger.debug(f"Skipping {document['id']} - already exists")
                self.stats['skipped'] += 1
                continue

            # Generate embedding
            embedding = self.generate_embedding_for_document(document)

            if embedding is None:
                self.logger.warning(f"Failed to generate embedding for {document['id']}")
                failed += 1
                self.stats['failed'] += 1
                self.stats['errors'].append({
                    'document_id': document['id'],
                    'error': 'Failed to generate embedding'
                })
                continue

            # Save embedding
            model_name = self.client.model_name if not self.dry_run else 'dry-run'
            if self.save_embedding(document, embedding, model_name):
                successful += 1
                self.stats['successful'] += 1
            else:
                failed += 1
                self.stats['failed'] += 1
                self.stats['errors'].append({
                    'document_id': document['id'],
                    'error': 'Failed to save embedding'
                })

        return successful, failed

    def generate_all(self, skip_existing: bool = True) -> Dict:
        """
        Generate embeddings for all documents

        Args:
            skip_existing: If True, skip documents with existing embeddings

        Returns:
            Statistics dict
        """
        # Discover documents
        documents = self.discover_documents()
        self.stats['total_documents'] = len(documents)

        if not documents:
            self.logger.warning("No documents found to process")
            return self.stats

        # Filter existing if requested
        if skip_existing:
            documents = [
                doc for doc in documents
                if not (self.output_dir / f"{doc['id']}.json").exists()
            ]
            self.logger.info(f"Processing {len(documents)} new documents "
                           f"(skipping {self.stats['total_documents'] - len(documents)} existing)")

        if not documents:
            self.logger.info("All documents already have embeddings")
            self.stats['skipped'] = self.stats['total_documents']
            return self.stats

        # Process in batches
        total_batches = (len(documents) + self.batch_size - 1) // self.batch_size
        self.logger.info(f"Processing {len(documents)} documents in {total_batches} batches")

        for i in range(0, len(documents), self.batch_size):
            batch = documents[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1

            self.logger.info(f"Processing batch {batch_num}/{total_batches} "
                           f"({len(batch)} documents)")

            successful, failed = self.process_batch(batch)

            self.logger.info(f"Batch {batch_num} complete: "
                           f"{successful} successful, {failed} failed")

        # Log final statistics
        self.logger.info(f"Embedding generation complete:")
        self.logger.info(f"  Total documents: {self.stats['total_documents']}")
        self.logger.info(f"  Successful: {self.stats['successful']}")
        self.logger.info(f"  Failed: {self.stats['failed']}")
        self.logger.info(f"  Skipped: {self.stats['skipped']}")

        if self.stats['errors']:
            self.logger.warning(f"  Errors: {len(self.stats['errors'])}")
            for error in self.stats['errors'][:5]:  # Show first 5
                self.logger.warning(f"    - {error['document_id']}: {error['error']}")

        return self.stats


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Generate embeddings for work units and agent reviews'
    )

    parser.add_argument(
        '--provider',
        choices=['lm_studio', 'openai'],
        default='lm_studio',
        help='Embedding provider (default: lm_studio)'
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=10,
        help='Number of documents per batch (default: 10)'
    )

    parser.add_argument(
        '--output-dir',
        type=Path,
        help='Output directory for embeddings (default: .claude/embeddings)'
    )

    parser.add_argument(
        '--log-dir',
        type=Path,
        help='Log directory (default: .claude/logs)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate without generating embeddings'
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help='Regenerate embeddings for all documents (ignore existing)'
    )

    args = parser.parse_args()

    # Create generator
    generator = EmbeddingGenerator(
        provider=args.provider,
        batch_size=args.batch_size,
        output_dir=args.output_dir,
        log_dir=args.log_dir,
        dry_run=args.dry_run
    )

    # Generate embeddings
    stats = generator.generate_all(skip_existing=not args.force)

    # Exit with error code if any failures
    return 1 if stats['failed'] > 0 else 0


if __name__ == '__main__':
    sys.exit(main())
