"""
Generate Realistic OpenStack-style Test Data
Simulates a cascading failure scenario across multiple services

Scenario: Database connection pool exhaustion causing VM boot failures
Timeline:
1. MySQL connection pool reaches max capacity
2. Keystone auth service starts timing out
3. Nova compute can't verify tokens
4. Neutron network allocation fails
5. VM boot requests fail
6. Customer impact: Unable to provision new VMs
"""

import requests
import time
from datetime import datetime, timedelta
import random
import uuid


# OpenStack-style services
SERVICES = {
    'mysql': ['mysql-server'],
    'keystone': ['keystone-api', 'keystone-admin'],
    'nova': ['nova-api', 'nova-compute', 'nova-scheduler'],
    'neutron': ['neutron-server', 'neutron-dhcp-agent', 'neutron-l3-agent'],
    'glance': ['glance-api', 'glance-registry'],
    'cinder': ['cinder-api', 'cinder-volume']
}


def generate_cascading_failure():
    """
    Generate realistic cascading failure scenario
    """

    logs = []
    base_time = time.time() - 3600  # Start 1 hour ago
    request_id = f"req-{uuid.uuid4()}"
    instance_uuid = str(uuid.uuid4())

    print("🎬 Generating OpenStack cascading failure scenario...")
    print(f"   Request ID: {request_id}")
    print(f"   Instance UUID: {instance_uuid}")

    # Phase 1: Database issues (T+0 to T+30s)
    print("\n📊 Phase 1: Database Connection Pool Exhaustion...")

    for i in range(10):
        logs.append({
            'timestamp': base_time + i,
            'level': 'WARN',
            'service': 'mysql-server',
            'message': f'Connection pool at 95% capacity: 475/500 connections active',
            'metadata': {'pool_size': 500, 'active': 475 + i*2}
        })

    logs.append({
        'timestamp': base_time + 30,
        'level': 'ERROR',
        'service': 'mysql-server',
        'message': 'Connection pool exhausted: max_connections=500 reached. New connections rejected',
        'metadata': {'pool_size': 500, 'active': 500}
    })

    # Phase 2: Keystone auth failures (T+35s to T+60s)
    print("🔑 Phase 2: Keystone Authentication Failures...")

    for i in range(5):
        logs.append({
            'timestamp': base_time + 35 + i*5,
            'level': 'ERROR',
            'service': 'keystone-api',
            'message': f'Database connection timeout after 30s. Cannot verify token {request_id}',
            'metadata': {'request_id': request_id, 'timeout': 30}
        })

    logs.append({
        'timestamp': base_time + 55,
        'level': 'CRITICAL',
        'service': 'keystone-api',
        'message': f'Authentication service degraded. 45% of requests failing. Request ID: {request_id}',
        'metadata': {'error_rate': 0.45, 'request_id': request_id}
    })

    # Phase 3: Nova compute failures (T+65s to T+120s)
    print("⚙️  Phase 3: Nova Compute Failures...")

    logs.append({
        'timestamp': base_time + 65,
        'level': 'ERROR',
        'service': 'nova-api',
        'message': f'Failed to validate token with Keystone for instance {instance_uuid}. Request ID: {request_id}',
        'metadata': {'instance_uuid': instance_uuid, 'request_id': request_id}
    })

    logs.append({
        'timestamp': base_time + 70,
        'level': 'ERROR',
        'service': 'nova-scheduler',
        'message': f'NoValidHost: No valid host found for instance {instance_uuid}. Authentication failed',
        'metadata': {'instance_uuid': instance_uuid, 'reason': 'auth_failure'}
    })

    logs.append({
        'timestamp': base_time + 75,
        'level': 'ERROR',
        'service': 'nova-compute',
        'message': f'Cannot boot instance {instance_uuid}: Keystone token validation timeout',
        'metadata': {'instance_uuid': instance_uuid}
    })

    # Phase 4: Neutron network failures (T+80s to T+130s)
    print("🌐 Phase 4: Neutron Network Allocation Failures...")

    port_uuid = str(uuid.uuid4())
    logs.append({
        'timestamp': base_time + 80,
        'level': 'ERROR',
        'service': 'neutron-server',
        'message': f'Failed to allocate network port {port_uuid} for instance {instance_uuid}. Database unavailable',
        'metadata': {'port_uuid': port_uuid, 'instance_uuid': instance_uuid}
    })

    logs.append({
        'timestamp': base_time + 85,
        'level': 'ERROR',
        'service': 'neutron-dhcp-agent',
        'message': f'Cannot assign IP to port {port_uuid}. DHCP lease write failed',
        'metadata': {'port_uuid': port_uuid}
    })

    # Phase 5: Multiple VM boot failures (T+90s to T+180s)
    print("💥 Phase 5: Multiple VM Boot Failures...")

    for i in range(8):
        fail_uuid = str(uuid.uuid4())
        logs.append({
            'timestamp': base_time + 90 + i*10,
            'level': 'ERROR',
            'service': 'nova-compute',
            'message': f'VM boot failed for instance {fail_uuid}. Networking setup failed',
            'metadata': {'instance_uuid': fail_uuid, 'error': 'NetworkingSetupFailed'}
        })

        logs.append({
            'timestamp': base_time + 92 + i*10,
            'level': 'ERROR',
            'service': 'nova-api',
            'message': f'Build failure for instance {fail_uuid}. State: ERROR',
            'metadata': {'instance_uuid': fail_uuid, 'state': 'ERROR'}
        })

    # Add some normal logs (noise)
    print("📝 Adding normal operational logs (noise)...")

    normal_messages = [
        'Periodic task completed successfully',
        'Health check passed',
        'Service heartbeat sent',
        'Cache cleanup completed',
        'Metrics collected and sent to monitoring'
    ]

    for service_type, service_list in SERVICES.items():
        for service in service_list:
            for i in range(3):
                logs.append({
                    'timestamp': base_time + random.randint(0, 180),
                    'level': 'INFO',
                    'service': service,
                    'message': random.choice(normal_messages),
                    'metadata': {}
                })

    # Phase 6: Recovery logs (T+200s to T+300s)
    print("✅ Phase 6: Recovery...")

    logs.append({
        'timestamp': base_time + 200,
        'level': 'WARN',
        'service': 'mysql-server',
        'message': 'Database connection pool manually increased to 1000',
        'metadata': {'pool_size': 1000}
    })

    logs.append({
        'timestamp': base_time + 210,
        'level': 'INFO',
        'service': 'keystone-api',
        'message': 'Authentication service recovering. Error rate down to 5%',
        'metadata': {'error_rate': 0.05}
    })

    logs.append({
        'timestamp': base_time + 220,
        'level': 'INFO',
        'service': 'nova-compute',
        'message': 'Successfully booted instance. Services nominal',
        'metadata': {'instance_uuid': str(uuid.uuid4())}
    })

    print(f"\n✅ Generated {len(logs)} log entries")
    print(f"   Errors: {sum(1 for l in logs if l['level'] == 'ERROR')}")
    print(f"   Critical: {sum(1 for l in logs if l['level'] == 'CRITICAL')}")
    print(f"   Warnings: {sum(1 for l in logs if l['level'] == 'WARN')}")
    print(f"   Info: {sum(1 for l in logs if l['level'] == 'INFO')}")

    return logs


