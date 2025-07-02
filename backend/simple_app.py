from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List
from datetime import datetime

app = FastAPI(
    title="Finance Bro API",
    description="Simple API for financial analysis",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_market_events(request: AnalysisRequest):
    """Analyze market events and generate trading recommendations."""
    try:
        # Mock analysis response
        analysis = f"""
Based on your query: "{request.message}"

Market Analysis Summary:
- Current market conditions appear stable with moderate volatility
- Your risk tolerance ({request.risk_tolerance}) and investment horizon ({request.investment_horizon}) suggest a balanced approach
- Key sectors showing strength: Technology, Healthcare, Energy
- Recommended strategy: Diversified portfolio with focus on dividend-paying stocks

Investment Considerations:
1. Market sentiment remains cautiously optimistic
2. Economic indicators suggest continued growth
3. Recommended position sizing: 2-5% per individual stock
4. Consider dollar-cost averaging for new positions

Risk Management:
- Maintain 10-20% cash reserves
- Set stop-losses at 8-10% below purchase price
- Regular portfolio rebalancing quarterly
        """

        mock_events = [
            {
                "title": "Federal Reserve Policy Update",
                "description": "Fed maintains current interest rates, signals potential future adjustments",
                "impact": "neutral",
                "timestamp": datetime.now().isoformat()
            },
            {
                "title": "Tech Sector Earnings Season",
                "description": "Major tech companies showing strong quarterly results",
                "impact": "positive",
                "timestamp": datetime.now().isoformat()
            }
        ]

        mock_signals = [
            {
                "symbol": "SPY",
                "action": "BUY",
                "confidence": 0.75,
                "reasoning": "Strong market momentum and positive economic indicators"
            },
            {
                "symbol": "VTI",
                "action": "HOLD",
                "confidence": 0.68,
                "reasoning": "Broad market exposure, good for long-term holdings"
            }
        ]

        mock_recommendations = [
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
            market_events=mock_events,
            trading_signals=mock_signals,
            portfolio_recommendations=mock_recommendations
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

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
        "features": ["analysis", "signals", "portfolio_recommendations"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)