"""
Comprehensive Finance Bro API Server
This module provides all the API endpoints needed by the frontend components.
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
import json
import logging
from contextlib import asynccontextmanager

# Import backend services
from src.EventAgent.portfolio_manager import get_portfolio_manager, PortfolioAnalysis
from src.EventAgent.financial_data_service import get_financial_service, StockData, NewsArticle
from src.EventAgent.tools_and_schemas import (
    get_stock_price, get_market_news, get_portfolio_metrics,
    add_portfolio_position, remove_portfolio_position,
    execute_trading_signal, get_trading_status,
    calculate_technical_indicators, analyze_market_sentiment,
    get_economic_calendar, analyze_time_series,
    update_risk_parameters as backend_update_risk_parameters,
    emergency_trading_stop
)

# Import TS Agent
try:
    from src.ts_agent.api import router as ts_router
    TS_AGENT_AVAILABLE = True
except ImportError as e:
    logger.warning(f"TS Agent not available: {e}")
    TS_AGENT_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Request/Response Models
class AnalysisRequest(BaseModel):
    message: str
    portfolio_data: Dict[str, Any] = {}
    risk_tolerance: str = "moderate"
    investment_horizon: str = "medium"

class AnalysisResponse(BaseModel):
    analysis: str
    market_events: List[Dict[str, Any]]
    trading_signals: List[Dict[str, Any]]
    portfolio_recommendations: List[Dict[str, Any]]

class TradeRequest(BaseModel):
    symbol: str
    action: str = Field(..., pattern="^(BUY|SELL)$")
    quantity: float = Field(..., gt=0)
    order_type: str = Field(default="MARKET", pattern="^(MARKET|LIMIT|STOP)$")
    price: Optional[float] = None
    stop_price: Optional[float] = None

class TradeResponse(BaseModel):
    order_id: str
    status: str
    message: str
    symbol: str
    action: str
    quantity: float
    filled_quantity: float
    average_price: float
    timestamp: datetime

class PortfolioSummary(BaseModel):
    total_value: float
    cash_balance: float
    invested_capital: float
    total_pnl: float
    total_pnl_percent: float
    positions_count: int
    daily_change: float
    daily_change_percent: float

class Position(BaseModel):
    symbol: str
    quantity: float
    average_cost: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_percent: float
    sector: Optional[str] = None

class NewsRequest(BaseModel):
    search_query: Optional[str] = None
    category: Optional[str] = None
    bookmarked_only: bool = False
    limit: int = Field(default=10, le=50)

class BookmarkRequest(BaseModel):
    article_id: str
    bookmarked: bool

class AgentMode(BaseModel):
    mode: str = Field(..., pattern="^(aggressive|conservative|balanced)$")

class RiskParametersUpdate(BaseModel):
    max_position_size_pct: Optional[float] = Field(None, ge=0.01, le=1.0)
    stop_loss_pct: Optional[float] = Field(None, ge=0.01, le=0.5)
    take_profit_pct: Optional[float] = Field(None, ge=0.05, le=2.0)
    max_daily_loss_pct: Optional[float] = Field(None, ge=0.01, le=0.2)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New WebSocket connection. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                disconnected.append(connection)
        
        # Remove disconnected connections
        for conn in disconnected:
            self.disconnect(conn)

# Global instances
manager = ConnectionManager()
_bookmarked_articles = set()  # Simple in-memory bookmark storage
_agent_thoughts = []  # Simple in-memory agent thoughts storage

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    logger.info("Starting Finance Bro API Server...")
    
    # Start background tasks
    market_data_task = asyncio.create_task(broadcast_market_updates())
    agent_thoughts_task = asyncio.create_task(broadcast_agent_thoughts())
    
    yield
    
    # Cleanup
    market_data_task.cancel()
    agent_thoughts_task.cancel()
    logger.info("Finance Bro API Server shutting down...")

# Create FastAPI app
app = FastAPI(
    title="Finance Bro API",
    description="Comprehensive API for financial analysis and trading",
    version="2.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include TS Agent router if available
if TS_AGENT_AVAILABLE:
    app.include_router(ts_router)
    logger.info("TS Agent endpoints available at /ts/*")
else:
    logger.warning("TS Agent endpoints not available")

# Background tasks for real-time data
async def broadcast_market_updates():
    """Broadcast market data updates to connected clients."""
    while True:
        try:
            # Get sample market data
            symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]
            market_data = {}
            
            for symbol in symbols:
                try:
                    stock_data = await get_stock_price.ainvoke({"symbol": symbol})
                    market_data[symbol] = stock_data
                except Exception as e:
                    logger.error(f"Error getting data for {symbol}: {e}")
                    # Fallback mock data
                    market_data[symbol] = {
                        "symbol": symbol,
                        "price": 150.0,
                        "change": 2.5,
                        "change_percent": 1.7,
                        "volume": 1000000
                    }
            
            # Broadcast to all connected clients
            await manager.broadcast(json.dumps({
                "type": "market_update",
                "data": market_data,
                "timestamp": datetime.now().isoformat()
            }))
            
            await asyncio.sleep(5)  # Update every 5 seconds
        except Exception as e:
            logger.error(f"Error in market data broadcast: {e}")
            await asyncio.sleep(10)

async def broadcast_agent_thoughts():
    """Broadcast agent thoughts to connected clients."""
    while True:
        try:
            # Simulate agent thoughts
            thoughts = [
                "Analyzing market volatility patterns...",
                "Evaluating portfolio diversification metrics...",
                "Monitoring economic indicators for trading signals...",
                "Scanning news sentiment for market opportunities...",
                "Calculating optimal position sizing...",
                "Reviewing risk management parameters..."
            ]
            
            import random
            thought = {
                "id": f"thought_{len(_agent_thoughts) + 1}",
                "timestamp": datetime.now().isoformat(),
                "type": "analysis",
                "content": random.choice(thoughts),
                "confidence": round(random.uniform(0.6, 0.95), 2)
            }
            
            _agent_thoughts.append(thought)
            if len(_agent_thoughts) > 100:  # Keep only last 100 thoughts
                _agent_thoughts.pop(0)
            
            await manager.broadcast(json.dumps({
                "type": "agent_thought",
                "data": thought
            }))
            
            await asyncio.sleep(random.randint(3, 8))  # Random interval
        except Exception as e:
            logger.error(f"Error in agent thoughts broadcast: {e}")
            await asyncio.sleep(10)

# Health and Config endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/config")
async def get_configuration():
    """Get current configuration."""
    return {
        "model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 2000,
        "features": ["analysis", "signals", "portfolio_recommendations", "real_time_data"],
        "version": "2.0.0",
        "backend_services": {
            "portfolio_manager": "active",
            "financial_data_service": "active", 
            "trading_agent": "active",
            "websocket_support": "active"
        }
    }

# Main Analysis endpoint (existing functionality)
@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_market_events(request: AnalysisRequest):
    """Analyze market events and generate trading recommendations."""
    try:
        # Mock analysis response with more sophisticated content
        analysis = f"""
