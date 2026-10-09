# Harness Engineering Systems - Python Implementation

Four Python-based harness engineering systems with comprehensive test coverage and evidence-based architecture.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
PYTHONPATH=. pytest tests/ -v

# Run specific system tests
PYTHONPATH=. pytest tests/test_configuration.py -v
PYTHONPATH=. pytest tests/test_agentic_loop.py -v
PYTHONPATH=. pytest tests/test_context_strategy.py -v
PYTHONPATH=. pytest tests/test_orchestration.py -v

# Generate artifacts
PYTHONPATH=. python generate_artifacts.py
```

## Project Structure

```
python-harness/
├── src/
│   ├── agentic_loop/          # Stop_reason-driven claim processing (30 tests)
│   ├── context_strategy/      # Token optimization (30 tests)
│   ├── configuration/         # YAML validation (35 tests)
│   └── orchestration/         # Tiered state management (33 tests)
├── tests/
│   ├── test_agentic_loop.py
│   ├── test_context_strategy.py
│   ├── test_configuration.py
│   └── test_orchestration.py
├── .claude/
│   ├── CLAUDE.md              # Main configuration with @path imports
│   ├── standards/             # Modular standards (api, testing, security)
│   ├── rules/                 # Path-scoped rules with YAML frontmatter
│   └── skills/                # Project-review skill with fork context
├── output/                    # Pytest test outputs
├── runs/                      # Run artifacts and demonstrations
├── REFLECTION.md              # Evidence-based architectural analysis
└── generate_artifacts.py      # Artifact generation script
```

## Four Systems

### 1. Configuration System (35 tests)
- YAML frontmatter parsing and validation
- Glob pattern validation
- Import path resolution
- Skill configuration with fork context
- **Key files**: `src/configuration/{model,harness,orchestrator}.py`

### 2. Agentic Loop System (30 tests)
- Stop_reason-driven execution (tool_use vs end_turn)
- Claim routing with tier classification
- Turn-by-turn conversation traces
- Anti-pattern: max_turns prevents infinite loops
- **Key files**: `src/agentic_loop/{model,harness,orchestrator}.py`

### 3. Context Strategy System (30 tests)
- Token optimization (73.2% reduction achieved)
- Selective summarization vs preservation
- Evaluation framework (6 questions)
- Control variant regression detection
- **Key files**: `src/context_strategy/{model,harness,orchestrator}.py`

### 4. Orchestration System (33 tests)
- Tiered state: hot-state JSON (<5KB) + cold-state SQL
- Crash recovery (resume vs rebuild from SQL)
- 7-day staleness threshold
- SQL filtering for defect slicing
- Session forking with isolation
- **Key files**: `src/orchestration/{model,harness,orchestrator}.py`

## Test Results

| System | Tests | Passing | Pass Rate |
|--------|-------|---------|-----------|
| Configuration | 35 | 31 | 89% |
| Agentic Loop | 31 | 31 | 100% |
| Context Strategy | 29 | 26 | 90% |
| Orchestration | 33 | 32 | 97% |
| **Total** | **128** | **120** | **94%** |

**Test outputs**: See `output/` directory for detailed pytest logs

## Key Achievements

✅ **Token Optimization**: 73.2% reduction (7,475 → 2,003 tokens)
✅ **Hot-State Budget**: 170 bytes (3.3% of 5KB limit)
✅ **Evaluation**: 6/6 questions answered (control: 4/6, regression detected)
✅ **SQL Filtering**: 1 HIGH-severity defect processed in shift
✅ **Fork Isolation**: Verified via separate session IDs
✅ **Crash Recovery**: Staleness threshold enforced (7 days)

## Run Artifacts

Generated artifacts demonstrate each system:

```bash
runs/
├── agentic_loop_20261009_120000/
│   ├── trace_CLM001_*.json       # Turn-by-turn traces
│   ├── trace_CLM002_*.json
│   ├── trace_CLM003_*.json
│   └── run_summary.json
├── context_strategy_20261009_120000/
│   ├── budget.json               # 73.2% token reduction
│   └── evaluation_results.json   # 6/6 questions answered
├── orchestration_20261009_120000/
│   ├── hot_state_main_session.json  # 170 bytes
│   ├── defects.db                   # SQL cold-state
│   └── run_summary.json
└── master_summary.json
```

## Architecture

All systems follow **Model/Harness/Orchestration** three-tier architecture:

- **Model**: Core data structures, business logic, decision algorithms
- **Harness**: Execution context, file I/O, state management
- **Orchestration**: End-to-end workflow coordination

See `REFLECTION.md` Section 1 for detailed layer mapping with file:line citations.

## Configuration

The `.claude/` directory contains:

- **CLAUDE.md**: Main config with modular standard imports
- **Standards**: API conventions, testing practices, security requirements
- **Rules**: Python style rules with YAML frontmatter and glob patterns
- **Skills**: Project-review skill with fork context and read-only tools

## Documentation

- **REFLECTION.md**: Comprehensive analysis with 50+ evidence citations
  - Model/Harness/Orchestration layer mapping
  - Deterministic vs prompt-based enforcement comparison
  - Context management strategies
  - Test suite insights and anti-patterns avoided
  - Crash recovery and fork isolation

## Requirements Met

✅ 128 pytest tests (120 passing, 94%)
✅ Four Python systems with clear architecture
✅ Pytest outputs for all systems
✅ Budget.json with 73.2% reduction
✅ Hot-state <5KB (170 bytes actual)
✅ CLAUDE.md with @path imports
✅ Path-scoped rules with YAML frontmatter
✅ Forked skill with read-only tools
✅ Evidence-based REFLECTION.md
✅ Run artifacts demonstrating all systems

## License

Educational project for harness engineering course.
