"""Alert Agent - Analyzes infrastructure alerts"""

from typing import Dict, Any
from datetime import datetime, timedelta
import json


class AlertAgent:
    """
    Analyzes infrastructure alerts to determine:
    - Root cause likelihood
    - Business impact
    - Urgency level
    """

    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.name = "Alert Agent"

    async def analyze(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze an alert and determine severity and context

        Args:
            alert_data: Alert information from monitoring system

        Returns:
            Analysis with root cause, impact, and urgency
        """
        alert_type = alert_data.get("type")
        severity = alert_data.get("severity")
        source = alert_data.get("source")
        metric_value = alert_data.get("metric_value")

        # Check historical patterns (mock for demo)
        historical_context = self._check_historical_patterns(alert_type, source)

        # Calculate impact score
        impact_score = self._calculate_impact_score(severity, source, metric_value)

        # Determine root cause likelihood based on alert type
        root_cause_analysis = self._analyze_root_cause(
            alert_type, metric_value, historical_context
        )

        analysis = {
            "agent": "alert_agent",
            "timestamp": datetime.utcnow().isoformat(),
            "duration": "1.2s",
            "completed": True,
            "alert_id": alert_data.get("id"),
            "root_cause": root_cause_analysis["likely_cause"],
            "root_cause_confidence": root_cause_analysis["confidence"],
            "business_impact": self._assess_business_impact(alert_type, source),
            "urgency_level": self._determine_urgency(severity, impact_score),
            "impact_score": impact_score,
            "historical_occurrences": historical_context["occurrence_count"],
            "last_occurrence": historical_context["last_seen"],
            "typical_resolution_time": historical_context["avg_resolution_time"],
            "recommendations": root_cause_analysis["recommendations"]
        }

        return analysis

    def _check_historical_patterns(
        self, alert_type: str, source: str
    ) -> Dict[str, Any]:
        """Check if this alert has occurred before (mock data for demo)"""
        # In production, would query time-series database
        patterns = {
            "CPU_SPIKE": {
                "occurrence_count": 12,
                "last_seen": "2025-10-14T15:30:00Z",
                "avg_resolution_time": "8 minutes"
            },
            "DISK_FULL": {
                "occurrence_count": 5,
                "last_seen": "2025-10-10T09:15:00Z",
                "avg_resolution_time": "15 minutes"
            },
            "HIGH_LATENCY": {
                "occurrence_count": 8,
                "last_seen": "2025-10-15T18:00:00Z",
                "avg_resolution_time": "5 minutes"
            }
        }
        return patterns.get(alert_type, {
            "occurrence_count": 0,
            "last_seen": None,
            "avg_resolution_time": "unknown"
        })

    def _calculate_impact_score(
        self, severity: str, source: str, metric_value: float
    ) -> int:
        """Calculate impact score (0-100)"""
        score = 0

        # Severity contribution
        severity_scores = {
            "CRITICAL": 40,
            "HIGH": 30,
            "MEDIUM": 20,
            "LOW": 10
        }
        score += severity_scores.get(severity, 10)

        # Source criticality contribution
        if "db" in source.lower():
            score += 30  # Database is critical
        elif "api" in source.lower():
            score += 25
        elif "web" in source.lower():
            score += 20
        else:
            score += 10

        # Metric value contribution (normalized)
        if metric_value > 90:
            score += 30
        elif metric_value > 80:
            score += 20
        elif metric_value > 70:
            score += 10

        return min(score, 100)

    def _analyze_root_cause(
        self, alert_type: str, metric_value: float, historical: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Determine likely root cause"""

        root_causes = {
            "CPU_SPIKE": {
                "likely_cause": "High request volume overwhelming web server worker processes",
                "confidence": 87,
                "reasoning": [
                    f"CPU at {metric_value}% exceeds capacity of current worker configuration",
                    "Traffic pattern suggests legitimate load increase, not attack",
                    f"Similar spikes occurred {historical['occurrence_count']} times in past 30 days"
                ],
                "recommendations": [
                    "Increase max_connections to handle burst traffic",
                    "Consider horizontal scaling if pattern continues",
                    "Review application code for inefficient queries"
                ]
            },
            "DISK_FULL": {
                "likely_cause": "Log files accumulating beyond retention policy limits",
                "confidence": 92,
                "reasoning": [
                    f"Disk usage at {metric_value}% on /var/log partition",
                    "Log retention set to 90 days, industry standard is 30 days",
                    "No evidence of data growth in application databases"
                ],
                "recommendations": [
                    "Archive logs older than 30 days to cold storage",
                    "Implement log rotation with compression",
                    "Set up automated cleanup job"
                ]
            },
            "HIGH_LATENCY": {
                "likely_cause": "Network path degradation on primary route",
                "confidence": 78,
                "reasoning": [
                    f"Average latency {metric_value}ms, normal baseline is 45ms",
                    "Primary network path showing degraded status",
                    "Backup path in us-east-1b performing normally (30ms)"
                ],
                "recommendations": [
                    "Switch to backup network path immediately",
                    "Monitor primary path for recovery",
                    "Investigate ISP or routing issues on primary path"
                ]
            }
        }

        return root_causes.get(alert_type, {
            "likely_cause": "Unknown - requires manual investigation",
            "confidence": 50,
            "reasoning": ["Insufficient data for automated analysis"],
            "recommendations": ["Escalate to on-call engineer"]
        })

    def _assess_business_impact(self, alert_type: str, source: str) -> str:
        """Assess business impact"""
        if "db" in source.lower():
            return "HIGH - Database issues affect all services and can cause data loss"
        elif "api" in source.lower():
            return "HIGH - API gateway issues affect customer-facing applications"
        elif alert_type == "HIGH_LATENCY":
            return "MEDIUM - Increased latency degrades user experience but service remains available"
        elif alert_type == "CPU_SPIKE":
            return "MEDIUM - Performance degradation, potential request failures if sustained"
        else:
            return "LOW - Isolated issue with minimal customer impact"

    def _determine_urgency(self, severity: str, impact_score: int) -> str:
        """Determine urgency level"""
        if severity == "CRITICAL" or impact_score >= 80:
            return "IMMEDIATE - Requires action within 5 minutes"
        elif severity == "HIGH" or impact_score >= 60:
            return "HIGH - Requires action within 15 minutes"
        elif severity == "MEDIUM" or impact_score >= 40:
            return "MEDIUM - Requires action within 1 hour"
        else:
            return "LOW - Can be scheduled during business hours"
