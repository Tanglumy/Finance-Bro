"""
Built-in functions and indicators for the formula engine.
"""

import pandas as pd
import numpy as np
import pandas_ta as ta
from typing import Union, List, Optional, Any, Dict
import logging

logger = logging.getLogger(__name__)

class IndicatorLibrary:
    """Library of technical indicators and mathematical functions."""
    
    def __init__(self):
        self.functions = {
            # Moving averages
            'MA': self.moving_average,
            'SMA': self.simple_moving_average,
            'EMA': self.exponential_moving_average,
            'WMA': self.weighted_moving_average,
            'VWMA': self.volume_weighted_moving_average,
            
            # Momentum indicators
            'RSI': self.relative_strength_index,
            'MACD': self.macd,
            'STOCH': self.stochastic,
            'MOMENTUM': self.momentum,
            'ROC': self.rate_of_change,
            'MFI': self.money_flow_index,
            
            # Volatility indicators
            'BB': self.bollinger_bands,
            'ATR': self.average_true_range,
            'KC': self.keltner_channels,
            'DONCHIAN': self.donchian_channels,
            
            # Trend indicators
            'ADX': self.average_directional_index,
            'AROON': self.aroon,
            'PSAR': self.parabolic_sar,
            'SUPERTREND': self.supertrend,
            
            # Volume indicators
            'OBV': self.on_balance_volume,
            'AD': self.accumulation_distribution,
            'CMF': self.chaikin_money_flow,
            'VWAP': self.volume_weighted_average_price,
            
            # Mathematical functions
            'ABS': self.absolute,
            'MAX': self.maximum,
            'MIN': self.minimum,
            'SUM': self.sum,
            'MEAN': self.mean,
            'MEDIAN': self.median,
            'STD': self.standard_deviation,
            'VAR': self.variance,
            'CORR': self.correlation,
            'RANK': self.rank,
            'PERCENTILE': self.percentile,
            
            # Statistical functions
            'ZSCORE': self.z_score,
            'BETA': self.beta,
            'ALPHA': self.alpha,
            'SHARPE': self.sharpe_ratio,
            'SORTINO': self.sortino_ratio,
            'DRAWDOWN': self.drawdown,
            
            # Logical functions
            'IF': self.if_then_else,
            'AND': self.logical_and,
            'OR': self.logical_or,
            'NOT': self.logical_not,
            
            # Date/Time functions
            'YEAR': self.year,
            'MONTH': self.month,
            'DAY': self.day,
            'WEEKDAY': self.weekday,
            'DAYOFYEAR': self.day_of_year,
            
            # Utility functions
            'SHIFT': self.shift,
            'DIFF': self.diff,
            'PCT_CHANGE': self.pct_change,
            'CUMSUM': self.cumsum,
            'CUMPROD': self.cumprod,
            'ROLLING': self.rolling,
            'RESAMPLE': self.resample,
            
            # Constants
            'PI': np.pi,
            'E': np.e,
            'TRUE': True,
            'FALSE': False,
            'NULL': np.nan,
            
            # Signal functions
            'BUY': 1,
            'SELL': -1,
            'HOLD': 0,
            'LONG': 1,
            'SHORT': -1,
            'NEUTRAL': 0,
        }
    
    def get_function(self, name: str):
        """Get function by name."""
        return self.functions.get(name.upper())
    
    def list_functions(self) -> List[str]:
        """List all available functions."""
        return list(self.functions.keys())
    
    # Moving Averages
    def moving_average(self, series: pd.Series, window: int) -> pd.Series:
        """Simple moving average."""
        return series.rolling(window=window).mean()
    
    def simple_moving_average(self, series: pd.Series, window: int) -> pd.Series:
        """Simple moving average."""
        return self.moving_average(series, window)
    
    def exponential_moving_average(self, series: pd.Series, window: int) -> pd.Series:
        """Exponential moving average."""
        return series.ewm(span=window).mean()
    
    def weighted_moving_average(self, series: pd.Series, window: int) -> pd.Series:
        """Weighted moving average."""
        weights = np.arange(1, window + 1)
        return series.rolling(window=window).apply(
            lambda x: np.average(x, weights=weights)
        )
    
    def volume_weighted_moving_average(self, price: pd.Series, volume: pd.Series, window: int) -> pd.Series:
        """Volume weighted moving average."""
        return (price * volume).rolling(window=window).sum() / volume.rolling(window=window).sum()
    
    # Momentum Indicators
    def relative_strength_index(self, series: pd.Series, window: int = 14) -> pd.Series:
        """Relative Strength Index."""
        return ta.rsi(series, length=window)
    
    def macd(self, series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """MACD indicator."""
        return ta.macd(series, fast=fast, slow=slow, signal=signal)
    
    def stochastic(self, high: pd.Series, low: pd.Series, close: pd.Series, 
                   k_period: int = 14, d_period: int = 3) -> pd.DataFrame:
        """Stochastic oscillator."""
        return ta.stoch(high, low, close, k=k_period, d=d_period)
    
    def momentum(self, series: pd.Series, window: int = 10) -> pd.Series:
        """Momentum indicator."""
        return series.diff(window)
    
    def rate_of_change(self, series: pd.Series, window: int = 10) -> pd.Series:
        """Rate of change."""
        return ta.roc(series, length=window)
    
    def money_flow_index(self, high: pd.Series, low: pd.Series, close: pd.Series, 
                        volume: pd.Series, window: int = 14) -> pd.Series:
        """Money Flow Index."""
        return ta.mfi(high, low, close, volume, length=window)
    
    # Volatility Indicators
    def bollinger_bands(self, series: pd.Series, window: int = 20, std_dev: float = 2) -> pd.DataFrame:
        """Bollinger Bands."""
        return ta.bbands(series, length=window, std=std_dev)
    
    def average_true_range(self, high: pd.Series, low: pd.Series, close: pd.Series, 
                          window: int = 14) -> pd.Series:
        """Average True Range."""
        return ta.atr(high, low, close, length=window)
    
    def keltner_channels(self, high: pd.Series, low: pd.Series, close: pd.Series, 
                        window: int = 20, multiplier: float = 2) -> pd.DataFrame:
        """Keltner Channels."""
        return ta.kc(high, low, close, length=window, scalar=multiplier)
    
    def donchian_channels(self, high: pd.Series, low: pd.Series, window: int = 20) -> pd.DataFrame:
        """Donchian Channels."""
        return ta.donchian(high, low, length=window)
    
    # Trend Indicators
    def average_directional_index(self, high: pd.Series, low: pd.Series, close: pd.Series, 
                                 window: int = 14) -> pd.Series:
        """Average Directional Index."""
        return ta.adx(high, low, close, length=window)
    
    def aroon(self, high: pd.Series, low: pd.Series, window: int = 14) -> pd.DataFrame:
        """Aroon indicator."""
        return ta.aroon(high, low, length=window)
    
    def parabolic_sar(self, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
        """Parabolic SAR."""
        return ta.psar(high, low, close)
    
    def supertrend(self, high: pd.Series, low: pd.Series, close: pd.Series, 
                   window: int = 10, multiplier: float = 3) -> pd.DataFrame:
        """SuperTrend indicator."""
        return ta.supertrend(high, low, close, length=window, multiplier=multiplier)
    
    # Volume Indicators
    def on_balance_volume(self, close: pd.Series, volume: pd.Series) -> pd.Series:
        """On Balance Volume."""
        return ta.obv(close, volume)
    
    def accumulation_distribution(self, high: pd.Series, low: pd.Series, 
                                 close: pd.Series, volume: pd.Series) -> pd.Series:
        """Accumulation/Distribution Line."""
        return ta.ad(high, low, close, volume)
    
    def chaikin_money_flow(self, high: pd.Series, low: pd.Series, 
                          close: pd.Series, volume: pd.Series, window: int = 20) -> pd.Series:
        """Chaikin Money Flow."""
        return ta.cmf(high, low, close, volume, length=window)
    
    def volume_weighted_average_price(self, high: pd.Series, low: pd.Series, 
                                     close: pd.Series, volume: pd.Series) -> pd.Series:
        """Volume Weighted Average Price."""
        return ta.vwap(high, low, close, volume)
    
    # Mathematical Functions
    def absolute(self, series: pd.Series) -> pd.Series:
        """Absolute value."""
        return series.abs()
    
    def maximum(self, series: pd.Series, window: int) -> pd.Series:
        """Rolling maximum."""
        return series.rolling(window=window).max()
    
    def minimum(self, series: pd.Series, window: int) -> pd.Series:
        """Rolling minimum."""
        return series.rolling(window=window).min()
    
    def sum(self, series: pd.Series, window: int) -> pd.Series:
        """Rolling sum."""
        return series.rolling(window=window).sum()
    
    def mean(self, series: pd.Series, window: int) -> pd.Series:
        """Rolling mean."""
        return series.rolling(window=window).mean()
    
    def median(self, series: pd.Series, window: int) -> pd.Series:
        """Rolling median."""
        return series.rolling(window=window).median()
    
    def standard_deviation(self, series: pd.Series, window: int) -> pd.Series:
        """Rolling standard deviation."""
        return series.rolling(window=window).std()
    
    def variance(self, series: pd.Series, window: int) -> pd.Series:
        """Rolling variance."""
        return series.rolling(window=window).var()
    
    def correlation(self, series1: pd.Series, series2: pd.Series, window: int) -> pd.Series:
        """Rolling correlation."""
        return series1.rolling(window=window).corr(series2)
    
    def rank(self, series: pd.Series, window: int) -> pd.Series:
        """Rolling rank."""
        return series.rolling(window=window).rank()
    
    def percentile(self, series: pd.Series, window: int, percentile: float) -> pd.Series:
        """Rolling percentile."""
        return series.rolling(window=window).quantile(percentile / 100.0)
    
    # Statistical Functions
    def z_score(self, series: pd.Series, window: int) -> pd.Series:
        """Z-score (standardized score)."""
        mean = series.rolling(window=window).mean()
        std = series.rolling(window=window).std()
        return (series - mean) / std
    
    def beta(self, stock_returns: pd.Series, market_returns: pd.Series, window: int) -> pd.Series:
        """Beta coefficient."""
        covariance = stock_returns.rolling(window=window).cov(market_returns)
        market_variance = market_returns.rolling(window=window).var()
        return covariance / market_variance
    
    def alpha(self, stock_returns: pd.Series, market_returns: pd.Series, 
              risk_free_rate: float, window: int) -> pd.Series:
        """Alpha coefficient."""
        beta = self.beta(stock_returns, market_returns, window)
        stock_mean = stock_returns.rolling(window=window).mean()
        market_mean = market_returns.rolling(window=window).mean()
        return stock_mean - risk_free_rate - beta * (market_mean - risk_free_rate)
    
    def sharpe_ratio(self, returns: pd.Series, risk_free_rate: float, window: int) -> pd.Series:
        """Sharpe ratio."""
        excess_returns = returns - risk_free_rate
        return excess_returns.rolling(window=window).mean() / excess_returns.rolling(window=window).std()
    
    def sortino_ratio(self, returns: pd.Series, risk_free_rate: float, window: int) -> pd.Series:
        """Sortino ratio."""
        excess_returns = returns - risk_free_rate
        downside_returns = excess_returns.where(excess_returns < 0, 0)
        downside_std = downside_returns.rolling(window=window).std()
        return excess_returns.rolling(window=window).mean() / downside_std
    
    def drawdown(self, series: pd.Series) -> pd.Series:
        """Drawdown calculation."""
        cumulative = series.cumsum()
        running_max = cumulative.expanding().max()
        return (cumulative - running_max) / running_max
    
    # Logical Functions
    def if_then_else(self, condition: pd.Series, true_value: Any, false_value: Any) -> pd.Series:
        """If-then-else conditional."""
        return pd.Series(np.where(condition, true_value, false_value), index=condition.index)
    
    def logical_and(self, series1: pd.Series, series2: pd.Series) -> pd.Series:
        """Logical AND."""
        return series1 & series2
    
    def logical_or(self, series1: pd.Series, series2: pd.Series) -> pd.Series:
        """Logical OR."""
        return series1 | series2
    
    def logical_not(self, series: pd.Series) -> pd.Series:
        """Logical NOT."""
        return ~series
    
    # Date/Time Functions
    def year(self, date_series: pd.Series) -> pd.Series:
        """Extract year from date."""
        return pd.to_datetime(date_series).dt.year
    
    def month(self, date_series: pd.Series) -> pd.Series:
        """Extract month from date."""
        return pd.to_datetime(date_series).dt.month
    
    def day(self, date_series: pd.Series) -> pd.Series:
        """Extract day from date."""
        return pd.to_datetime(date_series).dt.day
    
    def weekday(self, date_series: pd.Series) -> pd.Series:
        """Extract weekday from date."""
        return pd.to_datetime(date_series).dt.weekday
    
    def day_of_year(self, date_series: pd.Series) -> pd.Series:
        """Extract day of year from date."""
        return pd.to_datetime(date_series).dt.dayofyear
    
    # Utility Functions
    def shift(self, series: pd.Series, periods: int) -> pd.Series:
        """Shift series by periods."""
        return series.shift(periods)
    
    def diff(self, series: pd.Series, periods: int = 1) -> pd.Series:
        """Difference between consecutive elements."""
        return series.diff(periods)
    
    def pct_change(self, series: pd.Series, periods: int = 1) -> pd.Series:
        """Percentage change."""
        return series.pct_change(periods)
    
    def cumsum(self, series: pd.Series) -> pd.Series:
        """Cumulative sum."""
        return series.cumsum()
    
    def cumprod(self, series: pd.Series) -> pd.Series:
        """Cumulative product."""
        return series.cumprod()
    
    def rolling(self, series: pd.Series, window: int, func: str) -> pd.Series:
        """Generic rolling function."""
        rolling_obj = series.rolling(window=window)
        return getattr(rolling_obj, func)()
    
    def resample(self, series: pd.Series, freq: str, func: str) -> pd.Series:
        """Resample series to different frequency."""
        resampled = series.resample(freq)
        return getattr(resampled, func)()
    
    def add_custom_function(self, name: str, func: callable):
        """Add custom function to the library."""
        self.functions[name.upper()] = func
        logger.info(f"Added custom function: {name}")
    
    def remove_function(self, name: str):
        """Remove function from the library."""
        if name.upper() in self.functions:
            del self.functions[name.upper()]
            logger.info(f"Removed function: {name}")
        else:
            logger.warning(f"Function {name} not found")
    
    def get_function_info(self, name: str) -> Dict[str, Any]:
        """Get information about a function."""
        func = self.get_function(name)
        if func is None:
            return {"error": f"Function {name} not found"}
        
        if callable(func):
            return {
                "name": name,
                "type": "function",
                "callable": True,
                "doc": func.__doc__ or "No documentation available",
                "signature": str(func.__code__.co_varnames[:func.__code__.co_argcount]) if hasattr(func, '__code__') else "Unknown"
            }
        else:
            return {
                "name": name,
                "type": "constant",
                "value": func,
                "callable": False
            }