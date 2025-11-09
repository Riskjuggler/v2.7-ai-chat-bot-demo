# CLAUDE.md - v2.7-test

**Workflow Version**: V2.7.2 (Consolidated)
**Last Updated**: 2025-11-09

This file provides guidance to Claude Code when working in this repository.

> **Global Workflow**: See `~/.claude/CLAUDE.md` for complete workflow rules, agent templates, and multi-project features
> **V2.7.2**: Consolidated project template with all V2.6.2 features + Pattern Library (cross-project learning)

---

## 🎯 Session Start Protocol (CRITICAL)

**At the START of EVERY conversation:**

```bash
cat .claude/status.json
```

**What you get** (~80 lines):
- Current work unit (ID, title, status)
- Agent reviews (count, P0/P1/P2 totals)
- Test health (pass rate, collection errors)
- Memory system status (if active)
- Pattern library status (if active)
- Recent git commit info

**Token savings**: 93% reduction (200 lines vs 2,900 lines)

**When to read more:**
- `p0_total > 0` → Read agent review frontmatter (blocking issues)
- Need work details → Read `.claude/current_work_unit.md`
- Session context → Read `.claude/sessions/quick-resume.md`

---

## 🧠 Memory & Pattern Library

### Memory System (If Active)

**Check status.json to see if enabled:**
- `memory_system.active = true` → Project-specific semantic search

**Query project work units and agent reviews:**
```bash
# Basic query
python3 .claude/scripts/query_memory.py --query "[topic]" --threshold 0.4

# Filter by type
python3 .claude/scripts/query_memory.py --query "P0 issues" --type agent_review

# More results
python3 .claude/scripts/query_memory.py --query "testing" --limit 10
```

**When to query:**
- Creating new work units (check for similar past work)
- Debugging issues (find how similar bugs were fixed)
- User asks "How did we handle X before?"

**What's indexed**: Work units + agent reviews (NOT source code)

**See `~/.claude/CLAUDE.md` for complete memory system documentation.**

### Pattern Library (Active)

**Pattern Library is ACTIVE** - Global patterns from all projects at `~/.claude/patterns/`

**Query global pattern library:**
```bash
# Basic query
python3 .claude/scripts/pattern_query.py --query "[topic]" --threshold 0.6

# Examples
python3 .claude/scripts/pattern_query.py --query "background testing"
python3 .claude/scripts/pattern_query.py --query "API design patterns"
python3 .claude/scripts/pattern_query.py --query "error handling"
```

**When to query patterns:**
- Starting new features (learn from past projects)
- Planning architecture (reference proven patterns)
- Facing a known problem (find established solutions)
- User asks about best practices

**Pattern types:**
- **Architectural**: System design, module structure, data flow
- **Testing**: Test strategies, coverage approaches
- **Workflow**: Process improvements, automation
- **Implementation**: Code patterns, error handling
- **Anti-patterns**: What to avoid, common mistakes

**Pattern vs Memory:**
- **Memory**: "What have WE done in THIS project?"
- **Patterns**: "What have we learned ACROSS ALL projects?"

**Use both together:**
1. Query patterns for proven approaches
2. Query memory for project-specific context
3. Synthesize into implementation plan

**See `~/.claude/CLAUDE.md` for pattern extraction and synthesis documentation.**

---

## 📊 Reading Efficiency Protocol

### Agent Reviews - Read Frontmatter First

```bash
# Read just the frontmatter (first 15 lines)
head -15 .claude/agent-reviews/vision-plan-*.md
```

**Frontmatter shows:**
```yaml
---
agent: vision-alignment
work_unit_id: WU01
p0_count: 0
p1_count: 2
p2_count: 1
status: ALIGNED
---
```

**Decision:**
- `p0_count = 0` → Note status, skip body (savings: 85%)
- `p0_count > 0` → Read full review for details

### Test Results - Read JSON Summary

```bash
cat .claude/logs/test-results.json
```

**JSON shows:**
```json
{
  "tests": 487,
  "passed": 449,
  "failed": 38,
  "pass_rate": 92.2
}
```

**Only read full pytest output when debugging specific failures.**

### Efficiency Summary

| Source | Efficient | Inefficient |
|--------|-----------|-------------|
| Project status | `status.json` (80 lines) | Multiple files (500+ lines) |
| Agent reviews | Frontmatter (70 lines) | Full reviews (1,400+ lines) |
| Test results | JSON (50 lines) | pytest output (1,000+ lines) |

**Total savings**: 93% token reduction

---

## 🔧 Git Hooks Protocol (STRICT)

### NEVER Use --no-verify

**When hooks report errors:**

❌ **NEVER:**
```bash
git commit --no-verify -m "message"  # Bypasses validation
```

✅ **ALWAYS:**
```bash
# 1. Read error message
# 2. Fix the error
# 3. Re-commit normally
git commit -m "message"
```

### Valid --no-verify Uses (RARE)

