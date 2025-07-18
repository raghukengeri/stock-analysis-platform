import asyncio
import logging
from datetime import datetime, timedelta
from typing import Set
from app.services.stock_service import StockService
from app.services.websocket_service import connection_manager

logger = logging.getLogger(__name__)

class PriceUpdater:
    def __init__(self):
        self.update_interval = 30  # Update every 30 seconds
        self.is_running = False
        self.task = None

    async def start(self):
        """Start the price updater background task"""
        if self.is_running:
            return
        
        self.is_running = True
        self.task = asyncio.create_task(self._update_loop())
        logger.info("Price updater started")

    async def stop(self):
        """Stop the price updater background task"""
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Price updater stopped")

    async def _update_loop(self):
        """Main update loop"""
        while self.is_running:
            try:
                # Get all symbols that have active subscribers
                active_symbols = self._get_active_symbols()
                
                if active_symbols:
                    logger.info(f"Updating prices for {len(active_symbols)} symbols: {active_symbols}")
                    
                    # Update prices for all active symbols
                    tasks = [self._update_symbol_price(symbol) for symbol in active_symbols]
                    await asyncio.gather(*tasks, return_exceptions=True)
                
                # Wait before next update
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"Error in price update loop: {e}")
                await asyncio.sleep(5)  # Short delay before retrying

    def _get_active_symbols(self) -> Set[str]:
        """Get all symbols that have active subscribers"""
        return set(connection_manager.symbol_subscribers.keys())

    async def _update_symbol_price(self, symbol: str):
        """Update price for a specific symbol and broadcast to subscribers"""
        try:
            # Fetch latest stock data
            stock_data = await StockService.get_stock_data(symbol)
            
            if stock_data:
                # Broadcast update to all subscribers
                await connection_manager.broadcast_stock_update(
                    symbol, 
                    stock_data.dict()
                )
                logger.debug(f"Updated price for {symbol}: {stock_data.current_price}")
            else:
                logger.warning(f"Failed to fetch data for {symbol}")
                
        except Exception as e:
            logger.error(f"Error updating price for {symbol}: {e}")

# Global price updater instance
price_updater = PriceUpdater()