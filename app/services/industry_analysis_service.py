"""
Industry Analysis Service
Provides peer comparison and industry benchmarking for Indian stocks
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import statistics
import math

@dataclass
class IndustryBenchmark:
    """Industry benchmark data"""
    pe_ratio_avg: Optional[float] = None
    pb_ratio_avg: Optional[float] = None
    profit_margin_avg: Optional[float] = None
    revenue_growth_avg: Optional[float] = None
    debt_to_equity_avg: Optional[float] = None
    dividend_yield_avg: Optional[float] = None
    current_ratio_avg: Optional[float] = None

@dataclass
class PeerComparison:
    """Peer comparison result"""
    symbol: str
    industry: str
    peers: List[str]
    benchmark: IndustryBenchmark
    relative_position: Dict[str, str]  # 'high', 'average', 'low'

class IndustryAnalysisService:
    """Service for industry analysis and peer comparison"""
    
    # Industry classification for Indian stocks
    INDUSTRY_MAPPING = {
        # Technology & IT Services
        'TCS': 'IT Services',
        'INFY': 'IT Services', 
        'WIPRO': 'IT Services',
        'HCLTECH': 'IT Services',
        'TECHM': 'IT Services',
        'LTI': 'IT Services',
        'MINDTREE': 'IT Services',
        
        # Banking & Financial Services
        'HDFCBANK': 'Private Banking',
        'ICICIBANK': 'Private Banking',
        'KOTAKBANK': 'Private Banking',
        'AXISBANK': 'Private Banking',
        'INDUSINDBK': 'Private Banking',
        'SBIN': 'Public Banking',
        'PNB': 'Public Banking',
        'CANFIN': 'Public Banking',
        
        # Non-Banking Financial Services
        'BAJFINANCE': 'NBFC',
        'BAJAJFINSV': 'NBFC',
        'HDFCLIFE': 'Insurance',
        'SBILIFE': 'Insurance',
        'ICICIPRULI': 'Insurance',
        
        # Oil & Gas
        'RELIANCE': 'Oil & Gas',
        'ONGC': 'Oil & Gas',
        'BPCL': 'Oil & Gas',
        'IOCL': 'Oil & Gas',
        'GAIL': 'Oil & Gas',
        
        # Automobiles
        'MARUTI': 'Automobiles',
        'TATAMOTORS': 'Automobiles',
        'M&M': 'Automobiles',
        'BAJAJ-AUTO': 'Automobiles',
        'EICHERMOT': 'Automobiles',
        'HEROMOTOCO': 'Automobiles',
        
        # Pharmaceuticals
        'SUNPHARMA': 'Pharmaceuticals',
        'DRREDDY': 'Pharmaceuticals',
        'CIPLA': 'Pharmaceuticals',
        'BIOCON': 'Pharmaceuticals',
        'LUPIN': 'Pharmaceuticals',
        'AUROPHARMA': 'Pharmaceuticals',
        
        # FMCG & Consumer Goods
        'HINDUNILVR': 'FMCG',
        'ITC': 'FMCG',
        'NESTLEIND': 'FMCG',
        'BRITANNIA': 'FMCG',
        'DABUR': 'FMCG',
        'GODREJCP': 'FMCG',
        'MARICO': 'FMCG',
        
        # Retail
        'TRENT': 'Retail',
        'AVENUE': 'Retail',
        'SHOPSSTOP': 'Retail',
        
        # Metals & Mining
        'TATASTEEL': 'Metals',
        'JSWSTEEL': 'Metals',
        'HINDALCO': 'Metals',
        'VEDL': 'Metals',
        'NMDC': 'Metals',
        'COALINDIA': 'Mining',
        
        # Power & Infrastructure
        'NTPC': 'Power',
        'POWERGRID': 'Power',
        'LT': 'Infrastructure',
        'ADANIPORTS': 'Infrastructure',
        
        # Telecom
        'BHARTIARTL': 'Telecom',
        'IDEA': 'Telecom',
        
        # Cement
        'ULTRACEMCO': 'Cement',
        'ACC': 'Cement',
        'AMBUJCEM': 'Cement',
        'SHREECEM': 'Cement',
    }
    
    # Industry benchmark data (approximate values for Indian markets)
    INDUSTRY_BENCHMARKS = {
        'IT Services': IndustryBenchmark(
            pe_ratio_avg=25.0, pb_ratio_avg=8.5, profit_margin_avg=22.0,
            revenue_growth_avg=12.0, debt_to_equity_avg=0.1, dividend_yield_avg=2.5,
            current_ratio_avg=2.8
        ),
        'Private Banking': IndustryBenchmark(
            pe_ratio_avg=18.0, pb_ratio_avg=2.8, profit_margin_avg=25.0,
            revenue_growth_avg=15.0, debt_to_equity_avg=6.5, dividend_yield_avg=1.8,
            current_ratio_avg=1.1
        ),
        'Public Banking': IndustryBenchmark(
            pe_ratio_avg=12.0, pb_ratio_avg=1.2, profit_margin_avg=18.0,
            revenue_growth_avg=8.0, debt_to_equity_avg=8.0, dividend_yield_avg=3.5,
            current_ratio_avg=1.0
        ),
        'NBFC': IndustryBenchmark(
            pe_ratio_avg=22.0, pb_ratio_avg=3.5, profit_margin_avg=28.0,
            revenue_growth_avg=18.0, debt_to_equity_avg=4.2, dividend_yield_avg=1.5,
            current_ratio_avg=1.3
        ),
        'Oil & Gas': IndustryBenchmark(
            pe_ratio_avg=12.0, pb_ratio_avg=1.8, profit_margin_avg=8.0,
            revenue_growth_avg=5.0, debt_to_equity_avg=0.8, dividend_yield_avg=4.5,
            current_ratio_avg=1.2
        ),
        'Automobiles': IndustryBenchmark(
            pe_ratio_avg=20.0, pb_ratio_avg=2.5, profit_margin_avg=6.5,
            revenue_growth_avg=8.0, debt_to_equity_avg=0.5, dividend_yield_avg=2.0,
            current_ratio_avg=1.4
        ),
        'Pharmaceuticals': IndustryBenchmark(
            pe_ratio_avg=28.0, pb_ratio_avg=4.2, profit_margin_avg=18.0,
            revenue_growth_avg=12.0, debt_to_equity_avg=0.3, dividend_yield_avg=1.2,
            current_ratio_avg=2.1
        ),
        'FMCG': IndustryBenchmark(
            pe_ratio_avg=45.0, pb_ratio_avg=12.0, profit_margin_avg=15.0,
            revenue_growth_avg=8.0, debt_to_equity_avg=0.2, dividend_yield_avg=2.8,
            current_ratio_avg=1.8
        ),
        'Retail': IndustryBenchmark(
            pe_ratio_avg=85.0, pb_ratio_avg=15.0, profit_margin_avg=8.0,
            revenue_growth_avg=25.0, debt_to_equity_avg=0.4, dividend_yield_avg=0.5,
            current_ratio_avg=1.6
        ),
        'Metals': IndustryBenchmark(
            pe_ratio_avg=15.0, pb_ratio_avg=1.5, profit_margin_avg=12.0,
            revenue_growth_avg=6.0, debt_to_equity_avg=0.6, dividend_yield_avg=3.5,
            current_ratio_avg=1.3
        ),
        'Power': IndustryBenchmark(
            pe_ratio_avg=16.0, pb_ratio_avg=1.8, profit_margin_avg=12.0,
            revenue_growth_avg=7.0, debt_to_equity_avg=1.2, dividend_yield_avg=4.0,
            current_ratio_avg=1.1
        ),
        'Telecom': IndustryBenchmark(
            pe_ratio_avg=20.0, pb_ratio_avg=2.2, profit_margin_avg=15.0,
            revenue_growth_avg=5.0, debt_to_equity_avg=2.5, dividend_yield_avg=3.0,
            current_ratio_avg=0.9
        ),
    }
    
    @staticmethod
    def get_industry(symbol: str) -> Optional[str]:
        """Get industry for a stock symbol"""
        return IndustryAnalysisService.INDUSTRY_MAPPING.get(symbol.upper())
    
    @staticmethod
    def get_peers(symbol: str) -> List[str]:
        """Get peer companies in the same industry"""
        industry = IndustryAnalysisService.get_industry(symbol)
        if not industry:
            return []
        
        peers = [
            s for s, i in IndustryAnalysisService.INDUSTRY_MAPPING.items() 
            if i == industry and s != symbol.upper()
        ]
        return peers[:4]  # Return top 4 peers
    
    @staticmethod
    def get_industry_benchmark(industry: str) -> Optional[IndustryBenchmark]:
        """Get industry benchmark data"""
        return IndustryAnalysisService.INDUSTRY_BENCHMARKS.get(industry)
    
    @staticmethod
    def compare_to_industry(symbol: str, stock_data) -> Optional[PeerComparison]:
        """Compare stock metrics to industry benchmarks"""
        industry = IndustryAnalysisService.get_industry(symbol)
        if not industry:
            return None
        
        benchmark = IndustryAnalysisService.get_industry_benchmark(industry)
        if not benchmark:
            return None
        
        peers = IndustryAnalysisService.get_peers(symbol)
        
        # Calculate relative positions
        relative_position = {}
        
        # P/E Ratio comparison
        if stock_data.pe_ratio and benchmark.pe_ratio_avg:
            pe_diff = (stock_data.pe_ratio - benchmark.pe_ratio_avg) / benchmark.pe_ratio_avg
            if pe_diff > 0.2:
                relative_position['pe_ratio'] = 'high'
            elif pe_diff < -0.2:
                relative_position['pe_ratio'] = 'low'
            else:
                relative_position['pe_ratio'] = 'average'
        
        # Profit Margin comparison
        if stock_data.profit_margin and benchmark.profit_margin_avg:
            margin_diff = (stock_data.profit_margin - benchmark.profit_margin_avg) / benchmark.profit_margin_avg
            if margin_diff > 0.15:
                relative_position['profit_margin'] = 'high'
            elif margin_diff < -0.15:
                relative_position['profit_margin'] = 'low'
            else:
                relative_position['profit_margin'] = 'average'
        
        # Revenue Growth comparison
        if stock_data.revenue_growth and benchmark.revenue_growth_avg:
            growth_diff = (stock_data.revenue_growth - benchmark.revenue_growth_avg) / benchmark.revenue_growth_avg
            if growth_diff > 0.25:
                relative_position['revenue_growth'] = 'high'
            elif growth_diff < -0.25:
                relative_position['revenue_growth'] = 'low'
            else:
                relative_position['revenue_growth'] = 'average'
        
        # Debt to Equity comparison
        if stock_data.debt_to_equity is not None and benchmark.debt_to_equity_avg:
            debt_diff = (stock_data.debt_to_equity - benchmark.debt_to_equity_avg) / (benchmark.debt_to_equity_avg + 0.1)  # Avoid division by zero
            if debt_diff > 0.3:
                relative_position['debt_to_equity'] = 'high'  # Higher debt is worse
            elif debt_diff < -0.3:
                relative_position['debt_to_equity'] = 'low'   # Lower debt is better
            else:
                relative_position['debt_to_equity'] = 'average'
        
        return PeerComparison(
            symbol=symbol,
            industry=industry,
            peers=peers,
            benchmark=benchmark,
            relative_position=relative_position
        )

class ASCIIChartService:
    """Service for generating ASCII charts"""
    
    @staticmethod
    def generate_bar_chart(data: Dict[str, float], title: str = "", width: int = 30) -> str:
        """Generate horizontal bar chart"""
        if not data:
            return "No data available"
        
        max_value = max(data.values())
        min_value = min(data.values())
        
        # Normalize values to fit in the width
        normalized_data = {}
        for key, value in data.items():
            if max_value > 0:
                normalized_data[key] = int((value / max_value) * width)
            else:
                normalized_data[key] = 0
        
        chart = []
        if title:
            chart.append(title)
            chart.append("=" * len(title))
        
        for key, normalized_value in normalized_data.items():
            bar = "█" * normalized_value
            spaces = " " * (width - normalized_value)
            original_value = data[key]
            chart.append(f"{key:<15} {bar}{spaces} {original_value:.1f}")
        
        return "\n".join(chart)
    
    @staticmethod
    def generate_comparison_chart(stock_value: float, industry_avg: float, metric_name: str) -> str:
        """Generate comparison chart between stock and industry average"""
        max_val = max(stock_value, industry_avg) if stock_value and industry_avg else 1
        
        # Scale to 20 characters width
        stock_bar = int((stock_value / max_val) * 20) if stock_value else 0
        industry_bar = int((industry_avg / max_val) * 20) if industry_avg else 0
        
        chart = []
        chart.append(f"{metric_name} Comparison:")
        chart.append(f"Stock     {'█' * stock_bar:<20} {stock_value:.1f}")
        chart.append(f"Industry  {'░' * industry_bar:<20} {industry_avg:.1f}")
        
        return "\n".join(chart)
    
    @staticmethod
    def generate_trend_chart(values: List[float], labels: List[str], title: str = "") -> str:
        """Generate simple trend chart"""
        if not values or len(values) != len(labels):
            return "No trend data available"
        
        max_val = max(values) if values else 1
        min_val = min(values) if values else 0
        
        # Scale values to fit in 10 levels
        height = 8
        scaled_values = []
        for val in values:
            if max_val > min_val:
                scaled = int(((val - min_val) / (max_val - min_val)) * height)
            else:
                scaled = height // 2
            scaled_values.append(scaled)
        
        chart = []
        if title:
            chart.append(title)
            chart.append("-" * len(title))
        
        # Draw chart from top to bottom
        for level in range(height, -1, -1):
            line = ""
            for i, scaled_val in enumerate(scaled_values):
                if scaled_val >= level:
                    line += "██"
                else:
                    line += "  "
            
            # Add value labels on the right
            if level == height:
                line += f"  {max_val:.1f}"
            elif level == 0:
                line += f"  {min_val:.1f}"
            
            chart.append(line)
        
        # Add labels at bottom
        label_line = ""
        for label in labels:
            label_line += f"{label[:2]:<2}"
        chart.append(label_line)
        
        return "\n".join(chart)