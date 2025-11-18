from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from fastapi import Depends, HTTPException, status


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# TODO: Create a dependency `get_current_user` that verifies the current user from the JWT token.
async def get_current_user():
    # ... existing logic to get user from token ...
    pass


async def get_current_admin(current_user=Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user
    pass