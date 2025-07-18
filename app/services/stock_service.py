from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
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
                # Update or create stock in database
                if stock:
                    await stock.update({"$set": fresh_data})
                else:
                    stock = Stock(**fresh_data)
                    await stock.save()
                
                return StockResponse(**fresh_data)
            
            return None
            
        except Exception as e:
            print(f"Error fetching stock data for {symbol}: {e}")
            return None
    
    @staticmethod
    async def _fetch_yahoo_finance_data(symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch data from Yahoo Finance"""
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            ticker_data = await loop.run_in_executor(
                None, 
                lambda: yf.Ticker(f"{symbol}.NS" if not symbol.endswith('.NS') else symbol)
            )
            
            info = await loop.run_in_executor(None, lambda: ticker_data.info)
            hist = await loop.run_in_executor(
                None, 
                lambda: ticker_data.history(period="2d")
            )
            
            if hist.empty:
                return None
            
            latest = hist.iloc[-1]
            previous = hist.iloc[-2] if len(hist) > 1 else latest
            
            current_price = Decimal(str(latest['Close']))
            previous_price = Decimal(str(previous['Close']))
            price_change = current_price - previous_price
            price_change_percent = (price_change / previous_price) * 100 if previous_price > 0 else Decimal('0')
            
            return {
                "symbol": symbol.upper(),
                "name": info.get('longName', symbol),
                "exchange": "NSE" if symbol.endswith('.NS') else "NASDAQ",
                "sector": info.get('sector'),
                "industry": info.get('industry'),
                "current_price": current_price,
                "price_change": price_change,
                "price_change_percent": price_change_percent,
                "market_cap": Decimal(str(info.get('marketCap', 0))) if info.get('marketCap') else None,
                "pe_ratio": Decimal(str(info.get('trailingPE', 0))) if info.get('trailingPE') else None,
                "pb_ratio": Decimal(str(info.get('priceToBook', 0))) if info.get('priceToBook') else None,
                "dividend_yield": Decimal(str(info.get('dividendYield', 0))) if info.get('dividendYield') else None,
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