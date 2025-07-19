#!/usr/bin/env python3
"""
MongoDB Storage Verification Script
Verifies that variance analysis data is being properly stored in MongoDB
"""

import asyncio
import sys
from datetime import datetime
from app.models.stock import Stock
from app.core.database import init_db

async def verify_stock_data_storage():
    """Verify what stock data is stored in MongoDB"""
    
    print("🔍 MongoDB Storage Verification")
    print("=" * 50)
    
    try:
        # Initialize database connection
        await init_db()
        print("✅ Connected to MongoDB")
        
        # Get sample of stored stocks
        stocks = await Stock.find().limit(5).to_list()
        
        if not stocks:
            print("❌ No stocks found in MongoDB")
            return
        
        print(f"📊 Found {len(stocks)} stocks in database. Showing sample:")
        print()
        
        for stock in stocks:
            print(f"🏢 **{stock.symbol}** - {stock.name}")
            print(f"   Exchange: {stock.exchange}")
            print(f"   Last Updated: {stock.last_updated}")
            print(f"   Current Price: ₹{stock.current_price}" if stock.current_price else "   Current Price: N/A")
            
            # Check if variance data is present
            variance_fields = [
                'pe_ratio_qoq', 'pe_ratio_yoy',
                'current_ratio_qoq', 'current_ratio_yoy', 
                'debt_to_equity_qoq', 'debt_to_equity_yoy',
                'profit_margin_qoq', 'profit_margin_yoy'
            ]
            
            variance_present = []
            for field in variance_fields:
                if hasattr(stock, field) and getattr(stock, field) is not None:
                    variance_present.append(field)
            
            if variance_present:
                print(f"   ✅ Variance Data: {len(variance_present)}/{len(variance_fields)} fields populated")
                for field in variance_present[:3]:  # Show first 3
                    value = getattr(stock, field)
                    print(f"     • {field}: {value}")
                if len(variance_present) > 3:
                    print(f"     • ... and {len(variance_present) - 3} more fields")
            else:
                print(f"   ⚠️  No variance data found")
            
            # Check fundamental data
            fundamental_fields = ['pe_ratio', 'pb_ratio', 'eps', 'profit_margin', 'revenue', 'debt_to_equity']
            fundamental_present = sum(1 for field in fundamental_fields 
                                   if hasattr(stock, field) and getattr(stock, field) is not None)
            
            print(f"   📈 Fundamental Data: {fundamental_present}/{len(fundamental_fields)} fields populated")
            print()
        
        # Storage statistics
        total_stocks = await Stock.count()
        recent_stocks = await Stock.find(
            {"last_updated": {"$gte": datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)}}
        ).count()
        
        print("📊 **Storage Statistics**")
        print(f"   Total Stocks: {total_stocks}")
        print(f"   Updated Today: {recent_stocks}")
        print(f"   Sample Showing: {len(stocks)}")
        
        # Check for variance data across all stocks
        stocks_with_variance = await Stock.find(
            {"$or": [
                {"pe_ratio_qoq": {"$ne": None}},
                {"current_ratio_qoq": {"$ne": None}},
                {"debt_to_equity_qoq": {"$ne": None}},
                {"profit_margin_qoq": {"$ne": None}}
            ]}
        ).count()
        
        print(f"   Stocks with Variance Data: {stocks_with_variance}")
        
        if stocks_with_variance > 0:
            percentage = (stocks_with_variance / total_stocks) * 100 if total_stocks > 0 else 0
            print(f"   Variance Coverage: {percentage:.1f}%")
            print("   ✅ Variance analysis data is being stored!")
        else:
            print("   ⚠️  No variance data found in any stocks")
            print("   💡 Try fetching some stock data to populate variance fields")
        
    except Exception as e:
        print(f"❌ Error connecting to MongoDB: {e}")
        print("💡 Make sure MongoDB is running and connection settings are correct")

async def main():
    """Main function"""
    await verify_stock_data_storage()

if __name__ == "__main__":
    asyncio.run(main())