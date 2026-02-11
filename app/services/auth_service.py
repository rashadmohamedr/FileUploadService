from sqlalchemy.orm import Session # type: ignore
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.responses import JSONResponse
from datetime import datetime, timedelta
from app.models.user import User
from app.models.analytics_event import AnalyticsEvent
from app.schemas.user import UserCreate, UserLogin, Token
from app.core.security import (hash_password, 
                               verify_password, 
                               create_access_token, 
                               ACCESS_TOKEN_EXPIRE_MINUTES, 
                               reject_sql_injection)
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

def create_user(db: Session, user: UserCreate, isAdmin: bool = False):
    """Create a new user with hashed password and JWT token."""
    # Normalize email to lowercase for consistent checking and storage
    normalized_email = user.email.lower()
    
    existing_user_with_same_email = db.query(User).filter(User.email == normalized_email).first()
    existing_user_with_same_username = db.query(User).filter(User.username == user.username).first()
    if (existing_user_with_same_email is not None) | (existing_user_with_same_username is not None) :
        raise HTTPException(status_code=400, detail="Email already registered")
    if user.password=="":
        raise HTTPException(status_code=422,detail="no Password was Entered")
    hashed_password = hash_password(user.password)
    
    reject_sql_injection(user.username)
    reject_sql_injection(user.email)

    db_user = User(
        username=user.username,
        email=str(normalized_email),
        password=hashed_password,
        is_admin=isAdmin
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(db_user.id), "email": db_user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return JSONResponse(content={
        "id": db_user.id,
        "username": db_user.username,
        "email": db_user.email,
        "is_admin?": db_user.is_admin,
        "message": "User created successfully",
        "token": access_token,
        "token_type": "bearer"
    })

def authenticate_user(db: Session, user: UserLogin):
    """Authenticate user and return JWT token."""
    reject_sql_injection(user.email)
    reject_sql_injection(user.password)
    db_user = db.query(User).filter(User.email == str(user.email)).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Verify hashed password
    valid_password = verify_password(user.password, str(db_user.password))
    if not valid_password:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(db_user.id), "email": db_user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    # Update last login and log analytics event
    update_last_login(db, db_user)
    
    return JSONResponse(content={
        "message": f"Welcome back, {db_user.username}!",
        "token": access_token,
        "token_type": "bearer",
        "user_id": db_user.id,
        "user last login:": str(db_user.last_login),
        "user used storage": db_user.total_storage_used
    })




security = HTTPBearer()
