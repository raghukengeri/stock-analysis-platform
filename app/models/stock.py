from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from beanie import Document
from pydantic import BaseModel, Field

class Stock(Document):
    symbol: str = Field(..., index=True, unique=True)
    name: str
    exchange: str = Field(default="NSE")
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    current_price: Optional[float] = None
    price_change: Optional[float] = None
    price_change_percent: Optional[float] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
    
    # Financial metrics
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    roe: Optional[float] = None
    debt_to_equity: Optional[float] = None
    
    class Settings:
        collection = "stocks"
        indexes = [
            "symbol",
            "exchange",
            "sector",
        ]

class StockPrice(Document):
    symbol: str = Field(..., index=True)
    timestamp: datetime = Field(..., index=True)
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: int
    
    class Settings:
        collection = "stock_prices"
        indexes = [
            [("symbol", 1), ("timestamp", -1)],
        ]

class StockResponse(BaseModel):
    symbol: str
    name: str
    exchange: str
    current_price: Optional[Decimal]
    price_change: Optional[Decimal]
    price_change_percent: Optional[Decimal]
    volume: Optional[int]
    market_cap: Optional[Decimal]
    pe_ratio: Optional[Decimal]
    last_updated: datetime

class StockPriceResponse(BaseModel):
    symbol: str
    timestamp: datetime
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: int