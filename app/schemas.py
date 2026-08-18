from datetime import datetime

from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    business_id: int
    sender_id: int
    content: str = Field(min_length=1)
    sent_at: datetime


class MessageResponse(BaseModel):
    id: int
    business_id: int
    sender_id: int
    content: str
    sent_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class EntityMessageResponse(BaseModel):
    id: int
    business_id: int
    sender_id: int
    content: str
    sent_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True