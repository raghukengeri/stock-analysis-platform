"""
Historical Data Service
Comprehensive service for fetching and storing historical OHLC data and financial statements
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import asyncio
from app.models.stock import StockPrice, FinancialStatement, BalanceSheet, CashFlow

class HistoricalDataService:
    
    @staticmethod
    async def fetch_and_store_historical_prices(symbol: str, period: str = "10y") -> bool:
        """
        Fetch and store historical OHLC data
        
        Args:
            symbol: Stock symbol
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        """
        try:
            # Determine ticker symbol for Indian stocks
            ticker_symbol = f"{symbol.upper()}.NS"
            
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(None, lambda: yf.Ticker(ticker_symbol))
            
            # Get historical data
            hist = await loop.run_in_executor(
                None, 
                lambda: ticker.history(period=period)
            )
            
            if hist.empty:
                # Try without .NS suffix (for ADRs)
                ticker_symbol = symbol.upper()
                ticker = await loop.run_in_executor(None, lambda: yf.Ticker(ticker_symbol))
                hist = await loop.run_in_executor(
                    None, 
                    lambda: ticker.history(period=period)
                )
            
            if hist.empty:
                print(f"❌ No historical data found for {symbol}")
                return False
            
            # Convert DataFrame to list of documents
            price_documents = []
            for date, row in hist.iterrows():
                price_doc = {
                    "symbol": symbol.upper(),
                    "timestamp": date.to_pydatetime(),
                    "date": date.strftime("%Y-%m-%d"),
                    "open_price": float(row['Open']),
                    "high_price": float(row['High']),
                    "low_price": float(row['Low']),
                    "close_price": float(row['Close']),
                    "adj_close_price": float(row.get('Adj Close', row['Close'])),
                    "volume": int(row['Volume'])
                }
                price_documents.append(price_doc)
            
            # Bulk upsert to MongoDB
            if price_documents:
                # Delete existing data for this symbol and period to avoid duplicates
                await StockPrice.find({"symbol": symbol.upper()}).delete()
                
                # Insert new data
                for doc in price_documents:
                    await StockPrice.find_one_and_update(
                        {"symbol": doc["symbol"], "date": doc["date"]},
                        {"$set": doc},
                        upsert=True
                    )
                
                print(f"✅ Stored {len(price_documents)} historical price records for {symbol}")
                return True
            
        except Exception as e:
            print(f"❌ Error fetching historical prices for {symbol}: {e}")
            return False
    
    @staticmethod
    async def fetch_and_store_financial_statements(symbol: str) -> bool:
        """Fetch and store quarterly and annual financial statements"""
        try:
            ticker_symbol = f"{symbol.upper()}.NS"
            
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(None, lambda: yf.Ticker(ticker_symbol))
            
            # Get financial data
            quarterly_financials = await loop.run_in_executor(None, lambda: ticker.quarterly_financials)
            annual_financials = await loop.run_in_executor(None, lambda: ticker.financials)
            
            if quarterly_financials.empty and annual_financials.empty:
                # Try without .NS suffix
                ticker_symbol = symbol.upper()
                ticker = await loop.run_in_executor(None, lambda: yf.Ticker(ticker_symbol))
                quarterly_financials = await loop.run_in_executor(None, lambda: ticker.quarterly_financials)
                annual_financials = await loop.run_in_executor(None, lambda: ticker.financials)
            
            statements_stored = 0
            
            # Process quarterly financials
            if not quarterly_financials.empty:
                statements_stored += await HistoricalDataService._store_financial_statements(
                    symbol, quarterly_financials, "quarterly"
                )
            
            # Process annual financials
            if not annual_financials.empty:
                statements_stored += await HistoricalDataService._store_financial_statements(
                    symbol, annual_financials, "annual"
                )
            
            print(f"✅ Stored {statements_stored} financial statements for {symbol}")
            return statements_stored > 0
            
        except Exception as e:
            print(f"❌ Error fetching financial statements for {symbol}: {e}")
            return False
    
    @staticmethod
    async def fetch_and_store_balance_sheets(symbol: str) -> bool:
        """Fetch and store quarterly and annual balance sheets"""
        try:
            ticker_symbol = f"{symbol.upper()}.NS"
            
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(None, lambda: yf.Ticker(ticker_symbol))
            
            # Get balance sheet data
            quarterly_balance_sheet = await loop.run_in_executor(None, lambda: ticker.quarterly_balance_sheet)
            annual_balance_sheet = await loop.run_in_executor(None, lambda: ticker.balance_sheet)
            
            if quarterly_balance_sheet.empty and annual_balance_sheet.empty:
                # Try without .NS suffix
                ticker_symbol = symbol.upper()
                ticker = await loop.run_in_executor(None, lambda: yf.Ticker(ticker_symbol))
                quarterly_balance_sheet = await loop.run_in_executor(None, lambda: ticker.quarterly_balance_sheet)
                annual_balance_sheet = await loop.run_in_executor(None, lambda: ticker.balance_sheet)
            
            sheets_stored = 0
            
            # Process quarterly balance sheets
            if not quarterly_balance_sheet.empty:
                sheets_stored += await HistoricalDataService._store_balance_sheets(
                    symbol, quarterly_balance_sheet, "quarterly"
                )
            
            # Process annual balance sheets
            if not annual_balance_sheet.empty:
                sheets_stored += await HistoricalDataService._store_balance_sheets(
                    symbol, annual_balance_sheet, "annual"
                )
            
            print(f"✅ Stored {sheets_stored} balance sheets for {symbol}")
            return sheets_stored > 0
            
        except Exception as e:
            print(f"❌ Error fetching balance sheets for {symbol}: {e}")
            return False
    
    @staticmethod
    async def fetch_and_store_cash_flows(symbol: str) -> bool:
        """Fetch and store quarterly and annual cash flow statements"""
        try:
            ticker_symbol = f"{symbol.upper()}.NS"
            
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(None, lambda: yf.Ticker(ticker_symbol))
            
            # Get cash flow data
            quarterly_cashflow = await loop.run_in_executor(None, lambda: ticker.quarterly_cashflow)
            annual_cashflow = await loop.run_in_executor(None, lambda: ticker.cashflow)
            
            if quarterly_cashflow.empty and annual_cashflow.empty:
                # Try without .NS suffix
                ticker_symbol = symbol.upper()
                ticker = await loop.run_in_executor(None, lambda: yf.Ticker(ticker_symbol))
                quarterly_cashflow = await loop.run_in_executor(None, lambda: ticker.quarterly_cashflow)
                annual_cashflow = await loop.run_in_executor(None, lambda: ticker.cashflow)
            
            cashflows_stored = 0
            
            # Process quarterly cash flows
            if not quarterly_cashflow.empty:
                cashflows_stored += await HistoricalDataService._store_cash_flows(
                    symbol, quarterly_cashflow, "quarterly"
                )
            
            # Process annual cash flows
            if not annual_cashflow.empty:
                cashflows_stored += await HistoricalDataService._store_cash_flows(
                    symbol, annual_cashflow, "annual"
                )
            
            print(f"✅ Stored {cashflows_stored} cash flow statements for {symbol}")
            return cashflows_stored > 0
            
        except Exception as e:
            print(f"❌ Error fetching cash flows for {symbol}: {e}")
            return False
    
    @staticmethod
    async def fetch_and_store_complete_historical_data(symbol: str) -> Dict[str, bool]:
        """Fetch and store all historical data for a symbol"""
        results = {}
        
        print(f"🔄 Fetching complete historical data for {symbol}...")
        
        # Fetch historical prices
        results['prices'] = await HistoricalDataService.fetch_and_store_historical_prices(symbol)
        
        # Fetch financial statements
        results['financials'] = await HistoricalDataService.fetch_and_store_financial_statements(symbol)
        
        # Fetch balance sheets
        results['balance_sheets'] = await HistoricalDataService.fetch_and_store_balance_sheets(symbol)
        
        # Fetch cash flows
        results['cash_flows'] = await HistoricalDataService.fetch_and_store_cash_flows(symbol)
        
        success_count = sum(1 for success in results.values() if success)
        print(f"📊 Historical data fetch for {symbol}: {success_count}/4 categories successful")
        
        return results
    
    @staticmethod
    async def _store_financial_statements(symbol: str, df: pd.DataFrame, period_type: str) -> int:
        """Helper method to store financial statements"""
        stored_count = 0
        
        def safe_float(value):
            try:
                if pd.isna(value) or value is None:
                    return None
                return float(value)
            except (ValueError, TypeError):
                return None
        
        for date_col in df.columns:
            try:
                period_ending = date_col.to_pydatetime() if hasattr(date_col, 'to_pydatetime') else date_col
                period_string = f"{period_ending.year}Q{(period_ending.month-1)//3 + 1}" if period_type == "quarterly" else str(period_ending.year)
                
                # Extract financial data
                financial_data = {
                    "symbol": symbol.upper(),
                    "period_type": period_type,
                    "period_ending": period_ending,
                    "period_string": period_string,
                    "currency": "INR",
                }
                
                # Map common financial statement items
                field_mapping = {
                    'Total Revenue': 'total_revenue',
                    'Revenue': 'revenue',
                    'Cost Of Revenue': 'cost_of_revenue',
                    'Gross Profit': 'gross_profit',
                    'Operating Expense': 'operating_expense',
                    'Operating Income': 'operating_income',
                    'Net Income': 'net_income',
                    'Net Income Common Stockholders': 'net_income_common_stockholders',
                    'Basic EPS': 'basic_eps',
                    'Diluted EPS': 'diluted_eps',
                    'Tax Provision': 'tax_provision',
                    'Pretax Income': 'pretax_income'
                }
                
                for yahoo_field, our_field in field_mapping.items():
                    if yahoo_field in df.index:
                        financial_data[our_field] = safe_float(df.loc[yahoo_field, date_col])
                
                # Calculate margins
                revenue = financial_data.get('total_revenue') or financial_data.get('revenue')
                gross_profit = financial_data.get('gross_profit')
                operating_income = financial_data.get('operating_income')
                net_income = financial_data.get('net_income')
                
                if revenue and revenue != 0:
                    if gross_profit:
                        financial_data['gross_margin'] = (gross_profit / revenue) * 100
                    if operating_income:
                        financial_data['operating_margin'] = (operating_income / revenue) * 100
                    if net_income:
                        financial_data['profit_margin'] = (net_income / revenue) * 100
                
                # Store in MongoDB
                await FinancialStatement.find_one_and_update(
                    {"symbol": symbol.upper(), "period_string": period_string},
                    {"$set": financial_data},
                    upsert=True
                )
                stored_count += 1
                
            except Exception as e:
                print(f"⚠️ Error storing financial statement for {symbol} {date_col}: {e}")
                continue
        
        return stored_count
    
    @staticmethod
    async def _store_balance_sheets(symbol: str, df: pd.DataFrame, period_type: str) -> int:
        """Helper method to store balance sheets"""
        stored_count = 0
        
        def safe_float(value):
            try:
                if pd.isna(value) or value is None:
                    return None
                return float(value)
            except (ValueError, TypeError):
                return None
        
        for date_col in df.columns:
            try:
                period_ending = date_col.to_pydatetime() if hasattr(date_col, 'to_pydatetime') else date_col
                period_string = f"{period_ending.year}Q{(period_ending.month-1)//3 + 1}" if period_type == "quarterly" else str(period_ending.year)
                
                balance_sheet_data = {
                    "symbol": symbol.upper(),
                    "period_type": period_type,
                    "period_ending": period_ending,
                    "period_string": period_string,
                    "currency": "INR",
                }
                
                # Map balance sheet items
                field_mapping = {
                    'Cash And Cash Equivalents': 'cash_and_cash_equivalents',
                    'Current Assets': 'current_assets',
                    'Total Assets': 'total_assets',
                    'Current Liabilities': 'current_liabilities',
                    'Total Debt': 'total_debt',
                    'Total Liabilities Net Minority Interest': 'total_liabilities',
                    'Total Equity Gross Minority Interest': 'total_equity',
                    'Common Stock': 'common_stock',
                    'Retained Earnings': 'retained_earnings',
                    'Property Plant And Equipment Net': 'property_plant_equipment',
                    'Goodwill': 'goodwill',
                    'Accounts Receivable': 'accounts_receivable',
                    'Inventory': 'inventory',
                    'Accounts Payable': 'accounts_payable',
                    'Long Term Debt': 'long_term_debt'
                }
                
                for yahoo_field, our_field in field_mapping.items():
                    if yahoo_field in df.index:
                        balance_sheet_data[our_field] = safe_float(df.loc[yahoo_field, date_col])
                
                # Calculate ratios
                current_assets = balance_sheet_data.get('current_assets')
                current_liabilities = balance_sheet_data.get('current_liabilities')
                total_debt = balance_sheet_data.get('total_debt')
                total_equity = balance_sheet_data.get('total_equity')
                total_assets = balance_sheet_data.get('total_assets')
                
                if current_assets and current_liabilities and current_liabilities != 0:
                    balance_sheet_data['current_ratio'] = current_assets / current_liabilities
                
                if total_debt and total_equity and total_equity != 0:
                    balance_sheet_data['debt_to_equity'] = total_debt / total_equity
                
                if total_debt and total_assets and total_assets != 0:
                    balance_sheet_data['debt_to_assets'] = total_debt / total_assets
                
                # Store in MongoDB
                await BalanceSheet.find_one_and_update(
                    {"symbol": symbol.upper(), "period_string": period_string},
                    {"$set": balance_sheet_data},
                    upsert=True
                )
                stored_count += 1
                
            except Exception as e:
                print(f"⚠️ Error storing balance sheet for {symbol} {date_col}: {e}")
                continue
        
        return stored_count
    
    @staticmethod
    async def _store_cash_flows(symbol: str, df: pd.DataFrame, period_type: str) -> int:
        """Helper method to store cash flow statements"""
        stored_count = 0
        
        def safe_float(value):
            try:
                if pd.isna(value) or value is None:
                    return None
                return float(value)
            except (ValueError, TypeError):
                return None
        
        for date_col in df.columns:
            try:
                period_ending = date_col.to_pydatetime() if hasattr(date_col, 'to_pydatetime') else date_col
                period_string = f"{period_ending.year}Q{(period_ending.month-1)//3 + 1}" if period_type == "quarterly" else str(period_ending.year)
                
                cash_flow_data = {
                    "symbol": symbol.upper(),
                    "period_type": period_type,
                    "period_ending": period_ending,
                    "period_string": period_string,
                    "currency": "INR",
                }
                
                # Map cash flow items
                field_mapping = {
                    'Operating Cash Flow': 'operating_cash_flow',
                    'Investing Cash Flow': 'investing_cash_flow',
                    'Financing Cash Flow': 'financing_cash_flow',
                    'Net Income From Continuing Operations': 'net_income',
                    'Depreciation': 'depreciation',
                    'Capital Expenditure': 'capital_expenditures',
                    'Free Cash Flow': 'free_cash_flow',
                    'Dividends Paid': 'dividends_paid',
                    'Change In Cash': 'net_change_in_cash',
                    'Beginning Cash Position': 'beginning_cash_position',
                    'End Cash Position': 'ending_cash_position'
                }
                
                for yahoo_field, our_field in field_mapping.items():
                    if yahoo_field in df.index:
                        cash_flow_data[our_field] = safe_float(df.loc[yahoo_field, date_col])
                
                # Calculate free cash flow if not provided
                if not cash_flow_data.get('free_cash_flow'):
                    operating_cf = cash_flow_data.get('operating_cash_flow')
                    capex = cash_flow_data.get('capital_expenditures')
                    if operating_cf and capex:
                        cash_flow_data['free_cash_flow'] = operating_cf + capex  # capex is usually negative
                
                # Store in MongoDB
                await CashFlow.find_one_and_update(
                    {"symbol": symbol.upper(), "period_string": period_string},
                    {"$set": cash_flow_data},
                    upsert=True
                )
                stored_count += 1
                
            except Exception as e:
                print(f"⚠️ Error storing cash flow for {symbol} {date_col}: {e}")
                continue
        
        return stored_count