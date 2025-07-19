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
    
    # Advanced Fundamentals
    eps: Optional[float] = None  # Earnings Per Share
    book_value: Optional[float] = None  # Book Value Per Share
    revenue: Optional[float] = None  # Total Revenue (in crores)
    net_income: Optional[float] = None  # Net Income (in crores)
    operating_margin: Optional[float] = None  # Operating Margin %
    profit_margin: Optional[float] = None  # Net Profit Margin %
    current_ratio: Optional[float] = None  # Current Ratio
    quick_ratio: Optional[float] = None  # Quick Ratio
    price_to_sales: Optional[float] = None  # P/S Ratio
    enterprise_value: Optional[float] = None  # Enterprise Value
    ebitda: Optional[float] = None  # EBITDA
    free_cash_flow: Optional[float] = None  # Free Cash Flow
    beta: Optional[float] = None  # Stock Beta
    
    # Growth metrics
    revenue_growth: Optional[float] = None  # Revenue Growth YoY %
    earnings_growth: Optional[float] = None  # Earnings Growth YoY %
    
    # Dividend metrics
    dividend_per_share: Optional[float] = None  # Dividend Per Share
    payout_ratio: Optional[float] = None  # Dividend Payout Ratio %
    
    # Valuation metrics
    price_to_earnings_growth: Optional[float] = None  # PEG Ratio
    price_to_cash_flow: Optional[float] = None  # P/CF Ratio
    
    # Historical trend data for variance analysis
    # Previous Quarter (QoQ) data
    pe_ratio_qoq: Optional[float] = None
    current_ratio_qoq: Optional[float] = None
    debt_to_equity_qoq: Optional[float] = None
    profit_margin_qoq: Optional[float] = None
    revenue_qoq: Optional[float] = None
    eps_qoq: Optional[float] = None
    
    # Previous Year (YoY) data
    pe_ratio_yoy: Optional[float] = None
    current_ratio_yoy: Optional[float] = None
    debt_to_equity_yoy: Optional[float] = None
    profit_margin_yoy: Optional[float] = None
    revenue_yoy: Optional[float] = None
    eps_yoy: Optional[float] = None
    
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
    date: str = Field(..., index=True)  # YYYY-MM-DD format for easy querying
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    adj_close_price: Optional[float] = None  # Adjusted close price
    volume: int
    
    class Settings:
        collection = "stock_prices"
        indexes = [
            [("symbol", 1), ("timestamp", -1)],
            [("symbol", 1), ("date", -1)],
            "date",
        ]

class FinancialStatement(Document):
    """Quarterly and Annual Financial Statements"""
    symbol: str = Field(..., index=True)
    period_type: str = Field(..., index=True)  # "quarterly" or "annual"
    period_ending: datetime = Field(..., index=True)
    period_string: str = Field(..., index=True)  # "2024Q1", "2024", etc.
    currency: str = Field(default="INR")
    
    # Income Statement
    total_revenue: Optional[float] = None
    revenue: Optional[float] = None
    cost_of_revenue: Optional[float] = None
    gross_profit: Optional[float] = None
    operating_expense: Optional[float] = None
    operating_income: Optional[float] = None
    net_non_operating_interest_income: Optional[float] = None
    other_income_expense: Optional[float] = None
    pretax_income: Optional[float] = None
    tax_provision: Optional[float] = None
    net_income_common_stockholders: Optional[float] = None
    net_income: Optional[float] = None
    
    # Per Share Data
    basic_eps: Optional[float] = None
    diluted_eps: Optional[float] = None
    basic_average_shares: Optional[float] = None
    diluted_average_shares: Optional[float] = None
    
    # Margins (calculated)
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    profit_margin: Optional[float] = None
    
    class Settings:
        collection = "financial_statements"
        indexes = [
            [("symbol", 1), ("period_ending", -1)],
            [("symbol", 1), ("period_type", 1), ("period_ending", -1)],
            "period_string",
        ]

