"""
Time Series Agent Module

This module provides comprehensive time series forecasting capabilities for financial markets
using state-of-the-art models including Nixtla's TimeGPT, GluonTS, and statistical forecasting.

Key Components:
- Model Manager: Handles different forecasting models
- Data Manager: Fetches and preprocesses market data
- Predictor: Generates forecasts and predictions
- Portfolio Optimizer: Uses predictions for portfolio optimization
- Risk Manager: Assesses forecast uncertainty and risks
"""

from .models import TimeSeriesModelManager
from .data_manager import MarketDataManager
from .predictor import TimeSeriesPredictor
from .portfolio_optimizer import PortfolioOptimizer
from .risk_manager import RiskManager
from .ibkr_client import IBKRDataClient

__version__ = "1.0.0"
__all__ = [
    "TimeSeriesModelManager",
    "MarketDataManager", 
    "TimeSeriesPredictor",
    "PortfolioOptimizer",
    "RiskManager",
    "IBKRDataClient"
]