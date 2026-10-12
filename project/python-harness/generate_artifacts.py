#!/usr/bin/env python3
"""Generate run artifacts for all four systems"""

import sys
from pathlib import Path
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agentic_loop.model import Claim, ClaimType, ClaimPriority
from src.agentic_loop.orchestrator import ClaimProcessor
from src.context_strategy.model import ContentType
from src.context_strategy.orchestrator import ContextOptimizer
from src.orchestration.model import Defect, DefectSeverity, DefectStatus
from src.orchestration.orchestrator import DefectOrchestrator
from src.configuration.orchestrator import ConfigValidator


def generate_agentic_loop_artifacts():
    """Generate artifacts for agentic loop system"""
    print("=" * 70)
    print("Generating Agentic Loop System Artifacts")
    print("=" * 70)

    output_dir = Path("runs/agentic_loop_20261009_120000")
    output_dir.mkdir(parents=True, exist_ok=True)

    processor = ClaimProcessor(output_dir, max_turns=10)

    # Process sample claims
    claims = [
        Claim(
            claim_id="CLM001",
            claim_type=ClaimType.MEDICAL,
            priority=ClaimPriority.MEDIUM,
            description="Routine medical checkup",
            amount=5000
        ),
        Claim(
            claim_id="CLM002",
            claim_type=ClaimType.AUTOMOTIVE,
            priority=ClaimPriority.HIGH,
            description="Major collision damage",
            amount=18000
        ),
        Claim(
            claim_id="CLM003",
            claim_type=ClaimType.LIABILITY,
            priority=ClaimPriority.CRITICAL,
            description="Critical liability incident",
            amount=250000
        ),
    ]

    print(f"\nProcessing {len(claims)} claims...")
    decisions = []

    for claim in claims:
        decision = processor.process_claim(claim)
        decisions.append({
            "claim_id": claim.claim_id,
            "claim_type": claim.claim_type.value,
            "decision": decision.decision,
            "tier": decision.tier,
            "reason": decision.reason
        })
        print(f"  - {claim.claim_id}: {decision.decision} (tier {decision.tier})")

    # Get statistics
    stats = processor.get_statistics()

    # Save summary
    summary = {
        "run_id": "agentic_loop_20261009_120000",
        "timestamp": datetime.now().isoformat(),
        "claims_processed": len(claims),
        "decisions": decisions,
        "statistics": stats
    }

    with open(output_dir / "run_summary.json", 'w') as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"\n✓ Artifacts saved to: {output_dir}")
    print(f"  - {len(list(output_dir.glob('trace_*.json')))} trace files generated")
    print(f"  - Average turns per claim: {stats.get('avg_turns', 0):.1f}")

    return summary


