#!/usr/bin/env python3
"""
Comprehensive Test Script for Enhanced Time Series Agent

This script tests the upgraded TS Agent with Nixtla TimeGEN, enhanced GluonTS,
MLForecast models, and IBKR integration.
"""

import asyncio
import os
import sys
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any
import warnings
warnings.filterwarnings('ignore')

# Add the src directory to Python path
sys.path.append('/Users/bytedance/Finance-Bro/backend/src')

# Import TS Agent components
from ts_agent.models import TimeSeriesModelManager
from ts_agent.predictor import TimeSeriesPredictor
from ts_agent.data_manager import MarketDataManager
from ts_agent.ibkr_client import create_ibkr_client, IBKRConfig

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TSAgentTester:
    """Comprehensive test suite for TS Agent."""
    
    def __init__(self):
        """Initialize the test suite."""
        self.test_symbols = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA']
        self.test_results = {}
        self.predictor = None
        
    async def setup_environment(self):
        """Set up the testing environment."""
        logger.info("Setting up test environment...")
        
        # Check for required environment variables
        env_vars = {
            'NIXTLA_API_KEY': os.getenv('NIXTLA_API_KEY'),
            'ALPHA_VANTAGE_API_KEY': os.getenv('ALPHA_VANTAGE_API_KEY'),
            'USE_IBKR': os.getenv('USE_IBKR', 'false').lower() == 'true'
        }
        
        logger.info(f"Environment variables: {env_vars}")
        
        # Initialize the predictor
        try:
            self.predictor = TimeSeriesPredictor(
                nixtla_api_key=env_vars['NIXTLA_API_KEY'],
                alpha_vantage_key=env_vars['ALPHA_VANTAGE_API_KEY'],
                use_ibkr=env_vars['USE_IBKR']
            )
            logger.info("TimeSeriesPredictor initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize predictor: {e}")
            raise
    
    async def test_data_fetching(self):
        """Test data fetching capabilities."""
        logger.info("Testing data fetching...")
        
        test_results = {}
        
        for symbol in self.test_symbols[:2]:  # Test first 2 symbols
            try:
                # Test Yahoo Finance data fetching
                market_data = await self.predictor.data_manager.fetch_data(
                    symbol=symbol,
                    period="1y",
                    interval="1d",
                    source="yahoo"
                )
                
                test_results[symbol] = {
                    'data_points': len(market_data.data),
                    'columns': list(market_data.data.columns),
                    'date_range': {
                        'start': market_data.data['date'].min().strftime('%Y-%m-%d'),
                        'end': market_data.data['date'].max().strftime('%Y-%m-%d')
                    },
                    'source': market_data.source
                }
                
                logger.info(f"✓ {symbol}: Fetched {len(market_data.data)} data points")
                
            except Exception as e:
                logger.error(f"✗ {symbol}: Data fetching failed - {e}")
                test_results[symbol] = {'error': str(e)}
        
        self.test_results['data_fetching'] = test_results
        return test_results
    
    async def test_technical_indicators(self):
        """Test technical indicator generation."""
        logger.info("Testing technical indicators...")
        
        try:
            # Fetch sample data
            market_data = await self.predictor.data_manager.fetch_data('AAPL', period="6mo")
            
            # Add technical indicators
            enhanced_data = self.predictor.data_manager.add_technical_indicators(
                market_data.data,
                indicators=["rsi", "macd", "bb", "sma_20", "ema_12", "stoch"]
            )
            
            # Check which indicators were added
            original_cols = set(market_data.data.columns)
            new_cols = set(enhanced_data.columns) - original_cols
            
            test_result = {
                'original_columns': len(original_cols),
                'enhanced_columns': len(enhanced_data.columns),
                'new_indicators': list(new_cols),
                'success': len(new_cols) > 0
            }
            
            logger.info(f"✓ Technical indicators: Added {len(new_cols)} new columns")
            
        except Exception as e:
            logger.error(f"✗ Technical indicators failed: {e}")
            test_result = {'error': str(e)}
        
        self.test_results['technical_indicators'] = test_result
        return test_result
    
    async def test_statistical_models(self):
        """Test statistical forecasting models."""
        logger.info("Testing statistical models...")
        
        try:
            # Generate prediction using statistical models
            result = await self.predictor.predict_single(
                symbol='AAPL',
                horizon=30,
                models=['statistical'],
                period="1y"
            )
            
            test_result = {
                'success': True,
                'symbol': result.symbol,
                'horizon': result.horizon,
                'prediction_points': len(result.predictions),
                'model_performance': result.model_performance,
                'has_confidence_intervals': result.confidence_intervals is not None,
                'accuracy_metrics': result.accuracy_metrics
            }
            
            logger.info(f"✓ Statistical models: Generated {len(result.predictions)} predictions")
            
        except Exception as e:
            logger.error(f"✗ Statistical models failed: {e}")
            test_result = {'error': str(e)}
        
        self.test_results['statistical_models'] = test_result
        return test_result
    
    async def test_neural_models(self):
        """Test neural forecasting models."""
        logger.info("Testing neural models...")
        
        try:
            # Generate prediction using neural models
            result = await self.predictor.predict_single(
                symbol='AAPL',
                horizon=30,
                models=['neural'],
                period="1y"
            )
            
            test_result = {
                'success': True,
                'symbol': result.symbol,
                'horizon': result.horizon,
                'prediction_points': len(result.predictions),
                'model_performance': result.model_performance,
                'accuracy_metrics': result.accuracy_metrics
            }
            
            logger.info(f"✓ Neural models: Generated {len(result.predictions)} predictions")
            
        except Exception as e:
            logger.error(f"✗ Neural models failed: {e}")
            test_result = {'error': str(e)}
        
        self.test_results['neural_models'] = test_result
        return test_result
    
    async def test_ml_models(self):
        """Test machine learning forecasting models."""
        logger.info("Testing ML models...")
        
        try:
            # Generate prediction using ML models
            result = await self.predictor.predict_single(
                symbol='AAPL',
                horizon=30,
                models=['ml'],
                period="1y"
            )
            
            test_result = {
                'success': True,
                'symbol': result.symbol,
                'horizon': result.horizon,
                'prediction_points': len(result.predictions),
                'model_performance': result.model_performance,
                'accuracy_metrics': result.accuracy_metrics
            }
            
            logger.info(f"✓ ML models: Generated {len(result.predictions)} predictions")
            
        except Exception as e:
            logger.error(f"✗ ML models failed: {e}")
            test_result = {'error': str(e)}
        
        self.test_results['ml_models'] = test_result
        return test_result
    
    async def test_timegpt_models(self):
        """Test Nixtla TimeGPT models."""
        logger.info("Testing TimeGPT models...")
        
        if not (self.predictor.model_manager.nixtla_client or self.predictor.model_manager.timegpt):
            test_result = {'skipped': 'No Nixtla API key provided'}
            logger.warning("⚠ TimeGPT: Skipped (no API key)")
            self.test_results['timegpt_models'] = test_result
            return test_result
        
        try:
            # Generate prediction using TimeGPT
            result = await self.predictor.predict_single(
                symbol='AAPL',
                horizon=30,
                models=['timegpt'],
                period="1y"
            )
            
            test_result = {
                'success': True,
                'symbol': result.symbol,
                'horizon': result.horizon,
                'prediction_points': len(result.predictions),
                'model_performance': result.model_performance,
                'has_confidence_intervals': result.confidence_intervals is not None,
                'accuracy_metrics': result.accuracy_metrics
            }
            
            logger.info(f"✓ TimeGPT: Generated {len(result.predictions)} predictions")
            
        except Exception as e:
            logger.error(f"✗ TimeGPT failed: {e}")
            test_result = {'error': str(e)}
        
        self.test_results['timegpt_models'] = test_result
        return test_result
    
    async def test_ensemble_predictions(self):
        """Test ensemble prediction capabilities."""
        logger.info("Testing ensemble predictions...")
        
        try:
            # Use all available models
            available_models = ['statistical', 'neural', 'ml']
            if self.predictor.model_manager.nixtla_client or self.predictor.model_manager.timegpt:
                available_models.insert(0, 'timegpt')
            
            # Generate ensemble prediction
            result = await self.predictor.predict_single(
                symbol='AAPL',
                horizon=30,
                models=available_models,
                period="1y"
            )
            
            test_result = {
                'success': True,
                'symbol': result.symbol,
                'horizon': result.horizon,
                'models_used': list(result.model_performance.keys()),
                'prediction_points': len(result.predictions),
                'has_scenarios': result.scenarios is not None,
                'scenario_count': len(result.scenarios) if result.scenarios else 0
            }
            
            logger.info(f"✓ Ensemble: Used {len(result.model_performance)} models")
            
        except Exception as e:
            logger.error(f"✗ Ensemble predictions failed: {e}")
            test_result = {'error': str(e)}
        
        self.test_results['ensemble_predictions'] = test_result
        return test_result
    
    async def test_batch_predictions(self):
        """Test batch prediction capabilities."""
        logger.info("Testing batch predictions...")
        
        try:
            # Generate batch predictions
            result = await self.predictor.predict_batch(
                symbols=['AAPL', 'MSFT'],
                horizon=30,
                models=['statistical', 'ml'],
                period="6mo"
            )
            
            test_result = {
                'success': True,
                'symbols_processed': len(result.predictions),
                'symbols': list(result.predictions.keys()),
                'has_correlation_matrix': not result.correlation_matrix.empty,
                'market_regime': result.market_regime,
                'portfolio_metrics': result.portfolio_metrics
            }
            
            logger.info(f"✓ Batch: Processed {len(result.predictions)} symbols")
            
        except Exception as e:
            logger.error(f"✗ Batch predictions failed: {e}")
            test_result = {'error': str(e)}
        
        self.test_results['batch_predictions'] = test_result
        return test_result
    
    async def test_enhanced_features(self):
        """Test enhanced prediction with features."""
        logger.info("Testing enhanced features...")
        
        try:
            # Generate prediction with technical and market features
            result = await self.predictor.predict_with_features(
                symbol='AAPL',
                horizon=30,
                include_technical=True,
                include_market_features=True
            )
            
            test_result = {
                'success': True,
                'symbol': result.symbol,
                'horizon': result.horizon,
                'prediction_points': len(result.predictions),
                'has_scenarios': result.scenarios is not None,
                'model_performance': result.model_performance
            }
            
            logger.info(f"✓ Enhanced features: Generated predictions with features")
            
        except Exception as e:
            logger.error(f"✗ Enhanced features failed: {e}")
            test_result = {'error': str(e)}
        
        self.test_results['enhanced_features'] = test_result
        return test_result
    
    async def test_performance_tracking(self):
        """Test model performance tracking."""
        logger.info("Testing performance tracking...")
        
        try:
            # Get model performance
            performance = self.predictor.get_model_performance()
            
            # Get performance summary
            summary = self.predictor.get_model_performance_summary()
            
            test_result = {
                'success': True,
                'available_models': performance.get('available_models', {}),
                'nixtla_available': performance.get('nixtla_available', False),
                'cache_size': performance.get('cache_size', 0),
                'performance_history_size': performance.get('performance_history_size', 0),
                'model_performance_summary': summary
            }
            
            logger.info("✓ Performance tracking: Successfully retrieved metrics")
            
        except Exception as e:
            logger.error(f"✗ Performance tracking failed: {e}")
            test_result = {'error': str(e)}
        
        self.test_results['performance_tracking'] = test_result
        return test_result
    
    def generate_test_report(self):
        """Generate a comprehensive test report."""
        logger.info("Generating test report...")
        
        print("\n" + "="*80)
        print("ENHANCED TIME SERIES AGENT TEST REPORT")
        print("="*80)
        print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Python Version: {sys.version}")
        print(f"Test Symbols: {', '.join(self.test_symbols)}")
        
        # Summary section
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result.get('success', False))
        failed_tests = sum(1 for result in self.test_results.values() if 'error' in result)
        skipped_tests = sum(1 for result in self.test_results.values() if 'skipped' in result)
        
        print(f"\nSUMMARY:")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Skipped: {skipped_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Detailed results
        print(f"\nDETAILED RESULTS:")
        print("-"*80)
        
        for test_name, result in self.test_results.items():
            status = "PASS" if result.get('success') else "SKIP" if 'skipped' in result else "FAIL"
            print(f"\n{test_name.upper().replace('_', ' ')}: {status}")
            
            if 'error' in result:
                print(f"  Error: {result['error']}")
            elif 'skipped' in result:
                print(f"  Reason: {result['skipped']}")
            else:
                # Print key metrics
                for key, value in result.items():
                    if key not in ['success', 'error', 'skipped']:
                        if isinstance(value, dict):
                            print(f"  {key}: {len(value)} items")
                        elif isinstance(value, list):
                            print(f"  {key}: {len(value)} items")
                        else:
                            print(f"  {key}: {value}")
        
        # Environment info
        print(f"\nENVIRONMENT:")
        print("-"*40)
        print(f"Nixtla API Key: {'✓' if os.getenv('NIXTLA_API_KEY') else '✗'}")
        print(f"Alpha Vantage Key: {'✓' if os.getenv('ALPHA_VANTAGE_API_KEY') else '✗'}")
        print(f"IBKR Enabled: {'✓' if os.getenv('USE_IBKR', '').lower() == 'true' else '✗'}")
        
        print("\n" + "="*80)
        
        return {
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'skipped': skipped_tests,
                'success_rate': (passed_tests/total_tests)*100
            },
            'detailed_results': self.test_results
        }

