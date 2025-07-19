#!/usr/bin/env python3
"""
Simplified backend runner for development
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import yfinance as yf
import asyncio
from datetime import datetime, timedelta
import random

app = FastAPI(
    title="StockChat Backend",
    description="Simplified backend for StockChat development",
    version="1.0.0",
    docs_url="/docs"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# Mock data for development
MOCK_TRENDING_STOCKS = [
    {"symbol": "AAPL", "name": "Apple Inc.", "current_price": 185.23, "price_change": 2.45, "price_change_percent": 1.34},
    {"symbol": "TSLA", "name": "Tesla Inc.", "current_price": 242.67, "price_change": -5.12, "price_change_percent": -2.07},
    {"symbol": "GOOGL", "name": "Alphabet Inc.", "current_price": 134.56, "price_change": 1.78, "price_change_percent": 1.34},
    {"symbol": "MSFT", "name": "Microsoft Corp.", "current_price": 378.91, "price_change": 4.23, "price_change_percent": 1.13},
    {"symbol": "NVDA", "name": "NVIDIA Corp.", "current_price": 456.78, "price_change": 12.34, "price_change_percent": 2.78},
    {"symbol": "AMZN", "name": "Amazon.com Inc.", "current_price": 156.34, "price_change": -2.45, "price_change_percent": -1.54},
]

@app.get("/")
async def root():
    return {
        "message": "StockChat Backend API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/stocks/trending")
async def get_trending_stocks():
    """Get trending stocks"""
    # Add some random variation to prices
    trending = []
    for stock in MOCK_TRENDING_STOCKS:
        stock_copy = stock.copy()
        # Add small random variation
        variation = random.uniform(-0.5, 0.5)
        stock_copy["current_price"] += variation
        stock_copy["price_change"] += variation * 0.5
        trending.append(stock_copy)
    
    return {"trending": trending}

@app.get("/api/v1/stocks/{symbol}")
async def get_stock_data(symbol: str):
    """Get stock data for a specific symbol"""
    try:
        # Try to get real data from yfinance
        ticker = yf.Ticker(symbol.upper())
        info = ticker.info
        hist = ticker.history(period="1d")
        
        if not hist.empty:
            current_price = float(hist['Close'].iloc[-1])
            prev_close = float(info.get('previousClose', current_price))
            price_change = current_price - prev_close
            price_change_percent = (price_change / prev_close) * 100 if prev_close > 0 else 0
            
            return {
                "symbol": symbol.upper(),
                "name": info.get('longName', f"{symbol.upper()} Inc."),
                "current_price": current_price,
                "price_change": price_change,
                "price_change_percent": price_change_percent,
                "volume": int(info.get('volume', 0)),
                "market_cap": info.get('marketCap'),
                "day_high": float(hist['High'].iloc[-1]),
                "day_low": float(hist['Low'].iloc[-1]),
                "last_updated": datetime.now().isoformat()
            }
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
    
    # Fallback to mock data
    mock_stock = next((s for s in MOCK_TRENDING_STOCKS if s["symbol"] == symbol.upper()), None)
    if mock_stock:
        result = mock_stock.copy()
        result["volume"] = random.randint(1000000, 10000000)
        result["market_cap"] = random.randint(100000000000, 3000000000000)
        result["day_high"] = result["current_price"] + random.uniform(1, 5)
        result["day_low"] = result["current_price"] - random.uniform(1, 5)
        result["last_updated"] = datetime.now().isoformat()
        return result
    
    # Return generic mock data for unknown symbols
    return {
        "symbol": symbol.upper(),
        "name": f"{symbol.upper()} Corporation",
        "current_price": round(random.uniform(50, 300), 2),
        "price_change": round(random.uniform(-10, 10), 2),
        "price_change_percent": round(random.uniform(-5, 5), 2),
        "volume": random.randint(1000000, 50000000),
        "market_cap": random.randint(10000000000, 2000000000000),
        "day_high": 0,
        "day_low": 0,
        "last_updated": datetime.now().isoformat()
    }

@app.get("/api/v1/stocks/search")
async def search_stocks(q: str):
    """Search for stocks"""
    query = q.lower()
    results = []
    
    # Search in trending stocks first
    for stock in MOCK_TRENDING_STOCKS:
        if query in stock["symbol"].lower() or query in stock["name"].lower():
            results.append(stock)
    
    # Add some additional mock results
    if "apple" in query or "aapl" in query:
        results.append(MOCK_TRENDING_STOCKS[0])
    elif "tesla" in query or "tsla" in query:
        results.append(MOCK_TRENDING_STOCKS[1])
    
    return {"results": results[:10]}

@app.post("/api/v1/chat/send")
async def send_message(message: dict):
    """Send a chat message and get AI response"""
    content = message.get("content", "")
    
    # Simple mock AI response
    responses = [
        f"Based on your query about '{content}', here's what I found:",
        f"Let me analyze '{content}' for you.",
        f"Looking at the market data for your query: '{content}'",
        f"Here's my analysis of '{content}':"
    ]
    
    # Simulate processing delay
    await asyncio.sleep(1)
    
    return {
        "id": f"msg_{datetime.now().timestamp()}",
        "content": f"{random.choice(responses)} This is a simulated AI response for development purposes. The stock analysis features will be implemented when connected to the full backend.",
        "message_type": "assistant",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    """Get chat history for a session"""
    return {"messages": []}

if __name__ == "__main__":
    print("🚀 Starting StockChat Backend...")
    print("📊 Backend running at: http://localhost:8000")
    print("📖 API Docs available at: http://localhost:8000/docs")
    print("🔄 CORS enabled for: http://localhost:3000")
    
    uvicorn.run(
        "run_backend:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )