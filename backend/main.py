"""FastAPI Backend for InfraAgent"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import json
import asyncio
from pathlib import Path

from agents.orchestrator import InfraOrchestrator
from agents.action_agent import ActionAgent
from models.events import WorkflowApprovalRequest
from services.activity_service import ActivityService
from services.health_service import HealthDashboardService
from services.ai_postmortem import PostMortemGenerator

# Initialize FastAPI app
app = FastAPI(title="InfraAgent API", version="1.0.0")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://infra-agent-lilac.vercel.app",
        "https://*.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator and action agent
orchestrator = InfraOrchestrator()
action_agent = ActionAgent()

# Initialize services
activity_service = ActivityService()
health_service = HealthDashboardService()
postmortem_generator = PostMortemGenerator()

# WebSocket connections
active_connections: List[WebSocket] = []


# Request/Response models
class ApproveRequest(BaseModel):
    approved_by: Optional[str] = "demo-user"


class RejectRequest(BaseModel):
    reason: Optional[str] = None
    rejected_by: Optional[str] = "demo-user"


class SimulateAlertRequest(BaseModel):
    scenario: Optional[int] = 1  # 1, 2, or 3


class RollbackRequest(BaseModel):
    performed_by: Optional[str] = "demo-user"
    reason: Optional[str] = None


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error sending message: {e}")


manager = ConnectionManager()


# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "infraagent"}


# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# Simulate alert (demo trigger)
@app.post("/api/alerts/simulate")
async def simulate_alert(request: SimulateAlertRequest):
    """
    Trigger a demo alert scenario

    Returns approval_id to track the workflow
    """
    # Load mock alert based on scenario
    alert_data = _load_mock_alert(request.scenario)

    # Broadcast alert detected
    await manager.broadcast({
        "type": "alert_detected",
        "data": alert_data
    })

    # Start orchestration workflow
    approval_id = await orchestrator.handle_alert(alert_data)

    # Get the approval request
    approval_request = orchestrator.get_approval_request(approval_id)

    # Broadcast approval request created
    if approval_request:
        approval_data = approval_request.model_dump(mode='json')
    else:
        approval_data = {}

    await manager.broadcast({
        "type": "awaiting_approval",
        "data": approval_data
    })

    return {
        "status": "success",
        "approval_id": approval_id,
        "workflow_id": approval_request.workflow_id if approval_request else None
    }


# Get specific approval request
@app.get("/api/approvals/{approval_id}")
async def get_approval(approval_id: str):
    """Get approval request details"""
    approval_request = orchestrator.get_approval_request(approval_id)

    if not approval_request:
        raise HTTPException(status_code=404, detail="Approval request not found")

    return approval_request.model_dump(mode='json')


# Approve action
@app.post("/api/approvals/{approval_id}/approve")
async def approve_action(approval_id: str, request: ApproveRequest):
    """
    Approve an action request and execute the fix
    """
    try:
        # Approve in orchestrator
        result = await orchestrator.approve_request(approval_id, request.approved_by)

        # Broadcast approval
        await manager.broadcast({
            "type": "approved",
            "data": result
        })

        # Get the approval request to execute
        approval_request = orchestrator.get_approval_request(approval_id)
        if not approval_request:
            raise HTTPException(status_code=404, detail="Approval request not found")

        # Broadcast execution starting
        await manager.broadcast({
            "type": "executing",
            "data": {
                "approval_id": approval_id,
                "action": approval_request.suggestion["recommended_action"]["title"]
            }
        })

        # Execute the approved fix
        print(f"🔧 Starting execution for approval {approval_id}")
        execution_result = await action_agent.execute_fix(approval_request.suggestion)
        print(f"✅ Execution complete: {execution_result.get('success')}")

        # Create activity record from completed workflow
        print(f"📝 Creating activity record")
        activity = activity_service.create_activity_from_workflow(
            workflow_id=approval_request.workflow_id,
            alert_data=approval_request.alert,
            suggestion=approval_request.suggestion,
            execution_result=execution_result,
            approved_by=request.approved_by
        )
        print(f"✅ Activity created: {activity.id}")

        # Broadcast execution complete
        print(f"📡 Broadcasting completion event")
        await manager.broadcast({
            "type": "completed",
            "data": {
                **execution_result,
                "activity_id": activity.id
            }
        })
        print(f"✅ Completion broadcast sent")

        return {
            "status": "success",
            "approval_result": result,
            "execution_result": execution_result,
            "activity_id": activity.id
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")


# Reject action
@app.post("/api/approvals/{approval_id}/reject")
async def reject_action(approval_id: str, request: RejectRequest):
    """
    Reject an action request
    """
    try:
        result = await orchestrator.reject_request(
            approval_id, request.reason, request.rejected_by
        )

        # Broadcast rejection
        await manager.broadcast({
            "type": "rejected",
            "data": result
        })

        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Get all pending approvals
@app.get("/api/approvals")
async def get_pending_approvals():
    """Get all pending approval requests"""
    pending = await orchestrator.get_pending_approvals()
    return {
        "count": len(pending),
        "approvals": [req.model_dump(mode='json') for req in pending]
    }


# Get workflow state
@app.get("/api/workflows/{workflow_id}")
async def get_workflow(workflow_id: str):
    """Get workflow state and event history"""
    state = orchestrator.get_workflow_state(workflow_id)
    if not state:
        raise HTTPException(status_code=404, detail="Workflow not found")

    events = orchestrator.get_workflow_events(workflow_id)

    return {
        "state": state,
        "events": [event.model_dump(mode='json') for event in events]
    }


# Helper function to load mock alerts
def _load_mock_alert(scenario: int) -> dict:
    """Load mock alert data based on scenario"""

    # Load alerts from mock data
    try:
        alerts_path = Path(__file__).parent / "mock_infra" / "alerts.json"
        with open(alerts_path, 'r') as f:
            alerts = json.load(f)

        # Return alert based on scenario (1-indexed)
        if 1 <= scenario <= len(alerts):
            return alerts[scenario - 1]
        else:
            return alerts[0]  # Default to first alert

    except Exception as e:
        print(f"Error loading mock alerts: {e}")
        # Fallback alert
        return {
            "id": "alert-fallback",
            "timestamp": "2025-10-16T09:30:00Z",
            "severity": "HIGH",
            "source": "prod-web-03",
            "type": "CPU_SPIKE",
            "metric_value": 95,
            "threshold": 80,
            "description": "CPU utilization above 95%"
        }


# Demo scenarios endpoint
@app.get("/api/scenarios")
async def get_scenarios():
    """Get available demo scenarios"""
    return {
        "scenarios": [
            {
                "id": 1,
                "name": "CPU Spike Mitigation",
                "description": "High CPU on web server requiring config scale",
                "severity": "HIGH",
                "confidence": 87
            },
            {
                "id": 2,
                "name": "Disk Space Recovery",
                "description": "Critical disk space issue on database server",
                "severity": "CRITICAL",
                "confidence": 92
            },
            {
                "id": 3,
                "name": "Network Path Optimization",
                "description": "High latency requiring network path switch",
                "severity": "MEDIUM",
                "confidence": 78
            }
        ]
    }


# Get MCP server information
@app.get("/api/mcp/info")
async def get_mcp_info():
    """Get Model Context Protocol server information"""
    return orchestrator.mcp_server.get_mcp_integration_info()


# Get MCP tools
@app.get("/api/mcp/tools")
async def get_mcp_tools():
    """List available MCP tools"""
    return {
        "tools": orchestrator.mcp_server.list_tools(),
        "count": len(orchestrator.mcp_server.list_tools())
    }


# ============== ACTIVITIES API ==============

@app.get("/api/activities")
async def get_activities(limit: int = 10):
    """Get recent activities"""
    activities = activity_service.get_recent_activities(limit=limit)
    return {
        "count": len(activities),
        "activities": [act.model_dump(mode='json') for act in activities]
    }


@app.get("/api/activities/{activity_id}")
async def get_activity(activity_id: str):
    """Get specific activity details"""
    activity = activity_service.get_activity(activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    return activity.model_dump(mode='json')


@app.post("/api/activities/{activity_id}/rollback")
async def rollback_activity(activity_id: str, request: RollbackRequest):
    """
    Rollback an activity

    Args:
        activity_id: ID of activity to rollback
        request: Rollback request with performer info

    Returns:
        Result of rollback operation
    """
    try:
        result = activity_service.perform_rollback(
            activity_id=activity_id,
            performed_by=request.performed_by
        )

        # Broadcast rollback event
        await manager.broadcast({
            "type": "activity_rolled_back",
            "data": result
        })

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rollback failed: {str(e)}")


# ============== RUNBOOKS API ==============

@app.get("/api/runbooks")
async def get_runbooks(category: Optional[str] = None):
    """Get available runbooks"""
    runbooks = activity_service.list_runbooks(category=category)
    return {
        "count": len(runbooks),
        "runbooks": [rb.model_dump(mode='json') for rb in runbooks]
    }


@app.get("/api/runbooks/{runbook_id}")
async def get_runbook(runbook_id: str):
    """Get specific runbook details"""
    runbook = activity_service.get_runbook(runbook_id)
    if not runbook:
        raise HTTPException(status_code=404, detail="Runbook not found")

    return runbook.model_dump(mode='json')


# ============== HEALTH DASHBOARD API ==============

@app.get("/api/health/dashboard")
async def get_health_dashboard():
    """Get complete health dashboard data"""
    return health_service.get_dashboard_data()


@app.get("/api/health/overall")
async def get_overall_health():
    """Get overall health summary"""
    return health_service.get_overall_health()


@app.get("/api/health/services")
async def get_services(status: Optional[str] = None):
    """Get services list, optionally filtered by status"""
    services = health_service.get_services(status_filter=status)
    return {
        "count": len(services),
        "services": services
    }


@app.get("/api/health/services/{service_id}")
async def get_service(service_id: str):
    """Get specific service details"""
    service = health_service.get_service(service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    return service


@app.get("/api/health/cost")
async def get_cost_metrics():
    """Get cost optimization metrics"""
    return health_service.get_cost_metrics()


@app.get("/api/health/security")
async def get_security_summary():
    """Get security summary"""
    return health_service.get_security_summary()


@app.get("/api/health/compliance")
async def get_compliance_status():
    """Get compliance status"""
    return health_service.get_compliance_status()


# ============== AI POST-MORTEM API ==============

@app.post("/api/activities/{activity_id}/postmortem")
async def generate_postmortem(activity_id: str):
    """
    Generate AI-powered post-mortem report for a completed activity

    Args:
        activity_id: ID of the activity to generate report for

    Returns:
        Post-mortem report with timeline, root cause, impact, lessons learned
    """
    # Get activity details
    activity = activity_service.get_activity(activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Generate report
    try:
        report = await postmortem_generator.generate_report(activity.model_dump(mode='json'))
        return {
            "status": "success",
            "activity_id": activity_id,
            "report": report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


# Root endpoint
@app.get("/")
async def root():
    return {
        "service": "InfraAgent",
        "version": "1.0.0",
        "description": "Autonomous Infrastructure Operations with Human-in-the-Loop",
        "endpoints": {
            "health": "/health",
            "websocket": "/ws",
            "simulate_alert": "POST /api/alerts/simulate",
            "scenarios": "/api/scenarios",
            "approvals": "/api/approvals",
            "approve": "POST /api/approvals/{id}/approve",
            "reject": "POST /api/approvals/{id}/reject",
            "activities": "/api/activities",
            "rollback": "POST /api/activities/{id}/rollback",
            "runbooks": "/api/runbooks",
            "health_dashboard": "/api/health/dashboard",
            "services": "/api/health/services"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
