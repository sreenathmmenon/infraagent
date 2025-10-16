"""Orchestrator - Coordinates multi-agent workflow"""

from typing import Dict, Any, Optional
import uuid
import json
from datetime import datetime

from models.events import (
    WorkflowState,
    WorkflowEvent,
    AgentType,
    WorkflowApprovalRequest
)
from models.state import WorkflowStateMachine
from agents.alert_agent import AlertAgent
from agents.topology_agent import TopologyAgent
from agents.config_agent import ConfigAgent
from services.historical_context import HistoricalContextService
from services.mcp_server import MCPServer


class InfraOrchestrator:
    """
    Master orchestrator for infrastructure operations
    Coordinates: Alert Agent → Topology Agent → Config Agent → Human Approval
    """

    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.workflows: Dict[str, WorkflowStateMachine] = {}
        self.approval_requests: Dict[str, WorkflowApprovalRequest] = {}

        # Initialize agents
        self.alert_agent = AlertAgent(llm_client)
        self.topology_agent = TopologyAgent()
        self.config_agent = ConfigAgent(llm_client)

        # Initialize services
        self.historical_service = HistoricalContextService()
        self.mcp_server = MCPServer()

    async def handle_alert(self, alert_data: Dict[str, Any]) -> str:
        """
        Main orchestration flow for handling an infrastructure alert

        Args:
            alert_data: Alert information from monitoring system

        Returns:
            approval_id: ID of the approval request created
        """
        # Create new workflow
        workflow_id = str(uuid.uuid4())
        state_machine = WorkflowStateMachine(workflow_id)
        self.workflows[workflow_id] = state_machine

        # Transition: MONITORING → ALERT_DETECTED
        state_machine.transition(
            WorkflowState.ALERT_DETECTED,
            AgentType.ORCHESTRATOR,
            {"alert": alert_data}
        )

        # Transition: ALERT_DETECTED → ANALYZING
        state_machine.transition(
            WorkflowState.ANALYZING,
            AgentType.ORCHESTRATOR,
            {"status": "Starting multi-agent analysis"}
        )

        # Step 1: Alert Agent analyzes
        analysis = await self.alert_agent.analyze(alert_data)
        # Log event without state change (still ANALYZING)
        event = WorkflowEvent(
            workflow_id=workflow_id,
            state=WorkflowState.ANALYZING,
            agent=AgentType.ALERT_AGENT,
            data={"analysis": analysis}
        )
        state_machine.events.append(event)

        # Step 2: Topology Agent maps dependencies
        topology = await self.topology_agent.get_context(analysis)
        # Log event without state change
        event = WorkflowEvent(
            workflow_id=workflow_id,
            state=WorkflowState.ANALYZING,
            agent=AgentType.TOPOLOGY_AGENT,
            data={"topology": topology}
        )
        state_machine.events.append(event)

        # Step 3: Config Agent suggests fix
        suggestion = await self.config_agent.suggest_fix(analysis, topology)
        # Log event without state change
        event = WorkflowEvent(
            workflow_id=workflow_id,
            state=WorkflowState.ANALYZING,
            agent=AgentType.CONFIG_AGENT,
            data={"suggestion": suggestion}
        )
        state_machine.events.append(event)

        # Step 4: Get historical context (RAG)
        historical_context = self.historical_service.get_similar_incidents(
            alert_type=alert_data.get("type"),
            source=alert_data.get("source")
        )

        # Step 5: Calculate time/cost savings
        time_savings = self.historical_service.calculate_time_savings(
            ai_resolution_time=180,  # 3 minutes average
            alert_type=alert_data.get("type")
        )

        # Step 6: Get confidence breakdown
        confidence_breakdown = self.historical_service.get_confidence_breakdown(
            base_confidence=suggestion.get("confidence", 50),
            has_history=historical_context.get("found", False),
            pattern_match=historical_context.get("count", 0) >= 3
        )

        # Step 7: Get MCP server info
        mcp_info = self.mcp_server.get_mcp_integration_info()

        # Create approval request
        approval_request = self._create_approval_request(
            workflow_id, alert_data, analysis, topology, suggestion,
            historical_context, time_savings, confidence_breakdown, mcp_info
        )

        # Transition: ANALYZING → AWAITING_APPROVAL
        state_machine.transition(
            WorkflowState.AWAITING_APPROVAL,
            AgentType.ORCHESTRATOR,
            {"approval_id": approval_request.id}
        )

        return approval_request.id

    def _create_approval_request(
        self,
        workflow_id: str,
        alert_data: Dict[str, Any],
        analysis: Dict[str, Any],
        topology: Dict[str, Any],
        suggestion: Dict[str, Any],
        historical_context: Dict[str, Any],
        time_savings: Dict[str, Any],
        confidence_breakdown: Dict[str, Any],
        mcp_info: Dict[str, Any]
    ) -> WorkflowApprovalRequest:
        """Create human approval request with enhanced context"""

        # Build agent timeline for UI
        agent_steps = [
            {
                "agent_name": "Alert Detection",
                "description": "Infrastructure monitoring detected anomaly",
                "completed": True,
                "duration": "0.1s"
            },
            {
                "agent_name": self.alert_agent.name,
                "description": analysis.get("root_cause", "Analyzed alert pattern"),
                "completed": True,
                "duration": analysis.get("duration", "1.2s")
            },
            {
                "agent_name": self.topology_agent.name,
                "description": f"Mapped {topology.get('affected_count', 0)} affected services",
                "completed": True,
                "duration": topology.get("duration", "0.8s")
            },
            {
                "agent_name": self.config_agent.name,
                "description": suggestion["recommended_action"]["title"],
                "completed": True,
                "duration": suggestion.get("duration", "1.5s")
            }
        ]

        # Add historical context step if found
        if historical_context.get("found"):
            agent_steps.append({
                "agent_name": "Historical Context (RAG)",
                "description": f"Found {historical_context['count']} similar incidents ({historical_context['success_rate']}% success rate)",
                "completed": True,
                "duration": "0.3s"
            })

        approval_request = WorkflowApprovalRequest(
            workflow_id=workflow_id,
            alert=alert_data,
            analysis=analysis,
            topology=topology,
            suggestion=suggestion,
            agent_steps=agent_steps,
            historical_context=historical_context,
            time_savings=time_savings,
            confidence_breakdown=confidence_breakdown,
            mcp_info=mcp_info
        )

        # Store for retrieval
        self.approval_requests[approval_request.id] = approval_request

        return approval_request

    async def approve_request(
        self, approval_id: str, approved_by: str = "demo-user"
    ) -> Dict[str, Any]:
        """
        Approve an action request

        Args:
            approval_id: ID of the approval request
            approved_by: User who approved (for audit trail)

        Returns:
            Result of approval
        """
        approval_request = self.approval_requests.get(approval_id)
        if not approval_request:
            raise ValueError(f"Approval request {approval_id} not found")

        workflow_id = approval_request.workflow_id
        state_machine = self.workflows.get(workflow_id)
        if not state_machine:
            raise ValueError(f"Workflow {workflow_id} not found")

        # Update approval request
        approval_request.status = "approved"
        approval_request.approved_at = datetime.utcnow()
        approval_request.approved_by = approved_by

        # Transition: AWAITING_APPROVAL → APPROVED
        state_machine.transition(
            WorkflowState.APPROVED,
            AgentType.ORCHESTRATOR,
            {
                "approval_id": approval_id,
                "approved_by": approved_by,
                "approved_at": approval_request.approved_at.isoformat()
            }
        )

        return {
            "status": "approved",
            "workflow_id": workflow_id,
            "approval_id": approval_id,
            "next_step": "executing"
        }

    async def reject_request(
        self, approval_id: str, reason: str = None, rejected_by: str = "demo-user"
    ) -> Dict[str, Any]:
        """
        Reject an action request

        Args:
            approval_id: ID of the approval request
            reason: Reason for rejection
            rejected_by: User who rejected

        Returns:
            Result of rejection
        """
        approval_request = self.approval_requests.get(approval_id)
        if not approval_request:
            raise ValueError(f"Approval request {approval_id} not found")

        workflow_id = approval_request.workflow_id
        state_machine = self.workflows.get(workflow_id)
        if not state_machine:
            raise ValueError(f"Workflow {workflow_id} not found")

        # Update approval request
        approval_request.status = "rejected"
        approval_request.rejection_reason = reason

        # Transition: AWAITING_APPROVAL → REJECTED
        state_machine.transition(
            WorkflowState.REJECTED,
            AgentType.ORCHESTRATOR,
            {
                "approval_id": approval_id,
                "rejected_by": rejected_by,
                "reason": reason
            }
        )

        return {
            "status": "rejected",
            "workflow_id": workflow_id,
            "approval_id": approval_id
        }

    def get_approval_request(self, approval_id: str) -> Optional[WorkflowApprovalRequest]:
        """Get approval request by ID"""
        return self.approval_requests.get(approval_id)

    def get_workflow_state(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get current workflow state"""
        state_machine = self.workflows.get(workflow_id)
        if not state_machine:
            return None

        return state_machine.get_state_summary()

    def get_workflow_events(self, workflow_id: str) -> list[WorkflowEvent]:
        """Get complete event history for workflow (audit trail)"""
        state_machine = self.workflows.get(workflow_id)
        if not state_machine:
            return []

        return state_machine.get_event_history()

    async def get_pending_approvals(self) -> list[WorkflowApprovalRequest]:
        """Get all pending approval requests"""
        return [
            req for req in self.approval_requests.values()
            if req.status == "pending"
        ]
