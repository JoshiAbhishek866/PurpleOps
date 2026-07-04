from fastapi import APIRouter, HTTPException, Request, Depends
from datetime import datetime, timezone, timedelta
import bcrypt
# import jwt  <-- This was causing the conflict with the wrong 'jwt' library
from jose import jwt, ExpiredSignatureError, JWTError
import os

router = APIRouter()

from src.config import Config
JWT_SECRET = Config.ADMIN_JWT_SECRET

def create_token(user_id: str, email: str):
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=8)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/login")
async def admin_login(request: Request):
    db = request.app.state.db
    data = await request.json()
    
    email = data.get("email")
    password = data.get("password")
    
    try:
        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password required")
        
        user = await db.admin_users.find_one({"email": email})
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials (user not found)")
        
        # Debug 1: Check password types
        # print(f"Pass type: {type(password)}, Hash type: {type(user['password'])}")
        
        if not bcrypt.checkpw(password.encode("utf-8"), user["password"].encode("utf-8")):
            raise HTTPException(status_code=401, detail="Invalid credentials (pw mismatch)")
        
        token = create_token(str(user["_id"]), user["email"])
        
        # Ensure token is string for JSON serialization
        if isinstance(token, bytes):
            token = token.decode('utf-8')
        
        return {
            "success": True,
            "token": token,
            "admin": {
                "id": str(user["_id"]),
                "email": user["email"],
                "firstName": user.get("firstName", ""),
                "lastName": user.get("lastName", ""),
                "role": user.get("role", "admin")
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/me")
async def get_current_user(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No token provided")
    
    token = auth_header.replace("Bearer ", "")
    payload = verify_token(token)
    
    db = request.app.state.db
    from bson import ObjectId
    user = await db.admin_users.find_one({"_id": ObjectId(payload["user_id"])})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "user": {
            "id": str(user["_id"]),
            "email": user["email"],
            "firstName": user.get("firstName", ""),
            "lastName": user.get("lastName", ""),
            "role": user.get("role", "admin")
        }
    }
