#!/usr/bin/env python3
"""
Deep Research Report Generator for Finance-Bro
Generates comprehensive stock research reports using OpenAI GPT-4 and real market data.
"""

import asyncio
import json
import logging
import openai
import yfinance as yf
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pandas as pd
from dataclasses import dataclass

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import configuration
from config import config

# Configure OpenAI
openai.api_key = config.OPENAI_API_KEY

@dataclass
class StockData:
    """Structure for stock data"""
    symbol: str
    company_name: str
    current_price: float
    market_cap: float
    pe_ratio: float
    eps: float
    revenue: float
    profit_margin: float
    debt_to_equity: float
    return_on_equity: float
    price_to_book: float
    dividend_yield: float
    beta: float
    fifty_two_week_high: float
    fifty_two_week_low: float
    average_volume: float
    historical_data: pd.DataFrame

class DeepResearchReportGenerator:
    """Comprehensive research report generator using OpenAI and financial data"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
        
    def get_comprehensive_stock_data(self, symbol: str) -> StockData:
        """Get comprehensive stock data from multiple sources"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            history = ticker.history(period="2y")
            
            # Get financial data
            financials = ticker.financials
            balance_sheet = ticker.balance_sheet
            
            stock_data = StockData(
                symbol=symbol,
                company_name=info.get('longName', symbol),
                current_price=float(history['Close'].iloc[-1]),
                market_cap=info.get('marketCap', 0),
                pe_ratio=info.get('forwardPE', 0),
                eps=info.get('forwardEps', 0),
                revenue=info.get('totalRevenue', 0),
                profit_margin=info.get('profitMargins', 0),
                debt_to_equity=info.get('debtToEquity', 0),
                return_on_equity=info.get('returnOnEquity', 0),
                price_to_book=info.get('priceToBook', 0),
                dividend_yield=info.get('dividendYield', 0),
                beta=info.get('beta', 1.0),
                fifty_two_week_high=info.get('fiftyTwoWeekHigh', 0),
                fifty_two_week_low=info.get('fiftyTwoWeekLow', 0),
                average_volume=info.get('averageVolume', 0),
                historical_data=history
            )
            
            return stock_data
            
        except Exception as e:
            logger.error(f"Error getting stock data for {symbol}: {e}")
            raise

    def get_industry_comparison(self, symbol: str, sector: str) -> Dict[str, Any]:
        """Get industry peer comparison data"""
        try:
            # For demo purposes, using major tech stocks as comparison
            peer_symbols = {
                'Technology': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META'],
                'Healthcare': ['JNJ', 'PFE', 'UNH', 'MRK', 'ABBV'],
                'Finance': ['JPM', 'BAC', 'WFC', 'GS', 'MS'],
                'Consumer': ['TSLA', 'NFLX', 'NKE', 'HD', 'MCD']
            }
            
            peers = peer_symbols.get('Technology', ['SPY'])  # Default to tech
            if symbol in peers:
                peers.remove(symbol)
            
            peer_data = {}
            for peer in peers[:3]:  # Limit to 3 peers
                try:
                    peer_ticker = yf.Ticker(peer)
                    peer_info = peer_ticker.info
                    peer_data[peer] = {
                        'pe_ratio': peer_info.get('forwardPE', 0),
                        'market_cap': peer_info.get('marketCap', 0),
                        'profit_margin': peer_info.get('profitMargins', 0),
                        'roe': peer_info.get('returnOnEquity', 0)
                    }
                except:
                    continue
                    
            return peer_data
            
        except Exception as e:
            logger.warning(f"Error getting peer data: {e}")
            return {}

    async def generate_research_report(self, symbol: str, report_type: str = "comprehensive") -> Dict[str, Any]:
        """Generate a comprehensive research report using OpenAI GPT-4"""
        
        logger.info(f"Generating {report_type} research report for {symbol}")
        
        try:
            # Get comprehensive stock data
            stock_data = self.get_comprehensive_stock_data(symbol)
            
            # Get peer comparison
            peer_data = self.get_industry_comparison(symbol, "Technology")
            
            # Calculate technical indicators
            recent_history = stock_data.historical_data.tail(50)
            sma_20 = recent_history['Close'].rolling(window=20).mean().iloc[-1]
            sma_50 = recent_history['Close'].rolling(window=50).mean().iloc[-1] if len(recent_history) >= 50 else sma_20
            
            # Calculate price performance metrics
            ytd_performance = ((stock_data.current_price - stock_data.historical_data['Close'].iloc[0]) / 
                             stock_data.historical_data['Close'].iloc[0]) * 100
            
            system_prompt = """You are a senior equity research analyst with 15+ years of experience at a top-tier investment bank. 
            Generate a comprehensive research report that institutional investors would use for investment decisions.

            Your report should include:
            1. Executive Summary with investment thesis and rating
            2. Company Overview and Business Analysis
            3. Financial Analysis with key metrics interpretation
            4. Competitive Position and Market Analysis
            5. Growth Drivers and Investment Catalysts
            6. Risk Factors and Challenges
            7. Valuation Analysis with price target
            8. Investment Recommendation with rationale

            Be analytical, data-driven, and provide specific insights that justify your recommendation.
            Use professional financial language but keep it accessible.
            """
            
            user_prompt = f"""
            Generate a comprehensive equity research report for {stock_data.company_name} ({symbol}).

            FINANCIAL DATA:
            - Current Price: ${stock_data.current_price:.2f}
            - Market Cap: ${stock_data.market_cap:,.0f}
            - P/E Ratio: {stock_data.pe_ratio:.1f}
            - EPS (Forward): ${stock_data.eps:.2f}
            - Revenue (TTM): ${stock_data.revenue:,.0f}
            - Profit Margin: {stock_data.profit_margin*100:.1f}%
            - Debt-to-Equity: {stock_data.debt_to_equity:.2f}
            - Return on Equity: {stock_data.return_on_equity*100:.1f}%
            - Price-to-Book: {stock_data.price_to_book:.2f}
            - Dividend Yield: {stock_data.dividend_yield*100:.2f}%
            - Beta: {stock_data.beta:.2f}
            - 52-Week Range: ${stock_data.fifty_two_week_low:.2f} - ${stock_data.fifty_two_week_high:.2f}

            TECHNICAL ANALYSIS:
            - 20-Day SMA: ${sma_20:.2f}
            - 50-Day SMA: ${sma_50:.2f}
            - YTD Performance: {ytd_performance:.1f}%
            - Average Volume: {stock_data.average_volume:,.0f}

            PEER COMPARISON:
            {json.dumps(peer_data, indent=2)}

            REPORT REQUIREMENTS:
            - Target length: 2000-3000 words
            - Include specific price target with methodology
            - Provide clear BUY/HOLD/SELL recommendation
            - Support all assertions with data
            - Include risk assessment and scenario analysis
            - Date the report: {datetime.now().strftime('%B %d, %Y')}
            """
            
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=4000
            )
            
            report_content = response.choices[0].message.content
            
            # Generate investment highlights
            highlights_prompt = f"""
            Based on the research report for {symbol}, extract 5-7 key investment highlights as bullet points.
            Focus on the most compelling reasons to invest or avoid this stock.
            
            Research Report:
            {report_content[:1500]}...
            """
            
            highlights_response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model="gpt-4-turbo-preview",
                messages=[{"role": "user", "content": highlights_prompt}],
                temperature=0.2,
                max_tokens=500
            )
            
            investment_highlights = highlights_response.choices[0].message.content
            
            # Extract rating and price target from the report
            rating_prompt = f"""
            From this research report, extract the investment rating (BUY/HOLD/SELL) and price target.
            Return as JSON: {{"rating": "BUY/HOLD/SELL", "price_target": number, "current_price": {stock_data.current_price}}}
            
            Report: {report_content[-800:]}
            """
            
            rating_response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model="gpt-4-turbo-preview",
                messages=[{"role": "user", "content": rating_prompt}],
                temperature=0.1,
                max_tokens=200
            )
            
            try:
                rating_data = json.loads(rating_response.choices[0].message.content)
            except:
                rating_data = {
                    "rating": "HOLD",
                    "price_target": stock_data.current_price * 1.1,
                    "current_price": stock_data.current_price
                }
            
            # Compile final report
            research_report = {
                "symbol": symbol,
                "company_name": stock_data.company_name,
                "report_date": datetime.now().isoformat(),
                "analyst_rating": rating_data.get("rating", "HOLD"),
                "price_target": float(rating_data.get("price_target", stock_data.current_price * 1.1)),
                "current_price": stock_data.current_price,
                "upside_potential": ((float(rating_data.get("price_target", stock_data.current_price * 1.1)) - stock_data.current_price) / stock_data.current_price) * 100,
                "investment_highlights": investment_highlights,
                "full_report": report_content,
                "key_metrics": {
                    "market_cap": stock_data.market_cap,
                    "pe_ratio": stock_data.pe_ratio,
                    "eps": stock_data.eps,
                    "profit_margin": stock_data.profit_margin,
                    "roe": stock_data.return_on_equity,
                    "debt_to_equity": stock_data.debt_to_equity,
                    "dividend_yield": stock_data.dividend_yield,
                    "beta": stock_data.beta,
                    "ytd_performance": ytd_performance
                },
                "peer_comparison": peer_data,
                "report_type": report_type,
                "word_count": len(report_content.split())
            }
            
            return research_report
            
        except Exception as e:
            logger.error(f"Error generating research report for {symbol}: {e}")
            raise

