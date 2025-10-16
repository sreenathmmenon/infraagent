"""Event Sourcing Models for InfraAgent"""

from enum import Enum
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import uuid


class WorkflowState(str, Enum):
    """Workflow state machine states"""
    MONITORING = "monitoring"
    ALERT_DETECTED = "alert_detected"
    ANALYZING = "analyzing"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class AgentType(str, Enum):
    """Agent types in the system"""
    ORCHESTRATOR = "orchestrator"
    ALERT_AGENT = "alert_agent"
    TOPOLOGY_AGENT = "topology_agent"
    CONFIG_AGENT = "config_agent"
    ACTION_AGENT = "action_agent"


class WorkflowEvent(BaseModel):
    """Immutable event in the workflow"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    state: WorkflowState
    agent: AgentType
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WorkflowApprovalRequest(BaseModel):
    """Human approval request"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Alert information
    alert: Dict[str, Any]

    # AI Analysis
    analysis: Dict[str, Any]
    topology: Dict[str, Any]
    suggestion: Dict[str, Any]

    # Agent timeline
    agent_steps: list[Dict[str, Any]]

    # Enhanced features
    historical_context: Optional[Dict[str, Any]] = None
    time_savings: Optional[Dict[str, Any]] = None
    confidence_breakdown: Optional[Dict[str, Any]] = None
    mcp_info: Optional[Dict[str, Any]] = None

    # Approval status
    status: str = "pending"  # pending, approved, rejected
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    rejection_reason: Optional[str] = None


class WorkflowExecutionResult(BaseModel):
    """Result of executing an approved action"""
    workflow_id: str
    success: bool
    executed_at: datetime = Field(default_factory=datetime.utcnow)
    actions_taken: list[Dict[str, Any]]
    verification: Dict[str, Any]
    rollback_performed: bool = False
    error: Optional[str] = None


class ActivityType(str, Enum):
    """Types of activities in the system"""
    ALERT_FIX = "alert_fix"
    DEPLOYMENT = "deployment"
    CONFIG_CHANGE = "config_change"
    DISK_CLEANUP = "disk_cleanup"
    MESSAGE_QUEUE_MAINTENANCE = "message_queue_maintenance"
    SECURITY_PATCH = "security_patch"
    DATABASE_TUNING = "database_tuning"


class ActivityStatus(str, Enum):
    """Activity execution status"""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class RollbackInfo(BaseModel):
    """Rollback information for an activity"""
    eligible: bool
    expires_at: Optional[datetime] = None
    window_minutes: Optional[int] = None
    action: Optional[str] = None
    risk_level: Optional[str] = None
    rollback_steps: Optional[list[str]] = None
    # For expired or completed rollbacks
    reason: Optional[str] = None
    was_available_until: Optional[datetime] = None
    performed_at: Optional[datetime] = None
    performed_by: Optional[str] = None
    alternative: Optional[str] = None


class Activity(BaseModel):
    """Infrastructure activity with rollback capability"""
    id: str
    type: ActivityType
    title: str
    description: str
    timestamp: datetime
    status: ActivityStatus
    severity: str
    workflow_id: Optional[str] = None
    alert_id: Optional[str] = None
    approved_by: Optional[str] = None
    changes_made: list[Dict[str, Any]]
    runbook_used: Optional[str] = None
    metrics_before: Optional[Dict[str, Any]] = None
    metrics_after: Optional[Dict[str, Any]] = None
    rollback: RollbackInfo


class RunbookStep(BaseModel):
    """Single step in a runbook"""
    step: int
    name: str
    description: str
    estimated_time: str
    command: str
    validation: str
    rollback_impact: Optional[str] = None
    success_criteria: Optional[str] = None


class Runbook(BaseModel):
    """Automated runbook for infrastructure operations"""
    id: str
    title: str
    description: str
    category: str
    severity: str
    estimated_duration: str
    success_rate: int
    execution_count: int
    last_used: Optional[datetime] = None
    steps: list[RunbookStep]
    prerequisites: list[str]
    rollback_steps: list[str]
    risk_assessment: Dict[str, Any]
