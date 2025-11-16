from pydantic import BaseModel, EmailStr

# shared fields
class UserBase(BaseModel):
    email: EmailStr
    password: str

# used for sign up (adds username & password)
class UserCreate(UserBase):
    username: str

# used for login (only needs email + password)
class UserLogin(UserBase):
    pass

class Token(BaseModel):
    access_token: str
    token_type: str