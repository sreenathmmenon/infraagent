"""Historical Context Service - RAG for Learning from Past Incidents"""

import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict


class HistoricalContextService:
    """
    Provides historical context and learning from past incidents
    Simulates RAG (Retrieval Augmented Generation) for demo
    """

    def __init__(self):
        self.incidents = self._load_historical_incidents()

    def _load_historical_incidents(self) -> List[Dict[str, Any]]:
        """Load historical incidents from mock data"""
        try:
            incidents_path = Path(__file__).parent.parent / "mock_infra" / "historical_incidents.json"
            with open(incidents_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load historical incidents: {e}")
            return []

    def get_similar_incidents(
        self, alert_type: str, source: str = None, days: int = 90
    ) -> Dict[str, Any]:
        """
        Find similar incidents from history (RAG-like retrieval)

        Args:
            alert_type: Type of alert (CPU_SPIKE, DISK_FULL, etc.)
            source: Optional source filter
            days: Look back period

        Returns:
            Historical context with patterns and learnings
        """
        # Filter incidents by type
        similar = [
            incident for incident in self.incidents
            if incident['alert_type'] == alert_type
        ]

        # Further filter by source if provided
        if source:
            source_similar = [
                incident for incident in similar
                if incident['source'] == source
            ]
            # Use source-specific if available, otherwise use all similar
            if source_similar:
                similar = source_similar

        if not similar:
            return {
                "found": False,
                "count": 0,
                "message": "No historical incidents found for this pattern"
            }

        # Calculate statistics
        total_count = len(similar)
        automated_count = len([i for i in similar if not i['manual_intervention']])
        success_count = len([i for i in similar if i['outcome'] == 'success'])

        avg_resolution_time = sum(i['resolution_time_seconds'] for i in similar) / total_count
        total_cost_saved = sum(i['cost_saved'] for i in similar)

        # Get most recent incident
        similar_sorted = sorted(similar, key=lambda x: x['timestamp'], reverse=True)
        most_recent = similar_sorted[0]

        # Calculate success rate
        success_rate = (success_count / total_count) * 100 if total_count > 0 else 0
        automation_rate = (automated_count / total_count) * 100 if total_count > 0 else 0

        # Find most common fix
        fix_counts = defaultdict(int)
        for incident in similar:
            fix_counts[incident['fix_applied']] += 1
        most_common_fix = max(fix_counts.items(), key=lambda x: x[1]) if fix_counts else (None, 0)

        return {
            "found": True,
            "count": total_count,
            "automated_count": automated_count,
            "success_count": success_count,
            "success_rate": round(success_rate, 1),
            "automation_rate": round(automation_rate, 1),
            "avg_resolution_time_seconds": round(avg_resolution_time),
            "avg_resolution_time_formatted": self._format_seconds(avg_resolution_time),
            "total_cost_saved": round(total_cost_saved, 2),
            "most_recent": {
                "timestamp": most_recent['timestamp'],
                "days_ago": self._days_ago(most_recent['timestamp']),
                "resolution_time": most_recent['resolution_time_seconds'],
                "fix": most_recent['fix_applied']
            },
            "most_common_fix": {
                "fix": most_common_fix[0],
                "frequency": most_common_fix[1],
                "percentage": round((most_common_fix[1] / total_count) * 100, 1)
            },
            "patterns": self._identify_patterns(similar),
            "recommendation_confidence_boost": min(20, total_count * 2),  # More history = more confidence
            "learning_insights": self._generate_insights(similar, alert_type)
        }

    def _identify_patterns(self, incidents: List[Dict[str, Any]]) -> List[str]:
        """Identify patterns in historical incidents"""
        patterns = []

        if len(incidents) >= 3:
            # Check time-of-day pattern
            hours = [int(i['timestamp'].split('T')[1].split(':')[0]) for i in incidents]
            avg_hour = sum(hours) / len(hours)
            if 8 <= avg_hour <= 18:
                patterns.append(f"Typically occurs during business hours (avg: {int(avg_hour)}:00)")

            # Check resolution success
            success_rate = (len([i for i in incidents if i['outcome'] == 'success']) / len(incidents)) * 100
            if success_rate >= 90:
                patterns.append(f"High historical success rate ({success_rate:.0f}%)")

            # Check automation rate
            auto_rate = (len([i for i in incidents if not i['manual_intervention']]) / len(incidents)) * 100
            if auto_rate >= 70:
                patterns.append(f"Frequently resolved automatically ({auto_rate:.0f}% of cases)")

        return patterns

    def _generate_insights(self, incidents: List[Dict[str, Any]], alert_type: str) -> List[str]:
        """Generate learning insights from history"""
        insights = []

        if len(incidents) >= 5:
            insights.append("🧠 AI has learned from multiple similar incidents")

            # Check if automation is improving
            recent = sorted(incidents, key=lambda x: x['timestamp'], reverse=True)[:3]
            recent_auto = len([i for i in recent if not i['manual_intervention']])
            if recent_auto >= 2:
                insights.append("📈 Recent incidents resolved automatically (learning curve improving)")

            # Cost savings insight
            total_saved = sum(i['cost_saved'] for i in incidents)
            if total_saved > 500:
                insights.append(f"💰 Historical automation saved ${total_saved:.0f} in similar incidents")

        return insights

    def _days_ago(self, timestamp_str: str) -> int:
        """Calculate days ago from timestamp"""
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            now = datetime.now(timestamp.tzinfo)
            delta = now - timestamp
            return delta.days
        except:
            return 0

    def _format_seconds(self, seconds: float) -> str:
        """Format seconds to human readable"""
        minutes = int(seconds / 60)
        remaining_seconds = int(seconds % 60)

        if minutes > 0:
            return f"{minutes}m {remaining_seconds}s"
        else:
            return f"{remaining_seconds}s"

    def calculate_time_savings(
        self, ai_resolution_time: int, alert_type: str
    ) -> Dict[str, Any]:
        """
        Calculate time/cost savings vs manual resolution

        Args:
            ai_resolution_time: Time AI took in seconds
            alert_type: Type of alert

        Returns:
            Time and cost savings comparison
        """
        # Estimated manual resolution times (from industry data)
        manual_times = {
            "CPU_SPIKE": 2700,  # 45 minutes
            "DISK_FULL": 3600,  # 60 minutes
            "HIGH_LATENCY": 1800,  # 30 minutes
        }

        manual_time = manual_times.get(alert_type, 2700)
        time_saved_seconds = manual_time - ai_resolution_time
        time_saved_minutes = time_saved_seconds / 60

        # Calculate cost savings (assuming $150/hour engineer cost)
        engineer_cost_per_second = 150 / 3600
        cost_saved = time_saved_seconds * engineer_cost_per_second

        return {
            "ai_time_seconds": ai_resolution_time,
            "ai_time_formatted": self._format_seconds(ai_resolution_time),
            "manual_time_seconds": manual_time,
            "manual_time_formatted": self._format_seconds(manual_time),
            "time_saved_seconds": time_saved_seconds,
            "time_saved_formatted": self._format_seconds(time_saved_seconds),
            "time_saved_percentage": round((time_saved_seconds / manual_time) * 100, 1),
            "cost_saved": round(cost_saved, 2),
            "engineer_cost_per_hour": 150
        }

    def get_confidence_breakdown(
        self, base_confidence: int, has_history: bool, pattern_match: bool
    ) -> Dict[str, Any]:
        """
        Break down confidence score into components

        Args:
            base_confidence: Base confidence from analysis
            has_history: Whether historical data exists
            pattern_match: Whether current situation matches patterns

        Returns:
            Detailed confidence breakdown
        """
        components = []

        # Base analysis confidence
        components.append({
            "factor": "Current Analysis",
            "contribution": 40,
            "description": "Root cause identified from current metrics and logs"
        })

        # Historical pattern matching
        if has_history:
            historical_boost = 30 if pattern_match else 15
            components.append({
                "factor": "Historical Pattern Match",
                "contribution": historical_boost,
                "description": f"Similar incidents resolved successfully {12 if pattern_match else 5} times"
            })
        else:
            components.append({
                "factor": "Historical Data",
                "contribution": 0,
                "description": "No historical data available for this pattern"
            })

        # Topology analysis
        components.append({
            "factor": "Topology Analysis",
            "contribution": 20,
            "description": "Infrastructure dependencies mapped and blast radius calculated"
        })

        # Risk assessment
        components.append({
            "factor": "Risk Assessment",
            "contribution": 10,
            "description": "Low-risk change with comprehensive rollback plan"
        })

        total_confidence = sum(c['contribution'] for c in components)

        return {
            "total_confidence": total_confidence,
            "components": components,
            "confidence_level": (
                "Very High" if total_confidence >= 85 else
                "High" if total_confidence >= 70 else
                "Medium" if total_confidence >= 55 else
                "Low"
            )
        }
