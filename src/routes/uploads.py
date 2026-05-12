from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from fastapi.responses import FileResponse
from datetime import datetime
import os
import uuid
import shutil

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "images")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_file_extension(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()

def generate_unique_filename(original_filename: str) -> str:
    ext = get_file_extension(original_filename)
    unique_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{timestamp}_{unique_id}{ext}"

@router.post("/")
async def upload_image(file: UploadFile = File(...)):
    """Upload an image file"""
    
    # Validate file extension
    ext = get_file_extension(file.filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Read file content
    content = await file.read()
    
    # Validate file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB")
    
    # Generate unique filename
    unique_filename = generate_unique_filename(file.filename)
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Return the URL to access the image
    return {
        "success": True,
        "filename": unique_filename,
        "originalName": file.filename,
        "url": f"/api/uploads/images/{unique_filename}",
        "size": len(content),
        "type": file.content_type
    }

@router.post("/multiple")
async def upload_multiple_images(files: list[UploadFile] = File(...)):
    """Upload multiple image files"""
    
    uploaded_files = []
    errors = []
    
    for file in files:
        try:
            ext = get_file_extension(file.filename)
            if ext not in ALLOWED_EXTENSIONS:
                errors.append({"filename": file.filename, "error": "File type not allowed"})
                continue
            
            content = await file.read()
            
            if len(content) > MAX_FILE_SIZE:
                errors.append({"filename": file.filename, "error": "File too large"})
                continue
            
            unique_filename = generate_unique_filename(file.filename)
            file_path = os.path.join(UPLOAD_DIR, unique_filename)
            
            with open(file_path, "wb") as f:
                f.write(content)
            
            uploaded_files.append({
                "filename": unique_filename,
                "originalName": file.filename,
                "url": f"/api/uploads/images/{unique_filename}",
                "size": len(content)
            })
        except Exception as e:
            errors.append({"filename": file.filename, "error": str(e)})
    
    return {
        "success": True,
        "uploaded": uploaded_files,
        "errors": errors,
        "totalUploaded": len(uploaded_files),
        "totalErrors": len(errors)
    }

@router.get("/images/{filename}")
async def get_image(filename: str):
    """Serve an uploaded image"""
    
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    
    return FileResponse(file_path)

@router.delete("/images/{filename}")
async def delete_image(filename: str):
    """Delete an uploaded image"""
    
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    
    os.remove(file_path)
    
    return {"success": True, "message": "Image deleted successfully"}

@router.get("/")
async def list_images():
    """List all uploaded images"""
    
    images = []
    for filename in os.listdir(UPLOAD_DIR):
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.isfile(file_path):
            stat = os.stat(file_path)
            images.append({
                "filename": filename,
                "url": f"/api/uploads/images/{filename}",
                "size": stat.st_size,
                "uploadedAt": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
    
    return {"images": images, "total": len(images)}
