from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr
from app.models.user import UserCreate, UserResponse
from app.services.auth import AuthService
from app.api.deps import get_current_active_user
from app.models.user import User

router = APIRouter()
security = HTTPBearer()

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: UserResponse

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    """Register a new user"""
    return await AuthService.create_user(user_data)

@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest):
    """Login user and return tokens"""
    return await AuthService.login_user(login_data.email, login_data.password)

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        watchlist=current_user.watchlist,
        created_at=current_user.created_at
    )

@router.post("/logout")
async def logout():
    """Logout user (client should delete tokens)"""
    return {"message": "Successfully logged out"}