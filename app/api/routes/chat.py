import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from app.models.user import User
from app.models.chat import ChatMessage, ChatResponse
from app.services.chat_service import ChatService
from app.api.deps import get_current_active_user
from app.core.config import settings
from pydantic import BaseModel

router = APIRouter()

class DevChatMessage(BaseModel):
    content: str
    message_type: str = "user"

class DevChatResponse(BaseModel):
    id: str
    content: str
    message_type: str
    timestamp: str

# Development endpoint - no auth required
@router.post("/dev/message", response_model=DevChatResponse)
async def send_dev_message(
    message: DevChatMessage,
    session_id: str = Query(default_factory=lambda: str(uuid.uuid4()))
):
    """Development chat endpoint with smart responses - no authentication required"""
    from datetime import datetime
    import re
    import yfinance as yf
    import asyncio
    
    content = message.content.lower()
    
    # Improved stock symbol detection
    symbols = re.findall(r'\b([A-Z]{2,5})\b', message.content.upper())
    
    # Indian stock symbols and company name mappings (NSE symbols)
    indian_stocks = {
        # Major IT Companies (NSE symbols)
        'TCS': 'Tata Consultancy Services',
        'TATA CONSULTANCY SERVICES': 'TCS',
        'TATA CONSULTANCY': 'TCS',
        'INFY': 'Infosys Limited',
        'INFOSYS': 'INFY',
        'HDB': 'HDFC Bank',         # ADR symbol for HDFC Bank (with clear labeling)
        'HDFC BANK': 'HDB',
        'HDFC': 'HDB',
        'IBN': 'ICICI Bank',        # ADR symbol for ICICI Bank  
        'ICICI BANK': 'IBN',
        'ICICI': 'IBN',
        'WIT': 'Wipro Limited',     # ADR symbol for Wipro
        'WIPRO': 'WIT',
        'HCLTECH': 'HCL Technologies',
        'HCL TECHNOLOGIES': 'HCLTECH',
        'HCL': 'HCLTECH',
        'TECHM': 'Tech Mahindra',
        'TECH MAHINDRA': 'TECHM',
        
        # Banking & Financial Services  
        'RELIANCE': 'Reliance Industries',
        'RELIANCE INDUSTRIES': 'RELIANCE',
        'SBIN': 'State Bank of India',
        'STATE BANK OF INDIA': 'SBIN',
        'SBI': 'SBIN',
        'KOTAKBANK': 'Kotak Mahindra Bank',
        'KOTAK MAHINDRA BANK': 'KOTAKBANK',
        'KOTAK': 'KOTAKBANK',
        'AXISBANK': 'Axis Bank',
        'AXIS BANK': 'AXISBANK',
        'AXIS': 'AXISBANK',
        'INDUSINDBK': 'IndusInd Bank',
        'INDUSIND BANK': 'INDUSINDBK',
        'INDUSIND': 'INDUSINDBK',
        'BAJFINANCE': 'Bajaj Finance',
        'BAJAJ FINANCE': 'BAJFINANCE',
        'BAJAJ': 'BAJFINANCE',
        
        # Automobiles
        'MARUTI': 'Maruti Suzuki India',
        'MARUTI SUZUKI': 'MARUTI',
        'TATAMOTOR': 'Tata Motors',
        'TATA MOTORS': 'TATAMOTOR',
        'M&M': 'Mahindra & Mahindra',
        'MAHINDRA': 'M&M',
        'MAHINDRA & MAHINDRA': 'M&M',
        'BAJAJ-AUTO': 'Bajaj Auto',
        'BAJAJ AUTO': 'BAJAJ-AUTO',
        'EICHERMOT': 'Eicher Motors',
        'EICHER MOTORS': 'EICHERMOT',
        'EICHER': 'EICHERMOT',
        'TATAMOTORS': 'Tata Motors',
        
        # Pharmaceuticals
        'SUNPHARMA': 'Sun Pharmaceutical',
        'SUN PHARMACEUTICAL': 'SUNPHARMA',
        'SUN PHARMA': 'SUNPHARMA',
        'DRREDDY': "Dr. Reddy's Laboratories",
        'DR REDDY': 'DRREDDY',
        'DR REDDYS': 'DRREDDY',
        'CIPLA': 'Cipla Limited',
        'BIOCON': 'Biocon Limited',
        'LUPIN': 'Lupin Limited',
        'AUROPHARMA': 'Aurobindo Pharma',
        'AUROBINDO PHARMA': 'AUROPHARMA',
        'AUROBINDO': 'AUROPHARMA',
        
        # Telecom
        'BHARTIARTL': 'Bharti Airtel',
        'BHARTI AIRTEL': 'BHARTIARTL',
        'AIRTEL': 'BHARTIARTL',
        'JIO': 'Reliance Jio', # Note: Jio is part of Reliance
        'RELIANCE JIO': 'RELIANCE',
        
        # Consumer Goods
        'ITC': 'ITC Limited',
        'HINDUNILVR': 'Hindustan Unilever',
        'HINDUSTAN UNILEVER': 'HINDUNILVR',
        'HUL': 'HINDUNILVR',
        'NESTLEIND': 'Nestle India',
        'NESTLE INDIA': 'NESTLEIND',
        'NESTLE': 'NESTLEIND',
        'BRITANNIA': 'Britannia Industries',
        'BRITANNIA INDUSTRIES': 'BRITANNIA',
        'DABUR': 'Dabur India',
        'DABUR INDIA': 'DABUR',
        'GODREJCP': 'Godrej Consumer Products',
        'GODREJ': 'GODREJCP',
        
        # Metals & Mining
        'TATASTEEL': 'Tata Steel',
        'TATA STEEL': 'TATASTEEL',
        'HINDALCO': 'Hindalco Industries',
        'HINDALCO INDUSTRIES': 'HINDALCO',
        'JSWSTEEL': 'JSW Steel',
        'JSW STEEL': 'JSWSTEEL',
        'JSW': 'JSWSTEEL',
        'SAILSTEEL': 'Steel Authority of India',
        'SAIL': 'SAILSTEEL',
        'VEDL': 'Vedanta Limited',
        'VEDANTA': 'VEDL',
        
        # Oil & Gas
        'ONGC': 'Oil and Natural Gas Corporation',
        'OIL AND NATURAL GAS': 'ONGC',
        'BPCL': 'Bharat Petroleum Corporation',
        'BHARAT PETROLEUM': 'BPCL',
        'IOCL': 'Indian Oil Corporation',
        'INDIAN OIL': 'IOCL',
        'GAIL': 'GAIL (India) Limited',
        'GAIL INDIA': 'GAIL',
        
        # Power & Infrastructure
        'NTPC': 'NTPC Limited',
        'POWERGRID': 'Power Grid Corporation',
        'POWER GRID': 'POWERGRID',
        'LT': 'Larsen & Toubro',
        'LARSEN TOUBRO': 'LT',
        'LARSEN & TOUBRO': 'LT',
        'L&T': 'LT',
        'ADANIPORTS': 'Adani Ports',
        'ADANI PORTS': 'ADANIPORTS',
        'ADANI': 'ADANIPORTS',
        
        # Cement
        'ULTRACEMCO': 'UltraTech Cement',
        'ULTRATECH CEMENT': 'ULTRACEMCO',
        'ULTRATECH': 'ULTRACEMCO',
        'AMBUJACEM': 'Ambuja Cements',
        'AMBUJA CEMENTS': 'AMBUJACEM',
        'AMBUJA': 'AMBUJACEM',
        'ACC': 'ACC Limited',
        'SHREECEM': 'Shree Cement',
        'SHREE CEMENT': 'SHREECEM',
        
        # Miscellaneous
        'ASIANPAINT': 'Asian Paints',
        'ASIAN PAINTS': 'ASIANPAINT',
        'ASIAN PAINT': 'ASIANPAINT',
        'TITAN': 'Titan Company',
        'TITAN COMPANY': 'TITAN',
        'BAJAJFINSV': 'Bajaj Finserv',
        'BAJAJ FINSERV': 'BAJAJFINSV',
        'HDFCLIFE': 'HDFC Life Insurance',
        'HDFC LIFE': 'HDFCLIFE',
        'SBILIFE': 'SBI Life Insurance',
        'SBI LIFE': 'SBILIFE'
    }
    
    # Extract known symbols from the mapping
    known_stocks = list(set([v if v in indian_stocks else k for k, v in indian_stocks.items() if len(k) <= 10 and k.isupper()]))
    
    # Add some global stocks for comparison
    known_stocks.extend(['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'META', 'NFLX', 'NVDA', 'AMD', 'INTC'])
    
    # Common English words to exclude
    common_words = ['WHAT', 'THE', 'FOR', 'AND', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'WILL', 'HAVE', 'THIS', 'THAT', 'WITH', 'FROM', 'THEY', 'BEEN', 'HAVE', 'THEIR', 'WOULD', 'THERE', 'COULD', 'OTHER', 'AFTER', 'FIRST', 'WELL', 'ALSO', 'JUST', 'WHERE', 'MOST', 'KNOW', 'GET', 'USE', 'YEAR', 'WORK', 'PART', 'TIME', 'VERY', 'WHEN', 'MUCH', 'NEW', 'NOW', 'OLD', 'SEE', 'HIM', 'TWO', 'HOW', 'ITS', 'WHO', 'OIL', 'SIT', 'SET', 'HAD', 'LET', 'SAY', 'SHE', 'MAY', 'HER', 'HIM', 'HIS', 'HAS', 'ONE', 'OUR', 'OUT', 'DAY', 'WAY', 'PUT', 'END', 'WHY', 'TRY', 'GOD', 'SIX', 'DOG', 'EAT', 'AGO', 'SIR', 'FAR', 'SEA', 'EYE', 'BIG', 'BOX', 'YET', 'OFF', 'CUT', 'YES', 'CAR', 'JOB', 'LOT', 'FUN', 'RUN', 'TOP', 'ARM', 'BAD', 'BED', 'WIN', 'FIRE', 'FOUR', 'FIVE', 'SIZE', 'ONCE', 'TAKE', 'BACK', 'COME', 'GIVE', 'LOOK', 'MOVE', 'LIVE', 'SEEM', 'FEEL', 'KEEP', 'TURN', 'CALL', 'HELP', 'NEED', 'TELL', 'LONG', 'LATE', 'LAST', 'HIGH', 'GOOD', 'BEST', 'NEXT', 'OPEN', 'SURE', 'FULL', 'HARD', 'LEFT', 'EACH', 'REAL', 'BOTH', 'SAME', 'TRUE', 'MANY', 'SOME', 'FIND', 'SHOW', 'PRICE', 'OF']
    
    # Enhanced symbol detection for Indian stocks
    def detect_stock_symbols(text):
        detected_symbols = []
        text_upper = text.upper()
        
        # Method 1: Direct symbol matching from regex
        regex_symbols = [s for s in symbols if s in known_stocks]
        detected_symbols.extend(regex_symbols)
        
        # Method 2: Company name matching - prioritize exact matches
        # Sort by length (longer first) to match "HDFC BANK" before "HDFC"
        sorted_companies = sorted(indian_stocks.items(), key=lambda x: len(x[0]), reverse=True)
        
        for company_name, symbol in sorted_companies:
            if company_name in text_upper:
                # Always use the symbol (shorter identifier)
                if len(symbol) <= 10 and symbol.isupper():
                    detected_symbols.append(symbol)
                elif len(company_name) <= 10 and company_name.isupper():
                    detected_symbols.append(company_name)
                # Once we find a match, break to avoid multiple matches
                if detected_symbols:
                    break
        
        # Remove duplicates and filter
        detected_symbols = list(set(detected_symbols))
        
        # If no symbols found, try regex with common word filtering
        if not detected_symbols:
            detected_symbols = [s for s in symbols if s not in common_words and len(s) >= 2 and len(s) <= 10 and s.isalpha()]
        
        return detected_symbols[:3]  # Return max 3 symbols
    
    symbols = detect_stock_symbols(message.content)
    
    # Stock price queries
    if any(word in content for word in ["price", "quote", "cost", "value"]) and symbols:
        symbol = symbols[0]
        try:
            # Get stock data directly from yfinance for demo
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(None, lambda: yf.Ticker(symbol))
            info = await loop.run_in_executor(None, lambda: ticker.info)
            hist = await loop.run_in_executor(None, lambda: ticker.history(period="1d"))
            
            if not hist.empty:
                current_price = float(hist['Close'].iloc[-1])
                prev_close = float(info.get('previousClose', current_price))
                change = current_price - prev_close
                change_percent = (change / prev_close) * 100 if prev_close > 0 else 0
                
                change_text = "📈 up" if change >= 0 else "📉 down"
                exchange_info = info.get('exchange', 'Unknown')
                
                # Add context for ADR vs Indian exchange
                exchange_note = ""
                if "NYSE" in exchange_info or "NYQ" in exchange_info or "NASDAQ" in exchange_info:
                    exchange_note = "\n\n*📍 Showing ADR price (Indian stock trading on US exchange)*"
                elif "NSE" in exchange_info or "BSE" in exchange_info:
                    exchange_note = "\n\n*🇮🇳 Direct Indian market data*"
                
                response_content = f"💰 **{symbol}** ({info.get('longName', symbol)})\n\n" \
                                f"**Current Price**: ${current_price:.2f}\n" \
                                f"**Change**: {change_text} ${abs(change):.2f} ({change_percent:+.2f}%)\n" \
                                f"**Market Cap**: ${info.get('marketCap', 0):,.0f}\n" \
                                f"**Exchange**: {exchange_info}{exchange_note}"
            else:
                response_content = f"❌ Sorry, I couldn't find stock data for **{symbol}**. Please check the symbol and try again."
        except Exception as e:
            response_content = f"❌ Error fetching data for **{symbol}**: {str(e)}"
    
    # Help queries
    elif any(word in content for word in ["help", "commands", "what can you do"]):
        response_content = "🇮🇳 **StockChat - Indian Stock Market AI**\n\n" \
                          "🤖 **I can help you with:**\n\n" \
                          "📈 **Stock Prices**: 'Reliance price' or 'What's TCS worth?'\n" \
                          "🔍 **Company Search**: 'Tell me about Infosys' or 'HDFC Bank price'\n" \
                          "💡 **Smart Recognition**: Use company names or symbols!\n" \
                          "   • 'Tata Consultancy Services' → TCS\n" \
                          "   • 'HDFC Bank' → HDFCBANK\n" \
                          "   • 'Reliance Industries' → RELIANCE\n\n" \
                          "**Popular Stocks**: TCS, RELIANCE, INFY, HDFCBANK, ICICIBANK, SBIN, MARUTI, ITC\n\n" \
                          "Try: 'TCS price', 'What's Reliance worth?', or 'Infosys stock'"
    
    # Default response
    else:
        if symbols:
            response_content = f"🔍 I detected stock symbol **{symbols[0]}**. Try asking: 'What's the price of {symbols[0]}?' for detailed information!"
        else:
            response_content = "🇮🇳 I'm your Indian Stock Market AI! Ask me about stocks like:\n\n" \
                              "• 'Reliance price' or 'What's TCS worth?'\n" \
                              "• 'HDFC Bank stock' or 'Infosys price'\n" \
                              "• 'Tell me about Tata Motors'\n\n" \
                              "I understand both company names and symbols. Say 'help' for more options!"
    
    return DevChatResponse(
        id=str(uuid.uuid4()),
        content=response_content,
        message_type="assistant",
        timestamp=datetime.utcnow().isoformat()
    )

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