class BalanceSheet(Document):
    """Quarterly and Annual Balance Sheets"""
    symbol: str = Field(..., index=True)
    period_type: str = Field(..., index=True)  # "quarterly" or "annual"
    period_ending: datetime = Field(..., index=True)
    period_string: str = Field(..., index=True)
    currency: str = Field(default="INR")
    
    # Assets
    cash_and_cash_equivalents: Optional[float] = None
    short_term_investments: Optional[float] = None
    accounts_receivable: Optional[float] = None
    inventory: Optional[float] = None
    current_assets: Optional[float] = None
    property_plant_equipment: Optional[float] = None
    goodwill: Optional[float] = None
    intangible_assets: Optional[float] = None
    total_assets: Optional[float] = None
    
    # Liabilities
    accounts_payable: Optional[float] = None
    current_liabilities: Optional[float] = None
    long_term_debt: Optional[float] = None
    total_debt: Optional[float] = None
    total_liabilities: Optional[float] = None
    
    # Equity
    common_stock: Optional[float] = None
    retained_earnings: Optional[float] = None
    total_equity: Optional[float] = None
    total_capitalization: Optional[float] = None
    
    # Calculated Ratios
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    debt_to_equity: Optional[float] = None
    debt_to_assets: Optional[float] = None
    
    class Settings:
        collection = "balance_sheets"
        indexes = [
            [("symbol", 1), ("period_ending", -1)],
            [("symbol", 1), ("period_type", 1), ("period_ending", -1)],
            "period_string",
        ]

class CashFlow(Document):
    """Quarterly and Annual Cash Flow Statements"""
    symbol: str = Field(..., index=True)
    period_type: str = Field(..., index=True)
    period_ending: datetime = Field(..., index=True)
    period_string: str = Field(..., index=True)
    currency: str = Field(default="INR")
    
    # Operating Cash Flow
    net_income: Optional[float] = None
    depreciation: Optional[float] = None
    changes_in_working_capital: Optional[float] = None
    operating_cash_flow: Optional[float] = None
    
    # Investing Cash Flow
    capital_expenditures: Optional[float] = None
    investments: Optional[float] = None
    investing_cash_flow: Optional[float] = None
    
    # Financing Cash Flow
    dividends_paid: Optional[float] = None
    share_issuance: Optional[float] = None
    debt_issuance: Optional[float] = None
    financing_cash_flow: Optional[float] = None
    
    # Summary
    free_cash_flow: Optional[float] = None
    net_change_in_cash: Optional[float] = None
    beginning_cash_position: Optional[float] = None
    ending_cash_position: Optional[float] = None
    
    class Settings:
        collection = "cash_flows"
        indexes = [
            [("symbol", 1), ("period_ending", -1)],
            [("symbol", 1), ("period_type", 1), ("period_ending", -1)],
            "period_string",
        ]

class StockResponse(BaseModel):
    symbol: str
    name: str
    exchange: str
    current_price: Optional[float]
    price_change: Optional[float]
    price_change_percent: Optional[float]
    volume: Optional[int] = None
    market_cap: Optional[float]
    pe_ratio: Optional[float]
    last_updated: datetime
    
    # Extended fundamentals
    pb_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    eps: Optional[float] = None
    book_value: Optional[float] = None
    revenue: Optional[float] = None
    net_income: Optional[float] = None
    operating_margin: Optional[float] = None
    profit_margin: Optional[float] = None
    current_ratio: Optional[float] = None
    price_to_sales: Optional[float] = None
    ebitda: Optional[float] = None
    beta: Optional[float] = None
    revenue_growth: Optional[float] = None
    earnings_growth: Optional[float] = None
    dividend_per_share: Optional[float] = None
    payout_ratio: Optional[float] = None
    price_to_earnings_growth: Optional[float] = None
    debt_to_equity: Optional[float] = None
    
    # Historical trend data for variance analysis
    pe_ratio_qoq: Optional[float] = None
    current_ratio_qoq: Optional[float] = None
    debt_to_equity_qoq: Optional[float] = None
    profit_margin_qoq: Optional[float] = None
    revenue_qoq: Optional[float] = None
    eps_qoq: Optional[float] = None
    pe_ratio_yoy: Optional[float] = None
    current_ratio_yoy: Optional[float] = None
    debt_to_equity_yoy: Optional[float] = None
    profit_margin_yoy: Optional[float] = None
    revenue_yoy: Optional[float] = None
    eps_yoy: Optional[float] = None

class StockPriceResponse(BaseModel):
    symbol: str
    timestamp: datetime
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: int