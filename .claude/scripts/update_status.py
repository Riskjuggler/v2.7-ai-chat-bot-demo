#!/usr/bin/env python3
"""
Update .claude/status.json with current project state

This script is called by git hooks to maintain real-time status.
Generates machine-readable JSON for fast context loading.
"""

import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Schema normalization mappings
AGENT_NORMALIZATION = {
    'vision alignment': 'vision-alignment',
    'vision': 'vision-alignment',
    'scope control': 'scope-control',
    'scope': 'scope-control',
    'design effectiveness': 'design-effectiveness',
    'design': 'design-effectiveness',
    'code simplicity': 'code-simplicity',
    'simplicity': 'code-simplicity',
    'testing strategy': 'testing-strategy',
    'testing': 'testing-strategy',
    'validation': 'validation',
    'tattle-tale': 'tattle-tale',
    'tattletale': 'tattle-tale'
}

STATUS_NORMALIZATION = {
    'approve': 'ALIGNED',
    'approved': 'ALIGNED',
    'aligned': 'ALIGNED',
    'accept': 'ALIGNED',
    'concerns': 'CONCERNS',
    'approve with concerns': 'CONCERNS',
    'reject': 'NOT_ALIGNED',
    'not aligned': 'NOT_ALIGNED',
    'blocked': 'BLOCKED'
}

def normalize_agent_name(agent: str) -> str:
    """Normalize agent name to canonical schema value"""
    if not agent:
        return 'unknown'
    agent_lower = agent.lower().strip()
    return AGENT_NORMALIZATION.get(agent_lower, agent_lower)

def normalize_status(status: str) -> str:
    """Normalize status to canonical schema value"""
    if not status:
        return 'unknown'
    status_lower = status.lower().strip()
    return STATUS_NORMALIZATION.get(status_lower, status.upper())

def parse_yaml_frontmatter(content: str) -> Optional[Dict]:
    """Parse YAML frontmatter from agent review"""
    match = re.match(r'^---\n(.+?)\n---', content, re.DOTALL)
    if not match:
        return None

    yaml_content = match.group(1)
    frontmatter = {}

    for line in yaml_content.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()

            # Convert to appropriate types
            if value.isdigit():
                value = int(value)
            elif value.lower() in ['true', 'false']:
                value = value.lower() == 'true'

            frontmatter[key] = value

    return frontmatter

def parse_work_unit(file_path: Path) -> Optional[Dict]:
    """Parse work unit markdown file (V2.3: improved ID extraction)"""
    if not file_path.exists():
        return None

    content = file_path.read_text()

    # Extract work unit ID (multiple fallback strategies)
    work_unit_id = None

    # Strategy 1: Explicit **ID** field (highest priority)
    id_match = re.search(r'\*\*ID\*\*:\s*(.+)', content)
    if id_match:
        work_unit_id = id_match.group(1).strip()

    # Strategy 2: **Work Unit ID** field
    if not work_unit_id:
        work_unit_id_match = re.search(r'\*\*Work Unit ID\*\*:\s*(.+)', content)
        if work_unit_id_match:
            work_unit_id = work_unit_id_match.group(1).strip()

    # Strategy 3: Extract from title "# Work Unit: ID - Title"
    if not work_unit_id:
        title_match = re.search(r'# Work Unit:\s*([A-Z0-9]+-[A-Z0-9]+-[A-Z0-9]+|[A-Z]+-\d+[A-Z]?|WU-[A-Z]+-\d+|P\d+-\d+[A-Z]?)', content)
        if title_match:
            work_unit_id = title_match.group(1).strip()

    # Strategy 4: Extract any ID-like pattern from first heading
    if not work_unit_id:
        heading_match = re.search(r'# Work Unit: (.+)', content)
        if heading_match:
            full_title = heading_match.group(1).strip()
            # Try to extract ID from beginning (before " - ")
            if ' - ' in full_title:
                potential_id = full_title.split(' - ')[0].strip()
                # Validate it looks like an ID
                if re.match(r'^[A-Z0-9-]+$', potential_id):
                    work_unit_id = potential_id
            else:
                work_unit_id = full_title

    # Normalize work unit ID (trim whitespace, normalize case for patterns)
    if work_unit_id:
        work_unit_id = work_unit_id.strip()

    # Extract status
    status_match = re.search(r'\*\*Status\*\*:\s*(.+?)(?:\n|\*\*)', content)
    status = status_match.group(1).strip() if status_match else 'UNKNOWN'

    # Extract objective (multiple patterns)
    objective = ""
    # Try "## Objective (One Sentence)" with text on next line
    objective_match = re.search(r'## Objective[^\n]*\n\s*\n(.+)', content)
    if objective_match:
        objective = objective_match.group(1).strip()
    # Fallback: ## Objective with text immediately after
    if not objective:
        objective_match = re.search(r'## Objective[^\n]*\n([^\n#]+)', content)
        if objective_match:
            objective = objective_match.group(1).strip()

    # Extract expected file count (try multiple formats)
    files_expected = 0
    # Try **File Count**
    file_count_match = re.search(r'\*\*File Count\*\*:\s*(\d+)', content)
    if file_count_match:
        files_expected = int(file_count_match.group(1))
    # Try **Files Expected**
    if not files_expected:
        file_count_match = re.search(r'\*\*Files Expected\*\*:\s*(\d+)', content)
        if file_count_match:
            files_expected = int(file_count_match.group(1))
    # Try "File count:" anywhere
    if not files_expected:
        file_count_match = re.search(r'File count:\s*(\d+)', content, re.IGNORECASE)
        if file_count_match:
            files_expected = int(file_count_match.group(1))

    # Extract created date
    created_match = re.search(r'\*\*Created\*\*:\s*(.+)', content)
    created_at = created_match.group(1).strip() if created_match else None

    return {
        'id': work_unit_id,
        'title': work_unit_id if work_unit_id else 'Unknown',
        'status': status,
        'objective': objective,
        'created': created_at,
        'files_expected': files_expected
    }

