from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float
from sqlalchemy.orm import relationship
from app.db.database import Base
import datetime

# User table
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    
    # the following fields for analytics and admin features
    last_login = Column(DateTime, default=datetime.datetime.utcnow)
    is_admin = Column(Boolean, default=False)
    # is_active = Column(Boolean, default=True)
    total_storage_used = Column(Float, default=0)  # Total storage used by the user in bytes
    files = relationship("File", back_populates="owner", cascade="all, delete-orphan")
    events = relationship("AnalyticsEvent", back_populates="user", cascade="all, delete-orphan")