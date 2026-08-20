from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database import Base
# from sqlalchemy.dialects.postgresql import UUID  <-- Isko hata dena agar hai toh

class User(Base):
    __tablename__ = "users"

    # UUID ko hata kar Integer aur autoincrement set kar de:
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
