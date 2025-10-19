"""
Log Storage Service - SQLite-based time-series log storage
Handles log persistence, querying, and retrieval
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class LogStorageService:
    """
    Manages log storage using SQLite with time-series optimization
    """

    def __init__(self, db_path: str = "data/logs.db"):
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()

    def _ensure_db_directory(self):
        """Ensure the database directory exists"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    def _init_database(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Main logs table with time-series optimization
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    datetime TEXT NOT NULL,
                    level TEXT NOT NULL,
                    service TEXT NOT NULL,
                    message TEXT NOT NULL,
                    metadata TEXT,
                    created_at REAL DEFAULT (julianday('now'))
                )
            """)

            # Indexes for fast querying
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON logs(timestamp DESC)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_level
                ON logs(level)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_service
                ON logs(service)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_datetime
                ON logs(datetime DESC)
            """)

            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")

    def ingest_log(self, log_entry: Dict[str, Any]) -> int:
        """
        Insert a single log entry

        Args:
            log_entry: Dict with keys: timestamp, level, service, message, metadata

        Returns:
            Log ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Extract fields with defaults
            timestamp = log_entry.get('timestamp', datetime.utcnow().timestamp())
            dt = datetime.fromtimestamp(timestamp).isoformat()
            level = log_entry.get('level', 'INFO').upper()
            service = log_entry.get('service', 'unknown')
            message = log_entry.get('message', '')
            metadata = json.dumps(log_entry.get('metadata', {}))

            cursor.execute("""
                INSERT INTO logs (timestamp, datetime, level, service, message, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (timestamp, dt, level, service, message, metadata))

            conn.commit()
            return cursor.lastrowid

    def ingest_logs_batch(self, log_entries: List[Dict[str, Any]]) -> int:
        """
        Insert multiple log entries efficiently

        Args:
            log_entries: List of log entry dicts

        Returns:
            Number of logs inserted
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            rows = []
            for entry in log_entries:
                timestamp = entry.get('timestamp', datetime.utcnow().timestamp())
                dt = datetime.fromtimestamp(timestamp).isoformat()
                level = entry.get('level', 'INFO').upper()
                service = entry.get('service', 'unknown')
                message = entry.get('message', '')
                metadata = json.dumps(entry.get('metadata', {}))

                rows.append((timestamp, dt, level, service, message, metadata))

            cursor.executemany("""
                INSERT INTO logs (timestamp, datetime, level, service, message, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, rows)

            conn.commit()
            logger.info(f"Batch inserted {len(rows)} logs")
            return len(rows)

    def query_logs(
        self,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        levels: Optional[List[str]] = None,
        services: Optional[List[str]] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Query logs with filters

        Args:
            start_time: Start timestamp (inclusive)
            end_time: End timestamp (inclusive)
            levels: Filter by log levels (e.g., ['ERROR', 'WARN'])
            services: Filter by services
            search: Text search in message
            limit: Max results
            offset: Pagination offset

        Returns:
            List of log entries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Build query dynamically
            query = "SELECT * FROM logs WHERE 1=1"
            params = []

            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time)

            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)

            if levels:
                placeholders = ','.join('?' * len(levels))
                query += f" AND level IN ({placeholders})"
                params.extend([level.upper() for level in levels])

            if services:
                placeholders = ','.join('?' * len(services))
                query += f" AND service IN ({placeholders})"
                params.extend(services)

            if search:
                query += " AND message LIKE ?"
                params.append(f"%{search}%")

            query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            # Convert to dicts
            logs = []
            for row in rows:
                log = {
                    'id': row['id'],
                    'timestamp': row['timestamp'],
                    'datetime': row['datetime'],
                    'level': row['level'],
                    'service': row['service'],
                    'message': row['message'],
                    'metadata': json.loads(row['metadata']) if row['metadata'] else {}
                }
                logs.append(log)

            return logs

    def get_log_count(
        self,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        levels: Optional[List[str]] = None,
        services: Optional[List[str]] = None
    ) -> int:
        """
        Get count of logs matching filters

        Returns:
            Total count
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            query = "SELECT COUNT(*) FROM logs WHERE 1=1"
            params = []

            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time)

            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)

            if levels:
                placeholders = ','.join('?' * len(levels))
                query += f" AND level IN ({placeholders})"
                params.extend([level.upper() for level in levels])

            if services:
                placeholders = ','.join('?' * len(services))
                query += f" AND service IN ({placeholders})"
                params.extend(services)

            cursor.execute(query, params)
            return cursor.fetchone()[0]

    def get_services(self) -> List[str]:
        """Get list of unique services in logs"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT service FROM logs ORDER BY service")
            return [row[0] for row in cursor.fetchall()]

    def get_log_stats(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get statistics for recent logs

        Args:
            hours: Time window in hours

        Returns:
            Stats dict with counts by level
        """
        start_time = (datetime.utcnow() - timedelta(hours=hours)).timestamp()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Count by level
            cursor.execute("""
                SELECT level, COUNT(*) as count
                FROM logs
                WHERE timestamp >= ?
                GROUP BY level
            """, (start_time,))

            level_counts = {row[0]: row[1] for row in cursor.fetchall()}

            # Total count
            total = sum(level_counts.values())

            return {
                'total': total,
                'by_level': level_counts,
                'time_window_hours': hours
            }

    def cleanup_old_logs(self, days: int = 30) -> int:
        """
        Delete logs older than specified days

        Args:
            days: Keep logs from last N days

        Returns:
            Number of logs deleted
        """
        cutoff_time = (datetime.utcnow() - timedelta(days=days)).timestamp()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM logs WHERE timestamp < ?", (cutoff_time,))
            deleted = cursor.rowcount
            conn.commit()

            logger.info(f"Deleted {deleted} logs older than {days} days")
            return deleted

    def get_recent_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get most recent logs

        Args:
            limit: Max number of logs

        Returns:
            List of recent log entries
        """
        return self.query_logs(limit=limit, offset=0)


# Singleton instance
_log_storage_instance = None


def get_log_storage() -> LogStorageService:
    """Get singleton LogStorageService instance"""
    global _log_storage_instance
    if _log_storage_instance is None:
        _log_storage_instance = LogStorageService()
    return _log_storage_instance
