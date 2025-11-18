import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./files.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads/")
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", str(10 * 1024 * 1024)))
    
    # ALLOWED_EXTENSIONS - Whitelist of safe file extensions
    ALLOWED_EXTENSIONS: set = {
        "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx",  # Documents
        "txt", "csv", "json", "xml",                          # Text files
        "jpg", "jpeg", "png", "gif", "bmp", "webp",          # Images
        "mp4", "avi", "mov", "wmv",                          # Videos
        "mp3", "wav", "ogg",                                 # Audio
        "zip", "rar", "7z", "tar", "gz"                      # Archives
    }
    
    # BLOCKED_EXTENSIONS - Blacklist of dangerous file extensions
    BLOCKED_EXTENSIONS: set = {
        "exe", "bat", "cmd", "sh", "ps1", "msi", "app", "deb", "rpm",  # Executables
        "jar", "vbs", "js", "wsf", "scr", "com", "pif"                 # Scripts
    }
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()