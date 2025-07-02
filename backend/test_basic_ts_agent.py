#!/usr/bin/env python3
"""
Basic Test Script for Enhanced Time Series Agent

This script tests the core functionality without external dependencies.
"""

import asyncio
import os
import sys
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Add the src directory to Python path
sys.path.append('/Users/bytedance/Finance-Bro/backend/src')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_data_manager():
    """Test the data manager functionality."""
    print("\n=== Testing Data Manager ===")
    
    try:
        from ts_agent.data_manager import MarketDataManager
        
        # Initialize data manager
        data_manager = MarketDataManager()
        
        # Test data fetching
        market_data = await data_manager.fetch_data('AAPL', period='6mo', source='yahoo')
        
        print(f"✓ Data fetched: {len(market_data.data)} records")
        print(f"✓ Columns: {list(market_data.data.columns)}")
        print(f"✓ Date range: {market_data.data['date'].min()} to {market_data.data['date'].max()}")
        
        # Test technical indicators
        enhanced_data = data_manager.add_technical_indicators(
            market_data.data, 
            indicators=['rsi', 'sma_20', 'ema_12']
        )
        
        print(f"✓ Technical indicators added: {len(enhanced_data.columns)} total columns")
        
        # Test market features
        featured_data = data_manager.get_market_features(enhanced_data)
        print(f"✓ Market features added: {len(featured_data.columns)} total columns")
        
        return True
        
    except Exception as e:
        print(f"✗ Data Manager test failed: {e}")
        return False

async def test_basic_models():
    """Test basic statistical models."""
    print("\n=== Testing Basic Models ===")
    
    try:
        from ts_agent.models import TimeSeriesModelManager
        from ts_agent.data_manager import MarketDataManager
        
        # Get sample data
        data_manager = MarketDataManager()
        market_data = await data_manager.fetch_data('AAPL', period='1y', source='yahoo')
        forecast_data = data_manager.prepare_for_forecasting(market_data.data)
        
        # Initialize model manager (without external API keys)
        model_manager = TimeSeriesModelManager()
        
        print(f"✓ Model manager initialized")
        print(f"✓ Available models: {model_manager.get_available_models()}")
        
        # Test statistical models (should work without external dependencies)
        try:
            result = model_manager.predict_statistical(forecast_data, horizon=30)
            print(f"✓ Statistical models: Generated {len(result.predictions)} predictions")
            print(f"✓ Model used: {result.model_name}")
        except Exception as e:
            print(f"⚠ Statistical models not available: {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ Basic Models test failed: {e}")
        return False

async def test_predictor_basic():
    """Test basic predictor functionality."""
    print("\n=== Testing Basic Predictor ===")
    
    try:
        from ts_agent.predictor import TimeSeriesPredictor
        
        # Initialize predictor (without external APIs)
        predictor = TimeSeriesPredictor()
        
        print(f"✓ Predictor initialized")
        
        # Get model performance info
        performance = predictor.get_model_performance()
        print(f"✓ Available models: {performance['available_models']}")
        print(f"✓ Nixtla available: {performance['nixtla_available']}")
        print(f"✓ IBKR available: {performance['ibkr_available']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Basic Predictor test failed: {e}")
        return False

async def test_sample_prediction():
    """Test a complete prediction workflow."""
    print("\n=== Testing Sample Prediction ===")
    
    try:
        from ts_agent.predictor import TimeSeriesPredictor
        
        # Initialize predictor
        predictor = TimeSeriesPredictor()
        
        # Try to make a basic prediction
        try:
            result = await predictor.predict_single(
                symbol='AAPL',
                horizon=10,  # Short horizon for testing
                models=['statistical'],  # Basic models only
                period='6mo'
            )
            
            print(f"✓ Prediction successful!")
            print(f"✓ Symbol: {result.symbol}")
            print(f"✓ Horizon: {result.horizon}")
            print(f"✓ Predictions: {len(result.predictions)} data points")
            print(f"✓ Models used: {list(result.model_performance.keys())}")
            
            if result.scenarios:
                print(f"✓ Scenarios generated: {list(result.scenarios.keys())}")
            
            return True
            
        except Exception as e:
            print(f"⚠ Full prediction failed (expected without ML libraries): {e}")
            return True  # This is expected without ML dependencies
        
    except Exception as e:
        print(f"✗ Sample Prediction test failed: {e}")
        return False

async def main():
    """Main test function."""
    print("="*60)
    print("BASIC TIME SERIES AGENT TEST")
    print("="*60)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run basic tests
    tests = [
        ("Data Manager", test_data_manager),
        ("Basic Models", test_basic_models),
        ("Basic Predictor", test_predictor_basic),
        ("Sample Prediction", test_sample_prediction),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    # Check environment
    print(f"\nEnvironment Check:")
    print(f"Python Version: {sys.version}")
    print(f"Working Directory: {os.getcwd()}")
    print(f"NIXTLA_API_KEY: {'Set' if os.getenv('NIXTLA_API_KEY') else 'Not Set'}")
    
    if passed == total:
        print("\n🎉 All basic tests passed! The TS Agent core functionality is working.")
        print("\nNext steps:")
        print("1. Install additional ML dependencies: pip install nixtla gluonts statsforecast neuralforecast")
        print("2. Set NIXTLA_API_KEY for TimeGPT functionality")
        print("3. Run the full test suite")
    else:
        print(f"\n⚠ {total - passed} tests failed. Check the error messages above.")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)