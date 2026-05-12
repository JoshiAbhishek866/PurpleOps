from fastapi import APIRouter, HTTPException, Request
from datetime import datetime
from bson import ObjectId

router = APIRouter()

async def get_demo_stats(db):
    total = await db.demo_requests.count_documents({})
    pending = await db.demo_requests.count_documents({"status": "new"})
    return {"total": total, "pending": pending}

@router.get("/")
async def get_demo_requests(request: Request, status: str = None, limit: int = 50, offset: int = 0):
    db = request.app.state.db
    
    query = {}
    if status:
        query["status"] = status
    
    cursor = db.demo_requests.find(query).sort("createdAt", -1).skip(offset).limit(limit)
    requests = await cursor.to_list(length=limit)
    total = await db.demo_requests.count_documents(query)
    
    for req in requests:
        req["id"] = str(req.pop("_id"))
    
    return {"requests": requests, "total": total}

@router.get("/{request_id}")
async def get_demo_request(request_id: str, request: Request):
    db = request.app.state.db
    
    demo_req = await db.demo_requests.find_one({"_id": ObjectId(request_id)})
    if not demo_req:
        raise HTTPException(status_code=404, detail="Demo request not found")
    
    demo_req["id"] = str(demo_req.pop("_id"))
    return demo_req

@router.post("/")
async def create_demo_request(request: Request):
    db = request.app.state.db
    data = await request.json()
    
    demo_doc = {
        "firstName": data.get("firstName"),
        "lastName": data.get("lastName"),
        "email": data.get("email"),
        "company": data.get("company"),
        "phone": data.get("phone"),
        "message": data.get("message"),
        "companySize": data.get("companySize"),
        "preferredDate": data.get("preferredDate"),
        "status": "new",
        "priority": "low",
        "createdAt": datetime.utcnow()
    }
    
    result = await db.demo_requests.insert_one(demo_doc)
    
    return {
        "message": "Demo request submitted successfully",
        "status": "received",
        "id": str(result.inserted_id)
    }

@router.put("/{request_id}")
async def update_demo_request(request_id: str, request: Request):
    db = request.app.state.db
    data = await request.json()
    
    update_data = {k: v for k, v in data.items() if k not in ["_id", "id"]}
    update_data["updatedAt"] = datetime.utcnow()
    
    result = await db.demo_requests.update_one(
        {"_id": ObjectId(request_id)},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Demo request not found")
    
    # Fetch and return the updated request
    updated_request = await db.demo_requests.find_one({"_id": ObjectId(request_id)})
    updated_request["id"] = str(updated_request.pop("_id"))
    
    return {"message": "Demo request updated", "request": updated_request}

@router.delete("/{request_id}")
async def delete_demo_request(request_id: str, request: Request):
    db = request.app.state.db
    
    result = await db.demo_requests.delete_one({"_id": ObjectId(request_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Demo request not found")
    
    return {"message": "Demo request deleted"}
