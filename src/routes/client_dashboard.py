from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timedelta
# import jwt
from jose import jwt, ExpiredSignatureError, JWTError
import os
from bson import ObjectId

router = APIRouter()

from src.config import Config
JWT_SECRET = Config.JWT_SECRET

def verify_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_user_from_request(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Access denied. No token provided.")
    token = auth_header.replace("Bearer ", "")
    return verify_token(token)

@router.get("/overview")
async def get_overview(request: Request):
    payload = get_user_from_request(request)
    db = request.app.state.db
    
    now = datetime.utcnow()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    
    total_events = await db.security_events.count_documents({})
    events_24h = await db.security_events.count_documents({"createdAt": {"$gte": last_24h}})
    events_7d = await db.security_events.count_documents({"createdAt": {"$gte": last_7d}})
    critical_events = await db.security_events.count_documents({"severity": "critical", "createdAt": {"$gte": last_7d}})
    blocked_attacks = await db.security_events.count_documents({"status": "blocked", "createdAt": {"$gte": last_24h}})
    
    # Calculate trends
    prev_week_start = last_7d - timedelta(days=7)
    prev_week_events = await db.security_events.count_documents({
        "createdAt": {"$gte": prev_week_start, "$lt": last_7d}
    })
    
    trends_direction = "increase" if events_7d > prev_week_events else "decrease"
    trends_percentage = abs((events_7d - prev_week_events) / max(prev_week_events, 1) * 100)
    
    return {
        "overview": {
            "totalEvents": total_events,
            "events24h": events_24h,
            "events7d": events_7d,
            "criticalEvents": critical_events,
            "blockedAttacks": blocked_attacks,
            "systemUptime": 99.87,
            "trends": {
                "direction": trends_direction,
                "percentage": round(trends_percentage, 2)
            }
        },
        "lastUpdated": now.isoformat()
    }

@router.get("/attack-insights")
async def get_attack_insights(request: Request, period: str = "7d"):
    payload = get_user_from_request(request)
    db = request.app.state.db
    
    if period == "24h":
        start_date = datetime.utcnow() - timedelta(hours=24)
    elif period == "30d":
        start_date = datetime.utcnow() - timedelta(days=30)
    else:
        start_date = datetime.utcnow() - timedelta(days=7)
    
    # Aggregate by event type
    events_by_type = await db.security_events.aggregate([
        {"$match": {"createdAt": {"$gte": start_date}}},
        {"$group": {"_id": "$eventType", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]).to_list(length=100)
    
    # Aggregate by severity
    events_by_severity = await db.security_events.aggregate([
        {"$match": {"createdAt": {"$gte": start_date}}},
        {"$group": {"_id": "$severity", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]).to_list(length=100)
    
    # Top source IPs
    top_source_ips = await db.security_events.aggregate([
        {"$match": {"createdAt": {"$gte": start_date}, "source.ip": {"$exists": True}}},
        {"$group": {"_id": "$source.ip", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]).to_list(length=10)
    
    return {
        "attackInsights": {
            "eventsByType": events_by_type,
            "eventsBySeverity": events_by_severity,
            "topSourceIPs": top_source_ips,
            "period": period
        }
    }

@router.get("/defense-metrics")
async def get_defense_metrics(request: Request):
    payload = get_user_from_request(request)
    db = request.app.state.db
    
    last_7d = datetime.utcnow() - timedelta(days=7)
    
    total_blocked = await db.security_events.count_documents({"status": "blocked", "createdAt": {"$gte": last_7d}})
    total_detected = await db.security_events.count_documents({"createdAt": {"$gte": last_7d}})
    mitigation_rate = await db.security_events.count_documents({
        "status": {"$in": ["blocked", "resolved"]},
        "createdAt": {"$gte": last_7d}
    })
    
    blocking_efficiency = (total_blocked / max(total_detected, 1)) * 100
    mitigation_efficiency = (mitigation_rate / max(total_detected, 1)) * 100
    
    return {
        "defenseMetrics": {
            "blockingEfficiency": round(blocking_efficiency, 2),
            "mitigationEfficiency": round(mitigation_efficiency, 2),
            "averageResponseTime": 0.85,
            "totalBlocked": total_blocked,
            "totalDetected": total_detected,
            "securityScore": round((blocking_efficiency + mitigation_efficiency) / 2, 2)
        }
    }

@router.get("/activity-logs")
async def get_activity_logs(request: Request, page: int = 1, limit: int = 50, eventType: str = None, severity: str = None):
    payload = get_user_from_request(request)
    db = request.app.state.db
    
    query = {}
    if eventType:
        query["eventType"] = eventType
    if severity:
        query["severity"] = severity
    
    skip = (page - 1) * limit
    cursor = db.security_events.find(query).sort("createdAt", -1).skip(skip).limit(limit)
    logs = await cursor.to_list(length=limit)
    total = await db.security_events.count_documents(query)
    
    for log in logs:
        log["id"] = str(log.pop("_id"))
        if "createdAt" in log:
            log["createdAt"] = log["createdAt"].isoformat()
    
    return {
        "activityLogs": logs,
        "pagination": {
            "currentPage": page,
            "totalPages": (total + limit - 1) // limit,
            "totalLogs": total,
            "hasNextPage": page * limit < total,
            "hasPrevPage": page > 1
        }
    }

@router.get("/system-health")
async def get_system_health(request: Request):
    payload = get_user_from_request(request)
    
    # Mock system health data
    return {
        "systemHealth": {
            "services": [
                {"name": "API Gateway", "status": "healthy", "uptime": "99.9%", "responseTime": "45ms"},
                {"name": "Database", "status": "healthy", "uptime": "99.8%", "responseTime": "12ms"},
                {"name": "Authentication", "status": "healthy", "uptime": "99.9%", "responseTime": "23ms"},
                {"name": "Monitoring", "status": "healthy", "uptime": "99.7%", "responseTime": "67ms"},
                {"name": "Email Service", "status": "warning", "uptime": "98.5%", "responseTime": "156ms"}
            ],
            "serverStats": {
                "cpuUsage": 45.2,
                "memoryUsage": 67.8,
                "diskUsage": 34.1,
                "networkLatency": 12.5
            },
            "alerts": [
                {"type": "warning", "message": "High memory usage detected on server-02"},
                {"type": "info", "message": "Scheduled maintenance completed successfully"}
            ],
            "lastCheck": datetime.utcnow().isoformat()
        }
    }
