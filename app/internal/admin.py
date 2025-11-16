from fastapi import APIRouter

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/dashboard")
def get_admin_dashboard():
    """
    Endpoint to retrieve admin dashboard information.
    like analytics, user management, and system settings.
    include storage usage, user activity, and other relevant metrics. 
    """
    return {"message": "Admin Dashboard"}