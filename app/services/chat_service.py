from typing import List, Optional, Dict, Any
from datetime import datetime
import re
from app.models.chat import ChatHistory, ChatMessage, ChatResponse, MessageType
from app.models.user import User
from app.services.stock_service import StockService

class ChatService:
    @staticmethod
    async def process_message(
        user: User,
        message: ChatMessage,
        session_id: str
    ) -> ChatResponse:
        """Process a chat message and return AI response"""
        
        # Save user message
        user_chat = ChatHistory(
            user_id=str(user.id),
            session_id=session_id,
            message_type=message.message_type,
            content=message.content,
            metadata=message.metadata
        )
        await user_chat.save()
        
        # Process the message and generate response
        response_content = await ChatService._generate_response(message.content, user)
        
        # Save AI response
        ai_response = ChatHistory(
            user_id=str(user.id),
            session_id=session_id,
            message_type=MessageType.ASSISTANT,
            content=response_content["content"],
            metadata=response_content.get("metadata")
        )
        await ai_response.save()
        
        return ChatResponse(
            id=str(ai_response.id),
            content=response_content["content"],
            message_type=MessageType.ASSISTANT,
            metadata=response_content.get("metadata"),
            timestamp=ai_response.timestamp
        )
    
    @staticmethod
    async def _generate_response(message: str, user: User) -> Dict[str, Any]:
        """Generate AI response based on user message - Enhanced version"""
        # Import the enhanced logic from the dev chat route
        from app.api.routes.chat import send_dev_message, DevChatMessage
        
        # Create a dev message object to reuse the enhanced logic
        dev_message = DevChatMessage(content=message)
        
        # Get the enhanced response
        dev_response = await send_dev_message(dev_message)
        
        # Convert to the format expected by this service
        return {
            "content": dev_response.content,
            "metadata": {
                "type": "enhanced_response",
                "source": "dev_chat_logic"
            }
        }
    
    @staticmethod
    def _extract_stock_symbols(message: str) -> List[str]:
        """Extract potential stock symbols from message"""
        # Look for patterns like AAPL, GOOGL, RELIANCE, etc.
        symbols = re.findall(r'\b[A-Z]{2,10}\b', message.upper())
        
        # Common stock symbols
        known_symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'RELIANCE', 'TCS', 'INFY', 'HDFCBANK']
        
        # Filter to known symbols or return all uppercase words
        result = [s for s in symbols if s in known_symbols] or symbols[:3]  # Max 3 symbols
        return result
    
    @staticmethod
    async def _handle_price_query(symbol: str) -> Dict[str, Any]:
        """Handle stock price queries"""
        stock_data = await StockService.get_stock_data(symbol)
        
        if stock_data:
            change_text = "up" if stock_data.price_change >= 0 else "down"
            return {
                "content": f"📈 **{stock_data.symbol}** ({stock_data.name})\n\n"
                          f"💰 **Current Price**: ${stock_data.current_price:.2f}\n"
                          f"📊 **Change**: {change_text} ${abs(stock_data.price_change):.2f} "
                          f"({stock_data.price_change_percent:.2f}%)\n"
                          f"🏢 **Exchange**: {stock_data.exchange}\n"
                          f"🕐 **Last Updated**: {stock_data.last_updated.strftime('%Y-%m-%d %H:%M:%S')}",
                "metadata": {
                    "type": "stock_quote",
                    "symbol": stock_data.symbol,
                    "price": float(stock_data.current_price),
                    "change": float(stock_data.price_change),
                    "change_percent": float(stock_data.price_change_percent)
                }
            }
        else:
            return {
                "content": f"❌ Sorry, I couldn't find stock data for **{symbol}**. "
                          f"Please check the symbol and try again.",
                "metadata": {"type": "error", "symbol": symbol}
            }
    
    @staticmethod
    async def _handle_stock_search(symbol: str) -> Dict[str, Any]:
        """Handle stock search queries"""
        stocks = await StockService.search_stocks(symbol, limit=5)
        
        if stocks:
            content = f"🔍 **Search results for '{symbol}':**\n\n"
            for stock in stocks:
                change_emoji = "📈" if stock.price_change >= 0 else "📉"
                content += f"{change_emoji} **{stock.symbol}** - {stock.name}\n"
                content += f"   ${stock.current_price:.2f} ({stock.price_change_percent:+.2f}%)\n\n"
            
            return {
                "content": content,
                "metadata": {
                    "type": "search_results",
                    "query": symbol,
                    "results": [{"symbol": s.symbol, "name": s.name} for s in stocks]
                }
            }
        else:
            return {
                "content": f"❌ No stocks found matching **{symbol}**. Try a different search term.",
                "metadata": {"type": "no_results", "query": symbol}
            }
    
    @staticmethod
    async def _handle_watchlist_query(user: User) -> Dict[str, Any]:
        """Handle watchlist queries"""
        if not user.watchlist:
            return {
                "content": "📝 Your watchlist is empty. Add some stocks to get started!\n\n"
                          "Try saying: 'Add AAPL to my watchlist' or 'Show me TSLA price'",
                "metadata": {"type": "empty_watchlist"}
            }
        
        content = "📋 **Your Watchlist:**\n\n"
        watchlist_data = []
        
        for symbol in user.watchlist:
            stock_data = await StockService.get_stock_data(symbol)
            if stock_data:
                change_emoji = "📈" if stock_data.price_change >= 0 else "📉"
                content += f"{change_emoji} **{stock_data.symbol}** - {stock_data.name}\n"
                content += f"   ${stock_data.current_price:.2f} ({stock_data.price_change_percent:+.2f}%)\n\n"
                
                watchlist_data.append({
                    "symbol": stock_data.symbol,
                    "price": float(stock_data.current_price),
                    "change_percent": float(stock_data.price_change_percent)
                })
        
        return {
            "content": content,
            "metadata": {
                "type": "watchlist",
                "stocks": watchlist_data
            }
        }
    
    @staticmethod
    async def _handle_trending_query() -> Dict[str, Any]:
        """Handle trending stocks queries"""
        trending_stocks = await StockService.get_trending_stocks(limit=5)
        
        if trending_stocks:
            content = "🔥 **Trending Stocks:**\n\n"
            for stock in trending_stocks:
                change_emoji = "📈" if stock.price_change >= 0 else "📉"
                content += f"{change_emoji} **{stock.symbol}** - {stock.name}\n"
                content += f"   ${stock.current_price:.2f} ({stock.price_change_percent:+.2f}%)\n\n"
            
            return {
                "content": content,
                "metadata": {
                    "type": "trending_stocks",
                    "stocks": [{"symbol": s.symbol, "name": s.name} for s in trending_stocks]
                }
            }
        else:
            return {
                "content": "📊 No trending stocks data available right now. Try again later!",
                "metadata": {"type": "no_trending_data"}
            }
    
    @staticmethod
    def _handle_help_query() -> Dict[str, Any]:
        """Handle help queries"""
        return {
            "content": "🤖 **I can help you with:**\n\n"
                      "📈 **Stock Prices**: 'What's the price of AAPL?'\n"
                      "🔍 **Search Stocks**: 'Find Apple stocks'\n"
                      "📋 **Watchlist**: 'Show my watchlist'\n"
                      "🔥 **Trending**: 'What's trending?'\n"
                      "➕ **Add to Watchlist**: 'Add TSLA to watchlist'\n"
                      "➖ **Remove from Watchlist**: 'Remove MSFT from watchlist'\n\n"
                      "💡 **Tip**: Just mention a stock symbol (like AAPL, GOOGL) and I'll show you the price!",
            "metadata": {"type": "help"}
        }
    
    @staticmethod
    def _handle_default_query(message: str) -> Dict[str, Any]:
        """Handle default/unknown queries"""
        return {
            "content": "🤔 I'm not sure how to help with that. Here are some things I can do:\n\n"
                      "• Get stock prices: 'AAPL price' or 'What's Tesla worth?'\n"
                      "• Search stocks: 'Find Microsoft' or 'Show me tech stocks'\n"
                      "• Show your watchlist: 'My watchlist' or 'My stocks'\n"
                      "• Show trending stocks: 'What's hot?' or 'Trending stocks'\n\n"
                      "Try asking about a specific stock or say 'help' for more options!",
            "metadata": {"type": "default_response", "original_message": message}
        }
    
    @staticmethod
    async def get_chat_history(
        user_id: str,
        session_id: str,
        limit: int = 50
    ) -> List[ChatResponse]:
        """Get chat history for a user session"""
        chat_history = await ChatHistory.find(
            {"user_id": user_id, "session_id": session_id}
        ).sort([("timestamp", -1)]).limit(limit).to_list()
        
        return [
            ChatResponse(
                id=str(chat.id),
                content=chat.content,
                message_type=chat.message_type,
                metadata=chat.metadata,
                timestamp=chat.timestamp
            )
            for chat in reversed(chat_history)  # Reverse to get chronological order
        ]