Based on your query: "{request.message}"

## Comprehensive Market Analysis

### Current Market Overview
- Market sentiment: Cautiously optimistic with moderate volatility
- Your risk profile: {request.risk_tolerance} with {request.investment_horizon} investment horizon
- Key sectors showing strength: Technology, Healthcare, Clean Energy
- Recommended strategy: Diversified approach with tactical allocations

### Technical Analysis Summary
- S&P 500: Trading above 50-day MA, showing bullish momentum
- VIX levels: Moderate at 18-22 range, indicating normal market stress
- Bond yields: Stabilizing after recent volatility
- Dollar strength: Moderate, supporting international diversification

### Investment Strategy Recommendations
1. **Core Holdings (60-70%)**: Broad market ETFs (VTI, VXUS)
2. **Growth Allocation (20-25%)**: Technology and innovation sectors
3. **Defensive Allocation (10-15%)**: Utilities, consumer staples, REITs
4. **Cash Reserve**: Maintain 5-10% for opportunities

### Risk Management Guidelines
- Position sizing: Maximum 5% per individual stock
- Stop-loss levels: 8-12% below entry points
- Rebalancing frequency: Quarterly review, threshold-based execution
- Diversification: Minimum 15-20 holdings across sectors

### Economic Calendar Awareness
- Fed policy meetings: Monitor for rate guidance
- Earnings season: Focus on quality companies with pricing power
- Geopolitical events: Maintain defensive positioning during uncertainty
        """

        # Get real market data for events
        market_events = []
        try:
            economic_data = await get_economic_calendar(7)
            for event in economic_data[:3]:  # Top 3 events
                market_events.append({
                    "title": event["indicator_name"],
                    "description": f"Scheduled release: {event['indicator_name']} - Previous: {event.get('previous_value', 'N/A')}",
                    "impact": "high" if event.get("importance") == "HIGH" else "medium",
                    "timestamp": event["release_date"]
                })
        except Exception as e:
            logger.error(f"Error fetching economic data: {e}")
            # Fallback mock events
            market_events = [
                {
                    "title": "Federal Reserve Policy Update",
                    "description": "Fed maintains current interest rates, signals data-dependent approach",
                    "impact": "neutral",
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "title": "Tech Sector Earnings Season",
                    "description": "Major technology companies reporting strong quarterly results",
                    "impact": "positive", 
                    "timestamp": datetime.now().isoformat()
                }
            ]

        # Generate trading signals based on technical analysis
        trading_signals = []
        symbols = ["SPY", "QQQ", "VTI", "IWM"]
        for symbol in symbols:
            try:
                stock_data = await get_stock_price(symbol)
                technical_data = await calculate_technical_indicators(symbol, ["RSI", "MACD"])
                
                # Determine signal based on technical indicators
                rsi_signal = "NEUTRAL"
                confidence = 0.6
                
                for indicator in technical_data:
                    if indicator["indicator_type"] == "RSI":
                        if indicator["value"] < 30:
                            rsi_signal = "BUY"
                            confidence = 0.8
                        elif indicator["value"] > 70:
                            rsi_signal = "SELL"
                            confidence = 0.75
                
                trading_signals.append({
                    "symbol": symbol,
                    "action": rsi_signal,
                    "confidence": confidence,
                    "current_price": stock_data["price"],
                    "reasoning": f"Technical analysis suggests {rsi_signal} signal based on RSI and momentum indicators"
                })
            except Exception as e:
                logger.error(f"Error generating signal for {symbol}: {e}")

        # Generate portfolio recommendations
        try:
            portfolio_data = await get_portfolio_metrics({})
            recommendations = [
                {
                    "title": "Portfolio Diversification",
                    "description": f"Current diversification score: {portfolio_data.get('diversification_score', 0.7):.1%}. " +
                                 ("Consider adding international exposure." if portfolio_data.get('diversification_score', 0.7) < 0.8 else "Well diversified portfolio.")
                },
                {
                    "title": "Risk Management Review",
                    "description": f"Portfolio volatility: {portfolio_data.get('risk_metrics', {}).get('volatility', 0.15):.1%}. " +
                                 "Review position sizes and consider rebalancing if any single holding exceeds 5%."
                },
                {
                    "title": "Performance Optimization",
                    "description": f"Current Sharpe ratio: {portfolio_data.get('risk_metrics', {}).get('sharpe_ratio', 1.2):.2f}. " +
                                 "Focus on quality companies with sustainable competitive advantages."
                }
            ]
        except Exception as e:
            logger.error(f"Error generating portfolio recommendations: {e}")
            recommendations = [
                {
                    "title": "Portfolio Diversification",
                    "description": "Consider adding international exposure through VXUS or similar ETF"
                },
                {
                    "title": "Risk Management",
                    "description": "Review position sizes to ensure no single holding exceeds 5% of portfolio"
                }
            ]

        return AnalysisResponse(
            analysis=analysis.strip(),
            market_events=market_events,
            trading_signals=trading_signals,
            portfolio_recommendations=recommendations
        )
        
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

# Portfolio Management APIs
@app.get("/portfolio/summary", response_model=PortfolioSummary)
async def get_portfolio_summary():
    """Get portfolio summary information."""
    try:
        portfolio_manager = get_portfolio_manager()
        portfolio_data = await get_portfolio_metrics({})
        
        # Calculate daily change (mock for now)
        daily_change = portfolio_data.get("total_value", 0) * 0.012  # 1.2% mock daily change
        daily_change_percent = 1.2
        
        return PortfolioSummary(
            total_value=portfolio_data.get("total_value", 100000.0),
            cash_balance=portfolio_data.get("cash_balance", 5000.0),
            invested_capital=portfolio_data.get("invested_capital", 95000.0),
            total_pnl=portfolio_data.get("total_pnl", 2500.0),
            total_pnl_percent=portfolio_data.get("daily_pnl_percent", 2.6),
            positions_count=len(portfolio_data.get("positions", [])),
            daily_change=daily_change,
            daily_change_percent=daily_change_percent
        )
    except Exception as e:
        logger.error(f"Portfolio summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/portfolio/positions")
async def get_portfolio_positions():
    """Get detailed portfolio positions."""
    try:
        portfolio_data = await get_portfolio_metrics({})
        positions = portfolio_data.get("positions", [])
        
        return {
            "positions": positions,
            "total_positions": len(positions),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Portfolio positions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/portfolio/metrics")
async def get_detailed_portfolio_metrics():
    """Get comprehensive portfolio metrics."""
    try:
        portfolio_data = await get_portfolio_metrics({})
        return {
            "metrics": portfolio_data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Portfolio metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/portfolio/positions")
async def add_position(symbol: str, quantity: float, price: float, sector: Optional[str] = None):
    """Add a new position to the portfolio."""
    try:
        result = await add_portfolio_position(symbol, quantity, price, sector)
        return result
    except Exception as e:
        logger.error(f"Add position error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/portfolio/positions/{symbol}")
async def remove_position(symbol: str, quantity: float, price: float):
    """Remove or reduce a position in the portfolio."""
    try:
        result = await remove_portfolio_position(symbol, quantity, price)
        return result
    except Exception as e:
        logger.error(f"Remove position error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Market Data APIs
@app.get("/market/quotes")
async def get_market_quotes(symbols: str):
    """Get stock quotes for multiple symbols."""
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(",")]
        quotes = {}
        
        for symbol in symbol_list:
            stock_data = await get_stock_price(symbol)
            quotes[symbol] = stock_data
        
        return {
            "quotes": quotes,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Market quotes error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/market/trends")
async def get_market_trends():
    """Get market trend analysis."""
    try:
        # Mock trend data - in real implementation, this would analyze actual market data
        trends = [
            {
                "symbol": "SPY",
                "change": 12.5,
                "changePercent": 2.8,
                "sentiment": "bullish",
                "newsCount": 15,
                "volume": 50000000
            },
            {
                "symbol": "QQQ", 
                "change": 8.2,
                "changePercent": 2.1,
                "sentiment": "bullish",
                "newsCount": 12,
                "volume": 35000000
            },
            {
                "symbol": "IWM",
                "change": -2.1,
                "changePercent": -1.2,
                "sentiment": "bearish", 
                "newsCount": 8,
                "volume": 25000000
            }
        ]
        
        return {
            "trends": trends,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Market trends error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/market/sentiment")
async def get_market_sentiment():
    """Get overall market sentiment analysis."""
    try:
        sentiment_data = await analyze_market_sentiment()
        
        # Add percentage breakdown for frontend
        sentiment_percentages = {
            "bullish": 45.0,
            "neutral": 35.0,
            "bearish": 20.0
        }
        
        sentiment_data["sentiment_breakdown"] = sentiment_percentages
        return sentiment_data
    except Exception as e:
        logger.error(f"Market sentiment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# News APIs
@app.get("/news/feed")
async def get_news_feed(
    search_query: Optional[str] = None,
    category: Optional[str] = None,
    bookmarked_only: bool = False,
    limit: int = 10
):
    """Get financial news feed."""
    try:
        if bookmarked_only:
            # Return only bookmarked articles
            # This is a mock implementation - in reality, you'd filter from a database
            articles = []
            for i, article_id in enumerate(list(_bookmarked_articles)[:limit]):
                articles.append({
                    "id": article_id,
                    "title": f"Bookmarked Article {i+1}",
                    "summary": "This is a bookmarked financial news article.",
                    "source": "Financial News",
                    "publishedAt": (datetime.now() - timedelta(hours=i)).isoformat(),
                    "url": f"https://example.com/news/{article_id}",
                    "sentiment": "neutral",
                    "relevanceScore": 0.8,
                    "category": "market",
                    "symbols": ["SPY", "QQQ"],
                    "isBookmarked": True,
                    "readCount": 150 + i * 10
                })
        else:
            # Get regular news feed
            symbols = search_query.split(",") if search_query else None
            news_articles = await get_market_news(symbols, 24, limit)
            
            articles = []
            for i, article in enumerate(news_articles):
                article_id = f"article_{i+1}_{int(datetime.now().timestamp())}"
                articles.append({
                    "id": article_id,
                    "title": article["title"],
                    "summary": article["description"],
                    "source": article["source"],
                    "publishedAt": article["published_at"],
                    "url": article["url"],
                    "sentiment": article.get("sentiment", "neutral"),
                    "relevanceScore": article.get("relevance_score", 0.7),
                    "category": category or "general",
                    "symbols": symbols or ["SPY"],
                    "isBookmarked": article_id in _bookmarked_articles,
                    "readCount": 100 + i * 20
                })
        
        return {
            "articles": articles,
            "total": len(articles),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"News feed error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/news/bookmark")
async def manage_bookmark(request: BookmarkRequest):
    """Add or remove article bookmark."""
    try:
        if request.bookmarked:
            _bookmarked_articles.add(request.article_id)
            message = "Article bookmarked successfully"
        else:
            _bookmarked_articles.discard(request.article_id)
            message = "Article bookmark removed"
        
        return {
            "success": True,
            "message": message,
            "article_id": request.article_id,
            "bookmarked": request.bookmarked,
            "total_bookmarks": len(_bookmarked_articles)
        }
    except Exception as e:
        logger.error(f"Bookmark error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Trading APIs
@app.post("/trades/execute", response_model=TradeResponse)
async def execute_trade(request: TradeRequest):
    """Execute a trading order."""
    try:
        # Prepare signal data for execution
        signal_data = {
            "symbol": request.symbol,
            "action": request.action,
            "quantity": request.quantity,
            "order_type": request.order_type,
            "price": request.price,
            "stop_price": request.stop_price
        }
        
        # Execute the trade (in simulation mode by default for safety)
        execution_result = await execute_trading_signal(signal_data, enable_execution=False)
        
        # Generate order ID and response
        order_id = f"ord_{request.symbol}_{int(datetime.now().timestamp())}"
        
        return TradeResponse(
            order_id=order_id,
            status="submitted" if execution_result.get("success", True) else "rejected",
            message=execution_result.get("message", "Order submitted for processing"),
            symbol=request.symbol,
            action=request.action,
            quantity=request.quantity,
            filled_quantity=execution_result.get("filled_quantity", 0),
            average_price=execution_result.get("average_price", request.price or 0),
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"Trade execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trades/history")
async def get_trading_history(limit: int = 50):
    """Get trading history."""
    try:
        portfolio_manager = get_portfolio_manager()
        transactions = portfolio_manager.transactions[-limit:]  # Get last N transactions
        
        trades = []
        for txn in transactions:
            trades.append({
                "id": txn.transaction_id,
                "symbol": txn.symbol,
                "action": txn.action,
                "quantity": txn.quantity,
                "price": txn.price,
                "timestamp": txn.timestamp.isoformat(),
                "status": "filled",
                "fees": txn.fees,
                "notes": txn.notes
            })
        
        return {
            "trades": trades,
            "total": len(trades),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Trading history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trades/status/{order_id}")
async def get_trade_status(order_id: str):
    """Get status of a specific trade order."""
    try:
        # Mock trade status - in real implementation, would query order management system
        return {
            "order_id": order_id,
            "status": "filled",
            "filled_quantity": 100,
            "remaining_quantity": 0,
            "average_price": 150.25,
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Trade status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Agent Management APIs
@app.get("/agent/status")
async def get_agent_status():
    """Get current trading agent status."""
    try:
        trading_status = await get_trading_status()
        portfolio_data = await get_portfolio_metrics({})
        
        return {
            "isActive": True,
            "mode": "balanced",
            "balance": portfolio_data.get("cash_balance", 10000),
            "buyingPower": portfolio_data.get("cash_balance", 10000) * 4,  # Mock 4:1 leverage
            "dailyPnL": portfolio_data.get("total_pnl", 0) * 0.1,  # Mock daily P&L
            "totalTrades": len(portfolio_data.get("positions", [])),
            "successRate": 68.5,  # Mock success rate
            "lastAction": datetime.now().isoformat(),
            "status": "active",
            "trading_status": trading_status
        }
    except Exception as e:
        logger.error(f"Agent status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/start")
async def start_agent():
    """Start the trading agent."""
    try:
        return {
            "success": True,
            "message": "Trading agent started",
            "status": "active",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Agent start error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/stop")
async def stop_agent():
    """Stop the trading agent."""
    try:
        stop_result = await emergency_trading_stop()
        return {
            "success": True,
            "message": "Trading agent stopped",
            "status": "inactive",
            "emergency_stop_result": stop_result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Agent stop error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/agent/mode")
async def update_agent_mode(request: AgentMode):
    """Update trading agent mode."""
    try:
        return {
            "success": True,
            "message": f"Agent mode updated to {request.mode}",
            "mode": request.mode,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Agent mode update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agent/thoughts")
async def get_agent_thoughts():
    """Get recent agent thoughts and decisions."""
    try:
        return {
            "thoughts": _agent_thoughts[-20:],  # Last 20 thoughts
            "total": len(_agent_thoughts),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Agent thoughts error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/agent/riOPENAI_API_KEY_REDACTED")
async def update_risk_parameters(request: RiskParametersUpdate):
    """Update risk management parameters."""
    try:
        # Convert the request to the format expected by the backend
        params = {}
        if request.max_position_size_pct is not None:
            params["max_position_size_pct"] = request.max_position_size_pct
        if request.stop_loss_pct is not None:
            params["stop_loss_pct"] = request.stop_loss_pct
        if request.take_profit_pct is not None:
            params["take_profit_pct"] = request.take_profit_pct
        if request.max_daily_loss_pct is not None:
            params["max_daily_loss_pct"] = request.max_daily_loss_pct
        
        # Update the risk parameters
        result = await backend_update_risk_parameters(**params)
        return result
    except Exception as e:
        logger.error(f"Risk parameters update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Rewards System APIs
@app.get("/rewards/achievements")
async def get_achievements():
    """Get trading achievements and rewards."""
    try:
        portfolio_data = await get_portfolio_metrics({})
        
        # Generate achievements based on portfolio performance
        achievements = [
            {
                "id": "first_trade",
                "title": "First Steps",
                "description": "Executed your first trade",
                "points": 100,
                "type": "milestone",
                "unlockedAt": (datetime.now() - timedelta(days=30)).isoformat(),
                "icon": "🎯"
            },
            {
                "id": "portfolio_growth",
                "title": "Growth Master",
                "description": "Portfolio gained 10% in value",
                "points": 500,
                "type": "performance",
                "unlockedAt": (datetime.now() - timedelta(days=7)).isoformat(),
                "icon": "📈"
            },
            {
                "id": "diversification",
                "title": "Risk Manager",
                "description": "Maintained well-diversified portfolio",
                "points": 250,
                "type": "achievement",
                "unlockedAt": datetime.now().isoformat(),
                "icon": "🛡️"
            }
        ]
        
        return {
            "achievements": achievements,
            "total_points": sum(a["points"] for a in achievements),
            "total_achievements": len(achievements),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Achievements error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rewards/metrics")
async def get_reward_metrics():
    """Get performance metrics for rewards calculation."""
    try:
        portfolio_data = await get_portfolio_metrics({})
        
        metrics = [
            {
                "id": "sharpe_ratio",
                "title": "RiOPENAI_API_KEY_REDACTED Returns",
                "value": portfolio_data.get("risk_metrics", {}).get("sharpe_ratio", 1.2),
                "target": 1.5,
                "unit": "ratio",
                "trend": "up",
                "score": 85,
                "description": "Measures return per unit of risk",
                "suggestions": ["Focus on quality stocks", "Reduce portfolio volatility"]
            },
            {
                "id": "diversification_score", 
                "title": "Portfolio Diversification",
                "value": portfolio_data.get("diversification_score", 0.75),
                "target": 0.85,
                "unit": "score",
                "trend": "stable",
                "score": 75,
                "description": "Measures how well-diversified your portfolio is",
                "suggestions": ["Add international exposure", "Consider more sectors"]
            },
            {
                "id": "alpha_generation",
                "title": "Alpha Generation",
                "value": 2.3,
                "target": 3.0,
                "unit": "percent",
                "trend": "up",
                "score": 78,
                "description": "Excess return over market benchmark",
                "suggestions": ["Focus on undervalued stocks", "Improve timing"]
            }
        ]
        
        return {
            "metrics": metrics,
            "overall_score": sum(m["score"] for m in metrics) / len(metrics),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Reward metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Deep Research APIs
@app.get("/research/deep-analysis")
async def get_deep_analysis(query: str, symbols: Optional[str] = None):
    """Get comprehensive deep research analysis."""
    try:
        symbol_list = symbols.split(",") if symbols else ["SPY"]
        
        # Mock deep research analysis
        analysis = {
            "query": query,
            "symbols": symbol_list,
            "analysis": f"""
