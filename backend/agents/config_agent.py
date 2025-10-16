"""Config Agent - Suggests fixes with confidence scores"""

from typing import Dict, Any, List


class ConfigAgent:
    """
    Suggests configuration fixes based on:
    - Alert analysis
    - Topology context
    - Best practices
    """

    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.name = "Config Agent"

    async def suggest_fix(
        self, analysis: Dict[str, Any], topology: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Suggest fix based on analysis and topology

        Args:
            analysis: Analysis from Alert Agent
            topology: Topology context from Topology Agent

        Returns:
            Suggested fix with confidence score and alternatives
        """

        alert_data = analysis.get("alert_id", "")
        root_cause = analysis.get("root_cause", "")

        # Determine fix based on root cause
        if "CPU" in str(analysis) or "worker" in root_cause.lower():
            suggestion = self._suggest_cpu_fix(analysis, topology)
        elif "DISK" in str(analysis) or "log" in root_cause.lower():
            suggestion = self._suggest_disk_fix(analysis, topology)
        elif "LATENCY" in str(analysis) or "network" in root_cause.lower():
            suggestion = self._suggest_latency_fix(analysis, topology)
        else:
            suggestion = self._suggest_generic_fix(analysis, topology)

        # Add execution metadata
        suggestion.update({
            "agent": "config_agent",
            "timestamp": "2025-10-16T09:30:04Z",
            "duration": "1.5s",
            "completed": True
        })

        return suggestion

    def _suggest_cpu_fix(
        self, analysis: Dict[str, Any], topology: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Suggest fix for CPU spike issues"""

        affected_server_id = topology["affected_server"]["id"]

        return {
            "runbook_id": "cpu-spike-mitigation",
            "recommended_action": {
                "title": "Scale Web Server Configuration",
                "description": "Increase max_connections to handle current traffic load and prevent request queuing",
                "type": "config_change",
                "target": affected_server_id
            },
            "confidence": 87,
            "confidence_reasoning": [
                "CPU spike pattern matches traffic surge (not memory leak)",
                f"Similar fix resolved {analysis.get('historical_occurrences', 0)} previous incidents",
                "Current config below industry standard for this server class",
                "No signs of malicious traffic or DDoS attack"
            ],
            "config_changes": {
                "file": "/etc/nginx/nginx.conf",
                "section": "http",
                "changes": [
                    {
                        "parameter": "worker_connections",
                        "current_value": "1000",
                        "new_value": "1500",
                        "justification": "Increase capacity by 50% to handle traffic peaks"
                    },
                    {
                        "parameter": "keepalive_timeout",
                        "current_value": "30",
                        "new_value": "45",
                        "justification": "Allow more time for keep-alive connections"
                    }
                ]
            },
            "config_before": """http {
    worker_connections 1000;
    keepalive_timeout 30;
    client_max_body_size 10M;
}""",
            "config_after": """http {
    worker_connections 1500;
    keepalive_timeout 45;
    client_max_body_size 10M;
}""",
            "expected_outcome": {
                "metric": "CPU utilization",
                "current": "95%",
                "expected": "65-75%",
                "timeline": "2-3 minutes after application"
            },
            "alternatives": [
                {
                    "title": "Horizontal Scaling",
                    "description": "Add 2 additional web servers behind load balancer",
                    "confidence": 92,
                    "effort": "HIGH",
                    "timeline": "15-20 minutes"
                },
                {
                    "title": "Rate Limiting",
                    "description": "Implement rate limiting to prevent traffic spikes",
                    "confidence": 78,
                    "effort": "MEDIUM",
                    "timeline": "5-10 minutes",
                    "caveat": "May impact legitimate users during high traffic"
                }
            ],
            "rollback_plan": [
                "1. Monitor CPU utilization for 2 minutes after change",
                "2. If CPU doesn't decrease, revert to worker_connections=1000",
                "3. Automatic rollback triggered if error rate increases >5%",
                "4. Configuration backup stored at /etc/nginx/nginx.conf.backup",
                "5. Rollback command: sudo cp /etc/nginx/nginx.conf.backup /etc/nginx/nginx.conf && sudo systemctl reload nginx"
            ],
            "risk_assessment": {
                "level": "LOW",
                "factors": [
                    "Configuration change is non-destructive",
                    "Can be reverted with nginx reload (no restart required)",
                    "Similar changes applied successfully in past",
                    "No impact on data or user sessions"
                ]
            },
            "compliance_notes": "Configuration change logged for SOC2 audit trail"
        }

    def _suggest_disk_fix(
        self, analysis: Dict[str, Any], topology: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Suggest fix for disk space issues"""

        affected_server_id = topology["affected_server"]["id"]

        return {
            "runbook_id": "disk-space-recovery",
            "recommended_action": {
                "title": "Archive and Compress Old Logs",
                "description": "Move logs older than 30 days to compressed archive storage",
                "type": "cleanup",
                "target": affected_server_id
            },
            "confidence": 92,
            "confidence_reasoning": [
                "Log partition at 97% capacity, other partitions normal",
                "Log files older than 30 days consuming 45GB",
                "No application database growth detected",
                "Industry standard is 30-day retention for non-compliance logs"
            ],
            "config_changes": {
                "action": "log_cleanup",
                "commands": [
                    "find /var/log -name '*.log' -mtime +30 -exec gzip {} \\;",
                    "find /var/log -name '*.gz' -mtime +60 -exec mv {} /archive/logs/ \\;"
                ]
            },
            "config_before": """Disk Usage: /var/log partition
Total: 500GB
Used: 485GB (97%)
Available: 15GB (3%)

Log files:
- application.log (120GB)
- access.log (180GB)
- error.log (85GB)""",
            "config_after": """Disk Usage: /var/log partition
Total: 500GB
Used: 145GB (29%)
Available: 355GB (71%)

Recent logs retained:
- Last 30 days: 145GB
- Archived to /archive/logs: 340GB""",
            "expected_outcome": {
                "metric": "Disk utilization",
                "current": "97%",
                "expected": "25-30%",
                "timeline": "5-8 minutes (compression time)"
            },
            "alternatives": [
                {
                    "title": "Delete Old Logs",
                    "description": "Permanently delete logs older than 60 days",
                    "confidence": 85,
                    "effort": "LOW",
                    "timeline": "1 minute",
                    "caveat": "Irreversible - cannot recover deleted logs if needed for audit"
                },
                {
                    "title": "Expand Disk Capacity",
                    "description": "Increase /var/log partition from 500GB to 1TB",
                    "confidence": 95,
                    "effort": "HIGH",
                    "timeline": "30-45 minutes",
                    "caveat": "Requires filesystem resize and potential downtime"
                }
            ],
            "rollback_plan": [
                "1. Archived logs stored at /archive/logs with full path preserved",
                "2. If disk space doesn't free up, check for large temp files",
                "3. Archived logs can be decompressed back to /var/log if needed",
                "4. Rollback command: gunzip /var/log/**/*.gz (restores original logs)",
                "5. Archive maintained for 90 days before permanent deletion"
            ],
            "risk_assessment": {
                "level": "VERY_LOW",
                "factors": [
                    "Logs are archived, not deleted (reversible)",
                    "Compression is lossless",
                    "No impact on running applications",
                    "Operation can be paused/resumed if needed"
                ]
            },
            "compliance_notes": "Archived logs maintained for 90-day compliance requirement. Archive location: /archive/logs"
        }

    def _suggest_latency_fix(
        self, analysis: Dict[str, Any], topology: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Suggest fix for network latency issues"""

        affected_server_id = topology["affected_server"]["id"]
        network_context = topology.get("network_context", {})

        # Find healthy backup path
        backup_path = None
        for path in network_context.get("paths", []):
            if path["status"] == "healthy" and path["id"] == "backup":
                backup_path = path
                break

        return {
            "recommended_action": {
                "title": "Switch to Backup Network Path",
                "description": "Route traffic through us-east-1b while primary path recovers",
                "type": "network_reconfiguration",
                "target": affected_server_id
            },
            "confidence": 78,
            "confidence_reasoning": [
                "Primary network path showing degraded performance",
                f"Backup path healthy with latency {backup_path.get('latency_avg', 30)}ms (vs 450ms current)",
                "No application or server-level issues detected",
                "ISP routing tables may be suboptimal on primary path"
            ],
            "config_changes": {
                "file": "/etc/network/routes.conf",
                "changes": [
                    {
                        "parameter": "default_gateway",
                        "current_value": "us-east-1a-gateway (10.0.1.1)",
                        "new_value": "us-east-1b-gateway (10.0.3.1)",
                        "justification": "Route through healthy network path"
                    }
                ]
            },
            "config_before": """# Network Routes
default_gateway: us-east-1a-gateway
gateway_ip: 10.0.1.1
failover_enabled: false
status: primary""",
            "config_after": """# Network Routes
default_gateway: us-east-1b-gateway
gateway_ip: 10.0.3.1
failover_enabled: true
status: backup (auto-failback when primary recovers)""",
            "expected_outcome": {
                "metric": "API response latency",
                "current": "450ms",
                "expected": "50-80ms",
                "timeline": "Immediate (30-60 seconds for routing tables to update)"
            },
            "alternatives": [
                {
                    "title": "Wait for Primary Path Recovery",
                    "description": "Monitor primary path for ISP to resolve routing issues",
                    "confidence": 60,
                    "effort": "ZERO",
                    "timeline": "Unknown (typically 30-120 minutes)",
                    "caveat": "Continued degraded user experience during wait"
                },
                {
                    "title": "Load Balance Across Both Paths",
                    "description": "Split traffic 50/50 between primary and backup",
                    "confidence": 70,
                    "effort": "MEDIUM",
                    "timeline": "5 minutes",
                    "caveat": "50% of users still experience high latency"
                }
            ],
            "rollback_plan": [
                "1. Monitor latency metrics for 2 minutes after switch",
                "2. If latency doesn't improve, revert to primary path",
                "3. Automatic failback to primary path when it shows healthy status",
                "4. Route changes logged for network audit",
                "5. Rollback command: sudo route del default && sudo route add default gw 10.0.1.1"
            ],
            "risk_assessment": {
                "level": "LOW",
                "factors": [
                    "Backup path is pre-tested and verified healthy",
                    "Route changes are instantaneous and reversible",
                    "Both paths have equivalent bandwidth capacity",
                    "Auto-failback configured when primary recovers"
                ]
            },
            "compliance_notes": "Network path change logged. Primary path monitoring continues for automatic failback."
        }

    def _suggest_generic_fix(
        self, analysis: Dict[str, Any], topology: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generic fix suggestion for unknown issues"""
        return {
            "recommended_action": {
                "title": "Manual Investigation Required",
                "description": "Alert pattern does not match known automated remediation scenarios",
                "type": "escalation",
                "target": topology["affected_server"]["id"]
            },
            "confidence": 50,
            "confidence_reasoning": [
                "Insufficient historical data for automated fix",
                "Alert pattern not recognized in playbook",
                "Recommending human expert review"
            ],
            "alternatives": [
                {
                    "title": "Restart Affected Service",
                    "description": "Generic restart may resolve transient issues",
                    "confidence": 40,
                    "effort": "LOW",
                    "timeline": "2-3 minutes",
                    "caveat": "May cause brief service interruption"
                }
            ],
            "rollback_plan": ["Manual intervention required"],
            "risk_assessment": {
                "level": "UNKNOWN",
                "factors": ["Insufficient data for automated assessment"]
            }
        }
