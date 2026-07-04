"""
Architecture Map Generation API
Generates software architecture diagrams from scan results
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict, Optional
from pydantic import BaseModel
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

router = APIRouter(prefix="/api/architecture", tags=["architecture"])

# MongoDB connection
MONGODB_URI = os.getenv("MONGO_URL", "mongodb://localhost:27017/")
client = MongoClient(MONGODB_URI)
db_name = os.getenv("MONGO_DB", "purpleops")
db = client[db_name]


# Pydantic models
class ArchitectureNode(BaseModel):
    id: str
    name: str
    type: str  # web-service, database, api, external, infrastructure
    technology: Optional[str] = None
    version: Optional[str] = None
    port: Optional[int] = None
    x: int
    y: int
    vulnerabilities: int = 0
    description: Optional[str] = None
    vulnerabilityDetails: List[Dict] = []


class ArchitectureConnection(BaseModel):
    from_node: str  # Renamed from 'from' as it's a Python keyword
    to_node: str  # Renamed from 'to'
    protocol: Optional[str] = "HTTP"
    port: Optional[int] = None
    vulnerable: bool = False

    class Config:
        # Allow field aliases for JSON serialization
        fields = {
            'from_node': 'from',
            'to_node': 'to'
        }


class ArchitectureData(BaseModel):
    nodes: List[ArchitectureNode]
    connections: List[ArchitectureConnection]


class ArchitectureResponse(BaseModel):
    executionId: str
    target: str
    createdAt: datetime
    architecture: ArchitectureData
    totalComponents: int
    totalConnections: int
    vulnerableComponents: int


# Helper functions
def detect_component_type(service_name: str, port: Optional[int] = None) -> str:
    """Detect component type based on service name and port"""
    service_lower = service_name.lower()
    
    # Database detection
    if any(db in service_lower for db in ['mongodb', 'mysql', 'postgresql', 'redis', 'mariadb', 'oracle', 'mssql']):
        return 'database'
    
    # API detection
    if any(api in service_lower for api in ['api', 'rest', 'graphql', 'grpc']):
        return 'api'
    
    # Web service detection
    if any(web in service_lower for web in ['nginx', 'apache', 'iis', 'http', 'web']):
        return 'web-service'
    
    # Infrastructure
    if any(infra in service_lower for infra in ['cache', 'queue', 'cdn', 'storage', 's3', 'cloudflare']):
        return 'infrastructure'
    
    # Port-based detection
    if port:
        if port in [80, 443, 8080, 3000, 4200]:
            return 'web-service'
        elif port in [27017, 3306, 5432, 6379]:
            return 'database'
        elif port in [8000, 8001, 9000]:
            return 'api'
    
    # Default
    return 'external'


def calculate_node_positions(num_nodes: int, canvas_width: int = 800, canvas_height: int = 600) -> List[tuple]:
    """Calculate evenly distributed positions for nodes"""
    import math
    
    positions = []
    
    if num_nodes == 0:
        return positions
    
    # Arrange in a grid pattern
    cols = math.ceil(math.sqrt(num_nodes))
    rows = math.ceil(num_nodes / cols)
    
    x_spacing = canvas_width / (cols + 1)
    y_spacing = canvas_height / (rows + 1)
    
    for i in range(num_nodes):
        col = i % cols
        row = i // cols
        x = int((col + 1) * x_spacing)
        y = int((row + 1) * y_spacing)
        positions.append((x, y))
    
    return positions


def extract_architecture_from_scan(execution):
    """Extract architecture components from scan execution data"""
    nodes = []
    connections = []
    node_map = {}
    
    # Get agent results for this execution
    agent_results = list(db.agent_results.find({"execution_id": execution["execution_id"]}))
    
    # Get vulnerabilities
    vulnerabilities = list(db.vulnerabilities.find({"execution_id": execution["execution_id"]}))
    vuln_by_component = {}
    for vuln in vulnerabilities:
        component = vuln.get("affected_component", "Unknown")
        if component not in vuln_by_component:
            vuln_by_component[component] = []
        vuln_by_component[component].append({
            "id": vuln.get("vulnerability_id", ""),
            "title": vuln.get("title", ""),
            "severity": vuln.get("severity", "low"),
            "description": vuln.get("description", "")
        })
    
    # Extract components from agent results
    discovered_services = []
    for result in agent_results:
        if result.get("agent_name") in ["recon_agent", "scanner_agent", "port_scanner"]:
            # Extract discovered services
            result_data = result.get("result", {})
            
            # Mock service discovery (in real implementation, parse actual scan results)
            if result.get("agent_name") == "recon_agent":
                # Add web server
                discovered_services.append({
                    "name": f"Web Server - {execution['target']}",
                    "type": "web-service",
                    "technology": "Nginx",
                    "version": "1.21.0",
                    "port": 80,
                    "component": "Web Server"
                })
                
                # Add CDN
                discovered_services.append({
                    "name": "CDN",
                    "type": "infrastructure",
                    "technology": "Cloudflare",
                    "component": "CDN"
                })
            
            elif result.get("agent_name") == "scanner_agent":
                # Add application server
                discovered_services.append({
                    "name": "Application Server",
                    "type": "web-service",
                    "technology": "Node.js",
                    "version": "16.14.0",
                    "port": 3000,
                    "component": "Application Server"
                })
                
                # Add database
                discovered_services.append({
                    "name": "Database",
                    "type": "database",
                    "technology": "MongoDB",
                    "version": "5.0.6",
                    "port": 27017,
                    "component": "Database"
                })
                
                # Add API
                discovered_services.append({
                    "name": "REST API",
                    "type": "api",
                    "technology": "Express",
                    "version": "4.17.1",
                    "port": 8000,
                    "component": "API Endpoints"
                })
                
                # Add cache
                discovered_services.append({
                    "name": "Cache Server",
                    "type": "infrastructure",
                    "technology": "Redis",
                    "version": "6.2.0",
                    "port": 6379,
                    "component": "Cache"
                })
                
                # Add storage
                discovered_services.append({
                    "name": "Object Storage",
                    "type": "infrastructure",
                    "technology": "AWS S3",
                    "component": "Storage"
                })
    
    # Calculate positions
    positions = calculate_node_positions(len(discovered_services))
    
    # Create nodes
    for i, service in enumerate(discovered_services):
        node_id = f"node_{i}"
        component_name = service.get("component", service["name"])
        
        # Get vulnerabilities for this component
        component_vulns = vuln_by_component.get(component_name, [])
        
        node = ArchitectureNode(
            id=node_id,
            name=service["name"],
            type=service.get("type", "web-service"),
            technology=service.get("technology"),
            version=service.get("version"),
            port=service.get("port"),
            x=positions[i][0],
            y=positions[i][1],
            vulnerabilities=len(component_vulns),
            description=f"{service['type'].replace('-', ' ').title()} component",
            vulnerabilityDetails=component_vulns
        )
        nodes.append(node)
        node_map[service["name"]] = node_id
    
    # Create connections (simple heuristic-based)
    connection_rules = [
        ("Web Server", "Application Server", "HTTP", 3000),
        ("Application Server", "Database", "MongoDB", 27017),
        ("Application Server", "REST API", "REST", 8000),
        ("REST API", "Cache Server", "Redis", 6379),
        ("Web Server", "CDN", "HTTP", None),
        ("Application Server", "Object Storage", "S3", None),
    ]
    
    for from_name, to_name, protocol, port in connection_rules:
        # Check if both nodes exist
        from_full_name = None
        to_full_name = None
        
        for service in discovered_services:
            if from_name in service["name"]:
                from_full_name = service["name"]
            if to_name in service["name"]:
                to_full_name = service["name"]
        
        if from_full_name and to_full_name:
            # Check if connection is vulnerable
            vulnerable = False
            for vuln in vulnerabilities:
                affected = vuln.get("affected_component", "")
                if from_name in affected or to_name in affected:
                    if vuln.get("severity") in ["critical", "high"]:
                        vulnerable = True
                        break
            
            connection = ArchitectureConnection(
                from_node=node_map[from_full_name],
                to_node=node_map[to_full_name],
                protocol=protocol,
                port=port,
                vulnerable=vulnerable
            )
            connections.append(connection)
    
    return ArchitectureData(nodes=nodes, connections=connections)


# API Endpoints
@router.get("/{execution_id}", response_model=ArchitectureResponse)
async def get_architecture_by_execution(execution_id: str):
    """
    Get architecture map for a specific execution
    """
    # Find execution
    execution = db.executions.find_one({"execution_id": execution_id})
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution {execution_id} not found"
        )
    
    # Extract architecture
    architecture = extract_architecture_from_scan(execution)
    
    # Calculate statistics
    vulnerable_components = sum(1 for node in architecture.nodes if node.vulnerabilities > 0)
    
    return ArchitectureResponse(
        executionId=execution_id,
        target=execution.get("target", "Unknown"),
        createdAt=execution.get("created_at", datetime.now(timezone.utc)),
        architecture=architecture,
        totalComponents=len(architecture.nodes),
        totalConnections=len(architecture.connections),
        vulnerableComponents=vulnerable_components
    )


@router.get("/", response_model=List[Dict])
async def list_available_architectures():
    """
    List all available architecture maps (completed scans)
    """
    executions = list(db.executions.find(
        {"status": "completed"},
        {"execution_id": 1, "target": 1, "created_at": 1, "status": 1}
    ).sort("created_at", -1).limit(50))
    
    result = []
    for execution in executions:
        result.append({
            "executionId": execution["execution_id"],
            "target": execution.get("target", "Unknown"),
            "createdAt": execution.get("created_at"),
            "status": execution.get("status")
        })
    
    return result
