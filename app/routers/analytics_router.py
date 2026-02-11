from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Literal
from datetime import date

from app.schemas.user import UserLogin
from app.models.user import User
from app.schemas.analytics import (
    UserStatsResponse,
    EventLog,
    TimeSeriesDataPoint,
    #TopUser,
    #StorageByType,
)
from app.schemas.file import FileRead
from app.dependencies import get_db, get_current_user, get_current_admin
from app.services import analytics_service

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
    responses={404: {"description": "Not found"}},
)


@router.get("/me", response_model=UserStatsResponse)
def read_user_stats(
    current_user: UserLogin 
    ,
    db: Session = Depends(get_db),
):
    """
    Retrieve personal analytics for the current authenticated user.
    """
    print("read_user_stats router func is working")
    return analytics_service.get_user_stats(db=db, user=current_user)


@router.get("/admin/logs") # ,response_model=list[AnalyticsEvent]
def read_admin_logs(
    #current_admin: UserLogin,
    db: Session = Depends(get_db),
):
    """
    Retrieve a high-level overview of system analytics. (Admin only)
    """
    return analytics_service.get_admin_overview_logs(db=db)

@router.get("/admin/upload-stats")#, response_model=List[TimeSeriesDataPoint]
def read_upload_stats(
    current_admin: UserLogin, #Depends(get_current_admin)
    period: Literal['daily', 'weekly', 'monthly'] = 'daily',
    db: Session = Depends(get_db),
):
    """
    (Admin) Get daily, weekly, or monthly file upload statistics.
    """
    return analytics_service.get_upload_stats(db=db, period=period)


@router.get("/admin/top-users")#, response_model=List[TopUser]
def read_top_users_by_storage(
    current_admin: UserLogin,#Depends(get_current_admin)
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """
    (Admin) Get the top users by total storage used.
    """
    return analytics_service.get_top_users_by_storage(db=db, limit=limit)


@router.get("/admin/storage-by-type")#, response_model=List[StorageByType]
def read_storage_by_file_type(
    current_admin: UserLogin, #Depends(get_current_admin)
    db: Session = Depends(get_db),
):
    """
    (Admin) Get a breakdown of storage usage by file type.
    """
    return analytics_service.get_storage_by_file_type(db=db)

# @router.get("/admin/overview", response_model=AdminStatsResponse)
# def read_admin_overview(
#     current_admin: User = Depends(get_current_admin),
#     db: Session = Depends(get_db),
# ):
#     """
#     Retrieve a high-level overview of system analytics. (Admin only)
#     """
#     return analytics_service.get_admin_overview(db=db)


# @router.get("/admin/storage-breakdown", response_model=List[StorageBreakdownItem])
# def read_storage_breakdown(
#     current_admin: User = Depends(get_current_admin),
#     db: Session = Depends(get_db),
# ):
#     """
#     Get a breakdown of storage usage by content type. (Admin only)
#     """
#     return analytics_service.get_storage_breakdown(db=db)


# @router.get("/admin/upload-trends", response_model=List[TimeSeriesDataPoint])
# def read_upload_trends(
#     start_date: date | None = None,
#     end_date: date | None = None,
#     current_admin: User = Depends(get_current_admin),
#     db: Session = Depends(get_db),
# ):
#     """
#     Get the number of file uploads over a specified time period. (Admin only)
#     """
#     return analytics_service.get_upload_trends(db=db, start_date=start_date, end_date=end_date)


# @router.get("/admin/top-users", response_model=List[FileRead])
# def read_top_users(
#     limit: int = Query(10, ge=1, le=100),
#     current_admin: User = Depends(get_current_admin),
#     db: Session = Depends(get_db),
# ):
#     """
#     Get the most active users based on upload count and storage used. (Admin only)
#     """
#     return analytics_service.get_top_users(db=db, limit=limit)
