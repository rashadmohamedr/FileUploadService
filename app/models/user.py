from sqlalchemy import Column, Integer, String, Boolean, DateTime
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
    
    # TODO: Add the following fields for analytics and admin features
    # last_login = Column(DateTime, default=datetime.datetime.utcnow)
    # is_admin = Column(Boolean, default=False)
    # is_active = Column(Boolean, default=True)

    files = relationship("File", back_populates="owner", cascade="all, delete-orphan")