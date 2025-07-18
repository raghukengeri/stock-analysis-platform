from typing import Optional, List
from datetime import datetime
from beanie import Document
from pydantic import BaseModel, EmailStr, Field

class User(Document):
    email: EmailStr = Field(..., index=True, unique=True)
    username: str = Field(..., index=True, unique=True)
    full_name: Optional[str] = None
    hashed_password: str
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    watchlist: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        collection = "users"
        indexes = [
            "email",
            "username",
        ]

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    password: str

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    is_active: bool
    watchlist: List[str]
    created_at: datetime

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    watchlist: Optional[List[str]] = None