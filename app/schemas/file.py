from pydantic import BaseModel, Field
from datetime import datetime

class FileBase(BaseModel):
    model_config = {"from_attributes": True, "populate_by_name": True}

    id: int
    saved_name: str
    uploaded_name: str
    owner_id: int
    name: str = Field(validation_alias="uploaded_name")
    content_type: str | None = None
    path: str
    uploaded_at: datetime
    size: float | None = None

class FileRead(FileBase):
    class Config:
        from_attributes = True

class FileCreate(FileBase):
    pass