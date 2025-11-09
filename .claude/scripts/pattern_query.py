#!/usr/bin/env python3
"""
Pattern Query CLI - V2.7.0 Pattern Library Foundation

Simple grep-based search on pattern index for MVP.
Semantic search deferred to V2.7.1.

Usage:
    pattern_query.py --list
    pattern_query.py --domain web-app --category testing
    pattern_query.py --keywords "authentication security jwt"
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional


class PatternQuery:
    """Query patterns from library index"""

    def __init__(self):
        self.index_path = Path.home() / '.claude' / 'patterns' / 'index.json'
        self.patterns_dir = Path.home() / '.claude' / 'patterns'
        self.index = self._load_index()

    def _load_index(self) -> Dict[str, Any]:
        """Load pattern index"""
        if not self.index_path.exists():
            print(f"Error: Pattern index not found at {self.index_path}")
            print("Run synthesize_patterns.py to create patterns first.")
            sys.exit(1)

        with open(self.index_path, 'r') as f:
            return json.load(f)

    def list_all(self) -> List[Dict[str, Any]]:
        """List all patterns"""
        return [
            {
                'pattern_id': pid,
                'title': data['title'],
                'domain': data['domain'],
                'category': data['category'],
                'confidence': data['confidence'],
                'evidence_count': data['evidence_count']
            }
            for pid, data in self.index.items()
            if not pid.startswith('_') and pid != 'patterns'  # Skip metadata entries
        ]

    def filter_by_domain(self, domain: str) -> List[Dict[str, Any]]:
        """Filter patterns by domain"""
        results = []
        for pid, data in self.index.items():
            if pid.startswith('_') or pid == 'patterns':  # Skip metadata
                continue
            if domain in data['domain'] or 'universal' in data['domain']:
                results.append({
                    'pattern_id': pid,
                    'title': data['title'],
                    'domain': data['domain'],
                    'category': data['category'],
                    'confidence': data['confidence'],
                    'evidence_count': data['evidence_count']
                })
        return results

    def filter_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Filter patterns by category"""
        results = []
        for pid, data in self.index.items():
            if pid.startswith('_') or pid == 'patterns':  # Skip metadata
                continue
            if data['category'].lower() == category.lower():
                results.append({
                    'pattern_id': pid,
                    'title': data['title'],
                    'domain': data['domain'],
                    'category': data['category'],
                    'confidence': data['confidence'],
                    'evidence_count': data['evidence_count']
                })
        return results

    def search_keywords(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """Search patterns by keywords"""
        results = []
        keywords_lower = [k.lower() for k in keywords]

        for pid, data in self.index.items():
            if pid.startswith('_') or pid == 'patterns':  # Skip metadata
                continue

            # Check if any keyword matches
            pattern_keywords = data.get('keywords', [])
            title_words = data['title'].lower().split()

            matches = False
            for kw in keywords_lower:
                if kw in pattern_keywords or any(kw in tw for tw in title_words):
                    matches = True
                    break

            if matches:
                results.append({
                    'pattern_id': pid,
                    'title': data['title'],
                    'domain': data['domain'],
                    'category': data['category'],
                    'confidence': data['confidence'],
                    'evidence_count': data['evidence_count'],
                    'matched_keywords': [k for k in pattern_keywords if k in keywords_lower]
                })

        return results

    def get_pattern_details(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """Get full pattern details from YAML file"""
        import yaml

        # Search for pattern file
        pattern_files = list(self.patterns_dir.rglob(f"{pattern_id}.yaml"))

        if not pattern_files:
            return None

        with open(pattern_files[0], 'r') as f:
            return yaml.safe_load(f)

    def format_results(self, results: List[Dict[str, Any]], show_details: bool = False):
        """Format and print query results"""
        if not results:
            print("No patterns found matching criteria.")
            return

        print(f"\nFound {len(results)} pattern(s):\n")
        print("=" * 100)

        for i, pattern in enumerate(results, 1):
            print(f"\n{i}. {pattern['pattern_id']}")
            print(f"   Title: {pattern['title']}")
            print(f"   Domain: {', '.join(pattern['domain'])}")
            print(f"   Category: {pattern['category']}")
            print(f"   Confidence: {pattern['confidence']} (based on {pattern['evidence_count']} evidence sources)")

            if 'matched_keywords' in pattern:
                print(f"   Matched Keywords: {', '.join(pattern['matched_keywords'])}")

            if show_details:
                # Load full pattern
                details = self.get_pattern_details(pattern['pattern_id'])
                if details:
                    print(f"\n   Lessons:")
                    for lesson in details.get('lessons', [])[:3]:  # First 3 lessons
                        print(f"     - {lesson}")

                    print(f"\n   Applies When:")
                    for condition in details.get('context', {}).get('applies_when', [])[:3]:
                        print(f"     - {condition}")

            print("-" * 100)

        print()


def main():
    parser = argparse.ArgumentParser(
        description='Query patterns from V2.7 Pattern Library'
    )

    # Query options
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all patterns'
    )
    parser.add_argument(
        '--domain',
        help='Filter by domain (e.g., web-app, cli-tool, workflow-automation)'
    )
    parser.add_argument(
        '--category',
        help='Filter by category (e.g., testing, process, error-handling)'
    )
    parser.add_argument(
        '--keywords',
        help='Search by keywords (space-separated)'
    )
    parser.add_argument(
        '--details',
        action='store_true',
        help='Show detailed pattern information'
    )
    parser.add_argument(
        '--pattern-id',
        help='Get details for specific pattern ID'
    )

    args = parser.parse_args()

    # Create query instance
    query = PatternQuery()

    # Execute query
    if args.pattern_id:
        # Get specific pattern details
        details = query.get_pattern_details(args.pattern_id)
        if details:
            import yaml
            print(yaml.dump(details, default_flow_style=False, sort_keys=False))
        else:
            print(f"Pattern not found: {args.pattern_id}")
            return 1

    elif args.list:
        results = query.list_all()
        query.format_results(results, show_details=args.details)

    elif args.domain:
        results = query.filter_by_domain(args.domain)
        query.format_results(results, show_details=args.details)

    elif args.category:
        results = query.filter_by_category(args.category)
        query.format_results(results, show_details=args.details)

    elif args.keywords:
        keywords = args.keywords.split()
        results = query.search_keywords(keywords)
        query.format_results(results, show_details=args.details)

    else:
        parser.print_help()
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
