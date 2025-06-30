"""
Financial Data Service for integrating with various financial data providers.
This module provides a unified interface for accessing market data, news, and economic indicators.
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import aiohttp
from dataclasses import dataclass
from pydantic import BaseModel


@dataclass
class FinancialDataConfig:
    """Configuration for financial data providers."""
    alpha_vantage_api_key: Optional[str] = None
    polygon_api_key: Optional[str] = None
    news_api_key: Optional[str] = None
    fred_api_key: Optional[str] = None
    
    def __post_init__(self):
        """Load API keys from environment variables."""
        self.alpha_vantage_api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        self.polygon_api_key = os.getenv("POLYGON_API_KEY")
        self.news_api_key = os.getenv("NEWS_API_KEY")
        self.fred_api_key = os.getenv("FRED_API_KEY")


class StockData(BaseModel):
    """Stock price data model."""
    symbol: str
    price: float
    change: float
    change_percent: float
    volume: int
    timestamp: datetime
    open_price: float
    high_price: float
    low_price: float
    previous_close: float


class NewsArticle(BaseModel):
    """News article data model."""
    title: str
    description: str
    url: str
    source: str
    published_at: datetime
    sentiment: Optional[str] = None
    relevance_score: Optional[float] = None


class EconomicIndicator(BaseModel):
    """Economic indicator data model."""
    indicator_name: str
    value: float
    previous_value: Optional[float] = None
    forecast: Optional[float] = None
    release_date: datetime
    importance: str


class FinancialDataService:
    """Service for accessing financial data from multiple providers."""
    
    def __init__(self, config: FinancialDataConfig = None):
        """Initialize the financial data service."""
        self.config = config or FinancialDataConfig()
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def get_stock_quote(self, symbol: str) -> StockData:
        """Get real-time stock quote."""
        if self.config.alpha_vantage_api_key:
            return await self._get_alpha_vantage_quote(symbol)
        else:
            # Return mock data if no API key
            return self._get_mock_stock_data(symbol)
    
    async def get_stock_quotes(self, symbols: List[str]) -> List[StockData]:
        """Get multiple stock quotes."""
        tasks = [self.get_stock_quote(symbol) for symbol in symbols]
        return await asyncio.gather(*tasks)
    
    async def get_market_news(
        self, 
        symbols: Optional[List[str]] = None,
        hours_back: int = 24,
        limit: int = 10
    ) -> List[NewsArticle]:
        """Get market news articles."""
        if self.config.news_api_key:
            return await self._get_news_api_articles(symbols, hours_back, limit)
        else:
            # Return mock data if no API key
            return self._get_mock_news_data(symbols, limit)
    
    async def get_economic_calendar(self, days_ahead: int = 7) -> List[EconomicIndicator]:
        """Get upcoming economic events."""
        if self.config.fred_api_key:
            return await self._get_fred_data(days_ahead)
        else:
            # Return mock data if no API key
            return self._get_mock_economic_data(days_ahead)
    
    async def get_technical_indicators(
        self, 
        symbol: str, 
        indicators: List[str],
        period: int = 14
    ) -> Dict[str, Any]:
        """Calculate technical indicators."""
        if self.config.alpha_vantage_api_key:
            return await self._get_alpha_vantage_indicators(symbol, indicators, period)
        else:
            # Return mock data if no API key
            return self._get_mock_technical_data(symbol, indicators)
    
    async def analyze_market_sentiment(self) -> Dict[str, Any]:
        """Analyze overall market sentiment."""
        # This would integrate with sentiment analysis APIs
        return {
            "overall_sentiment": "neutral",
            "sentiment_score": 0.1,
            "confidence": 0.7,
            "timestamp": datetime.now(),
            "sources": ["news", "social_media", "analyst_ratings"],
            "breakdown": {
                "news": 0.05,
                "social_media": 0.15,
                "analyst_ratings": 0.0
            }
        }
    
    # Alpha Vantage API implementations
    async def _get_alpha_vantage_quote(self, symbol: str) -> StockData:
        """Get stock quote from Alpha Vantage."""
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": self.config.alpha_vantage_api_key
        }
        
        try:
            async with self.session.get(url, params=params) as response:
                data = await response.json()
                quote = data.get("Global Quote", {})
                
                return StockData(
                    symbol=symbol,
                    price=float(quote.get("05. price", 0)),
                    change=float(quote.get("09. change", 0)),
                    change_percent=float(quote.get("10. change percent", "0%").replace("%", "")),
                    volume=int(quote.get("06. volume", 0)),
                    timestamp=datetime.now(),
                    open_price=float(quote.get("02. open", 0)),
                    high_price=float(quote.get("03. high", 0)),
                    low_price=float(quote.get("04. low", 0)),
                    previous_close=float(quote.get("08. previous close", 0))
                )
        except Exception as e:
            print(f"Error fetching Alpha Vantage data: {e}")
            return self._get_mock_stock_data(symbol)
    
    async def _get_alpha_vantage_indicators(
        self, 
        symbol: str, 
        indicators: List[str], 
        period: int
    ) -> Dict[str, Any]:
        """Get technical indicators from Alpha Vantage."""
        results = {}
        
        for indicator in indicators:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": indicator.upper(),
                "symbol": symbol,
                "interval": "daily",
                "time_period": period,
                "apikey": self.config.alpha_vantage_api_key
            }
            
            try:
                async with self.session.get(url, params=params) as response:
                    data = await response.json()
                    technical_data = data.get(f"Technical Analysis: {indicator.upper()}", {})
                    
                    # Get the most recent value
                    if technical_data:
                        latest_date = max(technical_data.keys())
                        latest_value = technical_data[latest_date]
                        results[indicator] = {
                            "value": float(list(latest_value.values())[0]),
                            "timestamp": latest_date
                        }
            except Exception as e:
                print(f"Error fetching {indicator} from Alpha Vantage: {e}")
                results[indicator] = {"value": 50.0, "timestamp": datetime.now().isoformat()}
        
        return results
    
    # News API implementations
    async def _get_news_api_articles(
        self, 
        symbols: Optional[List[str]], 
        hours_back: int, 
        limit: int
    ) -> List[NewsArticle]:
        """Get news articles from News API."""
        url = "https://newsapi.org/v2/everything"
        
        # Build query
        query = "stock market finance"
        if symbols:
            query += " " + " OR ".join(symbols)
        
        params = {
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "from": (datetime.now() - timedelta(hours=hours_back)).isoformat(),
            "pageSize": limit,
            "apiKey": self.config.news_api_key
        }
        
        try:
            async with self.session.get(url, params=params) as response:
                data = await response.json()
                articles = []
                
                for article in data.get("articles", []):
                    articles.append(NewsArticle(
                        title=article["title"],
                        description=article["description"] or "",
                        url=article["url"],
                        source=article["source"]["name"],
                        published_at=datetime.fromisoformat(
                            article["publishedAt"].replace("Z", "+00:00")
                        )
                    ))
                
                return articles
        except Exception as e:
            print(f"Error fetching news data: {e}")
            return self._get_mock_news_data(symbols, limit)
    
    # FRED API implementations
    async def _get_fred_data(self, days_ahead: int) -> List[EconomicIndicator]:
        """Get economic data from FRED API."""
        # This would implement actual FRED API calls
        # For now, return mock data
        return self._get_mock_economic_data(days_ahead)
    
    # Mock data methods
    def _get_mock_stock_data(self, symbol: str) -> StockData:
        """Generate mock stock data."""
        import random
        base_price = random.uniform(50, 300)
        change = random.uniform(-5, 5)
        
        return StockData(
            symbol=symbol,
            price=base_price,
            change=change,
            change_percent=(change / base_price) * 100,
            volume=random.randint(100000, 10000000),
            timestamp=datetime.now(),
            open_price=base_price - random.uniform(-2, 2),
            high_price=base_price + random.uniform(0, 3),
            low_price=base_price - random.uniform(0, 3),
            previous_close=base_price - change
        )
    
    def _get_mock_news_data(self, symbols: Optional[List[str]], limit: int) -> List[NewsArticle]:
        """Generate mock news data."""
        articles = []
        for i in range(limit):
            symbol = symbols[i % len(symbols)] if symbols else "Market"
            articles.append(NewsArticle(
                title=f"{symbol} Stock Analysis - Market Update {i+1}",
                description=f"Latest analysis on {symbol} market performance and trends.",
                url=f"https://example.com/news/{i+1}",
                source="Financial News Network",
                published_at=datetime.now() - timedelta(hours=i)
            ))
        return articles
    
    def _get_mock_economic_data(self, days_ahead: int) -> List[EconomicIndicator]:
        """Generate mock economic data."""
        indicators = [
            "Non-Farm Payrolls",
            "GDP Growth Rate",
            "Inflation Rate",
            "Federal Funds Rate",
            "Unemployment Rate"
        ]
        
        data = []
        for i, indicator in enumerate(indicators):
            data.append(EconomicIndicator(
                indicator_name=indicator,
                value=0.0,  # Future event
                previous_value=2.5 + i * 0.5,
                forecast=2.7 + i * 0.5,
                release_date=datetime.now() + timedelta(days=i+1),
                importance="HIGH" if i < 2 else "MEDIUM"
            ))
        
        return data
    
    def _get_mock_technical_data(self, symbol: str, indicators: List[str]) -> Dict[str, Any]:
        """Generate mock technical indicator data."""
        import random
        results = {}
        
        for indicator in indicators:
            if indicator.upper() == "RSI":
                value = random.uniform(30, 70)
            elif indicator.upper() == "MACD":
                value = random.uniform(-1, 1)
            else:
                value = random.uniform(0, 100)
            
            results[indicator] = {
                "value": value,
                "timestamp": datetime.now().isoformat()
            }
        
        return results


# Singleton instance
_financial_service = None

async def get_financial_service() -> FinancialDataService:
    """Get the global financial data service instance."""
    global _financial_service
    if _financial_service is None:
        _financial_service = FinancialDataService()
    return _financial_service