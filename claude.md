In this capstone, you build, run, and verify the four systems from this course, then write a reflection brief that defends each system's design.

You receive complete reference implementations with full test suites. You do not write code. You:

Stand each system up
Run it against its fixtures
Run its tests
Capture what it produces
Explain why it is built that way
The reflection brief's questions require citing your own run output, so generic answers will not pass.

The Four Systems
Agentic loop — processes intake conversations, calls tools to gather and classify, routes or escalates each case. Control flow driven by stop_reason.

Context strategy — compresses a long, multi-issue conversation to under half its tokens while still answering evaluation questions.

Claude Code config — a CLAUDE.md hierarchy, path-scoped rules, a custom slash command, and a forked-context skill, checked by a validator.

Layer 3 orchestrator — runs as a fresh session per shift, keeps state tiny through tiered storage and SQL pre-filtering, recovers from crashes, supports forked investigations.

Learning Objectives
By the end of this project, you will be able to:

Operate a stop_reason-driven agentic loop and identify its termination logic and the anti-patterns it avoids
Engineer a position-aware context strategy that cuts token load while preserving answerability
Configure a Claude Code harness with a CLAUDE.md hierarchy, path-scoped rules, commands, and a forked-context skill
Implement Layer 3 orchestration with tiered state, crash recovery, and session forking
Verify each system against its test suite and explain what the tests guarantee
Defend architectural trade-offs in an evidence-grounded reflection brief
Deliverables
Evidence — passing test output for all four systems (30 + 30 + 35 + 33) and the key run artifact from each, one folder per system
Reflection brief — the reflection-brief-template.md, completed, every answer citing your own run artifacts
Resources
Capstone materials (Project-Harness Engineering with Claude and Claude Code/) — README.md and reflection-brief-template.md
The four systems — each is the final-exercise solution/ of its course project: Build a Claims Intake Agent with a stop_reason-Driven Loop/exercises/03-dynamic-decomposition/solution/, Engineer a Long-Conversation Context Strategy for a Retail Support Copilot/04-assemble-and-locate/solution/, Configure Claude Code for a Multi-Surface Monorepo Team/04-plan-mode-and-explore-decision-doc/solution/, and Build a Multi-Shift Quality Monitoring System with Claude Orchestration/04-fork-scratchpad/solution/. Each project has its own README.md.
Claude API key (ANTHROPIC_API_KEY) — required for three of the four systems. Setup is on the next page.

Prerequisites
Python 3.11+ — check with python --version
A Claude API key — required for three of the four systems:
export ANTHROPIC_API_KEY="voc-your-key-here"
# Using the Udacity-provided (Vocareum) key? Also point the SDK at the # proxy. The system code reads this automatically — no code edits needed:
export ANTHROPIC_BASE_URL="https://claude.vocareum.com"
If you set ANTHROPIC_API_KEY but skip ANTHROPIC_BASE_URL, a voc- key is sent to api.anthropic.com and fails with a 401. See Lesson 1 → "Accessing and Using the Claude API Vocareum Key" for full details.

git and a terminal (macOS, Linux, or Windows with WSL)
⚠️ Running all four systems against the live API costs about $1–$5 total on the default models. The orchestrator can run fully offline with a recorded response. The Claude Code config system needs no key.

Two systems pin different anthropic versions (0.39.0 and 0.69.0). Use a separate virtual environment per system.

Project Files
/workspace/
├── Build a Claims Intake Agent with a stop_reason-Driven Loop/   # System 1 → exercises/03-dynamic-decomposition/solution/
├── Engineer a Long-Conversation Context Strategy for a Retail Support Copilot/   # System 2 → 04-assemble-and-locate/solution/
├── Configure Claude Code for a Multi-Surface Monorepo Team/   # System 3 → 04-plan-mode-and-explore-decision-doc/solution/
├── Build a Multi-Shift Quality Monitoring System with Claude Orchestration/   # System 4 → 04-fork-scratchpad/solution/
└── Project-Harness Engineering with Claude and Claude Code/   # README + reflection-brief-template.md
Each system is the complete reference implementation in that project's final-exercise solution/ folder, the four paths shown above. Earlier exercises' folders hold intermediate code; work only in these four. You do not edit them. What you produce: evidence artifacts (run output, test logs) and your completed brief, copied from Project-Harness Engineering with Claude and Claude Code/reflection-brief-template.md.

Setup Steps
Same pattern for each system: enter the directory, create a venv, install with dev dependencies, run the tests.

