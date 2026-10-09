"""Orchestration System - Orchestration Layer

End-to-end defect processing with tiered state and crash recovery.
Located at: src/orchestration/orchestrator.py:12-45
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from .model import StateModel, Defect, DefectStatus, DefectSeverity, HotState
from .harness import OrchestrationHarness


class DefectOrchestrator:
    """
    Orchestration layer for defect processing

    Coordinates tiered state management, crash recovery, and SQL filtering.
    Located at: src/orchestration/orchestrator.py:12-45
    """

    def __init__(self, session_id: str, state_dir: Optional[Path] = None):
        """Initialize orchestrator"""
        self.harness = OrchestrationHarness(session_id, state_dir)
        self.session_id = session_id

    def start_session(self) -> HotState:
        """
        Start or resume session with crash recovery

        Implements resume-vs-fresh decision logic.
        """
        should_resume, hot_state = self.harness.attempt_recovery()

        if should_resume:
            # Resume from hot-state
            return hot_state
        else:
            # Rebuild from SQL (fresh start)
            return self.harness.rebuild_from_sql()

    def process_defect(self, defect: Defect) -> Dict[str, Any]:
        """
        Process a single defect through the pipeline

        1. Store in SQL (cold-state)
        2. Update hot-state
        3. Return processing result
        """
        # Store in SQL cold-state
        self.harness.store_defect_in_sql(defect)

        # Update hot-state
        is_active = defect.status == DefectStatus.IN_PROGRESS
        self.harness.update_hot_state(defect.defect_id, is_active)

        return {
            "defect_id": defect.defect_id,
            "status": defect.status.value,
            "stored_in_sql": True,
            "hot_state_updated": True
        }

    def process_shift(
        self,
        severity_filter: Optional[DefectSeverity] = None,
        status_filter: Optional[DefectStatus] = None
    ) -> Dict[str, Any]:
        """
        Process a shift using SQL-filtered defect slice

        Demonstrates SQL filtering for shift processing.
        """
        # Query filtered slice from SQL
        defects = self.harness.query_defects_sql(severity_filter, status_filter)

        # Process defects
        processed = 0
        for defect in defects:
            if defect.status == DefectStatus.PENDING:
                defect.status = DefectStatus.IN_PROGRESS
                self.harness.store_defect_in_sql(defect)
                self.harness.update_hot_state(defect.defect_id, is_active=True)
                processed += 1

        # Record shift
        filter_desc = f"severity={severity_filter.value if severity_filter else 'all'}, status={status_filter.value if status_filter else 'all'}"
        self.harness.record_shift(processed, f"Processed shift with filter: {filter_desc}")

        return {
            "defects_found": len(defects),
            "defects_processed": processed,
            "filter": filter_desc,
            "used_sql_filtering": True
        }

    def verify_hot_state_budget(self) -> Dict[str, Any]:
        """
        Verify hot-state file is under 5KB budget

        Returns size and budget status.
        """
        hot_state = self.harness.load_hot_state()

        if hot_state is None:
            return {
                "exists": False,
                "size_bytes": 0,
                "under_budget": True
            }

        size = hot_state.get_size_bytes()
        under_budget = hot_state.is_under_budget()

        return {
            "exists": True,
            "size_bytes": size,
            "budget_kb": 5,
            "under_budget": under_budget
        }

    def create_investigation_fork(self, fork_id: str) -> Dict[str, Any]:
        """
        Create forked session for parallel investigation

        Fork is isolated: changes don't affect main session.
        """
        fork = self.harness.create_fork(fork_id)

        # Verify isolation
        hot_state = self.harness.load_hot_state()
        is_isolated = StateModel.ensure_fork_isolation(fork, hot_state)

        return {
            "fork_id": fork_id,
            "parent_session": self.session_id,
            "fork_session": fork.isolated_state.session_id,
            "is_isolated": is_isolated,
            "created_at": fork.created_at.isoformat()
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        hot_state = self.harness.load_hot_state()
        all_defects = self.harness.query_defects_sql()

        stats = {
            "total_defects_in_sql": len(all_defects),
            "hot_state_recent_count": len(hot_state.recent_defects) if hot_state else 0,
            "hot_state_active_count": len(hot_state.active_defects) if hot_state else 0,
            "hot_state_version": hot_state.version if hot_state else 0,
            "hot_state_size_bytes": hot_state.get_size_bytes() if hot_state else 0
        }

        # Count by status
        stats["by_status"] = {}
        for defect in all_defects:
            status = defect.status.value
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1

        return stats

    def cleanup(self):
        """Clean up session"""
        self.harness.cleanup()


# Documentation of recovery and isolation:
#
# Resume vs Fresh Decision (src/orchestration/model.py:67-78):
# - If hot-state exists and is fresh (< 7 days old): RESUME
# - If hot-state is stale (> 7 days old): REBUILD from SQL
# - If hot-state is corrupted: REBUILD from SQL
# - Staleness threshold: 7 days (configurable)
#
# Fork Isolation (src/orchestration/harness.py:234-256):
# - Fork creates independent copy of hot-state
# - Fork has different session_id to prevent collision
# - Changes in fork don't modify parent state
# - Only investigation notes merge back to main session
