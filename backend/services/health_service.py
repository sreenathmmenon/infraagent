"""Health Dashboard Service"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional


class HealthDashboardService:
    """Manages infrastructure health dashboard data"""

    def __init__(self):
        self.health_data: Dict[str, Any] = {}
        self._load_mock_data()

    def _load_mock_data(self):
        """Load mock health dashboard data"""
        base_path = Path(__file__).parent.parent / "mock_infra"

        try:
            health_path = base_path / "health_dashboard.json"
            with open(health_path, 'r') as f:
                self.health_data = json.load(f)
        except Exception as e:
            print(f"Error loading health dashboard: {e}")
            self.health_data = self._get_fallback_data()

    def _get_fallback_data(self) -> Dict[str, Any]:
        """Fallback data if file loading fails"""
        return {
            "overall_health": {
                "status": "healthy",
                "score": 95,
                "services_total": 0,
                "services_healthy": 0
            },
            "services": [],
            "aggregate_metrics": {}
        }

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get complete dashboard data"""
        return self.health_data

    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall health summary"""
        return self.health_data.get("overall_health", {})

    def get_services(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get services list, optionally filtered by status

        Args:
            status_filter: Filter by status (healthy, degraded, critical)

        Returns:
            List of services
        """
        services = self.health_data.get("services", [])

        if status_filter:
            services = [s for s in services if s.get("status") == status_filter]

        return services

    def get_service(self, service_id: str) -> Optional[Dict[str, Any]]:
        """Get specific service by ID"""
        services = self.health_data.get("services", [])

        for service in services:
            if service.get("id") == service_id:
                return service

        return None

    def get_critical_services(self) -> List[Dict[str, Any]]:
        """Get services in critical state"""
        return self.get_services(status_filter="critical")

    def get_degraded_services(self) -> List[Dict[str, Any]]:
        """Get services in degraded state"""
        return self.get_services(status_filter="degraded")

    def get_cost_metrics(self) -> Dict[str, Any]:
        """Get cost optimization metrics"""
        return self.health_data.get("cost_metrics", {})

    def get_security_summary(self) -> Dict[str, Any]:
        """Get security summary"""
        return self.health_data.get("security_summary", {})

    def get_compliance_status(self) -> Dict[str, Any]:
        """Get compliance status"""
        return self.health_data.get("compliance_status", {})

    def update_service_status(self, service_id: str, new_status: str, alert_message: Optional[str] = None):
        """
        Update service status (for demo purposes)

        Args:
            service_id: Service ID
            new_status: New status (healthy, degraded, critical)
            alert_message: Optional alert message
        """
        service = self.get_service(service_id)

        if service:
            service["status"] = new_status
            if alert_message:
                service["active_alert"] = alert_message
            elif "active_alert" in service:
                del service["active_alert"]

            # Update overall health counts
            self._recalculate_overall_health()

    def _recalculate_overall_health(self):
        """Recalculate overall health metrics"""
        services = self.health_data.get("services", [])

        healthy = sum(1 for s in services if s.get("status") == "healthy")
        degraded = sum(1 for s in services if s.get("status") == "degraded")
        critical = sum(1 for s in services if s.get("status") == "critical")

        total = len(services)

        # Calculate health score (0-100)
        if total > 0:
            score = int((healthy * 100 + degraded * 50 + critical * 0) / total)
        else:
            score = 100

        # Determine overall status
        if critical > 0:
            status = "critical"
        elif degraded > 0:
            status = "degraded"
        else:
            status = "healthy"

        overall = self.health_data.get("overall_health", {})
        overall.update({
            "status": status,
            "score": score,
            "services_total": total,
            "services_healthy": healthy,
            "services_degraded": degraded,
            "services_critical": critical
        })
