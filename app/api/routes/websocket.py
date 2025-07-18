import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from app.services.websocket_service import connection_manager
from app.core.security import verify_token
from app.models.user import User
from app.services.stock_service import StockService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

async def get_user_from_websocket_token(token: str) -> User:
    """Authenticate user from WebSocket token"""
    if not token:
        raise ValueError("No token provided")
    
    payload = verify_token(token)
    if not payload:
        raise ValueError("Invalid token")
    
    user_id = payload.get("sub")
    if not user_id:
        raise ValueError("Invalid token payload")
    
    user = await User.get(user_id)
    if not user:
        raise ValueError("User not found")
    
    return user

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(None, description="JWT token for authentication")
):
    """WebSocket endpoint for real-time stock data"""
    try:
        # Authenticate user
        user = await get_user_from_websocket_token(token)
        user_id = str(user.id)
        
        # Connect user
        await connection_manager.connect(websocket, user_id)
        
        # Subscribe to user's watchlist automatically
        for symbol in user.watchlist:
            await connection_manager.subscribe_to_symbol(user_id, symbol)
        
        try:
            while True:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                message_type = message.get("type")
                
                if message_type == "subscribe":
                    symbol = message.get("symbol", "").upper()
                    if symbol:
                        await connection_manager.subscribe_to_symbol(user_id, symbol)
                        
                elif message_type == "unsubscribe":
                    symbol = message.get("symbol", "").upper()
                    if symbol:
                        await connection_manager.unsubscribe_from_symbol(user_id, symbol)
                        
                elif message_type == "get_stock_data":
                    symbol = message.get("symbol", "").upper()
                    if symbol:
                        stock_data = await StockService.get_stock_data(symbol)
                        if stock_data:
                            await connection_manager.send_personal_message({
                                "type": "stock_data_response",
                                "symbol": symbol,
                                "data": stock_data.dict(),
                                "timestamp": stock_data.last_updated.isoformat()
                            }, user_id)
                        else:
                            await connection_manager.send_personal_message({
                                "type": "error",
                                "message": f"Stock data not found for {symbol}",
                                "timestamp": None
                            }, user_id)
                            
                elif message_type == "ping":
                    await connection_manager.send_personal_message({
                        "type": "pong",
                        "timestamp": None
                    }, user_id)
                    
                else:
                    await connection_manager.send_personal_message({
                        "type": "error",
                        "message": f"Unknown message type: {message_type}",
                        "timestamp": None
                    }, user_id)
                    
        except WebSocketDisconnect:
            await connection_manager.disconnect(websocket, user_id)
            
    except ValueError as e:
        # Authentication failed
        await websocket.close(code=1008, reason=str(e))
        logger.warning(f"WebSocket authentication failed: {e}")
        
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=1011, reason="Internal server error")