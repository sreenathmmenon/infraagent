"""State Machine for Workflow Management"""

from typing import List, Dict, Any, Optional
from models.events import WorkflowState, WorkflowEvent, AgentType
from datetime import datetime


class WorkflowStateMachine:
    """Manages workflow state transitions with event sourcing"""

    # Valid state transitions
    TRANSITIONS = {
        WorkflowState.MONITORING: [WorkflowState.ALERT_DETECTED],
        WorkflowState.ALERT_DETECTED: [WorkflowState.ANALYZING],
        WorkflowState.ANALYZING: [WorkflowState.AWAITING_APPROVAL, WorkflowState.FAILED],
        WorkflowState.AWAITING_APPROVAL: [WorkflowState.APPROVED, WorkflowState.REJECTED],
        WorkflowState.APPROVED: [WorkflowState.EXECUTING],
        WorkflowState.EXECUTING: [WorkflowState.COMPLETED, WorkflowState.FAILED],
        WorkflowState.FAILED: [WorkflowState.ROLLED_BACK],
        WorkflowState.REJECTED: [],  # Terminal state
        WorkflowState.COMPLETED: [],  # Terminal state
        WorkflowState.ROLLED_BACK: []  # Terminal state
    }

    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.events: List[WorkflowEvent] = []
        self.current_state = WorkflowState.MONITORING

    def can_transition(self, to_state: WorkflowState) -> bool:
        """Check if transition to new state is valid"""
        valid_next_states = self.TRANSITIONS.get(self.current_state, [])
        return to_state in valid_next_states

    def transition(
        self,
        to_state: WorkflowState,
        agent: AgentType,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> WorkflowEvent:
        """
        Transition to a new state and create immutable event

        Raises:
            ValueError: If transition is not valid
        """
        if not self.can_transition(to_state):
            raise ValueError(
                f"Invalid transition from {self.current_state} to {to_state}"
            )

        # Create immutable event
        event = WorkflowEvent(
            workflow_id=self.workflow_id,
            state=to_state,
            agent=agent,
            data=data,
            metadata=metadata
        )

        # Log event and update state
        self.events.append(event)
        self.current_state = to_state

        return event

    def get_event_history(self) -> List[WorkflowEvent]:
        """Get complete event history (audit trail)"""
        return self.events.copy()

    def reconstruct_state(self, events: List[WorkflowEvent]) -> WorkflowState:
        """Reconstruct current state from event history"""
        if not events:
            return WorkflowState.MONITORING

        # Sort by timestamp and return last state
        sorted_events = sorted(events, key=lambda e: e.timestamp)
        return sorted_events[-1].state

    def get_state_summary(self) -> Dict[str, Any]:
        """Get summary of current workflow state"""
        return {
            "workflow_id": self.workflow_id,
            "current_state": self.current_state.value,
            "event_count": len(self.events),
            "created_at": self.events[0].timestamp.isoformat() if self.events else None,
            "last_updated": self.events[-1].timestamp.isoformat() if self.events else None,
            "agents_involved": list(set(e.agent.value for e in self.events))
        }
