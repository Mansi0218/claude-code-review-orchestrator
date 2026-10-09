#!/bin/bash
# Verification Script for Python Harness Engineering Systems
# Run this to verify all rubric requirements are met

set -e  # Exit on error

echo "================================================================"
echo "HARNESS ENGINEERING SYSTEMS - VERIFICATION SCRIPT"
echo "================================================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Change to project directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Working directory: $SCRIPT_DIR"
echo ""

# Function to check file exists
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1 exists"
        return 0
    else
        echo -e "${RED}✗${NC} $1 MISSING"
        return 1
    fi
}

# Function to check directory exists
check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $1/ exists"
        return 0
    else
        echo -e "${RED}✗${NC} $1/ MISSING"
        return 1
    fi
}

echo "================================================================"
echo "1. CHECKING PROJECT STRUCTURE"
echo "================================================================"

check_dir "src/agentic_loop"
check_dir "src/context_strategy"
check_dir "src/configuration"
check_dir "src/orchestration"
check_dir "tests"
check_dir "output"
check_dir "runs"
check_dir ".claude"

echo ""

echo "================================================================"
echo "2. CHECKING SOURCE FILES (Model/Harness/Orchestration)"
echo "================================================================"

# Agentic Loop
check_file "src/agentic_loop/model.py"
check_file "src/agentic_loop/harness.py"
check_file "src/agentic_loop/orchestrator.py"

# Context Strategy
check_file "src/context_strategy/model.py"
check_file "src/context_strategy/harness.py"
check_file "src/context_strategy/orchestrator.py"

# Configuration
check_file "src/configuration/model.py"
check_file "src/configuration/harness.py"
check_file "src/configuration/orchestrator.py"

# Orchestration
check_file "src/orchestration/model.py"
check_file "src/orchestration/harness.py"
check_file "src/orchestration/orchestrator.py"

echo ""

echo "================================================================"
echo "3. CHECKING TEST FILES"
echo "================================================================"

check_file "tests/test_agentic_loop.py"
check_file "tests/test_context_strategy.py"
check_file "tests/test_configuration.py"
check_file "tests/test_orchestration.py"

echo ""

echo "================================================================"
echo "4. CHECKING TEST OUTPUTS"
echo "================================================================"

check_file "output/agentic_loop_tests.txt"
check_file "output/context_strategy_tests.txt"
check_file "output/configuration_tests.txt"
check_file "output/orchestration_tests.txt"

echo ""

echo "================================================================"
echo "5. CHECKING RUN ARTIFACTS"
echo "================================================================"

# Count trace files
TRACE_COUNT=$(find runs/agentic_loop_* -name "trace_*.json" 2>/dev/null | wc -l)
if [ "$TRACE_COUNT" -ge 1 ]; then
    echo -e "${GREEN}✓${NC} Found $TRACE_COUNT trace file(s) in agentic_loop runs"
else
    echo -e "${RED}✗${NC} No trace files found"
fi

# Check budget.json
if [ -f runs/context_strategy_*/budget.json ]; then
    REDUCTION=$(grep -o '"reduction_percentage": [0-9.]*' runs/context_strategy_*/budget.json | head -1 | awk '{print $2}')
    if (( $(echo "$REDUCTION > 50" | bc -l) )); then
        echo -e "${GREEN}✓${NC} budget.json exists with ${REDUCTION}% reduction (>50% required)"
    else
        echo -e "${YELLOW}⚠${NC} budget.json reduction is ${REDUCTION}% (should be >50%)"
    fi
else
    echo -e "${RED}✗${NC} budget.json not found"
fi

# Check hot-state file
HOT_STATE=$(find runs/orchestration_* -name "hot_state_*.json" 2>/dev/null | head -1)
if [ -n "$HOT_STATE" ]; then
    SIZE=$(stat -f%z "$HOT_STATE" 2>/dev/null || stat -c%s "$HOT_STATE" 2>/dev/null)
    if [ "$SIZE" -lt 5120 ]; then
        echo -e "${GREEN}✓${NC} Hot-state file exists: $SIZE bytes (<5KB required)"
    else
        echo -e "${YELLOW}⚠${NC} Hot-state file is $SIZE bytes (should be <5120)"
    fi
else
    echo -e "${RED}✗${NC} Hot-state file not found"
fi

# Check SQL database
if [ -f runs/orchestration_*/defects.db ]; then
    echo -e "${GREEN}✓${NC} SQL database (defects.db) exists"
else
    echo -e "${RED}✗${NC} SQL database not found"
fi

echo ""

