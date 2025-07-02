"""
Working Finance Bro API Server
Simplified version with working endpoints for immediate frontend integration.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
import asyncio
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

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

class PortfolioSummary(BaseModel):
    total_value: float
    cash_balance: float
    invested_capital: float
    total_pnl: float
    total_pnl_percent: float
    positions_count: int
    daily_change: float
    daily_change_percent: float

# Create FastAPI app
app = FastAPI(
    title="Finance Bro API",
    description="Working API for financial analysis and trading",
    version="2.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data helpers
def get_mock_stock_data(symbol: str) -> Dict[str, Any]:
    """Generate realistic mock stock data."""
    import random
    base_price = random.uniform(50, 300)
    change = random.uniform(-5, 5)
    
    return {
        "symbol": symbol,
        "price": round(base_price, 2),
        "change": round(change, 2),
        "change_percent": round((change / base_price) * 100, 2),
        "volume": random.randint(100000, 10000000),
        "timestamp": datetime.now().isoformat(),
        "open": round(base_price - random.uniform(-2, 2), 2),
        "high": round(base_price + random.uniform(0, 3), 2),
        "low": round(base_price - random.uniform(0, 3), 2),
        "previous_close": round(base_price - change, 2)
    }

def get_mock_portfolio_data() -> Dict[str, Any]:
    """Generate mock portfolio data."""
    return {
        "total_value": 102500.0,
        "cash_balance": 7500.0,
        "invested_capital": 95000.0,
        "total_pnl": 2500.0,
        "total_pnl_percent": 2.6,
        "positions": [
            {
                "symbol": "AAPL",
                "quantity": 100,
                "current_price": 175.50,
                "market_value": 17550.0,
                "unrealized_pnl": 550.0,
                "unrealized_pnl_percent": 3.2,
                "sector": "Technology"
            },
            {
                "symbol": "MSFT",
                "quantity": 75,
                "current_price": 380.25,
                "market_value": 28518.75,
                "unrealized_pnl": 1200.0,
                "unrealized_pnl_percent": 4.4,
                "sector": "Technology"
            }
        ],
        "risk_metrics": {
            "sharpe_ratio": 1.45,
            "beta": 1.02,
            "volatility": 0.18,
            "max_drawdown": 0.08
        },
        "diversification_score": 0.78,
        "concentration_risk": 45.2,
        "rebalancing_needed": False
    }

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
            "trading_agent": "active"
        }
    }

# Initialize LLM
def get_llm():
    """Get LLM instance with proper configuration."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set")
    
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0.3,
        google_api_key=api_key
    )

