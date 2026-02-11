from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import decode_access_token
from app.models.user import User

security = HTTPBearer()

def get_db():
    """Database dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency that verifies JWT token and returns current user.
    
    Args:
        credentials: HTTP Authorization credentials containing the JWT token
        db: Database session
    
    Returns:
        Current authenticated user
    
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Extract and decode token
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise credentials_exception
    
    # Get user ID from token
    user_id: int = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    # Fetch user from database
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency that verifies current user has admin privileges.
    
    Args:
        current_user: Current authenticated user from get_current_user
    
    Returns:
        Current user if they are an admin
    
    Raises:
        HTTPException: If user doesn't have admin privileges
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user