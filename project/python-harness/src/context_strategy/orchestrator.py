"""Context Strategy System - Orchestration Layer

End-to-end context optimization workflow and evaluation.
Located at: src/context_strategy/orchestrator.py:23-67
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from .model import ContentType, EvaluationQuestion, TokenBudget
from .harness import ContextStrategyHarness


class ContextOptimizer:
    """
    Orchestration layer for context optimization

    Coordinates context assembly, optimization, and evaluation.
    Located at: src/context_strategy/orchestrator.py:23-67
    """

    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize optimizer"""
        self.harness = ContextStrategyHarness(output_dir)
        self.evaluation_questions = self._create_evaluation_questions()

    def _create_evaluation_questions(self) -> List[EvaluationQuestion]:
        """
        Create standard set of 6 evaluation questions

        Questions test answerability with optimized context.
        """
        return [
            EvaluationQuestion(
                question_id="Q1",
                question="What are the critical execution paths in the system?",
                requires_preserved=True
            ),
            EvaluationQuestion(
                question_id="Q2",
                question="What common error patterns should be monitored?",
                requires_preserved=True
            ),
            EvaluationQuestion(
                question_id="Q3",
                question="Summarize the recent change history",
                requires_preserved=False
            ),
            EvaluationQuestion(
                question_id="Q4",
                question="What modules are documented?",
                requires_preserved=False
            ),
            EvaluationQuestion(
                question_id="Q5",
                question="Describe the API reference structure",
                requires_preserved=False
            ),
            EvaluationQuestion(
                question_id="Q6",
                question="What is the test coverage status?",
                requires_preserved=False
            )
        ]

    def add_raw_context(self, content_blocks: Dict[ContentType, str]):
        """
        Add raw context blocks to be optimized

        Args:
            content_blocks: Dict mapping ContentType to content string
        """
        for content_type, content in content_blocks.items():
            self.harness.add_context_block(content_type, content)

    def optimize_and_evaluate(self) -> Dict[str, Any]:
        """
        Run complete optimization and evaluation workflow

        Returns:
            Dict with budget, evaluation results, and control comparison
        """
        # Calculate budget
        budget = self.harness.calculate_budget()

        # Save budget
        self.harness.save_budget(budget)

        # Run full evaluation
        full_results = self.harness.run_evaluation(
            self.evaluation_questions,
            variant="full"
        )

        # Run control evaluation (without persistent facts)
        control_results = self.harness.run_evaluation(
            self.evaluation_questions,
            variant="control"
        )

        # Calculate metrics
        full_correct = sum(1 for r in full_results if r.answered_correctly)
        control_correct = sum(1 for r in control_results if r.answered_correctly)

        regression_detected = full_correct > control_correct

        results = {
            "budget": budget.model_dump(),
            "full_evaluation": {
                "questions_answered": full_correct,
                "total_questions": len(self.evaluation_questions),
                "results": [r.model_dump() for r in full_results]
            },
            "control_evaluation": {
                "questions_answered": control_correct,
                "total_questions": len(self.evaluation_questions),
                "results": [r.model_dump() for r in control_results]
            },
            "regression_detected": regression_detected,
            "regression_count": full_correct - control_correct
        }

        # Save evaluation results
        eval_filepath = self.harness.output_dir / "evaluation_results.json"
        with open(eval_filepath, 'w') as f:
            json.dump(results, f, indent=2)

        return results

    def get_optimization_summary(self) -> Dict[str, Any]:
        """
        Get summary of optimization decisions

        Returns:
            Dict explaining what was summarized vs preserved and why
        """
        summary = {
            "blocks_processed": len(self.harness.context_blocks),
            "summarized": [],
            "preserved": [],
            "rationale": {}
        }

        for block in self.harness.context_blocks:
            if block.strategy.value == "full_preserve":
                summary["preserved"].append(block.content_type.value)
                summary["rationale"][block.content_type.value] = (
                    "Preserved verbatim for accuracy and completeness"
                )
            else:
                summary["summarized"].append(block.content_type.value)
                summary["rationale"][block.content_type.value] = (
                    f"Summarized using {block.strategy.value} to reduce token count"
                )

        return summary

    def verify_requirements(self) -> Dict[str, bool]:
        """
        Verify rubric requirements are met

        Returns:
            Dict of requirement checks
        """
        budget = self.harness.calculate_budget()
        results = self.optimize_and_evaluate()

        checks = {
            "budget_reduction_50_percent": budget.reduction_percentage >= 50,
            "answers_5_of_6_questions": results["full_evaluation"]["questions_answered"] >= 5,
            "control_shows_regression": results["regression_detected"],
            "budget_file_exists": (self.harness.output_dir / "budget.json").exists()
        }

        return checks

    def cleanup(self):
        """Clean up output files"""
        self.harness.cleanup()


# Documentation of context management decisions:
# - CRITICAL_PATHS and ERROR_PATTERNS preserved verbatim for accuracy
# - MODULE_DOCS and CHANGE_HISTORY aggressively summarized for token savings
# - Persistent facts block maintains key information for evaluation
# - Control variant removes facts to demonstrate regression
