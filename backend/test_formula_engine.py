#!/usr/bin/env python3
"""
Test script for the Formula Engine
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from formula_engine import FormulaEngine, FormulaEvaluator

def create_sample_data(days=252):
    """Create sample OHLCV data for testing."""
    np.random.seed(42)
    
    # Generate dates
    start_date = datetime.now() - timedelta(days=days)
    dates = [start_date + timedelta(days=i) for i in range(days)]
    
    # Generate realistic price data
    initial_price = 100.0
    prices = [initial_price]
    
    for i in range(1, days):
        # Random walk with slight upward bias
        change = np.random.normal(0.001, 0.02)  # 0.1% daily return, 2% volatility
        new_price = prices[-1] * (1 + change)
        prices.append(max(new_price, 0.01))  # Ensure positive prices
    
    # Create OHLC data
    opens = []
    highs = []
    lows = []
    closes = prices
    volumes = []
    
    for i, close in enumerate(closes):
        # Open is previous close with small gap
        if i == 0:
            open_price = close
        else:
            gap = np.random.normal(0, 0.005)
            open_price = closes[i-1] * (1 + gap)
        
        opens.append(open_price)
        
        # High and low around open and close
        high_price = max(open_price, close) * (1 + abs(np.random.normal(0, 0.01)))
        low_price = min(open_price, close) * (1 - abs(np.random.normal(0, 0.01)))
        
        highs.append(high_price)
        lows.append(low_price)
        
        # Volume with some correlation to price movement
        base_volume = 1000000
        volume_factor = 1 + abs(close - open_price) / open_price * 2
        volume = int(base_volume * volume_factor * np.random.uniform(0.5, 1.5))
        volumes.append(volume)
    
    return pd.DataFrame({
        'date': dates,
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
        'volume': volumes
    })

def test_formula_evaluator():
    """Test the formula evaluator with basic formulas."""
    print("Testing Formula Evaluator...")
    
    evaluator = FormulaEvaluator()
    data = create_sample_data(100)
    
    # Test simple formulas
    test_formulas = [
        "close",
        "close > open",
        "MA(close, 20)",
        "RSI(close, 14)",
        "close > MA(close, 20)",
        "RSI(close, 14) < 30",
        "MA(close, 10) > MA(close, 20)",
        "volume > MA(volume, 10) * 1.5"
    ]
    
    for formula in test_formulas:
        try:
            result = evaluator.evaluate(formula, data)
            print(f"✓ '{formula}' -> {type(result).__name__}")
            if hasattr(result, 'shape'):
                print(f"  Shape: {result.shape}")
        except Exception as e:
            print(f"✗ '{formula}' -> Error: {e}")
    
    print()

def test_formula_engine():
    """Test the formula engine with model creation and backtesting."""
    print("Testing Formula Engine...")
    
    engine = FormulaEngine()
    data = create_sample_data(252)
    
    # Create sample models
    models = {
        "simple_ma_cross": {
            "formula": "MA(close, 20) > MA(close, 50)",
            "description": "Simple moving average crossover"
        },
        "rsi_oversold": {
            "formula": "RSI(close, 14) < 30",
            "description": "RSI oversold condition"
        },
        "momentum_strategy": {
            "formula": "ROC(close, 10) > 0.05 AND volume > MA(volume, 20) * 1.5",
            "description": "Momentum strategy with volume confirmation"
        }
    }
    
    # Create and test models
    for name, model_info in models.items():
        try:
            model = engine.create_model(name, model_info["formula"], model_info["description"])
            print(f"✓ Created model: {name}")
            
            # Test evaluation
            result = engine.evaluate_model(name, data)
            print(f"  Evaluation result: {type(result).__name__}")
            
            # Test validation
            validation = model.validation_result
            if validation and validation.get("valid", False):
                print(f"  ✓ Formula is valid")
            else:
                print(f"  ✗ Formula validation issues: {validation}")
                
        except Exception as e:
            print(f"✗ Error with model {name}: {e}")
    
    print()

def test_backtesting():
    """Test backtesting functionality."""
    print("Testing Backtesting...")
    
    engine = FormulaEngine()
    data = create_sample_data(252)
    
    # Create a simple strategy
    strategy_formula = "MA(close, 20) > MA(close, 50)"
    model = engine.create_model("test_strategy", strategy_formula, "Test strategy")
    
    try:
        # Run backtest
        backtest_results = engine.backtest_model("test_strategy", data, initial_capital=100000)
        
        print("✓ Backtest completed successfully")
        
        # Print key metrics
        metrics = backtest_results.get("metrics", {})
        print(f"  Total Return: {metrics.get('total_return', 0):.2%}")
        print(f"  Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
        print(f"  Max Drawdown: {metrics.get('max_drawdown', 0):.2%}")
        print(f"  Win Rate: {metrics.get('win_rate', 0):.2%}")
        print(f"  Total Trades: {metrics.get('total_trades', 0)}")
        
    except Exception as e:
        print(f"✗ Backtest error: {e}")
    
    print()

def test_sample_formulas():
    """Test sample formulas provided by the engine."""
    print("Testing Sample Formulas...")
    
    engine = FormulaEngine()
    evaluator = FormulaEvaluator()
    data = create_sample_data(100)
    
    # Get sample formulas
    sample_formulas = engine.create_sample_formulas()
    
    print(f"Testing {len(sample_formulas)} sample formulas...")
    
    for name, formula in sample_formulas.items():
        try:
            # Validate formula
            validation = evaluator.validate_formula(formula)
            
            if validation.get("valid", False):
                # Try to evaluate
                result = evaluator.evaluate(formula, data)
                print(f"✓ {name}: {formula[:50]}...")
            else:
                print(f"✗ {name}: Validation failed - {validation.get('unknown_functions', [])}")
                
        except Exception as e:
            print(f"✗ {name}: Error - {e}")
    
    print()

def test_function_library():
    """Test the function library."""
    print("Testing Function Library...")
    
    evaluator = FormulaEvaluator()
    
    # Get available functions
    functions = evaluator.get_available_functions()
    print(f"Available functions: {len(functions)}")
    
    # Test some key functions
    test_functions = ['MA', 'RSI', 'MACD', 'BB', 'ATR', 'OBV']
    
    for func_name in test_functions:
        if func_name in functions:
            func_info = evaluator.get_function_info(func_name)
            print(f"✓ {func_name}: {func_info.get('doc', 'No description')[:50]}...")
        else:
            print(f"✗ {func_name}: Not found")
    
    print()

def main():
    """Run all tests."""
    print("=" * 60)
    print("Finance-Bro Formula Engine Test Suite")
    print("=" * 60)
    print()
    
    try:
        test_formula_evaluator()
        test_formula_engine()
        test_backtesting()
        test_sample_formulas()
        test_function_library()
        
        print("=" * 60)
        print("All tests completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"Test suite error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()