async def main():
    """Main test execution function."""
    logger.info("Starting Enhanced TS Agent Test Suite")
    
    tester = TSAgentTester()
    
    try:
        # Setup
        await tester.setup_environment()
        
        # Run all tests
        test_functions = [
            tester.test_data_fetching,
            tester.test_technical_indicators,
            tester.test_statistical_models,
            tester.test_neural_models,
            tester.test_ml_models,
            tester.test_timegpt_models,
            tester.test_ensemble_predictions,
            tester.test_batch_predictions,
            tester.test_enhanced_features,
            tester.test_performance_tracking
        ]
        
        for test_func in test_functions:
            try:
                await test_func()
            except Exception as e:
                logger.error(f"Test {test_func.__name__} failed: {e}")
        
        # Generate report
        report = tester.generate_test_report()
        
        # Save report to file
        report_file = f"/Users/bytedance/Finance-Bro/backend/test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        import json
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Test report saved to: {report_file}")
        
        return report
        
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        raise

if __name__ == "__main__":
    # Set environment variables for testing
    if not os.getenv('NIXTLA_API_KEY'):
        print("Warning: NIXTLA_API_KEY not set. TimeGPT tests will be skipped.")
    
    if not os.getenv('ALPHA_VANTAGE_API_KEY'):
        print("Info: Using Yahoo Finance as primary data source.")
    
    # Run the test suite
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest suite interrupted by user.")
    except Exception as e:
        print(f"Test suite failed: {e}")
        sys.exit(1)