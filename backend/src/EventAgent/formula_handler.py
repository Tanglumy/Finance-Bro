"""
Formula Handler Module for EventAgent

This module integrates the QuantDSL Formula Engine with the EventAgent,
providing utilities to evaluate trading formulas against real-time market data
and generate trading signals from formula outputs.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from pydantic import BaseModel
import asyncio


try:
    from src.formula_engine import FormulaEngine
    FORMULA_ENGINE_AVAILABLE = True
except ImportError:
    FORMULA_ENGINE_AVAILABLE = False
    logging.warning("Formula Engine not available")


logger = logging.getLogger(__name__)


@dataclass
class TradingSignal:
    """Trading signal generated from formula evaluation."""
    symbol: str
    signal_type: str  # BUY, SELL, HOLD
    signal_strength: float  # 0.0 to 1.0
    entry_price: Optional[float] = None
    quantity: Optional[float] = None
    rationale: str = ""
    formula_name: str = ""
    timestamp: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert signal to dictionary format."""
        return {
            "asset_symbol": self.symbol,
            "signal_type": self.signal_type,
            "signal_strength": self.signal_strength,
            "entry_price": self.entry_price,
            "quantity": self.quantity,
            "rationale": self.rationale,
            "formula_name": self.formula_name,
            "timestamp": self.timestamp.isoformat(),
            "source": "formula_engine",
            "metadata": self.metadata
        }