# Main Analysis endpoint
@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_market_events(request: AnalysisRequest):
    """Analyze market events and generate trading recommendations using LLM."""
    try:
        # Initialize LLM
        llm = get_llm()
        
        # Create comprehensive analysis prompt
        analysis_prompt = f"""
You are a professional financial analyst and investment advisor. Provide a comprehensive market analysis based on the following user query:

USER QUERY: "{request.message}"

CONTEXT:
- Risk Tolerance: {request.risk_tolerance}
- Investment Horizon: {request.investment_horizon}
- Portfolio Data: {request.portfolio_data}

Please provide a detailed analysis including:

1. **Market Analysis**: Current market conditions relevant to the query
2. **Investment Recommendations**: Specific actionable advice
3. **Risk Assessment**: Key risks and mitigation strategies
4. **Sector Analysis**: Relevant sector insights
5. **Technical Outlook**: Price trends and technical indicators

Format your response as a comprehensive market analysis report. Be specific, actionable, and professional. Focus on providing real value based on the user's query.

Current Date: {datetime.now().strftime('%Y-%m-%d')}
"""

        # Generate analysis using LLM
        response = await llm.ainvoke([HumanMessage(content=analysis_prompt)])
        
        # Extract analysis text
        analysis_text = response.content
        
        # Generate trading signals prompt
        signals_prompt = f"""
Based on this analysis: "{request.message}" and risk tolerance "{request.risk_tolerance}", provide 2-3 specific trading signals in JSON format.

Return ONLY a JSON array of objects with this structure:
[
  {{
    "symbol": "SYMBOL",
    "action": "BUY/SELL/HOLD",
    "confidence": 0.0-1.0,
    "current_price": 0.0,
    "reasoning": "brief explanation"
  }}
]
"""
        
        signals_response = await llm.ainvoke([HumanMessage(content=signals_prompt)])
        
        # Parse trading signals
        try:
            import json
            trading_signals = json.loads(signals_response.content)
        except:
            trading_signals = [
                {
                    "symbol": "SPY",
                    "action": "HOLD",
                    "confidence": 0.7,
                    "current_price": 450.0,
                    "reasoning": "Balanced market conditions"
                }
            ]
        
        # Generate market events
        market_events = [
            {
                "title": "AI Market Analysis",
                "description": f"Analysis generated for: {request.message}",
                "impact": "neutral",
                "timestamp": datetime.now().isoformat()
            }
        ]
        
        # Generate recommendations
        recommendations = [
            {
                "title": "Personalized Strategy",
                "description": f"Strategy tailored for {request.risk_tolerance} risk tolerance with {request.investment_horizon} horizon"
            }
        ]

        return AnalysisResponse(
            analysis=analysis_text,
            market_events=market_events,
            trading_signals=trading_signals,
            portfolio_recommendations=recommendations
        )
        
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        # Fallback to basic response if LLM fails
        fallback_analysis = f"""
# Market Analysis for: {request.message}

I encountered an issue connecting to the AI analysis service. Here's a brief overview:

## Query Analysis
Your query: "{request.message}"
Risk Profile: {request.risk_tolerance} 
Investment Horizon: {request.investment_horizon}

## General Market Outlook
The market continues to show mixed signals with ongoing volatility. For your {request.risk_tolerance} risk profile and {request.investment_horizon} investment horizon, consider:

1. **Diversification**: Maintain a balanced portfolio across sectors
2. **Risk Management**: Position sizing appropriate for your risk tolerance  
3. **Market Timing**: Dollar-cost averaging for long-term positions
4. **Regular Review**: Monitor and rebalance quarterly

Please try again in a moment as our AI analysis service comes back online.

Error: {str(e)}
"""
        
        return AnalysisResponse(
            analysis=fallback_analysis,
            market_events=[],
            trading_signals=[],
            portfolio_recommendations=[]
        )

# Portfolio Management APIs
@app.get("/portfolio/summary", response_model=PortfolioSummary)
async def get_portfolio_summary():
    """Get portfolio summary information."""
    try:
        portfolio_data = get_mock_portfolio_data()
        
        return PortfolioSummary(
            total_value=portfolio_data["total_value"],
            cash_balance=portfolio_data["cash_balance"],
            invested_capital=portfolio_data["invested_capital"],
            total_pnl=portfolio_data["total_pnl"],
            total_pnl_percent=portfolio_data["total_pnl_percent"],
            positions_count=len(portfolio_data["positions"]),
            daily_change=1250.0,
            daily_change_percent=1.2
        )
    except Exception as e:
        logger.error(f"Portfolio summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/portfolio/positions")
