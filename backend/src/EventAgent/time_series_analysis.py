"""
Time Series Analysis module for financial data and portfolio performance.
Provides advanced analytics including trend analysis, seasonality, forecasting, and correlation analysis.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from pydantic import BaseModel
import json
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler


@dataclass
class TrendAnalysis:
    """Results of trend analysis."""
    trend_direction: str  # "upward", "downward", "sideways"
    trend_strength: float  # 0-1 scale
    trend_slope: float
    r_squared: float
    support_level: Optional[float] = None
    resistance_level: Optional[float] = None


@dataclass
class SeasonalityAnalysis:
    """Results of seasonality analysis."""
    has_seasonality: bool
    seasonal_pattern: Dict[str, float]  # e.g., {"Monday": -0.5, "Tuesday": 0.2, ...}
    seasonal_strength: float
    best_performing_period: str
    worst_performing_period: str


@dataclass
class VolatilityAnalysis:
    """Results of volatility analysis."""
    current_volatility: float
    volatility_percentile: float  # Current vol vs historical
    volatility_regime: str  # "low", "normal", "high"
    volatility_clustering: bool
    garch_forecast: Optional[float] = None


@dataclass
class CorrelationAnalysis:
    """Results of correlation analysis."""
    correlations: Dict[str, float]
    average_correlation: float
    max_correlation: float
    min_correlation: float
    correlation_stability: float
    diversification_ratio: float


class ForecastResult(BaseModel):
    """Forecasting results."""
    method: str
    forecast_values: List[float]
    confidence_intervals: List[Tuple[float, float]]
    forecast_dates: List[str]
    accuracy_metrics: Dict[str, float]
    forecast_horizon_days: int


class TimeSeriesMetrics(BaseModel):
    """Comprehensive time series metrics."""
    mean_return: float
    volatility: float
    skewness: float
    kurtosis: float
    jarque_bera_stat: float
    jarque_bera_pvalue: float
    adf_stat: float
    adf_pvalue: float
    is_stationary: bool
    autocorrelation_lag1: float
    max_drawdown: float
    calmar_ratio: float


class TimeSeriesAnalyzer:
    """Advanced time series analysis for financial data."""
    
    def __init__(self):
        """Initialize the time series analyzer."""
        self.scaler = StandardScaler()
    
    def analyze_trend(self, data: pd.Series, window: int = 30) -> TrendAnalysis:
        """Analyze trend in time series data."""
        if len(data) < window:
            return TrendAnalysis(
                trend_direction="insufficient_data",
                trend_strength=0.0,
                trend_slope=0.0,
                r_squared=0.0
            )
        
        # Prepare data for linear regression
        x = np.arange(len(data)).reshape(-1, 1)
        y = data.values
        
        # Fit linear regression
        reg = LinearRegression()
        reg.fit(x, y)
        
        # Calculate R-squared
        y_pred = reg.predict(x)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # Determine trend direction and strength
        slope = reg.coef_[0]
        
        if abs(slope) < 0.001:  # Threshold for sideways movement
            trend_direction = "sideways"
        elif slope > 0:
            trend_direction = "upward"
        else:
            trend_direction = "downward"
        
        trend_strength = min(abs(r_squared), 1.0)
        
        # Calculate support and resistance levels
        rolling_min = data.rolling(window=window).min()
        rolling_max = data.rolling(window=window).max()
        
        support_level = rolling_min.iloc[-1] if len(rolling_min) > 0 else None
        resistance_level = rolling_max.iloc[-1] if len(rolling_max) > 0 else None
        
        return TrendAnalysis(
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            trend_slope=slope,
            r_squared=r_squared,
            support_level=support_level,
            resistance_level=resistance_level
        )
    
    def analyze_seasonality(self, data: pd.Series, freq: str = "daily") -> SeasonalityAnalysis:
        """Analyze seasonal patterns in time series data."""
        if len(data) < 50:  # Need sufficient data for seasonality analysis
            return SeasonalityAnalysis(
                has_seasonality=False,
                seasonal_pattern={},
                seasonal_strength=0.0,
                best_performing_period="unknown",
                worst_performing_period="unknown"
            )
        
        seasonal_pattern = {}
        
        if freq == "daily":
            # Day of week analysis
            data_with_dow = data.to_frame()
            data_with_dow['day_of_week'] = data.index.day_name()
            seasonal_stats = data_with_dow.groupby('day_of_week')[data.name or 0].mean()
            seasonal_pattern = seasonal_stats.to_dict()
            
        elif freq == "monthly":
            # Month analysis
            data_with_month = data.to_frame()
            data_with_month['month'] = data.index.month_name()
            seasonal_stats = data_with_month.groupby('month')[data.name or 0].mean()
            seasonal_pattern = seasonal_stats.to_dict()
        
        # Calculate seasonal strength
        if seasonal_pattern:
            values = list(seasonal_pattern.values())
            seasonal_strength = np.std(values) / np.mean(np.abs(values)) if np.mean(np.abs(values)) > 0 else 0
            
            best_period = max(seasonal_pattern, key=seasonal_pattern.get)
            worst_period = min(seasonal_pattern, key=seasonal_pattern.get)
            
            has_seasonality = seasonal_strength > 0.1  # Threshold for meaningful seasonality
        else:
            seasonal_strength = 0.0
            best_period = "unknown"
            worst_period = "unknown"
            has_seasonality = False
        
        return SeasonalityAnalysis(
            has_seasonality=has_seasonality,
            seasonal_pattern=seasonal_pattern,
            seasonal_strength=seasonal_strength,
            best_performing_period=best_period,
            worst_performing_period=worst_period
        )
    
    def analyze_volatility(self, returns: pd.Series, window: int = 30) -> VolatilityAnalysis:
        """Analyze volatility patterns in returns data."""
        if len(returns) < window:
            return VolatilityAnalysis(
                current_volatility=0.0,
                volatility_percentile=0.0,
                volatility_regime="unknown",
                volatility_clustering=False
            )
        
        # Calculate rolling volatility
        rolling_vol = returns.rolling(window=window).std() * np.sqrt(252)  # Annualized
        current_volatility = rolling_vol.iloc[-1] if len(rolling_vol) > 0 else 0.0
        
        # Calculate volatility percentile
        volatility_percentile = stats.percentileofscore(rolling_vol.dropna(), current_volatility)
        
        # Determine volatility regime
        if volatility_percentile < 25:
            volatility_regime = "low"
        elif volatility_percentile > 75:
            volatility_regime = "high"
        else:
            volatility_regime = "normal"
        
        # Test for volatility clustering (ARCH effect)
        squared_returns = returns ** 2
        if len(squared_returns) > 10:
            # Simple test: correlation between consecutive squared returns
            autocorr = squared_returns.autocorr(lag=1)
            volatility_clustering = autocorr > 0.1 and not np.isnan(autocorr)
        else:
            volatility_clustering = False
        
        return VolatilityAnalysis(
            current_volatility=current_volatility,
            volatility_percentile=volatility_percentile / 100,
            volatility_regime=volatility_regime,
            volatility_clustering=volatility_clustering
        )
    
    def analyze_correlations(
        self, 
        portfolio_returns: pd.Series, 
        asset_returns: Dict[str, pd.Series],
        market_returns: Optional[pd.Series] = None
    ) -> CorrelationAnalysis:
        """Analyze correlation patterns between portfolio and assets."""
        correlations = {}
        
        # Calculate correlations with individual assets
        for asset, returns in asset_returns.items():
            if len(returns) > 10 and len(portfolio_returns) > 10:
                # Align the series
                aligned_portfolio, aligned_asset = portfolio_returns.align(returns, join='inner')
                if len(aligned_portfolio) > 10:
                    corr = aligned_portfolio.corr(aligned_asset)
                    if not np.isnan(corr):
                        correlations[asset] = corr
        
        # Calculate correlation with market if provided
        if market_returns is not None and len(market_returns) > 10:
            aligned_portfolio, aligned_market = portfolio_returns.align(market_returns, join='inner')
            if len(aligned_portfolio) > 10:
                market_corr = aligned_portfolio.corr(aligned_market)
                if not np.isnan(market_corr):
                    correlations["market"] = market_corr
        
        # Calculate summary statistics
        if correlations:
            corr_values = list(correlations.values())
            average_correlation = np.mean(corr_values)
            max_correlation = np.max(corr_values)
            min_correlation = np.min(corr_values)
            
            # Correlation stability (inverse of standard deviation)
            correlation_stability = 1 - (np.std(corr_values) / 2) if len(corr_values) > 1 else 1.0
            
            # Diversification ratio (simplified)
            diversification_ratio = 1 - average_correlation if average_correlation > 0 else 1.0
        else:
            average_correlation = 0.0
            max_correlation = 0.0
            min_correlation = 0.0
            correlation_stability = 0.0
            diversification_ratio = 1.0
        
        return CorrelationAnalysis(
            correlations=correlations,
            average_correlation=average_correlation,
            max_correlation=max_correlation,
            min_correlation=min_correlation,
            correlation_stability=correlation_stability,
            diversification_ratio=diversification_ratio
        )
    
    def calculate_metrics(self, data: pd.Series) -> TimeSeriesMetrics:
        """Calculate comprehensive time series metrics."""
        if len(data) < 10:
            return TimeSeriesMetrics(
                mean_return=0.0, volatility=0.0, skewness=0.0, kurtosis=0.0,
                jarque_bera_stat=0.0, jarque_bera_pvalue=1.0,
                adf_stat=0.0, adf_pvalue=1.0, is_stationary=False,
                autocorrelation_lag1=0.0, max_drawdown=0.0, calmar_ratio=0.0
            )
        
        # Basic statistics
        mean_return = data.mean()
        volatility = data.std() * np.sqrt(252) if len(data) > 1 else 0.0
        skewness = stats.skew(data.dropna())
        kurtosis = stats.kurtosis(data.dropna())
        
        # Normality test
        jb_stat, jb_pvalue = stats.jarque_bera(data.dropna())
        
        # Stationarity test (simplified ADF test)
        try:
            from statsmodels.tsa.stattools import adfuller
            adf_result = adfuller(data.dropna())
            adf_stat = adf_result[0]
            adf_pvalue = adf_result[1]
            is_stationary = adf_pvalue < 0.05
        except ImportError:
            # Fallback if statsmodels not available
            adf_stat = 0.0
            adf_pvalue = 1.0
            is_stationary = False
        
        # Autocorrelation
        if len(data) > 2:
            autocorr_lag1 = data.autocorr(lag=1)
            if np.isnan(autocorr_lag1):
                autocorr_lag1 = 0.0
        else:
            autocorr_lag1 = 0.0
        
        # Maximum drawdown
        cumulative = (1 + data).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = abs(drawdown.min()) if not drawdown.empty else 0.0
        
        # Calmar ratio
        annual_return = mean_return * 252
        calmar_ratio = annual_return / max_drawdown if max_drawdown > 0 else 0.0
        
        return TimeSeriesMetrics(
            mean_return=mean_return,
            volatility=volatility,
            skewness=skewness,
            kurtosis=kurtosis,
            jarque_bera_stat=jb_stat,
            jarque_bera_pvalue=jb_pvalue,
            adf_stat=adf_stat,
            adf_pvalue=adf_pvalue,
            is_stationary=is_stationary,
            autocorrelation_lag1=autocorr_lag1,
            max_drawdown=max_drawdown,
            calmar_ratio=calmar_ratio
        )
    
    def simple_forecast(
        self, 
        data: pd.Series, 
        forecast_horizon: int = 10,
        method: str = "linear_trend"
    ) -> ForecastResult:
        """Simple forecasting methods."""
        if len(data) < 10:
            return ForecastResult(
                method=method,
                forecast_values=[],
                confidence_intervals=[],
                forecast_dates=[],
                accuracy_metrics={},
                forecast_horizon_days=forecast_horizon
            )
        
        forecast_values = []
        confidence_intervals = []
        forecast_dates = []
        
        # Generate forecast dates
        last_date = data.index[-1]
        for i in range(1, forecast_horizon + 1):
            forecast_date = last_date + timedelta(days=i)
            forecast_dates.append(forecast_date.strftime("%Y-%m-%d"))
        
        if method == "linear_trend":
            # Linear trend extrapolation
            x = np.arange(len(data))
            y = data.values
            
            reg = LinearRegression()
            reg.fit(x.reshape(-1, 1), y)
            
            # Forecast
            forecast_x = np.arange(len(data), len(data) + forecast_horizon)
            forecast_values = reg.predict(forecast_x.reshape(-1, 1)).tolist()
            
            # Simple confidence intervals (using residual standard error)
            residuals = y - reg.predict(x.reshape(-1, 1))
            residual_std = np.std(residuals)
            
            confidence_intervals = [
                (val - 1.96 * residual_std, val + 1.96 * residual_std)
                for val in forecast_values
            ]
            
        elif method == "moving_average":
            # Simple moving average
            window = min(30, len(data) // 2)
            ma_value = data.tail(window).mean()
            
            forecast_values = [ma_value] * forecast_horizon
            
            # Confidence intervals based on historical volatility
            volatility = data.tail(window).std()
            confidence_intervals = [
                (ma_value - 1.96 * volatility, ma_value + 1.96 * volatility)
                for _ in range(forecast_horizon)
            ]
        
        # Calculate simple accuracy metrics (using last period as test)
        if len(data) > 20:
            test_size = min(10, len(data) // 4)
            train_data = data[:-test_size]
            test_data = data[-test_size:]
            
            # Forecast test period
            test_forecast = self.simple_forecast(train_data, test_size, method)
            
            if test_forecast.forecast_values:
                mae = np.mean(np.abs(np.array(test_forecast.forecast_values) - test_data.values))
                rmse = np.sqrt(np.mean((np.array(test_forecast.forecast_values) - test_data.values) ** 2))
                
                accuracy_metrics = {
                    "mae": mae,
                    "rmse": rmse,
                    "mape": np.mean(np.abs((test_data.values - np.array(test_forecast.forecast_values)) / test_data.values)) * 100
                }
            else:
                accuracy_metrics = {}
        else:
            accuracy_metrics = {}
        
        return ForecastResult(
            method=method,
            forecast_values=forecast_values,
            confidence_intervals=confidence_intervals,
            forecast_dates=forecast_dates,
            accuracy_metrics=accuracy_metrics,
            forecast_horizon_days=forecast_horizon
        )
    
    def detect_anomalies(self, data: pd.Series, method: str = "zscore", threshold: float = 3.0) -> Dict[str, Any]:
        """Detect anomalies in time series data."""
        if len(data) < 10:
            return {"anomalies": [], "method": method, "threshold": threshold}
        
        anomalies = []
        
        if method == "zscore":
            # Z-score method
            z_scores = np.abs(stats.zscore(data.dropna()))
            anomaly_indices = np.where(z_scores > threshold)[0]
            
            for idx in anomaly_indices:
                anomalies.append({
                    "date": data.index[idx].strftime("%Y-%m-%d"),
                    "value": data.iloc[idx],
                    "z_score": z_scores[idx],
                    "severity": "high" if z_scores[idx] > threshold * 1.5 else "medium"
                })
        
        elif method == "iqr":
            # Interquartile range method
            Q1 = data.quantile(0.25)
            Q3 = data.quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            
            anomaly_mask = (data < lower_bound) | (data > upper_bound)
            anomaly_data = data[anomaly_mask]
            
            for date, value in anomaly_data.items():
                severity = "high" if (value < lower_bound - IQR) or (value > upper_bound + IQR) else "medium"
                anomalies.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "value": value,
                    "bound_violation": "lower" if value < lower_bound else "upper",
                    "severity": severity
                })
        
        return {
            "anomalies": anomalies,
            "method": method,
            "threshold": threshold,
            "total_anomalies": len(anomalies),
            "anomaly_rate": len(anomalies) / len(data) * 100
        }


# Global analyzer instance
_ts_analyzer = None

def get_time_series_analyzer() -> TimeSeriesAnalyzer:
    """Get the global time series analyzer instance."""
    global _ts_analyzer
    if _ts_analyzer is None:
        _ts_analyzer = TimeSeriesAnalyzer()
    return _ts_analyzer