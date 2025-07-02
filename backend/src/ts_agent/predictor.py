"""
Time Series Predictor

Main prediction engine that coordinates different models and provides
unified interface for time series forecasting.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Tuple, Any
from datetime import datetime, timedelta
import logging
import asyncio
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

from .models import TimeSeriesModelManager, ForecastResult
from .data_manager import MarketDataManager, MarketData
from .ibkr_client import create_ibkr_client, IBKRConfig

logger = logging.getLogger(__name__)

@dataclass
class PredictionRequest:
    """Request for time series prediction."""
    symbols: List[str]
    horizon: int = 30
    models: List[str] = None
    include_confidence: bool = True
    include_scenarios: bool = False
    data_source: str = "yahoo"
    period: str = "2y"
    
@dataclass
class PredictionResponse:
    """Response from time series prediction."""
    symbol: str
    predictions: pd.DataFrame
    confidence_intervals: Optional[pd.DataFrame]
    accuracy_metrics: Dict[str, float]
    model_performance: Dict[str, Any]
    scenarios: Optional[Dict[str, pd.DataFrame]]
    generated_at: datetime
    horizon: int
    
@dataclass
class BatchPredictionResponse:
    """Response for batch predictions."""
    predictions: Dict[str, PredictionResponse]
    correlation_matrix: pd.DataFrame
    portfolio_metrics: Dict[str, Any]
    market_regime: str
    generated_at: datetime

class TimeSeriesPredictor:
    """Main prediction engine for time series forecasting."""
    
    def __init__(
        self,
        nixtla_api_key: Optional[str] = None,
        alpha_vantage_key: Optional[str] = None,
        ibkr_config: Optional[IBKRConfig] = None,
        use_ibkr: bool = False
    ):
        """
        Initialize the predictor.
        
        Args:
            nixtla_api_key: Nixtla TimeGPT API key
            alpha_vantage_key: Alpha Vantage API key
            ibkr_config: IBKR configuration
            use_ibkr: Whether to use IBKR for data
        """
        self.model_manager = TimeSeriesModelManager(nixtla_api_key)
        self.data_manager = MarketDataManager(alpha_vantage_key)
        
        # IBKR client (optional)
        self.ibkr_client = None
        if use_ibkr:
            try:
                self.ibkr_client = create_ibkr_client(ibkr_config)
            except Exception as e:
                logger.warning(f"Failed to initialize IBKR client: {e}")
        
        self.prediction_cache = {}
        self.default_models = ["statistical", "neural", "ml"]
        self.model_performance_history = {}
        self.ensemble_weights = {}
        
    async def predict_single(
        self,
        symbol: str,
        horizon: int = 30,
        models: Optional[List[str]] = None,
        data_source: str = "yahoo",
        period: str = "2y"
    ) -> PredictionResponse:
        """
        Generate predictions for a single symbol.
        
        Args:
            symbol: Stock symbol
            horizon: Forecast horizon (days)
            models: List of models to use
            data_source: Data source ('yahoo', 'alpha_vantage', 'ibkr')
            period: Historical data period
            
        Returns:
            PredictionResponse object
        """
        try:
            # Use default models if none specified
            if models is None:
                models = self.default_models.copy()
                # Add TimeGPT if available
                if self.model_manager.nixtla_client or self.model_manager.timegpt:
                    models.insert(0, "timegpt")
            
            # Check cache for recent predictions
            cache_key = f"{symbol}_{horizon}_{'-'.join(sorted(models))}_{data_source}_{period}"
            if cache_key in self.prediction_cache:
                cached_result = self.prediction_cache[cache_key]
                if (datetime.now() - cached_result.generated_at).seconds < 1800:  # 30 min cache
                    logger.debug(f"Using cached prediction for {symbol}")
                    return cached_result
            
            # Fetch market data
            if data_source == "ibkr" and self.ibkr_client:
                market_data = await self._fetch_ibkr_data(symbol, period)
            else:
                market_data = await self.data_manager.fetch_data(
                    symbol, period=period, source=data_source
                )
            
            # Prepare data for forecasting
            forecast_data = self.data_manager.prepare_for_forecasting(market_data.data)
            
            # Validate data
            if not self.model_manager.validate_data(forecast_data):
                raise ValueError(f"Invalid data for {symbol}")
            
            # Generate predictions with different models
            predictions = {}
            model_performance = {}
            
            for model_name in models:
                try:
                    if model_name == "timegpt":
                        result = self.model_manager.predict_timegpt(forecast_data, horizon)
                    elif model_name == "statistical":
                        result = self.model_manager.predict_statistical(forecast_data, horizon=horizon)
                    elif model_name == "neural":
                        result = self.model_manager.predict_neural(forecast_data, horizon=horizon)
                    elif model_name == "ml":
                        result = self.model_manager.predict_ml(forecast_data, horizon=horizon)
                    elif model_name == "deepar":
                        result = self.model_manager.predict_gluonts(forecast_data, "deepar", horizon)
                    elif model_name == "transformer":
                        result = self.model_manager.predict_gluonts(forecast_data, "transformer", horizon)
                    elif model_name == "ensemble":
                        result = self.model_manager.ensemble_predict(forecast_data, horizon=horizon)
                    else:
                        logger.warning(f"Unknown model: {model_name}")
                        continue
                    
                    predictions[model_name] = result
                    model_performance[model_name] = {
                        "accuracy_metrics": result.accuracy_metrics,
                        "model_name": result.model_name,
                        "generated_at": result.generated_at
                    }
                    
                except Exception as e:
                    logger.error(f"Model {model_name} failed for {symbol}: {e}")
            
            if not predictions:
                raise ValueError(f"No models succeeded for {symbol}")
            
            # Create ensemble prediction if multiple models
            if len(predictions) > 1:
                ensemble_pred = self._create_ensemble_prediction(predictions)
                final_predictions = ensemble_pred.predictions
                confidence_intervals = ensemble_pred.confidence_intervals
                accuracy_metrics = ensemble_pred.accuracy_metrics
            else:
                # Use single model result
                single_result = list(predictions.values())[0]
                final_predictions = single_result.predictions
                confidence_intervals = single_result.confidence_intervals
                accuracy_metrics = single_result.accuracy_metrics
            
            # Generate scenarios (optional)
            scenarios = await self._generate_scenarios(forecast_data, final_predictions, horizon)
            
            # Update model performance history
            self._update_model_performance(symbol, predictions)
            
            # Create final response
            response = PredictionResponse(
                symbol=symbol,
                predictions=final_predictions,
                confidence_intervals=confidence_intervals,
                accuracy_metrics=accuracy_metrics,
                model_performance=model_performance,
                scenarios=scenarios,
                generated_at=datetime.now(),
                horizon=horizon
            )
            
            # Cache the result
            self.prediction_cache[cache_key] = response
            
            return response
            
        except Exception as e:
            logger.error(f"Prediction failed for {symbol}: {e}")
            raise
    
    async def predict_batch(
        self,
        symbols: List[str],
        horizon: int = 30,
        models: Optional[List[str]] = None,
        data_source: str = "yahoo",
        period: str = "2y"
    ) -> BatchPredictionResponse:
        """
        Generate predictions for multiple symbols.
        
        Args:
            symbols: List of stock symbols
            horizon: Forecast horizon (days)
            models: List of models to use
            data_source: Data source
            period: Historical data period
            
        Returns:
            BatchPredictionResponse object
        """
        try:
            # Generate predictions for each symbol
            prediction_tasks = []
            for symbol in symbols:
                task = self.predict_single(symbol, horizon, models, data_source, period)
                prediction_tasks.append(task)
            
            # Execute predictions concurrently
            results = await asyncio.gather(*prediction_tasks, return_exceptions=True)
            
            # Process results
            predictions = {}
            for symbol, result in zip(symbols, results):
                if isinstance(result, Exception):
                    logger.error(f"Prediction failed for {symbol}: {result}")
                else:
                    predictions[symbol] = result
            
            if not predictions:
                raise ValueError("No predictions succeeded")
            
            # Fetch data for portfolio analysis
            if data_source == "ibkr" and self.ibkr_client:
                symbols_data = await self._fetch_multiple_ibkr_data(symbols, period)
            else:
                symbols_data = await self.data_manager.fetch_multiple_symbols(
                    symbols, period=period, source=data_source
                )
            
            # Calculate correlation matrix
            correlation_matrix = self.data_manager.get_correlation_matrix(symbols_data)
            
            # Analyze market regime
            market_regime = await self._analyze_market_regime(symbols_data)
            
            # Calculate portfolio metrics
            portfolio_metrics = await self._calculate_portfolio_metrics(predictions, symbols_data)
            
            return BatchPredictionResponse(
                predictions=predictions,
                correlation_matrix=correlation_matrix,
                portfolio_metrics=portfolio_metrics,
                market_regime=market_regime,
                generated_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Batch prediction failed: {e}")
            raise
    
    async def predict_with_features(
        self,
        symbol: str,
        horizon: int = 30,
        include_technical: bool = True,
        include_market_features: bool = True,
        external_features: Optional[pd.DataFrame] = None
    ) -> PredictionResponse:
        """
        Generate predictions with additional features.
        
        Args:
            symbol: Stock symbol
            horizon: Forecast horizon
            include_technical: Include technical indicators
            include_market_features: Include market features
            external_features: External features DataFrame
            
        Returns:
            Enhanced PredictionResponse
        """
        try:
            # Fetch base data
            market_data = await self.data_manager.fetch_data(symbol)
            
            # Add technical indicators
            if include_technical:
                market_data.data = self.data_manager.add_technical_indicators(market_data.data)
            
            # Add market features
            if include_market_features:
                market_data.data = self.data_manager.get_market_features(market_data.data)
            
            # Merge external features if provided
            if external_features is not None:
                market_data.data = pd.merge(
                    market_data.data, external_features, 
                    on='date', how='left'
                )
            
            # Prepare for forecasting
            forecast_data = self.data_manager.prepare_for_forecasting(market_data.data)
            
            # Determine best models based on data characteristics
            available_models = ["statistical", "neural", "ml"]
            if self.model_manager.nixtla_client or self.model_manager.timegpt:
                available_models.insert(0, "timegpt")
            
            # Use adaptive ensemble based on data size and volatility
            if len(forecast_data) > 500:  # Enough data for complex models
                ensemble_models = available_models
            else:  # Use simpler models for limited data
                ensemble_models = ["statistical", "ml"]
            
            # Use ensemble prediction with enhanced features
            result = self.model_manager.ensemble_predict(
                forecast_data, 
                models=ensemble_models,
                horizon=horizon,
                weights=self._get_adaptive_weights(symbol, ensemble_models)
            )
            
            # Generate additional analysis
            scenarios = await self._generate_scenarios(forecast_data, result.predictions, horizon)
            
            return PredictionResponse(
                symbol=symbol,
                predictions=result.predictions,
                confidence_intervals=result.confidence_intervals,
                accuracy_metrics=result.accuracy_metrics,
                model_performance={"enhanced_ensemble": result.accuracy_metrics},
                scenarios=scenarios,
                generated_at=datetime.now(),
                horizon=horizon
            )
            
        except Exception as e:
            logger.error(f"Enhanced prediction failed for {symbol}: {e}")
            raise
    
    async def _fetch_ibkr_data(self, symbol: str, period: str) -> MarketData:
        """Fetch data from IBKR."""
        if not self.ibkr_client:
            raise ValueError("IBKR client not available")
        
        # Connect if not connected
        if not self.ibkr_client.connected:
            await self.ibkr_client.connect()
        
        # Map period to IBKR duration
        duration_map = {
            "1y": "1 Y",
            "2y": "2 Y",
            "5y": "5 Y",
            "6mo": "6 M",
            "3mo": "3 M"
        }
        duration = duration_map.get(period, "1 Y")
        
        # Fetch historical data
        data = await self.ibkr_client.get_historical_data(symbol, duration)
        
        return MarketData(
            symbol=symbol,
            data=data,
            timeframe=f"{period}_1d",
            source="ibkr",
            last_updated=datetime.now()
        )
    
    async def _fetch_multiple_ibkr_data(self, symbols: List[str], period: str) -> Dict[str, MarketData]:
        """Fetch data for multiple symbols from IBKR."""
        if not self.ibkr_client:
            raise ValueError("IBKR client not available")
        
        # Connect if not connected
        if not self.ibkr_client.connected:
            await self.ibkr_client.connect()
        
        duration_map = {
            "1y": "1 Y",
            "2y": "2 Y", 
            "5y": "5 Y",
            "6mo": "6 M",
            "3mo": "3 M"
        }
        duration = duration_map.get(period, "1 Y")
        
        # Fetch data for all symbols
        data_dict = await self.ibkr_client.get_multiple_historical_data(symbols, duration)
        
        # Convert to MarketData objects
        result = {}
        for symbol, data in data_dict.items():
            result[symbol] = MarketData(
                symbol=symbol,
                data=data,
                timeframe=f"{period}_1d",
                source="ibkr",
                last_updated=datetime.now()
            )
        
        return result
    
    def _create_ensemble_prediction(self, predictions: Dict[str, ForecastResult]) -> ForecastResult:
        """Create ensemble prediction from multiple model results."""
        try:
            # Equal weights for now
            weights = {model: 1.0 / len(predictions) for model in predictions.keys()}
            
            # Combine predictions
            combined_predictions = self.model_manager._combine_predictions(
                {model: result.predictions for model, result in predictions.items()},
                weights
            )
            
            # Average accuracy metrics
            combined_metrics = {}
            for model_name, result in predictions.items():
                for metric, value in result.accuracy_metrics.items():
                    if metric not in combined_metrics:
                        combined_metrics[metric] = []
                    combined_metrics[metric].append(value)
            
            averaged_metrics = {
                metric: np.mean(values) 
                for metric, values in combined_metrics.items()
            }
            
            return ForecastResult(
                symbol=list(predictions.values())[0].symbol,
                predictions=combined_predictions,
                confidence_intervals=None,
                model_name=f"Ensemble-{'-'.join(predictions.keys())}",
                accuracy_metrics=averaged_metrics,
                forecast_horizon=list(predictions.values())[0].forecast_horizon,
                generated_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error creating ensemble prediction: {e}")
            # Return first available prediction as fallback
            return list(predictions.values())[0]
    
    async def _generate_scenarios(
        self,
        historical_data: pd.DataFrame,
        base_predictions: pd.DataFrame,
        horizon: int
    ) -> Dict[str, pd.DataFrame]:
        """Generate scenario-based predictions."""
        try:
            scenarios = {}
            
            # Calculate historical volatility
            returns = historical_data['y'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252)  # Annualized
            
            # Get base prediction values
            if 'ensemble_prediction' in base_predictions.columns:
                base_values = base_predictions['ensemble_prediction']
            else:
                # Use first non-date column
                pred_cols = [col for col in base_predictions.columns if col != 'ds']
                base_values = base_predictions[pred_cols[0]] if pred_cols else base_predictions.iloc[:, -1]
            
            # Bull scenario (+1 std)
            scenarios['bull'] = base_predictions.copy()
            scenarios['bull']['prediction'] = base_values * (1 + volatility / np.sqrt(252))
            
            # Bear scenario (-1 std)
            scenarios['bear'] = base_predictions.copy()
            scenarios['bear']['prediction'] = base_values * (1 - volatility / np.sqrt(252))
            
            # Sideways scenario (reduced volatility)
            scenarios['sideways'] = base_predictions.copy()
            mean_price = historical_data['y'].tail(20).mean()
            scenarios['sideways']['prediction'] = mean_price + (base_values - mean_price) * 0.3
            
            return scenarios
            
        except Exception as e:
            logger.warning(f"Error generating scenarios: {e}")
            return {}
    
    async def _analyze_market_regime(self, symbols_data: Dict[str, MarketData]) -> str:
        """Analyze current market regime."""
        try:
            if not symbols_data:
                return "unknown"
            
            # Analyze trend across multiple symbols
            trends = []
            volatilities = []
            
            for market_data in symbols_data.values():
                if len(market_data.data) > 50:
                    # Calculate recent trend
                    recent_data = market_data.data.tail(20)
                    if 'close' in recent_data.columns:
                        returns = recent_data['close'].pct_change().dropna()
                        trend = returns.mean()
                        vol = returns.std()
                        
                        trends.append(trend)
                        volatilities.append(vol)
            
            if not trends:
                return "unknown"
            
            avg_trend = np.mean(trends)
            avg_vol = np.mean(volatilities)
            vol_threshold = np.median(volatilities) if volatilities else 0.02
            
            # Classify regime
            if avg_trend > 0.001:  # 0.1% daily trend
                return "bull_market"
            elif avg_trend < -0.001:
                if avg_vol > vol_threshold * 1.5:
                    return "bear_market_volatile"
                else:
                    return "bear_market"
            else:
                if avg_vol > vol_threshold * 1.2:
                    return "sideways_volatile"
                else:
                    return "sideways_calm"
            
        except Exception as e:
            logger.warning(f"Error analyzing market regime: {e}")
            return "unknown"
    
    async def _calculate_portfolio_metrics(
        self,
        predictions: Dict[str, PredictionResponse],
        symbols_data: Dict[str, MarketData]
    ) -> Dict[str, Any]:
        """Calculate portfolio-level metrics."""
        try:
            metrics = {}
            
            # Portfolio diversity score
            metrics['diversity_score'] = len(predictions) / max(len(predictions), 10)
            
            # Average prediction confidence
            confidence_scores = []
            for pred in predictions.values():
                if pred.accuracy_metrics:
                    # Use inverse of MSE as confidence proxy
                    mse = pred.accuracy_metrics.get('mse', 1.0)
                    confidence = 1.0 / (1.0 + mse)
                    confidence_scores.append(confidence)
            
            metrics['avg_confidence'] = np.mean(confidence_scores) if confidence_scores else 0.5
            
            # Prediction horizon coverage
            horizons = [pred.horizon for pred in predictions.values()]
            metrics['avg_horizon'] = np.mean(horizons) if horizons else 30
            
            # Model diversity
            used_models = set()
            for pred in predictions.values():
                used_models.update(pred.model_performance.keys())
            metrics['model_diversity'] = len(used_models)
            
            # Risk assessment
            predicted_returns = []
            for symbol, pred in predictions.items():
                if not pred.predictions.empty:
                    # Calculate predicted return
                    if symbol in symbols_data and not symbols_data[symbol].data.empty:
                        current_price = symbols_data[symbol].data['close'].iloc[-1]
                        if 'ensemble_prediction' in pred.predictions.columns:
                            future_price = pred.predictions['ensemble_prediction'].iloc[-1]
                        else:
                            pred_cols = [col for col in pred.predictions.columns if col != 'ds']
                            future_price = pred.predictions[pred_cols[0]].iloc[-1] if pred_cols else current_price
                        
                        predicted_return = (future_price - current_price) / current_price
                        predicted_returns.append(predicted_return)
            
            if predicted_returns:
                metrics['expected_return'] = np.mean(predicted_returns)
                metrics['predicted_volatility'] = np.std(predicted_returns)
                metrics['predicted_sharpe'] = metrics['expected_return'] / max(metrics['predicted_volatility'], 0.001)
            else:
                metrics['expected_return'] = 0.0
                metrics['predicted_volatility'] = 0.0
                metrics['predicted_sharpe'] = 0.0
            
            return metrics
            
        except Exception as e:
            logger.warning(f"Error calculating portfolio metrics: {e}")
            return {"error": str(e)}
    
    def get_model_performance(self) -> Dict[str, Any]:
        """Get performance statistics for different models."""
        available_models = self.model_manager.get_available_models()
        
        return {
            "available_models": available_models,
            "nixtla_available": (self.model_manager.nixtla_client is not None or 
                               self.model_manager.timegpt is not None),
            "ibkr_available": self.ibkr_client is not None,
            "cache_size": len(self.prediction_cache),
            "performance_history_size": len(self.model_performance_history),
            "supported_sources": ["yahoo", "alpha_vantage"] + (["ibkr"] if self.ibkr_client else []),
            "model_performance_summary": self.get_model_performance_summary()
        }
    
    def _update_model_performance(self, symbol: str, predictions: Dict[str, ForecastResult]):
        """Update model performance tracking."""
        try:
            if symbol not in self.model_performance_history:
                self.model_performance_history[symbol] = {}
            
            for model_name, result in predictions.items():
                if model_name not in self.model_performance_history[symbol]:
                    self.model_performance_history[symbol][model_name] = []
                
                # Store performance metrics
                performance_entry = {
                    'timestamp': datetime.now(),
                    'accuracy_metrics': result.accuracy_metrics,
                    'model_name': result.model_name
                }
                
                self.model_performance_history[symbol][model_name].append(performance_entry)
                
                # Keep only last 10 entries per model
                if len(self.model_performance_history[symbol][model_name]) > 10:
                    self.model_performance_history[symbol][model_name] = \
                        self.model_performance_history[symbol][model_name][-10:]
                        
        except Exception as e:
            logger.warning(f"Error updating model performance: {e}")
    
    def _get_adaptive_weights(self, symbol: str, models: List[str]) -> Optional[Dict[str, float]]:
        """Get adaptive weights based on historical performance."""
        try:
            if symbol not in self.model_performance_history:
                return None
            
            weights = {}
            total_score = 0
            
            for model in models:
                if model in self.model_performance_history[symbol]:
                    recent_performance = self.model_performance_history[symbol][model][-3:]  # Last 3 predictions
                    
                    if recent_performance:
                        # Use inverse MSE as performance score
                        mse_scores = [1.0 / (1.0 + perf['accuracy_metrics'].get('mse', 1.0)) 
                                     for perf in recent_performance if perf['accuracy_metrics']]
                        
                        if mse_scores:
                            avg_score = np.mean(mse_scores)
                            weights[model] = avg_score
                            total_score += avg_score
            
            # Normalize weights
            if total_score > 0:
                weights = {model: weight / total_score for model, weight in weights.items()}
                return weights
            
            return None
            
        except Exception as e:
            logger.warning(f"Error calculating adaptive weights: {e}")
            return None
    
    def get_model_performance_summary(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Get summary of model performance."""
        try:
            if symbol:
                if symbol in self.model_performance_history:
                    return self.model_performance_history[symbol]
                else:
                    return {}
            else:
                # Return aggregated performance across all symbols
                summary = {}
                for sym, models in self.model_performance_history.items():
                    for model, performances in models.items():
                        if model not in summary:
                            summary[model] = []
                        summary[model].extend(performances)
                
                # Calculate average metrics per model
                model_averages = {}
                for model, performances in summary.items():
                    if performances:
                        metrics = [p['accuracy_metrics'] for p in performances if p['accuracy_metrics']]
                        if metrics:
                            avg_metrics = {}
                            for metric in ['mse', 'mae', 'mape']:
                                values = [m.get(metric, 0) for m in metrics if metric in m]
                                if values:
                                    avg_metrics[metric] = np.mean(values)
                            model_averages[model] = avg_metrics
                
                return model_averages
                
        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {}
    
    def clear_cache(self):
        """Clear prediction cache."""
        self.prediction_cache.clear()
        self.data_manager.clear_cache()
        self.model_performance_history.clear()
        self.ensemble_weights.clear()
        logger.info("Prediction cache and performance history cleared")