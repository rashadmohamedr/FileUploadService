from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any
from datetime import datetime, date

# --- Response Schemas for Analytics Endpoints ---

class TimeSeriesDataPoint(BaseModel):
    """Represents a single data point in a time series, e.g., uploads per day."""
    timestamp: date
    value: int

class StorageBreakdownItem(BaseModel):
    """Represents storage usage statistics for a specific file type."""
    content_type: str
    file_count: int
    total_size: int  # in bytes

class UserStatsResponse(BaseModel):
    """Schema for a single user's personal statistics."""
    files_uploaded: int
    storage_used: float  # in bytes
    last_login: datetime

class AdminStatsResponse(BaseModel):
    """Schema for the main admin dashboard overview."""
    total_users: int
    total_files: int
    total_storage_used: int  # in bytes
    active_users_24h: int

# --- Internal Schemas for Service Layer ---

class EventLog(BaseModel):
    """Schema for creating a new analytics event (for internal service use)."""
    event_type: str
    user_id: int | None = None
    metadata: Dict[str, Any] | None = None
