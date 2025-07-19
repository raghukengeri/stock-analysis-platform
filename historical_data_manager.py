#!/usr/bin/env python3
"""
Historical Data Manager
Command-line tool for fetching and managing historical stock data in MongoDB
"""

import asyncio
import argparse
import sys
from datetime import datetime
from app.core.database import init_db
from app.services.historical_data_service import HistoricalDataService
from app.models.stock import StockPrice, FinancialStatement, BalanceSheet, CashFlow

async def fetch_historical_data(symbol: str, data_type: str = "all"):
    """Fetch historical data for a symbol"""
    
    print(f"🔄 Fetching {data_type} historical data for {symbol}...")
    
    if data_type in ["all", "prices"]:
        success = await HistoricalDataService.fetch_and_store_historical_prices(symbol, period="10y")
        if success:
            print(f"✅ Historical prices stored for {symbol}")
        else:
            print(f"❌ Failed to fetch historical prices for {symbol}")
    
    if data_type in ["all", "financials"]:
        success = await HistoricalDataService.fetch_and_store_financial_statements(symbol)
        if success:
            print(f"✅ Financial statements stored for {symbol}")
        else:
            print(f"❌ Failed to fetch financial statements for {symbol}")
    
    if data_type in ["all", "balance"]:
        success = await HistoricalDataService.fetch_and_store_balance_sheets(symbol)
        if success:
            print(f"✅ Balance sheets stored for {symbol}")
        else:
            print(f"❌ Failed to fetch balance sheets for {symbol}")
    
    if data_type in ["all", "cashflow"]:
        success = await HistoricalDataService.fetch_and_store_cash_flows(symbol)
        if success:
            print(f"✅ Cash flow statements stored for {symbol}")
        else:
            print(f"❌ Failed to fetch cash flows for {symbol}")

async def fetch_multiple_stocks(symbols: list, data_type: str = "all"):
    """Fetch historical data for multiple symbols"""
    
    print(f"🚀 Starting bulk historical data fetch for {len(symbols)} stocks")
    print(f"📊 Data type: {data_type}")
    print("=" * 60)
    
    successful = 0
    failed = 0
    
    for i, symbol in enumerate(symbols, 1):
        print(f"\n[{i}/{len(symbols)}] Processing {symbol}...")
        try:
            await fetch_historical_data(symbol, data_type)
            successful += 1
        except Exception as e:
            print(f"❌ Error processing {symbol}: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 **Bulk Fetch Summary**")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(successful/(successful+failed))*100:.1f}%")

async def show_storage_stats():
    """Show storage statistics"""
    
    print("📊 **MongoDB Historical Data Statistics**")
    print("=" * 50)
    
    # Count documents in each collection
    try:
        price_count = await StockPrice.count()
        financial_count = await FinancialStatement.count()
        balance_count = await BalanceSheet.count()
        cashflow_count = await CashFlow.count()
        
        print(f"📈 Historical Prices: {price_count:,} records")
        print(f"📋 Financial Statements: {financial_count:,} records")
        print(f"⚖️  Balance Sheets: {balance_count:,} records")
        print(f"💰 Cash Flow Statements: {cashflow_count:,} records")
        
        # Show unique symbols with data
        if price_count > 0:
            unique_symbols_with_prices = len(await StockPrice.distinct("symbol"))
            print(f"🏢 Stocks with Price Data: {unique_symbols_with_prices}")
        
        if financial_count > 0:
            unique_symbols_with_financials = len(await FinancialStatement.distinct("symbol"))
            print(f"📊 Stocks with Financial Data: {unique_symbols_with_financials}")
        
        # Show date ranges
        if price_count > 0:
            latest_price = await StockPrice.find().sort([("timestamp", -1)]).limit(1).to_list()
            oldest_price = await StockPrice.find().sort([("timestamp", 1)]).limit(1).to_list()
            
            if latest_price and oldest_price:
                print(f"📅 Price Data Range: {oldest_price[0].date} to {latest_price[0].date}")
        
        print("\n💡 **Data Coverage**:")
        total_unique_symbols = max(
            len(await StockPrice.distinct("symbol")) if price_count > 0 else 0,
            len(await FinancialStatement.distinct("symbol")) if financial_count > 0 else 0
        )
        
        if total_unique_symbols > 0:
            coverage_stats = []
            if price_count > 0:
                price_coverage = len(await StockPrice.distinct("symbol"))
                coverage_stats.append(f"Prices: {price_coverage}/{total_unique_symbols}")
            
            if financial_count > 0:
                financial_coverage = len(await FinancialStatement.distinct("symbol"))
                coverage_stats.append(f"Financials: {financial_coverage}/{total_unique_symbols}")
            
            print("   " + " | ".join(coverage_stats))
        
    except Exception as e:
        print(f"❌ Error getting statistics: {e}")

