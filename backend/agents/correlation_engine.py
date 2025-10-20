"""
Correlation Engine - Links related logs across microservices
Critical for L2/L3 engineers debugging cascading failures

Example:
- Keystone auth fails at 14:30:00
- Nova can't verify token at 14:30:05
- Neutron network setup fails at 14:30:10
- VM boot fails at 14:30:15

Correlation Engine links these into one incident timeline
"""

import re
from typing import List, Dict, Any, Set, Optional, Tuple
from collections import defaultdict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CorrelationEngine:
    """
    Correlates logs across services to build incident timelines
    Essential for debugging multi-service failures
    """

    def __init__(self):
        # Time window for correlating related events (seconds)
        self.correlation_window = 300  # 5 minutes

        # Common correlation keys
        self.uuid_pattern = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')
        self.request_id_pattern = re.compile(r'req-[0-9a-f-]+')

        # Service dependency map (typical OpenStack flow)
        self.service_dependencies = {
            'nova-compute': ['nova-api', 'neutron', 'keystone', 'glance'],
            'nova-api': ['keystone', 'neutron'],
            'neutron': ['keystone'],
            'glance': ['keystone'],
            'cinder': ['keystone'],
        }

        # Keywords indicating cross-service impact
        self.correlation_keywords = {
            'auth': ['keystone', 'token', 'authentication', 'authorization'],
            'network': ['neutron', 'network', 'port', 'subnet', 'router'],
            'compute': ['nova', 'instance', 'vm', 'hypervisor'],
            'storage': ['cinder', 'volume', 'glance', 'image'],
            'database': ['mysql', 'mariadb', 'database', 'connection pool']
        }

    def correlate_incidents(
        self,
        logs: List[Dict[str, Any]],
        time_window: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Group related logs into incident chains

        Args:
            logs: List of log entries
            time_window: Time window in seconds (default: 5 minutes)

        Returns:
            List of incidents with correlated logs
        """
        if time_window:
            self.correlation_window = time_window

        logger.info(f"Correlating {len(logs)} logs into incidents...")

        # Extract correlation IDs (UUIDs, request-ids)
        logs_with_ids = self._extract_correlation_ids(logs)

        # Group by correlation ID
        id_groups = self._group_by_correlation_id(logs_with_ids)

        # Find time-based correlations
        time_groups = self._group_by_time_proximity(logs)

        # Find service dependency correlations
        service_groups = self._group_by_service_dependencies(logs)

        # Merge correlation groups
        incidents = self._merge_correlations(id_groups, time_groups, service_groups)

        # Build incident summaries
        incident_summaries = []
        for i, incident_logs in enumerate(incidents):
            summary = self._create_incident_summary(i + 1, incident_logs)
            incident_summaries.append(summary)

        # Sort by severity and impact
        incident_summaries.sort(key=lambda inc: (
            -inc['severity_score'],
            -inc['affected_services_count']
        ))

        logger.info(f"Identified {len(incident_summaries)} correlated incidents")
        return incident_summaries

    def find_root_cause_candidates(
        self,
        incident: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Within an incident, identify likely root cause logs

        Root cause is typically:
        - Earliest ERROR/CRITICAL in dependency chain
        - In a foundational service (Keystone, Database)
        - Matches known failure patterns
        """
        logs = incident.get('logs', [])
        if not logs:
            return []

        # Sort by timestamp
        sorted_logs = sorted(logs, key=lambda l: l['timestamp'])

        candidates = []

        # Strategy 1: First critical error
        for log in sorted_logs:
            if log['level'] in ['ERROR', 'CRITICAL']:
                candidates.append({
                    'log': log,
                    'reason': 'first_critical_error',
                    'confidence': 0.9
                })
                break

        # Strategy 2: Foundational service failures
        foundational_services = ['keystone', 'database', 'rabbitmq', 'mysql']
        for log in sorted_logs:
            service_lower = log['service'].lower()
            if any(fs in service_lower for fs in foundational_services):
                if log['level'] in ['ERROR', 'CRITICAL']:
                    candidates.append({
                        'log': log,
                        'reason': 'foundational_service_failure',
                        'confidence': 0.85
                    })

        # Strategy 3: Known failure patterns
        known_patterns = [
            'connection refused',
            'timeout',
            'cannot connect',
            'authentication failed',
            'permission denied',
            'out of memory',
            'disk full',
            'no valid host'
        ]

        for log in sorted_logs:
            message_lower = log['message'].lower()
            for pattern in known_patterns:
                if pattern in message_lower and log['level'] in ['ERROR', 'CRITICAL']:
                    candidates.append({
                        'log': log,
                        'reason': f'known_pattern: {pattern}',
                        'confidence': 0.8
                    })
                    break

        # Deduplicate and sort by confidence
        seen = set()
        unique_candidates = []
        for candidate in candidates:
            log_id = candidate['log'].get('id')
            if log_id not in seen:
                seen.add(log_id)
                unique_candidates.append(candidate)

        unique_candidates.sort(key=lambda c: -c['confidence'])
        return unique_candidates[:3]  # Top 3 candidates

    def build_dependency_timeline(
        self,
        incident: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Build visual timeline showing cascade across services

        Returns:
            Timeline entries sorted by timestamp
        """
        logs = incident.get('logs', [])
        sorted_logs = sorted(logs, key=lambda l: l['timestamp'])

        timeline = []
        for i, log in enumerate(sorted_logs):
            entry = {
                'step': i + 1,
                'timestamp': log['timestamp'],
                'service': log['service'],
                'level': log['level'],
                'message': log['message'][:100],  # Truncate for display
                'is_error': log['level'] in ['ERROR', 'CRITICAL']
            }

            # Determine if this is a consequence of previous step
            if i > 0:
                prev_log = sorted_logs[i - 1]
                time_diff = log['timestamp'] - prev_log['timestamp']

                if time_diff < 10:  # Within 10 seconds
                    entry['likely_consequence_of'] = i  # Previous step

            timeline.append(entry)

        return timeline

    def _extract_correlation_ids(
        self,
        logs: List[Dict[str, Any]]
    ) -> List[Tuple[Dict[str, Any], Set[str]]]:
        """Extract UUIDs and request IDs from logs"""
        results = []

        for log in logs:
            ids = set()

            # Extract UUIDs
            uuids = self.uuid_pattern.findall(log['message'])
            ids.update(uuids)

            # Extract request IDs
            req_ids = self.request_id_pattern.findall(log['message'])
            ids.update(req_ids)

            # Check metadata for IDs
            if log.get('metadata'):
                metadata_str = str(log['metadata'])
                ids.update(self.uuid_pattern.findall(metadata_str))
                ids.update(self.request_id_pattern.findall(metadata_str))

            results.append((log, ids))

        return results

    def _group_by_correlation_id(
        self,
        logs_with_ids: List[Tuple[Dict[str, Any], Set[str]]]
    ) -> List[List[Dict[str, Any]]]:
        """Group logs that share correlation IDs"""
        # Build graph of which logs share IDs
        id_to_logs = defaultdict(list)

        for log, ids in logs_with_ids:
            for corr_id in ids:
                id_to_logs[corr_id].append(log)

        # Group logs that share any ID
        groups = []
        for log_list in id_to_logs.values():
            if len(log_list) > 1:  # Only groups with multiple logs
                groups.append(log_list)

        return groups

    def _group_by_time_proximity(
        self,
        logs: List[Dict[str, Any]]
    ) -> List[List[Dict[str, Any]]]:
        """Group errors that happen within time window"""
        # Only consider ERROR/CRITICAL for time-based correlation
        error_logs = [l for l in logs if l['level'] in ['ERROR', 'CRITICAL', 'WARN']]

        if not error_logs:
            return []

        # Sort by timestamp
        sorted_logs = sorted(error_logs, key=lambda l: l['timestamp'])

        groups = []
        current_group = [sorted_logs[0]]

        for log in sorted_logs[1:]:
            time_diff = log['timestamp'] - current_group[-1]['timestamp']

            if time_diff <= self.correlation_window:
                current_group.append(log)
            else:
                if len(current_group) > 1:
                    groups.append(current_group)
                current_group = [log]

        # Add final group
        if len(current_group) > 1:
            groups.append(current_group)

        return groups

    def _group_by_service_dependencies(
        self,
        logs: List[Dict[str, Any]]
    ) -> List[List[Dict[str, Any]]]:
        """Group logs based on known service dependencies"""
        groups = []

        # Find errors in dependent services
        for service, dependencies in self.service_dependencies.items():
            service_errors = [l for l in logs if service in l['service'].lower() and l['level'] in ['ERROR', 'CRITICAL']]

            if service_errors:
                # Find related errors in dependencies
                related_logs = service_errors.copy()

                for dep in dependencies:
                    dep_logs = [
                        l for l in logs
                        if dep in l['service'].lower() and l['level'] in ['ERROR', 'CRITICAL', 'WARN']
                    ]
                    related_logs.extend(dep_logs)

                if len(related_logs) > 1:
                    groups.append(related_logs)

        return groups

    def _merge_correlations(
        self,
        id_groups: List[List[Dict]],
        time_groups: List[List[Dict]],
        service_groups: List[List[Dict]]
    ) -> List[List[Dict[str, Any]]]:
        """Merge overlapping correlation groups"""
        all_groups = id_groups + time_groups + service_groups

        if not all_groups:
            return []

        # Merge groups that share any logs
        merged = []
        for group in all_groups:
            # Find if this group overlaps with any existing merged group
            group_ids = {log.get('id') for log in group}

            merged_into_existing = False
            for existing in merged:
                existing_ids = {log.get('id') for log in existing}
                if group_ids & existing_ids:  # Intersection
                    # Merge
                    for log in group:
                        if log.get('id') not in existing_ids:
                            existing.append(log)
                    merged_into_existing = True
                    break

            if not merged_into_existing:
                merged.append(group)

        return merged

    def _create_incident_summary(
        self,
        incident_id: int,
        logs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create summary for an incident"""
        if not logs:
            return {}

        sorted_logs = sorted(logs, key=lambda l: l['timestamp'])

        # Affected services
        services = list(set(log['service'] for log in logs))

        # Severity (highest level)
        severity_order = {'CRITICAL': 4, 'ERROR': 3, 'WARN': 2, 'INFO': 1, 'DEBUG': 0}
        max_severity = max(logs, key=lambda l: severity_order.get(l['level'], 0))['level']

        # Time range
        start_time = sorted_logs[0]['timestamp']
        end_time = sorted_logs[-1]['timestamp']

        # Count by level
        level_counts = defaultdict(int)
        for log in logs:
            level_counts[log['level']] += 1

        # Build narrative
        narrative = self._build_narrative(sorted_logs)

        return {
            'incident_id': incident_id,
            'severity': max_severity,
            'severity_score': severity_order.get(max_severity, 0),
            'start_time': start_time,
            'end_time': end_time,
            'duration_seconds': end_time - start_time,
            'affected_services': services,
            'affected_services_count': len(services),
            'log_count': len(logs),
            'level_breakdown': dict(level_counts),
            'logs': logs,
            'narrative': narrative,
            'root_cause_candidates': self.find_root_cause_candidates({'logs': logs}),
            'timeline': self.build_dependency_timeline({'logs': logs})
        }

    def _build_narrative(self, sorted_logs: List[Dict[str, Any]]) -> str:
        """Generate human-readable incident narrative"""
        if not sorted_logs:
            return ""

        services = list(set(log['service'] for log in sorted_logs))
        error_count = sum(1 for log in sorted_logs if log['level'] in ['ERROR', 'CRITICAL'])

        narrative = f"Incident involving {len(services)} service(s): {', '.join(services)}. "
        narrative += f"Detected {error_count} error(s) across {len(sorted_logs)} log entries. "

        # Identify pattern
        first_error = next((log for log in sorted_logs if log['level'] in ['ERROR', 'CRITICAL']), None)
        if first_error:
            narrative += f"First error occurred in {first_error['service']}: {first_error['message'][:80]}..."

        return narrative


# Singleton instance
_correlation_engine_instance = None


def get_correlation_engine() -> CorrelationEngine:
    """Get singleton CorrelationEngine instance"""
    global _correlation_engine_instance
    if _correlation_engine_instance is None:
        _correlation_engine_instance = CorrelationEngine()
    return _correlation_engine_instance
