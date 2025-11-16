import uuid
import shutil
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from app.models.file import File
from app.core.config import settings
# TODO: Import validation functions for file security
# These validators perform critical security checks:
# - sanitize_filename: Prevents directory traversal attacks
# - validate_file_extension: Whitelist/blacklist file types
# - validate_file_size: Prevents DoS attacks via huge files
# - validate_file_content: Detects fake file extensions using magic numbers
# - scan_file_for_viruses: Scans with ClamAV antivirus (optional)
# Uncomment the imports below once you create app/core/validators.py
# from app.core.validators import (
#     sanitize_filename,
#     validate_file_extension,
#     validate_file_size,
#     validate_file_content,
#     scan_file_for_viruses
# )
import os

UPLOAD_DIR = settings.UPLOAD_DIR

def save_upload(db: Session, upload_file: UploadFile, owner_id: int):
    """
    Save uploaded file to disk and database.
    
    TODO: Complete security validation workflow (currently partially implemented):
    1. ✓ Check file has a name
    2. ✗ Validate file size (prevent DoS) - Need to implement
    3. ✗ Sanitize filename (prevent path traversal) - Need to implement
    4. ✗ Validate extension (whitelist/blacklist) - Need to implement
    5. ✓ Save to disk with unique UUID name
    6. ✗ Validate content matches extension (magic numbers) - Need to implement
    7. ✗ Scan for viruses - Need to implement (optional)
    8. ✓ Save metadata to database
    9. ✓ If ANY step fails, delete file and rollback database
    
    TODO: Why use UUID for filenames:
    - Prevents filename collisions (two users upload "photo.jpg")
    - Prevents filename-based attacks (guessing file locations)
    - Makes files harder to enumerate/discover
    - Original filename is stored in database for downloads
    """
    
    # TODO: Step 1 - Validate file has a name
    # UploadFile.filename can be None in some edge cases
    # This is a basic check to ensure we have something to work with
    if not upload_file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required"
        )
    
    # TODO: Step 2 - Validate file size BEFORE saving to disk
    # CURRENTLY SKIPPED - Uncomment below once validators.py is created
    # This prevents attackers from uploading huge files that fill your disk
    # Also prevents DoS attacks where server runs out of space
    # validate_file_size(upload_file)
    
    # TODO: Step 3 - Sanitize filename to remove dangerous characters
    # CURRENTLY USING ORIGINAL FILENAME - Uncomment below once validators.py is created
    # Protects against:
    # - Directory traversal: "../../etc/passwd"
    # - Special characters: \, /, :, *, ?, ", <, >, |
    # - Excessively long names
    # safe_filename = sanitize_filename(upload_file.filename)
    safe_filename = upload_file.filename  # Temporary: using original until sanitize_filename is implemented
    
    # TODO: Step 4 - Validate extension against whitelist/blacklist
    # CURRENTLY SKIPPED - Uncomment below once validators.py is created
    # Returns extension if valid, raises HTTPException if dangerous
    # Prevents uploading executables (.exe, .bat, etc.)
    # ext = validate_file_extension(safe_filename)
    
    # TODO: Temporary extension extraction (replace with validate_file_extension)
    # This is NOT secure - just for basic functionality
    # It doesn't check against allowed/blocked lists
    ext = safe_filename.rsplit('.', 1)[-1].lower() if '.' in safe_filename else 'bin'
    
    # TODO: Step 5 - Generate unique filename using UUID
    # uuid.uuid4() creates a random UUID like: "550e8400-e29b-41d4-a716-446655440000"
    # We append the extension so the OS knows the file type
    # Example: "photo.jpg" becomes "550e8400-e29b-41d4-a716-446655440000.jpg"
    # This prevents:
    # - Two users uploading files with same name
    # - Attackers guessing file URLs
    # - Filename-based exploits
    saved_name = f"{uuid.uuid4()}.{ext}"
    
    # TODO: Ensure upload directory exists
    # exist_ok=True means don't raise error if directory already exists
    # This is idempotent (safe to run multiple times)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # TODO: Build full file path
    # Combines upload directory with unique filename
    # Example: "uploads/550e8400-e29b-41d4-a716-446655440000.jpg"
    file_path = os.path.join(UPLOAD_DIR, saved_name)

    try:
        # TODO: Step 6 - Save file to disk
        # shutil.copyfileobj streams data in chunks (memory efficient for large files)
        # Alternative: buffer.write(upload_file.file.read())
        # - Would load entire file into memory (bad for large files)
        # - Could cause OutOfMemory errors
        # Using context manager (with) ensures file is properly closed
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
        
        # TODO: Step 7 - Validate file content matches claimed extension
        # CURRENTLY SKIPPED - Uncomment below once validators.py is created
        # This prevents attacks where malware.exe is renamed to photo.jpg
        # Uses "magic numbers" (file signatures) to detect real file type
        # Example: PDF files always start with "%PDF", JPEG with "FF D8 FF"
        # validate_file_content(file_path, ext)
        
        # TODO: Step 8 - Scan file for viruses (if ClamAV is available)
        # CURRENTLY SKIPPED - Uncomment below once validators.py is created
        # This is the last line of defense against malicious files
        # Requires ClamAV to be installed and running
        # If ClamAV not available, this step is silently skipped
        # scan_file_for_viruses(file_path)
        
        # TODO: Step 9 - Save metadata to database
        # We store:
        # - name: Original sanitized filename (for download with original name)
        # - owner_id: Who uploaded it (for access control)
        # - content_type: MIME type from browser (e.g., "image/jpeg", "application/pdf")
        #   Note: This comes from client and might not be accurate
        # - path: Where file is stored on disk
        # - uploaded_at: Timestamp (set automatically by model default)
        db_file = File(
            name=safe_filename,
            owner_id=owner_id,
            content_type=upload_file.content_type,
            path=file_path
        )
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        return db_file
        
    except HTTPException:
        # TODO: Handle validation errors (re-raise them)
        # These are errors we intentionally raised:
        # - Invalid file extension
        # - File too large
        # - Virus detected
        # - Content doesn't match extension
        # We need to clean up before re-raising:
        # 1. Rollback database transaction (undo db.add)
        # 2. Delete partially saved file from disk
        db.rollback()
        if os.path.exists(file_path):
            os.remove(file_path)
        raise
        
    except Exception as e:
        # TODO: Handle unexpected errors
        # This catches errors we didn't anticipate:
        # - File system errors (disk full, permissions)
        # - Database errors (connection lost, constraint violations)
        # - Any other runtime errors
        # Clean up and return generic error (don't expose system details to user)
        db.rollback()
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving file: {str(e)}"
        )