async def test_research_report_generation():
    """Test the research report generator with concrete examples"""
    
    print("🔬 Finance-Bro Deep Research Report Generator Test")
    print("="*60)
    
    generator = DeepResearchReportGenerator()
    test_symbols = ["AAPL", "MSFT", "GOOGL"]
    
    results = {}
    
    for symbol in test_symbols:
        print(f"\n📊 Generating research report for {symbol}...")
        
        try:
            start_time = datetime.now()
            report = await generator.generate_research_report(symbol, "comprehensive")
            end_time = datetime.now()
            
            duration = (end_time - start_time).total_seconds()
            
            results[symbol] = {
                "status": "success",
                "report": report,
                "generation_time": duration
            }
            
            print(f"✅ {symbol} Research Report Generated Successfully")
            print(f"   - Rating: {report['analyst_rating']}")
            print(f"   - Price Target: ${report['price_target']:.2f}")
            print(f"   - Current Price: ${report['current_price']:.2f}")
            print(f"   - Upside Potential: {report['upside_potential']:.1f}%")
            print(f"   - Report Length: {report['word_count']} words")
            print(f"   - Generation Time: {duration:.1f} seconds")
            
        except Exception as e:
            results[symbol] = {
                "status": "error",
                "error": str(e)
            }
            print(f"❌ {symbol} Research Report Failed: {e}")
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f"research_reports_test_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Summary
    successful = sum(1 for r in results.values() if r["status"] == "success")
    total = len(results)
    
    print(f"\n{'='*60}")
    print("📈 RESEARCH REPORT GENERATION SUMMARY")
    print(f"{'='*60}")
    print(f"Total Stocks Analyzed: {total}")
    print(f"Successful Reports: {successful}")
    print(f"Success Rate: {successful/total*100:.1f}%")
    print(f"Results saved to: {results_file}")
    
    if successful > 0:
        avg_time = sum(r.get("generation_time", 0) for r in results.values() if r["status"] == "success") / successful
        avg_words = sum(r.get("report", {}).get("word_count", 0) for r in results.values() if r["status"] == "success") / successful
        print(f"Average Generation Time: {avg_time:.1f} seconds")
        print(f"Average Report Length: {avg_words:.0f} words")
    
    return results

if __name__ == "__main__":
    results = asyncio.run(test_research_report_generation())
    
    # Show sample report excerpt
    for symbol, result in results.items():
        if result["status"] == "success":
            report = result["report"]
            print(f"\n{'='*60}")
            print(f"📋 SAMPLE REPORT EXCERPT - {symbol}")
            print(f"{'='*60}")
            print(f"Company: {report['company_name']}")
            print(f"Rating: {report['analyst_rating']}")
            print(f"Price Target: ${report['price_target']:.2f} (Current: ${report['current_price']:.2f})")
            print(f"\nInvestment Highlights:")
            print(report['investment_highlights'][:500] + "...")
            print(f"\nReport Preview:")
            print(report['full_report'][:800] + "...")
            break