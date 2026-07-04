from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone
from bson import ObjectId
import re

router = APIRouter()

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')

async def get_blog_stats(db):
    total = await db.blog_posts.count_documents({})
    published = await db.blog_posts.count_documents({"status": "published"})
    return {"total": total, "published": published}

@router.get("/")
async def get_posts(request: Request, status: str = None, limit: int = 10, offset: int = 0):
    db = request.app.state.db
    
    query = {}
    if status:
        query["status"] = status
    
    cursor = db.blog_posts.find(query).sort("createdAt", -1).skip(offset).limit(limit)
    posts = await cursor.to_list(length=limit)
    total = await db.blog_posts.count_documents(query)
    
    # Convert ObjectId to string
    for post in posts:
        post["id"] = str(post.pop("_id"))
    
    return {"posts": posts, "total": total, "hasMore": offset + limit < total}

@router.get("/{post_id}")
async def get_post(post_id: str, request: Request):
    db = request.app.state.db
    
    try:
        post = await db.blog_posts.find_one({"_id": ObjectId(post_id)})
    except Exception:
        post = await db.blog_posts.find_one({"slug": post_id})
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    post["id"] = str(post.pop("_id"))
    return {"post": post}

@router.post("/")
async def create_post(request: Request):
    db = request.app.state.db
    data = await request.json()
    
    post_doc = {
        "title": data.get("title"),
        "slug": slugify(data.get("title", "")),
        "content": data.get("content", ""),
        "excerpt": data.get("excerpt", ""),
        "author": data.get("author", "Admin"),
        "category": data.get("category", "General"),
        "tags": data.get("tags", []),
        "status": data.get("status", "draft"),
        "featuredImage": data.get("featuredImage"),
        "createdAt": datetime.now(timezone.utc),
        "updatedAt": datetime.now(timezone.utc)
    }
    
    result = await db.blog_posts.insert_one(post_doc)
    post_doc["id"] = str(result.inserted_id)
    if "_id" in post_doc:
        del post_doc["_id"]
    
    return {"message": "Post created", "post": post_doc}

@router.put("/{post_id}")
async def update_post(post_id: str, request: Request):
    db = request.app.state.db
    data = await request.json()
    
    update_data = {k: v for k, v in data.items() if k not in ["_id", "id"]}
    update_data["updatedAt"] = datetime.now(timezone.utc)
    if "title" in update_data:
        update_data["slug"] = slugify(update_data["title"])
    
    result = await db.blog_posts.update_one(
        {"_id": ObjectId(post_id)},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Post not found")
    
    return {"message": "Post updated"}

@router.delete("/{post_id}")
async def delete_post(post_id: str, request: Request):
    db = request.app.state.db
    
    result = await db.blog_posts.delete_one({"_id": ObjectId(post_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Post not found")
    
    return {"message": "Post deleted"}
