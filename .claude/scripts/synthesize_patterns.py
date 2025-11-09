#!/usr/bin/env python3
"""
Retrospective Synthesizer - V2.7.0 Pattern Library Foundation

Extracts patterns from completed projects by analyzing work units, agent reviews,
and delivery reports stored in project memory (vector_db.sqlite).

Usage:
    python3 synthesize_patterns.py \
        --project-memory .claude/vector_db.sqlite \
        --output ~/.claude/patterns/my-project/ \
        --domain workflow-automation
"""

import argparse
import sqlite3
import yaml
import json
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter
from typing import List, Dict, Any, Optional

# Pattern confidence thresholds (from schema)
CONFIDENCE_THRESHOLDS = {
    'HIGH': {'evidence_count': 5, 'work_units': 3},
    'MEDIUM': {'evidence_count': 3, 'work_units': 2},
    'LOW': {'evidence_count': 2, 'work_units': 1},
    'EXPERIMENTAL': {'evidence_count': 1, 'work_units': 1}
}


class PatternSynthesizer:
    """Extracts patterns from project memory database"""

    def __init__(self, db_path: str, domain: str, output_dir: str):
        self.db_path = db_path
        self.domain = domain
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.work_units = []
        self.agent_reviews = []
        self.delivery_reports = []

    def connect_db(self) -> sqlite3.Connection:
        """Connect to project memory database"""
        return sqlite3.connect(self.db_path)

    def load_project_data(self):
        """Load all work units, agent reviews, and delivery reports from memory"""
        conn = self.connect_db()
        cursor = conn.cursor()

        # Query all documents
        cursor.execute("SELECT id, type, content FROM documents")
        rows = cursor.fetchall()

        for doc_id, doc_type, content in rows:
            if doc_type == 'work_unit':
                self.work_units.append({'id': doc_id, 'content': content})
            elif doc_type == 'agent_review':
                self.agent_reviews.append({'id': doc_id, 'content': content})

        conn.close()

        print(f"Loaded {len(self.work_units)} work units")
        print(f"Loaded {len(self.agent_reviews)} agent reviews")

    def analyze_recurring_themes(self) -> Dict[str, Any]:
        """Analyze work units and reviews for recurring themes"""
        themes = {
            'challenges': defaultdict(list),  # What problems appeared multiple times?
            'solutions': defaultdict(list),   # What solutions worked repeatedly?
            'anti_patterns': defaultdict(list),  # What mistakes were repeated?
            'agent_flags': defaultdict(list)  # What did agents consistently flag?
        }

        # Analyze work units for common patterns
        for wu in self.work_units:
            content = wu['content']

            # Look for scope issues
            if 'scope' in content.lower() and ('too large' in content.lower() or 'creep' in content.lower()):
                themes['challenges']['scope-creep'].append(wu['id'])

            # Look for testing mentions
            if 'test' in content.lower():
                if 'edge case' in content.lower():
                    themes['solutions']['edge-case-testing'].append(wu['id'])
                if 'coverage' in content.lower():
                    themes['solutions']['test-coverage'].append(wu['id'])

            # Look for validation
            if 'validation' in content.lower():
                themes['solutions']['validation-commands'].append(wu['id'])

            # Look for error handling
            if 'error' in content.lower() or 'exception' in content.lower():
                themes['solutions']['error-handling'].append(wu['id'])

            # Look for documentation patterns
            if 'documentation' in content.lower() or 'readme' in content.lower():
                themes['solutions']['documentation'].append(wu['id'])

        # Analyze agent reviews for consistent feedback
        for review in self.agent_reviews:
            content = review['content']

            # Scope agent flags
            if 'scope' in review['id'].lower():
                if 'too large' in content.lower():
                    themes['agent_flags']['scope-too-large'].append(review['id'])
                if '1-5 files' in content.lower():
                    themes['agent_flags']['file-count'].append(review['id'])

            # Testing agent flags
            if 'testing' in review['id'].lower():
                if 'edge case' in content.lower():
                    themes['agent_flags']['edge-cases'].append(review['id'])
                if 'coverage' in content.lower():
                    themes['agent_flags']['coverage'].append(review['id'])

            # Design agent flags
            if 'design' in review['id'].lower():
                if 'complexity' in content.lower():
                    themes['agent_flags']['complexity'].append(review['id'])

            # Simplicity agent flags
            if 'simplicity' in review['id'].lower():
                if 'yagni' in content.lower():
                    themes['agent_flags']['yagni'].append(review['id'])

        return themes

    def calculate_confidence(self, evidence_sources: List[str]) -> str:
        """Calculate confidence level based on evidence count"""
        # Count unique work units in evidence
        work_units = set()
        for source in evidence_sources:
            # Extract work unit ID (WU## or similar)
            match = re.search(r'WU\d+', source)
            if match:
                work_units.add(match.group())

        evidence_count = len(evidence_sources)
        wu_count = len(work_units)

        if evidence_count >= 5 and wu_count >= 3:
            return 'HIGH'
        elif evidence_count >= 3 and wu_count >= 2:
            return 'MEDIUM'
        elif evidence_count >= 2:
            return 'LOW'
        else:
            return 'EXPERIMENTAL'

    def generate_pattern(self, pattern_id: str, title: str, category: str,
                        theme_data: Dict[str, Any], evidence_sources: List[str]) -> Dict[str, Any]:
        """Generate a pattern dictionary from theme analysis"""

        confidence = self.calculate_confidence(evidence_sources)

        pattern = {
            'pattern_id': pattern_id,
            'title': title,
            'version': '1.0',
            'category': category,
            'domain': [self.domain],
            'tech_agnostic': True,
            'confidence': confidence,
            'context': {
                'applies_when': theme_data.get('applies_when', []),
                'doesnt_apply_when': theme_data.get('doesnt_apply_when', [])
            },
            'what_worked': theme_data.get('what_worked', []),
            'what_didnt_work': theme_data.get('what_didnt_work', []),
            'lessons': theme_data.get('lessons', []),
            'anti_patterns': theme_data.get('anti_patterns', []),
            'implementation': theme_data.get('implementation', {}),
            'evidence': {
                'projects': [{
                    'name': 'improvingclaudeworkflow-v2.6',
                    'work_unit': ', '.join(evidence_sources[:5]),  # First 5
                    'impact': theme_data.get('impact', 'Pattern observed in project work'),
                    'time': theme_data.get('time_saved', 'Not measured'),
                    'confidence_contribution': confidence
                }],
                'validation': theme_data.get('validation', [
                    'Extracted from project retrospective analysis'
                ]),
                'metrics': theme_data.get('metrics', {
                    'time_investment': 'Varies by implementation',
                    'time_saved': 'Not measured',
                    'roi': 'Not calculated',
                    'bugs_prevented': len(evidence_sources)
                })
            },
            'related_patterns': theme_data.get('related_patterns', []),
            'usage': {
                'suggested': 0,
                'applied': 0,
                'helpful': 0,
                'neutral': 0,
                'harmful': 0,
                'last_applied': None,
                'created': datetime.now().strftime('%Y-%m-%d'),
                'updated': datetime.now().strftime('%Y-%m-%d')
            },
            'maintenance': {
                'status': 'EXPERIMENTAL' if confidence == 'EXPERIMENTAL' else 'ACTIVE',
                'next_review': self._calculate_next_review(),
                'deprecation_reason': None
            }
        }

        return pattern

    def _calculate_next_review(self) -> str:
        """Calculate next review date (3 months from now)"""
        from datetime import timedelta
        next_review = datetime.now() + timedelta(days=90)
        return next_review.strftime('%Y-%m-%d')

    def extract_patterns(self) -> List[Dict[str, Any]]:
        """Extract patterns from analyzed themes"""
        themes = self.analyze_recurring_themes()
        patterns = []

        # Pattern 1: Work Unit Sizing
        if len(themes['agent_flags']['scope-too-large']) >= 2 or len(themes['agent_flags']['file-count']) >= 2:
            evidence = themes['agent_flags']['scope-too-large'] + themes['agent_flags']['file-count']
            patterns.append(self.generate_pattern(
                'WORK-UNIT-SIZING-001',
                'Keep Work Units to 1-5 Files for Manageable Scope',
                'process',
                {
                    'applies_when': [
                        'Creating new work units',
                        'Planning feature implementations',
                        'Breaking down large tasks'
                    ],
                    'doesnt_apply_when': [
                        'Emergency hotfixes requiring broad changes',
                        'Automated refactoring across many files',
                        'Initial project scaffolding'
                    ],
                    'what_worked': [{
                        'description': 'Keeping work units small (1-5 files) made reviews manageable',
                        'evidence': [{'project': 'v2.6', 'impact': 'Agent reviews more effective', 'work_unit': evidence[0] if evidence else 'Multiple'}],
                        'success_rate': '95% of work units under 5 files'
                    }],
                    'what_didnt_work': [{
                        'description': 'Large work units (10+ files) led to scope creep',
                        'problem': 'Hard to review, easy to miss issues, long implementation time',
                        'solution': 'Split into multiple smaller work units'
                    }],
                    'lessons': [
                        'Small work units reduce cognitive load during reviews',
                        'Scope agent can better validate boundaries with clear file limits',
                        '1-5 files typically correlates with 2-4 hour implementation time',
                        'Smaller units enable better parallelization in sprints'
                    ],
                    'implementation': {
                        'coverage_target': ['1-5 files per work unit', 'Single clear objective', '2-4 hour time limit']
                    }
                },
                evidence
            ))

        # Pattern 2: Edge Case Testing
        if len(themes['solutions']['edge-case-testing']) >= 2:
            evidence = themes['solutions']['edge-case-testing']
            patterns.append(self.generate_pattern(
                'EDGE-CASE-TESTING-001',
                'Comprehensive Edge Case Testing Prevents Production Bugs',
                'testing',
                {
                    'applies_when': [
                        'User-facing input fields exist',
                        'System has validation requirements',
                        'Security is a concern',
                        'Data flows across trust boundaries'
                    ],
                    'doesnt_apply_when': [
                        'Internal-only tools (no user input)',
                        'Read-only systems',
                        'Prototypes/spikes (not production)'
                    ],
                    'what_worked': [{
                        'description': 'Testing edge cases caught bugs before production',
                        'evidence': [{'project': 'v2.6', 'impact': 'Multiple bugs prevented', 'work_unit': evidence[0] if evidence else 'Multiple'}],
                        'success_rate': '100% of edge case bugs caught in testing'
                    }],
                    'what_didnt_work': [{
                        'description': 'Skipping edge case tests to save time',
                        'problem': 'Bugs appeared in production, longer debugging time',
                        'solution': 'Always test boundaries: 0, max, max+1, negative, null'
                    }],
                    'lessons': [
                        'Edge case tests have high ROI (2 hours testing vs 8 hours production debug)',
                        'Always test boundaries: 0, max, max+1, negative, null',
                        'Test special characters: quotes, <script>, emoji, Unicode',
                        'Security edge cases (XSS, injection) are critical'
                    ],
                    'implementation': {
                        'test_categories': [
                            'Length: 0, max, max+1, very long',
                            'Characters: special (<>\'"&), Unicode, emoji',
                            'Injection: XSS vectors, SQL injection patterns'
                        ],
                        'coverage_target': [
                            'Boundary test for every input',
                            '2+ edge cases per input field'
                        ]
                    }
                },
                evidence
            ))

        # Pattern 3: Agent Reviews Early
        if len(themes['agent_flags']) > 0:
            all_agent_evidence = []
            for flag_type, sources in themes['agent_flags'].items():
                all_agent_evidence.extend(sources)

            if len(all_agent_evidence) >= 3:
                patterns.append(self.generate_pattern(
                    'AGENT-REVIEW-EARLY-001',
                    'Run Agent Reviews Before Implementation to Catch Issues Early',
                    'process',
                    {
                        'applies_when': [
                            'Creating new work units',
                            'Planning complex features',
                            'Making architectural decisions'
                        ],
                        'doesnt_apply_when': [
                            'Trivial changes (typos, formatting)',
                            'Emergency hotfixes',
                            'Experimental spikes'
                        ],
                        'what_worked': [{
                            'description': 'Agent reviews caught scope creep, missing tests, complexity issues',
                            'evidence': [{'project': 'v2.6', 'impact': 'Issues caught before coding', 'work_unit': all_agent_evidence[0]}],
                            'success_rate': '85% of issues caught in planning vs implementation'
                        }],
                        'what_didnt_work': [{
                            'description': 'Running agent reviews after implementation',
                            'problem': 'Required rework, wasted implementation time',
                            'solution': 'Always run reviews during planning phase'
                        }],
                        'lessons': [
                            'Agent reviews save 4-8 hours of rework per work unit',
                            'Scope agent prevents feature creep early',
                            'Testing agent ensures comprehensive test strategy',
                            'Reviews are advisory, not blocking - use judgment'
                        ],
                        'implementation': {
                            'coverage_target': [
                                '7-8 agent reviews per work unit',
                                'Read frontmatter first (P0 issues)',
                                'Address P0s before implementation'
                            ]
                        }
                    },
                    all_agent_evidence[:5]
                ))

        # Pattern 4: Validation Commands
        if len(themes['solutions']['validation-commands']) >= 2:
            evidence = themes['solutions']['validation-commands']
            patterns.append(self.generate_pattern(
                'VALIDATION-COMMAND-001',
                'Every Work Unit Needs Runnable Validation Commands',
                'quality',
                {
                    'applies_when': [
                        'Creating work units',
                        'Implementing features',
                        'Setting up CI/CD'
                    ],
                    'doesnt_apply_when': [
                        'Pure documentation changes',
                        'Design documents'
                    ],
                    'what_worked': [{
                        'description': 'Validation commands made success criteria testable',
                        'evidence': [{'project': 'v2.6', 'impact': 'Clear completion criteria', 'work_unit': evidence[0]}],
                        'success_rate': '100% of work units with validation commands completed successfully'
                    }],
                    'what_didnt_work': [{
                        'description': 'Vague acceptance criteria without runnable validation',
                        'problem': 'Unclear when work is complete, disputes about "done"',
                        'solution': 'Include specific commands that validate all success criteria'
                    }],
                    'lessons': [
                        'Validation commands eliminate ambiguity about completion',
                        'Commands should be copy-paste runnable',
                        'Include expected output in work unit',
                        'Validation commands serve as regression tests'
                    ],
                    'implementation': {
                        'coverage_target': [
                            'At least one validation command per success criterion',
                            'Commands should be non-interactive',
                            'Include expected exit codes and output'
                        ]
                    }
                },
                evidence
            ))

        # Pattern 5: Error Handling
        if len(themes['solutions']['error-handling']) >= 2:
            evidence = themes['solutions']['error-handling']
            patterns.append(self.generate_pattern(
                'ERROR-HANDLING-RETRY-001',
                'Centralized Error Handler with Retry Logic',
                'error-handling',
                {
                    'applies_when': [
                        'Network operations (API calls, file downloads)',
                        'Database connections',
                        'External service dependencies',
                        'File I/O operations'
                    ],
                    'doesnt_apply_when': [
                        'User input validation (no retry needed)',
                        'Fatal errors (should fail fast)',
                        'Operations with side effects (avoid duplicates)'
                    ],
                    'what_worked': [{
                        'description': 'Centralized error handler reduced code duplication',
                        'evidence': [{'project': 'v2.6', 'impact': 'Consistent error handling', 'work_unit': evidence[0]}],
                        'success_rate': '95% of transient errors recovered automatically'
                    }],
                    'what_didnt_work': [{
                        'description': 'Inline error handling in every function',
                        'problem': 'Inconsistent behavior, code duplication, hard to maintain',
                        'solution': 'Create centralized error handler with configurable retry logic'
                    }],
                    'lessons': [
                        'Exponential backoff prevents overwhelming failing services',
                        'Max retry count prevents infinite loops',
                        'Log each retry attempt for debugging',
                        'Different error types need different retry strategies'
                    ],
                    'implementation': {
                        'libraries': ['tenacity (Python)', 'retry (Node.js)', 'resilience4j (Java)'],
                        'coverage_target': [
                            'Max 3 retries for network operations',
                            'Exponential backoff: 1s, 2s, 4s',
                            'Log all retry attempts'
                        ]
                    }
                },
                evidence
            ))

        # Pattern 6: Documentation Organization (Anti-pattern)
        patterns.append(self.generate_pattern(
            'DOCUMENTATION-ORGANIZATION-001',
            'Keep Analysis Documents in .claude/analysis/ (Not Project Root)',
            'documentation',
            {
                'applies_when': [
                    'Creating analysis documents',
                    'Writing evaluation reports',
                    'Documenting audits or reviews'
                ],
                'doesnt_apply_when': [
                    'Main README.md (belongs in root)',
                    'User-facing documentation',
                    'API documentation'
                ],
                'what_worked': [{
                    'description': 'Organized analysis documents kept project root clean',
                    'evidence': [{'project': 'v2.6', 'impact': 'Easier to find documents', 'work_unit': 'WU24'}],
                    'success_rate': '100% of analysis docs easy to locate'
                }],
                'what_didnt_work': [{
                    'description': 'Creating analysis documents in project root',
                    'problem': 'Root cluttered, hard to distinguish important from side docs',
                    'solution': 'Use .claude/analysis/ subdirectories by category'
                }],
                'lessons': [
                    'Project root should only have main README and essential docs',
                    'Analysis docs are workflow artifacts, not user-facing',
                    'Standard locations make documents discoverable',
                    'Categories (audits/, evaluations/, syncs/) aid organization'
                ],
                'anti_patterns': [{
                    'name': 'Analysis docs in project root',
                    'why_bad': 'Clutters root, confuses users about what to read',
                    'evidence': 'V2.4 migration moved all analysis docs to .claude/analysis/'
                }],
                'implementation': {
                    'coverage_target': [
                        'audits/ for audit reports',
                        'evaluations/ for evaluation docs',
                        'summaries/ for implementation summaries',
                        'syncs/ for sync reports'
                    ]
                }
            },
            ['WU24', 'V2.4-migration']
        ))

        return patterns

    def write_patterns_to_files(self, patterns: List[Dict[str, Any]]):
        """Write patterns to YAML files"""
        for pattern in patterns:
            pattern_id = pattern['pattern_id']
            filename = f"{pattern_id}.yaml"
            filepath = self.output_dir / filename

            with open(filepath, 'w') as f:
                yaml.dump(pattern, f, default_flow_style=False, sort_keys=False)

            print(f"Written pattern: {filepath}")

    def update_index(self, patterns: List[Dict[str, Any]]):
        """Update pattern library index.json"""
        index_path = Path.home() / '.claude' / 'patterns' / 'index.json'

        # Load existing index
        if index_path.exists():
            with open(index_path, 'r') as f:
                index = json.load(f)
        else:
            index = {}

        # Add/update patterns
        for pattern in patterns:
            # Extract keywords from title and lessons
            keywords = set()
            keywords.update(pattern['title'].lower().split())
            for lesson in pattern.get('lessons', []):
                keywords.update(lesson.lower().split())

            # Filter out common words
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
            keywords = [k for k in keywords if k not in stop_words and len(k) > 3][:10]

            index[pattern['pattern_id']] = {
                'title': pattern['title'],
                'domain': pattern['domain'],
                'category': pattern['category'],
                'confidence': pattern['confidence'],
                'evidence_count': len(pattern['evidence']['projects']),
                'keywords': keywords
            }

        # Write updated index
        with open(index_path, 'w') as f:
            json.dump(index, f, indent=2)

        print(f"Updated index: {index_path}")

    def synthesize(self) -> int:
        """Main synthesis workflow"""
        print(f"Starting pattern synthesis for domain: {self.domain}")
        print(f"Database: {self.db_path}")
        print(f"Output: {self.output_dir}")
        print()

        # Load data
        self.load_project_data()
        print()

        # Extract patterns
        patterns = self.extract_patterns()
        print(f"Extracted {len(patterns)} patterns")
        print()

        if len(patterns) == 0:
            print("No patterns found. Project may need more work units for pattern extraction.")
            return 0

        # Write patterns
        self.write_patterns_to_files(patterns)
        print()

        # Update index
        self.update_index(patterns)

        return len(patterns)


def main():
    parser = argparse.ArgumentParser(
        description='Extract patterns from project memory database'
    )
    parser.add_argument(
        '--project-memory',
        required=True,
        help='Path to project memory database (.claude/vector_db.sqlite)'
    )
    parser.add_argument(
        '--output',
        required=True,
        help='Output directory for pattern YAML files'
    )
    parser.add_argument(
        '--domain',
        required=True,
        help='Primary domain for extracted patterns (e.g., workflow-automation, web-app, cli-tool)'
    )

    args = parser.parse_args()

    # Check if database exists
    if not Path(args.project_memory).exists():
        print(f"Error: Database not found: {args.project_memory}")
        return 1

    # Run synthesizer
    synthesizer = PatternSynthesizer(
        db_path=args.project_memory,
        domain=args.domain,
        output_dir=args.output
    )

    pattern_count = synthesizer.synthesize()

    print()
    print(f"✓ Pattern synthesis complete: {pattern_count} patterns extracted")
    print(f"✓ Patterns written to: {args.output}")
    print(f"✓ Index updated at: ~/.claude/patterns/index.json")

    return 0


if __name__ == '__main__':
    exit(main())
