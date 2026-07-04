
# Utility function to create admin notifications
async def create_admin_notification(db, notification_type: str, title: str, message: str, data: dict = None):
    """Helper to create notifications for admin panel"""
    from datetime import datetime, timezone
    
    notification = {
        "recipient": "admin",
        "type": notification_type,  # 'new_client', 'demo_request', 'security_alert', etc.
        "title": title,
        "message": message,
        "data": data or {},
        "read": False,
        "createdAt": datetime.now(timezone.utc),
        "readAt": None
    }
    
    result = await db.notifications.insert_one(notification)
    notification["_id"] = str(result.inserted_id)
    
    # Send real-time notification to all admin connections
    from .notifications import manager
    await manager.broadcast({
        "type": "admin_notification",
        "data": {
            **notification,
            "createdAt": notification["createdAt"].isoformat()
        }
    })
    
    return notification
