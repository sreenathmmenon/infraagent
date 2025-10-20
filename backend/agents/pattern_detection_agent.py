"""
Pattern Detection Agent - Clusters similar logs to reduce noise
Perfect for L2/L3 engineers dealing with 100K+ logs from OpenStack/microservices

Key Features:
- Reduce 50K logs to 5-10 unique patterns
- Fast similarity detection (no LLM needed)
- Highlight most critical patterns first
"""

import re
import hashlib
from typing import List, Dict, Any, Optional
from collections import defaultdict, Counter
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PatternDetectionAgent:
    """
    Detects patterns in large log volumes using statistical clustering
    Optimized for L2/L3 support engineers debugging multi-service systems
    """

    def __init__(self):
        # Common log noise to ignore (health checks, debug spam)
        self.noise_patterns = [
            r'health.*check.*ok',
            r'heartbeat',
            r'keepalive',
            r'ping.*pong',
            r'status.*200',
            r'connection.*established'
        ]

        # OpenStack-specific UUID/ID pattern
        self.uuid_pattern = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')
        self.ip_pattern = re.compile(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')
        self.timestamp_pattern = re.compile(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}')

    def analyze_logs(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze logs and return detected patterns

        Args:
            logs: List of log entries with timestamp, level, service, message, metadata

        Returns:
            {
                'total_logs': int,
                'patterns': [
                    {
                        'id': str,
                        'template': str,  # Normalized message
                        'count': int,
                        'severity': str,
                        'services': [str],
                        'first_seen': float,
                        'last_seen': float,
                        'sample_message': str,
                        'is_critical': bool
                    }
                ],
                'noise_filtered': int,
                'unique_patterns': int,
                'critical_patterns': int
            }
        """
        logger.info(f"Analyzing {len(logs)} logs for patterns...")

        # Filter out noise first
        filtered_logs = self._filter_noise(logs)
        noise_count = len(logs) - len(filtered_logs)

        if not filtered_logs:
            return {
                'total_logs': len(logs),
                'patterns': [],
                'noise_filtered': noise_count,
                'unique_patterns': 0,
                'critical_patterns': 0
            }

        # Group logs by pattern template
        pattern_groups = defaultdict(list)

        for log in filtered_logs:
            template = self._normalize_message(log['message'])
            pattern_groups[template].append(log)

        # Build pattern summaries
        patterns = []
        for template, log_group in pattern_groups.items():
            pattern = self._create_pattern_summary(template, log_group)
            patterns.append(pattern)

        # Sort by severity and count
        patterns.sort(key=lambda p: (
            -self._severity_score(p['severity']),
            -p['count']
        ))

        critical_count = sum(1 for p in patterns if p['is_critical'])

        result = {
            'total_logs': len(logs),
            'patterns': patterns,
            'noise_filtered': noise_count,
            'unique_patterns': len(patterns),
            'critical_patterns': critical_count
        }

        logger.info(f"Detected {len(patterns)} unique patterns, {critical_count} critical")
        return result

    def detect_anomalies(
        self,
        logs: List[Dict[str, Any]],
        baseline_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalous patterns (sudden spikes in error rates)

        Returns:
            List of anomalies with details
        """
        # Group by time windows (10-minute buckets)
        window_size = 600  # 10 minutes in seconds
        time_buckets = defaultdict(lambda: defaultdict(int))

        for log in logs:
            bucket = int(log['timestamp'] // window_size) * window_size
            time_buckets[bucket][log['level']] += 1

        # Find spikes
        anomalies = []

        # Calculate baseline error rate
        if not time_buckets:
            return anomalies

        error_rates = []
        for bucket_counts in time_buckets.values():
            total = sum(bucket_counts.values())
            errors = bucket_counts.get('ERROR', 0) + bucket_counts.get('CRITICAL', 0)
            rate = errors / total if total > 0 else 0
            error_rates.append(rate)

        if not error_rates:
            return anomalies

        avg_rate = sum(error_rates) / len(error_rates)

        # Flag buckets with >3x baseline error rate
        for bucket_time, bucket_counts in time_buckets.items():
            total = sum(bucket_counts.values())
            errors = bucket_counts.get('ERROR', 0) + bucket_counts.get('CRITICAL', 0)
            rate = errors / total if total > 0 else 0

            if rate > avg_rate * 3 and errors > 5:
                anomalies.append({
                    'timestamp': bucket_time,
                    'error_rate': rate,
                    'baseline_rate': avg_rate,
                    'spike_factor': rate / avg_rate if avg_rate > 0 else 0,
                    'error_count': errors,
                    'total_logs': total
                })

        anomalies.sort(key=lambda a: -a['spike_factor'])
        return anomalies

    def _filter_noise(self, logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove known noise patterns"""
        filtered = []

        for log in logs:
            message_lower = log['message'].lower()

            # Skip if matches noise pattern
            is_noise = any(
                re.search(pattern, message_lower)
                for pattern in self.noise_patterns
            )

            if not is_noise:
                filtered.append(log)

        return filtered

    def _normalize_message(self, message: str) -> str:
        """
        Normalize log message to create pattern template
        Replace UUIDs, IPs, timestamps with placeholders

        Example:
        "VM 12345678-1234-1234-1234-123456789abc failed to boot"
        → "VM <UUID> failed to boot"
        """
        normalized = message

        # Replace UUIDs
        normalized = self.uuid_pattern.sub('<UUID>', normalized)

        # Replace IPs
        normalized = self.ip_pattern.sub('<IP>', normalized)

        # Replace timestamps
        normalized = self.timestamp_pattern.sub('<TIMESTAMP>', normalized)

        # Replace numbers
        normalized = re.sub(r'\b\d+\b', '<NUM>', normalized)

        # Replace hex values
        normalized = re.sub(r'0x[0-9a-fA-F]+', '<HEX>', normalized)

        # Normalize whitespace
        normalized = ' '.join(normalized.split())

        return normalized

    def _create_pattern_summary(
        self,
        template: str,
        logs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create summary for a pattern group"""

        # Count by service
        services = Counter(log['service'] for log in logs)

        # Get time range
        timestamps = [log['timestamp'] for log in logs]
        first_seen = min(timestamps)
        last_seen = max(timestamps)

        # Determine severity (most severe level in group)
        levels = [log['level'] for log in logs]
        severity = self._most_severe_level(levels)

        # Is critical? (ERROR/CRITICAL + high count or affecting multiple services)
        is_critical = (
            severity in ['ERROR', 'CRITICAL'] and
            (len(logs) > 10 or len(services) > 2)
        )

        # Generate pattern ID
        pattern_id = hashlib.md5(template.encode()).hexdigest()[:8]

        return {
            'id': pattern_id,
            'template': template,
            'count': len(logs),
            'severity': severity,
            'services': list(services.keys()),
            'service_breakdown': dict(services),
            'first_seen': first_seen,
            'last_seen': last_seen,
            'duration_seconds': last_seen - first_seen,
            'sample_message': logs[0]['message'],  # Original message
            'is_critical': is_critical
        }

    def _most_severe_level(self, levels: List[str]) -> str:
        """Determine most severe log level in a list"""
        severity_order = {'CRITICAL': 4, 'ERROR': 3, 'WARN': 2, 'INFO': 1, 'DEBUG': 0}
        max_severity = max(levels, key=lambda l: severity_order.get(l, 0))
        return max_severity

    def _severity_score(self, level: str) -> int:
        """Convert level to numeric score for sorting"""
        scores = {'CRITICAL': 4, 'ERROR': 3, 'WARN': 2, 'INFO': 1, 'DEBUG': 0}
        return scores.get(level, 0)


# Singleton instance
_pattern_detection_instance = None


def get_pattern_detection_agent() -> PatternDetectionAgent:
    """Get singleton PatternDetectionAgent instance"""
    global _pattern_detection_instance
    if _pattern_detection_instance is None:
        _pattern_detection_instance = PatternDetectionAgent()
    return _pattern_detection_instance
