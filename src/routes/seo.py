"""
SEO Management API
Allows admin to manage SEO metadata for frontend pages
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict
from datetime import datetime, timezone
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()


# Pydantic models
class SEOMetadata(BaseModel):
    title: str
    description: str
    keywords: Optional[str] = ""
    ogImage: Optional[str] = None
    ogType: Optional[str] = "website"
    twitterCard: Optional[str] = "summary_large_image"
    twitterSite: Optional[str] = "@PurpleOps"
    canonical: Optional[str] = None
    robots: Optional[str] = "index, follow"
    author: Optional[str] = "PurpleOps Team"


class PageSEO(BaseModel):
    page: str  # home, about, blog, book-demo, vulnerability-detail, dashboard, etc.
    seo: SEOMetadata
    updatedAt: Optional[datetime] = None


class BulkSEOUpdate(BaseModel):
    pages: List[PageSEO]


class GlobalSEO(BaseModel):
    siteName: str = "PurpleOps"
    siteUrl: str = "https://PurpleOps.com"
    defaultOgImage: str = "https://PurpleOps.com/og-image.jpg"
    themeColor: str = "#8b5cf6"
    twitterSite: str = "@PurpleOps"
    defaultAuthor: str = "PurpleOps Team"


# API Endpoints
@router.get("/global")
async def get_global_seo(request: Request):
    """
    Get global SEO settings
    """
    db = request.app.state.db
    global_seo = await db.seo_settings.find_one({"type": "global"}, {"_id": 0})
    
    if not global_seo:
        # Return defaults
        return GlobalSEO().dict()
    
    return global_seo.get("settings", GlobalSEO().dict())


@router.put("/global")
async def update_global_seo(settings: GlobalSEO, request: Request):
    """
    Update global SEO settings (admin only)
    """
    db = request.app.state.db
    
    result = await db.seo_settings.update_one(
        {"type": "global"},
        {
            "$set": {
                "settings": settings.dict(),
                "updatedAt": datetime.now(timezone.utc)
            }
        },
        upsert=True
    )
    
    return {
        "message": "Global SEO settings updated successfully",
        "settings": settings.dict()
    }


@router.get("/pages")
async def get_all_pages_seo(request: Request):
    """
    Get SEO metadata for all pages
    """
    db = request.app.state.db
    cursor = db.seo_pages.find({}, {"_id": 0})
    pages = await cursor.to_list(length=100)
    
    return {"pages": pages}


@router.get("/pages/{page}")
async def get_page_seo(page: str, request: Request):
    """
    Get SEO metadata for a specific page
    """
    db = request.app.state.db
    page_seo = await db.seo_pages.find_one({"page": page}, {"_id": 0})
    
    if not page_seo:
        # Return default SEO for the page
        default_seo = get_default_seo(page)
        return {
            "page": page,
            "seo": default_seo,
            "isDefault": True
        }
    
    return page_seo


@router.put("/pages/{page}")
async def update_page_seo(page: str, seo: SEOMetadata, request: Request):
    """
    Update SEO metadata for a specific page (admin only)
    """
    db = request.app.state.db
    
    page_data = {
        "page": page,
        "seo": seo.dict(),
        "updatedAt": datetime.now(timezone.utc)
    }
    
    result = await db.seo_pages.update_one(
        {"page": page},
        {"$set": page_data},
        upsert=True
    )
    
    return {
        "message": f"SEO metadata updated for page: {page}",
        "page": page,
        "seo": seo.dict()
    }


@router.delete("/pages/{page}")
async def delete_page_seo(page: str, request: Request):
    """
    Delete custom SEO metadata for a page (reverts to defaults)
    """
    db = request.app.state.db
    
    result = await db.seo_pages.delete_one({"page": page})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail=f"SEO metadata not found for page: {page}"
        )
    
    return {
        "message": f"SEO metadata deleted for page: {page}",
        "page": page
    }


@router.post("/pages/bulk")
async def bulk_update_seo(bulk_update: BulkSEOUpdate, request: Request):
    """
    Bulk update SEO metadata for multiple pages
    """
    db = request.app.state.db
    
    updated_pages = []
    
    for page_seo in bulk_update.pages:
        page_data = {
            "page": page_seo.page,
            "seo": page_seo.seo.dict(),
            "updatedAt": datetime.now(timezone.utc)
        }
        
        await db.seo_pages.update_one(
            {"page": page_seo.page},
            {"$set": page_data},
            upsert=True
        )
        
        updated_pages.append(page_seo.page)
    
    return {
        "message": f"SEO metadata updated for {len(updated_pages)} pages",
        "pages": updated_pages
    }


def get_default_seo(page: str) -> dict:
    """
    Get default SEO metadata for a page
    """
    defaults = {
        "home": {
            "title": "Secure Your Digital Assets",
            "description": "Advanced cybersecurity analytics and threat detection platform designed for modern organizations. Real-time monitoring, AI-powered insights, and automated defense mechanisms.",
            "keywords": "cybersecurity, AI security, threat detection, vulnerability scanning, security analytics, penetration testing",
            "ogImage": "https://PurpleOps.com/og-home.jpg",
            "ogType": "website"
        },
        "about": {
            "title": "About PurpleOps",
            "description": "Learn about PurpleOps's mission to provide cutting-edge cybersecurity solutions. Our team of experts is dedicated to protecting organizations worldwide.",
            "keywords": "about PurpleOps, cybersecurity company, security experts, mission, team",
            "ogType": "website"
        },
        "blog": {
            "title": "Cybersecurity Blog",
            "description": "Latest news, insights, and best practices in cybersecurity. Stay updated with threat intelligence, security trends, and expert analysis.",
            "keywords": "cybersecurity blog, security news, threat intelligence, security trends",
            "ogType": "website"
        },
        "book-demo": {
            "title": "Schedule a Demo",
            "description": "Get a personalized demonstration of PurpleOps and see how we can strengthen your cybersecurity posture. Book your demo today.",
            "keywords": "schedule demo, book demo, cybersecurity demo, product demonstration",
            "ogType": "website"
        },
        "dashboard": {
            "title": "Security Dashboard",
            "description": "Real-time security monitoring and threat analysis dashboard. Manage vulnerabilities, view insights, and protect your infrastructure.",
            "keywords": "security dashboard, threat monitoring, vulnerability management",
            "robots": "noindex, nofollow",  # Dashboard should not be indexed
            "ogType": "website"
        },
        "architecture-map": {
            "title": "Architecture Map",
            "description": "Interactive visualization of discovered software infrastructure. Explore your system architecture and identify vulnerabilities.",
            "keywords": "architecture map, infrastructure visualization, network topology, system architecture",
            "robots": "noindex, nofollow",
            "ogType": "website"
        }
    }
    
    default = defaults.get(page, {
        "title": "PurpleOps - Advanced Cybersecurity Platform",
        "description": "Protect your organization with PurpleOps's comprehensive cybersecurity solutions.",
        "keywords": "cybersecurity, security platform, threat detection",
        "ogType": "website"
    })
    
    return default