# repeat for each of the four system directories
cd <system-directory>
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/ -v
deactivate
Expected: 30 (System 1), 30 (System 2), 35 (System 3), 33 (System 4) tests. System 2 reports 28 passed, 2 skipped until it has run once: its last two tests read the run's output. You re-run them in Task 3.

On Windows without WSL, activate with .venv\Scripts\activate.

Verify Your Setup
From inside each system, with its venv active:

python -c "import sys; print(sys.version)"   # 3.11+
pytest tests/ -q                              # all pass
For the three API systems, confirm the key — and, for the Vocareum key, the base URL — are visible:

python -c "import os; print('key set:', bool(os.environ.get('ANTHROPIC_API_KEY')), '| base_url:', os.environ.get('ANTHROPIC_BASE_URL'))"
Four passing suites and a set key (with the base URL, if you are on the Vocareum key) means you are ready.

Project Instructions
Work through the tasks in order. Task 1 gets all four environments healthy. Tasks 2–5 run each system and capture its evidence. Tasks 6–7 organize the evidence and complete the brief.

Every task maps to a rubric criterion. Keep every terminal log and run artifact — you submit them.

Task List
 
Complete these in order. Tasks 2-5 each produce an evidence artifact; task 7 produces your brief.
 
Build and verify all four environments: create a venv, run pip install -e ".[dev]", and pytest tests/ -v in each repo. Save the passing output (30+30+35+33; System 2 shows 28 passed, 2 skipped until Task 3). Document any environment failure you hit and fix.
 
Run the agentic loop: python -m claims_intake.run --all. Capture summary.md and one trace from runs/<timestamp>/. Confirm each claim routes or escalates, and the trace shows stop_reason continuing on tool_use and stopping on end_turn.
 
Run the context strategy: python -m retail_context.run-all. Capture from runs/<run_id>/: budget.json (250% reduction), eval.jsonl, and eval_control.jsonl. Note which question regresses in the control. Then re-run pytest tests/-v and save that log as System 2's test evidence (30 passed).
 
Validate the Claude Code config: python -m ecommerce_team_config. (expect OK). Capture the output and the .claude/ structure glob frontmatter in the rules, the /review command, and the skill's context: fork and allowed-tools lines.
 
Run the orchestrator. First seed the warm tier once:
 
python -c "import json; from pathlib import Path; from shift_monitor.warm import WarmStore; w-WarmStore(Path('data/warm.sqlite')); w.initialize(); w.insert_many(json.load(open('fixtures/defects.json')))" . Then run
 
python -m shift_monitor run-shift-shift C-warm-db data/warm.sqlite-since 2026-04-01T00:00:00Z --recorded-response fixtures/recorded_responses/shift_C_2026-04-30.json
 
. Capture the shift output, the byte size of data/hot_state.json, and the defects returned vs the warm-tier total (expect 17 of 40).
 
Organize evidence into one folder per system, each with its test log and key artifact(s).
 
Complete the brief: copy reflection-brief-template.md and answer every prompt, citing at least one of your own run artifacts per answer. Uncited answers do not meet the standard.
 
 Verify Your Implementation
Run each scenario and confirm the output before submitting.

Tests pass

