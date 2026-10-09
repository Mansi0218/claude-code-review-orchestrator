"""Context Strategy System - Harness Layer

Context assembly, variant generation, and evaluation execution.
Located at: src/context_strategy/harness.py:45-89
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from .model import (
    ContextModel, ContextBlock, ContentType, SummarizationStrategy,
    TokenBudget, EvaluationQuestion, EvaluationResult
)


class ContextStrategyHarness:
    """
    Harness layer for context optimization

    Assembles context, generates variants, and executes evaluations.
    Located at: src/context_strategy/harness.py:45-89
    """

    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize harness with output directory"""
        self.output_dir = output_dir or Path("output/context_strategy")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.model = ContextModel()
        self.context_blocks: List[ContextBlock] = []

    def add_context_block(
        self,
        content_type: ContentType,
        content: str
    ) -> ContextBlock:
        """
        Add a context block with auto-determined strategy

        Returns:
            Created ContextBlock
        """
        strategy = self.model.determine_strategy(content_type)

        block = ContextBlock(
            content_type=content_type,
            original_content=content,
            strategy=strategy
        )

        # Apply summarization if not full preserve
        if strategy != SummarizationStrategy.FULL_PRESERVE:
            block.summarized_content = self.model.apply_summarization(content, strategy)
        else:
            block.summarized_content = content

        block.calculate_tokens()

        self.context_blocks.append(block)
        return block

    def assemble_optimized_context(self, include_facts: bool = True) -> str:
        """
        Assemble optimized context from blocks

        Args:
            include_facts: Whether to include persistent facts block

        Returns:
            Assembled context string
        """
        parts = []

        # Add persistent facts if requested
        if include_facts:
            facts = [
                "System handles insurance claims processing",
                "Critical paths must be preserved for accuracy",
                "Error patterns are essential for debugging"
            ]
            parts.append(self.model.create_persistent_facts_block(facts))

        # Add summarized content blocks
        for block in self.context_blocks:
            header = f"\n=== {block.content_type.value.upper()} ===\n"
            content = block.summarized_content or block.original_content
            parts.append(header + content)

        return '\n\n'.join(parts)

    def create_baseline_context(self) -> str:
        """Create baseline (unsummarized) context"""
        parts = []

        for block in self.context_blocks:
            header = f"\n=== {block.content_type.value.upper()} ===\n"
            parts.append(header + block.original_content)

        return '\n\n'.join(parts)

    def calculate_budget(self) -> TokenBudget:
        """
        Calculate token budget comparing baseline vs optimized

        Returns:
            TokenBudget with reduction metrics
        """
        baseline_tokens = sum(block.original_tokens for block in self.context_blocks)
        optimized_tokens = sum(block.summarized_tokens for block in self.context_blocks)

        # Add persistent facts overhead to optimized
        facts = self.model.create_persistent_facts_block([
            "System handles insurance claims processing",
            "Critical paths must be preserved for accuracy",
            "Error patterns are essential for debugging"
        ])
        optimized_tokens += self.model.estimate_token_count(facts)

        components = {
            "summarized": [
                block.content_type.value
                for block in self.context_blocks
                if block.strategy != SummarizationStrategy.FULL_PRESERVE
            ],
            "preserved": [
                block.content_type.value
                for block in self.context_blocks
                if block.strategy == SummarizationStrategy.FULL_PRESERVE
            ]
        }

        return self.model.create_budget(baseline_tokens, optimized_tokens, components)

    def save_budget(self, budget: TokenBudget, filename: str = "budget.json"):
        """Save budget to JSON file"""
        filepath = self.output_dir / filename

        data = budget.model_dump()

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def load_budget(self, filename: str = "budget.json") -> TokenBudget:
        """Load budget from JSON file"""
        filepath = self.output_dir / filename

        with open(filepath, 'r') as f:
            data = json.load(f)

        return TokenBudget(**data)

    def evaluate_question(
        self,
        question: EvaluationQuestion,
        context: str,
        variant: str = "full"
    ) -> EvaluationResult:
        """
        Evaluate if question can be answered with given context

        Simulates evaluation by checking if required content is present
        """
        # Simple simulation: check if expected keywords are in context
        answered = True

        if question.requires_preserved:
            # Check if preserved content types are in context
            if "CRITICAL_PATHS" not in context or "ERROR_PATTERNS" not in context:
                answered = False

        # Control variant test: if facts removed, some questions should fail
        if variant == "control" and "PERSISTENT FACTS" not in context:
            if question.requires_preserved:
                answered = False

        return EvaluationResult(
            question_id=question.question_id,
            answered_correctly=answered,
            confidence=0.9 if answered else 0.3,
            variant=variant
        )

    def run_evaluation(
        self,
        questions: List[EvaluationQuestion],
        variant: str = "full"
    ) -> List[EvaluationResult]:
        """
        Run evaluation on all questions

        Args:
            questions: List of questions to evaluate
            variant: "full" or "control" (without facts)

        Returns:
            List of evaluation results
        """
        # Assemble context
        if variant == "full":
            context = self.assemble_optimized_context(include_facts=True)
        else:
            context = self.assemble_optimized_context(include_facts=False)

        results = []
        for question in questions:
            result = self.evaluate_question(question, context, variant)
            results.append(result)

        return results

    def cleanup(self):
        """Clean up output files"""
        for file in self.output_dir.glob("*.json"):
            file.unlink()
