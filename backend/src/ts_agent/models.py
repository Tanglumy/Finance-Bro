"""
Time Series Models Manager

Handles different forecasting models including:
- Nixtla TimeGPT (foundation model)
- GluonTS models (deep learning)
- Statistical models (ARIMA, ETS, etc.)
"""

import os
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass

# Nixtla imports
from nixtla import NixtlaClient
try:
    from nixtlats import TimeGPT
    NIXTLATS_AVAILABLE = True
except ImportError:
    NIXTLATS_AVAILABLE = False
    TimeGPT = None

# GluonTS imports with fallback
try:
    from gluonts.mx import Trainer
    from gluonts.model.deepar import DeepAREstimator
    from gluonts.model.transformer import TransformerEstimator
    from gluonts.model.simple_feedforward import SimpleFeedForwardEstimator
    from gluonts.dataset.common import ListDataset
    from gluonts.evaluation import Evaluator
    GLUONTS_AVAILABLE = True
except ImportError:
    GLUONTS_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("GluonTS not available. Deep learning models will be disabled.")

# Statistical models from statsforecast with fallback
try:
    from statsforecast import StatsForecast
    from statsforecast.models import AutoARIMA, AutoETS, AutoCES, DynamicOptimizedTheta, MSTL, SeasonalNaive
    STATSFORECAST_AVAILABLE = True
except ImportError:
    STATSFORECAST_AVAILABLE = False
    if 'logger' not in globals():
        logger = logging.getLogger(__name__)
    logger.warning("StatsForecast not available. Statistical models will be disabled.")

# Neural models from neuralforecast with fallback
try:
    from neuralforecast import NeuralForecast
    from neuralforecast.models import NBEATS, NHITS, NBEATSx, TiDE, PatchTST, iTransformer, TimesNet
    NEURALFORECAST_AVAILABLE = True
except ImportError:
    NEURALFORECAST_AVAILABLE = False
    if 'logger' not in globals():
        logger = logging.getLogger(__name__)
    logger.warning("NeuralForecast not available. Neural models will be disabled.")

# ML models from mlforecast with fallback
try:
    from mlforecast import MLForecast
    from mlforecast.target_transforms import Differences
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.linear_model import LinearRegression, Ridge, Lasso
    MLFORECAST_AVAILABLE = True
except ImportError:
    MLFORECAST_AVAILABLE = False
    if 'logger' not in globals():
        logger = logging.getLogger(__name__)
    logger.warning("MLForecast or scikit-learn not available. ML models will be disabled.")

logger = logging.getLogger(__name__)

@dataclass
class ForecastResult:
    """Container for forecast results."""
    symbol: str
    predictions: pd.DataFrame
    confidence_intervals: Optional[pd.DataFrame]
    model_name: str
    accuracy_metrics: Dict[str, float]
    forecast_horizon: int
    generated_at: datetime

@dataclass
class ModelConfig:
    """Configuration for different models."""
    model_type: str
    model_name: str
    parameters: Dict[str, Any]
    horizon: int
    frequency: str