async def get_portfolio_positions():
    """Get detailed portfolio positions."""
    try:
        portfolio_data = get_mock_portfolio_data()
        return {
            "positions": portfolio_data["positions"],
            "total_positions": len(portfolio_data["positions"]),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Portfolio positions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/portfolio/metrics")
async def get_detailed_portfolio_metrics():
    """Get comprehensive portfolio metrics."""
    try:
        portfolio_data = get_mock_portfolio_data()
        return {
            "metrics": portfolio_data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Portfolio metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Market Data APIs
@app.get("/market/quotes")
async def get_market_quotes(symbols: str):
    """Get stock quotes for multiple symbols."""
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(",")]
        quotes = {}
        
        for symbol in symbol_list:
            quotes[symbol] = get_mock_stock_data(symbol)
        
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
        trends = [
            {
                "symbol": "SPY",
                "change": 12.5,
                "changePercent": 2.8,
                "sentiment": "bullish",
                "newsCount": 15
            },
            {
                "symbol": "QQQ", 
                "change": 8.2,
                "changePercent": 2.1,
                "sentiment": "bullish",
                "newsCount": 12
            },
            {
                "symbol": "IWM",
                "change": -2.1,
                "changePercent": -1.2,
                "sentiment": "bearish",
                "newsCount": 8
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
        return {
            "overall_sentiment": "neutral",
            "sentiment_score": 0.1,
            "confidence": 0.7,
            "sentiment_breakdown": {
                "bullish": 45.0,
                "neutral": 35.0,
                "bearish": 20.0
            },
            "timestamp": datetime.now().isoformat()
        }
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
        articles = []
        for i in range(limit):
            article_id = f"article_{i+1}_{int(datetime.now().timestamp())}"
            articles.append({
                "id": article_id,
                "title": f"Market Update: {search_query or 'General'} Analysis {i+1}",
                "summary": f"Latest financial analysis on {search_query or 'market trends'} with key insights.",
                "source": "Financial News Network",
                "publishedAt": (datetime.now() - timedelta(hours=i)).isoformat(),
                "url": f"https://example.com/news/{article_id}",
                "sentiment": ["positive", "neutral", "negative"][i % 3],
                "relevanceScore": round(0.9 - i * 0.05, 2),
                "category": category or "general",
                "symbols": search_query.split(",") if search_query else ["SPY"],
                "isBookmarked": False,
                "readCount": 200 - i * 10
            })
        
        return {
            "articles": articles,
            "total": len(articles),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"News feed error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Trading APIs
@app.post("/trades/execute")
async def execute_trade(request: TradeRequest):
    """Execute a trading order."""
    try:
        order_id = f"ord_{request.symbol}_{int(datetime.now().timestamp())}"
        
        return {
            "order_id": order_id,
            "status": "submitted",
            "message": "Order submitted for processing (simulation mode)",
            "symbol": request.symbol,
            "action": request.action,
            "quantity": request.quantity,
            "filled_quantity": 0,
            "average_price": request.price or 0,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Trade execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trades/history")
async def get_trading_history(limit: int = 50):
    """Get trading history."""
    try:
        trades = []
        for i in range(min(limit, 10)):  # Mock 10 recent trades
            trades.append({
                "id": f"txn_{i+1}",
                "symbol": ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"][i % 5],
                "action": "BUY" if i % 2 == 0 else "SELL",
                "quantity": 100,
                "price": 150.0 + i * 5,
                "timestamp": (datetime.now() - timedelta(days=i)).isoformat(),
                "status": "filled",
                "fees": 1.0
            })
        
        return {
            "trades": trades,
            "total": len(trades),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Trading history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Agent Management APIs
@app.get("/agent/status")
async def get_agent_status():
    """Get current trading agent status."""
    try:
        return {
            "isActive": True,
            "mode": "balanced",
            "balance": 10000.0,
            "buyingPower": 40000.0,
            "dailyPnL": 125.50,
            "totalTrades": 15,
            "successRate": 68.5,
            "lastAction": datetime.now().isoformat(),
            "status": "active"
        }
    except Exception as e:
        logger.error(f"Agent status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agent/thoughts")
async def get_agent_thoughts():
    """Get recent agent thoughts and decisions."""
    try:
        thoughts = []
        thought_templates = [
            "Analyzing market volatility patterns for optimal entry points",
            "Evaluating portfolio diversification metrics and sector allocation",
            "Monitoring economic indicators for potential trading signals",
            "Scanning news sentiment for market opportunities and risks",
            "Calculating optimal position sizing based on risk parameters"
        ]
        
        for i, template in enumerate(thought_templates):
            thoughts.append({
                "id": f"thought_{i+1}",
                "timestamp": (datetime.now() - timedelta(minutes=i*5)).isoformat(),
                "type": "analysis",
                "content": template,
                "confidence": round(0.9 - i * 0.05, 2)
            })
        
        return {
            "thoughts": thoughts,
            "total": len(thoughts),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Agent thoughts error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Rewards System APIs
@app.get("/rewards/achievements")
async def get_achievements():
    """Get trading achievements and rewards."""
    try:
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
        metrics = [
            {
                "id": "sharpe_ratio",
                "title": "RiOPENAI_API_KEY_REDACTED Returns",
                "value": 1.45,
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
                "value": 0.78,
                "target": 0.85,
                "unit": "score",
                "trend": "stable",
                "score": 75,
                "description": "Measures portfolio diversification",
                "suggestions": ["Add international exposure", "Consider more sectors"]
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

# Reward Agent APIs
@app.get("/rewards/learning-insights")
async def get_learning_insights():
    """Get current learning insights and progress from reward agent."""
    try:
        # Mock learning insights - in real implementation, this would use the reward agent
        insights = {
            "learning_mode": "balanced",
            "current_strategy": {
                "name": "Adaptive Growth Strategy",
                "type": "growth",
                "confidence": 0.78,
                "version": 3
            },
            "learning_progress": {
                "total_actions": 15,
                "successful_optimizations": 8,
                "average_improvement": 0.034,
                "current_performance": 78.5,
                "performance_grade": "B+"
            },
            "recent_performance": {
                "overall_score": 78.5,
                "performance_grade": "B+",
                "benchmark_comparison": 0.024,
                "individual_metrics": {
                    "return_performance": {"score": 82, "suggestions": ["Maintain current momentum"]},
                    "risk_adjusted": {"score": 75, "suggestions": ["Consider lowering volatility"]},
                    "diversification": {"score": 80, "suggestions": ["Add international exposure"]}
                }
            },
            "success_rate": 0.73,
            "total_improvements": 0.245,
            "last_optimization": (datetime.now() - timedelta(days=3)).isoformat(),
            "recent_actions": [
                {
                    "type": "optimize_strategy",
                    "improvement": 0.04,
                    "confidence": 0.8,
                    "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
                    "reasoning": "Performance below target, optimization improved riOPENAI_API_KEY_REDACTED returns"
                },
                {
                    "type": "adjust_parameters",
                    "improvement": 0.02,
                    "confidence": 0.6,
                    "timestamp": (datetime.now() - timedelta(days=3)).isoformat(),
                    "reasoning": "Fine-tuning risk level to improve consistency"
                }
            ]
        }
        
        return insights
    except Exception as e:
        logger.error(f"Learning insights error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rewards/strategy-recommendations")
async def get_strategy_recommendations():
    """Get current strategy recommendations from reward agent."""
    try:
        recommendations = [
            {
                "type": "improvement",
                "category": "risk_management",
                "message": "Volatility management needs attention (score: 68.5)",
                "action": "Consider reducing position sizes in high-volatility stocks; Implement better diversification"
            },
            {
                "type": "optimization",
                "category": "performance",
                "message": "Alpha generation could be improved (score: 72.1)",
                "action": "Focus on stock selection; Improve timing of trades"
            },
            {
                "type": "learning",
                "category": "adaptation",
                "message": "Strategy showing consistent improvement over last 30 days",
                "action": "Continue current learning approach with balanced mode"
            }
        ]
        
        return {
            "recommendations": recommendations,
            "total_recommendations": len(recommendations),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Strategy recommendations error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rewards/force-optimization")
async def force_strategy_optimization():
    """Force immediate strategy optimization."""
    try:
        # Mock optimization result
        optimization_result = {
            "success": True,
            "improvement_score": 0.067,
            "optimization_method": "gradient_ascent",
            "iterations": 23,
            "convergence_achieved": True,
            "original_performance": 78.5,
            "optimized_performance": 84.8,
            "recommendations": [
                "Risk level adjusted from 0.65 to 0.58 (reduced by 10.8%)",
                "Return target increased from 0.12 to 0.135 (increased by 12.5%)",
                "Growth weight optimized from 0.75 to 0.82 (increased by 9.3%)"
            ],
            "backtested_performance": {
                "total_return": 0.089,
                "volatility": 0.162,
                "sharpe_ratio": 1.34,
                "max_drawdown": 0.092,
                "win_rate": 0.647
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return optimization_result
    except Exception as e:
        logger.error(f"Force optimization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rewards/performance-analysis")
async def get_performance_analysis(period: str = "monthly"):
    """Get detailed performance analysis from reward agent."""
    try:
        # Mock performance analysis
        analysis = {
            "period": period,
            "start_date": (datetime.now() - timedelta(days=30)).isoformat(),
            "end_date": datetime.now().isoformat(),
            "comprehensive_metrics": {
                "total_return": 0.034,
                "annualized_return": 0.089,
                "volatility": 0.156,
                "sharpe_ratio": 1.42,
                "sortino_ratio": 1.89,
                "max_drawdown": 0.084,
                "calmar_ratio": 1.06,
                "win_rate": 0.623,
                "profit_factor": 1.87,
                "correlation_with_benchmark": 0.72,
                "beta": 1.08,
                "alpha": 0.021,
                "information_ratio": 0.64
            },
            "performance_trends": {
                "portfolio_value_trend": {
                    "direction": "increasing",
                    "percent_change": 3.4,
                    "total_change": 3485.67
                },
                "returns_trend": {
                    "direction": "improving",
                    "average_return": 0.0011,
                    "volatility": 0.156
                },
                "reward_score_trend": {
                    "direction": "improving",
                    "start_score": 72.3,
                    "end_score": 78.5,
                    "average_score": 75.8
                }
            },
            "sector_performance": {
                "Technology": {"allocation": 0.35, "return": 0.045, "contribution": 0.016},
                "Healthcare": {"allocation": 0.25, "return": 0.028, "contribution": 0.007},
                "Finance": {"allocation": 0.20, "return": 0.019, "contribution": 0.004},
                "Consumer": {"allocation": 0.15, "return": 0.032, "contribution": 0.005},
                "Energy": {"allocation": 0.05, "return": 0.041, "contribution": 0.002}
            },
            "reward_breakdown": {
                "return_based": {"score": 82, "weight": 0.25, "contribution": 20.5},
                "risk_adjusted": {"score": 75, "weight": 0.20, "contribution": 15.0},
                "consistency": {"score": 78, "weight": 0.15, "contribution": 11.7},
                "alpha_generation": {"score": 72, "weight": 0.15, "contribution": 10.8},
                "diversification": {"score": 80, "weight": 0.10, "contribution": 8.0},
                "drawdown_control": {"score": 85, "weight": 0.10, "contribution": 8.5},
                "volatility_management": {"score": 68, "weight": 0.05, "contribution": 3.4}
            },
            "improvement_priorities": [
                {
                    "metric": "volatility_management",
                    "current_score": 68,
                    "priority": "High",
                    "suggestions": ["Reduce portfolio volatility", "Consider more stable positions"],
                    "weight": 0.05
                },
                {
                    "metric": "alpha_generation", 
                    "current_score": 72,
                    "priority": "Medium",
                    "suggestions": ["Focus on undervalued stocks", "Improve timing"],
                    "weight": 0.15
                }
            ]
        }
        
        return analysis
    except Exception as e:
        logger.error(f"Performance analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rewards/strategy-comparison")
async def get_strategy_comparison():
    """Get comparison between different strategies."""
    try:
        comparison = {
            "strategies_compared": ["Adaptive Growth v3", "Balanced Portfolio v2", "Value Focus v1"],
            "comparison_period": 30,
            "winner": "Adaptive Growth v3",
            "performance_summary": {
                "Adaptive Growth v3": {
                    "total_return": 0.034,
                    "sharpe_ratio": 1.42,
                    "max_drawdown": 0.084,
                    "win_rate": 0.623,
                    "rank": 1
                },
                "Balanced Portfolio v2": {
                    "total_return": 0.028,
                    "sharpe_ratio": 1.31,
                    "max_drawdown": 0.067,
                    "win_rate": 0.589,
                    "rank": 2
                },
                "Value Focus v1": {
                    "total_return": 0.022,
                    "sharpe_ratio": 1.18,
                    "max_drawdown": 0.056,
                    "win_rate": 0.567,
                    "rank": 3
                }
            },
            "key_differences": {
                "return_performance": {
                    "winner": "Adaptive Growth v3",
                    "difference": 0.006,
                    "description": "1.2% better monthly return"
                },
                "risk_management": {
                    "winner": "Value Focus v1", 
                    "difference": 0.028,
                    "description": "2.8% lower maximum drawdown"
                },
                "consistency": {
                    "winner": "Adaptive Growth v3",
                    "difference": 0.056,
                    "description": "5.6% higher win rate"
                }
            },
            "recommendation": "Continue with Adaptive Growth v3 - shows best overall riOPENAI_API_KEY_REDACTED returns with acceptable drawdown levels",
            "next_optimization": (datetime.now() + timedelta(days=7)).isoformat()
        }
        
        return comparison
    except Exception as e:
        logger.error(f"Strategy comparison error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/rewards/learning-mode")
async def update_learning_mode(mode: str):
    """Update the learning mode of the reward agent."""
    try:
        valid_modes = ["conservative", "balanced", "aggressive"]
        if mode not in valid_modes:
            raise HTTPException(status_code=400, detail=f"Invalid mode. Must be one of: {valid_modes}")
        
        return {
            "success": True,
            "message": f"Learning mode updated to {mode}",
            "previous_mode": "balanced",
            "new_mode": mode,
            "learning_parameters": {
                "learning_rate": 0.005 if mode == "conservative" else (0.01 if mode == "balanced" else 0.02),
                "exploration_rate": 0.1 if mode == "conservative" else (0.2 if mode == "balanced" else 0.3),
                "risk_tolerance": 0.05 if mode == "conservative" else (0.1 if mode == "balanced" else 0.15)
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Learning mode update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)