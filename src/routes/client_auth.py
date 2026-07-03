from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timedelta
import bcrypt
# import jwt
from jose import jwt, ExpiredSignatureError, JWTError
import os
import secrets

router = APIRouter()

from src.config import Config
JWT_SECRET = Config.JWT_SECRET

def create_token(user_id: str):
    payload = {
        "userId": user_id,
        "exp": datetime.utcnow() + timedelta(days=7)
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

@router.post("/register")
async def register(request: Request):
    db = request.app.state.db
    data = await request.json()
    
    email = data.get("email")
    password = data.get("password")
    firstName = data.get("firstName")
    lastName = data.get("lastName")
    company = data.get("company")
    
    if not all([email, password, firstName, lastName, company]):
        raise HTTPException(status_code=400, detail="All fields are required")
    
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    
    existing = await db.users.find_one({"email": email.lower()})
    if existing:
        raise HTTPException(status_code=409, detail="User already exists with this email")
    
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    user_doc = {
        "email": email.lower(),
        "password": hashed_password,
        "firstName": firstName,
        "lastName": lastName,
        "company": company,
        "role": "viewer",
        "isActive": True,
        "emailVerified": False,
        "loginAttempts": 0,
        "createdAt": datetime.utcnow()
    }
    
    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)
    
    # Generate email verification token
    verification_token = secrets.token_urlsafe(32)
    await db.email_verifications.insert_one({
        "email": email.lower(),
        "token": verification_token,
        "expiresAt": datetime.utcnow() + timedelta(hours=24),
        "createdAt": datetime.utcnow()
    })
    
    # Create welcome notification
    await db.notifications.insert_one({
        "userId": user_id,
        "type": "success",
        "title": "Welcome to PurpleOps!",
        "message": "Your account has been created. Please verify your email to access all features.",
        "read": False,
        "createdAt": datetime.utcnow()
    })
    
    token = create_token(user_id)
    
    return {
        "message": "User created successfully",
        "token": token,
        "user": {
            "id": user_id,
            "email": email.lower(),
            "firstName": firstName,
            "lastName": lastName,
            "role": "viewer",
            "company": company,
            "emailVerified": False
        }
    }

@router.post("/login")
async def login(request: Request):
    db = request.app.state.db
    data = await request.json()
    
    email = data.get("email")
    password = data.get("password")
    
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")
    
    user = await db.users.find_one({"email": email.lower()})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Check if locked
    if user.get("lockUntil") and user["lockUntil"] > datetime.utcnow():
        raise HTTPException(status_code=423, detail="Account temporarily locked")
    
    if not user.get("isActive", True):
        raise HTTPException(status_code=403, detail="Account is deactivated")
    
    if not bcrypt.checkpw(password.encode(), user["password"].encode()):
        # Increment login attempts
        attempts = user.get("loginAttempts", 0) + 1
        update = {"loginAttempts": attempts}
        if attempts >= 5:
            update["lockUntil"] = datetime.utcnow() + timedelta(hours=2)
        await db.users.update_one({"_id": user["_id"]}, {"$set": update})
        
        # Create failed login notification
        await db.notifications.insert_one({
            "userId": str(user["_id"]),
            "type": "warning",
            "title": "Failed Login Attempt",
            "message": f"Failed login attempt detected at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
            "read": False,
            "createdAt": datetime.utcnow()
        })
        
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Reset login attempts
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"loginAttempts": 0, "lastLogin": datetime.utcnow()}, "$unset": {"lockUntil": ""}}
    )
    
    user_id = str(user["_id"])
    token = create_token(user_id)
    
    # Create login success notification
    await db.notifications.insert_one({
        "userId": user_id,
        "type": "info",
        "title": "New Login",
        "message": f"Successful login at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
        "read": False,
        "createdAt": datetime.utcnow()
    })
    
    return {
        "success": True,
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user_id,
            "email": user["email"],
            "firstName": user.get("firstName", ""),
            "lastName": user.get("lastName", ""),
            "role": user.get("role", "viewer"),
            "company": user.get("company", ""),
            "emailVerified": user.get("emailVerified", False)
        }
    }

@router.get("/me")
async def get_profile(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No token provided")
    
    token = auth_header.replace("Bearer ", "")
    payload = verify_token(token)
    
    db = request.app.state.db
    from bson import ObjectId
    user = await db.users.find_one({"_id": ObjectId(payload["userId"])})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "user": {
            "id": str(user["_id"]),
            "email": user["email"],
            "firstName": user.get("firstName", ""),
            "lastName": user.get("lastName", ""),
            "role": user.get("role", "viewer"),
            "company": user.get("company", ""),
            "emailVerified": user.get("emailVerified", False)
        }
    }
