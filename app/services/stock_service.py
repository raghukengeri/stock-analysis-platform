from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import yfinance as yf
import asyncio
from app.models.stock import Stock, StockPrice, StockResponse, StockPriceResponse

class StockService:
    @staticmethod
    async def get_stock_data(symbol: str) -> Optional[StockResponse]:
        """Get stock data for a symbol"""
        try:
            # First check if we have recent data in database
            stock = await Stock.find_one({"symbol": symbol.upper()})
            
            if stock and stock.last_updated > datetime.utcnow() - timedelta(minutes=5):
                return StockResponse(
                    symbol=stock.symbol,
                    name=stock.name,
                    exchange=stock.exchange,
                    current_price=stock.current_price,
                    price_change=stock.price_change,
                    price_change_percent=stock.price_change_percent,
                    market_cap=stock.market_cap,
                    pe_ratio=stock.pe_ratio,
                    last_updated=stock.last_updated
                )
            
            # Fetch fresh data from Yahoo Finance
            fresh_data = await StockService._fetch_yahoo_finance_data(symbol)
            if fresh_data:
                # For now, return data without saving to avoid type issues
                return StockResponse(**fresh_data)
            
            return None
            
        except Exception as e:
            print(f"Error fetching stock data for {symbol}: {e}")
            return None
    
    @staticmethod
    async def _fetch_yahoo_finance_data(symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch data from Yahoo Finance"""
        try:
            # Determine the correct ticker symbol - prioritize Indian stocks
            # Indian stocks need .NS or .BO suffix for NSE/BSE
            indian_stocks = [
                'RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'BHARTIARTL', 'ITC', 'KOTAKBANK',
                'ICICIBANK', 'SBIN', 'AXISBANK', 'INDUSINDBK', 'BAJFINANCE', 'MARUTI',
                'TATAMOTOR', 'M&M', 'BAJAJ-AUTO', 'EICHERMOT', 'SUNPHARMA', 'DRREDDY',
                'CIPLA', 'BIOCON', 'LUPIN', 'AUROPHARMA', 'HINDUNILVR', 'NESTLEIND',
                'BRITANNIA', 'DABUR', 'GODREJCP', 'TATASTEEL', 'HINDALCO', 'JSWSTEEL',
                'SAILSTEEL', 'VEDL', 'ONGC', 'BPCL', 'IOCL', 'GAIL', 'NTPC', 'POWERGRID',
                'LT', 'ADANIPORTS', 'ULTRACEMCO', 'AMBUJACEM', 'ACC', 'SHREECEM',
                'ASIANPAINT', 'TITAN', 'BAJAJFINSV', 'HDFCLIFE', 'SBILIFE', 'WIPRO',
                'HCLTECH', 'TECHM', 'LTI', 'LTTS'
            ]
            us_stocks = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'META', 'NFLX', 'NVDA', 'AMD', 'INTC']
            
            # For Indian market focus - prioritize NSE (.NS) over ADRs
            if symbol.upper() in us_stocks:
                # These are US stocks, use as-is
                ticker_symbol = symbol.upper()
                exchange = "NASDAQ"
            else:
                # For Indian stocks, try NSE first
                ticker_symbol = f"{symbol.upper()}.NS"
                exchange = "NSE (India)"
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            ticker_data = await loop.run_in_executor(
                None, 
                lambda: yf.Ticker(ticker_symbol)
            )
            
            info = await loop.run_in_executor(None, lambda: ticker_data.info)
            hist = await loop.run_in_executor(
                None, 
                lambda: ticker_data.history(period="2d")
            )
            
            # If no data found, try different variants
            if hist.empty:
                # Try different exchanges and suffixes systematically
                variants_to_try = []
                if ticker_symbol.endswith('.NS'):
                    # Try without suffix (for ADRs), BSE (.BO)
                    variants_to_try = [
                        symbol.upper(),  # US ADR version
                        f"{symbol.upper()}.BO",  # BSE
                    ]
                else:
                    # Try with NSE and BSE suffixes
                    variants_to_try = [
                        f"{symbol.upper()}.NS",  # NSE
                        f"{symbol.upper()}.BO",  # BSE
                    ]
                
                for variant in variants_to_try:
                    try:
                        ticker_data = await loop.run_in_executor(
                            None, 
                            lambda v=variant: yf.Ticker(v)
                        )
                        info = await loop.run_in_executor(None, lambda: ticker_data.info)
                        hist = await loop.run_in_executor(
                            None, 
                            lambda: ticker_data.history(period="2d")
                        )
                        
                        if not hist.empty:
                            ticker_symbol = variant
                            if variant.endswith('.NS'):
                                exchange = "NSE (India)"
                            elif variant.endswith('.BO'):
                                exchange = "BSE (India)"
                            else:
                                exchange = "NYSE/NASDAQ (ADR)"  # Clearly indicate it's an ADR
                            break
                    except:
                        continue
            
            if hist.empty:
                return None
            
            latest = hist.iloc[-1]
            previous = hist.iloc[-2] if len(hist) > 1 else latest
            
            current_price = float(latest['Close'])
            previous_price = float(previous['Close'])
            price_change = current_price - previous_price
            price_change_percent = (price_change / previous_price) * 100 if previous_price > 0 else 0.0
            
            return {
                "symbol": symbol.upper(),
                "name": info.get('longName', symbol),
                "exchange": exchange,
                "sector": info.get('sector'),
                "industry": info.get('industry'),
                "current_price": current_price,
                "price_change": price_change,
                "price_change_percent": price_change_percent,
                "market_cap": float(info.get('marketCap', 0)) if info.get('marketCap') else None,
                "pe_ratio": float(info.get('trailingPE', 0)) if info.get('trailingPE') else None,
                "pb_ratio": float(info.get('priceToBook', 0)) if info.get('priceToBook') else None,
                "dividend_yield": float(info.get('dividendYield', 0)) if info.get('dividendYield') else None,
                "last_updated": datetime.utcnow()
            }
            
        except Exception as e:
            print(f"Error fetching Yahoo Finance data for {symbol}: {e}")
            return None
    
    @staticmethod
    async def search_stocks(query: str, limit: int = 10) -> List[StockResponse]:
        """Search for stocks by symbol or name"""
        try:
            stocks = await Stock.find(
                {
                    "$or": [
                        {"symbol": {"$regex": query, "$options": "i"}},
                        {"name": {"$regex": query, "$options": "i"}}
                    ]
                }
            ).limit(limit).to_list()
            
            return [
                StockResponse(
                    symbol=stock.symbol,
                    name=stock.name,
                    exchange=stock.exchange,
                    current_price=stock.current_price,
                    price_change=stock.price_change,
                    price_change_percent=stock.price_change_percent,
                    market_cap=stock.market_cap,
                    pe_ratio=stock.pe_ratio,
                    last_updated=stock.last_updated
                )
                for stock in stocks
            ]
            
        except Exception as e:
            print(f"Error searching stocks: {e}")
            return []
    
    @staticmethod
    async def get_trending_stocks(limit: int = 10) -> List[StockResponse]:
        """Get trending stocks (most recently updated)"""
        try:
            stocks = await Stock.find(
                {"is_active": True}
            ).sort([("last_updated", -1)]).limit(limit).to_list()
            
            return [
                StockResponse(
                    symbol=stock.symbol,
                    name=stock.name,
                    exchange=stock.exchange,
                    current_price=stock.current_price,
                    price_change=stock.price_change,
                    price_change_percent=stock.price_change_percent,
                    market_cap=stock.market_cap,
                    pe_ratio=stock.pe_ratio,
                    last_updated=stock.last_updated
                )
                for stock in stocks
            ]
            
        except Exception as e:
            print(f"Error getting trending stocks: {e}")
            return []