# Deep Research Analysis: {query}

## Executive Summary
Based on comprehensive analysis of {', '.join(symbol_list)}, our research indicates moderate to strong investment potential with several key considerations.

## Fundamental Analysis
- **Financial Health**: Strong balance sheets with solid cash positions
- **Revenue Growth**: Consistent growth trajectory over past 3 years
- **Profitability**: Improving margins and operational efficiency
- **Competitive Position**: Market leaders with sustainable advantages

## Technical Analysis
- **Trend Analysis**: Upward trending with key support levels
- **Momentum Indicators**: Bullish momentum with RSI in healthy range
- **Volume Analysis**: Institutional accumulation patterns observed

## Risk Assessment
- **Market Risk**: Moderate exposure to systematic risk
- **Sector Risk**: Diversified across defensive and growth sectors
- **Liquidity Risk**: High liquidity with tight bid-ask spreads
- **Concentration Risk**: Well-distributed holdings

## Investment Thesis
1. **Growth Potential**: Multiple expansion opportunities identified
2. **Defensive Characteristics**: Stable cash flows and dividend history
3. **Valuation**: Trading at reasonable multiples vs. historical averages
4. **Catalysts**: Upcoming earnings and product launches

## Recommendation
**BUY** with target allocation of 3-5% of portfolio. Implement dollar-cost averaging over 2-3 month period.
            """,
            "confidence": 0.82,
            "sources": [
                "SEC filings and financial statements",
                "Industry reports and analyst coverage", 
                "Technical analysis and market data",
                "Economic indicators and macro trends"
            ],
            "last_updated": datetime.now().isoformat()
        }
        
        return analysis
    except Exception as e:
        logger.error(f"Deep analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/research/symbols/{symbol}")
async def get_symbol_research(symbol: str):
    """Get research analysis for a specific symbol."""
    try:
        # Get stock data and technical analysis
        stock_data = await get_stock_price(symbol)
        technical_data = await calculate_technical_indicators(symbol, ["RSI", "MACD", "SMA"])
        
        research = {
            "symbol": symbol,
            "current_price": stock_data["price"],
            "price_change": stock_data["change"],
            "price_change_percent": stock_data["change_percent"],
            "technical_indicators": technical_data,
            "analyst_rating": "BUY",
            "target_price": stock_data["price"] * 1.15,
            "support_level": stock_data["price"] * 0.95,
            "resistance_level": stock_data["price"] * 1.08,
            "research_summary": f"""
