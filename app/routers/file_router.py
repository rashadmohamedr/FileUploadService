from fastapi import APIRouter, Depends, UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
import os

from app.dependencies import get_db
from app.schemas.file import FileRead
from app.services.file_service import save_upload
from app.models.file import File

router = APIRouter(prefix="/file", tags=["file"])

# upload
@router.post("/upload", response_model=FileRead, status_code=status.HTTP_201_CREATED)
def upload(file: UploadFile, owner_id: int=1, db: Session = Depends(get_db)):
    """Upload a file and save its metadata to the database."""
    db_file = save_upload(db, file, owner_id)
    return db_file

# download
@router.get("/download/{file_id}", response_class=FileResponse)
def download(file_id: int, db: Session = Depends(get_db)):
    """Download a file by its ID."""
    db_file = db.query(File).filter(File.id == file_id).first()
    
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    if not os.path.exists(str(db_file.path)):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        path=str(db_file.path),
        filename=str(db_file.name),  # Changed from original_name to name
        media_type=str(db_file.content_type) if db_file.content_type is not None else None
    )

# list all files
@router.get("/", response_model=list[FileRead])
def list_files(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all uploaded files with pagination."""
    files = db.query(File).offset(skip).limit(limit).all()
    return files

# delete file
@router.delete("/{file_id}")
def delete_file(file_id: int, db: Session = Depends(get_db)):
    """Delete a file by its ID."""
    db_file = db.query(File).filter(File.id == file_id).first()
    
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Delete file from disk
    try:
        if os.path.exists(str(db_file.path)):
            os.remove(str(db_file.path))
    except Exception:
        pass  # Continue even if file deletion fails
    
    # Delete from database
    db.delete(db_file)
    db.commit()
    
    return None