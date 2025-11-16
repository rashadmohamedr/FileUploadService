from sqlalchemy.orm import Session # type: ignore
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.responses import JSONResponse
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, Token
from app.core.security import hash_password, pwd_context
from app.dependencies import get_db


def create_user(db: Session, user: UserCreate):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = hash_password(user.password)
    db_user = User(username=user.username, email=str(user.email), password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    token = ""
    return JSONResponse(content={"username": db_user.username, "email": db_user.email, "message": "User created successfully","token":token})

def authenticate_user(db: Session, user: UserLogin):
    db_user = db.query(User).filter(User.email == str(user.email)).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    #Verify hashed password
    valid_password = pwd_context.verify(user.password, str(db_user.password))
    if not valid_password:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = ""

    return JSONResponse(content={"message": f"Welcome back, {db_user.username}!","token":token})


security = HTTPBearer()
