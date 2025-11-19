from sqlalchemy.orm import Session # type: ignore
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.responses import JSONResponse
from datetime import datetime
from app.models.user import User
from app.models.analytics_event import AnalyticsEvent
from app.schemas.user import UserCreate, UserLogin, Token
from app.core.security import hash_password, pwd_context
from app.dependencies import get_db

def update_last_login(db: Session, user: User):
    """Updates the user's last_login timestamp and logs the login event."""
    user.last_login = datetime.utcnow() # type: ignore
    log_event = AnalyticsEvent(
        user_id=user.id,
        event_type="user_login",
        details={
            "user_id": user.id,
            "username": user.username,
            "login_time": user.last_login.isoformat()
        }
    )
    db.add(log_event)
    db.commit()
    db.refresh(user)

def create_user(db: Session, user: UserCreate,isAdmin: bool=False):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = hash_password(user.password)
    db_user = User(username=user.username, email=str(user.email), password=hashed_password, is_admin=isAdmin)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    token = ""
    return JSONResponse(content={"id": db_user.id, 
                                 "username": db_user.username, 
                                 "email": db_user.email, 
                                 "is_admin?": db_user.is_admin,
                                 "message": "User created successfully",
                                 "token":token})

def authenticate_user(db: Session, user: UserLogin):
    db_user = db.query(User).filter(User.email == str(user.email)).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    #Verify hashed password
    valid_password = pwd_context.verify(user.password, str(db_user.password))
    if not valid_password:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = ""
    update_last_login(db, db_user)
    # TODO: After successful authentication:
    # 1. Call analytics_service.log_event(user_id=user.id, event_type="user_login")
    return JSONResponse(content={"message": f"Welcome back, {db_user.username}!",
                                 "token":token,
                                 "user_id":db_user.id,
                                 "user last login:": str(db_user.last_login),
                                 "user used storage": db_user.total_storage_used })




security = HTTPBearer()
