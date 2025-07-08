"""
Tests for Formula Engine module.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

@pytest.mark.formula
class TestFormulaEngine:
    """Test suite for Formula Engine."""
    
    def test_engine_initialization(self, formula_engine):
        """Test formula engine initialization."""
        assert formula_engine is not None
        assert hasattr(formula_engine, 'evaluator')
        assert hasattr(formula_engine, 'backtester')
        assert hasattr(formula_engine, 'models')
    
    def test_create_model(self, formula_engine):
        """Test creating a formula model."""
        model = formula_engine.create_model(
            "test_model",
            "close > open",
            "Test model description"
        )
        
        assert model.name == "test_model"
        assert model.formula == "close > open"
        assert model.description == "Test model description"
        assert model.validation_result is not None
    
    def test_evaluate_model(self, formula_engine, sample_market_data):
        """Test evaluating a formula model."""
        # Create model
        formula_engine.create_model("test_eval", "close > open", "Test evaluation")
        
        # Evaluate model
        result = formula_engine.evaluate_model("test_eval", sample_market_data)
        
        assert result is not None
        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_market_data)
        assert result.dtype == bool
    
    def test_list_models(self, formula_engine):
        """Test listing models."""
        # Create test models
        formula_engine.create_model("model1", "close > open", "Model 1")
        formula_engine.create_model("model2", "volume > 1000", "Model 2")
        
        models = formula_engine.list_models()
        
        assert isinstance(models, list)
        assert "model1" in models
        assert "model2" in models
    
    def test_get_model(self, formula_engine):
        """Test getting a specific model."""
        # Create model
        formula_engine.create_model("get_test", "RSI(close, 14) < 30", "Get test model")
        
        model = formula_engine.get_model("get_test")
        
        assert model is not None
        assert model.name == "get_test"
        assert model.formula == "RSI(close, 14) < 30"
    
    def test_delete_model(self, formula_engine):
        """Test deleting a model."""
        # Create model
        formula_engine.create_model("delete_test", "close", "Delete test model")
        
        # Verify model exists
        assert "delete_test" in formula_engine.list_models()
        
        # Delete model
        success = formula_engine.delete_model("delete_test")
        
        assert success is True
        assert "delete_test" not in formula_engine.list_models()
    
    def test_update_model(self, formula_engine):
        """Test updating a model."""
        # Create model
        formula_engine.create_model("update_test", "close > open", "Original description")
        
        # Update model
        success = formula_engine.update_model(
            "update_test",
            formula="volume > 1000",
            description="Updated description"
        )
        
        assert success is True
        
        # Verify update
        model = formula_engine.get_model("update_test")
        assert model.formula == "volume > 1000"
        assert model.description == "Updated description"
    
    def test_get_available_functions(self, formula_engine):
        """Test getting available functions."""
        functions = formula_engine.get_available_functions()
        
        assert isinstance(functions, list)
        assert len(functions) > 0
        assert "MA" in functions
        assert "RSI" in functions
        assert "MACD" in functions
    
    def test_get_function_info(self, formula_engine):
        """Test getting function information."""
        info = formula_engine.get_function_info("MA")
        
        assert isinstance(info, dict)
        assert "name" in info
        assert "type" in info
        assert info["callable"] is True
    
    def test_sample_formulas(self, formula_engine):
        """Test sample formulas."""
        samples = formula_engine.create_sample_formulas()
        
        assert isinstance(samples, dict)
        assert len(samples) > 0
        assert "simple_ma_cross" in samples
        assert "rsi_oversold" in samples
    
    def test_engine_stats(self, formula_engine):
        """Test engine statistics."""
        # Create some models
        formula_engine.create_model("stats_test1", "close > open", "Test 1")
        formula_engine.create_model("stats_test2", "volume > 1000", "Test 2")
        
        stats = formula_engine.get_engine_stats()
        
        assert isinstance(stats, dict)
        assert "total_models" in stats
        assert "available_functions" in stats
        assert "valid_models" in stats
        assert stats["total_models"] >= 2

@pytest.mark.formula
class TestFormulaEvaluator:
    """Test suite for Formula Evaluator."""
    
    def test_basic_evaluation(self, formula_engine, sample_market_data):
        """Test basic formula evaluation."""
        result = formula_engine.evaluator.evaluate("close", sample_market_data)
        
        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_market_data)
        assert np.allclose(result.values, sample_market_data['close'].values)
    
    def test_arithmetic_operations(self, formula_engine, sample_market_data):
        """Test arithmetic operations in formulas."""
        # Test addition
        result = formula_engine.evaluator.evaluate("close + open", sample_market_data)
        expected = sample_market_data['close'] + sample_market_data['open']
        assert np.allclose(result.values, expected.values)
        
        # Test multiplication
        result = formula_engine.evaluator.evaluate("close * 2", sample_market_data)
        expected = sample_market_data['close'] * 2
        assert np.allclose(result.values, expected.values)
    
    def test_comparison_operations(self, formula_engine, sample_market_data):
        """Test comparison operations in formulas."""
        result = formula_engine.evaluator.evaluate("close > open", sample_market_data)
        expected = sample_market_data['close'] > sample_market_data['open']
        
        assert isinstance(result, pd.Series)
        assert result.dtype == bool
        assert (result == expected).all()
    
    def test_function_calls(self, formula_engine, sample_market_data):
        """Test function calls in formulas."""
        # Test moving average
        result = formula_engine.evaluator.evaluate("MA(close, 10)", sample_market_data)
        
        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_market_data)
        # First 9 values should be NaN
        assert result.iloc[:9].isna().all()
        # Later values should be valid
        assert result.iloc[9:].notna().all()
    
    def test_conditional_expressions(self, formula_engine, sample_market_data):
        """Test conditional expressions."""
        result = formula_engine.evaluator.evaluate(
            "close > open ? 1 : 0", 
            sample_market_data
        )
        
        assert isinstance(result, pd.Series)
        assert set(result.unique()) <= {0, 1}
    
    def test_formula_validation(self, formula_engine):
        """Test formula validation."""
        # Valid formula
        validation = formula_engine.evaluator.validate_formula("close > open")
        assert validation["valid"] is True
        assert "close" in validation["identifiers"]
        assert "open" in validation["identifiers"]
        
        # Invalid formula
        validation = formula_engine.evaluator.validate_formula("close > unknown_column")
        assert validation["valid"] is True  # Parser doesn't check column existence
        assert "unknown_column" in validation["identifiers"]
    
    def test_variables_in_formulas(self, formula_engine, sample_market_data):
        """Test using variables in formulas."""
        variables = {"threshold": 100}
        result = formula_engine.evaluator.evaluate("close > threshold", sample_market_data, variables)
        
        assert isinstance(result, pd.Series)
        assert result.dtype == bool

@pytest.mark.formula
class TestFormulaBacktester:
    """Test suite for Formula Backtester."""
    
    def test_basic_backtest(self, formula_engine, sample_market_data):
        """Test basic backtesting functionality."""
        # Create model
        formula_engine.create_model("backtest_model", "close > open", "Backtest model")
        
        # Run backtest
        results = formula_engine.backtest_model(
            "backtest_model",
            sample_market_data,
            initial_capital=100000
        )
        
        assert "metrics" in results
        assert "equity_curve" in results
        assert "trades" in results
        
        metrics = results["metrics"]
        assert "total_return" in metrics
        assert "sharpe_ratio" in metrics
        assert "max_drawdown" in metrics
        assert "win_rate" in metrics
    
    def test_backtest_with_date_range(self, formula_engine, sample_market_data):
        """Test backtesting with date range."""
        # Create model
        formula_engine.create_model("date_range_model", "volume > 1000000", "Date range model")
        
        # Run backtest with date range
        results = formula_engine.backtest_model(
            "date_range_model",
            sample_market_data,
            start_date="2023-03-01",
            end_date="2023-09-01"
        )
        
        assert "metrics" in results
        assert "backtest_config" in results
        assert results["backtest_config"]["start_date"] == "2023-03-01"
        assert results["backtest_config"]["end_date"] == "2023-09-01"
    
    def test_model_performance_tracking(self, formula_engine, sample_market_data):
        """Test model performance tracking."""
        # Create and backtest model
        formula_engine.create_model("performance_model", "close > MA(close, 10)", "Performance model")
        formula_engine.backtest_model("performance_model", sample_market_data)
        
        # Get performance metrics
        performance = formula_engine.get_model_performance("performance_model")
        
        assert "name" in performance
        assert "created_at" in performance
        assert "validation" in performance
        assert "backtest_metrics" in performance
    
    @pytest.mark.slow
    def test_multiple_models_backtest(self, formula_engine, sample_market_data):
        """Test backtesting multiple models."""
        models = [
            ("model1", "close > open"),
            ("model2", "volume > 1000000"),
            ("model3", "close > MA(close, 20)")
        ]
        
        results = []
        for name, formula in models:
            formula_engine.create_model(name, formula, f"Model {name}")
            result = formula_engine.backtest_model(name, sample_market_data)
            results.append(result)
        
        assert len(results) == 3
        for result in results:
            assert "metrics" in result
            assert "equity_curve" in result

@pytest.mark.formula
@pytest.mark.integration
class TestFormulaEngineIntegration:
    """Integration tests for Formula Engine."""
    
    def test_end_to_end_workflow(self, formula_engine, sample_market_data):
        """Test complete end-to-end workflow."""
        # 1. Create model
        model = formula_engine.create_model(
            "integration_test",
            "MA(close, 10) > MA(close, 20)",
            "Integration test model",
            {"lookback": 20}
        )
        
        # 2. Validate model
        assert model.validation_result["valid"] is True
        
        # 3. Evaluate model
        result = formula_engine.evaluate_model("integration_test", sample_market_data)
        assert isinstance(result, pd.Series)
        
        # 4. Backtest model
        backtest_results = formula_engine.backtest_model("integration_test", sample_market_data)
        assert "metrics" in backtest_results
        
        # 5. Get performance
        performance = formula_engine.get_model_performance("integration_test")
        assert "backtest_metrics" in performance
        
        # 6. Update model
        success = formula_engine.update_model(
            "integration_test",
            description="Updated integration test model"
        )
        assert success is True
        
        # 7. Verify update
        updated_model = formula_engine.get_model("integration_test")
        assert updated_model.description == "Updated integration test model"
    
    def test_model_persistence(self, formula_engine, tmp_path):
        """Test model persistence (save/load)."""
        # Create models
        formula_engine.create_model("persist1", "close > open", "Persist model 1")
        formula_engine.create_model("persist2", "volume > 1000", "Persist model 2")
        
        # Save models
        save_path = tmp_path / "models.json"
        formula_engine.save_models(str(save_path))
        
        # Clear models
        formula_engine.models.clear()
        assert len(formula_engine.list_models()) == 0
        
        # Load models
        formula_engine.load_models(str(save_path))
        
        # Verify models loaded
        models = formula_engine.list_models()
        assert "persist1" in models
        assert "persist2" in models
        
        # Verify model content
        model1 = formula_engine.get_model("persist1")
        assert model1.formula == "close > open"
        assert model1.description == "Persist model 1"