def generate_context_strategy_artifacts():
    """Generate artifacts for context strategy system"""
    print("\n" + "=" * 70)
    print("Generating Context Strategy System Artifacts")
    print("=" * 70)

    output_dir = Path("runs/context_strategy_20261009_120000")
    output_dir.mkdir(parents=True, exist_ok=True)

    optimizer = ContextOptimizer(output_dir)

    # Add realistic context blocks without artificial inflation
    content_blocks = {
        ContentType.MODULE_DOCS: """
        Module Documentation:

        The harness engineering system provides comprehensive claim processing capabilities including
        automated routing, tier classification, and escalation handling. It supports multiple claim
        types (medical, automotive, property, liability, workers compensation) with configurable
        thresholds and business rules.

        Architecture:
        The system follows a clean three-layer architecture:
        - Model Layer: Core data structures, validation logic, and business rules
        - Harness Layer: Execution control, trace management, and artifact generation
        - Orchestration Layer: End-to-end workflow coordination and system integration

        Key Components:
        - AgenticLoopHarness: Manages conversation turns and stop_reason checking
        - ContextStrategyHarness: Handles context optimization and token budgeting
        - ConfigValidator: Validates YAML configuration and Claude Code setup
        - DefectOrchestrator: Manages tiered state (hot/warm/cold) and shift processing

        Design Patterns:
        - Model-Harness-Orchestrator separation ensures testability
        - Pydantic models provide type safety and validation
        - SQLAlchemy enables persistent cold storage
        - JSON files provide lightweight hot-state serialization
        """,

        ContentType.CHANGE_HISTORY: """
        Version History:

        v1.5.0 (2026-10-09):
        - Added support for workers compensation claims
        - Implemented fork_for_hypothesis in orchestration system
        - Enhanced state staleness detection with configurable thresholds

        v1.4.2 (2026-09-15):
        - Fixed routing logic for edge cases in tier determination
        - Improved error handling for invalid claim types
        - Added retry logic for database connection failures

        v1.4.1 (2026-08-22):
        - Performance improvements in SQL query execution
        - Optimized hot-state serialization for large sessions
        - Reduced token overhead in context assembly

        v1.4.0 (2026-07-30):
        - Implemented tiered state management (hot/warm/cold)
        - Added SQL filtering for shift-based defect processing
        - Introduced session forking for isolated investigations

        v1.3.5 (2026-06-18):
        - Enhanced configuration validation with exit codes
        - Added YAML frontmatter support for path-scoped rules
        - Implemented fork context for project-review skill
        """,

        ContentType.CRITICAL_PATHS: """
        Critical Execution Paths:

        1. Claim Processing Flow:
           Claim validation -> Tier determination -> Routing decision
           Priority check -> Escalation logic -> Final decision

        2. State Recovery Flow:
           Session start -> Hot-state check -> Staleness assessment
           If stale: SQL rebuild -> Warm tier loading
           If fresh: Resume from hot-state

        3. Shift Processing Flow:
           SQL filtering -> Defect slicing -> Batch processing
           Priority ordering -> Status updates -> Result aggregation

        4. Configuration Validation:
           YAML parsing -> Frontmatter extraction -> Path pattern matching
           @import resolution -> Skill validation -> Exit code generation
        """,

        ContentType.ERROR_PATTERNS: """
        Common Error Patterns:

        - Stale state detection (>7 days) triggers SQL rebuild from cold storage
        - Invalid claim types raise ValueError with clear error messages
        - Missing configuration files trigger FileNotFoundError
        - Database connection errors handled with exponential backoff retry logic
        - Max tokens exceeded during agentic loop triggers graceful termination
        - Malformed YAML frontmatter logged as warning, uses defaults
        - Fork isolation failures rollback to parent session state
        """
    }

    print("\nAdding context blocks...")
    optimizer.add_raw_context(content_blocks)

    print("Optimizing and evaluating...")
    results = optimizer.optimize_and_evaluate()

    # Print results
    print(f"\n✓ Token Optimization Results:")
    print(f"  - Baseline tokens: {results['budget']['baseline_tokens']:,}")
    print(f"  - Optimized tokens: {results['budget']['optimized_tokens']:,}")
    print(f"  - Reduction: {results['budget']['reduction_percentage']:.1f}%")
    print(f"\n✓ Evaluation Results:")
    print(f"  - Questions answered (full): {results['full_evaluation']['questions_answered']}/6")
    print(f"  - Questions answered (control): {results['control_evaluation']['questions_answered']}/6")
    print(f"  - Regression detected: {results['regression_detected']}")

    # Verify budget.json exists
    budget_file = output_dir / "budget.json"
    print(f"\n✓ Artifacts saved to: {output_dir}")
    print(f"  - budget.json: {budget_file.exists()}")
    print(f"  - evaluation_results.json: {(output_dir / 'evaluation_results.json').exists()}")

    return results


