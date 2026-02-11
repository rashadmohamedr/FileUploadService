import os
import re
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings

# Import python-magic for file content validation
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    # Production systems should have python-magic installed
    # Install with: pip install python-magic python-magic-bin (on Windows)

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

def validate_file_size(file: UploadFile) -> float:
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
    return file_size / (1024 * 1024)

def validate_file_content(file_path: str, expected_ext: str) -> None:
    """
    Validate file content matches its extension using magic numbers.
    
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
    """
    if not MAGIC_AVAILABLE:
        # python-magic not installed, skip content validation
        # In production, consider making this mandatory
        return
    
    try:
        # Use python-magic to detect actual file type
        mime = magic.Magic(mime=True)
        detected_mime = mime.from_file(file_path)
        
        # Define mapping of extensions to acceptable MIME types
        # Some files can have multiple valid MIME types
        mime_mapping = {
            'pdf': ['application/pdf'],
            'doc': ['application/msword'],
            'docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
            'xls': ['application/vnd.ms-excel'],
            'xlsx': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
            'ppt': ['application/vnd.ms-powerpoint'],
            'pptx': ['application/vnd.openxmlformats-officedocument.presentationml.presentation'],
            'jpg': ['image/jpeg'],
            'jpeg': ['image/jpeg'],
            'png': ['image/png'],
            'gif': ['image/gif'],
            'bmp': ['image/bmp', 'image/x-ms-bmp'],
            'webp': ['image/webp'],
            'txt': ['text/plain'],
            'csv': ['text/csv', 'text/plain'],
            'json': ['application/json', 'text/plain'],
            'xml': ['application/xml', 'text/xml'],
            'zip': ['application/zip', 'application/x-zip-compressed'],
            'rar': ['application/x-rar-compressed', 'application/vnd.rar'],
            '7z': ['application/x-7z-compressed'],
            'tar': ['application/x-tar'],
            'gz': ['application/gzip', 'application/x-gzip'],
            'mp4': ['video/mp4'],
            'avi': ['video/x-msvideo'],
            'mov': ['video/quicktime'],
            'wmv': ['video/x-ms-wmv'],
            'mp3': ['audio/mpeg'],
            'wav': ['audio/wav', 'audio/x-wav'],
            'ogg': ['audio/ogg'],
        }
        
        # Get list of acceptable MIME types for this extension
        allowed_mimes = mime_mapping.get(expected_ext.lower(), [])
        
        # If we have MIME types defined and file doesn't match, reject it
        if allowed_mimes and detected_mime not in allowed_mimes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File content type ({detected_mime}) doesn't match extension (.{expected_ext})"
            )
    except HTTPException:
        # Re-raise our validation errors
        raise
    except Exception as e:
        # Handle other errors gracefully
        # In production, log this error for debugging
        pass

def scan_file_for_viruses(file_path: str) -> None:
    """
    Scan file for viruses using ClamAV antivirus engine.
    
    What is ClamAV:
    - Free, open-source antivirus engine
    - Can detect trojans, viruses, malware, and other threats
    - Used by many mail servers and file storage systems
    
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
    try:
        import clamd
        
        # Connect to ClamAV daemon
        try:
            # Try Unix socket first (Linux/Mac)
            cd = clamd.ClamdUnixSocket()
        except:
            # Fallback to network socket (Windows or remote ClamAV)
            cd = clamd.ClamdNetworkSocket()
        
        # Scan the file
        scan_result = cd.scan(file_path)
        
        # Check if virus was found
        if scan_result and file_path in scan_result:
            status_type, virus_name = scan_result[file_path]
            if status_type == 'FOUND':
                # Delete infected file immediately
                if os.path.exists(file_path):
                    os.remove(file_path)
                
                # Reject upload with virus information
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File rejected: malware detected ({virus_name})"
                )
    except ImportError:
        # clamd library not installed - skip virus scanning
        # In production, consider making this mandatory
        pass
    except Exception as e:
        # ClamAV not running or other errors
        # Currently using fail-open approach (allow file if can't scan)
        # In production, log this error and consider failing-safe
        pass