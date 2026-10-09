"""
==================== Agentic Loop System Tests ====================

Test suite for agentic loop system (30 tests)

Tests stop_reason-driven execution, claim routing, and loop termination.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from src.agentic_loop.model import (
    AgentModel, Claim, RoutingDecision, StopReason,
    ClaimType, ClaimPriority, ConversationTurn, LoopTrace
)
from src.agentic_loop.harness import AgenticLoopHarness
from src.agentic_loop.orchestrator import ClaimProcessor


# ==================== Model Layer Tests (10 tests) ====================

@pytest.mark.agentic_loop
class TestAgentModel:
    """Test agentic loop model layer"""

    def test_determine_tier_1_medical(self):
        """Test tier 1 determination for low-value medical claim"""
        claim = Claim(
            claim_id="M001",
            claim_type=ClaimType.MEDICAL,
            priority=ClaimPriority.MEDIUM,
            description="Office visit",
            amount=5000
        )

        tier = AgentModel.determine_tier(claim)
        assert tier == 1

    def test_determine_tier_2_automotive(self):
        """Test tier 2 determination for medium-value automotive claim"""
        claim = Claim(
            claim_id="A001",
            claim_type=ClaimType.AUTOMOTIVE,
            priority=ClaimPriority.MEDIUM,
            description="Collision repair",
            amount=15000
        )

        tier = AgentModel.determine_tier(claim)
        assert tier == 2

    def test_determine_tier_3_property(self):
        """Test tier 3 determination for high-value property claim"""
        claim = Claim(
            claim_id="P001",
            claim_type=ClaimType.PROPERTY,
            priority=ClaimPriority.HIGH,
            description="Fire damage",
            amount=100000
        )

        tier = AgentModel.determine_tier(claim)
        assert tier == 3

    def test_should_escalate_critical_priority(self):
        """Test escalation for critical priority claims"""
        claim = Claim(
            claim_id="C001",
            claim_type=ClaimType.LIABILITY,
            priority=ClaimPriority.CRITICAL,
            description="Urgent liability claim",
            amount=5000
        )

        assert AgentModel.should_escalate(claim)

    def test_should_escalate_high_value(self):
        """Test escalation for tier 3 high-value claims"""
        claim = Claim(
            claim_id="C002",
            claim_type=ClaimType.WORKERS_COMP,
            priority=ClaimPriority.MEDIUM,
            description="Workers comp claim",
            amount=50000
        )

        assert AgentModel.should_escalate(claim)

    def test_should_not_escalate_low_value(self):
        """Test no escalation for low-value, low-priority claims"""
        claim = Claim(
            claim_id="C003",
            claim_type=ClaimType.AUTOMOTIVE,
            priority=ClaimPriority.LOW,
            description="Minor fender bender",
            amount=2000
        )

        assert not AgentModel.should_escalate(claim)

    def test_route_claim_tier_1_approved(self):
        """Test routing decision for tier 1 auto-approval"""
        claim = Claim(
            claim_id="R001",
            claim_type=ClaimType.AUTOMOTIVE,
            priority=ClaimPriority.LOW,
            description="Minor damage",
            amount=3000
        )

        decision = AgentModel.route_claim(claim)
        assert decision.decision == "approved"
        assert decision.tier == 1

    def test_route_claim_tier_2_review(self):
        """Test routing decision for tier 2 review"""
        claim = Claim(
            claim_id="R002",
            claim_type=ClaimType.MEDICAL,
            priority=ClaimPriority.MEDIUM,
            description="Surgery",
            amount=30000
        )

        decision = AgentModel.route_claim(claim)
        assert decision.decision == "approved"
        assert decision.tier == 2

    def test_route_claim_escalated(self):
        """Test routing decision for escalation"""
        claim = Claim(
            claim_id="R003",
            claim_type=ClaimType.LIABILITY,
            priority=ClaimPriority.CRITICAL,
            description="Major liability",
            amount=500000
        )

        decision = AgentModel.route_claim(claim)
        assert decision.decision == "escalated"
        assert decision.tier == 3

    def test_simulate_stop_reason_tool_use(self):
        """Test simulated stop_reason returns tool_use for early turns"""
        stop_reason = AgentModel.simulate_stop_reason(turn_number=2, max_turns=5)
        assert stop_reason == StopReason.TOOL_USE

    def test_simulate_stop_reason_end_turn(self):
        """Test simulated stop_reason returns end_turn at max turns"""
        stop_reason = AgentModel.simulate_stop_reason(turn_number=5, max_turns=5)
        assert stop_reason == StopReason.END_TURN


# ==================== Loop Trace Tests (6 tests) ====================

@pytest.mark.agentic_loop
class TestLoopTrace:
    """Test conversation trace management"""

    def test_loop_trace_add_turn(self):
        """Test adding turns to trace"""
        trace = LoopTrace(claim_id="T001")

        turn1 = ConversationTurn(
            turn_number=1,
            role="user",
            content="Process claim",
            stop_reason=None
        )

        trace.add_turn(turn1)
        assert trace.total_turns == 1
        assert len(trace.turns) == 1

    def test_loop_trace_should_continue_tool_use(self):
        """Test loop continuation on tool_use stop_reason"""
        trace = LoopTrace(claim_id="T002")

        turn = ConversationTurn(
            turn_number=1,
            role="assistant",
            content="Analyzing...",
            stop_reason=StopReason.TOOL_USE
        )

        trace.add_turn(turn)
        assert trace.should_continue() is True

    def test_loop_trace_should_terminate_end_turn(self):
        """Test loop termination on end_turn stop_reason"""
        trace = LoopTrace(claim_id="T003")

        turn = ConversationTurn(
            turn_number=1,
            role="assistant",
            content="Complete",
            stop_reason=StopReason.END_TURN
        )

        trace.add_turn(turn)
        assert trace.should_continue() is False

    def test_loop_trace_should_terminate_max_tokens(self):
        """Test loop termination on max_tokens stop_reason"""
        trace = LoopTrace(claim_id="T004")

        turn = ConversationTurn(
            turn_number=1,
            role="assistant",
            content="Long response...",
            stop_reason=StopReason.MAX_TOKENS
        )

        trace.add_turn(turn)
        assert trace.should_continue() is False

    def test_loop_trace_empty_should_continue(self):
        """Test that empty trace allows continuation"""
        trace = LoopTrace(claim_id="T005")
        assert trace.should_continue() is True

    def test_loop_trace_multiple_turns(self):
        """Test trace with multiple turns"""
        trace = LoopTrace(claim_id="T006")

        # Turn 1: tool_use (continue)
        trace.add_turn(ConversationTurn(
            turn_number=1,
            role="assistant",
            content="Turn 1",
            stop_reason=StopReason.TOOL_USE
        ))

        # Turn 2: tool_use (continue)
        trace.add_turn(ConversationTurn(
            turn_number=2,
            role="assistant",
            content="Turn 2",
            stop_reason=StopReason.TOOL_USE
        ))

        # Turn 3: end_turn (terminate)
        trace.add_turn(ConversationTurn(
            turn_number=3,
            role="assistant",
            content="Turn 3",
            stop_reason=StopReason.END_TURN
        ))

        assert trace.total_turns == 3
        assert trace.should_continue() is False


# ==================== Harness Layer Tests (7 tests) ====================

@pytest.mark.agentic_loop
class TestAgenticLoopHarness:
    """Test agentic loop harness layer"""

    @pytest.fixture
    def temp_output(self):
        """Create temporary output directory"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_start_claim_processing(self, temp_output):
        """Test starting claim processing creates trace"""
        harness = AgenticLoopHarness(temp_output)

        claim = Claim(
            claim_id="H001",
            claim_type=ClaimType.MEDICAL,
            priority=ClaimPriority.MEDIUM,
            description="Test claim",
            amount=10000
        )

        trace = harness.start_claim_processing(claim)
        assert trace.claim_id == "H001"
        assert "H001" in harness.active_traces

    def test_execute_turn(self, temp_output):
        """Test executing a conversation turn"""
        harness = AgenticLoopHarness(temp_output)

        claim = Claim(
            claim_id="H002",
            claim_type=ClaimType.AUTOMOTIVE,
            priority=ClaimPriority.LOW,
            description="Test",
            amount=5000
        )

        trace = harness.start_claim_processing(claim)

        turn = harness.execute_turn(
            trace,
            content="Analyzing claim",
            role="assistant",
            stop_reason=StopReason.TOOL_USE,
            tool_calls=["get_history"]
        )

        assert turn.turn_number == 1
        assert turn.stop_reason == StopReason.TOOL_USE
        assert "get_history" in turn.tool_calls

    def test_check_termination_continue(self, temp_output):
        """Test termination check allows continuation on tool_use"""
        harness = AgenticLoopHarness(temp_output)

        trace = LoopTrace(claim_id="H003")
        trace.add_turn(ConversationTurn(
            turn_number=1,
            role="assistant",
            content="Working...",
            stop_reason=StopReason.TOOL_USE
        ))

        assert not harness.check_termination(trace)

    def test_check_termination_stop(self, temp_output):
        """Test termination check stops on end_turn"""
        harness = AgenticLoopHarness(temp_output)

        trace = LoopTrace(claim_id="H004")
        trace.add_turn(ConversationTurn(
            turn_number=1,
            role="assistant",
            content="Done",
            stop_reason=StopReason.END_TURN
        ))

        assert harness.check_termination(trace)

    def test_save_and_load_trace(self, temp_output):
        """Test saving and loading trace from file"""
        harness = AgenticLoopHarness(temp_output)

        trace = LoopTrace(claim_id="H005")
        trace.add_turn(ConversationTurn(
            turn_number=1,
            role="user",
            content="Test",
            stop_reason=None
        ))

        decision = RoutingDecision(
            claim_id="H005",
            decision="approved",
            tier=1,
            reason="Test"
        )

        trace.final_decision = decision
        trace.terminated_reason = StopReason.END_TURN

        harness.save_trace(trace)

        # Load it back
        trace_files = list(temp_output.glob("trace_*.json"))
        assert len(trace_files) == 1

        loaded_trace = harness.load_trace(trace_files[0])
        assert loaded_trace.claim_id == "H005"
        assert loaded_trace.total_turns == 1
        assert loaded_trace.terminated_reason == StopReason.END_TURN

    def test_finalize_trace(self, temp_output):
        """Test finalizing trace with decision"""
        harness = AgenticLoopHarness(temp_output)

        claim = Claim(
            claim_id="H006",
            claim_type=ClaimType.PROPERTY,
            priority=ClaimPriority.MEDIUM,
            description="Test",
            amount=20000
        )

        trace = harness.start_claim_processing(claim)
        harness.execute_turn(
            trace,
            content="Complete",
            stop_reason=StopReason.END_TURN
        )

        decision = RoutingDecision(
            claim_id="H006",
            decision="approved",
            tier=2,
            reason="Test"
        )

        harness.finalize_trace(trace, decision)

        assert trace.final_decision == decision
        assert "H006" not in harness.active_traces

    def test_get_traces_for_claim_type(self, temp_output):
        """Test retrieving trace files"""
        harness = AgenticLoopHarness(temp_output)

        trace = LoopTrace(claim_id="H007")
        harness.save_trace(trace)

        traces = harness.get_traces_for_claim_type("medical")
        assert len(traces) >= 1


