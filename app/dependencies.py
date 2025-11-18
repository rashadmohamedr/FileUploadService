from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from fastapi import Depends, HTTPException, status


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user():
    # ... existing logic to get user from token ...
    pass


# TODO: (Analytics) Create a dependency `get_current_admin` that verifies the current user has admin privileges.
# It should depend on `get_current_user` and raise an HTTPException with status 403 if `user.is_admin` is not True.
async def get_current_admin(current_user=Depends(get_current_user)):
    # if not current_user.is_admin:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="The user doesn't have enough privileges",
    #     )
    # return current_user
    pass