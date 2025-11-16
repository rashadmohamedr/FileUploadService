from fastapi import APIRouter, Depends, UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
import os

from app.dependencies import get_db
from app.schemas.file import FileRead
from app.services.file_service import save_upload#, delete_file
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
    owner_id: int = 1,  # TODO: Replace with current_user: User = Depends(get_current_user)
    db: Session = Depends(get_db)
):
    """
    Upload a file with security validation.
    
    TODO: What happens in this endpoint:
    1. FastAPI receives multipart/form-data request with file
    2. File is wrapped in UploadFile object (file-like interface)
    3. owner_id comes from authenticated user (currently hardcoded as 1)
    4. save_upload performs all security checks and saves file
    5. Returns file metadata as FileRead schema
    
    TODO: Test with curl:
    curl -X POST "http://localhost:8000/file/upload" \
         -F "file=@/path/to/file.pdf" \
         -F "owner_id=1"
    
    Or use Swagger UI at http://localhost:8000/docs
    """
    db_file = save_upload(db, file, owner_id)
    return db_file

@router.get("/download/{file_id}", response_class=FileResponse)
def download(
    file_id: int,
    owner_id: int = 1,  # TODO: Replace with current_user: User = Depends(get_current_user)
    db: Session = Depends(get_db)
):
    """
    Download a file by its ID with ownership verification.
    
    TODO: Security checks performed:
    1. File exists in database
    2. User owns the file (prevent accessing other users' files)
    3. File exists on disk
    
    TODO: Why ownership check matters:
    - Prevents "Insecure Direct Object Reference" (IDOR) attack
    - Without it, anyone could download any file by guessing file_id
    - Example attack: Try /download/1, /download/2, ... /download/1000
    
    TODO: How FileResponse works:
    - Streams file directly to client (efficient for large files)
    - Sets proper headers (Content-Disposition, Content-Type)
    - Browser knows to download file with original name
    """
    
    # TODO: Step 1 - Find file in database
    db_file = db.query(File).filter(File.id == file_id).first()
    
    # TODO: Step 2 - Check file exists in database
    if not db_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # TODO: Step 3 - CRITICAL - Verify user owns this file
    # This is your authorization check (different from authentication)
    # Authentication = who are you? (JWT token)
    # Authorization = what can you do? (ownership check)
    # Once you implement JWT auth, replace owner_id with current_user.id
    #if db_file.owner_id != owner_id:
    #    raise HTTPException(
    #        status_code=status.HTTP_403_FORBIDDEN,
    #        detail="You don't have permission to access this file"
    #    )
    
    # TODO: Step 4 - Check file exists on disk
    # Database could have record but file might be deleted/corrupted
    if not os.path.exists(str(db_file.path)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk"
        )
    
    # TODO: Step 5 - Return file to user
    # FileResponse handles streaming, headers, and proper download behavior
    return FileResponse(
        path=str(db_file.path),
        filename=str(db_file.name),  # Original filename user uploaded
        media_type=str(db_file.content_type) if db_file.content_type is not None else None
    )

@router.get("/", response_model=list[FileRead])
def list_files(
    skip: int = 0,
    limit: int = 100,
    owner_id: int = 1,  # TODO: Replace with current_user: User = Depends(get_current_user)
    db: Session = Depends(get_db)
):
    """
    List all uploaded files with pagination.
    
    TODO: Understanding Pagination:
    - skip: How many records to skip (for page 1: skip=0, page 2: skip=10, etc.)
    - limit: Maximum records to return (page size)
    - Prevents loading huge result sets that crash the server
    
    TODO: Pagination Examples:
    - Page 1 (first 10 files): skip=0, limit=10
    - Page 2 (next 10 files): skip=10, limit=10
    - Page 3 (next 10 files): skip=20, limit=10
    
    TODO: Security Feature:
    - Filter by owner_id so users only see their own files
    - Without this filter, users could see all files in system
    - This prevents information disclosure vulnerability
    
    TODO: Test with query parameters:
    GET /file/?skip=0&limit=20
    """
    
    # TODO: Query database with filters and pagination
    # .filter(File.owner_id == owner_id) - Security: only show user's files
    # .offset(skip) - Pagination: skip first N records
    # .limit(limit) - Pagination: return max N records
    # Once JWT auth is implemented, owner_id will come from current_user.id
    files = db.query(File).filter(File.owner_id == owner_id).offset(skip).limit(limit).all()
    return files

@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file_endpoint(
    file_id: int,
    owner_id: int = 1,  # TODO: Replace with current_user: User = Depends(get_current_user)
    db: Session = Depends(get_db)
):
    """
    Delete a file by its ID with ownership verification.
    
    TODO: Understanding HTTP 204 No Content:
    - Indicates success but no data to return
    - Standard response for DELETE operations
    - Client knows file was deleted successfully
    
    TODO: Security Feature:
    - Ownership check happens inside delete_file service function
    - Prevents users from deleting files they don't own
    - This prevents unauthorized data deletion
    
    TODO: Test with curl:
    curl -X DELETE "http://localhost:8000/file/1?owner_id=1"
    
    TODO: What happens behind the scenes:
    1. Verify file exists in database
    2. Verify user owns the file (authorization)
    3. Delete physical file from disk
    4. Delete database record
    5. Return 204 status (success, no content)
    """
    # TODO: Call service layer which handles all deletion logic and security checks
    # The delete_file function in file_service.py performs:
    # - File existence check
    # - Ownership verification
    # - Physical file deletion
    # - Database record deletion
    #delete_file(db, file_id, owner_id) also that one need to be done
    return None