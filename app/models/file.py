from sqlalchemy import Column, Integer,Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import datetime

# Task table
class File(Base):
    __tablename__ = "Files"

    id = Column(Integer, primary_key=True, index=True)
    saved_name = Column(String, unique=True, nullable=False)
    uploaded_name = Column(String,  nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content_type = Column(String,nullable=True)
    path  = Column(String, unique=True, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    owner = relationship("User", back_populates="files")

    # the following fields for analytics
    size = Column(Float)  # File size in bytes
    content_type = Column(String)