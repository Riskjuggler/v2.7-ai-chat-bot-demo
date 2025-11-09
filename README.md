# v2.7-test

**Purpose**: Testing and validation environment for V2.7.2 workflow features

**Workflow Version**: V2.7.2 (Consolidated)

## Project Overview

This is a test project for validating and demonstrating V2.7.2 workflow capabilities:
- Consolidated CLAUDE.md templates (50-60% size reduction)
- Pattern Library integration (cross-project learning)
- Memory System support (project-specific semantic search)
- Daily memory indexing automation
- Seven-agent review workflow

## V2.7.2 Features

### Template Consolidation
- **Global template**: 565 lines (down from 914 lines in V2.7.0)
- **Project template**: 426 lines with project-specific customization
- **Token savings**: 93% reduction in context loading

### Pattern Library
Global patterns from all projects at `~/.claude/patterns/`:

```bash
# Query cross-project patterns
python3 .claude/scripts/pattern_query.py --query "background testing"
python3 .claude/scripts/pattern_query.py --query "API design patterns"
```

**Pattern vs Memory:**
- **Memory**: "What have WE done in THIS project?"
- **Patterns**: "What have we learned ACROSS ALL projects?"

### Memory System (Optional)
Project-specific semantic search when activated:

```bash
# Query project history
python3 .claude/scripts/query_memory.py --query "error handling"

# Generate embeddings (runs automatically daily via post-commit hook)
python3 .claude/scripts/generate_embeddings.py
```

### Daily Memory Indexing
Post-commit hook automatically:
- Generates embeddings for new work units/reviews
- Imports into vector database
- Runs once per day in background
- Ensures recent work searchable within 24 hours

## Quick Start

**Session start:**
```bash
cat .claude/status.json
```

**Query patterns:**
```bash
python3 .claude/scripts/pattern_query.py --query "[topic]"
```

**Commit:**
```bash
git add .
git commit -m "message"
# Daily memory indexing runs automatically on first commit of the day
```

## Workflow Infrastructure

**Deployed components:**
- ✅ V2.7.2 CLAUDE.md template
- ✅ Pattern query scripts
- ✅ Memory system scripts
- ✅ Post-commit hook with daily indexing
- ✅ status.json automation
- ✅ Directory structure (.claude/*)

**Git hooks:**
- Post-commit: Updates status.json + daily memory indexing

## Documentation

- `CLAUDE.md` - Project-specific workflow guide
- `~/.claude/CLAUDE.md` - Global workflow reference
- `~/.claude/templates/v2.2/` - Agent review templates

## Status

**Workflow**: V2.7.2 (Consolidated)
**Pattern Library**: Active (global patterns available)
**Memory System**: Not activated (can be enabled when needed)
**Test Project**: Ready for validation and experimentation

---

**Version**: V2.7.2
**Created**: 2025-11-09
**Purpose**: V2.7.2 workflow validation and testing