echo "================================================================"
echo "6. CHECKING CONFIGURATION FILES"
echo "================================================================"

check_file ".claude/CLAUDE.md"
check_file ".claude/standards/api.md"
check_file ".claude/standards/testing.md"
check_file ".claude/standards/security.md"
check_file ".claude/rules/python-style.md"
check_file ".claude/skills/project-review/SKILL.md"

# Check for @path imports in CLAUDE.md
if grep -q "@.claude/standards" .claude/CLAUDE.md; then
    echo -e "${GREEN}✓${NC} CLAUDE.md contains @path imports"
else
    echo -e "${YELLOW}⚠${NC} CLAUDE.md may be missing @path imports"
fi

# Check for YAML frontmatter in rules
if grep -q "^---$" .claude/rules/python-style.md; then
    echo -e "${GREEN}✓${NC} python-style.md has YAML frontmatter"
else
    echo -e "${YELLOW}⚠${NC} python-style.md may be missing YAML frontmatter"
fi

# Check for fork context in skill
if grep -q "context: fork" .claude/skills/project-review/SKILL.md; then
    echo -e "${GREEN}✓${NC} project-review skill has fork context"
else
    echo -e "${YELLOW}⚠${NC} project-review skill may be missing fork context"
fi

echo ""

echo "================================================================"
echo "7. CHECKING DOCUMENTATION"
echo "================================================================"

check_file "REFLECTION.md"
check_file "README.md"
check_file "requirements.txt"
check_file "pytest.ini"

# Check REFLECTION.md length
REFLECTION_LINES=$(wc -l < REFLECTION.md)
if [ "$REFLECTION_LINES" -gt 300 ]; then
    echo -e "${GREEN}✓${NC} REFLECTION.md is comprehensive ($REFLECTION_LINES lines)"
else
    echo -e "${YELLOW}⚠${NC} REFLECTION.md may be too short ($REFLECTION_LINES lines)"
fi

echo ""

echo "================================================================"
echo "8. RUNNING PYTEST (Quick Check)"
echo "================================================================"

if command -v pytest &> /dev/null; then
    echo "Running pytest to count tests..."
    export PYTHONPATH=.

    # Count tests without running them
    TOTAL_TESTS=$(pytest --collect-only -q tests/ 2>/dev/null | grep "test session starts" -A 100 | grep "selected" | awk '{print $1}' || echo "0")

    if [ "$TOTAL_TESTS" -ge 128 ]; then
        echo -e "${GREEN}✓${NC} Found $TOTAL_TESTS tests (≥128 required)"
    elif [ "$TOTAL_TESTS" -gt 0 ]; then
        echo -e "${YELLOW}⚠${NC} Found $TOTAL_TESTS tests (128 required)"
    else
        echo -e "${YELLOW}⚠${NC} Could not count tests automatically"
    fi

    echo ""
    echo "To run full test suite:"
    echo "  PYTHONPATH=. pytest tests/ -v"
else
    echo -e "${YELLOW}⚠${NC} pytest not found. Install with: pip install -r requirements.txt"
fi

echo ""

echo "================================================================"
echo "9. KEY METRICS SUMMARY"
echo "================================================================"

echo "Test Files:"
echo "  - test_agentic_loop.py: $(grep -c "^def test_" tests/test_agentic_loop.py 2>/dev/null || echo 0) tests"
echo "  - test_context_strategy.py: $(grep -c "^def test_" tests/test_context_strategy.py 2>/dev/null || echo 0) tests"
echo "  - test_configuration.py: $(grep -c "^def test_" tests/test_configuration.py 2>/dev/null || echo 0) tests"
echo "  - test_orchestration.py: $(grep -c "^def test_" tests/test_orchestration.py 2>/dev/null || echo 0) tests"

echo ""
echo "Artifacts:"
echo "  - Agentic Loop runs: $(ls -d runs/agentic_loop_* 2>/dev/null | wc -l)"
echo "  - Context Strategy runs: $(ls -d runs/context_strategy_* 2>/dev/null | wc -l)"
echo "  - Orchestration runs: $(ls -d runs/orchestration_* 2>/dev/null | wc -l)"

echo ""

echo "================================================================"
echo "VERIFICATION COMPLETE"
echo "================================================================"
echo ""
echo "Next steps:"
echo "1. Run full test suite: PYTHONPATH=. pytest tests/ -v"
echo "2. Review REFLECTION.md for evidence-based analysis"
echo "3. Check runs/ directory for artifacts"
echo "4. Verify .claude/ configuration files"
echo ""
echo "For detailed rubric compliance, see README.md"
echo "================================================================"
