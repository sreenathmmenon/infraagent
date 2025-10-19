"""
Test script for Logs API
Tests backend functionality before frontend implementation
"""

import requests
import json
from datetime import datetime, timedelta
import time

BASE_URL = "http://localhost:8000"


def test_health():
    """Test if server is running"""
    print("🔍 Testing server health...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Server is healthy")
            return True
        else:
            print(f"❌ Server returned {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server not reachable: {e}")
        return False


def test_ingest_logs():
    """Test log ingestion"""
    print("\n🔍 Testing log ingestion...")

    # Sample logs
    sample_logs = [
        {
            "timestamp": datetime.utcnow().timestamp(),
            "level": "ERROR",
            "service": "api-service",
            "message": "Database connection timeout - pool exhausted",
            "metadata": {
                "pool_size": 20,
                "active_connections": 20
            }
        },
        {
            "timestamp": (datetime.utcnow() - timedelta(seconds=5)).timestamp(),
            "level": "WARN",
            "service": "api-service",
            "message": "Slow query detected: SELECT * FROM orders took 12.3s",
            "metadata": {
                "query_time": 12.3,
                "table": "orders"
            }
        },
        {
            "timestamp": (datetime.utcnow() - timedelta(seconds=10)).timestamp(),
            "level": "INFO",
            "service": "payment-service",
            "message": "Payment processed successfully",
            "metadata": {
                "amount": 99.99,
                "currency": "USD"
            }
        },
        {
            "timestamp": (datetime.utcnow() - timedelta(seconds=15)).timestamp(),
            "level": "DEBUG",
            "service": "auth-service",
            "message": "User logged in",
            "metadata": {
                "user_id": "user123"
            }
        },
        {
            "timestamp": (datetime.utcnow() - timedelta(seconds=20)).timestamp(),
            "level": "ERROR",
            "service": "payment-service",
            "message": "Failed to process payment - Connection refused",
            "metadata": {
                "error_code": "CONN_REFUSED"
            }
        }
    ]

    try:
        response = requests.post(
            f"{BASE_URL}/api/logs/ingest",
            json={"logs": sample_logs}
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Ingested {data['count']} logs successfully")
            return True
        else:
            print(f"❌ Ingestion failed: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Error during ingestion: {e}")
        return False


def test_query_logs():
    """Test log querying"""
    print("\n🔍 Testing log querying...")

    try:
        # Query all logs
        response = requests.post(
            f"{BASE_URL}/api/logs/query",
            json={
                "limit": 10,
                "offset": 0
            }
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Query returned {data['count']} logs (total: {data['total']})")

            # Print first log
            if data['logs']:
                log = data['logs'][0]
                print(f"   Latest log: [{log['level']}] {log['service']}: {log['message']}")
            return True
        else:
            print(f"❌ Query failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error during query: {e}")
        return False


def test_filter_by_level():
    """Test filtering by log level"""
    print("\n🔍 Testing filter by level (ERROR)...")

    try:
        response = requests.post(
            f"{BASE_URL}/api/logs/query",
            json={
                "levels": ["ERROR"],
                "limit": 10
            }
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {data['count']} ERROR logs")

            for log in data['logs'][:3]:
                print(f"   - {log['service']}: {log['message']}")
            return True
        else:
            print(f"❌ Filter failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error during filter: {e}")
        return False


def test_filter_by_service():
    """Test filtering by service"""
    print("\n🔍 Testing filter by service...")

    try:
        response = requests.post(
            f"{BASE_URL}/api/logs/query",
            json={
                "services": ["api-service"],
                "limit": 10
            }
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {data['count']} logs from api-service")
            return True
        else:
            print(f"❌ Filter failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error during filter: {e}")
        return False


def test_search_logs():
    """Test text search"""
    print("\n🔍 Testing text search (search for 'database')...")

    try:
        response = requests.post(
            f"{BASE_URL}/api/logs/query",
            json={
                "search": "database",
                "limit": 10
            }
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {data['count']} logs matching 'database'")

            for log in data['logs']:
                print(f"   - {log['message']}")
            return True
        else:
            print(f"❌ Search failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error during search: {e}")
        return False


def test_get_recent_logs():
    """Test getting recent logs"""
    print("\n🔍 Testing get recent logs...")

    try:
        response = requests.get(f"{BASE_URL}/api/logs/recent?limit=5")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Retrieved {data['count']} recent logs")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_get_stats():
    """Test getting log statistics"""
    print("\n🔍 Testing log statistics...")

    try:
        response = requests.get(f"{BASE_URL}/api/logs/stats?hours=24")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Statistics (last 24h):")
            print(f"   Total logs: {data['total']}")
            print(f"   By level: {data['by_level']}")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_get_services():
    """Test getting list of services"""
    print("\n🔍 Testing get services list...")

    try:
        response = requests.get(f"{BASE_URL}/api/logs/services")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {data['count']} unique services:")
            print(f"   Services: {', '.join(data['services'])}")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("LOGS API TEST SUITE")
    print("=" * 60)

    # Test server
    if not test_health():
        print("\n❌ Server is not running. Start it with:")
        print("   cd /Users/sreenath/Code/LYZR/infraagent/backend")
        print("   python main.py")
        return

    # Run tests
    tests = [
        test_ingest_logs,
        test_query_logs,
        test_filter_by_level,
        test_filter_by_service,
        test_search_logs,
        test_get_recent_logs,
        test_get_stats,
        test_get_services
    ]

    passed = 0
    failed = 0

    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
        time.sleep(0.5)  # Small delay between tests

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {passed + failed}")

    if failed == 0:
        print("\n🎉 All tests passed! Backend is working correctly.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Check the errors above.")


if __name__ == "__main__":
    main()