def generate_orchestration_artifacts():
    """Generate artifacts for orchestration system"""
    print("\n" + "=" * 70)
    print("Generating Orchestration System Artifacts")
    print("=" * 70)

    output_dir = Path("runs/orchestration_20261009_120000")
    output_dir.mkdir(parents=True, exist_ok=True)

    orchestrator = DefectOrchestrator("main_session", output_dir)

    # Start session
    hot_state = orchestrator.start_session()
    print(f"\n✓ Session started: {hot_state.session_id}")

    # Process defects
    defects = [
        Defect(
            defect_id="DEF001",
            severity=DefectSeverity.HIGH,
            status=DefectStatus.PENDING,
            description="Critical bug in authentication"
        ),
        Defect(
            defect_id="DEF002",
            severity=DefectSeverity.MEDIUM,
            status=DefectStatus.PENDING,
            description="UI alignment issue"
        ),
        Defect(
            defect_id="DEF003",
            severity=DefectSeverity.LOW,
            status=DefectStatus.PENDING,
            description="Minor typo in documentation"
        ),
    ]

    print(f"\nProcessing {len(defects)} defects...")
    for defect in defects:
        result = orchestrator.process_defect(defect)
        print(f"  - {defect.defect_id}: {defect.severity.value}")

    # Process shift with SQL filtering
    print("\nProcessing shift with SQL filtering (HIGH severity only)...")
    shift_result = orchestrator.process_shift(severity_filter=DefectSeverity.HIGH)
    print(f"  - Defects found: {shift_result['defects_found']}")
    print(f"  - Defects processed: {shift_result['defects_processed']}")
    print(f"  - Used SQL filtering: {shift_result['used_sql_filtering']}")

    # Verify hot-state budget
    budget_check = orchestrator.verify_hot_state_budget()
    print(f"\n✓ Hot-State Budget Check:")
    print(f"  - Size: {budget_check['size_bytes']} bytes")
    print(f"  - Budget: {budget_check['budget_kb']}KB ({budget_check['budget_kb'] * 1024} bytes)")
    print(f"  - Under budget: {budget_check['under_budget']}")

    # Create investigation fork
    fork_result = orchestrator.create_investigation_fork("investigation_001")
    print(f"\n✓ Session Fork Created:")
    print(f"  - Fork ID: {fork_result['fork_id']}")
    print(f"  - Is isolated: {fork_result['is_isolated']}")

    # Get statistics
    stats = orchestrator.get_statistics()

    # Save summary
    summary = {
        "run_id": "orchestration_20261009_120000",
        "timestamp": datetime.now().isoformat(),
        "defects_processed": len(defects),
        "shift_processing": shift_result,
        "hot_state_budget": budget_check,
        "fork_created": fork_result,
        "statistics": stats
    }

    with open(output_dir / "run_summary.json", 'w') as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"\n✓ Artifacts saved to: {output_dir}")
    print(f"  - Hot-state file: {output_dir / f'hot_state_main_session.json'}")
    print(f"  - SQL database: {output_dir / 'defects.db'}")

    return summary


def generate_configuration_artifacts():
    """Generate artifacts for configuration system"""
    print("\n" + "=" * 70)
    print("Generating Configuration System Artifacts")
    print("=" * 70)

    # Use the existing .claude directory
    project_root = Path.cwd()

    validator = ConfigValidator(project_root)
    print("\nRunning configuration validation...")

    result = validator.validate_all()

    print(f"\n{result}")
    print(f"\n✓ Configuration validation completed")

    return {
        "validation_passed": result.passed,
        "exit_code": result.get_exit_code(),
        "errors": len(result.errors),
        "warnings": len(result.warnings)
    }


def main():
    """Generate all artifacts"""
    print("\n" + "=" * 70)
    print("HARNESS ENGINEERING SYSTEMS - ARTIFACT GENERATION")
    print("=" * 70)

    results = {}

    # Generate artifacts for each system
    results['agentic_loop'] = generate_agentic_loop_artifacts()
    results['context_strategy'] = generate_context_strategy_artifacts()
    results['orchestration'] = generate_orchestration_artifacts()
    results['configuration'] = generate_configuration_artifacts()

    # Save master summary
    master_summary = {
        "generated_at": datetime.now().isoformat(),
        "systems": results
    }

    with open("runs/master_summary.json", 'w') as f:
        json.dump(master_summary, f, indent=2, default=str)

    print("\n" + "=" * 70)
    print("✓ ALL ARTIFACTS GENERATED SUCCESSFULLY")
    print("=" * 70)
    print(f"\nSummary saved to: runs/master_summary.json")


if __name__ == '__main__':
    main()
