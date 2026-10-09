"""Orchestration System - Harness Layer

Tiered storage (hot-state JSON + cold-state SQL), crash recovery, and session forking.
Located at: src/orchestration/harness.py:45-123
"""

import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from .model import StateModel, Defect, DefectStatus, DefectSeverity, HotState, SessionFork


class OrchestrationHarness:
    """
    Harness layer for orchestration with tiered storage

    Manages hot-state (JSON <5KB) and cold-state (SQL DB) separation.
    Located at: src/orchestration/harness.py:45-123
    """

    def __init__(self, session_id: str, state_dir: Optional[Path] = None):
        """Initialize harness with tiered storage"""
        self.session_id = session_id
        self.state_dir = state_dir or Path("output/orchestration")
        self.state_dir.mkdir(parents=True, exist_ok=True)

        self.model = StateModel()
        self.hot_state_file = self.state_dir / f"hot_state_{session_id}.json"
        self.db_file = self.state_dir / "defects.db"

        # Initialize SQL database
        self._init_database()

    def _init_database(self):
        """Initialize SQL database for cold-state storage"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS defects (
                defect_id TEXT PRIMARY KEY,
                severity TEXT NOT NULL,
                status TEXT NOT NULL,
                description TEXT,
                created_at TEXT,
                updated_at TEXT,
                metadata TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shifts (
                shift_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                timestamp TEXT,
                defects_processed INTEGER,
                notes TEXT
            )
        """)

        conn.commit()
        conn.close()

    # ==================== Hot-State Operations ====================

    def save_hot_state(self, hot_state: HotState):
        """Save hot-state to JSON file"""
        with open(self.hot_state_file, 'w') as f:
            json.dump(hot_state.model_dump(), f, indent=2, default=str)

    def load_hot_state(self) -> Optional[HotState]:
        """
        Load hot-state from JSON file

        Returns None if file doesn't exist or is corrupted
        """
        if not self.hot_state_file.exists():
            return None

        try:
            with open(self.hot_state_file, 'r') as f:
                data = json.load(f)

            # Parse datetime fields
            data['last_updated'] = datetime.fromisoformat(data['last_updated'])

            return HotState(**data)
        except (json.JSONDecodeError, KeyError, ValueError):
            # Corrupted state file
            return None

    def update_hot_state(self, defect_id: str, is_active: bool = True):
        """Update hot-state with new defect"""
        hot_state = self.load_hot_state()

        if hot_state is None:
            hot_state = HotState(session_id=self.session_id)

        # Add to recent defects
        if defect_id not in hot_state.recent_defects:
            hot_state.recent_defects.append(defect_id)

            # Keep only last 10 recent
            if len(hot_state.recent_defects) > 10:
                hot_state.recent_defects = hot_state.recent_defects[-10:]

        # Manage active defects
        if is_active and defect_id not in hot_state.active_defects:
            hot_state.active_defects.append(defect_id)
        elif not is_active and defect_id in hot_state.active_defects:
            hot_state.active_defects.remove(defect_id)

        hot_state.last_updated = datetime.now()
        hot_state.version += 1

        self.save_hot_state(hot_state)

    # ==================== Cold-State (SQL) Operations ====================

    def store_defect_in_sql(self, defect: Defect):
        """Store defect in SQL database (cold-state)"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO defects
            (defect_id, severity, status, description, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            defect.defect_id,
            defect.severity.value,
            defect.status.value,
            defect.description,
            defect.created_at.isoformat(),
            defect.updated_at.isoformat(),
            json.dumps(defect.metadata)
        ))

        conn.commit()
        conn.close()

    def query_defects_sql(
        self,
        severity: Optional[DefectSeverity] = None,
        status: Optional[DefectStatus] = None
    ) -> List[Defect]:
        """
        Query defects from SQL with filtering

        Demonstrates SQL-based defect slicing for shift processing.
        """
        sql_filter = self.model.create_sql_filter(severity, status)
        query = f"SELECT * FROM defects {sql_filter}"

        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute(query)
        rows = cursor.fetchall()

        defects = []
        for row in rows:
            defect = Defect(
                defect_id=row[0],
                severity=DefectSeverity(row[1]),
                status=DefectStatus(row[2]),
                description=row[3],
                created_at=datetime.fromisoformat(row[4]),
                updated_at=datetime.fromisoformat(row[5]),
                metadata=json.loads(row[6]) if row[6] else {}
            )
            defects.append(defect)

        conn.close()
        return defects

    def record_shift(self, defects_processed: int, notes: str = ""):
        """Record processing shift in SQL"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO shifts (session_id, timestamp, defects_processed, notes)
            VALUES (?, ?, ?, ?)
        """, (self.session_id, datetime.now().isoformat(), defects_processed, notes))

        conn.commit()
        conn.close()

    # ==================== Crash Recovery ====================

    def attempt_recovery(self) -> tuple[bool, Optional[HotState]]:
        """
        Attempt crash recovery

        Returns:
            (should_resume, hot_state_or_none)

        Located at: src/orchestration/harness.py:89-112
        """
        hot_state = self.load_hot_state()

        if self.model.should_resume(hot_state):
            return (True, hot_state)  # Resume from hot-state
        else:
            return (False, None)  # Rebuild from SQL

    def rebuild_from_sql(self) -> HotState:
        """
        Rebuild hot-state from SQL cold-state

        Used when hot-state is stale or corrupted.
        """
        # Query recent defects from SQL
        all_defects = self.query_defects_sql()

        # Sort by updated_at, take most recent
        all_defects.sort(key=lambda d: d.updated_at, reverse=True)
        recent = all_defects[:10]

        # Find active (in-progress) defects
        active_defects = self.query_defects_sql(status=DefectStatus.IN_PROGRESS)

        hot_state = HotState(
            session_id=self.session_id,
            recent_defects=[d.defect_id for d in recent],
            active_defects=[d.defect_id for d in active_defects]
        )

        self.save_hot_state(hot_state)
        return hot_state

    # ==================== Session Forking ====================

    def create_fork(self, fork_id: str) -> SessionFork:
        """
        Create isolated fork of session

        Fork has its own state, changes don't affect parent.
        """
        hot_state = self.load_hot_state() or HotState(session_id=self.session_id)

        # Create isolated copy of state
        fork_state = HotState(
            session_id=f"{self.session_id}_fork_{fork_id}",
            recent_defects=hot_state.recent_defects.copy(),
            active_defects=hot_state.active_defects.copy()
        )

        fork = SessionFork(
            fork_id=fork_id,
            parent_session_id=self.session_id,
            isolated_state=fork_state
        )

        return fork

    def merge_fork(self, fork: SessionFork, merge_notes: bool = True):
        """
        Merge fork results back to main session

        Only notes are merged, state remains isolated.
        """
        if merge_notes and fork.investigation_notes:
            # In practice, would merge insights/findings
            pass

    def cleanup(self):
        """Clean up state files and database"""
        if self.hot_state_file.exists():
            self.hot_state_file.unlink()

        if self.db_file.exists():
            self.db_file.unlink()
