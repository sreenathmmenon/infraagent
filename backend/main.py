"""FastAPI Backend for InfraAgent"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import json
import asyncio
import os
from pathlib import Path

from agents.orchestrator import InfraOrchestrator
from agents.action_agent import ActionAgent
from agents.log_ingest_agent import get_log_ingest_agent
from agents.pattern_detection_agent import get_pattern_detection_agent
from agents.correlation_engine import get_correlation_engine
from agents.root_cause_analysis_agent import get_root_cause_analysis_agent
from models.events import WorkflowApprovalRequest
from services.activity_service import ActivityService
from services.health_service import HealthDashboardService
from services.ai_postmortem import PostMortemGenerator
from services.log_storage_service import get_log_storage

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
log_ingest_agent = get_log_ingest_agent()
log_storage = get_log_storage()

# Initialize AI agents
pattern_agent = get_pattern_detection_agent()
correlation_engine = get_correlation_engine()
rca_agent = get_root_cause_analysis_agent()

# WebSocket connections
active_connections: List[WebSocket] = []


# Startup: Auto-generate sample data if database is empty
@app.on_event("startup")
async def startup_event():
    """Generate sample data on startup if database is empty"""
    try:
        # Check if database has any logs
        stats = log_storage.get_log_stats()

        if stats['total'] == 0:
            print("\n" + "="*80)
            print("📊 DATABASE IS EMPTY - GENERATING SAMPLE DATA FOR DEMO")
            print("="*80)

            # Generate sample OpenStack cascading failure logs
            import time
            import uuid
            from datetime import datetime

            sample_logs = []
            base_time = time.time() - 3600  # 1 hour ago
            request_id = f"req-{uuid.uuid4()}"
            instance_uuid = str(uuid.uuid4())

            # Phase 1: Database issues
            for i in range(10):
                sample_logs.append({
                    'timestamp': datetime.fromtimestamp(base_time + i).isoformat(),
                    'level': 'WARN',
                    'service': 'mysql-server',
                    'host': 'db-01',
                    'message': f'Connection pool at 95% capacity: {475 + i*2}/500 connections active'
                })

            sample_logs.append({
                'timestamp': datetime.fromtimestamp(base_time + 30).isoformat(),
                'level': 'ERROR',
                'service': 'mysql-server',
                'host': 'db-01',
                'message': 'Connection pool exhausted: max_connections=500 reached'
            })

            # Phase 2: Keystone failures
            for i in range(5):
                sample_logs.append({
                    'timestamp': datetime.fromtimestamp(base_time + 35 + i*5).isoformat(),
                    'level': 'ERROR',
                    'service': 'keystone-api',
                    'host': 'auth-01',
                    'message': f'Database connection timeout after 30s. Cannot verify token'
                })

            # Phase 3: Nova failures
            for i in range(8):
                vm_id = f"vm-{uuid.uuid4().hex[:8]}"
                sample_logs.append({
                    'timestamp': datetime.fromtimestamp(base_time + 70 + i*10).isoformat(),
                    'level': 'ERROR',
                    'service': 'nova-compute',
                    'host': f'compute-{i%3 + 1:02d}',
                    'message': f'VM boot failed for {vm_id}. Networking setup failed'
                })

            # Phase 4: Recovery
            sample_logs.append({
                'timestamp': datetime.fromtimestamp(base_time + 200).isoformat(),
                'level': 'INFO',
                'service': 'mysql-server',
                'host': 'db-01',
                'message': 'Connection pool back to normal: 120/500 connections'
            })

            # Add normal operational logs
            for i in range(40):
                sample_logs.append({
                    'timestamp': datetime.fromtimestamp(base_time + 250 + i*10).isoformat(),
                    'level': 'INFO',
                    'service': ['nova-api', 'neutron-server', 'glance-api', 'keystone-admin'][i % 4],
                    'host': f'controller-{i%2 + 1:02d}',
                    'message': 'Metrics collected and sent to monitoring'
                })

            # Ingest all sample logs
            log_ingest_agent.ingest_json_logs_batch(sample_logs)

            print(f"✅ Generated {len(sample_logs)} sample logs")
            print(f"   - Database exhaustion scenario")
            print(f"   - VM boot failures")
            print(f"   - Recovery phase")
            print("="*80 + "\n")
        else:
            print(f"\n✅ Database already has {stats['total']} logs - skipping sample data generation\n")

    except Exception as e:
        print(f"\n⚠️  Error generating sample data: {e}\n")


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


class LogIngestRequest(BaseModel):
    logs: List[dict]  # List of log entries


class LogQueryRequest(BaseModel):
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    levels: Optional[List[str]] = None
    services: Optional[List[str]] = None
    search: Optional[str] = None
    limit: int = 100
    offset: int = 0


# AI Request Models
class AIAnalyzeRequest(BaseModel):
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    services: Optional[List[str]] = None
    include_remediation: bool = True


class NLQueryRequest(BaseModel):
    query: str
    hours: int = 1  # Look back window


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


# ============== LOGS API ==============

@app.post("/api/logs/ingest")
async def ingest_logs(request: LogIngestRequest):
    """
    Ingest logs from external sources

    Accepts JSON-formatted logs in batch
    """
    try:
        count = log_ingest_agent.ingest_json_logs_batch(request.logs)

        # Broadcast new logs event
        await manager.broadcast({
            "type": "logs_ingested",
            "data": {
                "count": count,
                "timestamp": asyncio.get_event_loop().time()
            }
        })

        return {
            "status": "success",
            "count": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@app.post("/api/logs/query")
async def query_logs(request: LogQueryRequest):
    """
    Query logs with filters

    Supports filtering by time range, levels, services, and text search
    """
    try:
        logs = log_storage.query_logs(
            start_time=request.start_time,
            end_time=request.end_time,
            levels=request.levels,
            services=request.services,
            search=request.search,
            limit=request.limit,
            offset=request.offset
        )

        total = log_storage.get_log_count(
            start_time=request.start_time,
            end_time=request.end_time,
            levels=request.levels,
            services=request.services
        )

        return {
            "logs": logs,
            "count": len(logs),
            "total": total,
            "offset": request.offset,
            "limit": request.limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@app.get("/api/logs/recent")
async def get_recent_logs(limit: int = 100):
    """Get most recent logs"""
    try:
        logs = log_storage.get_recent_logs(limit=limit)
        return {
            "logs": logs,
            "count": len(logs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get logs: {str(e)}")


@app.get("/api/logs/stats")
async def get_log_stats(hours: int = 24):
    """Get log statistics for time window"""
    try:
        stats = log_storage.get_log_stats(hours=hours)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@app.post("/api/logs/load-sample-data")
async def load_sample_data():
    """Manually load sample data for demo purposes"""
    try:
        # Check if database already has data
        stats = log_storage.get_log_stats()

        if stats['total'] > 0:
            return {
                "status": "skipped",
                "message": f"Database already has {stats['total']} logs",
                "total": stats['total']
            }

        # Generate sample logs
        import time
        import uuid
        from datetime import datetime

        sample_logs = []
        base_time = time.time() - 3600  # 1 hour ago

        # Phase 1: Database issues
        for i in range(10):
            sample_logs.append({
                'timestamp': datetime.fromtimestamp(base_time + i).isoformat(),
                'level': 'WARN',
                'service': 'mysql-server',
                'host': 'db-01',
                'message': f'Connection pool at 95% capacity: {475 + i*2}/500 connections active'
            })

        sample_logs.append({
            'timestamp': datetime.fromtimestamp(base_time + 30).isoformat(),
            'level': 'ERROR',
            'service': 'mysql-server',
            'host': 'db-01',
            'message': 'Connection pool exhausted: max_connections=500 reached'
        })

        # Phase 2: Keystone failures
        for i in range(5):
            sample_logs.append({
                'timestamp': datetime.fromtimestamp(base_time + 35 + i*5).isoformat(),
                'level': 'ERROR',
                'service': 'keystone-api',
                'host': 'auth-01',
                'message': f'Database connection timeout after 30s. Cannot verify token'
            })

        # Phase 3: Nova failures
        for i in range(8):
            vm_id = f"vm-{uuid.uuid4().hex[:8]}"
            sample_logs.append({
                'timestamp': datetime.fromtimestamp(base_time + 70 + i*10).isoformat(),
                'level': 'ERROR',
                'service': 'nova-compute',
                'host': f'compute-{i%3 + 1:02d}',
                'message': f'VM boot failed for {vm_id}. Networking setup failed'
            })

        # Phase 4: Recovery
        sample_logs.append({
            'timestamp': datetime.fromtimestamp(base_time + 200).isoformat(),
            'level': 'INFO',
            'service': 'mysql-server',
            'host': 'db-01',
            'message': 'Connection pool back to normal: 120/500 connections'
        })

        # Add normal operational logs
        for i in range(40):
            sample_logs.append({
                'timestamp': datetime.fromtimestamp(base_time + 250 + i*10).isoformat(),
                'level': 'INFO',
                'service': ['nova-api', 'neutron-server', 'glance-api', 'keystone-admin'][i % 4],
                'host': f'controller-{i%2 + 1:02d}',
                'message': 'Metrics collected and sent to monitoring'
            })

        # Ingest all sample logs
        log_ingest_agent.ingest_json_logs_batch(sample_logs)

        return {
            "status": "success",
            "message": "Sample data loaded successfully",
            "total": len(sample_logs),
            "scenarios": ["Database exhaustion", "VM boot failures", "Recovery phase"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load sample data: {str(e)}")


@app.get("/api/logs/services")
async def get_log_services():
    """Get list of unique services in logs"""
    try:
        services = log_storage.get_services()
        return {
            "services": services,
            "count": len(services)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get services: {str(e)}")


# ============== AI INTELLIGENCE API ==============

@app.post("/api/ai/analyze")
async def analyze_logs(request: AIAnalyzeRequest):
    """
    AI-powered incident analysis
    Performs pattern detection, correlation, and root cause analysis

    Perfect for L2/L3 engineers: "What went wrong in the last hour?"
    """
    try:
        # Get logs for time window
        import time
        end_time = request.end_time or time.time()
        start_time = request.start_time or (end_time - 3600)  # Default 1 hour

        logs = log_storage.query_logs(
            start_time=start_time,
            end_time=end_time,
            services=request.services,
            limit=10000
        )

        if not logs:
            return {
                "status": "no_data",
                "message": "No logs found for the specified time range"
            }

        # Step 1: Pattern Detection
        pattern_analysis = pattern_agent.analyze_logs(logs)

        # Step 2: Anomaly Detection
        anomalies = pattern_agent.detect_anomalies(logs)

        # Step 3: Correlation (find incidents)
        incidents = correlation_engine.correlate_incidents(logs)

        # Step 4: Root Cause Analysis (on top incident)
        root_cause_analysis = None
        if incidents:
            top_incident = incidents[0]
            root_cause_analysis = rca_agent.analyze_incident(
                top_incident,
                include_remediation=request.include_remediation
            )

        return {
            "status": "success",
            "time_range": {
                "start": start_time,
                "end": end_time,
                "duration_hours": (end_time - start_time) / 3600
            },
            "logs_analyzed": len(logs),
            "patterns": pattern_analysis,
            "anomalies": anomalies,
            "incidents": incidents,
            "root_cause_analysis": root_cause_analysis
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/api/ai/nl-query")
async def natural_language_query(request: NLQueryRequest):
    """
    Ask questions in natural language

    Examples:
    - "Why are VMs failing to boot?"
    - "What caused the authentication errors?"
    - "Show me database connection issues"

    Returns instant AI-powered answers
    """
    try:
        # Get recent logs
        import time
        end_time = time.time()
        start_time = end_time - (request.hours * 3600)

        logs = log_storage.query_logs(
            start_time=start_time,
            end_time=end_time,
            limit=1000
        )

        if not logs:
            return {
                "status": "no_data",
                "answer": "No logs found for the specified time range"
            }

        # Call AI for natural language answer
        result = rca_agent.answer_natural_language_query(
            request.query,
            logs
        )

        return {
            "status": "success",
            "query": request.query,
            "time_range_hours": request.hours,
            "logs_analyzed": len(logs),
            **result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@app.get("/api/ai/patterns")
async def get_log_patterns(hours: int = 1):
    """
    Get detected log patterns

    Reduces 50K logs to 5-10 unique patterns for easy review
    """
    try:
        import time
        end_time = time.time()
        start_time = end_time - (hours * 3600)

        logs = log_storage.query_logs(
            start_time=start_time,
            end_time=end_time,
            limit=50000
        )

        if not logs:
            return {
                "status": "no_data",
                "patterns": []
            }

        analysis = pattern_agent.analyze_logs(logs)

        return {
            "status": "success",
            "time_range_hours": hours,
            **analysis
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pattern detection failed: {str(e)}")


@app.post("/api/ai/correlate")
async def correlate_logs(request: AIAnalyzeRequest):
    """
    Find correlated incidents across services

    Links failures: Keystone auth → Nova compute → Neutron network
    """
    try:
        import time
        end_time = request.end_time or time.time()
        start_time = request.start_time or (end_time - 3600)

        logs = log_storage.query_logs(
            start_time=start_time,
            end_time=end_time,
            services=request.services,
            limit=10000
        )

        if not logs:
            return {
                "status": "no_data",
                "incidents": []
            }

        incidents = correlation_engine.correlate_incidents(logs)

        return {
            "status": "success",
            "time_range": {
                "start": start_time,
                "end": end_time
            },
            "logs_analyzed": len(logs),
            "incidents_found": len(incidents),
            "incidents": incidents
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Correlation failed: {str(e)}")


@app.get("/api/ai/anomalies")
async def detect_anomalies(hours: int = 24):
    """
    Detect anomalous patterns (error rate spikes)

    Finds unusual behavior compared to baseline
    """
    try:
        import time
        end_time = time.time()
        start_time = end_time - (hours * 3600)

        logs = log_storage.query_logs(
            start_time=start_time,
            end_time=end_time,
            limit=50000
        )

        if not logs:
            return {
                "status": "no_data",
                "anomalies": []
            }

        anomalies = pattern_agent.detect_anomalies(logs, baseline_hours=hours)

        return {
            "status": "success",
            "time_range_hours": hours,
            "logs_analyzed": len(logs),
            "anomalies_found": len(anomalies),
            "anomalies": anomalies
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Anomaly detection failed: {str(e)}")


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


# Debug endpoint - check AI status
@app.get("/api/ai/status")
async def ai_status():
    """Check if Claude AI is properly initialized"""
    has_api_key = bool(os.getenv('ANTHROPIC_API_KEY'))
    has_client = rca_agent.client is not None

    return {
        "api_key_set": has_api_key,
        "claude_client_initialized": has_client,
        "status": "Real Claude AI" if has_client else "Mock AI (no API key)"
    }


# Root endpoint
@app.get("/")
async def root():
    return {
        "service": "InfraAgent",
        "version": "2.0.0",
        "description": "AI-Powered Infrastructure Operations with Intelligent Log Analysis",
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
            "logs_ingest": "POST /api/logs/ingest",
            "logs_query": "POST /api/logs/query",
            "logs_recent": "/api/logs/recent",
            "logs_stats": "/api/logs/stats",
            "ai_analyze": "POST /api/ai/analyze - Full AI incident analysis",
            "ai_nl_query": "POST /api/ai/nl-query - Ask questions in natural language",
            "ai_patterns": "GET /api/ai/patterns - Detect log patterns",
            "ai_correlate": "POST /api/ai/correlate - Find correlated incidents",
            "ai_anomalies": "GET /api/ai/anomalies - Detect anomalous behavior",
            "health_dashboard": "/api/health/dashboard",
            "services": "/api/health/services"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