class MarketDataTransformer:
    """Transforms market events and data into formula-compatible format."""
    
    @staticmethod
    def events_to_dataframe(
        events: List[Dict[str, Any]],
        market_data: Dict[str, Any]
    ) -> pd.DataFrame:
        """
        Convert market events and data to DataFrame for formula evaluation.
        
        Args:
            events: List of detected market events
            market_data: Current market data (prices, indicators, etc.)
        
        Returns:
            DataFrame with columns suitable for formula evaluation
        """
        try:
            # Extract price data
            prices = market_data.get("prices", {})
            indicators = market_data.get("indicators", {})
            
            # Create base DataFrame
            if isinstance(prices, dict):
                df = pd.DataFrame({
                    "symbol": list(prices.keys()),
                    "close": list(prices.values())
                })
            else:
                df = pd.DataFrame(prices)
            
            # Add technical indicators
            for indicator_name, indicator_value in indicators.items():
                if isinstance(indicator_value, dict):
                    for key, value in indicator_value.items():
                        df[f"{indicator_name}_{key}"] = value
                else:
                    df[indicator_name] = indicator_value
            
            # Add event features
            event_features = MarketDataTransformer._extract_event_features(events)
            for feature_name, feature_value in event_features.items():
                df[feature_name] = feature_value
            
            # Add timestamp
            df["timestamp"] = datetime.now()
            
            return df
            
        except Exception as e:
            logger.error(f"Error converting events to DataFrame: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def _extract_event_features(events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract quantifiable features from market events."""
        features = {
            "event_count": len(events),
            "avg_significance": 0.0,
            "high_impact_events": 0,
            "earnings_events": 0,
            "fed_events": 0
        }
        
        if not events:
            return features
        
        significance_scores = []
        for event in events:
            sig_score = event.get("significance_score", 0.5)
            significance_scores.append(sig_score)
            
            if sig_score > 0.8:
                features["high_impact_events"] += 1
            
            event_type = event.get("event_type", "").lower()
            if "earning" in event_type:
                features["earnings_events"] += 1
            elif "fed" in event_type or "interest" in event_type:
                features["fed_events"] += 1
        
        features["avg_significance"] = np.mean(significance_scores) if significance_scores else 0.0
        
        return features
    
    @staticmethod
    async def fetch_historical_data(
        symbol: str,
        period_days: int = 30
    ) -> pd.DataFrame:
        """
        Fetch historical price data for formula evaluation.
        
        Args:
            symbol: Stock symbol
            period_days: Number of days of historical data
        
        Returns:
            DataFrame with OHLCV data
        """
        try:
            from EventAgent.financial_data_service import get_financial_service
            
            async with await get_financial_service() as service:
                # This is a placeholder - actual implementation would fetch real historical data
                # For now, generate mock data
                dates = pd.date_range(
                    end=datetime.now(),
                    periods=period_days,
                    freq='D'
                )
                
                # Mock price data with realistic patterns
                base_price = 100.0
                returns = np.random.normal(0.001, 0.02, period_days)
                prices = base_price * (1 + returns).cumprod()
                
                df = pd.DataFrame({
                    "date": dates,
                    "open": prices * (1 + np.random.normal(0, 0.005, period_days)),
                    "high": prices * (1 + np.random.uniform(0, 0.02, period_days)),
                    "low": prices * (1 - np.random.uniform(0, 0.02, period_days)),
                    "close": prices,
                    "volume": np.random.randint(1000000, 10000000, period_days)
                })
                
                return df
                
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return pd.DataFrame()


class FormulaHandler:
    """Main handler for formula-based trading signal generation."""
    
    def __init__(self):
        """Initialize formula handler."""
        self.formula_engine = None
        self.transformer = MarketDataTransformer()
        self.active_formulas: Dict[str, Dict[str, Any]] = {}
        
        if FORMULA_ENGINE_AVAILABLE:
            self.formula_engine = FormulaEngine()
            logger.info("Formula Engine initialized successfully")
        else:
            logger.warning("Formula Engine not available - using mock mode")
    
    async def evaluate_formula_strategy(
        self,
        formula_name: str,
        market_data: Dict[str, Any],
        portfolio_context: Dict[str, Any],
        symbols: Optional[List[str]] = None
    ) -> List[TradingSignal]:
        """
        Evaluate a formula strategy against current market data.
        
        Args:
            formula_name: Name of the formula model to evaluate
            market_data: Current market data including prices and indicators
            portfolio_context: Portfolio information for position sizing
            symbols: List of symbols to evaluate (None = all available)
        
        Returns:
            List of trading signals generated from formula
        """
        try:
            if not self.formula_engine:
                logger.warning("Formula engine not available")
                return []
            
            # Get formula model
            formula_model = self.formula_engine.get_model(formula_name)
            if not formula_model:
                logger.error(f"Formula model {formula_name} not found")
                return []
            
            signals = []
            
            # Evaluate for each symbol
            target_symbols = symbols or list(market_data.get("prices", {}).keys())
            
            for symbol in target_symbols:
                try:
                    # Fetch historical data for technical indicators
                    historical_data = await self.transformer.fetch_historical_data(symbol)
                    
                    if historical_data.empty:
                        logger.warning(f"No historical data for {symbol}")
                        continue
                    
                    # Evaluate formula
                    result = self.formula_engine.evaluate_model(
                        formula_name,
                        historical_data
                    )
                    
                    # Generate signal from result
                    signal = self._result_to_signal(
                        symbol,
                        result,
                        formula_name,
                        market_data,
                        portfolio_context
                    )
                    
                    if signal:
                        signals.append(signal)
                        
                except Exception as e:
                    logger.error(f"Error evaluating formula for {symbol}: {e}")
                    continue
            
            return signals
            
        except Exception as e:
            logger.error(f"Error in evaluate_formula_strategy: {e}")
            return []
    
    def _result_to_signal(
        self,
        symbol: str,
        result: Any,
        formula_name: str,
        market_data: Dict[str, Any],
        portfolio_context: Dict[str, Any]
    ) -> Optional[TradingSignal]:
        """
        Convert formula evaluation result to trading signal.
        
        Args:
            symbol: Stock symbol
            result: Formula evaluation result
            formula_name: Name of the formula
            market_data: Current market data
            portfolio_context: Portfolio information
        
        Returns:
            TradingSignal or None if no signal
        """
        try:
            # Handle different result types
            if isinstance(result, pd.Series):
                signal_value = result.iloc[-1]
            elif isinstance(result, (int, float)):
                signal_value = result
            else:
                logger.warning(f"Unexpected result type: {type(result)}")
                return None
            
            # Interpret signal value
            # Convention: > 0.5 = BUY, < -0.5 = SELL, else HOLD
            if signal_value > 0.5:
                signal_type = "BUY"
                signal_strength = min(signal_value, 1.0)
            elif signal_value < -0.5:
                signal_type = "SELL"
                signal_strength = min(abs(signal_value), 1.0)
            else:
                signal_type = "HOLD"
                signal_strength = 0.0
            
            # Skip HOLD signals
            if signal_type == "HOLD":
                return None
            
            # Get current price
            current_price = market_data.get("prices", {}).get(symbol)
            
            # Calculate position size based on portfolio
            quantity = self._calculate_position_size(
                portfolio_context,
                current_price,
                signal_strength
            )
            
            # Create signal
            signal = TradingSignal(
                symbol=symbol,
                signal_type=signal_type,
                signal_strength=signal_strength,
                entry_price=current_price,
                quantity=quantity,
                rationale=f"Formula: {formula_name}, Signal Value: {signal_value:.3f}",
                formula_name=formula_name,
                metadata={
                    "signal_value": float(signal_value),
                    "formula_result_type": str(type(result).__name__)
                }
            )
            
            return signal
            
        except Exception as e:
            logger.error(f"Error converting result to signal: {e}")
            return None
    
    def _calculate_position_size(
        self,
        portfolio_context: Dict[str, Any],
        price: Optional[float],
        signal_strength: float
    ) -> float:
        """
        Calculate position size based on portfolio and signal strength.
        
        Args:
            portfolio_context: Portfolio information
            price: Entry price
            signal_strength: Signal confidence (0-1)
        
        Returns:
            Position size in shares
        """
        try:
            if not price or price <= 0:
                return 0.0
            
            # Get portfolio value
            cash_balance = portfolio_context.get("cash", 10000.0)
            total_value = portfolio_context.get("total_value", cash_balance)
            
            # Base position size: 5% of portfolio
            base_position_pct = 0.05
            
            # Adjust by signal strength (50% to 100% of base)
            adjusted_position_pct = base_position_pct * (0.5 + 0.5 * signal_strength)
            
            # Calculate position value
            position_value = total_value * adjusted_position_pct
            
            # Calculate shares
            shares = position_value / price
            
            # Round to integer
            shares = int(shares)
            
            return max(shares, 1)  # At least 1 share
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0.0
    
    def register_formula(
        self,
        formula_name: str,
        config: Dict[str, Any]
    ) -> bool:
        """
        Register a formula for active trading.
        
        Args:
            formula_name: Name of the formula model
            config: Configuration for the formula strategy
        
        Returns:
            True if successfully registered
        """
        try:
            if not self.formula_engine:
                logger.error("Formula engine not available")
                return False
            
            # Verify formula exists
            formula_model = self.formula_engine.get_model(formula_name)
            if not formula_model:
                logger.error(f"Formula model {formula_name} not found")
                return False
            
            # Store configuration
            self.active_formulas[formula_name] = {
                "config": config,
                "registered_at": datetime.now(),
                "evaluation_count": 0,
                "signal_count": 0
            }
            
            logger.info(f"Formula {formula_name} registered successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error registering formula {formula_name}: {e}")
            return False
    
    def unregister_formula(self, formula_name: str) -> bool:
        """
        Unregister an active formula.
        
        Args:
            formula_name: Name of the formula to unregister
        
        Returns:
            True if successfully unregistered
        """
        if formula_name in self.active_formulas:
            del self.active_formulas[formula_name]
            logger.info(f"Formula {formula_name} unregistered")
            return True
        return False
    
    def get_active_formulas(self) -> List[str]:
        """Get list of active formula names."""
        return list(self.active_formulas.keys())
    
    async def evaluate_all_active_formulas(
        self,
        market_data: Dict[str, Any],
        portfolio_context: Dict[str, Any]
    ) -> List[TradingSignal]:
        """
        Evaluate all active formulas and aggregate signals.
        
        Args:
            market_data: Current market data
            portfolio_context: Portfolio information
        
        Returns:
            Aggregated list of trading signals
        """
        all_signals = []
        
        for formula_name, formula_info in self.active_formulas.items():
            try:
                config = formula_info["config"]
                symbols = config.get("symbols")
                
                signals = await self.evaluate_formula_strategy(
                    formula_name,
                    market_data,
                    portfolio_context,
                    symbols
                )
                
                # Update stats
                formula_info["evaluation_count"] += 1
                formula_info["signal_count"] += len(signals)
                formula_info["last_evaluated"] = datetime.now()
                
                all_signals.extend(signals)
                
            except Exception as e:
                logger.error(f"Error evaluating formula {formula_name}: {e}")
                continue
        
        return all_signals


# Global instance
_formula_handler = None

def get_formula_handler() -> FormulaHandler:
    """Get the global formula handler instance."""
    global _formula_handler
    if _formula_handler is None:
        _formula_handler = FormulaHandler()
    return _formula_handler
