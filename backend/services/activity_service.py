"""Activity and Runbook Management Service"""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from models.events import Activity, Runbook, ActivityStatus, RollbackInfo


class ActivityService:
    """Manages activities and runbooks"""

    def __init__(self):
        self.activities: List[Activity] = []
        self.runbooks: Dict[str, Runbook] = {}
        self._load_mock_data()

    def _load_mock_data(self):
        """Load mock activities and runbooks from JSON files"""
        base_path = Path(__file__).parent.parent / "mock_infra"

        # Load activities
        try:
            activities_path = base_path / "activities.json"
            with open(activities_path, 'r') as f:
                activities_data = json.load(f)
                self.activities = [Activity(**act) for act in activities_data]
        except Exception as e:
            print(f"Error loading activities: {e}")
            self.activities = []

        # Load runbooks
        try:
            runbooks_path = base_path / "runbooks.json"
            with open(runbooks_path, 'r') as f:
                runbooks_data = json.load(f)
                self.runbooks = {rb['id']: Runbook(**rb) for rb in runbooks_data}
        except Exception as e:
            print(f"Error loading runbooks: {e}")
            self.runbooks = {}

    def get_recent_activities(self, limit: int = 10) -> List[Activity]:
        """Get recent activities sorted by timestamp"""
        # Update rollback eligibility based on current time
        from datetime import timezone
        current_time = datetime.now(timezone.utc)

        for activity in self.activities:
            if activity.rollback.eligible and activity.rollback.expires_at:
                # Make both datetimes timezone-aware for comparison
                expires_at = activity.rollback.expires_at
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)

                if current_time > expires_at:
                    # Expire the rollback
                    activity.rollback.eligible = False
                    activity.rollback.reason = "Rollback window expired"
                    activity.rollback.was_available_until = activity.rollback.expires_at

        # Sort by timestamp descending (ensure timezone-aware comparison)
        sorted_activities = sorted(
            self.activities,
            key=lambda x: x.timestamp if x.timestamp.tzinfo else x.timestamp.replace(tzinfo=timezone.utc),
            reverse=True
        )

        return sorted_activities[:limit]

    def get_activity(self, activity_id: str) -> Optional[Activity]:
        """Get activity by ID"""
        for activity in self.activities:
            if activity.id == activity_id:
                return activity
        return None

    def add_activity(self, activity: Activity) -> Activity:
        """Add new activity to tracking"""
        self.activities.append(activity)
        return activity

    def perform_rollback(self, activity_id: str, performed_by: str = "demo-user") -> Dict[str, Any]:
        """
        Perform rollback for an activity

        Args:
            activity_id: ID of the activity to rollback
            performed_by: User performing the rollback

        Returns:
            Result of rollback operation
        """
        activity = self.get_activity(activity_id)

        if not activity:
            raise ValueError(f"Activity {activity_id} not found")

        if not activity.rollback.eligible:
            raise ValueError(
                f"Activity {activity_id} is not eligible for rollback. "
                f"Reason: {activity.rollback.reason}"
            )

        # Check if rollback window expired
        from datetime import timezone
        current_time = datetime.now(timezone.utc)
        expires_at = activity.rollback.expires_at
        if expires_at:
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if current_time > expires_at:
                raise ValueError(
                    f"Rollback window expired at {activity.rollback.expires_at.isoformat()}"
                )

        # Update activity status
        activity.status = ActivityStatus.ROLLED_BACK

        # Update rollback info
        activity.rollback.performed_at = current_time
        activity.rollback.performed_by = performed_by
        activity.rollback.eligible = False

        # In a real system, this would execute the actual rollback commands
        # For demo, we'll simulate success

        return {
            "status": "success",
            "activity_id": activity_id,
            "rolled_back_at": current_time.isoformat(),
            "performed_by": performed_by,
            "changes_reverted": activity.changes_made,
            "rollback_steps_executed": activity.rollback.rollback_steps
        }

    def get_runbook(self, runbook_id: str) -> Optional[Runbook]:
        """Get runbook by ID"""
        return self.runbooks.get(runbook_id)

    def list_runbooks(self, category: Optional[str] = None) -> List[Runbook]:
        """List all runbooks, optionally filtered by category"""
        runbooks = list(self.runbooks.values())

        if category:
            runbooks = [rb for rb in runbooks if rb.category == category]

        # Sort by execution count (most used first)
        return sorted(runbooks, key=lambda x: x.execution_count, reverse=True)

    def get_rollback_eligible_count(self) -> int:
        """Get count of activities eligible for rollback"""
        from datetime import timezone
        current_time = datetime.now(timezone.utc)
        count = 0

        for activity in self.activities:
            if activity.rollback.eligible and activity.rollback.expires_at:
                expires_at = activity.rollback.expires_at
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
                if current_time <= expires_at:
                    count += 1

        return count

    def create_activity_from_workflow(
        self,
        workflow_id: str,
        alert_data: Dict[str, Any],
        suggestion: Dict[str, Any],
        execution_result: Dict[str, Any],
        approved_by: str
    ) -> Activity:
        """
        Create an activity record from a completed workflow

        Args:
            workflow_id: Workflow ID
            alert_data: Original alert data
            suggestion: AI suggestion data
            execution_result: Result of execution
            approved_by: User who approved

        Returns:
            Created Activity object
        """
        # Determine activity type based on alert type
        alert_type = alert_data.get("type", "UNKNOWN")
        activity_type_map = {
            "CPU_SPIKE": "alert_fix",
            "MEMORY_SPIKE": "alert_fix",
            "DISK_SPACE": "disk_cleanup",
            "HIGH_LATENCY": "config_change"
        }

        activity_type = activity_type_map.get(alert_type, "alert_fix")

        # Create rollback info
        from datetime import timezone
        current_time = datetime.now(timezone.utc)
        rollback = RollbackInfo(
            eligible=True,
            expires_at=current_time + timedelta(minutes=5),
            window_minutes=5,
            action=f"Revert changes made by {suggestion['recommended_action']['title']}",
            risk_level="low",
            rollback_steps=[
                "Restore previous configuration from backup",
                "Reload affected service",
                "Verify system metrics"
            ]
        )

        # Create activity
        activity = Activity(
            id=f"act-{workflow_id[:8]}",
            type=activity_type,
            title=f"{suggestion['recommended_action']['title']} on {alert_data.get('source', 'system')}",
            description=suggestion['recommended_action'].get('description', ''),
            timestamp=current_time,
            status=ActivityStatus.COMPLETED,
            severity=alert_data.get('severity', 'MEDIUM').lower(),
            workflow_id=workflow_id,
            alert_id=alert_data.get('id'),
            approved_by=approved_by,
            changes_made=execution_result.get('actions_taken', []),
            runbook_used=suggestion.get('runbook_id'),
            rollback=rollback
        )

        # Add to tracking
        self.add_activity(activity)

        return activity
