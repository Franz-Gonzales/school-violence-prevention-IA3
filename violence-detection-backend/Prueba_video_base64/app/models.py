from sqlalchemy import Column, Integer, String, Text, DateTime, Float, LargeBinary
from sqlalchemy.sql import func
from .database import Base

class Video(Base):
    __tablename__ = "videos"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    video_base64 = Column(Text, nullable=False)  # Mantener TEXT pero sin límite
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    duration = Column(Float, default=0.0)
    file_size = Column(Integer, default=0)