pytest tests/ -v # run inside each system's own venv → 30, 30, 35, 33
Agentic loop — python -m claims_intake.run --all → runs/<ts>/ with summary.md, traces/, queues/*.jsonl, escalations.jsonl; exit 0.

Context strategy — python -m retail_context.run --all → budget.json ≥50% reduction; eval.jsonl ≥5/6; control regresses on ≥1.

Claude Code config — python -m ecommerce_team_config . → OK, exit 0.

Orchestrated shift — run-shift … --since 2026-04-01T00:00:00Z --recorded-response … → shift C: 17 new defects, summary prints; hot_state.json updates, under ~5 KB; a line appends to shift_scratchpad.jsonl.

Writing the Brief
Two rules separate a passing brief from a generic one:

Cite your own artifacts. Every answer references something only your runs produced — a run ID, a token count from budget.json, a claim outcome from summary.md, the size of hot_state.json, a trace line. An answer identical for every learner does not pass.
Synthesize across systems. Part 2 asks you to connect two or more systems: locate the three layers, contrast deterministic enforcement with prompt guidance, compare context management within one conversation vs across sessions.
Submission Instructions
Confirm you have included:
Passing test output for all four systems (30+30+35+ 33), each identifiable to its system
 
System 1: summary.md + one trace showing per-turn stop_reason
 
System 2: budget.json, eval.jsonl, eval_control.jsonl
 
System 3: validator OK output + the .claude/ structure
 
System 4: shift output + hot_state.json size
 
Evidence in one folder per system.
 
Completed reflection-brief-template.md, every answer citing a run artifact
 
Package the four evidence folders (system1/tosystem4/) and the brief at the top level of one .zip, with no wrapper folder, and submit.

How It's Evaluated
Your reviewer checks two things: that the evidence shows all four systems built, run, and passing tests; and that the brief is accurate and grounded in that evidence. Cited numbers are cross-checked against your artifacts.

Valid runs vary — token counts, turns, and outcomes differ by model and input. There is no single correct set of numbers. What matters is that your analysis fits the behavior your runs produced. See the project rubric in the classroom for full criteria and stand-out suggestions.

Use this project rubric to understand and assess the project criteria.

Building the Projects
Criteria	Submission Requirements
Operate a stop_reason-driven agentic loop with integrated tools

Test output shows the agentic-loop system's suite passing (30 tests).
A run artifact shows claims processed end-to-end, each terminating in either a routing decision or an escalation.
At least one submitted trace shows turn-by-turn stop_reason values, with the loop continuing on tool_use and terminating on end_turn.
The reflection brief identifies, by file and function, where loop termination is decided, and names one anti-pattern the loop avoids.
Implement Layer 3 orchestration with tiered state, crash recovery, and session forking

Test output shows the orchestration system's suite passing (33 tests).
A run artifact shows a shift processed using a SQL-filtered slice of defects rather than the full history.
Submitted evidence shows the hot-state file remaining within its size budget (under ~5 KB) after a run.
The reflection brief explains the resume-vs-fresh recovery decision and the staleness threshold that drives it, and explains how a forked investigation stays isolated from the main state.
Engineer a context strategy that reduces token load while preserving answerability

Test output shows the context-strategy system's suite passing (30 tests).
A budget.json artifact shows the assembled context is at least 50% smaller than the raw baseline.
Evaluation results show the assembled context answers at least 5 of 6 evaluation questions.
The control-variant results (with the Case Facts block removed) show at least one question regressing relative to the full run.
The reflection brief explains which information was summarized, which was preserved verbatim, and why, citing the learner's own token numbers.
Criteria: Configure a Claude Code harness with hierarchy, path-scoped rules, commands, and skills

The configuration validator runs and reports a passing result (OK, exit code 0).
Test output shows the configuration system's suite passing (35 tests).
Submitted evidence shows a CLAUDE.md that imports modular standards with @pathreferences (for example@.claude(opens in a new tab)/standards/api.md).
Submitted evidence shows path-scoped rule files whose YAML frontmatter declares glob patterns, a project-scoped slash command, and a skill configured with context: fork and a read-only allowed-tools set.
The reflection brief explains why a path-scoped rule is preferred over a directory-level CLAUDE.md for conventions that span the codebase, and why the skill runs in a forked context.
Verification
Criteria	Submission Requirements
Verify each project against its automated test suite

Passing pytest output is submitted for all four systems (30 + 30 + 35 + 33 tests).
Each test log is identifiable to its system (file path or header visible).
The reflection brief names one behavior that a test suite guarantees which manual inspection of a single run would not reveal.
Reflection & Synthesis
Criteria	Submission Requirements
Defend architectural trade-offs in an evidence-grounded reflection brief

Every reflection answer cites at least one concrete artifact from the learner's own runs (a run ID, file path, token count, test count, or claim outcome).
The cross-project synthesis locates each of the three layers (Model, Harness, Orchestration) in a named file from at least one of the four systems.
The brief contrasts deterministic enforcement with prompt-based guidance, citing one example of each from the projects built.
The brief compares how context management appears in the context-strategy system versus the orchestration system, with cited numbers from both.
Suggestions to Make Your Project Stand Out
Run the same system on two models. Re-run projec 1 with --model claude-sonnet-4-6 and compare turn counts, escalation rates, and cost against the Haiku baseline. Note where the stronger model changes routing behavior.
Break a system on purpose. Temporarily strip the case-facts block in System 2, or feed System 1 a deliberately ambiguous claim, and document how the system degrades. Understanding failure modes is core to architecture.
Exercise the fork path end-to-end. In System 4, fork the state to investigate two competing hypotheses about a defect cluster, then show both forks' scratchpads stayed isolated from the main stream.
Map a system to a new use case. Pick a real-world product scenario you know and write a short note on which of the four systems you would reuse to implement it and why.
Personalize it. Re-frame one system for an industry vertical you actually work in, and describe in the brief what would change about the tool set, the context strategy, or the state design.


































