import uuid
from typing import List
from fastapi import APIRouter, Depends, Query
from app.models.user import User
from app.models.chat import ChatMessage, ChatResponse
from app.services.chat_service import ChatService
from app.api.deps import get_current_active_user

router = APIRouter()

@router.post("/message", response_model=ChatResponse)
async def send_message(
    message: ChatMessage,
    session_id: str = Query(default_factory=lambda: str(uuid.uuid4())),
    current_user: User = Depends(get_current_active_user)
):
    """Send a chat message and get AI response"""
    return await ChatService.process_message(current_user, message, session_id)

@router.get("/history", response_model=List[ChatResponse])
async def get_chat_history(
    session_id: str = Query(..., description="Chat session ID"),
    limit: int = Query(50, ge=1, le=100, description="Number of messages to return"),
    current_user: User = Depends(get_current_active_user)
):
    """Get chat history for a session"""
    return await ChatService.get_chat_history(str(current_user.id), session_id, limit)

@router.delete("/history/{session_id}")
async def clear_chat_history(
    session_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Clear chat history for a session"""
    await ChatHistory.find({
        "user_id": str(current_user.id),
        "session_id": session_id
    }).delete()
    
    return {"message": f"Chat history cleared for session {session_id}"}