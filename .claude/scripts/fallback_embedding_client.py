#!/usr/bin/env python3
"""
Fallback Embedding Client (WU11)

Three-tier graceful degradation for embedding generation:
  Tier 1: LM Studio (preferred, local, private)
  Tier 2: OpenAI API (cloud, requires key)
  Tier 3: Keyword Search (always available)

Features:
- Automatic fallback on provider failure
- Health check integration (skip unhealthy providers)
- User notifications on degradation
- Performance metrics tracking
- Transparent degradation

Usage:
    from fallback_embedding_client import FallbackEmbeddingClient

    client = FallbackEmbeddingClient()
    embedding, provider_used = client.generate_embedding("test query")

    # For keyword search fallback
    results = client.keyword_search("test query", limit=10)
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Import existing providers
import sys
sys.path.insert(0, str(Path(__file__).parent))

from lm_studio_client import LMStudioClient
from keyword_search import KeywordSearchFallback


logger = logging.getLogger('FallbackEmbeddingClient')


class FallbackEmbeddingClient:
    """Embedding client with three-tier fallback"""

    def __init__(
        self,
        db_path: str = ".claude/vector_db.sqlite",
        health_status_path: str = ".claude/logs/health-status.json",
        enable_notifications: bool = True
    ):
        """
        Initialize fallback embedding client

        Args:
            db_path: Path to vector database (for keyword search)
            health_status_path: Path to health status JSON
            enable_notifications: Display fallback notifications
        """
        self.db_path = db_path
        self.health_status_path = Path(health_status_path)
        self.enable_notifications = enable_notifications

        # Initialize providers
        self.lm_studio_client = LMStudioClient()
        self.keyword_search_client = KeywordSearchFallback(db_path=db_path)

        # Degradation log (use same directory as health status for consistency in tests)
        log_dir = self.health_status_path.parent if self.health_status_path.parent.exists() else Path('.claude/logs')
        self.degradation_log_path = log_dir / 'degradation.log'
        self.degradation_log_path.parent.mkdir(parents=True, exist_ok=True)

        # Performance metrics
        self.metrics_path = log_dir / 'embedding-metrics.json'
        self.metrics_path.parent.mkdir(parents=True, exist_ok=True)

        # Last notification time (rate limiting)
        self.last_notification_time = {}

    def _should_notify(self, provider: str) -> bool:
        """
        Check if notification should be displayed (rate limiting)

        Args:
            provider: Provider name

        Returns:
            True if notification should be shown
        """
        if not self.enable_notifications:
            return False

        # Rate limit: max 1 notification per provider per 5 minutes
        now = time.time()
        last_time = self.last_notification_time.get(provider, 0)

        if now - last_time < 300:  # 5 minutes
            return False

        self.last_notification_time[provider] = now
        return True

    def _notify_fallback(self, from_provider: str, to_provider: str, reason: str):
        """
        Notify user of fallback degradation

        Args:
            from_provider: Failed provider
            to_provider: Fallback provider
            reason: Failure reason
        """
        # Always log degradation events (for metrics)
        self._log_degradation_event(from_provider, to_provider, reason)

        # User notification (rate-limited)
        if not self._should_notify(from_provider):
            return

        messages = {
            'lm_studio': '⚠ LM Studio unavailable',
            'openai': '⚠ OpenAI API unavailable',
            'keyword': 'ℹ Using basic keyword search'
        }

        quality_notes = {
            'openai': '(cloud provider - may be slower)',
            'keyword': '(basic search - lower quality results)'
        }

        from_msg = messages.get(from_provider, from_provider)
        to_note = quality_notes.get(to_provider, '')

        print(f"\n{from_msg} - falling back to {to_provider} {to_note}")
        print(f"Reason: {reason}\n")

    def _log_degradation_event(self, from_provider: str, to_provider: str, reason: str):
        """
        Log degradation event to file

        Args:
            from_provider: Failed provider
            to_provider: Fallback provider
            reason: Failure reason
        """
        try:
            timestamp = datetime.now().isoformat()
            log_entry = f"[{timestamp}] {from_provider} -> {to_provider}: {reason}\n"

            with open(self.degradation_log_path, 'a') as f:
                f.write(log_entry)

        except Exception as e:
            logger.warning(f"Failed to log degradation event: {e}")

    def _read_health_status(self) -> Dict:
        """
        Read health status from file

        Returns:
            Health status dict, or empty dict if unavailable
        """
        try:
            if not self.health_status_path.exists():
                return {}

            with open(self.health_status_path, 'r') as f:
                return json.load(f)

        except Exception as e:
            logger.warning(f"Failed to read health status: {e}")
            return {}

    def _is_provider_healthy(self, provider: str) -> bool:
        """
        Check if provider is marked healthy

        Args:
            provider: Provider name ('lm_studio', 'openai')

        Returns:
            True if healthy, False if known to be unhealthy
        """
        health_status = self._read_health_status()

        if not health_status:
            return True  # Assume healthy if no status available

        checks = health_status.get('checks', {})
        provider_status = checks.get(provider, {})

        # Check status field
        status = provider_status.get('status', 'ok')
        return status in ['ok', 'info']  # 'error' or 'warning' = unhealthy

    def _record_metrics(
        self,
        provider: str,
        success: bool,
        response_time: float,
        error: Optional[str] = None
    ):
        """
        Record performance metrics

        Args:
            provider: Provider name
            success: Whether operation succeeded
            response_time: Time taken in seconds
            error: Error message if failed
        """
        try:
            # Read existing metrics
            if self.metrics_path.exists():
                with open(self.metrics_path, 'r') as f:
                    metrics = json.load(f)
            else:
                metrics = {'events': []}

            # Add event
            event = {
                'timestamp': datetime.now().isoformat(),
                'provider': provider,
                'success': success,
                'response_time': response_time,
                'error': error
            }

            metrics['events'].append(event)

            # Keep last 1000 events
            metrics['events'] = metrics['events'][-1000:]

            # Write back
            with open(self.metrics_path, 'w') as f:
                json.dump(metrics, f, indent=2)

        except Exception as e:
            logger.warning(f"Failed to record metrics: {e}")

    def generate_embedding(self, text: str) -> Tuple[Optional[List[float]], str]:
        """
        Generate embedding with fallback chain

        Args:
            text: Input text

        Returns:
            Tuple of (embedding vector, provider_used)
            Returns (None, 'failed') if all providers fail
        """
        # Tier 1: LM Studio (preferred)
        if self._is_provider_healthy('lm_studio'):
            start_time = time.time()
            try:
                embedding = self.lm_studio_client.generate_embedding(text)
                response_time = time.time() - start_time

                if embedding:
                    self._record_metrics('lm_studio', True, response_time)
                    logger.debug("Using LM Studio (Tier 1)")
                    return embedding, 'lm_studio'

                # Failed - record and fallback
                self._record_metrics('lm_studio', False, response_time, "Returned None")

            except Exception as e:
                response_time = time.time() - start_time
                self._record_metrics('lm_studio', False, response_time, str(e))
                logger.warning(f"LM Studio failed: {e}")

            # Notify fallback to Tier 2
            self._notify_fallback('lm_studio', 'openai', 'Service unavailable or returned None')
        else:
            logger.debug("Skipping LM Studio (marked unhealthy)")
            self._notify_fallback('lm_studio', 'openai', 'Marked unhealthy in health check')

        # Tier 2: OpenAI API
        if self.lm_studio_client.openai_api_key:
            if self._is_provider_healthy('openai'):
                start_time = time.time()
                try:
                    embedding = self.lm_studio_client._generate_embedding_openai(text)
                    response_time = time.time() - start_time

                    if embedding:
                        self._record_metrics('openai', True, response_time)
                        logger.debug("Using OpenAI API (Tier 2)")
                        return embedding, 'openai'

                    # Failed - record
                    self._record_metrics('openai', False, response_time, "Returned None")

                except Exception as e:
                    response_time = time.time() - start_time
                    self._record_metrics('openai', False, response_time, str(e))
                    logger.warning(f"OpenAI API failed: {e}")
            else:
                logger.debug("Skipping OpenAI (marked unhealthy)")
        else:
            logger.debug("Skipping OpenAI (no API key)")

        # Tier 3: Return None (caller will use keyword search)
        # We don't generate embeddings for keyword search
        self._notify_fallback('openai', 'keyword', 'All embedding providers unavailable')
        return None, 'keyword'

    def keyword_search(
        self,
        query: str,
        limit: int = 10,
        document_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Perform keyword search (Tier 3 fallback)

        Args:
            query: Search query
            limit: Maximum results
            document_type: Optional type filter

        Returns:
            List of result dicts
        """
        start_time = time.time()
        try:
            results = self.keyword_search_client.search(
                query=query,
                limit=limit,
                document_type=document_type
            )
            response_time = time.time() - start_time

            self._record_metrics('keyword', True, response_time)
            logger.debug(f"Keyword search returned {len(results)} results")
            return results

        except Exception as e:
            response_time = time.time() - start_time
            self._record_metrics('keyword', False, response_time, str(e))
            logger.error(f"Keyword search failed: {e}")
            return []


def main():
    """CLI entry point for testing"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 fallback_embedding_client.py <text>")
        return 1

    text = sys.argv[1]

    # Test embedding generation
    client = FallbackEmbeddingClient()
    embedding, provider = client.generate_embedding(text)

    if embedding:
        print(f"\n✅ Embedding generated using {provider}")
        print(f"   Dimensions: {len(embedding)}")
        print(f"   First 5 values: {embedding[:5]}")
    else:
        print(f"\n⚠ Embedding failed, falling back to keyword search")
        print(f"   Provider chain exhausted: {provider}")

        # Test keyword search
        results = client.keyword_search(text, limit=5)
        print(f"\n   Keyword search returned {len(results)} results")

    return 0


if __name__ == '__main__':
    sys.exit(main())
