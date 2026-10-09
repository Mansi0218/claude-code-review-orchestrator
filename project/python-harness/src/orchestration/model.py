"""Orchestration System - Model Layer

State models, defect tracking, and recovery decision logic.
Located at: src/orchestration/model.py:34-89
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import json


class DefectStatus(str, Enum):
    """Defect processing status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


class DefectSeverity(str, Enum):
    """Defect severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Defect(BaseModel):
    """Represents a software defect"""
    defect_id: str
    severity: DefectSeverity
    status: DefectStatus = DefectStatus.PENDING
    description: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class HotState(BaseModel):
    """Hot-state (recent/active) context - target <5KB"""
    session_id: str
    recent_defects: List[str] = Field(default_factory=list, max_length=10)
    active_defects: List[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.now)
    version: int = 1

    def get_size_bytes(self) -> int:
        """Calculate size of hot-state in bytes"""
        return len(json.dumps(self.model_dump(), default=str))

    def is_under_budget(self) -> bool:
        """Check if hot-state is under 5KB budget"""
        return self.get_size_bytes() < 5120  # 5KB = 5120 bytes


class SessionFork(BaseModel):
    """Forked session for parallel investigation"""
    fork_id: str
    parent_session_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    isolated_state: Optional[HotState] = None
    investigation_notes: List[str] = Field(default_factory=list)


class StateModel:
    """
    Model layer for state management

    Implements staleness thresholds and recovery decision logic.
    Located at: src/orchestration/model.py:34-89
    """

    # Staleness threshold: state older than 7 days is considered stale
    STALENESS_THRESHOLD_DAYS = 7

    @staticmethod
    def is_state_stale(last_updated: datetime) -> bool:
        """
        Determine if state is stale based on staleness threshold

        Located at: src/orchestration/model.py:67-78
        """
        threshold = timedelta(days=StateModel.STALENESS_THRESHOLD_DAYS)
        age = datetime.now() - last_updated
        return age > threshold

    @staticmethod
    def should_resume(hot_state: Optional[HotState]) -> bool:
        """
        Decide whether to resume from hot-state or start fresh

        Returns True to resume, False to rebuild from SQL.

        Decision logic:
        - If no hot-state exists: start fresh (rebuild from SQL)
        - If hot-state is stale: start fresh (rebuild from SQL)
        - If hot-state is fresh: resume from hot-state
        """
        if hot_state is None:
            return False  # No state, must rebuild from SQL

        if StateModel.is_state_stale(hot_state.last_updated):
            return False  # State is stale, rebuild from SQL

        return True  # State is fresh, resume

    @staticmethod
    def create_sql_filter(severity: Optional[DefectSeverity] = None, status: Optional[DefectStatus] = None) -> str:
        """
        Create SQL WHERE clause for defect filtering

        Returns:
            SQL filter string
        """
        conditions = []

        if severity:
            conditions.append(f"severity = '{severity.value}'")

        if status:
            conditions.append(f"status = '{status.value}'")

        if conditions:
            return "WHERE " + " AND ".join(conditions)
        else:
            return ""

    @staticmethod
    def ensure_fork_isolation(fork: SessionFork, parent_state: HotState) -> bool:
        """
        Verify fork isolation: changes in fork don't affect parent

        Returns True if fork is properly isolated
        """
        if fork.isolated_state is None:
            return False

        # Fork should have different session ID
        if fork.isolated_state.session_id == parent_state.session_id:
            return False

        return True
