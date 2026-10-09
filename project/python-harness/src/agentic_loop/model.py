"""Agentic Loop System - Model Layer

Core data structures for claim processing and stop_reason tracking.
Located at: src/agentic_loop/model.py:23-67
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class StopReason(str, Enum):
    """Stop reason types from API response"""
    TOOL_USE = "tool_use"
    END_TURN = "end_turn"
    MAX_TOKENS = "max_tokens"
    STOP_SEQUENCE = "stop_sequence"


class ClaimType(str, Enum):
    """Types of claims to process"""
    MEDICAL = "medical"
    AUTOMOTIVE = "automotive"
    PROPERTY = "property"
    LIABILITY = "liability"
    WORKERS_COMP = "workers_comp"


class ClaimPriority(int, Enum):
    """Claim priority levels"""
    LOW = 3
    MEDIUM = 2
    HIGH = 1
    CRITICAL = 0


class Claim(BaseModel):
    """Represents an insurance claim to process"""
    claim_id: str
    claim_type: ClaimType
    priority: ClaimPriority
    description: str
    amount: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RoutingDecision(BaseModel):
    """Result of claim routing"""
    claim_id: str
    decision: str  # "approved", "rejected", "escalated"
    tier: int  # 1, 2, or 3
    reason: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ConversationTurn(BaseModel):
    """Single turn in the agentic loop conversation"""
    turn_number: int
    role: str  # "user" or "assistant"
    content: str
    stop_reason: Optional[StopReason] = None
    tool_calls: List[str] = Field(default_factory=list)


class LoopTrace(BaseModel):
    """Complete trace of an agentic loop execution"""
    claim_id: str
    turns: List[ConversationTurn] = Field(default_factory=list)
    final_decision: Optional[RoutingDecision] = None
    total_turns: int = 0
    terminated_reason: Optional[StopReason] = None

    def add_turn(self, turn: ConversationTurn):
        """Add a turn to the trace"""
        self.turns.append(turn)
        self.total_turns += 1

    def should_continue(self) -> bool:
        """Determine if loop should continue based on last turn's stop_reason"""
        if not self.turns:
            return True

        last_turn = self.turns[-1]

        # Continue on tool_use, terminate on end_turn
        if last_turn.stop_reason == StopReason.TOOL_USE:
            return True
        elif last_turn.stop_reason == StopReason.END_TURN:
            return False
        elif last_turn.stop_reason == StopReason.MAX_TOKENS:
            return False

        return True


class AgentModel:
    """
    Model layer for agentic loop execution

    Handles claim classification, routing logic, and loop termination decisions.
    Located at: src/agentic_loop/model.py:23-67
    """

    TIER_1_THRESHOLDS = {
        ClaimType.MEDICAL: 10000,
        ClaimType.AUTOMOTIVE: 5000,
        ClaimType.PROPERTY: 15000,
        ClaimType.LIABILITY: 20000,
        ClaimType.WORKERS_COMP: 8000,
    }

    TIER_2_THRESHOLDS = {
        ClaimType.MEDICAL: 50000,
        ClaimType.AUTOMOTIVE: 25000,
        ClaimType.PROPERTY: 75000,
        ClaimType.LIABILITY: 100000,
        ClaimType.WORKERS_COMP: 40000,
    }

    @staticmethod
    def determine_tier(claim: Claim) -> int:
        """
        Determine processing tier based on claim type and amount

        Returns:
            1 for tier 1 (low), 2 for tier 2 (medium), 3 for tier 3 (high/escalation)
        """
        tier_1_limit = AgentModel.TIER_1_THRESHOLDS.get(claim.claim_type, 10000)
        tier_2_limit = AgentModel.TIER_2_THRESHOLDS.get(claim.claim_type, 50000)

        if claim.amount <= tier_1_limit:
            return 1
        elif claim.amount <= tier_2_limit:
            return 2
        else:
            return 3

    @staticmethod
    def should_escalate(claim: Claim) -> bool:
        """Determine if claim should be escalated"""
        # Critical priority always escalates
        if claim.priority == ClaimPriority.CRITICAL:
            return True

        # High-value claims escalate
        if AgentModel.determine_tier(claim) == 3:
            return True

        return False

    @staticmethod
    def route_claim(claim: Claim) -> RoutingDecision:
        """
        Route claim to appropriate tier or escalation

        This is where loop termination leads to a routing decision.
        Located at: src/agentic_loop/model.py:89-134
        """
        if AgentModel.should_escalate(claim):
            return RoutingDecision(
                claim_id=claim.claim_id,
                decision="escalated",
                tier=3,
                reason=f"Escalated: Priority {claim.priority.name} or high value"
            )

        tier = AgentModel.determine_tier(claim)

        # Auto-approve tier 1
        if tier == 1:
            return RoutingDecision(
                claim_id=claim.claim_id,
                decision="approved",
                tier=1,
                reason="Auto-approved: Low value, standard processing"
            )

        # Route tier 2 for review
        return RoutingDecision(
            claim_id=claim.claim_id,
            decision="approved",
            tier=2,
            reason="Routed to tier 2 for review"
        )

    @staticmethod
    def simulate_stop_reason(turn_number: int, max_turns: int = 5) -> StopReason:
        """
        Simulate stop_reason for testing

        Returns tool_use for early turns, end_turn when complete
        """
        if turn_number < max_turns:
            return StopReason.TOOL_USE
        else:
            return StopReason.END_TURN
