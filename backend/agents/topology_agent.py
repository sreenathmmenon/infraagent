"""Topology Agent - Maps infrastructure dependencies"""

from typing import Dict, Any, List, Set
import json
from pathlib import Path


class TopologyAgent:
    """
    Maps infrastructure topology to understand:
    - Service dependencies
    - Blast radius
    - Downstream impact
    """

    def __init__(self, topology_file: str = None):
        self.name = "Topology Agent"
        self.topology_file = topology_file or "backend/mock_infra/topology.json"
        self.topology_data = self._load_topology()

    def _load_topology(self) -> Dict[str, Any]:
        """Load topology data from mock file"""
        try:
            topology_path = Path(__file__).parent.parent / "mock_infra" / "topology.json"
            with open(topology_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load topology data: {e}")
            return {"servers": [], "network_paths": []}

    async def get_context(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get topology context for an alert

        Args:
            analysis: Analysis from Alert Agent

        Returns:
            Topology context with dependencies and blast radius
        """
        alert_source = analysis.get("alert_id", "").split("-")[0]

        # Find the affected server
        affected_server = None
        for server in self.topology_data.get("servers", []):
            if analysis.get("alert_id"):
                # Extract server name from alert context if available
                affected_server = server
                break

        # For demo, map alert to server based on common patterns
        for server in self.topology_data.get("servers", []):
            # Simple matching - in production would use proper mapping
            if "web" in server["id"] and "CPU" in str(analysis):
                affected_server = server
                break
            elif "db" in server["id"] and "DISK" in str(analysis):
                affected_server = server
                break
            elif "api" in server["id"] and "LATENCY" in str(analysis):
                affected_server = server
                break

        if not affected_server:
            # Default to first server for demo
            affected_server = self.topology_data.get("servers", [{}])[0]

        # Map dependencies
        dependencies = self._map_dependencies(affected_server)
        dependents = self._map_dependents(affected_server)

        # Calculate blast radius
        blast_radius = self._calculate_blast_radius(affected_server, dependents)

        topology_context = {
            "agent": "topology_agent",
            "timestamp": "2025-10-16T09:30:02Z",
            "duration": "0.8s",
            "completed": True,
            "affected_server": {
                "id": affected_server["id"],
                "type": affected_server["type"],
                "zone": affected_server["zone"],
                "ip": affected_server.get("ip", "unknown")
            },
            "dependencies": dependencies,
            "dependents": dependents,
            "blast_radius": blast_radius,
            "affected_count": len(blast_radius["directly_affected"]) + len(blast_radius["indirectly_affected"]),
            "critical_path": self._identify_critical_path(affected_server, dependencies),
            "network_context": self._get_network_context(affected_server)
        }

        return topology_context

    def _map_dependencies(self, server: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Map what this server depends on"""
        dependency_ids = server.get("dependencies", [])
        dependencies = []

        for dep_id in dependency_ids:
            dep_server = self._find_server(dep_id)
            if dep_server:
                dependencies.append({
                    "id": dep_server["id"],
                    "type": dep_server["type"],
                    "status": "healthy",  # Mock for demo
                    "criticality": "high" if dep_server["type"] in ["database", "cache"] else "medium"
                })

        return dependencies

    def _map_dependents(self, server: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Map what depends on this server"""
        dependent_ids = server.get("dependents", [])
        dependents = []

        for dep_id in dependent_ids:
            dep_server = self._find_server(dep_id)
            if dep_server:
                dependents.append({
                    "id": dep_server["id"],
                    "type": dep_server["type"],
                    "impact": "service degradation" if server.get("type") != "database" else "service outage"
                })

        return dependents

    def _calculate_blast_radius(
        self, affected_server: Dict[str, Any], dependents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate blast radius of an issue"""

        directly_affected = [dep["id"] for dep in dependents]

        # Find services that depend on the dependents (cascading impact)
        indirectly_affected = []
        for dependent_id in directly_affected:
            dep_server = self._find_server(dependent_id)
            if dep_server:
                indirect_deps = dep_server.get("dependents", [])
                indirectly_affected.extend([
                    dep for dep in indirect_deps
                    if dep not in directly_affected and dep != affected_server["id"]
                ])

        # Estimate customer impact
        customer_impact = self._estimate_customer_impact(
            affected_server, len(directly_affected), len(indirectly_affected)
        )

        return {
            "directly_affected": directly_affected,
            "indirectly_affected": list(set(indirectly_affected)),
            "total_services_at_risk": len(directly_affected) + len(set(indirectly_affected)),
            "estimated_customer_impact": customer_impact,
            "severity_multiplier": 1.5 if affected_server["type"] == "database" else 1.0
        }

    def _identify_critical_path(
        self, server: Dict[str, Any], dependencies: List[Dict[str, Any]]
    ) -> List[str]:
        """Identify critical path in dependency chain"""
        critical_path = []

        # Find database in dependencies (most critical)
        for dep in dependencies:
            if dep["criticality"] == "high":
                critical_path.append(dep["id"])

        critical_path.append(server["id"])

        # Add load balancer if server has dependents
        if server.get("dependents"):
            for dependent_id in server["dependents"]:
                dep_server = self._find_server(dependent_id)
                if dep_server and dep_server["type"] == "load-balancer":
                    critical_path.append(dependent_id)

        return critical_path

    def _get_network_context(self, server: Dict[str, Any]) -> Dict[str, Any]:
        """Get network context for the server"""
        zone = server.get("zone", "unknown")

        # Find network paths for this zone
        network_paths = self.topology_data.get("network_paths", [])
        relevant_paths = [
            path for path in network_paths
            if zone.split("-")[0] in path.get("route", "")
        ]

        return {
            "zone": zone,
            "available_paths": len(relevant_paths),
            "paths": [
                {
                    "id": path["id"],
                    "route": path["route"],
                    "status": path["status"],
                    "latency_avg": path.get("latency_avg", "unknown")
                }
                for path in relevant_paths
            ]
        }

    def _find_server(self, server_id: str) -> Dict[str, Any]:
        """Find server by ID in topology"""
        for server in self.topology_data.get("servers", []):
            if server["id"] == server_id:
                return server
        return None

    def _estimate_customer_impact(
        self, affected_server: Dict[str, Any], direct_count: int, indirect_count: int
    ) -> str:
        """Estimate customer impact based on topology"""
        server_type = affected_server.get("type", "unknown")

        if server_type == "database":
            return "HIGH - Potential data loss, complete service outage"
        elif server_type == "load-balancer":
            return "CRITICAL - All customer traffic affected"
        elif direct_count + indirect_count > 3:
            return "HIGH - Multiple services degraded or unavailable"
        elif direct_count > 0:
            return "MEDIUM - Partial service degradation"
        else:
            return "LOW - Isolated component, minimal customer visibility"
