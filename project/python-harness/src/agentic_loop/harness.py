"""Agentic Loop System - Harness Layer

Execution context for running agentic loops with conversation tracking.
Located at: src/agentic_loop/harness.py:89-134
"""

import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from .model import (
    AgentModel, Claim, RoutingDecision, ConversationTurn,
    LoopTrace, StopReason
)


class AgenticLoopHarness:
    """
    Harness layer for agentic loop execution

    Manages conversation state, turn tracking, and trace persistence.
    Located at: src/agentic_loop/harness.py:89-134
    """

    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize harness with optional output directory"""
        self.output_dir = output_dir or Path("output/agentic_loop")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.model = AgentModel()
        self.active_traces: dict[str, LoopTrace] = {}

    def start_claim_processing(self, claim: Claim) -> LoopTrace:
        """
        Start processing a claim, creating a new trace

        Returns:
            New LoopTrace for this claim
        """
        trace = LoopTrace(claim_id=claim.claim_id)
        self.active_traces[claim.claim_id] = trace
        return trace

    def execute_turn(
        self,
        trace: LoopTrace,
        content: str,
        role: str = "assistant",
        stop_reason: Optional[StopReason] = None,
        tool_calls: Optional[List[str]] = None
    ) -> ConversationTurn:
        """
        Execute a single conversation turn

        Returns:
            The created ConversationTurn
        """
        turn = ConversationTurn(
            turn_number=trace.total_turns + 1,
            role=role,
            content=content,
            stop_reason=stop_reason,
            tool_calls=tool_calls or []
        )

        trace.add_turn(turn)
        return turn

    def check_termination(self, trace: LoopTrace) -> bool:
        """
        Check if loop should terminate based on stop_reason

        This is the loop termination decision point.
        Located at: src/agentic_loop/harness.py:45-67
        """
        return not trace.should_continue()

    def finalize_trace(self, trace: LoopTrace, decision: RoutingDecision):
        """
        Finalize trace with routing decision

        Records the final decision and terminated reason
        """
        trace.final_decision = decision

        if trace.turns:
            trace.terminated_reason = trace.turns[-1].stop_reason

        # Save to disk
        self.save_trace(trace)

        # Remove from active traces
        if trace.claim_id in self.active_traces:
            del self.active_traces[trace.claim_id]

    def save_trace(self, trace: LoopTrace):
        """Save trace to JSON file"""
        filename = f"trace_{trace.claim_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.output_dir / filename

        data = {
            'claim_id': trace.claim_id,
            'total_turns': trace.total_turns,
            'terminated_reason': trace.terminated_reason.value if trace.terminated_reason else None,
            'turns': [
                {
                    'turn_number': t.turn_number,
                    'role': t.role,
                    'content': t.content,
                    'stop_reason': t.stop_reason.value if t.stop_reason else None,
                    'tool_calls': t.tool_calls
                }
                for t in trace.turns
            ],
            'final_decision': trace.final_decision.model_dump() if trace.final_decision else None
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def load_trace(self, filepath: Path) -> LoopTrace:
        """Load trace from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)

        trace = LoopTrace(claim_id=data['claim_id'])

        for turn_data in data['turns']:
            turn = ConversationTurn(
                turn_number=turn_data['turn_number'],
                role=turn_data['role'],
                content=turn_data['content'],
                stop_reason=StopReason(turn_data['stop_reason']) if turn_data['stop_reason'] else None,
                tool_calls=turn_data.get('tool_calls', [])
            )
            trace.add_turn(turn)

        if data.get('final_decision'):
            trace.final_decision = RoutingDecision(**data['final_decision'])

        if data.get('terminated_reason'):
            trace.terminated_reason = StopReason(data['terminated_reason'])

        return trace

    def get_traces_for_claim_type(self, claim_type: str) -> List[Path]:
        """Get all trace files (for analysis)"""
        return list(self.output_dir.glob(f"trace_*.json"))

    def cleanup(self):
        """Clean up old traces"""
        for trace_file in self.output_dir.glob("trace_*.json"):
            trace_file.unlink()
