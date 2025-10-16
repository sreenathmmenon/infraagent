"""AI-powered Post-Mortem Report Generator"""

import os
from typing import Dict, Any, Optional

# Optional import - works without AI
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    Anthropic = None


class PostMortemGenerator:
    """Generates incident post-mortem reports using AI"""

    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if ANTHROPIC_AVAILABLE and api_key and Anthropic:
            self.client = Anthropic(api_key=api_key)
        else:
            self.client = None
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

    async def generate_report(self, activity: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate AI post-mortem report for a completed activity

        Args:
            activity: Completed activity data

        Returns:
            Post-mortem report with timeline, root cause, impact, lessons learned
        """
        if not self.client:
            return self._generate_mock_report(activity)

        try:
            prompt = f"""Generate a professional incident post-mortem report for this infrastructure remediation:

INCIDENT DETAILS:
- Title: {activity.get('title', 'Unknown')}
- Severity: {activity.get('severity', 'Unknown')}
- Timestamp: {activity.get('timestamp', 'Unknown')}
- Status: {activity.get('status', 'Unknown')}

CHANGES MADE:
{self._format_changes(activity.get('changes_made', []))}

Generate a JSON response with this structure:
{{
  "incident_id": "INC-{activity.get('id', 'unknown')[:8]}",
  "summary": "2-3 sentence executive summary",
  "timeline": [
    {{"time": "HH:MM", "event": "Event description"}},
    {{"time": "HH:MM", "event": "Event description"}}
  ],
  "root_cause": {{
    "category": "Configuration|Resource|Network|Application",
    "description": "Detailed root cause explanation",
    "contributing_factors": ["factor 1", "factor 2"]
  }},
  "impact": {{
    "duration": "X minutes",
    "services_affected": ["service1"],
    "user_impact": "Description of user impact",
    "estimated_requests_affected": "number or N/A"
  }},
  "resolution": {{
    "actions_taken": ["action 1", "action 2"],
    "time_to_resolve": "X minutes",
    "verification": "How we verified the fix"
  }},
  "lessons_learned": [
    {{"what_went_well": "positive aspect"}},
    {{"what_could_improve": "improvement area"}},
    {{"action_item": "specific follow-up action"}}
  ],
  "preventive_measures": [
    "measure 1",
    "measure 2"
  ]
}}

Be professional, specific, and actionable."""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Extract JSON from response
            import json
            content = response.content[0].text
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            report = json.loads(content.strip())
            report["generated_by"] = "AI"
            return report

        except Exception as e:
            print(f"AI post-mortem generation error: {e}")
            return self._generate_mock_report(activity)

    def _format_changes(self, changes: list) -> str:
        """Format changes list for prompt"""
        if not changes:
            return "No changes recorded"

        formatted = []
        for change in changes:
            if isinstance(change, dict):
                action = change.get('action', '')
                detail = change.get('detail', '')
                formatted.append(f"- {action}: {detail}")
            else:
                formatted.append(f"- {change}")

        return "\n".join(formatted)

    def _generate_mock_report(self, activity: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback mock report when AI is unavailable"""
        return {
            "incident_id": f"INC-{activity.get('id', 'unknown')[:8]}",
            "summary": f"Infrastructure incident resolved: {activity.get('title', 'Unknown incident')}. Automated remediation successfully applied with human approval.",
            "timeline": [
                {"time": "09:30", "event": "Alert detected - High resource utilization"},
                {"time": "09:31", "event": "AI analysis completed - Root cause identified"},
                {"time": "09:32", "event": "Remediation plan approved by operator"},
                {"time": "09:33", "event": "Fix applied successfully"},
                {"time": "09:35", "event": "System verified healthy"}
            ],
            "root_cause": {
                "category": "Configuration",
                "description": "Resource limits were insufficient for current traffic patterns",
                "contributing_factors": [
                    "Traffic spike during peak hours",
                    "Configuration not updated since initial deployment"
                ]
            },
            "impact": {
                "duration": "5 minutes",
                "services_affected": [activity.get('title', 'Service')],
                "user_impact": "Elevated response times during incident window",
                "estimated_requests_affected": "~2,500"
            },
            "resolution": {
                "actions_taken": [
                    change.get('action', str(change)) if isinstance(change, dict) else str(change)
                    for change in activity.get('changes_made', [])[:3]
                ],
                "time_to_resolve": "3 minutes",
                "verification": "Metrics returned to normal thresholds, no error rate increase"
            },
            "lessons_learned": [
                {"what_went_well": "Automated detection and AI analysis reduced mean time to resolution"},
                {"what_could_improve": "Proactive monitoring could have caught this before user impact"},
                {"action_item": "Review and update resource limits across all production services"}
            ],
            "preventive_measures": [
                "Implement automated scaling policies",
                "Schedule quarterly configuration reviews",
                "Set up predictive alerts for resource trends"
            ],
            "generated_by": "rule-based"
        }
