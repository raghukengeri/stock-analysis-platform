#!/usr/bin/env python3
"""
NSE Top 500 Stocks Test Script
Tests the stock analysis platform's ability to recognize and fetch data for NSE listed stocks.
"""

import csv
import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import argparse

# Test configuration
BASE_URL = "http://localhost:8000"
CSV_FILE_PATH = "/Users/raghushankarkengeri/Downloads/ind_nifty500list (3).csv"

class NSEStockTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.results = {
            "total_stocks": 0,
            "successful_detections": 0,
            "successful_data_fetch": 0,
            "failed_detections": 0,
            "failed_data_fetch": 0,
            "errors": [],
            "successful_stocks": [],
            "failed_stocks": [],
            "detection_details": {},
            "performance_stats": {
                "avg_response_time": 0.0,
                "total_test_time": 0.0
            }
        }
        
    async def load_nse_stocks(self) -> List[Dict[str, str]]:
        """Load NSE stocks from CSV file"""
        stocks = []
        try:
            with open(CSV_FILE_PATH, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row.get('Symbol') and row.get('Company Name'):
                        stocks.append({
                            'symbol': row['Symbol'].strip(),
                            'company_name': row['Company Name'].strip(),
                            'industry': row.get('Industry', '').strip(),
                            'isin': row.get('ISIN Code', '').strip()
                        })
            print(f"✅ Loaded {len(stocks)} stocks from NSE CSV")
            return stocks
        except Exception as e:
            print(f"❌ Error loading CSV: {e}")
            return []
    
    async def test_stock_detection(self, session: aiohttp.ClientSession, stock: Dict[str, str]) -> Dict[str, any]:
        """Test if a stock can be detected and data fetched"""
        symbol = stock['symbol']
        company_name = stock['company_name']
        
        # Test both symbol and company name
        test_queries = [
            f"price for {symbol}",
            f"get me price of {symbol}",
            f"{company_name} price",
            f"what is the price of {company_name}?",
            f"{symbol} quote"
        ]
        
        results = {
            'symbol': symbol,
            'company_name': company_name,
            'industry': stock.get('industry', ''),
            'detection_success': False,
            'data_fetch_success': False,
            'response_times': [],
            'test_results': {},
            'errors': []
        }
        
        for query in test_queries:
            try:
                start_time = time.time()
                
                async with session.post(
                    f"{self.base_url}/api/v1/chat/dev/message",
                    json={
                        "content": query,
                        "message_type": "user"
                    },
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    end_time = time.time()
                    response_time = end_time - start_time
                    results['response_times'].append(response_time)
                    
                    if response.status == 200:
                        data = await response.json()
                        content = data.get('content', '').lower()
                        
                        # Check if the response contains price information
                        has_price = any(indicator in content for indicator in [
                            'current price', '₹', '$', 'price:', 'cost:', 'quote:',
                            'market cap', 'change:', 'exchange:'
                        ])
                        
                        # Check if it's an error response
                        is_error = any(error_indicator in content for error_indicator in [
                            "couldn't find", "sorry", "error", "try again",
                            "check the symbol", "no data"
                        ])
                        
                        results['test_results'][query] = {
                            'status': 'success',
                            'has_price_data': has_price,
                            'is_error_response': is_error,
                            'response_time': response_time,
                            'content_preview': content[:200] + "..." if len(content) > 200 else content
                        }
                        
                        if has_price and not is_error:
                            results['detection_success'] = True
                            results['data_fetch_success'] = True
                            break  # Found working query, no need to test others
                        elif not is_error:
                            results['detection_success'] = True
                            
                    else:
                        results['test_results'][query] = {
                            'status': f'http_error_{response.status}',
                            'response_time': response_time
                        }
                        results['errors'].append(f"HTTP {response.status} for query: {query}")
                        
            except asyncio.TimeoutError:
                results['test_results'][query] = {
                    'status': 'timeout',
                    'response_time': 10.0
                }
                results['errors'].append(f"Timeout for query: {query}")
            except Exception as e:
                results['test_results'][query] = {
                    'status': 'exception',
                    'error': str(e),
                    'response_time': 0.0
                }
                results['errors'].append(f"Exception for query '{query}': {str(e)}")
                
        return results
    
    async def run_comprehensive_test(self, max_concurrent: int = 5, sample_size: Optional[int] = None) -> Dict:
        """Run comprehensive test on NSE stocks"""
        print("🚀 Starting NSE Top 500 Stocks Test")
        print(f"📊 Base URL: {self.base_url}")
        print(f"📁 CSV File: {CSV_FILE_PATH}")
        
        # Load stocks
        stocks = await self.load_nse_stocks()
        if not stocks:
            return {"error": "Failed to load stocks from CSV"}
        
        # Limit to sample size if specified
        if sample_size:
            stocks = stocks[:sample_size]
            print(f"🔬 Testing sample of {len(stocks)} stocks")
        else:
            print(f"🔬 Testing all {len(stocks)} stocks")
        
        self.results["total_stocks"] = len(stocks)
        
        # Create semaphore for concurrent requests
        semaphore = asyncio.Semaphore(max_concurrent)
        start_time = time.time()
        
        async def test_with_semaphore(session, stock):
            async with semaphore:
                return await self.test_stock_detection(session, stock)
        
        # Run tests concurrently
        async with aiohttp.ClientSession() as session:
            tasks = [test_with_semaphore(session, stock) for stock in stocks]
            
            print(f"⏳ Running {len(tasks)} tests with max {max_concurrent} concurrent requests...")
            
            # Process results as they complete
            completed = 0
            for coro in asyncio.as_completed(tasks):
                result = await coro
                completed += 1
                
                # Update statistics
                if result['detection_success']:
                    self.results["successful_detections"] += 1
                else:
                    self.results["failed_detections"] += 1
                    
                if result['data_fetch_success']:
                    self.results["successful_data_fetch"] += 1
                    self.results["successful_stocks"].append(result)
                else:
                    self.results["failed_data_fetch"] += 1
                    self.results["failed_stocks"].append(result)
                
                self.results["detection_details"][result['symbol']] = result
                
                # Progress indicator
                if completed % 50 == 0 or completed == len(tasks):
                    success_rate = (self.results["successful_data_fetch"] / completed) * 100
                    print(f"📈 Progress: {completed}/{len(tasks)} ({success_rate:.1f}% success rate)")
        
        # Calculate performance stats
        end_time = time.time()
        self.results["performance_stats"]["total_test_time"] = end_time - start_time
        
        all_response_times = []
        for details in self.results["detection_details"].values():
            all_response_times.extend(details.get('response_times', []))
        
        if all_response_times:
            self.results["performance_stats"]["avg_response_time"] = sum(all_response_times) / len(all_response_times)
        
        return self.results
    
    def generate_detailed_report(self, results: Dict) -> str:
        """Generate detailed test report"""
        total = results["total_stocks"]
        successful_detection = results["successful_detections"]
        successful_data = results["successful_data_fetch"]
        failed_detection = results["failed_detections"]
        failed_data = results["failed_data_fetch"]
        
        detection_rate = (successful_detection / total) * 100 if total > 0 else 0
        success_rate = (successful_data / total) * 100 if total > 0 else 0
        
        report = f"""
🏦 NSE TOP 500 STOCKS - COMPREHENSIVE TEST REPORT
{'='*60}

📊 OVERALL STATISTICS
Total Stocks Tested: {total}
Successful Detections: {successful_detection} ({detection_rate:.1f}%)
Successful Data Fetch: {successful_data} ({success_rate:.1f}%)
Failed Detections: {failed_detection}
Failed Data Fetch: {failed_data}

⚡ PERFORMANCE METRICS
Total Test Time: {results['performance_stats']['total_test_time']:.2f} seconds
Average Response Time: {results['performance_stats']['avg_response_time']:.3f} seconds

✅ TOP SUCCESSFUL STOCKS (Sample)
"""
        
        # Show successful stocks by industry
        successful_by_industry = {}
        for stock in results["successful_stocks"][:20]:  # Top 20
            industry = stock.get('industry', 'Unknown')
            if industry not in successful_by_industry:
                successful_by_industry[industry] = []
            successful_by_industry[industry].append(stock)
        
        for industry, stocks in list(successful_by_industry.items())[:5]:  # Top 5 industries
            report += f"\n{industry}:\n"
            for stock in stocks[:3]:  # Top 3 per industry
                avg_time = sum(stock['response_times']) / len(stock['response_times']) if stock['response_times'] else 0
                report += f"  • {stock['symbol']} ({stock['company_name']}) - {avg_time:.3f}s\n"
        
        # Show failed stocks with reasons
        report += f"\n❌ FAILED STOCKS (Sample)\n"
        for stock in results["failed_stocks"][:10]:  # First 10 failures
            errors = stock.get('errors', [])
            error_summary = errors[0] if errors else "Unknown error"
            report += f"  • {stock['symbol']} ({stock['company_name']}) - {error_summary}\n"
        
        # Industry analysis
        report += f"\n📈 INDUSTRY ANALYSIS\n"
        industry_stats = {}
        for stock_symbol, details in results["detection_details"].items():
            industry = details.get('industry', 'Unknown')
            if industry not in industry_stats:
                industry_stats[industry] = {'total': 0, 'successful': 0}
            industry_stats[industry]['total'] += 1
            if details['data_fetch_success']:
                industry_stats[industry]['successful'] += 1
        
        # Sort industries by success rate
        sorted_industries = sorted(
            industry_stats.items(),
            key=lambda x: x[1]['successful'] / x[1]['total'] if x[1]['total'] > 0 else 0,
            reverse=True
        )
        
        for industry, stats in sorted_industries[:10]:  # Top 10 industries
            rate = (stats['successful'] / stats['total']) * 100 if stats['total'] > 0 else 0
            report += f"  • {industry}: {stats['successful']}/{stats['total']} ({rate:.1f}%)\n"
        
        # Recommendations
        report += f"\n💡 RECOMMENDATIONS\n"
        if success_rate < 50:
            report += "  • Success rate is below 50%. Consider expanding the symbol mapping database.\n"
        if failed_detection > 0:
            report += f"  • {failed_detection} stocks failed detection. Review symbol detection algorithm.\n"
        if results['performance_stats']['avg_response_time'] > 2.0:
            report += "  • Average response time is high. Consider caching or API optimization.\n"
        
        report += f"\n{'='*60}\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        return report
    
    def save_results(self, results: Dict, filename: str = None):
        """Save detailed results to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"nse_test_results_{timestamp}.json"
        
        filepath = f"/Users/raghushankarkengeri/Documents/python code/stock market/AI Screener/stock-analysis-platform/{filename}"
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"💾 Detailed results saved to: {filepath}")
        except Exception as e:
            print(f"❌ Failed to save results: {e}")

async def main():
    parser = argparse.ArgumentParser(description='Test NSE stocks against StockChat platform')
    parser.add_argument('--url', default='http://localhost:8000', help='Base URL of the API')
    parser.add_argument('--sample', type=int, help='Test only first N stocks (for quick testing)')
    parser.add_argument('--concurrent', type=int, default=5, help='Max concurrent requests')
    parser.add_argument('--save', action='store_true', help='Save detailed results to JSON file')
    
    args = parser.parse_args()
    
    tester = NSEStockTester(args.url)
    
    print(f"🧪 NSE TOP 500 STOCKS TESTING TOOL")
    print(f"Target API: {args.url}")
    print(f"Max Concurrent: {args.concurrent}")
    if args.sample:
        print(f"Sample Size: {args.sample}")
    print(f"{'='*60}")
    
    try:
        results = await tester.run_comprehensive_test(
            max_concurrent=args.concurrent,
            sample_size=args.sample
        )
        
        if "error" in results:
            print(f"❌ Test failed: {results['error']}")
            return
        
        # Generate and display report
        report = tester.generate_detailed_report(results)
        print(report)
        
        # Save detailed results if requested
        if args.save:
            tester.save_results(results)
        
        # Quick summary
        total = results["total_stocks"]
        successful = results["successful_data_fetch"]
        success_rate = (successful / total) * 100 if total > 0 else 0
        
        print(f"\n🎯 QUICK SUMMARY: {successful}/{total} stocks working ({success_rate:.1f}% success rate)")
        
        if success_rate >= 80:
            print("🎉 EXCELLENT! Platform handles NSE stocks very well.")
        elif success_rate >= 60:
            print("👍 GOOD! Platform handles most NSE stocks well.")
        elif success_rate >= 40:
            print("⚠️  MODERATE! Some issues with NSE stock recognition.")
        else:
            print("🚨 NEEDS IMPROVEMENT! Many NSE stocks not recognized.")
            
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(main())