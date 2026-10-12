"""Agentic Loop System - Orchestration Layer

End-to-end claim processing workflow coordinating Model and Harness layers.
Located at: src/agentic_loop/orchestrator.py:12-45
"""

import os
from pathlib import Path
from typing import List, Optional
from anthropic import Anthropic
from .model import AgentModel, Claim, RoutingDecision, StopReason
from .harness import AgenticLoopHarness
from .model import LoopTrace


class ClaimProcessor:
    """
    Orchestration layer for end-to-end claim processing

    Coordinates the agentic loop: starts conversation, executes turns,
    checks stop_reason, terminates on end_turn, produces routing decision.

    Located at: src/agentic_loop/orchestrator.py:12-45
    """

    def __init__(self, output_dir: Optional[Path] = None, max_turns: int = 10):
        """
        Initialize claim processor

        Args:
            output_dir: Directory for trace outputs
            max_turns: Maximum turns before forcing termination
        """
        self.harness = AgenticLoopHarness(output_dir)
        self.model = AgentModel()
        self.max_turns = max_turns
        self.client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    def process_claim(self, claim: Claim) -> RoutingDecision:
        """
        Process a claim through the complete agentic loop

        This demonstrates the full loop:
        1. Start conversation
        2. Execute turns with real Claude API calls
        3. Check stop_reason after each turn
        4. Continue on tool_use, terminate on end_turn
        5. Produce routing decision or escalation

        Returns:
            RoutingDecision (routing or escalation)
        """
        # Start trace
        trace = self.harness.start_claim_processing(claim)

        # Build conversation messages
        messages = [{
            "role": "user",
            "content": f"Process claim {claim.claim_id}: {claim.description}. Analyze the claim amount (${claim.amount}) and type ({claim.claim_type.value}) to determine the appropriate processing tier."
        }]

        # Initial user turn
        self.harness.execute_turn(
            trace,
            content=messages[0]["content"],
            role="user"
        )

        # Agent conversation loop
        turn_count = 0
        while turn_count < self.max_turns:
            turn_count += 1

            # Make real API call to Claude
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=1024,
                messages=messages,
                tools=[
                    {
                        "name": "get_claim_history",
                        "description": "Get historical data for similar claims",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "claim_id": {"type": "string"}
                            }
                        }
                    },
                    {
                        "name": "check_policy",
                        "description": "Check policy coverage details",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "policy_id": {"type": "string"}
                            }
                        }
                    }
                ]
            )

            # Extract stop_reason from response
            stop_reason_value = response.stop_reason
            if stop_reason_value == "tool_use":
                stop_reason = StopReason.TOOL_USE
            elif stop_reason_value == "end_turn":
                stop_reason = StopReason.END_TURN
            elif stop_reason_value == "max_tokens":
                stop_reason = StopReason.MAX_TOKENS
            else:
                stop_reason = StopReason.END_TURN

            # Extract content and tool calls
            content_parts = []
            tool_calls = []
            for block in response.content:
                if block.type == "text":
                    content_parts.append(block.text)
                elif block.type == "tool_use":
                    tool_calls.append(block.name)

            content = " ".join(content_parts) if content_parts else f"Processing claim (turn {turn_count})"

            # Execute turn
            self.harness.execute_turn(
                trace,
                content=content,
                role="assistant",
                stop_reason=stop_reason,
                tool_calls=tool_calls
            )

            # Add assistant message to conversation
            messages.append({
                "role": "assistant",
                "content": response.content
            })

            # Check termination (this is the key decision point)
            if self.harness.check_termination(trace):
                break

            # If tool use, provide tool results
            if stop_reason == StopReason.TOOL_USE:
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": f"Tool {block.name} executed successfully"
                        })

                messages.append({
                    "role": "user",
                    "content": tool_results
                })

        # Generate routing decision
        decision = self.model.route_claim(claim)

        # Finalize trace
        self.harness.finalize_trace(trace, decision)

        return decision

    def process_batch(self, claims: List[Claim]) -> List[RoutingDecision]:
        """
        Process multiple claims

        Returns:
            List of routing decisions
        """
        decisions = []

        for claim in claims:
            decision = self.process_claim(claim)
            decisions.append(decision)

        return decisions

    def get_statistics(self) -> dict:
        """Get processing statistics"""
        trace_files = list(self.harness.output_dir.glob("trace_*.json"))

        stats = {
            'total_processed': len(trace_files),
            'traces_available': len(trace_files)
        }

        # Analyze traces
        if trace_files:
            traces = [self.harness.load_trace(f) for f in trace_files]

            stats['avg_turns'] = sum(t.total_turns for t in traces) / len(traces)
            stats['termination_reasons'] = {}

            for trace in traces:
                reason = trace.terminated_reason.value if trace.terminated_reason else "unknown"
                stats['termination_reasons'][reason] = stats['termination_reasons'].get(reason, 0) + 1

        return stats

    def cleanup(self):
        """Clean up traces"""
        self.harness.cleanup()


# Anti-pattern avoidance documented in the orchestrator:
# 1. Infinite loops: We check stop_reason and enforce max_turns
# 2. Ignoring stop signals: We explicitly check stop_reason == END_TURN to terminate
# 3. Unbounded execution: max_turns parameter provides safety boundary
