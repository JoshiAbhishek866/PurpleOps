from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId

class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, handler):
        if isinstance(v, ObjectId):
            return str(v)
        return str(v)

# Admin User
class AdminUser(BaseModel):
    email: EmailStr
    password: str
    firstName: str
    lastName: str
    role: str = "admin"
    permissions: List[str] = []
    
class AdminUserInDB(AdminUser):
    id: Optional[str] = None
    createdAt: Optional[datetime] = None

class AdminLogin(BaseModel):
    email: EmailStr
    password: str

# Client User  
class ClientUser(BaseModel):
    email: EmailStr
    password: str
    firstName: str
    lastName: str
    company: str
    role: str = "viewer"

class ClientUserInDB(ClientUser):
    id: Optional[str] = None
    isActive: bool = True
    lastLogin: Optional[datetime] = None
    loginAttempts: int = 0
    lockUntil: Optional[datetime] = None
    createdAt: Optional[datetime] = None

class ClientLogin(BaseModel):
    email: EmailStr
    password: str

# Website Content
class WebsiteContent(BaseModel):
    section: str
    content: dict

# Blog Post
class BlogPost(BaseModel):
    title: str
    content: str
    excerpt: Optional[str] = ""
    author: str = "Admin"
    category: str = "General"
    tags: List[str] = []
    status: str = "draft"
    featuredImage: Optional[str] = None

class BlogPostInDB(BlogPost):
    id: Optional[str] = None
    slug: Optional[str] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

# Client Company
class ClientCompany(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    industry: Optional[str] = None
    subscription: str = "basic"
    services: List[str] = []
    isActive: bool = True

class ClientCompanyInDB(ClientCompany):
    id: Optional[str] = None
    createdAt: Optional[datetime] = None

# Demo Request
class DemoRequest(BaseModel):
    firstName: str
    lastName: str
    email: EmailStr
    company: str
    phone: Optional[str] = None
    message: Optional[str] = None
    companySize: Optional[str] = None
    preferredDate: Optional[str] = None

class DemoRequestInDB(DemoRequest):
    id: Optional[str] = None
    status: str = "new"
    createdAt: Optional[datetime] = None

# Security Event (for client dashboard)
class SecurityEvent(BaseModel):
    eventType: str
    severity: str
    description: str
    status: str = "detected"
    source: Optional[dict] = None
    target: Optional[dict] = None
    tags: List[str] = []

class SecurityEventInDB(SecurityEvent):
    id: Optional[str] = None
    createdAt: Optional[datetime] = None
