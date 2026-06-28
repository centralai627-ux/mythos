"""
Mythos Goal Tracker
===================
Sistem tracking dan decomposisi tujuan untuk autonomous operation.
"""
from __future__ import annotations
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class GoalStatus(Enum):
    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    BLOCKED = 'blocked'
    CANCELLED = 'cancelled'


@dataclass
class Goal:
    id: str
    title: str
    description: str
    status: GoalStatus = GoalStatus.PENDING
    priority: int = 5  # 1-10, 10 = highest
    parent_id: Optional[str] = None
    subgoals: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None


class GoalTracker:
    """Sistem tracking tujuan untuk autonomous operation."""

    def __init__(self):
        self.goals: Dict[str, Goal] = {}
        self.current_goal_id: Optional[str] = None
        self.history: List[Dict[str, Any]] = []

    def create_goal(
        self,
        title: str,
        description: str = '',
        priority: int = 5,
        parent_id: Optional[str] = None,
        dependencies: Optional[List[str]] = None
    ) -> str:
        """Buat tujuan baru."""
        goal_id = f"goal_{int(time.time())}_{len(self.goals)}"
        goal = Goal(
            id=goal_id,
            title=title,
            description=description,
            priority=priority,
            parent_id=parent_id,
            dependencies=dependencies or []
        )
        self.goals[goal_id] = goal

        # Add to parent's subgoals
        if parent_id and parent_id in self.goals:
            self.goals[parent_id].subgoals.append(goal_id)

        self._log('created', goal_id, title)
        return goal_id

    def decompose_goal(self, goal_id: str, subgoals: List[str]) -> List[str]:
        """Decompose tujuan menjadi sub-tujuan."""
        if goal_id not in self.goals:
            return []

        created = []
        for title in subgoals:
            sub_id = self.create_goal(
                title=title,
                parent_id=goal_id,
                priority=self.goals[goal_id].priority
            )
            created.append(sub_id)

        return created

    def start_goal(self, goal_id: str) -> bool:
        """Mulai eksekusi tujuan."""
        if goal_id not in self.goals:
            return False

        goal = self.goals[goal_id]

        # Check dependencies
        for dep_id in goal.dependencies:
            if dep_id in self.goals and self.goals[dep_id].status != GoalStatus.COMPLETED:
                return False

        goal.status = GoalStatus.IN_PROGRESS
        goal.updated_at = time.time()
        self.current_goal_id = goal_id
        self._log('started', goal_id, goal.title)
        return True

    def complete_goal(self, goal_id: str) -> bool:
        """Tandai tujuan selesai."""
        if goal_id not in self.goals:
            return False

        goal = self.goals[goal_id]
        goal.status = GoalStatus.COMPLETED
        goal.completed_at = time.time()
        goal.updated_at = time.time()
        self._log('completed', goal_id, goal.title)

        # Check if parent can be completed
        if goal.parent_id and goal.parent_id in self.goals:
            parent = self.goals[goal.parent_id]
            if all(self.goals[sid].status == GoalStatus.COMPLETED for sid in parent.subgoals):
                self.complete_goal(goal.parent_id)

        if self.current_goal_id == goal_id:
            self.current_goal_id = None

        return True

    def block_goal(self, goal_id: str, reason: str = '') -> bool:
        """Blokir tujuan."""
        if goal_id not in self.goals:
            return False

        goal = self.goals[goal_id]
        goal.status = GoalStatus.BLOCKED
        goal.updated_at = time.time()
        self._log('blocked', goal_id, f"{goal.title} - {reason}")
        return True

    def cancel_goal(self, goal_id: str) -> bool:
        """Batalkan tujuan."""
        if goal_id not in self.goals:
            return False

        goal = self.goals[goal_id]
        goal.status = GoalStatus.CANCELLED
        goal.updated_at = time.time()
        self._log('cancelled', goal_id, goal.title)

        if self.current_goal_id == goal_id:
            self.current_goal_id = None

        return True

    def get_next_goal(self) -> Optional[Goal]:
        """Dapatkan tujuan berikutnya berdasarkan prioritas."""
        pending = [
            g for g in self.goals.values()
            if g.status == GoalStatus.PENDING
        ]

        if not pending:
            return None

        # Sort by priority (highest first)
        pending.sort(key=lambda g: g.priority, reverse=True)

        # Check dependencies
        for goal in pending:
            deps_met = all(
                self.goals[dep_id].status == GoalStatus.COMPLETED
                for dep_id in goal.dependencies
                if dep_id in self.goals
            )
            if deps_met:
                return goal

        return None

    def get_status(self) -> Dict[str, Any]:
        """Dapatkan status semua tujuan."""
        return {
            'total': len(self.goals),
            'pending': sum(1 for g in self.goals.values() if g.status == GoalStatus.PENDING),
            'in_progress': sum(1 for g in self.goals.values() if g.status == GoalStatus.IN_PROGRESS),
            'completed': sum(1 for g in self.goals.values() if g.status == GoalStatus.COMPLETED),
            'blocked': sum(1 for g in self.goals.values() if g.status == GoalStatus.BLOCKED),
            'current': self.current_goal_id,
        }

    def get_goal_tree(self, goal_id: str) -> Dict[str, Any]:
        """Dapatkan tree tujuan (goal + subgoals)."""
        if goal_id not in self.goals:
            return {}

        goal = self.goals[goal_id]
        return {
            'id': goal.id,
            'title': goal.title,
            'status': goal.status.value,
            'subgoals': [self.get_goal_tree(sid) for sid in goal.subgoals if sid in self.goals]
        }

    def _log(self, action: str, goal_id: str, details: str):
        """Log aktivitas."""
        self.history.append({
            'action': action,
            'goal_id': goal_id,
            'details': details,
            'timestamp': time.time()
        })


# Global instance
goal_tracker = GoalTracker()