class TimeSeriesModelManager:
    """Manages multiple time series forecasting models."""
    
    def __init__(self, nixtla_api_key: Optional[str] = None):
        """
        Initialize the model manager.
        
        Args:
            nixtla_api_key: API key for Nixtla TimeGPT
        """
        self.nixtla_api_key = nixtla_api_key or os.getenv("NIXTLA_API_KEY")
        self.nixtla_client = None
        self.timegpt = None
        self.models = {}
        self.model_configs = self._get_default_configs()
        
        # Initialize Nixtla clients if API key is available
        if self.nixtla_api_key:
            try:
                self.nixtla_client = NixtlaClient(api_key=self.nixtla_api_key)
                if NIXTLATS_AVAILABLE and TimeGPT:
                    self.timegpt = TimeGPT(token=self.nixtla_api_key)
                logger.info("Nixtla TimeGPT clients initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Nixtla clients: {e}")
        
        # Initialize model registry
        self._initialize_models()
    
    def _get_default_configs(self) -> Dict[str, ModelConfig]:
        """Get default configurations for different models."""
        return {
            "timegpt": ModelConfig(
                model_type="foundation",
                model_name="timegpt-1",
                parameters={"level": [80, 90]},
                horizon=30,
                frequency="D"
            ),
            "deepar": ModelConfig(
                model_type="deep_learning",
                model_name="deepar",
                parameters={
                    "prediction_length": 30,
                    "context_length": 60,
                    "num_layers": 2,
                    "num_cells": 40,
                    "dropout_rate": 0.1,
                    "trainer": Trainer(epochs=100, learning_rate=1e-3, num_batches_per_epoch=50)
                },
                horizon=30,
                frequency="D"
            ),
            "transformer": ModelConfig(
                model_type="deep_learning", 
                model_name="transformer",
                parameters={
                    "prediction_length": 30,
                    "context_length": 60,
                    "d_model": 32,
                    "num_heads": 4,
                    "num_encoder_layers": 2,
                    "num_decoder_layers": 2,
                    "trainer": Trainer(epochs=100, learning_rate=1e-3, num_batches_per_epoch=50)
                },
                horizon=30,
                frequency="D"
            ),
            "nbeats": ModelConfig(
                model_type="neural",
                model_name="nbeats",
                parameters={
                    "h": 30,
                    "input_size": 60,
                    "max_steps": 1000,
                    "val_check_steps": 100,
                    "early_stop_patience_steps": 3
                },
                horizon=30,
                frequency="D"
            ),
            "autoarima": ModelConfig(
                model_type="statistical",
                model_name="autoarima",
                parameters={},
                horizon=30,
                frequency="D"
            ),
            "autoets": ModelConfig(
                model_type="statistical",
                model_name="autoets", 
                parameters={},
                horizon=30,
                frequency="D"
            )
        }
    
    def _initialize_models(self):
        """Initialize available models."""
        try:
            # Statistical models
            self.models["statistical"] = StatsForecast(
                models=[
                    AutoARIMA(season_length=252),  # Trading days in a year
                    AutoETS(season_length=252),
                    AutoCES(season_length=252),
                    DynamicOptimizedTheta(season_length=252),
                    MSTL(season_length=[5, 22, 252]),  # Weekly, monthly, yearly
                    SeasonalNaive(season_length=252)
                ],
                freq="D"
            )
            
            # Neural models
            self.models["neural"] = NeuralForecast(
                models=[
                    NBEATS(h=30, input_size=90, max_steps=1000, early_stop_patience_steps=5),
                    NHITS(h=30, input_size=90, max_steps=1000, early_stop_patience_steps=5),
                    NBEATSx(h=30, input_size=90, max_steps=1000, early_stop_patience_steps=5),
                    TiDE(h=30, input_size=90, max_steps=500, early_stop_patience_steps=3),
                    PatchTST(h=30, input_size=90, max_steps=1000, early_stop_patience_steps=5),
                    iTransformer(h=30, input_size=90, max_steps=1000, early_stop_patience_steps=5),
                    TimesNet(h=30, input_size=90, max_steps=800, early_stop_patience_steps=5)
                ],
                freq="D"
            )
            
            # ML models
            self.models["ml"] = MLForecast(
                models=[
                    RandomForestRegressor(n_estimators=100, random_state=42),
                    GradientBoostingRegressor(n_estimators=100, random_state=42),
                    LinearRegression(),
                    Ridge(alpha=1.0),
                    Lasso(alpha=1.0)
                ],
                freq="D",
                target_transforms=[Differences([1, 7, 30])],  # Diff at 1 day, 1 week, 1 month
                lags=[1, 7, 14, 21, 30, 60, 90],
                lag_transforms={
                    1: ["rolling_mean", "rolling_std"],
                    7: ["rolling_mean", "rolling_std"],
                    30: ["rolling_mean", "rolling_std"]
                },
                date_features=["dayofweek", "month", "quarter"],
                num_threads=1
            )
            
            logger.info("Time series models initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing models: {e}")
    
    def predict_ml(
        self,
        data: pd.DataFrame,
        models: List[str] = ["random_forest"],
        horizon: int = 30
    ) -> ForecastResult:
        """
        Generate predictions using ML models.
        
        Args:
            data: Historical price data with 'ds' and 'y' columns
            models: List of ML models to use
            horizon: Number of periods to forecast
            
        Returns:
            ForecastResult object
        """
        try:
            # Prepare data for MLForecast
            ml_data = data.copy()
            if 'unique_id' not in ml_data.columns:
                if 'symbol' in ml_data.columns:
                    ml_data['unique_id'] = ml_data['symbol']
                else:
                    ml_data['unique_id'] = 'stock'
            
            # Ensure proper column names
            if 'ds' not in ml_data.columns and 'date' in ml_data.columns:
                ml_data['ds'] = ml_data['date']
            if 'y' not in ml_data.columns and 'close' in ml_data.columns:
                ml_data['y'] = ml_data['close']
            
            # Create model list
            model_list = []
            for model_name in models:
                if model_name == "random_forest":
                    model_list.append(("RandomForest", RandomForestRegressor(n_estimators=100, random_state=42)))
                elif model_name == "gradient_boosting":
                    model_list.append(("GradientBoosting", GradientBoostingRegressor(n_estimators=100, random_state=42)))
                elif model_name == "linear_regression":
                    model_list.append(("LinearRegression", LinearRegression()))
                elif model_name == "ridge":
                    model_list.append(("Ridge", Ridge(alpha=1.0)))
                elif model_name == "lasso":
                    model_list.append(("Lasso", Lasso(alpha=1.0)))
            
            # Initialize and fit MLForecast
            mlf = MLForecast(
                models=[model[1] for model in model_list],
                freq="D",
                target_transforms=[Differences([1, 7, 30])],
                lags=[1, 7, 14, 21, 30, 60, 90],
                lag_transforms={
                    1: ["rolling_mean", "rolling_std"],
                    7: ["rolling_mean", "rolling_std"],
                    30: ["rolling_mean", "rolling_std"]
                },
                date_features=["dayofweek", "month", "quarter"],
                num_threads=1
            )
            
            # Generate forecast
            forecast = mlf.fit(ml_data).predict(h=horizon)
            
            # Calculate accuracy metrics
            accuracy_metrics = {}
            
            return ForecastResult(
                symbol=ml_data['unique_id'].iloc[0],
                predictions=forecast,
                confidence_intervals=None,
                model_name=f"ML-{'-'.join(models)}",
                accuracy_metrics=accuracy_metrics,
                forecast_horizon=horizon,
                generated_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"ML prediction failed: {e}")
            raise
    
    def predict_timegpt(
        self, 
        data: pd.DataFrame, 
        horizon: int = 30,
        confidence_levels: List[int] = [80, 90],
        model_type: str = "timegpt-1",
        add_history: bool = True,
        finetune_steps: int = 0
    ) -> ForecastResult:
        """
        Generate predictions using Nixtla TimeGPT.
        
        Args:
            data: Historical price data with 'ds' (date) and 'y' (price) columns
            horizon: Number of periods to forecast
            confidence_levels: Confidence levels for intervals
            model_type: TimeGPT model version ("timegpt-1", "timegpt-1-long-horizon")
            add_history: Whether to include historical context
            finetune_steps: Number of fine-tuning steps (0 = no fine-tuning)
            
        Returns:
            ForecastResult object
        """
        if not self.nixtla_client and not self.timegpt:
            raise ValueError("Nixtla client not initialized. Please provide API key.")
        
        try:
            # Prepare data for TimeGPT
            timegpt_data = data.copy()
            if 'unique_id' not in timegpt_data.columns:
                timegpt_data['unique_id'] = timegpt_data.get('symbol', 'stock')
            
            # Use the newer TimeGPT client if available
            if self.timegpt:
                # Enhanced TimeGPT with more features
                forecast = self.timegpt.forecast(
                    df=timegpt_data,
                    h=horizon,
                    level=confidence_levels,
                    freq="D",
                    model=model_type,
                    add_history=add_history,
                    finetune_steps=finetune_steps
                )
            else:
                # Fallback to original client
                forecast = self.nixtla_client.forecast(
                    df=timegpt_data,
                    h=horizon,
                    level=confidence_levels,
                    freq="D"
                )
            
            # Calculate accuracy metrics using cross-validation if enough data
            accuracy_metrics = {}
            if len(timegpt_data) > horizon * 3:
                try:
                    cv_results = self.nixtla_client.cross_validation(
                        df=timegpt_data,
                        h=horizon,
                        step_size=horizon,
                        n_windows=3
                    )
                    
                    # Calculate metrics
                    from statsforecast.utils import ConformalPrediction
                    residuals = cv_results['y'] - cv_results['TimeGPT']
                    accuracy_metrics = {
                        'mae': abs(residuals).mean(),
                        'mse': (residuals ** 2).mean(),
                        'rmse': np.sqrt((residuals ** 2).mean()),
                        'mape': (abs(residuals / cv_results['y']) * 100).mean()
                    }
                except Exception as cv_error:
                    logger.warning(f"Cross-validation failed: {cv_error}")
            
            # Extract confidence intervals
            confidence_intervals = None
            if len(confidence_levels) > 0:
                ci_cols = [col for col in forecast.columns if 'lo-' in col or 'hi-' in col]
                if ci_cols:
                    confidence_intervals = forecast[ci_cols]
            
            return ForecastResult(
                symbol=timegpt_data['unique_id'].iloc[0],
                predictions=forecast[['ds', 'TimeGPT']],
                confidence_intervals=confidence_intervals,
                model_name=f"TimeGPT-{model_type}",
                accuracy_metrics=accuracy_metrics,
                forecast_horizon=horizon,
                generated_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"TimeGPT prediction failed: {e}")
            raise
    
    def predict_gluonts(
        self,
        data: pd.DataFrame,
        model_name: str = "deepar",
        horizon: int = 30,
        use_feat_static_cat: bool = False,
        use_feat_dynamic_real: bool = False
    ) -> ForecastResult:
        """
        Generate predictions using GluonTS models.
        
        Args:
            data: Historical price data
            model_name: Model to use ('deepar', 'transformer', 'feedforward')
            horizon: Number of periods to forecast
            
        Returns:
            ForecastResult object
        """
        try:
            # Prepare data for GluonTS
            train_data = self._prepare_gluonts_data(data, horizon)
            
            # Select and configure model with enhanced settings
            context_length = min(90, len(data) // 2)
            
            if model_name == "deepar":
                estimator = DeepAREstimator(
                    freq="D",
                    prediction_length=horizon,
                    context_length=context_length,
                    num_layers=3,
                    num_cells=60,
                    dropout_rate=0.15,
                    use_feat_static_cat=use_feat_static_cat,
                    use_feat_dynamic_real=use_feat_dynamic_real,
                    trainer=Trainer(
                        epochs=100,
                        learning_rate=1e-3,
                        num_batches_per_epoch=50,
                        patience=10,
                        clip_gradient=10.0
                    )
                )
            elif model_name == "transformer":
                estimator = TransformerEstimator(
                    freq="D",
                    prediction_length=horizon,
                    context_length=context_length,
                    d_model=64,
                    num_heads=8,
                    num_encoder_layers=3,
                    num_decoder_layers=3,
                    dim_feedforward=256,
                    dropout=0.1,
                    use_feat_static_cat=use_feat_static_cat,
                    use_feat_dynamic_real=use_feat_dynamic_real,
                    trainer=Trainer(
                        epochs=100,
                        learning_rate=1e-4,
                        num_batches_per_epoch=50,
                        patience=10,
                        clip_gradient=10.0
                    )
                )
            else:
                estimator = SimpleFeedForwardEstimator(
                    freq="D",
                    prediction_length=horizon,
                    context_length=context_length,
                    num_hidden_dimensions=[64, 32],
                    use_feat_static_cat=use_feat_static_cat,
                    use_feat_dynamic_real=use_feat_dynamic_real,
                    trainer=Trainer(
                        epochs=100,
                        learning_rate=1e-3,
                        num_batches_per_epoch=50,
                        patience=10
                    )
                )
            
            # Train model
            predictor = estimator.train(train_data)
            
            # Generate predictions
            forecast_it = predictor.predict(train_data)
            forecasts = list(forecast_it)
            
            # Process results
            forecast_df = self._process_gluonts_forecast(forecasts[0], data, horizon)
            
            # Calculate accuracy metrics
            accuracy_metrics = self._calculate_gluonts_metrics(forecasts, train_data)
            
            return ForecastResult(
                symbol=data.get('symbol', 'Unknown')[0] if 'symbol' in data.columns else 'Unknown',
                predictions=forecast_df,
                confidence_intervals=None,  # Can be extracted from forecast samples
                model_name=f"GluonTS-{model_name}",
                accuracy_metrics=accuracy_metrics,
                forecast_horizon=horizon,
                generated_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"GluonTS prediction failed: {e}")
            raise
    
    def predict_statistical(
        self,
        data: pd.DataFrame,
        models: List[str] = ["AutoARIMA", "AutoETS"],
        horizon: int = 30
    ) -> ForecastResult:
        """
        Generate predictions using statistical models.
        
        Args:
            data: Historical price data with 'ds' and 'y' columns
            models: List of statistical models to use
            horizon: Number of periods to forecast
            
        Returns:
            ForecastResult object
        """
        try:
            # Prepare data for StatsForecast
            sf_data = data.copy()
            if 'symbol' not in sf_data.columns:
                sf_data['unique_id'] = 'stock'
            else:
                sf_data['unique_id'] = sf_data['symbol']
            
            # Ensure proper column names
            if 'ds' not in sf_data.columns and 'date' in sf_data.columns:
                sf_data['ds'] = sf_data['date']
            if 'y' not in sf_data.columns and 'close' in sf_data.columns:
                sf_data['y'] = sf_data['close']
            
            # Create model list
            model_list = []
            for model_name in models:
                if model_name == "AutoARIMA":
                    model_list.append(AutoARIMA())
                elif model_name == "AutoETS":
                    model_list.append(AutoETS())
                elif model_name == "AutoCES":
                    model_list.append(AutoCES())
                elif model_name == "DynamicOptimizedTheta":
                    model_list.append(DynamicOptimizedTheta())
            
            # Initialize and fit StatsForecast
            sf = StatsForecast(models=model_list, freq="D")
            
            # Generate forecast
            forecast = sf.forecast(df=sf_data, h=horizon, level=[80, 90])
            
            # Calculate accuracy metrics using cross-validation if enough data
            accuracy_metrics = {}
            if len(sf_data) > horizon * 3:
                try:
                    cv_results = sf.cross_validation(df=sf_data, h=horizon, step_size=horizon, n_windows=3)
                    accuracy_metrics = self._calculate_statistical_metrics(cv_results)
                except:
                    pass
            
            return ForecastResult(
                symbol=sf_data['unique_id'].iloc[0],
                predictions=forecast,
                confidence_intervals=forecast[[col for col in forecast.columns if 'lo-' in col or 'hi-' in col]] if any('lo-' in col for col in forecast.columns) else None,
                model_name=f"Statistical-{'-'.join(models)}",
                accuracy_metrics=accuracy_metrics,
                forecast_horizon=horizon,
                generated_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Statistical prediction failed: {e}")
            raise
    
    def predict_neural(
        self,
        data: pd.DataFrame,
        models: List[str] = ["NBEATS"],
        horizon: int = 30,
        accelerator: str = "auto"
    ) -> ForecastResult:
        """
        Generate predictions using neural models.
        
        Args:
            data: Historical price data with 'ds' and 'y' columns
            models: List of neural models to use
            horizon: Number of periods to forecast
            
        Returns:
            ForecastResult object
        """
        try:
            # Prepare data for NeuralForecast
            nf_data = data.copy()
            if 'unique_id' not in nf_data.columns:
                if 'symbol' in nf_data.columns:
                    nf_data['unique_id'] = nf_data['symbol']
                else:
                    nf_data['unique_id'] = 'stock'
            
            # Ensure proper column names
            if 'ds' not in nf_data.columns and 'date' in nf_data.columns:
                nf_data['ds'] = nf_data['date']
            if 'y' not in nf_data.columns and 'close' in nf_data.columns:
                nf_data['y'] = nf_data['close']
            
            # Create model list with enhanced configurations
            input_size = min(90, len(nf_data)//2)
            model_list = []
            for model_name in models:
                if model_name == "NBEATS":
                    model_list.append(NBEATS(
                        h=horizon, 
                        input_size=input_size, 
                        max_steps=1000,
                        early_stop_patience_steps=10,
                        accelerator=accelerator,
                        scaler_type="robust"
                    ))
                elif model_name == "NHITS":
                    model_list.append(NHITS(
                        h=horizon, 
                        input_size=input_size, 
                        max_steps=1000,
                        early_stop_patience_steps=10,
                        accelerator=accelerator,
                        scaler_type="robust"
                    ))
                elif model_name == "NBEATSx":
                    model_list.append(NBEATSx(
                        h=horizon, 
                        input_size=input_size, 
                        max_steps=1000,
                        early_stop_patience_steps=10,
                        accelerator=accelerator,
                        scaler_type="robust"
                    ))
                elif model_name == "TiDE":
                    model_list.append(TiDE(
                        h=horizon, 
                        input_size=input_size, 
                        max_steps=800,
                        early_stop_patience_steps=8,
                        accelerator=accelerator,
                        scaler_type="robust"
                    ))
                elif model_name == "PatchTST":
                    model_list.append(PatchTST(
                        h=horizon,
                        input_size=input_size,
                        max_steps=1000,
                        early_stop_patience_steps=10,
                        accelerator=accelerator,
                        scaler_type="robust"
                    ))
                elif model_name == "iTransformer":
                    model_list.append(iTransformer(
                        h=horizon,
                        input_size=input_size,
                        max_steps=1000,
                        early_stop_patience_steps=10,
                        accelerator=accelerator,
                        scaler_type="robust"
                    ))
                elif model_name == "TimesNet":
                    model_list.append(TimesNet(
                        h=horizon,
                        input_size=input_size,
                        max_steps=800,
                        early_stop_patience_steps=8,
                        accelerator=accelerator,
                        scaler_type="robust"
                    ))
            
            # Initialize and fit NeuralForecast
            nf = NeuralForecast(models=model_list, freq="D")
            
            # Generate forecast
            forecast = nf.fit(nf_data).predict()
            
            # Calculate accuracy metrics
            accuracy_metrics = {}
            
            return ForecastResult(
                symbol=nf_data['unique_id'].iloc[0],
                predictions=forecast,
                confidence_intervals=None,
                model_name=f"Neural-{'-'.join(models)}",
                accuracy_metrics=accuracy_metrics,
                forecast_horizon=horizon,
                generated_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Neural prediction failed: {e}")
            raise
    
    def ensemble_predict(
        self,
        data: pd.DataFrame,
        models: List[str] = ["timegpt", "statistical", "neural"],
        horizon: int = 30,
        weights: Optional[Dict[str, float]] = None
    ) -> ForecastResult:
        """
        Generate ensemble predictions combining multiple models.
        
        Args:
            data: Historical price data
            models: List of model types to ensemble
            horizon: Number of periods to forecast
            weights: Optional weights for different models
            
        Returns:
            ForecastResult object with ensemble predictions
        """
        try:
            predictions = {}
            all_metrics = {}
            
            # Generate predictions from each model
            for model_type in models:
                try:
                    if model_type == "timegpt" and self.nixtla_client:
                        result = self.predict_timegpt(data, horizon)
                        predictions[model_type] = result.predictions
                        all_metrics[model_type] = result.accuracy_metrics
                        
                    elif model_type == "statistical":
                        result = self.predict_statistical(data, horizon=horizon)
                        predictions[model_type] = result.predictions
                        all_metrics[model_type] = result.accuracy_metrics
                        
                    elif model_type == "neural":
                        result = self.predict_neural(data, horizon=horizon)
                        predictions[model_type] = result.predictions
                        all_metrics[model_type] = result.accuracy_metrics
                        
                    elif model_type == "ml":
                        result = self.predict_ml(data, horizon=horizon)
                        predictions[model_type] = result.predictions
                        all_metrics[model_type] = result.accuracy_metrics
                        
                    elif model_type == "deepar":
                        result = self.predict_gluonts(data, "deepar", horizon)
                        predictions[model_type] = result.predictions
                        all_metrics[model_type] = result.accuracy_metrics
                        
                except Exception as e:
                    logger.warning(f"Failed to generate predictions for {model_type}: {e}")
            
            if not predictions:
                raise ValueError("No models generated successful predictions")
            
            # Combine predictions
            ensemble_forecast = self._combine_predictions(predictions, weights)
            
            return ForecastResult(
                symbol=data.get('symbol', 'Unknown')[0] if 'symbol' in data.columns else 'Unknown',
                predictions=ensemble_forecast,
                confidence_intervals=None,
                model_name=f"Ensemble-{'-'.join(predictions.keys())}",
                accuracy_metrics=all_metrics,
                forecast_horizon=horizon,
                generated_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Ensemble prediction failed: {e}")
            raise
    
    def _prepare_gluonts_data(self, data: pd.DataFrame, horizon: int):
        """Prepare data for GluonTS models."""
        # Convert to appropriate format
        if 'close' in data.columns:
            target = data['close'].values
        elif 'y' in data.columns:
            target = data['y'].values
        else:
            target = data.iloc[:, -1].values  # Use last column
        
        if not GLUONTS_AVAILABLE:
            raise ValueError("GluonTS not available")
            
        # Create GluonTS dataset
        start_date = pd.to_datetime(data.iloc[0]['ds'] if 'ds' in data.columns else data.index[0])
        
        train_data = ListDataset(
            [{"target": target[:-horizon], "start": start_date}] if len(target) > horizon else [{"target": target, "start": start_date}],
            freq="D"
        )
        
        return train_data
    
    def _process_gluonts_forecast(self, forecast, original_data: pd.DataFrame, horizon: int) -> pd.DataFrame:
        """Process GluonTS forecast results."""
        # Extract mean forecast
        mean_forecast = forecast.mean
        
        # Create date range for forecast
        last_date = pd.to_datetime(original_data.iloc[-1]['ds'] if 'ds' in original_data.columns else original_data.index[-1])
        forecast_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=horizon, freq='D')
        
        # Create forecast DataFrame
        forecast_df = pd.DataFrame({
            'ds': forecast_dates,
            'prediction': mean_forecast
        })
        
        return forecast_df
    
    def _calculate_gluonts_metrics(self, forecasts, train_data) -> Dict[str, float]:
        """Calculate accuracy metrics for GluonTS models."""
        if not GLUONTS_AVAILABLE:
            return {}
            
        try:
            evaluator = Evaluator(quantiles=[0.1, 0.5, 0.9])
            agg_metrics, _ = evaluator(iter(forecasts), train_data)
            
            return {
                "mse": agg_metrics.get("MSE", 0.0),
                "mape": agg_metrics.get("MAPE", 0.0),
                "smape": agg_metrics.get("sMAPE", 0.0)
            }
        except:
            return {}
    
    def _calculate_statistical_metrics(self, cv_results: pd.DataFrame) -> Dict[str, float]:
        """Calculate accuracy metrics for statistical models."""
        try:
            # Calculate common metrics
            metrics = {}
            for model_col in cv_results.columns:
                if model_col not in ['unique_id', 'ds', 'cutoff', 'y']:
                    residuals = cv_results['y'] - cv_results[model_col]
                    metrics[f"{model_col}_mse"] = (residuals ** 2).mean()
                    metrics[f"{model_col}_mae"] = abs(residuals).mean()
                    metrics[f"{model_col}_mape"] = (abs(residuals / cv_results['y']) * 100).mean()
            
            return metrics
        except:
            return {}
    
    def _combine_predictions(
        self, 
        predictions: Dict[str, pd.DataFrame], 
        weights: Optional[Dict[str, float]] = None
    ) -> pd.DataFrame:
        """Combine predictions from multiple models."""
        if weights is None:
            # Equal weights
            weights = {model: 1.0 / len(predictions) for model in predictions.keys()}
        
        # Normalize weights
        total_weight = sum(weights.values())
        weights = {k: v / total_weight for k, v in weights.items()}
        
        # Find common structure
        base_df = None
        prediction_cols = []
        
        for model_name, pred_df in predictions.items():
            if base_df is None:
                base_df = pred_df[['ds']].copy() if 'ds' in pred_df.columns else pred_df.index.to_frame()
            
            # Find prediction column
            pred_col = None
            for col in pred_df.columns:
                if col not in ['ds', 'unique_id', 'cutoff'] and not col.startswith('lo-') and not col.startswith('hi-'):
                    pred_col = col
                    break
            
            if pred_col:
                prediction_cols.append((model_name, pred_col, pred_df))
        
        # Combine predictions
        ensemble_pred = None
        for model_name, pred_col, pred_df in prediction_cols:
            weight = weights.get(model_name, 0)
            if ensemble_pred is None:
                ensemble_pred = pred_df[pred_col] * weight
            else:
                ensemble_pred += pred_df[pred_col] * weight
        
        # Create result DataFrame
        result_df = base_df.copy()
        result_df['ensemble_prediction'] = ensemble_pred
        
        return result_df
    
    def get_available_models(self) -> Dict[str, List[str]]:
        """Get list of available models by category."""
        return {
            "foundation": ["timegpt", "timegpt-long-horizon"] if self.nixtla_client else [],
            "deep_learning": ["deepar", "transformer", "feedforward"],
            "neural": ["nbeats", "nhits", "nbeatsx", "tide", "patchtst", "itransformer", "timesnet"],
            "statistical": ["autoarima", "autoets", "autoces", "theta", "mstl", "seasonal_naive"],
            "ml": ["random_forest", "gradient_boosting", "linear_regression", "ridge", "lasso"],
            "ensemble": ["combined", "weighted_average", "stacking"]
        }
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """Validate input data for forecasting."""
        required_cols = ['ds', 'y'] if 'ds' in data.columns else ['date', 'close']
        
        if not all(col in data.columns for col in required_cols):
            logger.error(f"Data must contain columns: {required_cols}")
            return False
        
        if len(data) < 30:
            logger.error("Data must contain at least 30 observations")
            return False
        
        return True