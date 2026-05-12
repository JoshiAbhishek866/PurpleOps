from fastapi import APIRouter, HTTPException, Request
from datetime import datetime

router = APIRouter()

@router.get("/")
async def get_all_content(request: Request):
    db = request.app.state.db
    cursor = db.website_content.find({}, {"_id": 0})
    contents = await cursor.to_list(length=100)
    return {"content": contents, "sections": contents}

@router.get("/{section}")
async def get_content(section: str, request: Request):
    db = request.app.state.db
    content = await db.website_content.find_one({"section": section}, {"_id": 0})
    
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    return content

@router.put("/{section}")
async def update_content(section: str, request: Request):
    db = request.app.state.db
    data = await request.json()
    
    content_data = data.get("content", data)
    
    result = await db.website_content.update_one(
        {"section": section},
        {"$set": {"content": content_data, "updatedAt": datetime.utcnow()}},
        upsert=True
    )
    
    # Return updated content
    updated = await db.website_content.find_one({"section": section}, {"_id": 0})
    return {"message": "Content updated successfully", "section": section, "content": updated}
