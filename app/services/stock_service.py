from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import yfinance as yf
import asyncio
from app.models.stock import Stock, StockPrice, StockResponse, StockPriceResponse, FinancialStatement, BalanceSheet, CashFlow
from app.services.historical_data_service import HistoricalDataService

class StockService:
    @staticmethod
    async def get_stock_data(symbol: str) -> Optional[StockResponse]:
        """Get stock data for a symbol"""
        try:
            # First check if we have recent data in database
            stock = await Stock.find_one({"symbol": symbol.upper()})
            
            if stock and stock.last_updated > datetime.utcnow() - timedelta(minutes=5):
                # Create response with all available fields from database
                stock_dict = stock.dict()
                response_fields = {}
                for field_name in StockResponse.__fields__:
                    response_fields[field_name] = stock_dict.get(field_name)
                return StockResponse(**response_fields)
            
            # Fetch fresh data from Yahoo Finance
            fresh_data = await StockService._fetch_yahoo_finance_data(symbol)
            if fresh_data:
                # Save/Update the comprehensive data in MongoDB
                try:
                    # Prepare data for MongoDB storage
                    stock_data_for_db = {}
                    for field_name in Stock.__fields__:
                        if field_name in fresh_data:
                            stock_data_for_db[field_name] = fresh_data[field_name]
                    
                    # Update or create stock record in MongoDB
                    await Stock.find_one_and_update(
                        {"symbol": symbol.upper()},
                        {"$set": stock_data_for_db},
                        upsert=True
                    )
                    print(f"✅ Saved enhanced stock data for {symbol} to MongoDB with variance analysis")
                    
                except Exception as e:
                    print(f"⚠️ Warning: Failed to save stock data to MongoDB: {e}")
                    # Continue anyway - we can still return the data even if save fails
                
                # Optionally fetch and store comprehensive historical data
                # This can be done asynchronously in the background
                try:
                    # Check if we have recent historical data
                    recent_price_data = await StockPrice.find(
                        {"symbol": symbol.upper()}
                    ).sort([("timestamp", -1)]).limit(1).to_list()
                    
                    # If no recent price data, fetch historical data
                    if not recent_price_data or \
                       (recent_price_data[0].timestamp < datetime.utcnow() - timedelta(days=7)):
                        print(f"🔄 Fetching historical data for {symbol} in background...")
                        # Note: In production, this should be done asynchronously
                        # For now, we'll just trigger it but not wait
                        asyncio.create_task(
                            HistoricalDataService.fetch_and_store_complete_historical_data(symbol)
                        )
                        
                except Exception as e:
                    print(f"⚠️ Warning: Failed to trigger historical data fetch: {e}")
                
                # Create StockResponse with all available fields
                response_fields = {}
                for field_name in StockResponse.__fields__:
                    response_fields[field_name] = fresh_data.get(field_name)
                return StockResponse(**response_fields)
            
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
                '360ONE', '3MINDIA', 'RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'HDFCAMC', 'BHARTIARTL', 'ITC', 'KOTAKBANK',
                'ICICIBANK', 'ICICIGI', 'ICICIPRULI', 'JIOFIN', 'SBIN', 'AXISBANK', 'INDUSINDBK', 'BAJFINANCE', 'MARUTI',
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
            
            # Get additional fundamental data including historical
            financials = await loop.run_in_executor(None, lambda: ticker_data.financials)
            balance_sheet = await loop.run_in_executor(None, lambda: ticker_data.balance_sheet)
            cash_flow = await loop.run_in_executor(None, lambda: ticker_data.cashflow)
            quarterly_financials = await loop.run_in_executor(None, lambda: ticker_data.quarterly_financials)
            quarterly_balance_sheet = await loop.run_in_executor(None, lambda: ticker_data.quarterly_balance_sheet)
            
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
            
            # Helper function to safely extract numeric values
            def safe_float(value):
                try:
                    if value is None or value == 'N/A' or str(value).lower() == 'nan':
                        return None
                    return float(value)
                except (ValueError, TypeError):
                    return None
            
            # Helper function to convert currency values to crores (for Indian context)
            def to_crores(value):
                if value is None:
                    return None
                return value / 10000000  # Convert to crores (1 crore = 10 million)
            
            # Helper function to calculate historical metrics
            def calculate_historical_metrics(current_val, df, metric_name, periods_back=1):
                """Calculate historical values for QoQ and YoY comparison"""
                try:
                    if df is None or df.empty or len(df.columns) < periods_back + 1:
                        return None
                    
                    # Get the value from periods_back columns ago
                    if len(df.columns) >= periods_back + 1:
                        historical_col = df.columns[periods_back]  # 1 = previous quarter, 4 = previous year
                        if metric_name in df.index:
                            historical_value = df.loc[metric_name, historical_col]
                            return safe_float(historical_value)
                    return None
                except:
                    return None
                    
            # Calculate derived historical metrics
            def calculate_historical_ratios():
                """Calculate historical PE, current ratio, etc. from raw data"""
                historical_metrics = {}
                
                try:
                    # Historical P/E calculation (if we have EPS data)
                    if quarterly_financials is not None and not quarterly_financials.empty:
                        # Get historical revenue and net income for margins
                        historical_metrics['revenue_qoq'] = calculate_historical_metrics(
                            None, quarterly_financials, 'Total Revenue', 1)
                        historical_metrics['revenue_yoy'] = calculate_historical_metrics(
                            None, quarterly_financials, 'Total Revenue', 4)
                        
                        # Calculate historical profit margins
                        current_revenue = safe_float(info.get('totalRevenue'))
                        current_net_income = safe_float(info.get('netIncomeToCommon'))
                        
                        if current_revenue and current_net_income:
                            current_margin = (current_net_income / current_revenue) * 100
                            
                            # QoQ margin
                            qoq_revenue = historical_metrics.get('revenue_qoq')
                            qoq_net_income = calculate_historical_metrics(
                                None, quarterly_financials, 'Net Income', 1)
                            if qoq_revenue and qoq_net_income:
                                historical_metrics['profit_margin_qoq'] = (qoq_net_income / qoq_revenue) * 100
                            
                            # YoY margin  
                            yoy_revenue = historical_metrics.get('revenue_yoy')
                            yoy_net_income = calculate_historical_metrics(
                                None, quarterly_financials, 'Net Income', 4)
                            if yoy_revenue and yoy_net_income:
                                historical_metrics['profit_margin_yoy'] = (yoy_net_income / yoy_revenue) * 100
                    
                    # Historical balance sheet ratios
                    if quarterly_balance_sheet is not None and not quarterly_balance_sheet.empty:
                        # Current Ratio = Current Assets / Current Liabilities
                        current_assets_qoq = calculate_historical_metrics(
                            None, quarterly_balance_sheet, 'Current Assets', 1)
                        current_liabilities_qoq = calculate_historical_metrics(
                            None, quarterly_balance_sheet, 'Current Liabilities', 1)
                        
                        if current_assets_qoq and current_liabilities_qoq:
                            historical_metrics['current_ratio_qoq'] = current_assets_qoq / current_liabilities_qoq
                        
                        # YoY Current Ratio
                        current_assets_yoy = calculate_historical_metrics(
                            None, quarterly_balance_sheet, 'Current Assets', 4)
                        current_liabilities_yoy = calculate_historical_metrics(
                            None, quarterly_balance_sheet, 'Current Liabilities', 4)
                        
                        if current_assets_yoy and current_liabilities_yoy:
                            historical_metrics['current_ratio_yoy'] = current_assets_yoy / current_liabilities_yoy
                        
                        # Debt to Equity historical
                        total_debt_qoq = calculate_historical_metrics(
                            None, quarterly_balance_sheet, 'Total Debt', 1)
                        total_equity_qoq = calculate_historical_metrics(
                            None, quarterly_balance_sheet, 'Total Equity Gross Minority Interest', 1)
                        
                        if total_debt_qoq and total_equity_qoq:
                            historical_metrics['debt_to_equity_qoq'] = total_debt_qoq / total_equity_qoq
                        
                        # YoY Debt to Equity
                        total_debt_yoy = calculate_historical_metrics(
                            None, quarterly_balance_sheet, 'Total Debt', 4)
                        total_equity_yoy = calculate_historical_metrics(
                            None, quarterly_balance_sheet, 'Total Equity Gross Minority Interest', 4)
                        
                        if total_debt_yoy and total_equity_yoy:
                            historical_metrics['debt_to_equity_yoy'] = total_debt_yoy / total_equity_yoy
                            
                except Exception as e:
                    print(f"Error calculating historical metrics: {e}")
                
                return historical_metrics
            
            # Get historical metrics
            historical_data = calculate_historical_ratios()
            
            # Extract comprehensive fundamental data
            fundamentals_data = {
                "symbol": symbol.upper(),
                "name": info.get('longName', symbol),
                "exchange": exchange,
                "sector": info.get('sector'),
                "industry": info.get('industry'),
                
                # Price data
                "current_price": current_price,
                "price_change": price_change,
                "price_change_percent": price_change_percent,
                "volume": int(latest.get('Volume', 0)) if latest.get('Volume') else None,
                
                # Basic valuation metrics
                "market_cap": safe_float(info.get('marketCap')),
                "pe_ratio": safe_float(info.get('trailingPE')),
                "pb_ratio": safe_float(info.get('priceToBook')),
                "price_to_sales": safe_float(info.get('priceToSalesTrailing12Months')),
                "price_to_earnings_growth": safe_float(info.get('pegRatio')),
                
                # Profitability metrics
                "eps": safe_float(info.get('trailingEps')),
                "operating_margin": safe_float(info.get('operatingMargins')) * 100 if safe_float(info.get('operatingMargins')) else None,
                "profit_margin": safe_float(info.get('profitMargins')) * 100 if safe_float(info.get('profitMargins')) else None,
                "book_value": safe_float(info.get('bookValue')),
                
                # Financial strength metrics
                "current_ratio": safe_float(info.get('currentRatio')),
                "debt_to_equity": safe_float(info.get('debtToEquity')),
                "beta": safe_float(info.get('beta')),
                
                # Growth metrics
                "revenue_growth": safe_float(info.get('revenueGrowth')) * 100 if safe_float(info.get('revenueGrowth')) else None,
                "earnings_growth": safe_float(info.get('earningsGrowth')) * 100 if safe_float(info.get('earningsGrowth')) else None,
                
                # Cash flow and enterprise value
                "enterprise_value": safe_float(info.get('enterpriseValue')),
                "ebitda": to_crores(safe_float(info.get('ebitda'))),
                "free_cash_flow": to_crores(safe_float(info.get('freeCashflow'))),
                
                # Revenue and profit (in crores)
                "revenue": to_crores(safe_float(info.get('totalRevenue'))),
                "net_income": to_crores(safe_float(info.get('netIncomeToCommon'))),
                
                # Dividend metrics
                "dividend_yield": safe_float(info.get('dividendYield')) * 100 if safe_float(info.get('dividendYield')) else None,
                "dividend_per_share": safe_float(info.get('dividendRate')),
                "payout_ratio": safe_float(info.get('payoutRatio')) * 100 if safe_float(info.get('payoutRatio')) else None,
                
                # Historical data for trend analysis
                "pe_ratio_qoq": historical_data.get('pe_ratio_qoq'),
                "current_ratio_qoq": historical_data.get('current_ratio_qoq'),
                "debt_to_equity_qoq": historical_data.get('debt_to_equity_qoq'),
                "profit_margin_qoq": historical_data.get('profit_margin_qoq'),
                "revenue_qoq": to_crores(historical_data.get('revenue_qoq')),
                "eps_qoq": historical_data.get('eps_qoq'),
                
                "pe_ratio_yoy": historical_data.get('pe_ratio_yoy'),
                "current_ratio_yoy": historical_data.get('current_ratio_yoy'),
                "debt_to_equity_yoy": historical_data.get('debt_to_equity_yoy'),
                "profit_margin_yoy": historical_data.get('profit_margin_yoy'),
                "revenue_yoy": to_crores(historical_data.get('revenue_yoy')),
                "eps_yoy": historical_data.get('eps_yoy'),
                
                "last_updated": datetime.utcnow()
            }
            
            return fundamentals_data
            
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