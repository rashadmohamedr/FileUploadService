from datetime  import datetime
from fastapi import HTTPException
from sqlalchemy import func, desc
from sqlalchemy.orm import Session
from typing import Literal
from app.schemas.analytics import UserStatsResponse,EventLog
from app.models.user import User
from app.models.file import File
from app.models.analytics_event import AnalyticsEvent
from rich import print # remove at production

def get_user_stats(db, user):
    """
    Retrieve user statistics from the database.

    Args:
        db: Database connection object.
        user_id: ID of the user whose stats are to be retrieved.
    Returns:
        UserStatsResponse.
    """
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid user")
    
    _storage_used = db_user.total_storage_used or 0
    _files_uploaded = len(db_user.files)
    _last_login = db_user.last_login
    print("_files_uploaded:",_files_uploaded,
          "_storage_used:",_storage_used,
          "_last_login:",_last_login)
    return UserStatsResponse(files_uploaded =_files_uploaded,
                             storage_used=_storage_used,
                             last_login =_last_login)

def get_admin_overview_logs(db, skip: int = 0, limit: int = 100)-> list[AnalyticsEvent]:
    """
    Retrieve all analytics events from the database, ordered by most recent.
    This is intended for admin use.

    Args:
        db: The database session.
        skip: The number of records to skip (for pagination).
        limit: The maximum number of records to return.
    Returns:
        A list of AnalyticsEvent objects.
    """
    
    events = db.query(AnalyticsEvent).order_by(AnalyticsEvent.timestamp.desc()).offset(skip).limit(limit).all()
    return events

def get_upload_stats(db: Session, period: Literal['daily', 'weekly', 'monthly']) -> list:
    """
    Calculates file upload statistics grouped by the specified period.
    """
    if period == 'daily':
        date_format_sql = "%Y-%m-%d"
        date_format_py = "%Y-%m-%d"
    elif period == 'weekly':
        date_format_sql = "%Y-%W"  # Year-Week number
        date_format_py = "%Y-%W-%w" # Add weekday for parsing
    elif period == 'monthly':
        date_format_sql = "%Y-%m"
        date_format_py = "%Y-%m"
    else:
        return []

    stats = (
        db.query(
            func.strftime(date_format_sql, AnalyticsEvent.timestamp).label("date_group"),
            func.count(AnalyticsEvent.id).label("count"),
        )
        .filter(AnalyticsEvent.event_type == "file_upload")
        .group_by("date_group")
        .order_by("date_group")
        .all()
    )

    result = []
    for s in stats:
        date_str = s.date_group
        # For weekly stats, append '-1' to represent Monday to make strptime work
        if period == 'weekly':
            date_str = f"{s.date_group}-1"
        
        parsed_date = datetime.strptime(date_str, date_format_py).date()
        result.append({"date": parsed_date, "count": s.count})

    return result

def get_top_users_by_storage(db, limit: int = 10) -> list[User]:
    """
    Retrieves a list of users who are using the most storage.
    """
    return (
        db.query(User)
        .order_by(User.total_storage_used.desc())
        .limit(limit)
        .all()
    )


def get_storage_by_file_type(db) -> list:
    """
    Calculates total storage used, grouped by file content type.
    """
    return (
        db.query(
            File.content_type,
            func.sum(File.size).label("total_storage"),
            func.count(File.id).label("file_count"),
        )
        .group_by(File.content_type)
        .order_by(desc("total_storage"))
        .all()
    )