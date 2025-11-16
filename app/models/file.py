from sqlalchemy import Column, Integer, String, DateTime
from app.db.database import Base
from datetime import datetime

# Task table
class File(Base):
    __tablename__ = "Tasks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    ownerID = Column(Integer, nullable=False)
    content_type = Column(String,nullable=True)
    path  = Column(String, unique=True, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)