def find_agent_reviews(reviews_dir: Path, work_unit_id: str) -> List[Dict]:
    """Find all agent reviews for a work unit"""
    if not reviews_dir.exists():
        return []

    reviews = []

    # Look for both plan and output reviews (use wildcard pattern for flexibility)
    # Matches: vision-plan-P5-5A-2025-10-15.md, vision-P5-5A-2025-10-15.md, etc.
    for review_file in reviews_dir.glob(f"*{work_unit_id}*.md"):
        content = review_file.read_text()

        # Try to parse frontmatter
        frontmatter = parse_yaml_frontmatter(content)

        if frontmatter:
            # Normalize schema values
            agent_raw = frontmatter.get('agent', 'unknown')
            status_raw = frontmatter.get('status', 'unknown')

            reviews.append({
                'file': review_file.name,
                'agent': normalize_agent_name(agent_raw),
                'type': frontmatter.get('review_type', 'unknown'),
                'status': normalize_status(status_raw),
                'p0_count': frontmatter.get('p0_count', 0),
                'p1_count': frontmatter.get('p1_count', 0),
                'p2_count': frontmatter.get('p2_count', 0),
                'timestamp': frontmatter.get('timestamp', '')
            })
        else:
            # Fallback for reviews without frontmatter
            agent_match = re.search(r'^([a-z]+)-(?:plan|output)', review_file.name)
            agent = agent_match.group(1) if agent_match else 'unknown'

            reviews.append({
                'file': review_file.name,
                'agent': agent,
                'type': 'plan' if '-plan-' in review_file.name else 'output',
                'status': 'unknown',
                'p0_count': None,
                'p1_count': None,
                'p2_count': None,
                'timestamp': datetime.fromtimestamp(review_file.stat().st_mtime).isoformat()
            })

    return reviews

def get_git_status() -> Dict:
    """Get current git status"""
    try:
        # Last commit
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%H|%at|%s'],
            capture_output=True,
            text=True,
            check=True
        )

        if result.stdout.strip():
            commit_hash, timestamp, message = result.stdout.strip().split('|', 2)
            commit_time = datetime.fromtimestamp(int(timestamp)).isoformat()
        else:
            commit_hash = None
            commit_time = None
            message = None

        # Current branch
        branch_result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            capture_output=True,
            text=True,
            check=True
        )
        branch = branch_result.stdout.strip()

        return {
            'branch': branch,
            'last_commit': {
                'hash': commit_hash[:7] if commit_hash else None,
                'timestamp': commit_time,
                'message': message
            }
        }
    except subprocess.CalledProcessError:
        return {
            'branch': 'unknown',
            'last_commit': None
        }