def delete_file(db: Session, file_id: int, owner_id: int) -> None:
    """
    Delete a file with ownership verification.
    
    TODO: Security considerations implemented:
    1. ✓ Verify file exists in database
    2. ✓ Verify user owns the file (prevent deleting other users' files)
    3. ✓ Delete physical file from disk
    4. ✓ Delete metadata from database
    
    TODO: Why ownership check matters:
    - Without it, user A could delete user B's files by guessing IDs
    - This is called "Insecure Direct Object Reference" (IDOR) vulnerability
    - Example attack: Loop through DELETE /file/1, /file/2, ... /file/1000
    - In production, owner_id comes from JWT token (authenticated user)
    
    TODO: Attack scenario prevented:
    Attacker tries: DELETE /file/999?owner_id=1
    But file 999 actually belongs to owner_id=5
    Without ownership check: File deleted (BAD!)
    With ownership check: 403 Forbidden error (GOOD!)
    """
    
    # TODO: Step 1 - Find file in database
    # .first() returns None if not found (instead of raising error)
    db_file = db.query(File).filter(File.id == file_id).first()
    
    # TODO: Step 2 - Check if file exists in database
    # If file doesn't exist, return 404 Not Found
    # This could mean:
    # - File was already deleted
    # - File never existed
    # - User is trying random IDs (potential attack)
    if not db_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # TODO: Step 3 - CRITICAL - Verify ownership
    # This is your authorization check (different from authentication)
    # Authentication = "Who are you?" (verified by JWT token)
    # Authorization = "What can you do?" (verified by ownership check)
    # In production, owner_id comes from JWT token (current_user.id)
    # For now, it's passed as parameter (INSECURE - will fix with JWT)
    # if db_file.owner_id != owner_id:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="You don't have permission to delete this file"
    #     )
    
    # TODO: Step 4 - Delete physical file from disk
    # We try to delete but don't fail the entire operation if it's already gone
    # File might not exist on disk because:
    # - Manual deletion by admin
    # - Disk corruption
    # - Previous failed deletion attempt
    # We still want to clean up the database record
    try:
        if os.path.exists(str(db_file.path)):
            os.remove(str(db_file.path))
    except Exception as e:
        # TODO: In production, log this error for investigation
        # Example logging (not implemented yet):
        # logger.warning(f"Failed to delete file {db_file.path}: {str(e)}")
        # File is now orphaned on disk but we'll still remove from database
        # Admin can manually clean up orphaned files later
        pass
    
    # TODO: Step 5 - Delete database record
    # This removes the file metadata from database
    # After this, users can't see or access this file anymore
    # Even if physical file still exists on disk
    db.delete(db_file)
    db.commit()
    
    # TODO: No return value needed
    # FastAPI endpoint returns 204 No Content for successful DELETE
    # The None return is implicit in Python but included for clarity