# ==================== Orchestration Layer Tests (7 tests) ====================

@pytest.mark.agentic_loop
class TestClaimProcessor:
    """Test claim processor orchestration"""

    @pytest.fixture
    def temp_output(self):
        """Create temporary output directory"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_process_claim_tier_1(self, temp_output):
        """Test processing tier 1 claim end-to-end"""
        processor = ClaimProcessor(temp_output, max_turns=10)

        claim = Claim(
            claim_id="O001",
            claim_type=ClaimType.AUTOMOTIVE,
            priority=ClaimPriority.LOW,
            description="Minor damage",
            amount=3000
        )

        decision = processor.process_claim(claim)

        assert decision.decision == "approved"
        assert decision.tier == 1
        assert decision.claim_id == "O001"

    def test_process_claim_tier_2(self, temp_output):
        """Test processing tier 2 claim end-to-end"""
        processor = ClaimProcessor(temp_output, max_turns=10)

        claim = Claim(
            claim_id="O002",
            claim_type=ClaimType.MEDICAL,
            priority=ClaimPriority.MEDIUM,
            description="Surgery",
            amount=35000
        )

        decision = processor.process_claim(claim)

        assert decision.decision == "approved"
        assert decision.tier == 2

    def test_process_claim_escalated(self, temp_output):
        """Test processing escalated claim"""
        processor = ClaimProcessor(temp_output, max_turns=10)

        claim = Claim(
            claim_id="O003",
            claim_type=ClaimType.LIABILITY,
            priority=ClaimPriority.CRITICAL,
            description="Major incident",
            amount=500000
        )

        decision = processor.process_claim(claim)

        assert decision.decision == "escalated"
        assert decision.tier == 3

    def test_process_claim_creates_trace(self, temp_output):
        """Test that processing creates trace file"""
        processor = ClaimProcessor(temp_output, max_turns=10)

        claim = Claim(
            claim_id="O004",
            claim_type=ClaimType.PROPERTY,
            priority=ClaimPriority.MEDIUM,
            description="Test",
            amount=15000
        )

        processor.process_claim(claim)

        trace_files = list(temp_output.glob("trace_*.json"))
        assert len(trace_files) == 1

    def test_process_batch_multiple_claims(self, temp_output):
        """Test batch processing multiple claims"""
        processor = ClaimProcessor(temp_output, max_turns=10)

        claims = [
            Claim(
                claim_id=f"B{i:03d}",
                claim_type=ClaimType.AUTOMOTIVE,
                priority=ClaimPriority.LOW,
                description=f"Claim {i}",
                amount=2000 + i * 1000
            )
            for i in range(5)
        ]

        decisions = processor.process_batch(claims)

        assert len(decisions) == 5
        assert all(d.decision in ["approved", "escalated"] for d in decisions)

    def test_get_statistics(self, temp_output):
        """Test getting processing statistics"""
        processor = ClaimProcessor(temp_output, max_turns=10)

        claim = Claim(
            claim_id="S001",
            claim_type=ClaimType.MEDICAL,
            priority=ClaimPriority.MEDIUM,
            description="Test",
            amount=10000
        )

        processor.process_claim(claim)

        stats = processor.get_statistics()

        assert stats['total_processed'] == 1
        assert 'avg_turns' in stats
        assert 'termination_reasons' in stats

    def test_max_turns_enforced(self, temp_output):
        """Test that max_turns limit is enforced to prevent infinite loops"""
        processor = ClaimProcessor(temp_output, max_turns=3)

        claim = Claim(
            claim_id="M001",
            claim_type=ClaimType.AUTOMOTIVE,
            priority=ClaimPriority.LOW,
            description="Test",
            amount=5000
        )

        decision = processor.process_claim(claim)

        # Should still produce decision even with limited turns
        assert decision is not None
        assert decision.claim_id == "M001"


# ==================== Summary ====================
# Total tests: 30
# - Model Layer: 11 tests
# - Loop Trace: 6 tests
# - Harness Layer: 7 tests
# - Orchestration Layer: 7 tests
#
# Tests verify:
# - Loop continuation on tool_use stop_reason
# - Loop termination on end_turn stop_reason
# - Claim routing to tiers 1, 2, or escalation
# - Turn-by-turn conversation tracking
# - Trace persistence and loading
# - Anti-pattern: max_turns prevents infinite loops
