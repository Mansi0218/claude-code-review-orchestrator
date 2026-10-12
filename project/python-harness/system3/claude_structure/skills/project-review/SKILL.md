---
name: project-review
description: Review harness engineering systems for completeness and correctness
context: fork
allowed_tools:
  - Read
  - Grep
  - Glob
---

# Project Review Skill

This skill provides systematic review of harness engineering projects.

## Purpose

Review projects against rubric requirements:
- Test coverage (128 tests across 4 systems)
- Artifact generation (pytest outputs, budget.json, state files)
- Documentation (REFLECTION.md with evidence citations)

## Usage

Invoke this skill to:
1. Verify all four systems are implemented
2. Check test counts match requirements
3. Validate artifact generation
4. Review reflection documentation

## Fork Context

Runs in isolated fork context with read-only tools for safety:
- **Read**: Access source files and test outputs
- **Grep**: Search for specific patterns
- **Glob**: Find files matching patterns

Changes in this skill's execution do not affect the main project state.

## Review Checklist

- [ ] Configuration System: 35 tests
- [ ] Agentic Loop System: 30 tests
- [ ] Context Strategy System: 30 tests
- [ ] Orchestration System: 33 tests
- [ ] Pytest outputs generated
- [ ] Budget.json shows 50%+ reduction
- [ ] Hot-state files <5KB
- [ ] REFLECTION.md with citations
