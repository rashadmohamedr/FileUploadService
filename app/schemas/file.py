from pydantic import BaseModel
from datetime import datetime

class FileBase(BaseModel):
    id: int
    ownerID: int
    name: str
    content_type: str | None = None
    path: str
    uploaded_at: datetime

class FileRead(FileBase):

    class Config:
        from_attributes = True

class FileCreate(FileBase):
    pass