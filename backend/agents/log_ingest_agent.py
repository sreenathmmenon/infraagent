"""
Log Ingest Agent - Handles log ingestion from multiple sources
Parses, validates, and stores logs
"""

import re
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from services.log_storage_service import get_log_storage

logger = logging.getLogger(__name__)


class LogIngestAgent:
    """
    Agent responsible for ingesting logs from various sources
    Supports multiple formats: JSON, syslog, plain text
    """

    def __init__(self):
        self.storage = get_log_storage()
        self.log_level_map = {
            'CRITICAL': 'CRITICAL',
            'FATAL': 'CRITICAL',
            'ERROR': 'ERROR',
            'ERR': 'ERROR',
            'WARNING': 'WARN',
            'WARN': 'WARN',
            'INFO': 'INFO',
            'DEBUG': 'DEBUG',
            'TRACE': 'DEBUG'
        }

    def ingest_json_log(self, log_data: Dict[str, Any]) -> int:
        """
        Ingest a single JSON-formatted log

        Expected fields:
        - timestamp (optional): Unix timestamp or ISO datetime
        - level: Log level (ERROR, WARN, INFO, DEBUG)
        - service: Service name
        - message: Log message
        - metadata (optional): Additional fields

        Returns:
            Log ID
        """
        try:
            # Parse timestamp
            timestamp = self._parse_timestamp(log_data.get('timestamp'))

            # Normalize level
            level = self._normalize_level(log_data.get('level', 'INFO'))

            # Extract service
            service = log_data.get('service', 'unknown')

            # Get message
            message = log_data.get('message', '')

            # Collect metadata
            metadata = log_data.get('metadata', {})

            # Store
            log_entry = {
                'timestamp': timestamp,
                'level': level,
                'service': service,
                'message': message,
                'metadata': metadata
            }

            log_id = self.storage.ingest_log(log_entry)
            logger.debug(f"Ingested JSON log #{log_id} from {service}")
            return log_id

        except Exception as e:
            logger.error(f"Error ingesting JSON log: {e}")
            raise

    def ingest_json_logs_batch(self, logs: List[Dict[str, Any]]) -> int:
        """
        Ingest multiple JSON logs efficiently

        Args:
            logs: List of log dicts

        Returns:
            Number of logs ingested
        """
        try:
            log_entries = []

            for log_data in logs:
                timestamp = self._parse_timestamp(log_data.get('timestamp'))
                level = self._normalize_level(log_data.get('level', 'INFO'))
                service = log_data.get('service', 'unknown')
                message = log_data.get('message', '')
                metadata = log_data.get('metadata', {})

                log_entries.append({
                    'timestamp': timestamp,
                    'level': level,
                    'service': service,
                    'message': message,
                    'metadata': metadata
                })

            count = self.storage.ingest_logs_batch(log_entries)
            logger.info(f"Batch ingested {count} JSON logs")
            return count

        except Exception as e:
            logger.error(f"Error batch ingesting JSON logs: {e}")
            raise

    def ingest_syslog(self, syslog_line: str, service: str = 'syslog') -> Optional[int]:
        """
        Ingest a syslog-formatted line

        Example: "Jan 12 14:32:15 hostname service[1234]: Error message"

        Returns:
            Log ID or None if parsing fails
        """
        try:
            parsed = self._parse_syslog(syslog_line)
            if not parsed:
                return None

            log_entry = {
                'timestamp': parsed['timestamp'],
                'level': parsed['level'],
                'service': service,
                'message': parsed['message'],
                'metadata': {
                    'hostname': parsed.get('hostname'),
                    'pid': parsed.get('pid')
                }
            }

            log_id = self.storage.ingest_log(log_entry)
            logger.debug(f"Ingested syslog #{log_id}")
            return log_id

        except Exception as e:
            logger.error(f"Error ingesting syslog: {e}")
            return None

    def ingest_plain_text(
        self,
        text: str,
        service: str,
        level: str = 'INFO',
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Ingest plain text log

        Args:
            text: Log message
            service: Service name
            level: Log level
            metadata: Optional metadata dict

        Returns:
            Log ID
        """
        try:
            log_entry = {
                'timestamp': datetime.utcnow().timestamp(),
                'level': self._normalize_level(level),
                'service': service,
                'message': text,
                'metadata': metadata or {}
            }

            log_id = self.storage.ingest_log(log_entry)
            logger.debug(f"Ingested plain text log #{log_id}")
            return log_id

        except Exception as e:
            logger.error(f"Error ingesting plain text: {e}")
            raise

    def _parse_timestamp(self, ts: Any) -> float:
        """
        Parse timestamp from various formats

        Supports:
        - Unix timestamp (float/int)
        - ISO datetime string
        - None (use current time)
        """
        if ts is None:
            return datetime.utcnow().timestamp()

        if isinstance(ts, (int, float)):
            return float(ts)

        if isinstance(ts, str):
            try:
                # Try ISO format
                dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                return dt.timestamp()
            except:
                # Fallback to current time
                logger.warning(f"Could not parse timestamp: {ts}, using current time")
                return datetime.utcnow().timestamp()

        return datetime.utcnow().timestamp()

    def _normalize_level(self, level: str) -> str:
        """Normalize log level to standard values"""
        level_upper = str(level).upper()
        return self.log_level_map.get(level_upper, 'INFO')

    def _parse_syslog(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Parse syslog format

        Example formats:
        - "Jan 12 14:32:15 hostname service[1234]: Message"
        - "2024-01-12T14:32:15Z hostname service: Message"
        """
        # Pattern 1: Traditional syslog
        pattern1 = r'(\w+\s+\d+\s+\d+:\d+:\d+)\s+(\S+)\s+(\S+?)(\[\d+\])?\:\s+(.*)'
        match = re.match(pattern1, line)

        if match:
            timestamp_str, hostname, service, pid, message = match.groups()
            # Approximate timestamp (syslog doesn't include year)
            current_year = datetime.utcnow().year
            try:
                timestamp = datetime.strptime(
                    f"{current_year} {timestamp_str}",
                    "%Y %b %d %H:%M:%S"
                ).timestamp()
            except:
                timestamp = datetime.utcnow().timestamp()

            # Infer level from message
            level = self._infer_level_from_message(message)

            return {
                'timestamp': timestamp,
                'hostname': hostname,
                'service': service,
                'pid': pid.strip('[]') if pid else None,
                'message': message,
                'level': level
            }

        # Pattern 2: ISO timestamp
        pattern2 = r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?)\s+(\S+)\s+(\S+)\:\s+(.*)'
        match = re.match(pattern2, line)

        if match:
            timestamp_str, hostname, service, message = match.groups()
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00')).timestamp()
            except:
                timestamp = datetime.utcnow().timestamp()

            level = self._infer_level_from_message(message)

            return {
                'timestamp': timestamp,
                'hostname': hostname,
                'service': service,
                'message': message,
                'level': level
            }

        # Could not parse
        logger.warning(f"Could not parse syslog line: {line}")
        return None

    def _infer_level_from_message(self, message: str) -> str:
        """Infer log level from message content"""
        message_lower = message.lower()

        if any(word in message_lower for word in ['error', 'fail', 'exception', 'fatal']):
            return 'ERROR'
        elif any(word in message_lower for word in ['warn', 'warning']):
            return 'WARN'
        elif any(word in message_lower for word in ['debug', 'trace']):
            return 'DEBUG'
        else:
            return 'INFO'


# Singleton instance
_log_ingest_instance = None


def get_log_ingest_agent() -> LogIngestAgent:
    """Get singleton LogIngestAgent instance"""
    global _log_ingest_instance
    if _log_ingest_instance is None:
        _log_ingest_instance = LogIngestAgent()
    return _log_ingest_instance
