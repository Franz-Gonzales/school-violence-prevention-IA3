# app/schemas.py
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class VideoBase(BaseModel):
    filename: str
    duration: Optional[float] = 0.0
    file_size: Optional[int] = 0

class VideoCreate(VideoBase):
    video_base64: str

class VideoResponse(VideoBase):
    id: int
    created_at: datetime
    
    # Pydantic V2 - cambio de orm_mode a from_attributes
    model_config = ConfigDict(from_attributes=True)

class VideoWithBase64(VideoResponse):
    video_base64: str