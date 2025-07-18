from typing import Optional, Dict, Any
from datetime import datetime
from beanie import Document
from pydantic import BaseModel, Field
from enum import Enum

class MessageType(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ChatHistory(Document):
    user_id: str = Field(..., index=True)
    session_id: str = Field(..., index=True)
    message_type: MessageType
    content: str
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        collection = "chat_history"
        indexes = [
            [("user_id", 1), ("session_id", 1), ("timestamp", -1)],
        ]

class ChatMessage(BaseModel):
    content: str
    message_type: MessageType = MessageType.USER
    metadata: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    id: str
    content: str
    message_type: MessageType
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime