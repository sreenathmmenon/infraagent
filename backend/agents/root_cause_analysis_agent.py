"""
Root Cause Analysis Agent - LLM-powered deep analysis
The AI brain that explains WHAT happened, WHY, and HOW to fix it

This is what makes InfraAgent intelligent for L2/L3 engineers
"""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logger = logging.getLogger(__name__)


class RootCauseAnalysisAgent:
    """
    Uses Claude AI to perform deep root cause analysis

    Features:
    - Analyzes correlated logs and explains root cause
    - Generates human-readable summaries for L2/L3 engineers
    - Suggests specific remediation actions
    - Builds timeline narratives
    """

    def __init__(self):
        self.client = None

        if ANTHROPIC_AVAILABLE:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if api_key:
                self.client = Anthropic(api_key=api_key)
                print("\n" + "🎉"*40)
                print("✅ ROOT CAUSE ANALYSIS AGENT: CLAUDE AI INITIALIZED")
                print("🎉"*40 + "\n")
                logger.info("Root Cause Analysis Agent initialized with Claude AI")
            else:
                print("\n" + "⚠️ "*40)
                print("❌ ANTHROPIC_API_KEY NOT FOUND - USING MOCK AI")
                print("⚠️ "*40 + "\n")
                logger.warning("ANTHROPIC_API_KEY not found - AI analysis will return mock results")
        else:
            print("\n⚠️  Anthropic SDK not available - AI analysis will return mock results\n")
            logger.warning("Anthropic SDK not available - AI analysis will return mock results")

    def analyze_incident(
        self,
        incident: Dict[str, Any],
        include_remediation: bool = True
    ) -> Dict[str, Any]:
        """
        Perform deep root cause analysis on an incident

        Args:
            incident: Incident data from CorrelationEngine
            include_remediation: Whether to include fix suggestions

        Returns:
            {
                'root_cause': str,  # What actually failed
                'explanation': str,  # Why it failed
                'impact': str,  # What was affected
                'timeline_narrative': str,  # Story of what happened
                'remediation': {
                    'immediate_actions': [str],
                    'long_term_fixes': [str],
                    'specific_commands': [str]
                },
                'confidence': float,  # 0-1
                'related_documentation': [str]
            }
        """
        logger.info(f"Analyzing incident #{incident.get('incident_id', 'unknown')}")

        if not self.client:
            return self._mock_analysis(incident)

        # Prepare context for LLM
        context = self._prepare_context(incident)

        # Call Claude
        try:
            analysis = self._call_claude_for_analysis(context, include_remediation)
            return analysis
        except Exception as e:
            logger.error(f"Error calling Claude API: {e}")
            return self._mock_analysis(incident)

    def answer_natural_language_query(
        self,
        query: str,
        logs: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Answer natural language questions about logs

        Examples:
        - "Why are VMs failing to boot?"
        - "What caused the authentication errors?"
        - "Is the database connection pool exhausted?"

        Returns:
            {
                'answer': str,  # Direct answer to the question
                'relevant_logs': [Dict],  # Logs that support the answer
                'suggestions': [str],  # What to check next
                'confidence': float
            }
        """
        logger.info(f"Answering NL query: {query}")

        if not self.client:
            return self._mock_nl_answer(query, logs)

        # Prepare context
        nl_context = self._prepare_nl_context(query, logs, context)

        try:
            answer = self._call_claude_for_nl_query(nl_context)
            return answer
        except Exception as e:
            logger.error(f"Error calling Claude API: {e}")
            return self._mock_nl_answer(query, logs)

    def suggest_remediations(
        self,
        incident: Dict[str, Any],
        system_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate specific remediation steps

        Returns:
            {
                'immediate_actions': [
                    {
                        'action': str,
                        'command': str,  # Specific command to run
                        'rationale': str
                    }
                ],
                'long_term_fixes': [
                    {
                        'action': str,
                        'file': str,  # File to modify
                        'line': int,  # Line number
                        'change': str  # What to change
                    }
                ],
                'prevention': [str]  # How to prevent this in future
            }
        """
        logger.info("Generating remediation suggestions")

        if not self.client:
            return self._mock_remediation(incident)

        context = self._prepare_remediation_context(incident, system_info)

        try:
            remediation = self._call_claude_for_remediation(context)
            return remediation
        except Exception as e:
            logger.error(f"Error calling Claude API: {e}")
            return self._mock_remediation(incident)

    def _prepare_context(self, incident: Dict[str, Any]) -> str:
        """Prepare incident context for LLM"""
        logs = incident.get('logs', [])
        sorted_logs = sorted(logs, key=lambda l: l.get('timestamp', 0))

        # Format timeline
        timeline_text = "INCIDENT TIMELINE:\n"
        for i, log in enumerate(sorted_logs[:20]):  # Limit to 20 most important logs
            timestamp = datetime.fromtimestamp(log['timestamp']).strftime('%H:%M:%S')
            timeline_text += f"[{timestamp}] {log['service']} - {log['level']}: {log['message']}\n"

        # Add metadata
        context = f"""
INCIDENT ANALYSIS REQUEST

Services Affected: {', '.join(incident.get('affected_services', []))}
Severity: {incident.get('severity', 'UNKNOWN')}
Duration: {incident.get('duration_seconds', 0):.1f} seconds
Total Logs: {len(logs)}

{timeline_text}

TASK: Analyze this incident and identify:
1. ROOT CAUSE: What actually failed (be specific)
2. EXPLANATION: Why did this failure occur
3. IMPACT: What systems/users were affected
4. TIMELINE NARRATIVE: Tell the story of this incident in 2-3 sentences
5. REMEDIATION: Immediate actions and long-term fixes

Focus on actionable insights for an L2/L3 support engineer on-call.
"""
        return context

    def _prepare_nl_context(
        self,
        query: str,
        logs: List[Dict[str, Any]],
        extra_context: Optional[Dict[str, Any]]
    ) -> str:
        """Prepare context for natural language query"""

        # Format recent logs
        sorted_logs = sorted(logs, key=lambda l: l.get('timestamp', 0), reverse=True)[:30]

        logs_text = "RECENT LOGS:\n"
        for log in sorted_logs:
            timestamp = datetime.fromtimestamp(log['timestamp']).strftime('%H:%M:%S')
            logs_text += f"[{timestamp}] {log['service']} - {log['level']}: {log['message'][:150]}\n"

        context = f"""
NATURAL LANGUAGE QUERY

USER QUESTION: {query}

{logs_text}

TASK: Answer the user's question based on the logs above.
- Be direct and specific
- Reference exact log entries if relevant
- Suggest what to investigate next
- If you're not certain, say so

Respond in a format that an L2/L3 engineer can act on immediately.
"""
        return context

    def _prepare_remediation_context(
        self,
        incident: Dict[str, Any],
        system_info: Optional[Dict[str, Any]]
    ) -> str:
        """Prepare context for remediation suggestions"""

        root_cause_candidates = incident.get('root_cause_candidates', [])

        cause_text = "LIKELY ROOT CAUSES:\n"
        for candidate in root_cause_candidates[:3]:
            log = candidate.get('log', {})
            cause_text += f"- {log.get('service')}: {log.get('message')}\n"
            cause_text += f"  Reason: {candidate.get('reason')}\n"

        context = f"""
REMEDIATION GENERATION REQUEST

{cause_text}

Services: {', '.join(incident.get('affected_services', []))}

TASK: Provide specific, actionable remediation steps:

1. IMMEDIATE ACTIONS (to stop the bleeding):
   - Include exact commands to run
   - Focus on service recovery

2. LONG-TERM FIXES (to prevent recurrence):
   - Specific config file changes
   - Code modifications with file:line references
   - Infrastructure improvements

3. PREVENTION:
   - Monitoring to add
   - Alerts to configure

Be specific and actionable for an L2/L3 engineer managing production systems.
"""
        return context

    def _call_claude_for_analysis(
        self,
        context: str,
        include_remediation: bool
    ) -> Dict[str, Any]:
        """Call Claude API for incident analysis"""

        message = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            messages=[
                {"role": "user", "content": context}
            ]
        )

        response_text = message.content[0].text

        # Parse response (simplified - in production, use structured output)
        return {
            'root_cause': self._extract_section(response_text, 'ROOT CAUSE'),
            'explanation': self._extract_section(response_text, 'EXPLANATION'),
            'impact': self._extract_section(response_text, 'IMPACT'),
            'timeline_narrative': self._extract_section(response_text, 'TIMELINE NARRATIVE'),
            'remediation': self._parse_remediation(response_text),
            'confidence': 0.85,
            'raw_analysis': response_text
        }

    def _call_claude_for_nl_query(self, context: str) -> Dict[str, Any]:
        """Call Claude API for natural language query"""

        # Print to console so user can see
        print("\n" + "="*80)
        print("🤖 CALLING REAL CLAUDE API FOR NATURAL LANGUAGE QUERY")
        print("="*80)
        print(f"Query context length: {len(context)} chars")
        print("Sending request to Anthropic API...")

        message = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": context}
            ]
        )

        response_text = message.content[0].text

        print("✅ CLAUDE API RESPONSE RECEIVED")
        print(f"Response length: {len(response_text)} chars")
        print(f"First 150 chars: {response_text[:150]}")
        print("="*80 + "\n")

        return {
            'answer': response_text,
            'confidence': 0.8,
            'suggestions': []  # Could parse from response
        }

    def _call_claude_for_remediation(self, context: str) -> Dict[str, Any]:
        """Call Claude API for remediation suggestions"""

        message = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1536,
            messages=[
                {"role": "user", "content": context}
            ]
        )

        response_text = message.content[0].text

        return self._parse_remediation(response_text)

    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract a section from LLM response"""
        import re

        # Try to find section
        pattern = rf"{section_name}:?\s*(.+?)(?=\n[A-Z\s]+:|$)"
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)

        if match:
            return match.group(1).strip()

        return "Analysis in progress..."

    def _parse_remediation(self, text: str) -> Dict[str, Any]:
        """Parse remediation section from response"""
        # Simplified parsing - in production, use structured output
        return {
            'immediate_actions': self._extract_bullet_points(text, 'IMMEDIATE'),
            'long_term_fixes': self._extract_bullet_points(text, 'LONG-TERM'),
            'prevention': self._extract_bullet_points(text, 'PREVENTION')
        }

    def _extract_bullet_points(self, text: str, section: str) -> List[str]:
        """Extract bullet points from a section"""
        import re

        # Find section
        pattern = rf"{section}[^:]*:(.+?)(?=\n[A-Z\-\s]+:|$)"
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)

        if not match:
            return []

        section_text = match.group(1)

        # Extract bullet points (lines starting with -, *, or numbers)
        bullets = re.findall(r'[-*\d]+\.?\s+(.+)', section_text)

        return [b.strip() for b in bullets if b.strip()]

    def _mock_analysis(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Mock analysis when API is not available"""

        services = incident.get('affected_services', [])
        logs = incident.get('logs', [])

        # Find first error
        first_error = next(
            (log for log in sorted(logs, key=lambda l: l['timestamp'])
             if log['level'] in ['ERROR', 'CRITICAL']),
            None
        )

        root_cause = "Service communication failure"
        if first_error:
            if 'auth' in first_error['message'].lower():
                root_cause = "Authentication failure"
            elif 'connect' in first_error['message'].lower():
                root_cause = "Connection failure"
            elif 'timeout' in first_error['message'].lower():
                root_cause = "Timeout error"

        return {
            'root_cause': root_cause,
            'explanation': f"The incident began with an error in {first_error['service'] if first_error else 'unknown service'}, which cascaded across {len(services)} services.",
            'impact': f"{len(services)} services affected, {len(logs)} error logs generated",
            'timeline_narrative': f"At {datetime.fromtimestamp(incident['start_time']).strftime('%H:%M:%S')}, an error occurred and propagated across the system over {incident['duration_seconds']:.0f} seconds.",
            'remediation': {
                'immediate_actions': [
                    'Restart affected services',
                    'Check network connectivity',
                    'Verify authentication tokens'
                ],
                'long_term_fixes': [
                    'Add retry logic with exponential backoff',
                    'Implement circuit breakers',
                    'Increase connection pool size'
                ],
                'prevention': [
                    'Add monitoring for service dependencies',
                    'Set up alerts for connection failures',
                    'Implement health checks'
                ]
            },
            'confidence': 0.7,
            'note': 'Mock analysis - ANTHROPIC_API_KEY not configured'
        }

    def _mock_nl_answer(self, query: str, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Mock NL answer when API is not available"""

        print("\n" + "⚠️ "*40)
        print("🤖 USING MOCK AI (No Claude API)")
        print(f"Query: {query}")
        print("⚠️ "*40 + "\n")

        error_count = sum(1 for log in logs if log['level'] == 'ERROR')

        return {
            'answer': f"Based on {len(logs)} logs analyzed, {error_count} errors detected. The most common pattern appears to be service communication issues. Check network connectivity and authentication.",
            'confidence': 0.6,
            'suggestions': [
                'Review recent configuration changes',
                'Check service health endpoints',
                'Verify network policies'
            ],
            'note': 'Mock answer - ANTHROPIC_API_KEY not configured'
        }

    def _mock_remediation(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Mock remediation when API is not available"""

        return {
            'immediate_actions': [
                {'action': 'Restart affected services', 'command': 'systemctl restart service-name', 'rationale': 'Quick recovery'},
                {'action': 'Check logs', 'command': 'journalctl -u service-name -n 100', 'rationale': 'Gather more context'}
            ],
            'long_term_fixes': [
                {'action': 'Increase timeout', 'file': '/etc/service/config.yaml', 'line': 42, 'change': 'timeout: 30s → 60s'},
                {'action': 'Add retry logic', 'file': 'src/client.py', 'line': 123, 'change': 'Add exponential backoff'}
            ],
            'prevention': [
                'Add monitoring for response times',
                'Set up alerts for high error rates',
                'Implement circuit breakers'
            ],
            'note': 'Mock remediation - ANTHROPIC_API_KEY not configured'
        }


# Singleton instance
_rca_instance = None


def get_root_cause_analysis_agent() -> RootCauseAnalysisAgent:
    """Get singleton RootCauseAnalysisAgent instance"""
    global _rca_instance
    if _rca_instance is None:
        _rca_instance = RootCauseAnalysisAgent()
    return _rca_instance
