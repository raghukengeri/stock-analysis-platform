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
    
    # Improved stock symbol detection - include symbols starting with numbers
    symbols = re.findall(r'\b([0-9]*[A-Z][A-Z0-9]{1,9})\b', message.content.upper())
    
    # Indian stock symbols and company name mappings (NSE symbols)
    indian_stocks = {
        # Financial Services with numbers
        '360ONE': '360 ONE WAM Ltd.',
        '360 ONE WAM': '360ONE',
        '360 ONE': '360ONE',
        '3MINDIA': '3M India Ltd.',
        '3M INDIA': '3MINDIA',
        
        # Major IT Companies (NSE symbols)
        'TCS': 'Tata Consultancy Services',
        'TATA CONSULTANCY SERVICES': 'TCS',
        'TATA CONSULTANCY': 'TCS',
        'INFY': 'Infosys Limited',
        'INFOSYS': 'INFY',
        'HDFCBANK': 'HDFC Bank Limited',
        'HDFC BANK': 'HDFCBANK',
        'HDFC BANK LIMITED': 'HDFCBANK',
        'HDFCAMC': 'HDFC Asset Management Company Limited',
        'HDFC ASSET MANAGEMENT': 'HDFCAMC',
        'HDFC AMC': 'HDFCAMC',
        'ICICIBANK': 'ICICI Bank Limited',
        'ICICI BANK': 'ICICIBANK',
        'ICICI BANK LIMITED': 'ICICIBANK',
        'ICICIGI': 'ICICI Lombard General Insurance Company Limited',
        'ICICI LOMBARD': 'ICICIGI',
        'ICICIPRULI': 'ICICI Prudential Life Insurance Company Limited',
        'ICICI PRUDENTIAL': 'ICICIPRULI',
        'JIOFIN': 'Jio Financial Services Limited',
        'JIO FINANCIAL': 'JIOFIN',
        'JIO FINANCIAL SERVICES': 'JIOFIN',
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
        'SBI LIFE': 'SBILIFE',
        
        # Wind Energy & Others
        'INOXWIND': 'Inox Wind Limited',
        'INOX WIND': 'INOXWIND',  # Company name to symbol mapping
        'INOX WIND LIMITED': 'INOXWIND',
        'PVRINOX': 'PVR INOX Limited',
        'PVR INOX': 'PVRINOX',
        'PVR INOX LIMITED': 'PVRINOX',
        'GMDCLTD': 'Gujarat Mineral Development Corporation',
        'GUJARAT MINERAL DEVELOPMENT': 'GMDCLTD',
        'GUJARAT MINERAL DEVELOPMENT CORPORATION': 'GMDCLTD'
    }
    
    # Extract known symbols from the mapping
    known_stocks = list(set([v if v in indian_stocks else k for k, v in indian_stocks.items() if len(k) <= 10 and (k.isupper() or any(c.isdigit() for c in k))]))
    
    # Add some global stocks for comparison
    known_stocks.extend(['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'META', 'NFLX', 'NVDA', 'AMD', 'INTC'])
    
    # Common English words to exclude
    common_words = ['WHAT', 'THE', 'FOR', 'AND', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'WILL', 'HAVE', 'THIS', 'THAT', 'WITH', 'FROM', 'THEY', 'BEEN', 'HAVE', 'THEIR', 'WOULD', 'THERE', 'COULD', 'OTHER', 'AFTER', 'FIRST', 'WELL', 'ALSO', 'JUST', 'WHERE', 'MOST', 'KNOW', 'GET', 'USE', 'YEAR', 'WORK', 'PART', 'TIME', 'VERY', 'WHEN', 'MUCH', 'NEW', 'NOW', 'OLD', 'SEE', 'HIM', 'TWO', 'HOW', 'ITS', 'WHO', 'OIL', 'SIT', 'SET', 'HAD', 'LET', 'SAY', 'SHE', 'MAY', 'HER', 'HIM', 'HIS', 'HAS', 'ONE', 'OUR', 'OUT', 'DAY', 'WAY', 'PUT', 'END', 'WHY', 'TRY', 'GOD', 'SIX', 'DOG', 'EAT', 'AGO', 'SIR', 'FAR', 'SEA', 'EYE', 'BIG', 'BOX', 'YET', 'OFF', 'CUT', 'YES', 'CAR', 'JOB', 'LOT', 'FUN', 'RUN', 'TOP', 'ARM', 'BAD', 'BED', 'WIN', 'FIRE', 'FOUR', 'FIVE', 'SIZE', 'ONCE', 'TAKE', 'BACK', 'COME', 'GIVE', 'LOOK', 'MOVE', 'LIVE', 'SEEM', 'FEEL', 'KEEP', 'TURN', 'CALL', 'HELP', 'NEED', 'TELL', 'LONG', 'LATE', 'LAST', 'HIGH', 'GOOD', 'BEST', 'NEXT', 'OPEN', 'SURE', 'FULL', 'HARD', 'LEFT', 'EACH', 'REAL', 'BOTH', 'SAME', 'TRUE', 'MANY', 'SOME', 'FIND', 'SHOW', 'PRICE', 'OF']
    
    # Enhanced symbol detection for Indian stocks
    def detect_stock_symbols(text):
        detected_symbols = []
        text_upper = text.upper()
        
        # Method 1: Company name matching FIRST (prioritize multi-word company names)
        # Sort by length (longer first) to match "INOX WIND LIMITED" before "INOX WIND" before "INOX"
        sorted_companies = sorted(indian_stocks.items(), key=lambda x: len(x[0]), reverse=True)
        
        for company_name, symbol in sorted_companies:
            if company_name in text_upper:
                # Always use the symbol (shorter identifier)
                if len(symbol) <= 10 and symbol.isupper():
                    detected_symbols.append(symbol)
                elif len(company_name) <= 10 and company_name.isupper():
                    detected_symbols.append(company_name)
                # Once we find a match, break to avoid multiple matches
                break
        
        # Method 2: Look for exact stock symbols as standalone words (only if no company names found)
        if not detected_symbols:
            words = text_upper.split()
            for word in words:
                # Clean the word of common punctuation but keep alphanumeric
                clean_word = ''.join(c for c in word if c.isalnum())
                if clean_word and len(clean_word) >= 2:
                    # Check if this is a known symbol or could be a stock symbol
                    if clean_word in known_stocks:
                        detected_symbols.append(clean_word)
                    elif len(clean_word) >= 3 and clean_word.isalpha() and clean_word not in common_words:
                        # Potential stock symbol - add it for testing
                        detected_symbols.append(clean_word)
        
        # Method 3: Fallback to regex matching only if still no symbols
        if not detected_symbols:
            regex_symbols = [s for s in symbols if s in known_stocks]
            detected_symbols.extend(regex_symbols)
            
            # If still nothing, try filtered regex
            if not detected_symbols:
                detected_symbols = [s for s in symbols if s not in common_words and len(s) >= 2 and len(s) <= 10 and s.isalpha()]
        
        # Remove duplicates and return
        detected_symbols = list(dict.fromkeys(detected_symbols))  # Preserve order while removing duplicates
        return detected_symbols[:3]  # Return max 3 symbols
    
    symbols = detect_stock_symbols(message.content)
    
    # Fundamental analysis queries
    fundamental_keywords = {
        "pe": ["pe ratio", "p/e", "price to earnings", "pe multiple"],
        "pb": ["pb ratio", "p/b", "price to book", "book value"],
        "eps": ["eps", "earnings per share", "earnings"],
        "dividend": ["dividend", "dividend yield", "payout", "dividend per share"],
        "margin": ["margin", "profit margin", "operating margin", "profitability"],
        "debt": ["debt", "debt to equity", "leverage", "financial strength"],
        "trends": ["trends", "variance", "qoq", "yoy", "quarter", "year over year"],
        "growth": ["growth", "revenue growth", "earnings growth", "expansion"],
        "valuation": ["valuation", "expensive", "cheap", "overvalued", "undervalued"],
        "financials": ["financials", "financial", "fundamental", "fundamentals", "analysis"],
        "revenue": ["revenue", "sales", "turnover", "income"],
        "cash": ["cash flow", "free cash flow", "cash", "liquidity"],
        "beta": ["beta", "volatility", "risk"]
    }
    
    fundamental_query = None
    for category, keywords in fundamental_keywords.items():
        if any(keyword in content for keyword in keywords):
            fundamental_query = category
            break
    
    # Stock price queries
    if any(word in content for word in ["price", "quote", "cost", "value"]) and symbols and not fundamental_query:
        symbol = symbols[0]
        try:
            # Use our enhanced stock service with fallback logic
            from app.services.stock_service import StockService
            stock_data = await StockService.get_stock_data(symbol)
            
            if stock_data:
                change_text = "📈 up" if stock_data.price_change >= 0 else "📉 down"
                exchange_info = stock_data.exchange
                
                # Add context for ADR vs Indian exchange
                exchange_note = ""
                if "NYSE" in exchange_info or "NYQ" in exchange_info or "NASDAQ" in exchange_info or "ADR" in exchange_info:
                    exchange_note = "\n\n*📍 Showing ADR price (Indian stock trading on US exchange)*"
                elif "NSE" in exchange_info or "BSE" in exchange_info or "India" in exchange_info:
                    exchange_note = "\n\n*🇮🇳 Direct Indian market data*"
                
                # Format market cap properly
                market_cap_text = "N/A"
                if stock_data.market_cap:
                    if stock_data.market_cap >= 1e12:
                        market_cap_text = f"${stock_data.market_cap/1e12:.2f}T"
                    elif stock_data.market_cap >= 1e9:
                        market_cap_text = f"${stock_data.market_cap/1e9:.2f}B"
                    elif stock_data.market_cap >= 1e6:
                        market_cap_text = f"${stock_data.market_cap/1e6:.2f}M"
                    else:
                        market_cap_text = f"${stock_data.market_cap:,.0f}"
                
                # Use Indian Rupee symbol for NSE/BSE stocks
                currency = "₹" if ("NSE" in exchange_info or "BSE" in exchange_info) else "$"
                
                response_content = f"💰 **{stock_data.symbol}** ({stock_data.name})\n\n" \
                                f"**Current Price**: {currency}{stock_data.current_price:.2f}\n" \
                                f"**Change**: {change_text} {currency}{abs(stock_data.price_change):.2f} ({stock_data.price_change_percent:+.2f}%)\n" \
                                f"**Market Cap**: {market_cap_text}\n" \
                                f"**Exchange**: {exchange_info}{exchange_note}"
            else:
                # Enhanced error handling with suggestions
                def suggest_similar_symbols(failed_symbol):
                    suggestions = []
                    failed_upper = failed_symbol.upper()
                    message_upper = message.content.upper()
                    
                    # Method 1: Look for other potential symbols in the entire message
                    text_words = message_upper.split()
                    for word in text_words:
                        clean_word = ''.join(c for c in word if c.isalnum())
                        if (clean_word != failed_upper and 
                            len(clean_word) >= 3 and
                            clean_word not in common_words):
                            # Check if it's a known symbol
                            if clean_word in known_stocks:
                                suggestions.append(clean_word)
                            # Check if it's similar to known symbols (partial matching)
                            elif len(clean_word) >= 4:
                                for known_symbol in known_stocks:
                                    if (len(known_symbol) >= 4 and
                                        (clean_word in known_symbol or 
                                         known_symbol in clean_word or
                                         abs(len(clean_word) - len(known_symbol)) <= 1)):
                                        suggestions.append(known_symbol)
                    
                    # Method 2: Check similarity with failed symbol
                    if len(failed_upper) >= 3:
                        for known_symbol in known_stocks:
                            # String similarity checks
                            if (failed_upper in known_symbol or 
                                known_symbol in failed_upper or
                                abs(len(failed_upper) - len(known_symbol)) <= 2):
                                suggestions.append(known_symbol)
                    
                    return list(dict.fromkeys(suggestions))[:3]  # Return max 3 unique suggestions, preserve order
                
                suggestions = suggest_similar_symbols(symbol)
                
                if suggestions:
                    suggestion_text = ", ".join([f"**{s}**" for s in suggestions])
                    response_content = f"❌ Sorry, I couldn't find stock data for **{symbol}**.\n\n" \
                                    f"🤔 Did you mean: {suggestion_text}?\n\n" \
                                    f"💡 Try asking: 'What's the price of {suggestions[0]}?'"
                else:
                    response_content = f"❌ Sorry, I couldn't find stock data for **{symbol}**. Please check the symbol and try again.\n\n" \
                                    f"💡 Try popular stocks like: **TCS**, **RELIANCE**, **INFY**, **SBIN**, or **HDFCBANK**"
        except Exception as e:
            response_content = f"❌ Error fetching data for **{symbol}**: {str(e)}"
    
    # Fundamental analysis queries
    elif fundamental_query and symbols:
        symbol = symbols[0]
        try:
            from app.services.stock_service import StockService
            stock_data = await StockService.get_stock_data(symbol)
            
            if stock_data:
                currency = "₹" if ("NSE" in stock_data.exchange or "BSE" in stock_data.exchange) else "$"
                
                def format_number(value, suffix="", is_percentage=False, decimal_places=2):
                    if value is None:
                        return "N/A"
                    if is_percentage:
                        return f"{value:.{decimal_places}f}%"
                    if suffix == "cr":
                        return f"₹{value:.{decimal_places}f} cr" if value >= 0 else f"-₹{abs(value):.{decimal_places}f} cr"
                    return f"{value:.{decimal_places}f}{suffix}"
                
                def calculate_variance_analysis(current, qoq, yoy, metric_name, is_higher_better=True):
                    """Calculate variance analysis with trend interpretation"""
                    analysis = {}
                    
                    # QoQ Analysis
                    if current is not None and qoq is not None:
                        qoq_change = ((current - qoq) / qoq) * 100
                        analysis['qoq_change'] = qoq_change
                        analysis['qoq_direction'] = "📈" if qoq_change > 0 else "📉" if qoq_change < 0 else "➡️"
                        
                        if is_higher_better:
                            analysis['qoq_sentiment'] = "Improving" if qoq_change > 2 else "Declining" if qoq_change < -2 else "Stable"
                        else:
                            analysis['qoq_sentiment'] = "Improving" if qoq_change < -2 else "Declining" if qoq_change > 2 else "Stable"
                    
                    # YoY Analysis  
                    if current is not None and yoy is not None:
                        yoy_change = ((current - yoy) / yoy) * 100
                        analysis['yoy_change'] = yoy_change
                        analysis['yoy_direction'] = "📈" if yoy_change > 0 else "📉" if yoy_change < 0 else "➡️"
                        
                        if is_higher_better:
                            analysis['yoy_sentiment'] = "Strong Growth" if yoy_change > 10 else "Moderate Growth" if yoy_change > 0 else "Declining"
                        else:
                            analysis['yoy_sentiment'] = "Strong Improvement" if yoy_change < -10 else "Moderate Improvement" if yoy_change < 0 else "Deteriorating"
                    
                    return analysis
                
                if fundamental_query == "pe":
                    pe_analysis = ""
                    if stock_data.pe_ratio:
                        if stock_data.pe_ratio < 15:
                            pe_analysis = "📊 **Low P/E** - May indicate undervalued stock or slower growth"
                        elif stock_data.pe_ratio > 25:
                            pe_analysis = "📊 **High P/E** - May indicate high growth expectations or overvaluation"
                        else:
                            pe_analysis = "📊 **Moderate P/E** - Reasonable valuation range"
                    
                    response_content = f"📈 **{stock_data.symbol} - P/E Ratio Analysis**\n\n" \
                                    f"**Current P/E Ratio**: {format_number(stock_data.pe_ratio, 'x')}\n" \
                                    f"**Current Price**: {currency}{stock_data.current_price:.2f}\n" \
                                    f"**EPS**: {currency}{format_number(stock_data.eps)}\n\n" \
                                    f"{pe_analysis}\n\n" \
                                    f"💡 **P/E Ratio** shows how much investors pay for each rupee of earnings"
                
                elif fundamental_query == "dividend":
                    div_analysis = ""
                    if stock_data.dividend_yield:
                        if stock_data.dividend_yield > 4:
                            div_analysis = "💰 **High Dividend Yield** - Good for income investors"
                        elif stock_data.dividend_yield > 2:
                            div_analysis = "💰 **Moderate Dividend Yield** - Balanced income potential"
                        else:
                            div_analysis = "💰 **Low Dividend Yield** - Growth-focused company"
                    
                    response_content = f"💰 **{stock_data.symbol} - Dividend Analysis**\n\n" \
                                    f"**Dividend Yield**: {format_number(stock_data.dividend_yield, is_percentage=True)}\n" \
                                    f"**Dividend Per Share**: {currency}{format_number(stock_data.dividend_per_share)}\n" \
                                    f"**Payout Ratio**: {format_number(stock_data.payout_ratio, is_percentage=True)}\n\n" \
                                    f"{div_analysis}\n\n" \
                                    f"💡 **Dividend Yield** = Annual Dividend ÷ Current Price"
                
                elif fundamental_query == "financials":
                    response_content = f"📊 **{stock_data.symbol} - Complete Fundamentals**\n\n" \
                                    f"**💰 Valuation Metrics**\n" \
                                    f"• P/E Ratio: {format_number(stock_data.pe_ratio, 'x')}\n" \
                                    f"• P/B Ratio: {format_number(stock_data.pb_ratio, 'x')}\n" \
                                    f"• EPS: {currency}{format_number(stock_data.eps)}\n\n" \
                                    f"**📈 Performance Metrics**\n" \
                                    f"• Revenue: {format_number(stock_data.revenue, 'cr')}\n" \
                                    f"• Net Income: {format_number(stock_data.net_income, 'cr')}\n" \
                                    f"• Profit Margin: {format_number(stock_data.profit_margin, is_percentage=True)}\n\n" \
                                    f"**💪 Financial Strength**\n" \
                                    f"• Current Ratio: {format_number(stock_data.current_ratio, 'x')}\n" \
                                    f"• Debt-to-Equity: {format_number(stock_data.debt_to_equity, 'x')}\n" \
                                    f"• Beta: {format_number(stock_data.beta)}\n\n" \
                                    f"**🌱 Growth & Dividends**\n" \
                                    f"• Revenue Growth: {format_number(stock_data.revenue_growth, is_percentage=True)}\n" \
                                    f"• Dividend Yield: {format_number(stock_data.dividend_yield, is_percentage=True)}"
                
                elif fundamental_query == "margin":
                    # Margin Analysis with Trends
                    margin_variance = calculate_variance_analysis(
                        stock_data.profit_margin,
                        stock_data.profit_margin_qoq,
                        stock_data.profit_margin_yoy,
                        "profit_margin",
                        is_higher_better=True
                    )
                    
                    margin_analysis = ""
                    if stock_data.profit_margin:
                        if stock_data.profit_margin > 15:
                            margin_analysis = "🟢 **High Profitability** - Strong profit margins"
                        elif stock_data.profit_margin > 5:
                            margin_analysis = "🟡 **Moderate Profitability** - Decent profit margins"
                        else:
                            margin_analysis = "🔴 **Low Profitability** - Weak profit margins"
                    
                    trend_insight = ""
                    if margin_variance.get('yoy_sentiment'):
                        if margin_variance['yoy_sentiment'] in ['Strong Growth', 'Moderate Growth']:
                            trend_insight = "📈 **Improving Efficiency** - Profit margins expanding over time"
                        elif margin_variance['yoy_sentiment'] == 'Declining':
                            trend_insight = "📉 **Margin Pressure** - Profitability declining, may indicate cost pressures"
                        else:
                            trend_insight = "➡️ **Stable Operations** - Consistent margin performance"
                    
                    response_content = f"📊 **{stock_data.symbol} - Profitability Analysis**\n\n" \
                                    f"**🎯 Current Profitability**\n" \
                                    f"• Operating Margin: {format_number(stock_data.operating_margin, is_percentage=True)}\n" \
                                    f"• Profit Margin: {format_number(stock_data.profit_margin, is_percentage=True)}\n\n" \
                                    f"**📈 Profit Margin Trends**\n"
                    
                    if margin_variance.get('qoq_change') is not None:
                        response_content += f"• QoQ: {margin_variance['qoq_direction']} {margin_variance['qoq_change']:+.1f}% ({margin_variance['qoq_sentiment']})\n"
                    if margin_variance.get('yoy_change') is not None:
                        response_content += f"• YoY: {margin_variance['yoy_direction']} {margin_variance['yoy_change']:+.1f}% ({margin_variance['yoy_sentiment']})\n"
                    
                    response_content += f"\n**💰 Financial Scale**\n" \
                                     f"• Revenue: {format_number(stock_data.revenue, 'cr')}\n" \
                                     f"• Net Income: {format_number(stock_data.net_income, 'cr')}\n\n" \
                                     f"{margin_analysis}\n"
                    
                    if trend_insight:
                        response_content += f"\n{trend_insight}\n"
                    
                    response_content += f"\n💡 **Profit Margin** = Net Income ÷ Revenue"
                
                elif fundamental_query == "growth":
                    growth_analysis = ""
                    if stock_data.revenue_growth:
                        if stock_data.revenue_growth > 15:
                            growth_analysis = "🚀 **High Growth** - Strong revenue expansion"
                        elif stock_data.revenue_growth > 5:
                            growth_analysis = "📈 **Moderate Growth** - Steady expansion"
                        else:
                            growth_analysis = "📉 **Slow Growth** - Limited expansion"
                    
                    response_content = f"🌱 **{stock_data.symbol} - Growth Analysis**\n\n" \
                                    f"**Revenue Growth**: {format_number(stock_data.revenue_growth, is_percentage=True)}\n" \
                                    f"**Earnings Growth**: {format_number(stock_data.earnings_growth, is_percentage=True)}\n" \
                                    f"**Current Revenue**: {format_number(stock_data.revenue, 'cr')}\n" \
                                    f"**P/E Ratio**: {format_number(stock_data.pe_ratio, 'x')}\n\n" \
                                    f"{growth_analysis}\n\n" \
                                    f"💡 **Growth rates** are year-over-year comparisons"
                
                elif fundamental_query == "debt":
                    # Debt/Financial Strength Analysis with Trends
                    debt_variance = calculate_variance_analysis(
                        stock_data.debt_to_equity, 
                        stock_data.debt_to_equity_qoq, 
                        stock_data.debt_to_equity_yoy, 
                        "debt_to_equity", 
                        is_higher_better=False  # Lower debt is better
                    )
                    
                    current_variance = calculate_variance_analysis(
                        stock_data.current_ratio,
                        stock_data.current_ratio_qoq,
                        stock_data.current_ratio_yoy,
                        "current_ratio",
                        is_higher_better=True  # Higher current ratio is better
                    )
                    
                    # Overall financial health assessment
                    financial_health = "Strong"
                    if stock_data.debt_to_equity and stock_data.debt_to_equity > 1.0:
                        financial_health = "Moderate" if stock_data.current_ratio and stock_data.current_ratio > 1.5 else "Weak"
                    elif stock_data.current_ratio and stock_data.current_ratio < 1.0:
                        financial_health = "Weak"
                    
                    trend_summary = ""
                    if debt_variance.get('yoy_sentiment') and current_variance.get('yoy_sentiment'):
                        if debt_variance['yoy_sentiment'] in ['Strong Improvement', 'Moderate Improvement'] and \
                           current_variance['yoy_sentiment'] in ['Strong Growth', 'Moderate Growth']:
                            trend_summary = "📈 **Improving Financial Position** - Both debt and liquidity trending positively"
                        elif debt_variance['yoy_sentiment'] == 'Deteriorating' or \
                             current_variance['yoy_sentiment'] == 'Declining':
                            trend_summary = "⚠️ **Concerning Trends** - Financial metrics showing deterioration"
                        else:
                            trend_summary = "➡️ **Mixed Signals** - Some metrics improving, others stable"
                    
                    response_content = f"💪 **{stock_data.symbol} - Financial Strength Analysis**\n\n" \
                                    f"**🏦 Current Financial Health**: {financial_health}\n\n" \
                                    f"**📊 Debt-to-Equity Ratio**\n" \
                                    f"• Current: {format_number(stock_data.debt_to_equity, 'x')}\n"
                    
                    if debt_variance.get('qoq_change') is not None:
                        response_content += f"• QoQ: {debt_variance['qoq_direction']} {debt_variance['qoq_change']:+.1f}% ({debt_variance['qoq_sentiment']})\n"
                    if debt_variance.get('yoy_change') is not None:
                        response_content += f"• YoY: {debt_variance['yoy_direction']} {debt_variance['yoy_change']:+.1f}% ({debt_variance['yoy_sentiment']})\n"
                    
                    response_content += f"\n**💰 Current Ratio (Liquidity)**\n" \
                                     f"• Current: {format_number(stock_data.current_ratio, 'x')}\n"
                    
                    if current_variance.get('qoq_change') is not None:
                        response_content += f"• QoQ: {current_variance['qoq_direction']} {current_variance['qoq_change']:+.1f}% ({current_variance['qoq_sentiment']})\n"
                    if current_variance.get('yoy_change') is not None:
                        response_content += f"• YoY: {current_variance['yoy_direction']} {current_variance['yoy_change']:+.1f}% ({current_variance['yoy_sentiment']})\n"
                    
                    if trend_summary:
                        response_content += f"\n{trend_summary}\n"
                    
                    response_content += f"\n💡 **Lower debt-to-equity** and **higher current ratio** indicate stronger financial health"
                
                else:
                    # Default fundamental response
                    response_content = f"📊 **{stock_data.symbol} - Key Fundamentals**\n\n" \
                                    f"**P/E Ratio**: {format_number(stock_data.pe_ratio, 'x')}\n" \
                                    f"**EPS**: {currency}{format_number(stock_data.eps)}\n" \
                                    f"**Dividend Yield**: {format_number(stock_data.dividend_yield, is_percentage=True)}\n" \
                                    f"**Profit Margin**: {format_number(stock_data.profit_margin, is_percentage=True)}\n" \
                                    f"**Revenue Growth**: {format_number(stock_data.revenue_growth, is_percentage=True)}\n\n" \
                                    f"💡 Ask about specific metrics like 'TCS PE ratio' or 'Reliance dividend'"
            else:
                response_content = f"❌ Sorry, I couldn't find fundamental data for **{symbol}**. Please check the symbol and try again."
                
        except Exception as e:
            response_content = f"❌ Error fetching fundamental data for **{symbol}**: {str(e)}"
    
    # Help queries
    elif any(word in content for word in ["help", "commands", "what can you do"]):
        response_content = "🇮🇳 **StockChat - Indian Stock Market AI**\n\n" \
                          "🤖 **I can help you with:**\n\n" \
                          "📈 **Stock Prices**: 'Reliance price' or 'What's TCS worth?'\n" \
                          "📊 **Fundamentals**: 'TCS PE ratio', 'Reliance dividend', 'Infosys financials'\n" \
                          "🔍 **Company Search**: 'Tell me about Infosys' or 'HDFC Bank price'\n" \
                          "💡 **Smart Recognition**: Use company names or symbols!\n" \
                          "   • 'Tata Consultancy Services' → TCS\n" \
                          "   • 'HDFC Bank' → HDFCBANK\n" \
                          "   • 'Reliance Industries' → RELIANCE\n\n" \
                          "📋 **Fundamental Queries**:\n" \
                          "   • P/E Ratio: 'TCS PE ratio'\n" \
                          "   • Dividends: 'Reliance dividend yield'\n" \
                          "   • Growth: 'Infosys growth'\n" \
                          "   • Margins: 'HDFC profit margin'\n" \
                          "   • Complete Analysis: 'TCS fundamentals'\n\n" \
                          "**Popular Stocks**: TCS, RELIANCE, INFY, HDFCBANK, ICICIBANK, SBIN, MARUTI, ITC\n\n" \
                          "Try: 'TCS financials', 'Reliance PE ratio', or 'Infosys dividend'"
    
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