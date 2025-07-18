import json
import asyncio
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Store subscriptions by user_id -> set of symbols
        self.user_subscriptions: Dict[str, Set[str]] = {}
        # Store symbol subscribers by symbol -> set of user_ids
        self.symbol_subscribers: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept WebSocket connection and add to manager"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        
        self.active_connections[user_id].append(websocket)
        
        if user_id not in self.user_subscriptions:
            self.user_subscriptions[user_id] = set()
        
        logger.info(f"User {user_id} connected. Total connections: {self.get_connection_count()}")
        
        # Send welcome message
        await self.send_personal_message({
            "type": "welcome",
            "message": "Connected to real-time stock data",
            "timestamp": datetime.utcnow().isoformat()
        }, user_id)

    async def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove WebSocket connection"""
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            
            # Clean up empty connection lists
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                
                # Remove user subscriptions
                if user_id in self.user_subscriptions:
                    symbols = self.user_subscriptions[user_id].copy()
                    for symbol in symbols:
                        await self.unsubscribe_from_symbol(user_id, symbol)
                    del self.user_subscriptions[user_id]
        
        logger.info(f"User {user_id} disconnected. Total connections: {self.get_connection_count()}")

    async def send_personal_message(self, message: dict, user_id: str):
        """Send message to specific user"""
        if user_id in self.active_connections:
            disconnected_connections = []
            
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except:
                    disconnected_connections.append(connection)
            
            # Clean up disconnected connections
            for connection in disconnected_connections:
                await self.disconnect(connection, user_id)

    async def subscribe_to_symbol(self, user_id: str, symbol: str):
        """Subscribe user to stock symbol updates"""
        symbol = symbol.upper()
        
        # Add to user subscriptions
        if user_id not in self.user_subscriptions:
            self.user_subscriptions[user_id] = set()
        self.user_subscriptions[user_id].add(symbol)
        
        # Add to symbol subscribers
        if symbol not in self.symbol_subscribers:
            self.symbol_subscribers[symbol] = set()
        self.symbol_subscribers[symbol].add(user_id)
        
        await self.send_personal_message({
            "type": "subscription_confirmed",
            "symbol": symbol,
            "message": f"Subscribed to {symbol} updates",
            "timestamp": datetime.utcnow().isoformat()
        }, user_id)
        
        logger.info(f"User {user_id} subscribed to {symbol}")

    async def unsubscribe_from_symbol(self, user_id: str, symbol: str):
        """Unsubscribe user from stock symbol updates"""
        symbol = symbol.upper()
        
        # Remove from user subscriptions
        if user_id in self.user_subscriptions:
            self.user_subscriptions[user_id].discard(symbol)
        
        # Remove from symbol subscribers
        if symbol in self.symbol_subscribers:
            self.symbol_subscribers[symbol].discard(user_id)
            
            # Clean up empty symbol subscribers
            if not self.symbol_subscribers[symbol]:
                del self.symbol_subscribers[symbol]
        
        await self.send_personal_message({
            "type": "unsubscription_confirmed",
            "symbol": symbol,
            "message": f"Unsubscribed from {symbol} updates",
            "timestamp": datetime.utcnow().isoformat()
        }, user_id)
        
        logger.info(f"User {user_id} unsubscribed from {symbol}")

    async def broadcast_stock_update(self, symbol: str, stock_data: dict):
        """Broadcast stock update to all subscribers of the symbol"""
        symbol = symbol.upper()
        
        if symbol in self.symbol_subscribers:
            message = {
                "type": "stock_update",
                "symbol": symbol,
                "data": stock_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Send to all subscribers
            for user_id in self.symbol_subscribers[symbol].copy():
                await self.send_personal_message(message, user_id)

    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return sum(len(connections) for connections in self.active_connections.values())

    def get_user_subscriptions(self, user_id: str) -> List[str]:
        """Get list of symbols user is subscribed to"""
        return list(self.user_subscriptions.get(user_id, set()))

# Global connection manager instance
connection_manager = ConnectionManager()