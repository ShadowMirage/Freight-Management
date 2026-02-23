import uuid
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class ConversationSessionBase(BaseModel):
    phone_number: str = Field(..., max_length=20)
    current_flow: str = Field(..., max_length=50)
    current_step: str = Field(..., max_length=50)
    collected_data: Dict[str, Any] = Field(default_factory=dict)

class ConversationSessionCreate(ConversationSessionBase):
    pass

class ConversationSessionUpdate(BaseModel):
    current_step: Optional[str] = None
    collected_data: Optional[Dict[str, Any]] = None

class ConversationSessionInDB(ConversationSessionBase):
    id: uuid.UUID
    updated_at: datetime

    class Config:
        from_attributes = True
