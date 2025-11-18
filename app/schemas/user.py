from datetime import datetime
from pydantic import BaseModel, EmailStr

# Shared properties
class UserBase(BaseModel):
    email: EmailStr

# Properties to receive via API on creation
class UserCreate(UserBase):
    username: str
    password: str

# Properties to receive via API on login
class UserLogin(UserBase):
    password: str

# Properties to return to client
class User(UserBase):
    username: str
    # is_active: bool
    is_admin: bool
    last_login: datetime | None = None

    class Config:
        orm_mode = True

# Properties stored in DB
class UserInDB(User):
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str