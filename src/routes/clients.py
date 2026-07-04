from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone
from bson import ObjectId

router = APIRouter()

async def get_client_stats(db):
    total = await db.client_companies.count_documents({})
    active = await db.client_companies.count_documents({"isActive": True})
    return {"total": total, "active": active}

@router.get("/")
async def get_clients(request: Request, limit: int = 50, offset: int = 0):
    db = request.app.state.db
    
    cursor = db.client_companies.find({}).sort("createdAt", -1).skip(offset).limit(limit)
    clients = await cursor.to_list(length=limit)
    total = await db.client_companies.count_documents({})
    
    for client in clients:
        client["id"] = str(client.pop("_id"))
    
    return {"clients": clients, "total": total}

@router.get("/{client_id}")
async def get_client(client_id: str, request: Request):
    db = request.app.state.db
    
    client = await db.client_companies.find_one({"_id": ObjectId(client_id)})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    client["id"] = str(client.pop("_id"))
    return client

@router.post("/")
async def create_client(request: Request):
    db = request.app.state.db
    data = await request.json()
    
    client_doc = {
        "name": data.get("name"),
        "email": data.get("email"),
        "phone": data.get("phone"),
        "website": data.get("website"),
        "industry": data.get("industry"),
        "size": data.get("size"),
        "subscription": data.get("subscription", {"plan": "free", "status": "trial"}),
        "services": data.get("services", []),
        "securityModels": data.get("securityModels", {"offensive": False, "defensive": False}),
        "isActive": data.get("isActive", True),
        "createdAt": datetime.now(timezone.utc)
    }
    
    result = await db.client_companies.insert_one(client_doc)
    client_doc["id"] = str(result.inserted_id)
    del client_doc["_id"]
    
    return {"message": "Client created", "client": client_doc}

@router.put("/{client_id}")
async def update_client(client_id: str, request: Request):
    db = request.app.state.db
    data = await request.json()
    
    update_data = {k: v for k, v in data.items() if k not in ["_id", "id"]}
    update_data["updatedAt"] = datetime.now(timezone.utc)
    
    result = await db.client_companies.update_one(
        {"_id": ObjectId(client_id)},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Fetch and return the updated client
    updated_client = await db.client_companies.find_one({"_id": ObjectId(client_id)})
    updated_client["id"] = str(updated_client.pop("_id"))
    
    return {"message": "Client updated", "client": updated_client}

@router.delete("/{client_id}")
async def delete_client(client_id: str, request: Request):
    db = request.app.state.db
    
    result = await db.client_companies.delete_one({"_id": ObjectId(client_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Client not found")
    
    return {"message": "Client deleted"}
