from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Request
from datetime import datetime, timezone
from typing import Dict, List
from bson import ObjectId
import json
import asyncio
from jose import jwt
import os
from src.config import Config

router = APIRouter()

# Store active WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
    
    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass
    
    async def broadcast(self, message: dict):
        for user_id in self.active_connections:
            await self.send_personal_message(message, user_id)

manager = ConnectionManager()

# WebSocket endpoint for real-time notifications
@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive and listen for messages
            data = await websocket.receive_text()
            # Echo back or handle client messages if needed
            await websocket.send_json({"type": "ack", "message": "received"})
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)

# REST endpoints for notifications

@router.get("/")
async def get_notifications(request: Request, limit: int = 50, unread_only: bool = False):
    """Get user notifications"""
    db = request.app.state.db
    
    # Get user from auth header
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = auth_header.replace("Bearer ", "")
    
    # Decode token to get user_id
    # import jwt (removed)
    # import os (removed)
    try:
        payload = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("userId")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    query = {"userId": user_id}
    if unread_only:
        query["read"] = False
    
    cursor = db.notifications.find(query).sort("createdAt", -1).limit(limit)
    notifications = await cursor.to_list(length=limit)
    
    # Count unread
    unread_count = await db.notifications.count_documents({"userId": user_id, "read": False})
    
    for n in notifications:
        n["id"] = str(n.pop("_id"))
        if "createdAt" in n:
            n["createdAt"] = n["createdAt"].isoformat()
    
    return {
        "notifications": notifications,
        "unreadCount": unread_count,
        "total": len(notifications)
    }

@router.post("/")
async def create_notification(request: Request):
    """Create a new notification (admin/system use)"""
    db = request.app.state.db
    data = await request.json()
    
    notification = {
        "userId": data.get("userId"),
        "type": data.get("type", "info"),  # info, warning, error, success, security
        "title": data.get("title"),
        "message": data.get("message"),
        "link": data.get("link"),
        "read": False,
        "createdAt": datetime.now(timezone.utc)
    }
    
    result = await db.notifications.insert_one(notification)
    notification["id"] = str(result.inserted_id)
    if "_id" in notification:
        del notification["_id"]
    
    # Send real-time notification via WebSocket
    if notification["userId"]:
        await manager.send_personal_message({
            "type": "notification",
            "data": {
                **notification,
                "createdAt": notification["createdAt"].isoformat()
            }
        }, notification["userId"])
    
    return {"success": True, "notification": notification}

@router.put("/{notification_id}/read")
async def mark_as_read(notification_id: str, request: Request):
    """Mark notification as read"""
    db = request.app.state.db
    
    result = await db.notifications.update_one(
        {"_id": ObjectId(notification_id)},
        {"$set": {"read": True, "readAt": datetime.now(timezone.utc)}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"success": True, "message": "Marked as read"}

@router.put("/mark-all-read")
async def mark_all_as_read(request: Request):
    """Mark all notifications as read for a user"""
    db = request.app.state.db
    
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = auth_header.replace("Bearer ", "")
    
    # import jwt (removed)
    # import os (removed)
    try:
        payload = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("userId")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    result = await db.notifications.update_many(
        {"userId": user_id, "read": False},
        {"$set": {"read": True, "readAt": datetime.now(timezone.utc)}}
    )
    
    return {"success": True, "markedRead": result.modified_count}

@router.delete("/{notification_id}")
async def delete_notification(notification_id: str, request: Request):
    """Delete a notification"""
    db = request.app.state.db
    
    result = await db.notifications.delete_one({"_id": ObjectId(notification_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"success": True, "message": "Notification deleted"}

@router.delete("/")
async def clear_all_notifications(request: Request):
    """Clear all notifications for a user"""
    db = request.app.state.db
    
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = auth_header.replace("Bearer ", "")
    
    # import jwt (removed)
    # import os (removed)
    try:
        payload = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("userId")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    result = await db.notifications.delete_many({"userId": user_id})
    
    return {"success": True, "deleted": result.deleted_count}

# Utility function to create security notifications
async def create_security_notification(db, user_id: str, event_type: str, details: dict):
    """Helper to create security-related notifications"""
    notification_templates = {
        "login_success": {
            "type": "info",
            "title": "New Login",
            "message": f"New login from {details.get('ip', 'unknown')} at {details.get('location', 'unknown')}"
        },
        "login_failed": {
            "type": "warning",
            "title": "Failed Login Attempt",
            "message": f"Failed login attempt from {details.get('ip', 'unknown')}"
        },
        "password_changed": {
            "type": "success",
            "title": "Password Changed",
            "message": "Your password was successfully changed"
        },
        "threat_detected": {
            "type": "error",
            "title": "Threat Detected",
            "message": f"Security threat detected: {details.get('threat_type', 'Unknown threat')}"
        },
        "attack_blocked": {
            "type": "success",
            "title": "Attack Blocked",
            "message": f"Blocked {details.get('attack_type', 'attack')} from {details.get('source', 'unknown source')}"
        }
    }
    
    template = notification_templates.get(event_type, {
        "type": "info",
        "title": event_type.replace("_", " ").title(),
        "message": str(details)
    })
    
    notification = {
        "userId": user_id,
        **template,
        "metadata": details,
        "read": False,
        "createdAt": datetime.now(timezone.utc)
    }
    
    result = await db.notifications.insert_one(notification)
    notification["id"] = str(result.inserted_id)
    
    # Send via WebSocket
    await manager.send_personal_message({
        "type": "notification",
        "data": {
            **notification,
            "createdAt": notification["createdAt"].isoformat(),
            "_id": str(notification.get("_id", ""))
        }
    }, user_id)
    
    return notification
