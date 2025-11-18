import os
import re
# TODO: Learn about python-magic library
# - python-magic reads the first few bytes of a file (called "magic numbers" or file signature)
# - This tells you the TRUE file type, not just what the extension claims
# - For example: someone could rename virus.exe to photo.jpg, but magic will detect it's an executable
# - Install: pip install python-magic python-magic-bin (on Windows)
import magic
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent security attacks
    
    Why:
    1. Directory Traversal Attack: A user could upload "../../etc/passwd" to access system files
    2. Special Characters: Characters like \, /, :, *, ?, ", <, >, | can break file systems
    3. Long Names: Very long filenames can cause errors or buffer overflows
    
    What this function does:
    - Removes any path components (keeps only the filename, not directories)
    - Replaces dangerous characters with underscores
    - Limits filename length to filesystem maximum (255 characters)
    
    Example: 
    - "../../virus.exe" becomes "_.._.._.._virus.exe" and is then caught by extension check
    """
    # Remove path components to prevent directory traversal
    # os.path.basename extracts just the filename from a full path
    filename = os.path.basename(filename)
    
    # Remove or replace dangerous characters using regex
    # \w = letters, numbers, underscore
    # \s = whitespace
    # \- = hyphen
    # \. = dot
    # Anything NOT in this set gets replaced with _
    filename = re.sub(r'[^\w\s\-\.]', '_', filename)
    
    # Prevent double extension attacks
    # Attack: "malware.exe.jpg" might get executed as .exe 
    # We keep only the LAST extension, replace other dots with underscores
    name, ext = os.path.splitext(filename)
    name = name.replace('.', '_')
    filename = f"{name}{ext}"
    
    # Limit filename length to prevent filesystem errors
    # Most filesystems have a 255 character limit for filenames
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    
    return filename

def validate_file_extension(filename: str) -> str:
    """
    Validate file extension against allowed/blocked lists
    
    Steps:
    1. Check if file has an extension (reject files without extensions)
    2. Check against BLOCKED list (explicit deny of dangerous files)
    3. Check against ALLOWED list (explicit allow of safe files)
    
    Returns the extension if valid, raises HTTPException if invalid
    """
    # Extract extension from filename
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    
    # Reject files without extensions
    # Files without extensions are suspicious and hard to validate
    if not ext:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have an extension"
        )
    
    # Check against blocked extensions
    if ext in settings.BLOCKED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '.{ext}' is not allowed for security reasons"
        )
    
    # Check against allowed extensions
    # Only explicitly allowed file types can be uploaded
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '.{ext}' is not allowed. Allowed types: {', '.join(sorted(settings.ALLOWED_EXTENSIONS))}"
        )
    
    return ext

def validate_file_size(file: UploadFile) -> None:
    """
    Validate file size doesn't exceed maximum allowed
    
    How it works:
    - seek(0, 2) moves the file pointer to the end (2 = end of file)
    - tell() returns current position = file size in bytes
    - seek(0) resets pointer to beginning so file can be read normally
    - Compares size against MAX_FILE_SIZE from settings
    """
    # Check file size using seek/tell method
    # This works with file-like objects without reading entire file into memory
    file.file.seek(0, 2)  # Move to end of file
    file_size = file.file.tell()  # Get current position (= file size)
    file.file.seek(0)  # Reset to beginning for later reading
    
    # Compare against maximum and raise error if too large
    if file_size > settings.MAX_FILE_SIZE:
        max_mb = settings.MAX_FILE_SIZE / (1024 * 1024)
        actual_mb = file_size / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size ({actual_mb:.2f}MB) exceeds maximum allowed size ({max_mb:.2f}MB)"
        )

def validate_file_content(file_path: str, expected_ext: str) -> None:
    """
    TODO: Validate file content matches its extension using magic numbers
    
    IMPORTANT SECURITY CONCEPT - "Magic Numbers":
    - Every file type has a unique signature in its first few bytes
    - PDF files start with "%PDF"
    - JPEG files start with "FF D8 FF"
    - PNG files start with "89 50 4E 47"
    - ZIP files start with "50 4B"
    
    Why we need this:
    - A user could rename "virus.exe" to "photo.jpg"
    - Extension check would pass, but the file is still dangerous
    - Magic number check reads the actual file content to detect the real type
    
    Example Attack Prevented:
    - Attacker uploads "malware.exe" renamed as "document.pdf"
    - Extension check: passes (pdf is allowed)
    - Magic number check: FAILS (file is actually exe, not pdf)
    
    Note: This requires python-magic library
    - On Linux: pip install python-magic
    - On Windows: pip install python-magic python-magic-bin
    """
    try:
        # TODO: Use python-magic to detect actual file type
        # magic.Magic(mime=True) creates a magic detector that returns MIME types
        # MIME type = standardized way to identify file types (e.g., "image/jpeg", "application/pdf")
        mime = magic.Magic(mime=True)
        detected_mime = mime.from_file(file_path)
        
        # TODO: Define mapping of extensions to acceptable MIME types
        # Some files can have multiple valid MIME types (e.g., CSV can be text/csv or text/plain)
        mime_mapping = {
            'pdf': ['application/pdf'],
            'doc': ['application/msword'],
            'docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
            'xls': ['application/vnd.ms-excel'],
            'xlsx': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
            'jpg': ['image/jpeg'],
            'jpeg': ['image/jpeg'],
            'png': ['image/png'],
            'gif': ['image/gif'],
            'txt': ['text/plain'],
            'csv': ['text/csv', 'text/plain'],
            'json': ['application/json', 'text/plain'],
            'zip': ['application/zip'],
            'mp4': ['video/mp4'],
            'mp3': ['audio/mpeg'],
            # TODO: Add more mappings for other file types you allow
        }
        
        # TODO: Get list of acceptable MIME types for this extension
        allowed_mimes = mime_mapping.get(expected_ext.lower(), [])
        
        # TODO: If we have MIME types defined and file doesn't match, reject it
        # If extension isn't in mapping, we skip this check (not ideal, but safe)
        if allowed_mimes and detected_mime not in allowed_mimes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File content type ({detected_mime}) doesn't match extension (.{expected_ext})"
            )
    except ImportError:
        # TODO: Handle case where python-magic isn't installed
        # In production, you should log this warning
        # Consider making this check mandatory by raising error if library not found
        pass
    except HTTPException:
        # Re-raise our validation errors
        raise
    except Exception as e:
        # TODO: Handle other errors (file not found, permission issues, etc.)
        # In production, log this error for debugging
        pass

def scan_file_for_viruses(file_path: str) -> None:
    """
    TODO: Scan file for viruses using ClamAV antivirus engine
    
    What is ClamAV:
    - Free, open-source antivirus engine
    - Can detect trojans, viruses, malware, and other threats
    - Used by many mail servers and file storage systems
    
    How it works:
    1. ClamAV daemon (clamd) runs in background
    2. We send file path to clamd using Python client (clamd library)
    3. ClamAV scans file against virus database
    4. Returns "OK" if clean, "FOUND" if infected
    
    Setup (optional but recommended for production):
    Windows:
    - Download from https://www.clamav.net/downloads
    - Or use: choco install clamav
    - Start daemon: clamd
    
    Linux:
    - sudo apt-get install clamav clamav-daemon
    - sudo systemctl start clamav-daemon
    
    Python:
    - pip install clamd
    
    Note: This is optional. If ClamAV isn't installed, scanning is skipped.
    In production, you might want to make this mandatory.
    """
    # try:
    #     # TODO: Import clamd library (only if available)
    #     import clamd
        
    #     # TODO: Connect to ClamAV daemon
    #     # ClamdUnixSocket() for Linux/Mac
    #     # ClamdNetworkSocket() for Windows or remote ClamAV
    #     cd = clamd.ClamdUnixSocket()
        
    #     # TODO: Scan the file
    #     # Returns dict like: {'/path/to/file': ('FOUND', 'Trojan.Generic')}
    #     # Or: {'/path/to/file': ('OK', None)}
    #     scan_result = cd.scan(file_path)
        
    #     # TODO: Check if virus was found
    #     if scan_result and file_path in scan_result:
    #         status_type, virus_name = scan_result[file_path]
    #         if status_type == 'FOUND':
    #             # TODO: Delete infected file immediately
    #             if os.path.exists(file_path):
    #                 os.remove(file_path)
                
    #             # TODO: Reject upload with virus information
    #             raise HTTPException(
    #                 status_code=status.HTTP_400_BAD_REQUEST,
    #                 detail=f"File rejected: malware detected ({virus_name})"
    #             )
    # except ImportError:
    #     # TODO: Handle case where clamd library isn't installed
    #     # This means virus scanning is disabled
    #     # In production, you might want to:
    #     # 1. Log a warning that scanning is disabled
    #     # 2. Or raise an error to force virus scanning setup
    #     pass
    # except Exception as e:
    #     # TODO: Handle ClamAV not running or other errors
    #     # Options:
    #     # 1. Fail-safe: Reject file if can't scan (most secure)
    #     # 2. Fail-open: Allow file if can't scan (more user-friendly but less secure)
    #     # Currently using fail-open approach
    #     # In production, log this error and consider failing-safe
    #     pass