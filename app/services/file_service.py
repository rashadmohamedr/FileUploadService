import uuid
import shutil
from fastapi import UploadFile, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import Integer
from app.models.file import File
from app.core.config import settings
from app.core.validators import (
    sanitize_filename,
    validate_file_extension,
    validate_file_size,
#    validate_file_content,
#    scan_file_for_viruses
)
import os

UPLOAD_DIR = settings.UPLOAD_DIR

def save_upload(db: Session, upload_file: UploadFile, owner_id: int):
    """
    Save uploaded file to disk and database.
    
    TODO: Complete security validation workflow (currently partially implemented):
    1. ✓ Check file has a name
    2. ✓ Validate file size (to prevent DoS attacks)
    3. ✓ Sanitize filename (prevent path traversal) - Need to implement
    4. ✓ Validate extension (whitelist/blacklist) - Need to implement
    5. ✓ Save to disk with unique UUID name
    6. ✗ Validate content matches extension (magic numbers) - Need to implement
    7. ✗ Scan for viruses - Need to implement (optional)
    8. ✓ Save metadata to database
    9. ✓ If ANY step fails, delete file and rollback database
    """
    
    # Validate file has a name
    # UploadFile.filename can be None in some edge cases
    if not upload_file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required"
        )
    
    # Validate file size BEFORE saving to disk
    validate_file_size(upload_file)
    
    # Sanitize filename to remove dangerous characters
    safe_filename = sanitize_filename(upload_file.filename)
    
    # Validate extension against whitelist/blacklist
    ext = validate_file_extension(safe_filename)
    
    
    # Generate unique filename using UUID
    # uuid.uuid4() creates a random UUID like: "550e8400-e29b-41d4-a716-446655440000"
    # We append the extension so the OS knows the file type
    # Example: "photo.jpg" becomes "550e8400-e29b-41d4-a716-446655440000.jpg"
    # This prevents:
    # - Two users uploading files with same name
    # - Attackers guessing file URLs
    # - Filename-based exploits
    saved_name = f"{uuid.uuid4()}.{ext}"
    
    # TEnsure upload directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, saved_name)

    # TODO: Validate file content matches claimed extension
    # CURRENTLY SKIPPED - Uncomment below once validators.py is created
    # This prevents attacks where malware.exe is renamed to photo.jpg
    # Uses "magic numbers" (file signatures) to detect real file type
    # Example: PDF files always start with "%PDF", JPEG with "FF D8 FF"
    # validate_file_content(file_path, ext)
    
    # TODO:  Scan file for viruses (if ClamAV is available)
    # This is the last line of defense against malicious files
    # Requires ClamAV to be installed and running
    # If ClamAV not available, this step is silently skipped
    # scan_file_for_viruses(file_path)
    try:
        # Save file to disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer) # shutil.copyfileobj streams data in chunks (memory efficient for large files)
        
        
        # Save metadata to database
        db_file = File(
            saved_name=saved_name,
            uploaded_name=safe_filename,
            owner_id=owner_id,
            content_type=upload_file.content_type,
            path=file_path
        )
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        
        # TODO: (Analytics) Integrate event logging for all file operations.
        # After successfully saving the file and creating the DB record:
        # 1. Call analytics_service.log_event(
        #    user_id=current_user.id,
        #    event_type="file_upload",
        #    metadata={"file_id": new_file.id, "size": file_size, "content_type": content_type}
        # )
        
        return db_file
        
    except HTTPException:
        db.rollback()
        if os.path.exists(file_path):
            os.remove(file_path)
        raise
        
    except Exception as e:
        db.rollback()
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving file: {str(e)}"
        )

def delete_file(db: Session, file_id: int, owner_id: int)-> JSONResponse:
    """
    Delete a file with ownership verification.
    
    Security considerations implemented:
    1. Verify file exists in database
    2. Verify user owns the file (prevent deleting other users' files)
    3. Delete physical file from disk
    4. Delete metadata from database
    
    TODO ownership check is commented out until JWT auth is implemented.
    Once JWT is in place, replace owner_id param with current_user.id from token.
    """
    
    # Find file in database
    # .first() returns None if not found (instead of raising error)
    db_file = db.query(File).filter(File.id == file_id).first()
    
    # Check if file exists in database
    if not db_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # TODO CRITICAL - Verify ownership
    # This is your authorization check (different from authentication)
    # Authentication = "Who are you?" (verified by JWT token)
    # Authorization = "What can you do?" (verified by ownership check)
    # In production, owner_id comes from JWT token (current_user.id)
    # For now, it's passed as parameter (INSECURE - will fix with JWT)
    db_file_owner_id=db_file.owner_id.casted(Integer)
    if db_file_owner_id != owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this file"
        )
    
    # Delete physical file from disk
    try:
        if os.path.exists(str(db_file.path)):
            os.remove(str(db_file.path))
        # Delete database record
        db.delete(db_file)
        db.commit()
        
        # TODO: (Analytics) Integrate event logging for all file operations.
        # After successfully deleting the file from disk and DB:
        # 1. Call analytics_service.log_event(
        #    user_id=current_user.id,
        #    event_type="file_delete",
        #    metadata={"file_id": file_id}
        # )
        
    except Exception as e:
        # TODO: In production, log this error for investigation
        # Example logging (not implemented yet):
        # logger.warning(f"Failed to delete file {db_file.path}: {str(e)}")
        # File is now orphaned on disk but we'll still remove from database
        # Admin can manually clean up orphaned files later
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file"
        )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "File deleted successfully", "file_id": file_id}
    )
    
    
    
def download_file(db: Session, file_id: int, owner_id: int) -> FileResponse:
    #  Find file in database
    db_file = db.query(File).filter(File.id == file_id).first()
    
    # Check file exists in database
    if not db_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # TODO: CRITICAL - Verify user owns this file
    # Once you implement JWT auth, replace owner_id with current_user.id
    db_file_owner_id=db_file.owner_id.casted(Integer)
    if db_file_owner_id != owner_id:
       raise HTTPException(
           status_code=status.HTTP_403_FORBIDDEN,
           detail="You don't have permission to access this file"
       )
    
    # Check file exists on disk
    # Database could have record but file might be deleted/corrupted
    if not os.path.exists(str(db_file.path)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk"
        )
    
    # Return file to user
    # FileResponse handles streaming, headers, and proper download behavior
    response = FileResponse(
        path=str(db_file.path),
        filename=str(db_file.uploaded_name),  # Original filename user uploaded
        media_type=str(db_file.content_type) if db_file.content_type is not None else None
    )
    
    # TODO: (Analytics) Integrate event logging for all file operations.
    # After successfully retrieving the file for download:
    # 1. Call analytics_service.log_event(
    #    user_id=current_user.id,
    #    event_type="file_download",
    #    metadata={"file_id": file.id}
    # )
    
    return response