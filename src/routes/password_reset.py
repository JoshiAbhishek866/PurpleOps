from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timedelta
import secrets
import bcrypt

router = APIRouter()

# Token expiration times
PASSWORD_RESET_EXPIRY = timedelta(hours=1)
EMAIL_VERIFICATION_EXPIRY = timedelta(hours=24)

def generate_token():
    return secrets.token_urlsafe(32)

@router.post("/forgot-password")
async def forgot_password(request: Request):
    """Request password reset - generates reset token"""
    db = request.app.state.db
    data = await request.json()
    email = data.get("email", "").lower()
    
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    user = await db.users.find_one({"email": email})
    if not user:
        # Don't reveal if user exists - return success anyway
        return {"message": "If an account exists with this email, a reset link has been sent"}
    
    # Generate reset token
    reset_token = generate_token()
    expires_at = datetime.utcnow() + PASSWORD_RESET_EXPIRY
    
    # Store token in database
    await db.password_resets.delete_many({"email": email})  # Remove old tokens
    await db.password_resets.insert_one({
        "email": email,
        "token": reset_token,
        "expiresAt": expires_at,
        "createdAt": datetime.utcnow()
    })
    
    # In production, send email here
    # For now, return token in response (for testing)
    reset_link = f"/auth/reset-password?token={reset_token}"
    
    return {
        "message": "If an account exists with this email, a reset link has been sent",
        "resetLink": reset_link,  # Remove in production
        "token": reset_token,  # Remove in production
        "expiresIn": "1 hour"
    }

@router.post("/verify-reset-token")
async def verify_reset_token(request: Request):
    """Verify if reset token is valid"""
    db = request.app.state.db
    data = await request.json()
    token = data.get("token")
    
    if not token:
        raise HTTPException(status_code=400, detail="Token is required")
    
    reset_record = await db.password_resets.find_one({"token": token})
    
    if not reset_record:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    if reset_record["expiresAt"] < datetime.utcnow():
        await db.password_resets.delete_one({"token": token})
        raise HTTPException(status_code=400, detail="Token has expired")
    
    return {"valid": True, "email": reset_record["email"]}

@router.post("/reset-password")
async def reset_password(request: Request):
    """Reset password using token"""
    db = request.app.state.db
    data = await request.json()
    token = data.get("token")
    new_password = data.get("newPassword")
    
    if not token or not new_password:
        raise HTTPException(status_code=400, detail="Token and new password are required")
    
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    
    reset_record = await db.password_resets.find_one({"token": token})
    
    if not reset_record:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    if reset_record["expiresAt"] < datetime.utcnow():
        await db.password_resets.delete_one({"token": token})
        raise HTTPException(status_code=400, detail="Token has expired")
    
    # Hash new password
    hashed_password = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    
    # Update user password
    result = await db.users.update_one(
        {"email": reset_record["email"]},
        {"$set": {"password": hashed_password, "updatedAt": datetime.utcnow()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Delete used token
    await db.password_resets.delete_one({"token": token})
    
    return {"message": "Password reset successful", "success": True}

@router.post("/send-verification")
async def send_verification_email(request: Request):
    """Send or resend email verification"""
    db = request.app.state.db
    data = await request.json()
    email = data.get("email", "").lower()
    
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.get("emailVerified"):
        return {"message": "Email is already verified"}
    
    # Generate verification token
    verification_token = generate_token()
    expires_at = datetime.utcnow() + EMAIL_VERIFICATION_EXPIRY
    
    # Store token
    await db.email_verifications.delete_many({"email": email})
    await db.email_verifications.insert_one({
        "email": email,
        "token": verification_token,
        "expiresAt": expires_at,
        "createdAt": datetime.utcnow()
    })
    
    verification_link = f"/auth/verify-email?token={verification_token}"
    
    return {
        "message": "Verification email sent",
        "verificationLink": verification_link,  # Remove in production
        "token": verification_token,  # Remove in production
        "expiresIn": "24 hours"
    }

@router.post("/verify-email")
async def verify_email(request: Request):
    """Verify email using token"""
    db = request.app.state.db
    data = await request.json()
    token = data.get("token")
    
    if not token:
        raise HTTPException(status_code=400, detail="Token is required")
    
    verification_record = await db.email_verifications.find_one({"token": token})
    
    if not verification_record:
        raise HTTPException(status_code=400, detail="Invalid or expired verification link")
    
    if verification_record["expiresAt"] < datetime.utcnow():
        await db.email_verifications.delete_one({"token": token})
        raise HTTPException(status_code=400, detail="Verification link has expired")
    
    # Update user as verified
    result = await db.users.update_one(
        {"email": verification_record["email"]},
        {"$set": {"emailVerified": True, "emailVerifiedAt": datetime.utcnow()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Delete used token
    await db.email_verifications.delete_one({"token": token})
    
    return {"message": "Email verified successfully", "success": True}

@router.get("/verification-status/{email}")
async def get_verification_status(email: str, request: Request):
    """Check email verification status"""
    db = request.app.state.db
    user = await db.users.find_one({"email": email.lower()})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "email": email.lower(),
        "verified": user.get("emailVerified", False),
        "verifiedAt": user.get("emailVerifiedAt")
    }
