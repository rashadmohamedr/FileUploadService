from fastapi import APIRouter, Depends, UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
import os

from app.dependencies import get_db
from app.schemas.file import FileRead
from app.services.file_service import save_upload, delete_file, download_file
from app.models.file import File

router = APIRouter(prefix="/file", tags=["file"])

# TODO: IMPORTANT - Replace owner_id parameter with real authentication
# Currently using owner_id=1 as a placeholder, which is INSECURE
# 
# What you need to learn:
# 1. JWT (JSON Web Tokens) - How to create and verify authentication tokens
# 2. OAuth2 with Password Flow - FastAPI's authentication pattern
# 3. Dependency injection - How to get current user from token
#
# Steps to implement:
# 1. Create get_current_user dependency in app/dependencies.py
# 2. Replace owner_id: int = 1 with current_user: User = Depends(get_current_user)
# 3. Use current_user.id instead of owner_id
#
# Example of what it should look like:
# def upload(file: UploadFile, current_user: User = Depends(get_current_user), ...):
#     db_file = save_upload(db, file, current_user.id)

@router.post("/upload", response_model=FileRead, status_code=status.HTTP_201_CREATED)
def upload(
    file: UploadFile,
    owner_id: int = 1,  # Replace with current_user: User = Depends(get_current_user)
    db: Session = Depends(get_db)
):
    """
    Upload a file with security validation.
    
    What happens in this endpoint:
    1. FastAPI receives multipart/form-data request with file
    2. File is wrapped in UploadFile object (file-like interface)
    3. owner_id comes from authenticated user (currently hardcoded as 1)
    4. save_upload performs all security checks and saves file
    5. Returns file metadata as FileRead schema
    
    Test with curl:
    curl -X POST "http://localhost:8000/file/upload" \
         -F "file=@/path/to/file.pdf" \
         -F "owner_id=1"
    
    Or use Swagger UI at http://localhost:8000/docs
    """ 
    db_file = save_upload(db, file, owner_id)
    return db_file

@router.get("/download/{file_id}", response_class=FileResponse)
def download(
    file_id: int, # or saved_name: str decide later
    owner_id: int = 1,  # Replace with current_user: User = Depends(get_current_user)
    db: Session = Depends(get_db)
):
    """
    Download a file by its ID with ownership verification.
    """
    
    return download_file(db, file_id, owner_id)

@router.get("/", response_model=list[FileRead])
def list_files(
    skip: int = 0,
    limit: int = 100,
    owner_id: int = 1,  # Replace with current_user: User = Depends(get_current_user)
    db: Session = Depends(get_db)
):
    """
    List all uploaded files with pagination.
    
    """
    
    #  Query database with filters and pagination
    # Once JWT auth is implemented, owner_id will come from current_user.id
    files = db.query(File).filter(File.owner_id == owner_id).offset(skip).limit(limit).all()
    return files

@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    file_id: int,
    owner_id: int = 1,  # Replace with current_user: User = Depends(get_current_user)
    db: Session = Depends(get_db)
):
    """
    Delete a file by its ID with ownership verification.
    
    Understanding HTTP 204 No Content:
    - Indicates success but no data to return
    - Standard response for DELETE operations
    - Client knows file was deleted successfully
    
    Security Feature:
    - Ownership check happens inside delete_file service function
    - Prevents users from deleting files they don't own
    - This prevents unauthorized data deletion
    
    Test with curl:
    curl -X DELETE "http://localhost:8000/file/1?owner_id=1"
    
    What happens behind the scenes:
    1. Verify file exists in database
    2. Verify user owns the file (authorization)
    3. Delete physical file from disk
    4. Delete database record
    5. Return 204 status (success, no content)
    """
    return delete_file(db, file_id, owner_id)