async def show_sample_data(symbol: str):
    """Show sample stored data for a symbol"""
    
    print(f"🔍 **Sample Data for {symbol.upper()}**")
    print("=" * 50)
    
    # Show recent price data
    recent_prices = await StockPrice.find(
        {"symbol": symbol.upper()}
    ).sort([("timestamp", -1)]).limit(5).to_list()
    
    if recent_prices:
        print("📈 **Recent Price Data (Last 5 days):**")
        for price in recent_prices:
            print(f"   {price.date}: ₹{price.close_price:.2f} (Vol: {price.volume:,})")
    else:
        print("📈 No price data found")
    
    # Show financial statements
    financials = await FinancialStatement.find(
        {"symbol": symbol.upper()}
    ).sort([("period_ending", -1)]).limit(3).to_list()
    
    if financials:
        print("\n📋 **Recent Financial Statements:**")
        for stmt in financials:
            revenue = stmt.total_revenue or stmt.revenue
            print(f"   {stmt.period_string} ({stmt.period_type}): Revenue ₹{revenue/10000000:.0f}cr" if revenue else f"   {stmt.period_string}: No revenue data")
    else:
        print("\n📋 No financial statements found")
    
    # Show balance sheets
    balance_sheets = await BalanceSheet.find(
        {"symbol": symbol.upper()}
    ).sort([("period_ending", -1)]).limit(3).to_list()
    
    if balance_sheets:
        print("\n⚖️  **Recent Balance Sheets:**")
        for bs in balance_sheets:
            assets = bs.total_assets
            print(f"   {bs.period_string}: Assets ₹{assets/10000000:.0f}cr" if assets else f"   {bs.period_string}: No asset data")
    else:
        print("\n⚖️  No balance sheets found")

async def main():
    parser = argparse.ArgumentParser(description='Historical Data Manager for Stock Analysis Platform')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Fetch command
    fetch_parser = subparsers.add_parser('fetch', help='Fetch historical data for stocks')
    fetch_parser.add_argument('symbols', nargs='+', help='Stock symbols to fetch')
    fetch_parser.add_argument('--type', choices=['all', 'prices', 'financials', 'balance', 'cashflow'], 
                            default='all', help='Type of data to fetch')
    
    # Stats command
    subparsers.add_parser('stats', help='Show storage statistics')
    
    # Sample command
    sample_parser = subparsers.add_parser('sample', help='Show sample data for a symbol')
    sample_parser.add_argument('symbol', help='Stock symbol to show sample data for')
    
    # Bulk fetch command
    bulk_parser = subparsers.add_parser('bulk', help='Bulk fetch for NSE top stocks')
    bulk_parser.add_argument('--count', type=int, default=50, help='Number of top stocks to fetch')
    bulk_parser.add_argument('--type', choices=['all', 'prices', 'financials', 'balance', 'cashflow'], 
                           default='all', help='Type of data to fetch')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize database
    try:
        await init_db()
        print("✅ Connected to MongoDB")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        return
    
    try:
        if args.command == 'fetch':
            if len(args.symbols) == 1:
                await fetch_historical_data(args.symbols[0], args.type)
            else:
                await fetch_multiple_stocks(args.symbols, args.type)
        
        elif args.command == 'stats':
            await show_storage_stats()
        
        elif args.command == 'sample':
            await show_sample_data(args.symbol)
        
        elif args.command == 'bulk':
            # Common NSE stocks for bulk fetch
            nse_stocks = [
                'TCS', 'RELIANCE', 'INFY', 'HDFCBANK', 'ICICIBANK', 'SBIN', 'BHARTIARTL',
                'ITC', 'KOTAKBANK', 'LT', 'AXISBANK', 'MARUTI', 'ASIANPAINT', 'NESTLEIND',
                'ULTRACEMCO', 'TITAN', 'BAJFINANCE', 'SUNPHARMA', 'NTPC', 'POWERGRID',
                'TATASTEEL', 'HINDALCO', 'JSWSTEEL', 'INDUSINDBK', 'TECHM', 'DRREDDY',
                'CIPLA', 'BAJAJ-AUTO', 'EICHERMOT', 'BRITANNIA', 'COALINDIA', 'GRASIM',
                'ONGC', 'IOC', 'BPCL', 'HINDUNILVR', 'DABUR', 'GODREJCP', 'ADANIPORTS',
                'ADANIENT', 'WIPRO', 'HCLTECH', 'DIVISLAB', 'BIOCON', 'LUPIN', 'APOLLOHOSP',
                'BAJAJFINSV', 'HDFCLIFE', 'SBILIFE', 'ICICIPRULI'
            ]
            
            selected_stocks = nse_stocks[:args.count]
            await fetch_multiple_stocks(selected_stocks, args.type)
    
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())