## {symbol} Research Summary

### Current Situation
- **Price**: ${stock_data['price']:.2f} ({stock_data['change']:+.2f}, {stock_data['change_percent']:+.1f}%)
- **Volume**: {stock_data['volume']:,} shares

### Key Metrics
- **Market Cap**: $XXX billion
- **P/E Ratio**: XX.X
- **Dividend Yield**: X.X%
- **Beta**: X.XX

### Investment Highlights
1. Strong fundamentals with consistent earnings growth
2. Market leader in its sector with competitive advantages
3. Solid balance sheet and cash generation
4. Positive analyst sentiment and price target revisions

### Risks to Consider
- Market volatility and sector rotation risks
- Regulatory changes and competitive pressures
- Macroeconomic headwinds affecting demand

### Recommendation
Suitable for growth-oriented portfolios with moderate risk tolerance.
            """,
            "last_updated": datetime.now().isoformat()
        }
        
        return research
    except Exception as e:
        logger.error(f"Symbol research error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoints
@app.websocket("/ws/market/realtime")
async def websocket_market_data(websocket: WebSocket):
    """WebSocket for real-time market data."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and let background tasks send data
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.websocket("/ws/agent/thoughts")
async def websocket_agent_thoughts(websocket: WebSocket):
    """WebSocket for real-time agent thoughts."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and let background tasks send data
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Technical indicators endpoint
@app.get("/market/technical/{symbol}")
async def get_technical_indicators(symbol: str, indicators: str = "RSI,MACD,SMA"):
    """Get technical indicators for a symbol."""
    try:
        indicator_list = [i.strip() for i in indicators.split(",")]
        technical_data = await calculate_technical_indicators(symbol, indicator_list)
        
        return {
            "symbol": symbol,
            "indicators": technical_data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Technical indicators error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Time series analysis endpoint
@app.get("/market/analysis/{symbol}")
async def get_time_series_analysis(symbol: str, analysis_type: str = "trend", period_days: int = 90):
    """Get time series analysis for a symbol."""
    try:
        analysis_result = await analyze_time_series(symbol, analysis_type, period_days)
        return analysis_result
    except Exception as e:
        logger.error(f"Time series analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)