def get_memory_status() -> Optional[Dict]:
    """Check if memory system is active and get statistics"""
    vector_db = Path('.claude/vector_db.sqlite')

    if not vector_db.exists():
        return None

    try:
        import sqlite3

        conn = sqlite3.connect(str(vector_db))
        cursor = conn.cursor()

        # Get document count
        cursor.execute("SELECT COUNT(*) FROM documents")
        doc_count = cursor.fetchone()[0]

        # Get last updated timestamp from file modification time
        last_updated = datetime.fromtimestamp(vector_db.stat().st_mtime).isoformat()

        conn.close()

        return {
            'active': True,
            'documents_indexed': doc_count,
            'last_updated': last_updated,
            'query_command': 'python3 .claude/scripts/query_memory.py'
        }
    except Exception as e:
        # If we can't read the database, consider memory inactive
        return None

def update_test_health(test_results_path='.claude/logs/test-results.json'):
    """Update test_health section in status.json

    Args:
        test_results_path: Path to test results JSON file

    Returns:
        dict with test health metrics, or None if file doesn't exist

    Raises:
        json.JSONDecodeError: If test results file is malformed
    """
    test_results_file = Path(test_results_path)
    if not test_results_file.exists():
        return None

    with open(test_results_file) as f:
        results = json.load(f)

    tests = results.get('tests', 0)
    passed = results.get('passed', 0)

    # Avoid division by zero
    pass_rate = round(passed / tests * 100, 1) if tests > 0 else 0.0

    return {
        'last_run': results.get('timestamp'),
        'collection_errors': results.get('collection_errors', 0),
        'tests_collected': tests,
        'tests_passed': passed,
        'tests_failed': results.get('failed', 0),
        'pass_rate': pass_rate
    }

def update_status_json(output_path: Path):
    """Generate status.json with current project state"""

    # Parse current work unit
    work_unit_file = Path('.claude/current_work_unit.md')
    work_unit = parse_work_unit(work_unit_file)

    # Find agent reviews
    reviews_dir = Path('.claude/agent-reviews')
    reviews = []
    p0_total = 0
    p1_total = 0
    p2_total = 0

    if work_unit and work_unit['id']:
        reviews = find_agent_reviews(reviews_dir, work_unit['id'])

        # Count P0/P1/P2 issues
        for review in reviews:
            if review['p0_count'] is not None:
                p0_total += review['p0_count']
            if review['p1_count'] is not None:
                p1_total += review['p1_count']
            if review['p2_count'] is not None:
                p2_total += review['p2_count']

    # Get git status
    git_status = get_git_status()

    # Get memory system status (V2.6: memory integration)
    memory_status = get_memory_status()

    # Get test health status (V2.6.1: test health monitoring)
    test_health = update_test_health()

    # Build status object
    status = {
        'last_updated': datetime.now().isoformat(),
        'current_work_unit': work_unit if work_unit else {
            'id': None,
            'title': 'Unknown',
            'status': 'UNKNOWN',
            'objective': '',
            'created': None,
            'files_expected': 0
        },
        'agent_reviews': {
            'count': len(reviews),
            'required': 7,
            'p0_total': p0_total,
            'p1_total': p1_total,
            'p2_total': p2_total,
            'reviews': reviews
        },
        'git': git_status,
        'workflow_version': 'v2.6'
    }

    # Add memory system section if active
    if memory_status:
        status['memory_system'] = memory_status

    # Add test health section if available (V2.6.1: test health monitoring)
    if test_health:
        status['test_health'] = test_health

    # Write to file
    with open(output_path, 'w') as f:
        json.dump(status, f, indent=2)

    print(f"✅ Status updated: {output_path}")
    print(f"   Work Unit: {status['current_work_unit']['id'] or 'None'}")
    print(f"   Reviews: {len(reviews)}/7")
    if p0_total > 0:
        print(f"   ⚠️  P0 Issues: {p0_total}")
    if memory_status:
        print(f"   🧠 Memory: {memory_status['documents_indexed']} documents indexed")

def main():
    """Main entry point"""
    output_path = Path('.claude/status.json')
    update_status_json(output_path)

if __name__ == '__main__':
    main()
