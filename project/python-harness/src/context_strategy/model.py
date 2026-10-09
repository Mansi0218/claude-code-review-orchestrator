"""Context Strategy System - Model Layer

Token counting, context optimization strategies, and evaluation models.
Located at: src/context_strategy/model.py:12-78
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class ContentType(str, Enum):
    """Types of content for summarization decisions"""
    MODULE_DOCS = "module_docs"
    CHANGE_HISTORY = "change_history"
    API_REFERENCE = "api_reference"
    ERROR_PATTERNS = "error_patterns"
    CRITICAL_PATHS = "critical_paths"
    TEST_COVERAGE = "test_coverage"


class SummarizationStrategy(str, Enum):
    """Strategies for content reduction"""
    FULL_PRESERVE = "full_preserve"  # Keep verbatim
    LIGHT_SUMMARY = "light_summary"  # 50% reduction
    AGGRESSIVE_SUMMARY = "aggressive_summary"  # 75% reduction
    KEY_POINTS_ONLY = "key_points_only"  # 90% reduction


class TokenBudget(BaseModel):
    """Token budget tracking"""
    baseline_tokens: int
    optimized_tokens: int
    reduction_percentage: float = 0.0
    components: Dict[str, Any] = Field(default_factory=dict)

    def calculate_reduction(self):
        """Calculate reduction percentage"""
        if self.baseline_tokens > 0:
            self.reduction_percentage = (
                (self.baseline_tokens - self.optimized_tokens) / self.baseline_tokens * 100
            )


class EvaluationQuestion(BaseModel):
    """Question for evaluating context quality"""
    question_id: str
    question: str
    requires_preserved: bool  # Requires preserved content
    expected_answer: Optional[str] = None


class EvaluationResult(BaseModel):
    """Result of answering evaluation question"""
    question_id: str
    answered_correctly: bool
    confidence: float = 0.0
    variant: str = "full"  # "full" or "control"


class ContextBlock(BaseModel):
    """Block of context content"""
    content_type: ContentType
    original_content: str
    summarized_content: Optional[str] = None
    strategy: SummarizationStrategy = SummarizationStrategy.FULL_PRESERVE
    original_tokens: int = 0
    summarized_tokens: int = 0

    def calculate_tokens(self):
        """Estimate token count (rough approximation: 1 token ~= 4 chars)"""
        self.original_tokens = len(self.original_content) // 4
        if self.summarized_content:
            self.summarized_tokens = len(self.summarized_content) // 4
        else:
            self.summarized_tokens = self.original_tokens


class ContextModel:
    """
    Model layer for context optimization

    Implements token counting, summarization decisions, and optimization strategies.
    Located at: src/context_strategy/model.py:12-78
    """

    # Preservation rules: these content types should be preserved verbatim
    PRESERVE_VERBATIM = {
        ContentType.CRITICAL_PATHS,
        ContentType.ERROR_PATTERNS
    }

    # Summarization rules: these can be aggressively summarized
    AGGRESSIVE_SUMMARY = {
        ContentType.MODULE_DOCS,
        ContentType.CHANGE_HISTORY
    }

    @staticmethod
    def determine_strategy(content_type: ContentType) -> SummarizationStrategy:
        """
        Determine summarization strategy based on content type

        Critical paths and error patterns preserved, docs/history summarized.
        """
        if content_type in ContextModel.PRESERVE_VERBATIM:
            return SummarizationStrategy.FULL_PRESERVE

        if content_type in ContextModel.AGGRESSIVE_SUMMARY:
            return SummarizationStrategy.AGGRESSIVE_SUMMARY

        return SummarizationStrategy.LIGHT_SUMMARY

    @staticmethod
    def apply_summarization(content: str, strategy: SummarizationStrategy) -> str:
        """
        Apply summarization strategy to content

        Simulates summarization by reducing content length
        """
        if strategy == SummarizationStrategy.FULL_PRESERVE:
            return content

        # Simulate summarization by extracting key points
        lines = content.split('\n')

        if strategy == SummarizationStrategy.LIGHT_SUMMARY:
            # Keep 50% of lines
            return '\n'.join(lines[::2])

        elif strategy == SummarizationStrategy.AGGRESSIVE_SUMMARY:
            # Keep 25% of lines
            return '\n'.join(lines[::4])

        else:  # KEY_POINTS_ONLY
            # Keep 10% of lines
            return '\n'.join(lines[::10]) if len(lines) >= 10 else lines[0] if lines else ""

    @staticmethod
    def create_persistent_facts_block(facts: List[str]) -> str:
        """
        Create a persistent facts block

        This is the key context element for control variant testing.
        """
        header = "=== PERSISTENT FACTS ===\n\n"
        facts_str = '\n'.join(f"- {fact}" for fact in facts)
        footer = "\n\n=== END PERSISTENT FACTS ==="

        return header + facts_str + footer

    @staticmethod
    def estimate_token_count(text: str) -> int:
        """
        Estimate token count for text

        Rough approximation: 1 token ~= 4 characters
        """
        return len(text) // 4

    @staticmethod
    def create_budget(baseline: int, optimized: int, components: Dict[str, Any]) -> TokenBudget:
        """Create token budget with calculated reduction"""
        budget = TokenBudget(
            baseline_tokens=baseline,
            optimized_tokens=optimized,
            components=components
        )
        budget.calculate_reduction()
        return budget
