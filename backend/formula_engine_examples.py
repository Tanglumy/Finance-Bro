#!/usr/bin/env python3
"""
Formula Engine Examples - Demonstrates usage of the Formula DSL
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from formula_engine import FormulaEngine

def create_sample_data():
    """Create sample market data."""
    np.random.seed(42)
    days = 500
    
    # Generate dates
    start_date = datetime(2023, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(days)]
    
    # Generate realistic price data with trend
    initial_price = 100.0
    prices = [initial_price]
    
    for i in range(1, days):
        # Add trend and noise
        trend = 0.0002  # Slight upward trend
        noise = np.random.normal(0, 0.015)  # 1.5% daily volatility
        change = trend + noise
        new_price = prices[-1] * (1 + change)
        prices.append(max(new_price, 1.0))
    
    # Create OHLC data
    opens = []
    highs = []
    lows = []
    closes = prices
    volumes = []
    
    for i, close in enumerate(closes):
        if i == 0:
            open_price = close
        else:
            gap = np.random.normal(0, 0.003)
            open_price = closes[i-1] * (1 + gap)
        
        opens.append(open_price)
        
        high_price = max(open_price, close) * (1 + abs(np.random.normal(0, 0.008)))
        low_price = min(open_price, close) * (1 - abs(np.random.normal(0, 0.008)))
        
        highs.append(high_price)
        lows.append(low_price)
        
        base_volume = 1000000
        volume_factor = 1 + abs(close - open_price) / open_price * 3
        volume = int(base_volume * volume_factor * np.random.uniform(0.5, 2.0))
        volumes.append(volume)
    
    return pd.DataFrame({
        'date': dates,
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
        'volume': volumes
    })

def example_1_basic_indicators():
    """Example 1: Basic technical indicators."""
    print("Example 1: Basic Technical Indicators")
    print("=" * 40)
    
    engine = FormulaEngine()
    data = create_sample_data()
    
    # Create models with different indicators
    models = {
        "moving_average": "MA(close, 20)",
        "rsi": "RSI(close, 14)",
        "macd_signal": "MACD(close, 12, 26, 9)",
        "bollinger_bands": "BB(close, 20, 2)",
        "volume_sma": "MA(volume, 10)"
    }
    
    for name, formula in models.items():
        try:
            model = engine.create_model(name, formula, f"Basic {name} indicator")
            result = engine.evaluate_model(name, data)
            
            if isinstance(result, pd.Series):
                print(f"✓ {name}: {result.iloc[-1]:.2f} (latest value)")
            elif isinstance(result, pd.DataFrame):
                print(f"✓ {name}: DataFrame with {len(result.columns)} columns")
            else:
                print(f"✓ {name}: {type(result).__name__}")
                
        except Exception as e:
            print(f"✗ {name}: {e}")
    
    print()

def example_2_trading_signals():
    """Example 2: Trading signals and conditions."""
    print("Example 2: Trading Signals and Conditions")
    print("=" * 45)
    
    engine = FormulaEngine()
    data = create_sample_data()
    
    # Create trading signal models
    signals = {
        "ma_crossover": "MA(close, 20) > MA(close, 50)",
        "rsi_oversold": "RSI(close, 14) < 30",
        "rsi_overbought": "RSI(close, 14) > 70",
        "breakout": "close > MAX(high, 20)",
        "volume_spike": "volume > MA(volume, 20) * 2",
        "price_momentum": "ROC(close, 10) > 0.05",
        "volatility_expansion": "ATR(high, low, close, 14) > MA(ATR(high, low, close, 14), 10) * 1.5"
    }
    
    for name, formula in signals.items():
        try:
            model = engine.create_model(name, formula, f"Trading signal: {name}")
            result = engine.evaluate_model(name, data)
            
            if isinstance(result, pd.Series):
                true_count = result.sum() if result.dtype == bool else (result > 0).sum()
                print(f"✓ {name}: {true_count} signals out of {len(result)} days")
            else:
                print(f"✓ {name}: {type(result).__name__}")
                
        except Exception as e:
            print(f"✗ {name}: {e}")
    
    print()

def example_3_complex_strategies():
    """Example 3: Complex trading strategies."""
    print("Example 3: Complex Trading Strategies")
    print("=" * 40)
    
    engine = FormulaEngine()
    data = create_sample_data()
    
    # Create complex strategy models
    strategies = {
        "momentum_volume": "ROC(close, 10) > 0.03 AND volume > MA(volume, 20) * 1.5 AND RSI(close, 14) < 70",
        "mean_reversion": "RSI(close, 14) < 30 AND close < MA(close, 20) * 0.98",
        "trend_following": "MA(close, 20) > MA(close, 50) AND ADX(high, low, close, 14) > 25 AND volume > MA(volume, 10)",
        "bollinger_squeeze": "BB(close, 20, 2) AND ATR(high, low, close, 14) < MA(ATR(high, low, close, 14), 20) * 0.8",
        "breakout_confirmation": "close > MAX(high, 20) AND volume > MA(volume, 10) * 1.5 AND RSI(close, 14) > 50"
    }
    
    for name, formula in strategies.items():
        try:
            model = engine.create_model(name, formula, f"Complex strategy: {name}")
            result = engine.evaluate_model(name, data)
            
            if isinstance(result, pd.Series):
                if result.dtype == bool:
                    signals = result.sum()
                else:
                    signals = (result > 0).sum()
                print(f"✓ {name}: {signals} signals ({signals/len(result)*100:.1f}%)")
            else:
                print(f"✓ {name}: {type(result).__name__}")
                
        except Exception as e:
            print(f"✗ {name}: {e}")
    
    print()

def example_4_backtesting():
    """Example 4: Backtesting strategies."""
    print("Example 4: Backtesting Strategies")
    print("=" * 35)
    
    engine = FormulaEngine()
    data = create_sample_data()
    
    # Create strategies for backtesting
    strategies = {
        "simple_ma": "MA(close, 20) > MA(close, 50)",
        "rsi_mean_reversion": "RSI(close, 14) < 30",
        "momentum": "ROC(close, 10) > 0.02 AND volume > MA(volume, 20)"
    }
    
    for name, formula in strategies.items():
        try:
            # Create model
            model = engine.create_model(name, formula, f"Backtest strategy: {name}")
            
            # Run backtest
            backtest_results = engine.backtest_model(
                name, 
                data, 
                initial_capital=100000,
                start_date="2023-01-01",
                end_date="2023-12-31"
            )
            
            metrics = backtest_results.get("metrics", {})
            
            print(f"✓ {name}:")
            print(f"    Total Return: {metrics.get('total_return', 0):.2%}")
            print(f"    Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
            print(f"    Max Drawdown: {metrics.get('max_drawdown', 0):.2%}")
            print(f"    Win Rate: {metrics.get('win_rate', 0):.2%}")
            print(f"    Total Trades: {metrics.get('total_trades', 0)}")
            print()
            
        except Exception as e:
            print(f"✗ {name}: {e}")
    
    print()

def example_5_conditional_logic():
    """Example 5: Conditional logic and complex expressions."""
    print("Example 5: Conditional Logic")
    print("=" * 30)
    
    engine = FormulaEngine()
    data = create_sample_data()
    
    # Create models with conditional logic
    conditions = {
        "market_regime": "RSI(close, 14) > 70 ? -1 : RSI(close, 14) < 30 ? 1 : 0",
        "position_size": "ATR(high, low, close, 14) > MA(ATR(high, low, close, 14), 20) ? 0.5 : 1.0",
        "stop_loss": "close < MA(close, 20) * 0.95 ? 1 : 0",
        "trend_strength": "ADX(high, low, close, 14) > 25 ? 1 : 0.5"
    }
    
    for name, formula in conditions.items():
        try:
            model = engine.create_model(name, formula, f"Conditional: {name}")
            result = engine.evaluate_model(name, data)
            
            if isinstance(result, pd.Series):
                avg_value = result.mean()
                print(f"✓ {name}: Average value = {avg_value:.2f}")
            else:
                print(f"✓ {name}: {type(result).__name__}")
                
        except Exception as e:
            print(f"✗ {name}: {e}")
    
    print()

def example_6_custom_variables():
    """Example 6: Using custom variables in formulas."""
    print("Example 6: Custom Variables")
    print("=" * 28)
    
    engine = FormulaEngine()
    data = create_sample_data()
    
    # Create models with custom variables
    custom_formulas = {
        "dynamic_ma": "MA(close, period)",
        "rsi_threshold": "RSI(close, 14) < oversold_level",
        "volatility_filter": "ATR(high, low, close, 14) > atr_threshold * volatility_multiplier"
    }
    
    # Define variables
    variables = {
        "period": 25,
        "oversold_level": 25,
        "atr_threshold": 2.0,
        "volatility_multiplier": 1.5
    }
    
    for name, formula in custom_formulas.items():
        try:
            model = engine.create_model(name, formula, f"Custom variables: {name}", variables)
            result = engine.evaluate_model(name, data)
            
            if isinstance(result, pd.Series):
                if result.dtype == bool:
                    true_count = result.sum()
                    print(f"✓ {name}: {true_count} true values")
                else:
                    avg_value = result.mean()
                    print(f"✓ {name}: Average = {avg_value:.2f}")
            else:
                print(f"✓ {name}: {type(result).__name__}")
                
        except Exception as e:
            print(f"✗ {name}: {e}")
    
    print()

def example_7_model_management():
    """Example 7: Model management and persistence."""
    print("Example 7: Model Management")
    print("=" * 30)
    
    engine = FormulaEngine()
    data = create_sample_data()
    
    # Create several models
    models = {
        "model_1": "MA(close, 20) > MA(close, 50)",
        "model_2": "RSI(close, 14) < 30",
        "model_3": "volume > MA(volume, 20) * 1.5"
    }
    
    # Create models
    for name, formula in models.items():
        engine.create_model(name, formula, f"Test model {name}")
    
    # List models
    print(f"Created models: {engine.list_models()}")
    
    # Get model performance
    for model_name in engine.list_models():
        performance = engine.get_model_performance(model_name)
        print(f"Model {model_name}: Valid = {performance.get('validation', {}).get('valid', False)}")
    
    # Update a model
    engine.update_model("model_1", description="Updated moving average crossover")
    
    # Get engine statistics
    stats = engine.get_engine_stats()
    print(f"Engine stats: {stats}")
    
    print()

def main():
    """Run all examples."""
    print("=" * 60)
    print("Finance-Bro Formula Engine Examples")
    print("=" * 60)
    print()
    
    try:
        example_1_basic_indicators()
        example_2_trading_signals()
        example_3_complex_strategies()
        example_4_backtesting()
        example_5_conditional_logic()
        example_6_custom_variables()
        example_7_model_management()
        
        print("=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"Examples error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()