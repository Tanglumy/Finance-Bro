#!/usr/bin/env python3
"""
Standalone TS Agent API Server

Run just the Time Series Agent API endpoints for testing.
"""

import sys
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Time Series Agent API",
    description="Enhanced Time Series Prediction Agent with Nixtla TimeGPT and GluonTS",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include TS Agent router
try:
    from ts_agent.api import router as ts_router
    app.include_router(ts_router)
    logger.info("✅ TS Agent API loaded successfully")
except ImportError as e:
    logger.error(f"❌ Failed to load TS Agent API: {e}")
    sys.exit(1)

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Time Series Agent API",
        "version": "1.0.0",
        "description": "Enhanced financial time series prediction with Nixtla TimeGPT and GluonTS",
        "endpoints": {
            "predictions": "/ts/predict",
            "batch_predictions": "/ts/predict/batch", 
            "forecasts": "/ts/forecast/{symbol}",
            "portfolio_optimization": "/ts/portfolio/optimize",
            "risk_assessment": "/ts/risk/assess",
            "trend_analysis": "/ts/trends/{symbol}",
            "volatility_forecast": "/ts/volatility/{symbol}",
            "available_models": "/ts/models/available",
            "historical_data": "/ts/data/{symbol}/history"
        },
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "ts-agent"}

if __name__ == "__main__":
    print("""
    🚀 Starting Time Series Agent API Server
    
    📊 Available Features:
    - Nixtla TimeGPT Foundation Models
    - GluonTS Deep Learning Models  
    - Statistical Forecasting Models
    - ML-based Predictions
    - Portfolio Optimization
    - Risk Assessment
    - Real-time Market Analysis
    
    🌐 Access the API at:
    - Main API: http://localhost:8002
    - Documentation: http://localhost:8002/docs
    - ReDoc: http://localhost:8002/redoc
    
    📈 Example Endpoints:
    - POST /ts/predict - Single symbol prediction
    - POST /ts/predict/batch - Multiple symbols  
    - GET /ts/forecast/AAPL?horizon=30 - Detailed forecast
    - POST /ts/portfolio/optimize - Portfolio optimization
    """)
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8002,
        reload=True,
        log_level="info"
    )