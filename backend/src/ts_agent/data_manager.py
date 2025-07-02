"""
Market Data Manager

Handles data fetching, preprocessing, and caching for time series forecasting.
Supports multiple data sources including Yahoo Finance, Alpha Vantage, and IBKR.
"""

import pandas as pd
import numpy as np
import yfinance as yf
import pandas_ta as ta
from typing import Dict, List, Optional, Union, Tuple
from datetime import datetime, timedelta
import logging
import asyncio
from dataclasses import dataclass
import aiohttp

logger = logging.getLogger(__name__)

@dataclass
class MarketData:
    """Container for market data."""
    symbol: str
    data: pd.DataFrame
    timeframe: str
    source: str
    last_updated: datetime
    indicators: Optional[Dict[str, pd.Series]] = None

@dataclass
class DataConfig:
    """Configuration for data fetching."""
    symbols: List[str]
    period: str = "2y"  # 2 years default
    interval: str = "1d"  # Daily default
    include_indicators: bool = True
    indicators: List[str] = None
    clean_data: bool = True

class MarketDataManager:
    """Manages market data fetching and preprocessing."""
    
    def __init__(self, alpha_vantage_key: Optional[str] = None):
        """
        Initialize the data manager.
        
        Args:
            alpha_vantage_key: Optional Alpha Vantage API key for premium data
        """
        self.alpha_vantage_key = alpha_vantage_key
        self.data_cache = {}
        self.supported_intervals = ["1m", "5m", "15m", "30m", "1h", "1d", "1wk", "1mo"]
        self.default_indicators = [
            "rsi", "macd", "bb", "sma_20", "sma_50", "ema_12", "ema_26",
            "stoch", "atr", "volume_sma", "obv"
        ]
    
    async def fetch_data(
        self, 
        symbol: str, 
        period: str = "2y",
        interval: str = "1d",
        source: str = "yahoo"
    ) -> MarketData:
        """
        Fetch market data for a symbol.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            period: Time period ('1y', '2y', '5y', 'max')
            interval: Data interval ('1d', '1h', etc.)
            source: Data source ('yahoo', 'alpha_vantage')
            
        Returns:
            MarketData object
        """
        cache_key = f"{symbol}_{period}_{interval}_{source}"
        
        # Check cache first
        if cache_key in self.data_cache:
            cached_data = self.data_cache[cache_key]
            if (datetime.now() - cached_data.last_updated).seconds < 3600:  # 1 hour cache
                logger.debug(f"Using cached data for {symbol}")
                return cached_data
        
        try:
            if source == "yahoo":
                data = await self._fetch_yahoo_data(symbol, period, interval)
            elif source == "alpha_vantage":
                data = await self._fetch_alpha_vantage_data(symbol, period, interval)
            else:
                raise ValueError(f"Unsupported data source: {source}")
            
            # Clean and validate data
            cleaned_data = self._clean_data(data)
            
            # Create MarketData object
            market_data = MarketData(
                symbol=symbol,
                data=cleaned_data,
                timeframe=f"{period}_{interval}",
                source=source,
                last_updated=datetime.now()
            )
            
            # Cache the data
            self.data_cache[cache_key] = market_data
            
            logger.info(f"Fetched {len(cleaned_data)} records for {symbol}")
            return market_data
            
        except Exception as e:
            logger.error(f"Failed to fetch data for {symbol}: {e}")
            raise
    
    async def _fetch_yahoo_data(
        self, 
        symbol: str, 
        period: str, 
        interval: str
    ) -> pd.DataFrame:
        """Fetch data from Yahoo Finance."""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval=interval)
            
            if data.empty:
                raise ValueError(f"No data found for {symbol}")
            
            # Standardize column names
            data.columns = data.columns.str.lower()
            data.reset_index(inplace=True)
            
            # Ensure we have the required columns
            required_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
            if not all(col in data.columns for col in required_cols):
                logger.warning(f"Missing columns for {symbol}: {set(required_cols) - set(data.columns)}")
            
            return data
            
        except Exception as e:
            logger.error(f"Yahoo Finance fetch failed for {symbol}: {e}")
            raise
    
    async def _fetch_alpha_vantage_data(
        self, 
        symbol: str, 
        period: str, 
        interval: str
    ) -> pd.DataFrame:
        """Fetch data from Alpha Vantage."""
        if not self.alpha_vantage_key:
            raise ValueError("Alpha Vantage API key required")
        
        # Map intervals to Alpha Vantage format
        av_interval_map = {
            "1d": "TIME_SERIES_DAILY",
            "1wk": "TIME_SERIES_WEEKLY",
            "1mo": "TIME_SERIES_MONTHLY"
        }
        
        if interval not in av_interval_map:
            raise ValueError(f"Interval {interval} not supported for Alpha Vantage")
        
        function = av_interval_map[interval]
        url = f"https://www.alphavantage.co/query"
        params = {
            "function": function,
            "symbol": symbol,
            "apikey": self.alpha_vantage_key,
            "datatype": "json",
            "outputsize": "full"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    data = await response.json()
            
            # Parse Alpha Vantage response
            if "Error Message" in data:
                raise ValueError(f"Alpha Vantage error: {data['Error Message']}")
            
            if "Note" in data:
                raise ValueError(f"Alpha Vantage rate limit: {data['Note']}")
            
            # Find the time series key
            ts_key = None
            for key in data.keys():
                if "Time Series" in key:
                    ts_key = key
                    break
            
            if not ts_key:
                raise ValueError("No time series data found in Alpha Vantage response")
            
            # Convert to DataFrame
            ts_data = data[ts_key]
            df = pd.DataFrame.from_dict(ts_data, orient='index')
            
            # Clean column names and data types
            df.columns = [col.split('. ')[1].lower().replace(' ', '_') for col in df.columns]
            df = df.astype(float)
            df.reset_index(inplace=True)
            df.rename(columns={'index': 'date'}, inplace=True)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Alpha Vantage fetch failed for {symbol}: {e}")
            raise
    
    def _clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate market data."""
        df = data.copy()
        
        # Ensure date column is datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        
        # Remove any rows with missing critical data
        critical_cols = ['open', 'high', 'low', 'close', 'volume']
        available_cols = [col for col in critical_cols if col in df.columns]
        df = df.dropna(subset=available_cols)
        
        # Remove outliers (basic approach)
        for col in ['open', 'high', 'low', 'close']:
            if col in df.columns:
                Q1 = df[col].quantile(0.01)
                Q3 = df[col].quantile(0.99)
                df = df[(df[col] >= Q1) & (df[col] <= Q3)]
        
        # Ensure volume is non-negative
        if 'volume' in df.columns:
            df['volume'] = df['volume'].abs()
        
        # Sort by date
        if 'date' in df.columns:
            df = df.sort_values('date').reset_index(drop=True)
        
        return df
    
    async def fetch_multiple_symbols(
        self, 
        symbols: List[str],
        period: str = "2y",
        interval: str = "1d",
        source: str = "yahoo"
    ) -> Dict[str, MarketData]:
        """
        Fetch data for multiple symbols concurrently.
        
        Args:
            symbols: List of stock symbols
            period: Time period
            interval: Data interval
            source: Data source
            
        Returns:
            Dictionary mapping symbols to MarketData objects
        """
        tasks = []
        for symbol in symbols:
            task = self.fetch_data(symbol, period, interval, source)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        symbol_data = {}
        for symbol, result in zip(symbols, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to fetch data for {symbol}: {result}")
            else:
                symbol_data[symbol] = result
        
        return symbol_data
    
    def add_technical_indicators(
        self, 
        data: pd.DataFrame,
        indicators: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Add technical indicators to price data.
        
        Args:
            data: Price data DataFrame
            indicators: List of indicators to add
            
        Returns:
            DataFrame with indicators added
        """
        if indicators is None:
            indicators = self.default_indicators
        
        df = data.copy()
        
        try:
            # Add each indicator
            for indicator in indicators:
                if indicator == "rsi":
                    df['rsi'] = ta.rsi(df['close'])
                elif indicator == "macd":
                    macd_result = ta.macd(df['close'])
                    df = pd.concat([df, macd_result], axis=1)
                elif indicator == "bb":
                    bb_result = ta.bbands(df['close'])
                    df = pd.concat([df, bb_result], axis=1)
                elif indicator == "sma_20":
                    df['sma_20'] = ta.sma(df['close'], length=20)
                elif indicator == "sma_50":
                    df['sma_50'] = ta.sma(df['close'], length=50)
                elif indicator == "ema_12":
                    df['ema_12'] = ta.ema(df['close'], length=12)
                elif indicator == "ema_26":
                    df['ema_26'] = ta.ema(df['close'], length=26)
                elif indicator == "stoch":
                    stoch_result = ta.stoch(df['high'], df['low'], df['close'])
                    df = pd.concat([df, stoch_result], axis=1)
                elif indicator == "atr":
                    df['atr'] = ta.atr(df['high'], df['low'], df['close'])
                elif indicator == "volume_sma":
                    df['volume_sma'] = ta.sma(df['volume'], length=20)
                elif indicator == "obv":
                    df['obv'] = ta.obv(df['close'], df['volume'])
                elif indicator == "adx":
                    df['adx'] = ta.adx(df['high'], df['low'], df['close'])
                elif indicator == "cci":
                    df['cci'] = ta.cci(df['high'], df['low'], df['close'])
                elif indicator == "williams_r":
                    df['williams_r'] = ta.willr(df['high'], df['low'], df['close'])
        
        except Exception as e:
            logger.warning(f"Error adding technical indicators: {e}")
        
        return df
    
    def prepare_for_forecasting(
        self, 
        data: pd.DataFrame,
        target_column: str = "close",
        date_column: str = "date"
    ) -> pd.DataFrame:
        """
        Prepare data for time series forecasting.
        
        Args:
            data: Market data DataFrame
            target_column: Column to forecast
            date_column: Date column name
            
        Returns:
            DataFrame ready for forecasting with 'ds' and 'y' columns
        """
        df = data.copy()
        
        # Create standard forecasting format
        forecast_df = pd.DataFrame()
        forecast_df['ds'] = pd.to_datetime(df[date_column])
        forecast_df['y'] = df[target_column]
        
        # Add symbol if available
        if 'symbol' in df.columns:
            forecast_df['symbol'] = df['symbol']
        
        # Remove any missing values
        forecast_df = forecast_df.dropna()
        
        # Sort by date
        forecast_df = forecast_df.sort_values('ds').reset_index(drop=True)
        
        return forecast_df
    
    def get_market_features(
        self, 
        data: pd.DataFrame,
        lookback_periods: List[int] = [5, 10, 20, 50]
    ) -> pd.DataFrame:
        """
        Extract market features for enhanced forecasting.
        
        Args:
            data: Market data DataFrame
            lookback_periods: Periods for rolling features
            
        Returns:
            DataFrame with market features
        """
        df = data.copy()
        
        try:
            # Price-based features
            df['returns'] = df['close'].pct_change()
            df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
            df['price_range'] = (df['high'] - df['low']) / df['close']
            df['gap'] = (df['open'] - df['close'].shift(1)) / df['close'].shift(1)
            
            # Volume features
            if 'volume' in df.columns:
                df['volume_change'] = df['volume'].pct_change()
                df['price_volume'] = df['close'] * df['volume']
                
                # Volume-price trend
                df['vpt'] = (df['volume'] * df['returns']).cumsum()
            
            # Rolling features
            for period in lookback_periods:
                # Volatility
                df[f'volatility_{period}'] = df['returns'].rolling(period).std()
                
                # Price momentum
                df[f'momentum_{period}'] = df['close'] / df['close'].shift(period) - 1
                
                # Moving averages
                df[f'ma_{period}'] = df['close'].rolling(period).mean()
                df[f'ma_ratio_{period}'] = df['close'] / df[f'ma_{period}']
                
                # Volume features
                if 'volume' in df.columns:
                    df[f'volume_ma_{period}'] = df['volume'].rolling(period).mean()
                    df[f'volume_ratio_{period}'] = df['volume'] / df[f'volume_ma_{period}']
            
            # Market regime features
            df['trend_strength'] = abs(df['close'].rolling(20).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0]
            ))
            
            # Seasonal features
            if 'date' in df.columns:
                df['day_of_week'] = pd.to_datetime(df['date']).dt.dayofweek
                df['day_of_month'] = pd.to_datetime(df['date']).dt.day
                df['month'] = pd.to_datetime(df['date']).dt.month
                df['quarter'] = pd.to_datetime(df['date']).dt.quarter
            
        except Exception as e:
            logger.warning(f"Error generating market features: {e}")
        
        return df
    
    def get_correlation_matrix(
        self, 
        symbols_data: Dict[str, MarketData],
        feature: str = "close"
    ) -> pd.DataFrame:
        """
        Calculate correlation matrix between symbols.
        
        Args:
            symbols_data: Dictionary of symbol data
            feature: Feature to calculate correlations for
            
        Returns:
            Correlation matrix DataFrame
        """
        try:
            # Prepare data for correlation
            price_data = {}
            
            for symbol, market_data in symbols_data.items():
                if feature in market_data.data.columns:
                    # Use date as index
                    temp_df = market_data.data.set_index('date')[feature]
                    price_data[symbol] = temp_df
            
            if not price_data:
                return pd.DataFrame()
            
            # Create DataFrame with all symbols
            combined_df = pd.DataFrame(price_data)
            
            # Calculate correlation matrix
            correlation_matrix = combined_df.corr()
            
            return correlation_matrix
            
        except Exception as e:
            logger.error(f"Error calculating correlation matrix: {e}")
            return pd.DataFrame()
    
    def detect_market_regime(
        self, 
        data: pd.DataFrame,
        lookback: int = 50
    ) -> pd.DataFrame:
        """
        Detect market regime (bull/bear/sideways).
        
        Args:
            data: Market data DataFrame
            lookback: Lookback period for regime detection
            
        Returns:
            DataFrame with regime information
        """
        df = data.copy()
        
        try:
            # Calculate trend strength
            df['trend'] = df['close'].rolling(lookback).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) == lookback else np.nan
            )
            
            # Calculate volatility
            df['volatility'] = df['close'].pct_change().rolling(lookback).std()
            
            # Define regime based on trend and volatility
            def classify_regime(row):
                if pd.isna(row['trend']) or pd.isna(row['volatility']):
                    return 'unknown'
                
                trend_threshold = df['trend'].std() * 0.5
                vol_threshold = df['volatility'].median()
                
                if row['trend'] > trend_threshold:
                    return 'bull'
                elif row['trend'] < -trend_threshold:
                    return 'bear'
                else:
                    if row['volatility'] > vol_threshold:
                        return 'volatile_sideways'
                    else:
                        return 'calm_sideways'
            
            df['regime'] = df.apply(classify_regime, axis=1)
            
            # Add regime confidence
            df['regime_confidence'] = abs(df['trend']) / (df['volatility'] + 1e-8)
            
        except Exception as e:
            logger.warning(f"Error detecting market regime: {e}")
            df['regime'] = 'unknown'
            df['regime_confidence'] = 0.0
        
        return df
    
    def clear_cache(self):
        """Clear the data cache."""
        self.data_cache.clear()
        logger.info("Data cache cleared")
    
    def get_cache_status(self) -> Dict[str, any]:
        """Get information about cached data."""
        return {
            "cached_items": len(self.data_cache),
            "cache_keys": list(self.data_cache.keys()),
            "total_memory_mb": sum(
                data.data.memory_usage(deep=True).sum() / 1024 / 1024 
                for data in self.data_cache.values()
            )
        }