**ONLY when:**
1. Modifying hook scripts themselves (can't self-validate)
2. Emergency hotfix with explicit user approval

**Hook types:**
- **Pre-commit**: Fast validation (<200ms) - syntax, secrets, work unit structure
- **Post-commit**: Background updates - status.json, test execution, memory indexing

### Error Handling

**Syntax error:**
```bash
# Hook: "SyntaxError in file.py line 42"
# Action: Fix syntax at line 42, re-commit
```

**Secret detected:**
```bash
# Hook: "Potential secret detected"
# Action: Remove secret OR user confirms false positive
```

**Work unit validation failed:**
```bash
# Hook: "Work unit frontmatter invalid"
# Action: Fix frontmatter format, re-commit
```

**Tests fail (post-commit, non-blocking):**
```bash
# Action: Commit succeeded, read test-results.json, fix in next commit
```

---

## 🏗️ Test Health Monitoring (V2.6.1+)

**status.json includes test health:**
```json
{
  "test_health": {
    "collection_errors": 0,
    "tests_collected": 487,
    "pass_rate": 92.2
  }
}
```

**Thresholds:**
- `collection_errors > 0` → P0 (test suite broken)
- `pass_rate < 90%` → Investigate
- `pass_rate < 80%` → Stop feature work, fix tests

**Check at session start:**
```bash
cat .claude/status.json | grep -A 7 "test_health"
```

**Benefit**: See test health without running tests (95% token savings)

---

## 📋 Work Unit Workflow (When Using Work Units)

### Creating Work Units

**1. Create work unit:**
```bash
vim .claude/work-units/WU01.md
```

**2. Run agent reviews (if using seven-agent workflow):**
- Launch 6 specialists in parallel: Vision, Scope, Design, Simplicity, Testing, Validation
- Launch Tattle-Tale after all 6 complete
- See `~/.claude/CLAUDE.md` for agent templates and review sequence

**3. Read frontmatter (70 lines total):**
```bash
head -15 .claude/agent-reviews/*-plan-*.md
```

**4. Check for P0 issues:**
- If P0 > 0: Read full reviews, address issues
- If P0 = 0: Proceed to implementation

**5. Implement and commit:**
```bash
git add .
git commit -m "[WU01] Feature description"
# Hooks validate automatically
```

### Sprint Orchestration (Multi-Work-Unit Projects)

**For projects with 5+ work units:**
```bash
# Create sprint plan
vim .claude/planning/sprint-plan.yaml

# Execute sprint (via slash command, not Task tool)
/orchestrate .claude/planning/sprint-plan.yaml
```

**What orchestration does:**
1. Groups work units by dependencies
2. Executes independent work in parallel
3. Runs retrospectives after each sprint
4. Enforces quality gates (P0 blocking)

**See `~/.claude/CLAUDE.md` V2.4.2 section for complete sprint orchestration documentation.**

---

## 📁 Project-Specific Configuration

### Project Overview

**Purpose**: Testing and validation environment for V2.7.2 workflow features

**Key Principles**:
- Test V2.7.2 consolidated templates
- Verify Pattern Library integration
- Validate Memory System functionality
- Demonstrate daily memory indexing

### Architecture

V2.7.2 test project with full workflow infrastructure for validation and experimentation.

### Common Commands

**Development:**
```bash
# Run tests
pytest tests/ -v

# Format code
black .

# Lint
ruff check .
```

**Testing:**
```bash
# Unit tests only
pytest -m unit

# Integration tests
pytest -m integration

# With coverage
pytest --cov=src --cov-report=term-missing
```

### Key Files

**Always read (small, essential):**
- `.claude/status.json` - Complete project status
- `.claude/logs/test-results.json` - Test summary
- `.claude/agent-reviews/*-plan-*.md` (frontmatter) - Review summaries

**Read when needed:**
- `.claude/current_work_unit.md` - Current work details
- `.claude/sessions/quick-resume.md` - Session context
- Full agent reviews (only if P0 > 0)

**Configuration:**
- `pyproject.toml` - Tool configuration
- `pytest.ini` - Test discovery (REQUIRED if tests in .claude/tests/)
- `.claude/config/*.yaml` - Workflow configuration

---

## 🎯 Quick Reference

**Session start:**
```bash
cat .claude/status.json
```

**Query memory (if active):**
```bash
python3 .claude/scripts/query_memory.py --query "[topic]"
```

**Query patterns (active):**
```bash
python3 .claude/scripts/pattern_query.py --query "[topic]"
```

**Commit:**
```bash
git add .
git commit -m "message"
# NEVER add --no-verify unless explicitly required
```

---

## ✅ Four Critical Rules

1. **Read status.json first** (93% token savings)
2. **NEVER use --no-verify** (bypasses validation)
3. **Read frontmatter/JSON summaries** (not full logs/reviews)
4. **Query patterns before memory** (cross-project → project-specific)

Follow these rules for fast, efficient, maintainable workflow.

---

## 📖 Additional Documentation

**Workflow:**
- `~/.claude/CLAUDE.md` - Complete workflow reference

**Templates:**
- `~/.claude/templates/v2.2/` - Agent review templates (V2.6.2+)

**Analysis:**
- `.claude/analysis/` - Analysis documents
- `.claude/analysis/summaries/` - Delivery reports

**Patterns:**
- `~/.claude/patterns/` - Global pattern library (cross-project)

---

**Template Version**: V2.7.2
**Token Budget**: ~5,000 tokens (vs 58,000 old way)
**Features**: All V2.6.2 capabilities + Pattern Library (cross-project learning)
