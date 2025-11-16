from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session # type: ignore
from starlette.responses import JSONResponse

from app.dependencies import get_db
from app.schemas.user import UserCreate, UserLogin, UserBase
from app.services.auth_service import create_user, authenticate_user

router = APIRouter(prefix="/auth", tags=["auth"])

# Signup
@router.post("/signup", response_class=JSONResponse)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    return create_user(db, user)

# Login
@router.post("/login", response_class=JSONResponse)
def login(user: UserLogin, db: Session = Depends(get_db)):
    return authenticate_user(db, user)

##@router.get("/me", response_model=UserBase)
##def get_current_user_info(current_user: UserBase = Depends(get_current_user)):
##    return current_user