import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./files.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads/")
    
    # TODO: File upload security settings
    # These settings control what files users can upload to protect your server
    # MAX_FILE_SIZE: Maximum file size in bytes (default 10MB = 10 * 1024 * 1024 bytes)
    # - Prevents users from uploading huge files that could fill up your disk
    # - Also prevents DoS attacks where attackers upload massive files to crash your server
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", str(10 * 1024 * 1024)))
    
    # TODO: ALLOWED_EXTENSIONS - Whitelist of safe file extensions
    # - Only files with these extensions can be uploaded
    # - This is the primary defense against malicious file uploads
    # - Add or remove extensions based on your application needs
    # - Always use lowercase for consistency
    ALLOWED_EXTENSIONS: set = {
        "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx",  # Documents
        "txt", "csv", "json", "xml",                          # Text files
        "jpg", "jpeg", "png", "gif", "bmp", "webp",          # Images
        "mp4", "avi", "mov", "wmv",                          # Videos
        "mp3", "wav", "ogg",                                 # Audio
        "zip", "rar", "7z", "tar", "gz"                      # Archives
    }
    
    # TODO: BLOCKED_EXTENSIONS - Blacklist of dangerous file extensions
    # - These are explicitly blocked even if accidentally added to ALLOWED_EXTENSIONS
    # - Executable files (.exe, .bat, etc.) can run malicious code on your server
    # - Scripts (.js, .vbs, etc.) can be used for attacks
    # - This is a defense-in-depth approach (whitelist + blacklist)
    BLOCKED_EXTENSIONS: set = {
        "exe", "bat", "cmd", "sh", "ps1", "msi", "app", "deb", "rpm",  # Executables
        "jar", "vbs", "js", "wsf", "scr", "com", "pif"                 # Scripts
    }
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()