"""
Formula Engine - Main interface for formula-based modeling
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import logging
import json

from .evaluator import FormulaEvaluator
from .backtester import FormulaBacktester
from .functions import IndicatorLibrary

logger = logging.getLogger(__name__)

class FormulaModel:
    """Represents a complete formula-based model."""
    
    def __init__(self, name: str, formula: str, description: str = "", 
                 variables: Optional[Dict[str, Any]] = None):
        self.name = name
        self.formula = formula
        self.description = description
        self.variables = variables or {}
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
        self.validation_result = None
        self.backtest_results = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            'name': self.name,
            'formula': self.formula,
            'description': self.description,
            'variables': self.variables,
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'validation_result': self.validation_result,
            'backtest_results': self.backtest_results
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FormulaModel':
        """Create model from dictionary."""
        model = cls(
            name=data['name'],
            formula=data['formula'],
            description=data.get('description', ''),
            variables=data.get('variables', {})
        )
        
        if 'created_at' in data:
            model.created_at = datetime.fromisoformat(data['created_at'])
        if 'last_updated' in data:
            model.last_updated = datetime.fromisoformat(data['last_updated'])
        
        model.validation_result = data.get('validation_result')
        model.backtest_results = data.get('backtest_results')
        
        return model

class FormulaEngine:
    """Main formula engine for creating and managing formula-based models."""
    
    def __init__(self):
        self.evaluator = FormulaEvaluator()
        self.backtester = FormulaBacktester()
        self.library = IndicatorLibrary()
        self.models = {}  # Store formula models
        self.model_results = {}  # Store model evaluation results
    
    def create_model(self, name: str, formula: str, description: str = "",
                    variables: Optional[Dict[str, Any]] = None) -> FormulaModel:
        """
        Create a new formula model.
        
        Args:
            name: Model name
            formula: Formula string
            description: Model description
            variables: Optional variables dictionary
            
        Returns:
            Created FormulaModel
        """
        try:
            # Validate the formula
            validation_result = self.evaluator.validate_formula(formula)
            
            # Create model
            model = FormulaModel(name, formula, description, variables)
            model.validation_result = validation_result
            
            # Store model
            self.models[name] = model
            
            logger.info(f"Created formula model: {name}")
            return model
            
        except Exception as e:
            logger.error(f"Error creating model {name}: {e}")
            raise
    
    def evaluate_model(self, model_name: str, data: pd.DataFrame,
                      variables: Optional[Dict[str, Any]] = None) -> Any:
        """
        Evaluate a formula model against market data.
        
        Args:
            model_name: Name of the model to evaluate
            data: Market data DataFrame
            variables: Optional additional variables
            
        Returns:
            Evaluation result
        """
        try:
            if model_name not in self.models:
                raise ValueError(f"Model {model_name} not found")
            
            model = self.models[model_name]
            
            # Merge variables
            eval_variables = model.variables.copy()
            if variables:
                eval_variables.update(variables)
            
            # Evaluate formula
            result = self.evaluator.evaluate(model.formula, data, eval_variables)
            
            # Store result
            self.model_results[model_name] = {
                'result': result,
                'timestamp': datetime.now(),
                'data_shape': data.shape,
                'variables': eval_variables
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error evaluating model {model_name}: {e}")
            raise
    
    def backtest_model(self, model_name: str, data: pd.DataFrame,
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None,
                      initial_capital: float = 100000,
                      commission: float = 0.001) -> Dict[str, Any]:
        """
        Backtest a formula model.
        
        Args:
            model_name: Name of the model to backtest
            data: Historical market data
            start_date: Backtest start date
            end_date: Backtest end date
            initial_capital: Initial capital
            commission: Commission rate
            
        Returns:
            Backtest results
        """
        try:
            if model_name not in self.models:
                raise ValueError(f"Model {model_name} not found")
            
            model = self.models[model_name]
            
            # Run backtest
            backtest_results = self.backtester.run_backtest(
                model.formula,
                data,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                commission=commission,
                variables=model.variables
            )
            
            # Store results in model
            model.backtest_results = backtest_results
            model.last_updated = datetime.now()
            
            return backtest_results
            
        except Exception as e:
            logger.error(f"Error backtesting model {model_name}: {e}")
            raise
    
    def get_model(self, name: str) -> Optional[FormulaModel]:
        """Get model by name."""
        return self.models.get(name)
    
    def list_models(self) -> List[str]:
        """List all model names."""
        return list(self.models.keys())
    
    def delete_model(self, name: str) -> bool:
        """Delete a model."""
        if name in self.models:
            del self.models[name]
            if name in self.model_results:
                del self.model_results[name]
            logger.info(f"Deleted model: {name}")
            return True
        return False
    
    def update_model(self, name: str, formula: Optional[str] = None,
                    description: Optional[str] = None,
                    variables: Optional[Dict[str, Any]] = None) -> bool:
        """Update an existing model."""
        if name not in self.models:
            return False
        
        model = self.models[name]
        
        if formula is not None:
            # Validate new formula
            validation_result = self.evaluator.validate_formula(formula)
            model.formula = formula
            model.validation_result = validation_result
        
        if description is not None:
            model.description = description
        
        if variables is not None:
            model.variables = variables
        
        model.last_updated = datetime.now()
        logger.info(f"Updated model: {name}")
        return True
    
    def save_models(self, filepath: str):
        """Save models to file."""
        try:
            models_data = {name: model.to_dict() for name, model in self.models.items()}
            
            with open(filepath, 'w') as f:
                json.dump(models_data, f, indent=2, default=str)
            
            logger.info(f"Saved {len(self.models)} models to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving models: {e}")
            raise
    
    def load_models(self, filepath: str):
        """Load models from file."""
        try:
            with open(filepath, 'r') as f:
                models_data = json.load(f)
            
            for name, model_dict in models_data.items():
                model = FormulaModel.from_dict(model_dict)
                self.models[name] = model
            
            logger.info(f"Loaded {len(models_data)} models from {filepath}")
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            raise
    
    def get_model_performance(self, model_name: str) -> Dict[str, Any]:
        """Get performance metrics for a model."""
        if model_name not in self.models:
            return {"error": f"Model {model_name} not found"}
        
        model = self.models[model_name]
        performance = {
            "name": model.name,
            "created_at": model.created_at.isoformat(),
            "last_updated": model.last_updated.isoformat(),
            "validation": model.validation_result,
            "has_backtest": model.backtest_results is not None
        }
        
        if model.backtest_results:
            performance["backtest_metrics"] = {
                "total_return": model.backtest_results.get("total_return"),
                "annualized_return": model.backtest_results.get("annualized_return"),
                "volatility": model.backtest_results.get("volatility"),
                "sharpe_ratio": model.backtest_results.get("sharpe_ratio"),
                "max_drawdown": model.backtest_results.get("max_drawdown")
            }
        
        if model_name in self.model_results:
            result_info = self.model_results[model_name]
            performance["last_evaluation"] = {
                "timestamp": result_info["timestamp"].isoformat(),
                "data_shape": result_info["data_shape"],
                "result_type": type(result_info["result"]).__name__
            }
        
        return performance
    
    def create_strategy(self, name: str, entry_formula: str, exit_formula: str,
                       position_size_formula: Optional[str] = None,
                       description: str = "") -> Dict[str, Any]:
        """
        Create a trading strategy with entry and exit formulas.
        
        Args:
            name: Strategy name
            entry_formula: Formula for entry signals
            exit_formula: Formula for exit signals
            position_size_formula: Optional position sizing formula
            description: Strategy description
            
        Returns:
            Strategy dictionary
        """
        try:
            # Validate formulas
            entry_validation = self.evaluator.validate_formula(entry_formula)
            exit_validation = self.evaluator.validate_formula(exit_formula)
            
            strategy = {
                "name": name,
                "entry_formula": entry_formula,
                "exit_formula": exit_formula,
                "position_size_formula": position_size_formula,
                "description": description,
                "created_at": datetime.now().isoformat(),
                "entry_validation": entry_validation,
                "exit_validation": exit_validation
            }
            
            if position_size_formula:
                position_validation = self.evaluator.validate_formula(position_size_formula)
                strategy["position_validation"] = position_validation
            
            logger.info(f"Created strategy: {name}")
            return strategy
            
        except Exception as e:
            logger.error(f"Error creating strategy {name}: {e}")
            raise
    
    def get_available_functions(self) -> List[str]:
        """Get list of available functions."""
        return self.evaluator.get_available_functions()
    
    def get_function_info(self, func_name: str) -> Dict[str, Any]:
        """Get information about a function."""
        return self.evaluator.get_function_info(func_name)
    
    def add_custom_function(self, name: str, func: callable):
        """Add custom function to the engine."""
        self.evaluator.add_custom_function(name, func)
        logger.info(f"Added custom function: {name}")
    
    def create_sample_formulas(self) -> Dict[str, str]:
        """Create sample formulas for demonstration."""
        return {
            "simple_ma_cross": "MA(close, 20) > MA(close, 50)",
            "rsi_oversold": "RSI(close, 14) < 30",
            "bollinger_squeeze": "BB(close, 20, 2).upper - BB(close, 20, 2).lower < STD(close, 20) * 0.1",
            "momentum_strategy": "ROC(close, 10) > 0.05 AND volume > MA(volume, 20) * 1.5",
            "mean_reversion": "ABS(close - MA(close, 20)) / MA(close, 20) > 0.02",
            "trend_following": "EMA(close, 12) > EMA(close, 26) AND ADX(high, low, close, 14) > 25",
            "volatility_breakout": "ATR(high, low, close, 14) > MA(ATR(high, low, close, 14), 10) * 1.2",
            "volume_confirmation": "volume > MA(volume, 10) * 2 AND close > SHIFT(close, 1)",
            "support_resistance": "close > MAX(high, 20) * 0.98",
            "divergence_signal": "RSI(close, 14) > SHIFT(RSI(close, 14), 5) AND close < SHIFT(close, 5)"
        }
    
    def get_model_dependencies(self, model_name: str) -> Dict[str, List[str]]:
        """Get dependencies for a model."""
        if model_name not in self.models:
            return {"error": f"Model {model_name} not found"}
        
        model = self.models[model_name]
        validation = model.validation_result
        
        if not validation:
            return {"error": "Model not validated"}
        
        return {
            "identifiers": validation.get("identifiers", []),
            "functions": validation.get("function_calls", []),
            "unknown_functions": validation.get("unknown_functions", [])
        }
    
    def optimize_model(self, model_name: str, data: pd.DataFrame,
                      parameter_ranges: Dict[str, tuple],
                      objective: str = "sharpe_ratio") -> Dict[str, Any]:
        """
        Optimize model parameters.
        
        Args:
            model_name: Name of the model to optimize
            data: Historical data for optimization
            parameter_ranges: Dictionary of parameter ranges
            objective: Optimization objective
            
        Returns:
            Optimization results
        """
        try:
            if model_name not in self.models:
                raise ValueError(f"Model {model_name} not found")
            
            model = self.models[model_name]
            
            # Use backtester for optimization
            optimization_results = self.backtester.optimize_parameters(
                model.formula,
                data,
                parameter_ranges,
                objective
            )
            
            return optimization_results
            
        except Exception as e:
            logger.error(f"Error optimizing model {model_name}: {e}")
            raise
    
    def get_engine_stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        return {
            "total_models": len(self.models),
            "total_results": len(self.model_results),
            "available_functions": len(self.get_available_functions()),
            "models_with_backtests": sum(1 for m in self.models.values() if m.backtest_results),
            "valid_models": sum(1 for m in self.models.values() 
                               if m.validation_result and m.validation_result.get("valid", False))
        }