def ingest_logs(logs):
    """Send logs to InfraAgent API"""

    print("\n📤 Ingesting logs to InfraAgent...")

    # Choose URL based on environment
    # For local testing: http://localhost:8000
    # For production: https://infraagent-14zf.onrender.com
    url = "http://localhost:8000/api/logs/ingest"

    # To use production, uncomment this line:
    # url = "https://infraagent-14zf.onrender.com/api/logs/ingest"

    try:
        response = requests.post(url, json={'logs': logs})
        response.raise_for_status()

        result = response.json()
        print(f"✅ Successfully ingested {result.get('count', 0)} logs")
        return True

    except requests.exceptions.ConnectionError:
        print(f"❌ Error: Cannot connect to InfraAgent backend at {url}")
        if "localhost" in url:
            print("   Make sure the backend is running: cd backend && python3 main.py")
        else:
            print("   Make sure the Render backend is accessible")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_ai_analysis():
    """Test the AI analysis endpoint"""

    print("\n🤖 Testing AI Analysis...")

    # Use same environment as log ingestion
    url = "http://localhost:8000/api/ai/analyze"
    # url = "https://infraagent-14zf.onrender.com/api/ai/analyze"

    try:
        response = requests.post(url, json={
            'include_remediation': True
        })
        response.raise_for_status()

        result = response.json()

        print(f"\n✅ AI Analysis Complete!")
        print(f"   Status: {result.get('status')}")
        print(f"   Logs analyzed: {result.get('logs_analyzed')}")
        print(f"   Unique patterns: {result.get('patterns', {}).get('unique_patterns', 0)}")
        print(f"   Incidents found: {len(result.get('incidents', []))}")

        if result.get('root_cause_analysis'):
            rca = result['root_cause_analysis']
            print(f"\n🔍 Root Cause Analysis:")
            print(f"   Root Cause: {rca.get('root_cause', 'N/A')}")
            print(f"   Impact: {rca.get('impact', 'N/A')}")
            print(f"   Confidence: {rca.get('confidence', 0)*100:.0f}%")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_nl_query():
    """Test natural language query"""

    print("\n💬 Testing Natural Language Query...")

    # Use same environment as log ingestion
    url = "http://localhost:8000/api/ai/nl-query"
    # url = "https://infraagent-14zf.onrender.com/api/ai/nl-query"

    queries = [
        "Why are VMs failing to boot?",
        "What caused the database connection issues?",
        "Show me authentication errors"
    ]

    for query in queries:
        print(f"\n   Q: {query}")

        try:
            response = requests.post(url, json={'query': query, 'hours': 2})
            response.raise_for_status()

            result = response.json()
            answer = result.get('answer', 'No answer')
            print(f"   A: {answer[:200]}...")

        except Exception as e:
            print(f"   ❌ Error: {e}")
            continue

    return True


if __name__ == "__main__":
    print("=" * 80)
    print("  INFRAAGENT - OPENSTACK TEST DATA GENERATOR")
    print("  Simulating: Database Pool Exhaustion → Cascading Failures")
    print("=" * 80)

    # Generate logs
    logs = generate_cascading_failure()

    # Ingest to API
    if ingest_logs(logs):
        print("\n" + "=" * 80)
        print("  TESTING AI CAPABILITIES")
        print("=" * 80)

        # Give backend a moment to process
        time.sleep(2)

        # Test AI analysis
        test_ai_analysis()

        # Test NL queries
        test_nl_query()

        print("\n" + "=" * 80)
        print("  ✅ COMPLETE! Open http://localhost:5174 to view logs")
        print("=" * 80)

    print("\n💡 Next steps:")
    print("   1. Open http://localhost:5174")
    print("   2. Click 'Logs' tab")
    print("   3. Set time range to 'All Time'")
    print("   4. See the cascading failure timeline!")
