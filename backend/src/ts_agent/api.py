"""
Time Series Agent API

FastAPI endpoints for time series forecasting, portfolio optimization,
and risk management.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
import asyncio
import os

from .predictor import TimeSeriesPredictor, PredictionRequest, PredictionResponse, BatchPredictionResponse
from .portfolio_optimizer import PortfolioOptimizer, OptimizationConstraints, PortfolioWeights, RebalancingRecommendation
from .risk_manager import RiskManager, RiskMetrics, PortfolioRisk, RiskAlert
from .data_manager import MarketDataManager
from .ibkr_client import IBKRConfig, create_ibkr_client

logger = logging.getLogger(__name__)

# Request/Response Models
class TSPredictionRequest(BaseModel):
    """Request for time series prediction."""
    symbols: List[str] = Field(..., description="List of stock symbols")
    horizon: int = Field(30, description="Forecast horizon in days", ge=1, le=365)
    models: Optional[List[str]] = Field(None, description="Models to use")
    data_source: str = Field("yahoo", description="Data source")
    period: str = Field("2y", description="Historical data period")
    include_confidence: bool = Field(True, description="Include confidence intervals")
    include_scenarios: bool = Field(False, description="Include scenario analysis")

class TSPredictionSingleRequest(BaseModel):
    """Request for single symbol prediction."""
    symbol: str = Field(..., description="Stock symbol")
    horizon: int = Field(30, description="Forecast horizon in days", ge=1, le=365)
    models: Optional[List[str]] = Field(None, description="Models to use")
    data_source: str = Field("yahoo", description="Data source")
    period: str = Field("2y", description="Historical data period")
    include_technical: bool = Field(True, description="Include technical indicators")
    include_market_features: bool = Field(True, description="Include market features")

class PortfolioOptimizationRequest(BaseModel):
    """Request for portfolio optimization."""
    symbols: List[str] = Field(..., description="List of stock symbols")
    current_weights: Optional[Dict[str, float]] = Field(None, description="Current portfolio weights")
    optimization_method: str = Field("max_sharpe", description="Optimization method")
    constraints: Optional[Dict[str, Any]] = Field(None, description="Optimization constraints")
    horizon: int = Field(30, description="Forecast horizon for predictions")

class RiskAssessmentRequest(BaseModel):
    """Request for risk assessment."""
    symbols: List[str] = Field(..., description="List of stock symbols")
    weights: Dict[str, float] = Field(..., description="Portfolio weights")
    horizon: int = Field(30, description="Forecast horizon")
    include_stress_tests: bool = Field(True, description="Include stress tests")

class RebalanceRequest(BaseModel):
    """Request for rebalancing recommendations."""
    current_weights: Dict[str, float] = Field(..., description="Current portfolio weights")
    target_weights: Dict[str, float] = Field(..., description="Target portfolio weights")
    threshold: float = Field(0.05, description="Rebalancing threshold")

# API Router
router = APIRouter(prefix="/ts", tags=["Time Series Agent"])

# Global instances (will be initialized in lifespan)
predictor: Optional[TimeSeriesPredictor] = None
optimizer: Optional[PortfolioOptimizer] = None
risk_manager: Optional[RiskManager] = None

def get_predictor() -> TimeSeriesPredictor:
    """Get predictor instance."""
    global predictor
    if predictor is None:
        nixtla_key = os.getenv("NIXTLA_API_KEY")
        alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        use_ibkr = os.getenv("USE_IBKR", "false").lower() == "true"
        
        predictor = TimeSeriesPredictor(
            nixtla_api_key=nixtla_key,
            alpha_vantage_key=alpha_vantage_key,
            use_ibkr=use_ibkr
        )
    return predictor

def get_optimizer() -> PortfolioOptimizer:
    """Get optimizer instance."""
    global optimizer
    if optimizer is None:
        optimizer = PortfolioOptimizer()
    return optimizer

def get_risk_manager() -> RiskManager:
    """Get risk manager instance."""
    global risk_manager
    if risk_manager is None:
        risk_manager = RiskManager()
    return risk_manager

# Core Prediction Endpoints
@router.post("/predict", response_model=Dict[str, Any])
async def predict_single_symbol(
    request: TSPredictionSingleRequest,
    predictor: TimeSeriesPredictor = Depends(get_predictor)
):
    """Generate predictions for a single symbol."""
    try:
        if request.include_technical or request.include_market_features:
            # Enhanced prediction with features
            result = await predictor.predict_with_features(
                symbol=request.symbol,
                horizon=request.horizon,
                include_technical=request.include_technical,
                include_market_features=request.include_market_features
            )
        else:
            # Standard prediction
            result = await predictor.predict_single(
                symbol=request.symbol,
                horizon=request.horizon,
                models=request.models,
                data_source=request.data_source,
                period=request.period
            )
        
        return {
            "success": True,
            "prediction": {
                "symbol": result.symbol,
                "predictions": result.predictions.to_dict("records"),
                "confidence_intervals": result.confidence_intervals.to_dict("records") if result.confidence_intervals is not None else None,
                "accuracy_metrics": result.accuracy_metrics,
                "model_performance": result.model_performance,
                "scenarios": {k: v.to_dict("records") for k, v in result.scenarios.items()} if result.scenarios else None,
                "horizon": result.horizon,
                "generated_at": result.generated_at.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Prediction failed for {request.symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@router.post("/predict/batch", response_model=Dict[str, Any])
async def predict_batch_symbols(
    request: TSPredictionRequest,
    predictor: TimeSeriesPredictor = Depends(get_predictor)
):
    """Generate predictions for multiple symbols."""
    try:
        result = await predictor.predict_batch(
            symbols=request.symbols,
            horizon=request.horizon,
            models=request.models,
            data_source=request.data_source,
            period=request.period
        )
        
        # Convert to serializable format
        predictions_dict = {}
        for symbol, pred in result.predictions.items():
            predictions_dict[symbol] = {
                "predictions": pred.predictions.to_dict("records"),
                "confidence_intervals": pred.confidence_intervals.to_dict("records") if pred.confidence_intervals is not None else None,
                "accuracy_metrics": pred.accuracy_metrics,
                "model_performance": pred.model_performance,
                "scenarios": {k: v.to_dict("records") for k, v in pred.scenarios.items()} if pred.scenarios else None,
                "horizon": pred.horizon,
                "generated_at": pred.generated_at.isoformat()
            }
        
        return {
            "success": True,
            "batch_prediction": {
                "predictions": predictions_dict,
                "correlation_matrix": result.correlation_matrix.to_dict() if not result.correlation_matrix.empty else {},
                "portfolio_metrics": result.portfolio_metrics,
                "market_regime": result.market_regime,
                "generated_at": result.generated_at.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Batch prediction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")

@router.get("/forecast/{symbol}", response_model=Dict[str, Any])
async def get_detailed_forecast(
    symbol: str,
    horizon: int = 30,
    confidence_levels: List[int] = [80, 90],
    include_technical: bool = True,
    predictor: TimeSeriesPredictor = Depends(get_predictor)
):
    """Get detailed forecast with confidence intervals."""
    try:
        result = await predictor.predict_with_features(
            symbol=symbol,
            horizon=horizon,
            include_technical=include_technical,
            include_market_features=True
        )
        
        return {
            "success": True,
            "forecast": {
                "symbol": result.symbol,
                "predictions": result.predictions.to_dict("records"),
                "confidence_intervals": result.confidence_intervals.to_dict("records") if result.confidence_intervals is not None else None,
                "scenarios": {k: v.to_dict("records") for k, v in result.scenarios.items()} if result.scenarios else None,
                "accuracy_metrics": result.accuracy_metrics,
                "horizon": result.horizon,
                "generated_at": result.generated_at.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Detailed forecast failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Forecast failed: {str(e)}")

# Portfolio Optimization Endpoints
@router.post("/portfolio/optimize", response_model=Dict[str, Any])
async def optimize_portfolio(
    request: PortfolioOptimizationRequest,
    predictor: TimeSeriesPredictor = Depends(get_predictor),
    optimizer: PortfolioOptimizer = Depends(get_optimizer)
):
    """Optimize portfolio allocation using predictions."""
    try:
        # Generate predictions for portfolio
        predictions = {}
        for symbol in request.symbols:
            pred = await predictor.predict_single(
                symbol=symbol,
                horizon=request.horizon,
                models=["statistical", "neural"]  # Fast models for optimization
            )
            predictions[symbol] = pred
        
        # Convert constraints
        constraints = OptimizationConstraints()
        if request.constraints:
            for key, value in request.constraints.items():
                if hasattr(constraints, key):
                    setattr(constraints, key, value)
        
        # Optimize portfolio
        result = optimizer.optimize_portfolio(
            predictions=predictions,
            current_weights=request.current_weights,
            constraints=constraints,
            method=request.optimization_method
        )
        
        return {
            "success": True,
            "optimization": {
                "weights": result.weights,
                "expected_return": result.expected_return,
                "expected_risk": result.expected_risk,
                "sharpe_ratio": result.sharpe_ratio,
                "optimization_method": result.optimization_method,
                "constraints_satisfied": result.constraints_satisfied,
                "generated_at": result.generated_at.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Portfolio optimization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")

@router.post("/portfolio/rebalance", response_model=Dict[str, Any])
async def get_rebalancing_recommendations(
    request: RebalanceRequest,
    optimizer: PortfolioOptimizer = Depends(get_optimizer)
):
    """Get portfolio rebalancing recommendations."""
    try:
        recommendations = optimizer.generate_rebalancing_recommendations(
            current_weights=request.current_weights,
            target_weights=request.target_weights,
            threshold=request.threshold
        )
        
        return {
            "success": True,
            "rebalancing": {
                "recommendations": [
                    {
                        "symbol": rec.symbol,
                        "current_weight": rec.current_weight,
                        "target_weight": rec.target_weight,
                        "weight_change": rec.weight_change,
                        "action": rec.action,
                        "urgency": rec.urgency,
                        "reason": rec.reason
                    }
                    for rec in recommendations
                ],
                "total_changes": len([r for r in recommendations if r.action != "hold"]),
                "high_priority": len([r for r in recommendations if r.urgency == "high"])
            }
        }
        
    except Exception as e:
        logger.error(f"Rebalancing recommendations failed: {e}")
        raise HTTPException(status_code=500, detail=f"Rebalancing failed: {str(e)}")

# Risk Management Endpoints
@router.post("/risk/assess", response_model=Dict[str, Any])
async def assess_portfolio_risk(
    request: RiskAssessmentRequest,
    predictor: TimeSeriesPredictor = Depends(get_predictor),
    risk_manager: RiskManager = Depends(get_risk_manager)
):
    """Assess portfolio risk metrics."""
    try:
        # Generate predictions for risk assessment
        predictions = {}
        for symbol in request.symbols:
            pred = await predictor.predict_single(
                symbol=symbol,
                horizon=request.horizon
            )
            predictions[symbol] = pred
        
        # Create mock portfolio weights for risk assessment
        portfolio_weights = PortfolioWeights(
            weights=request.weights,
            expected_return=0.08,  # Will be calculated
            expected_risk=0.15,    # Will be calculated
            sharpe_ratio=0.5,      # Will be calculated
            optimization_method="risk_assessment",
            constraints_satisfied=True,
            generated_at=datetime.now()
        )
        
        # Assess portfolio risk
        portfolio_risk = risk_manager.assess_portfolio_risk(
            portfolio_weights=portfolio_weights,
            predictions=predictions
        )
        
        # Generate risk alerts
        asset_risks = {}
        for symbol, prediction in predictions.items():
            asset_risks[symbol] = risk_manager.assess_prediction_risk(prediction)
        
        alerts = risk_manager.generate_risk_alerts(
            portfolio_weights=portfolio_weights,
            portfolio_risk=portfolio_risk,
            asset_risks=asset_risks
        )
        
        # Get risk summary
        risk_summary = risk_manager.get_risk_summary(portfolio_risk, alerts)
        
        return {
            "success": True,
            "risk_assessment": {
                "portfolio_risk": {
                    "portfolio_var_95": portfolio_risk.portfolio_var_95,
                    "portfolio_var_99": portfolio_risk.portfolio_var_99,
                    "portfolio_expected_shortfall": portfolio_risk.portfolio_expected_shortfall,
                    "concentration_risk": portfolio_risk.concentration_risk,
                    "correlation_risk": portfolio_risk.correlation_risk,
                    "liquidity_risk": portfolio_risk.liquidity_risk,
                    "tail_risk": portfolio_risk.tail_risk,
                    "stress_test_results": portfolio_risk.stress_test_results,
                    "risk_attribution": portfolio_risk.risk_attribution
                },
                "asset_risks": {
                    symbol: {
                        "var_95": risk.var_95,
                        "var_99": risk.var_99,
                        "expected_shortfall_95": risk.expected_shortfall_95,
                        "max_drawdown": risk.max_drawdown,
                        "volatility": risk.volatility,
                        "beta": risk.beta,
                        "sharpe_ratio": risk.sharpe_ratio,
                        "sortino_ratio": risk.sortino_ratio,
                        "calmar_ratio": risk.calmar_ratio
                    }
                    for symbol, risk in asset_risks.items()
                },
                "alerts": [
                    {
                        "alert_type": alert.alert_type,
                        "severity": alert.severity,
                        "symbol": alert.symbol,
                        "message": alert.message,
                        "current_value": alert.current_value,
                        "threshold": alert.threshold,
                        "timestamp": alert.timestamp.isoformat()
                    }
                    for alert in alerts
                ],
                "summary": risk_summary
            }
        }
        
    except Exception as e:
        logger.error(f"Risk assessment failed: {e}")
        raise HTTPException(status_code=500, detail=f"Risk assessment failed: {str(e)}")

# Market Analysis Endpoints
@router.get("/trends/{symbol}", response_model=Dict[str, Any])
async def analyze_trends(
    symbol: str,
    period: str = "1y",
    include_regime: bool = True,
    predictor: TimeSeriesPredictor = Depends(get_predictor)
):
    """Analyze trends and patterns for a symbol."""
    try:
        # Fetch market data
        data_manager = MarketDataManager()
        market_data = await data_manager.fetch_data(symbol, period=period)
        
        # Add technical indicators
        enhanced_data = data_manager.add_technical_indicators(market_data.data)
        
        # Get market features
        featured_data = data_manager.get_market_features(enhanced_data)
        
        # Detect market regime
        regime_data = data_manager.detect_market_regime(featured_data) if include_regime else featured_data
        
        # Generate short-term prediction for trend analysis
        prediction = await predictor.predict_single(symbol, horizon=10, models=["statistical"])
        
        return {
            "success": True,
            "trend_analysis": {
                "symbol": symbol,
                "current_regime": regime_data['regime'].iloc[-1] if 'regime' in regime_data.columns else "unknown",
                "trend_strength": regime_data['trend'].iloc[-1] if 'trend' in regime_data.columns else 0.0,
                "volatility": regime_data['volatility'].iloc[-1] if 'volatility' in regime_data.columns else 0.0,
                "recent_returns": enhanced_data['close'].pct_change().tail(20).tolist(),
                "technical_indicators": {
                    "rsi": enhanced_data['rsi'].iloc[-1] if 'rsi' in enhanced_data.columns else None,
                    "macd": enhanced_data['MACD_12_26_9'].iloc[-1] if 'MACD_12_26_9' in enhanced_data.columns else None,
                    "sma_20": enhanced_data['sma_20'].iloc[-1] if 'sma_20' in enhanced_data.columns else None,
                    "ema_12": enhanced_data['ema_12'].iloc[-1] if 'ema_12' in enhanced_data.columns else None
                },
                "short_term_forecast": prediction.predictions.to_dict("records"),
                "analysis_date": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Trend analysis failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Trend analysis failed: {str(e)}")

@router.get("/volatility/{symbol}", response_model=Dict[str, Any])
async def forecast_volatility(
    symbol: str,
    horizon: int = 30,
    predictor: TimeSeriesPredictor = Depends(get_predictor)
):
    """Forecast volatility for a symbol."""
    try:
        # Generate prediction
        prediction = await predictor.predict_single(symbol, horizon=horizon)
        
        # Calculate volatility metrics
        if not prediction.predictions.empty:
            pred_col = 'ensemble_prediction' if 'ensemble_prediction' in prediction.predictions.columns else prediction.predictions.columns[-1]
            pred_returns = prediction.predictions[pred_col].pct_change().dropna()
            
            current_vol = pred_returns.std() * np.sqrt(252)  # Annualized
            vol_forecast = pred_returns.rolling(window=5).std() * np.sqrt(252)
            
            return {
                "success": True,
                "volatility_forecast": {
                    "symbol": symbol,
                    "current_volatility": current_vol,
                    "forecasted_volatility": vol_forecast.tolist(),
                    "vol_regime": "high" if current_vol > 0.3 else "medium" if current_vol > 0.15 else "low",
                    "horizon": horizon,
                    "generated_at": datetime.now().isoformat()
                }
            }
        else:
            raise ValueError("No predictions available for volatility calculation")
            
    except Exception as e:
        logger.error(f"Volatility forecast failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Volatility forecast failed: {str(e)}")

# Data and Model Management
@router.get("/models/available", response_model=Dict[str, Any])
async def get_available_models(
    predictor: TimeSeriesPredictor = Depends(get_predictor)
):
    """Get list of available prediction models."""
    try:
        performance = predictor.get_model_performance()
        return {
            "success": True,
            "models": performance
        }
    except Exception as e:
        logger.error(f"Failed to get available models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get models: {str(e)}")

@router.get("/data/{symbol}/history", response_model=Dict[str, Any])
async def get_historical_data(
    symbol: str,
    period: str = "1y",
    interval: str = "1d",
    include_indicators: bool = False
):
    """Get historical data with optional technical indicators."""
    try:
        data_manager = MarketDataManager()
        market_data = await data_manager.fetch_data(
            symbol=symbol,
            period=period,
            interval=interval
        )
        
        if include_indicators:
            market_data.data = data_manager.add_technical_indicators(market_data.data)
        
        return {
            "success": True,
            "historical_data": {
                "symbol": market_data.symbol,
                "data": market_data.data.to_dict("records"),
                "timeframe": market_data.timeframe,
                "source": market_data.source,
                "last_updated": market_data.last_updated.isoformat(),
                "total_records": len(market_data.data)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get historical data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get data: {str(e)}")

@router.post("/models/retrain", response_model=Dict[str, Any])
async def retrain_models(
    background_tasks: BackgroundTasks,
    symbols: List[str],
    force: bool = False
):
    """Trigger model retraining (background task)."""
    try:
        def retrain_task():
            logger.info(f"Starting model retraining for {len(symbols)} symbols")
            # Mock retraining process
            import time
            time.sleep(2)  # Simulate retraining
            logger.info("Model retraining completed")
        
        background_tasks.add_task(retrain_task)
        
        return {
            "success": True,
            "message": f"Model retraining started for {len(symbols)} symbols",
            "task_id": f"retrain_{int(datetime.now().timestamp())}",
            "estimated_completion": (datetime.now() + timedelta(minutes=5)).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to start model retraining: {e}")
        raise HTTPException(status_code=500, detail=f"Retraining failed: {str(e)}")

@router.delete("/cache/clear", response_model=Dict[str, Any])
async def clear_cache(
    predictor: TimeSeriesPredictor = Depends(get_predictor)
):
    """Clear prediction and data cache."""
    try:
        predictor.clear_cache()
        return {
            "success": True,
            "message": "Cache cleared successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=f"Cache clear failed: {str(e)}")