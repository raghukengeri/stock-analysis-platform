from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.models.user import User
from app.models.stock import StockResponse
from app.services.stock_service import StockService
from app.api.deps import get_current_active_user

router = APIRouter()

@router.get("/search", response_model=List[StockResponse])
async def search_stocks(
    q: str = Query(..., description="Search query (symbol or company name)"),
    limit: int = Query(10, ge=1, le=50, description="Number of results to return"),
    current_user: User = Depends(get_current_active_user)
):
    """Search for stocks by symbol or company name"""
    return await StockService.search_stocks(q, limit)

@router.get("/trending", response_model=List[StockResponse])
async def get_trending_stocks(
    limit: int = Query(10, ge=1, le=50, description="Number of results to return"),
    current_user: User = Depends(get_current_active_user)
):
    """Get trending stocks"""
    return await StockService.get_trending_stocks(limit)

@router.get("/{symbol}", response_model=StockResponse)
async def get_stock(
    symbol: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed information about a specific stock"""
    stock_data = await StockService.get_stock_data(symbol)
    
    if not stock_data:
        raise HTTPException(
            status_code=404,
            detail=f"Stock with symbol '{symbol}' not found"
        )
    
    return stock_data

@router.post("/watchlist/{symbol}")
async def add_to_watchlist(
    symbol: str,
    current_user: User = Depends(get_current_active_user)
):
    """Add a stock to user's watchlist"""
    # Verify stock exists
    stock_data = await StockService.get_stock_data(symbol)
    if not stock_data:
        raise HTTPException(
            status_code=404,
            detail=f"Stock with symbol '{symbol}' not found"
        )
    
    # Add to watchlist if not already present
    if symbol.upper() not in current_user.watchlist:
        current_user.watchlist.append(symbol.upper())
        await current_user.save()
    
    return {"message": f"Added {symbol} to watchlist"}

@router.delete("/watchlist/{symbol}")
async def remove_from_watchlist(
    symbol: str,
    current_user: User = Depends(get_current_active_user)
):
    """Remove a stock from user's watchlist"""
    if symbol.upper() in current_user.watchlist:
        current_user.watchlist.remove(symbol.upper())
        await current_user.save()
    
    return {"message": f"Removed {symbol} from watchlist"}

@router.get("/watchlist/my", response_model=List[StockResponse])
async def get_my_watchlist(
    current_user: User = Depends(get_current_active_user)
):
    """Get user's watchlist with current stock data"""
    watchlist_data = []
    
    for symbol in current_user.watchlist:
        stock_data = await StockService.get_stock_data(symbol)
        if stock_data:
            watchlist_data.append(stock_data)
    
    return watchlist_data