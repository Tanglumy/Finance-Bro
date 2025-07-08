"""
Formula Evaluator - Executes parsed formulas against market data
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Union, List
from datetime import datetime
import logging

from .parser import ASTNode, FormulaParser
from .functions import IndicatorLibrary

logger = logging.getLogger(__name__)

class EvaluationContext:
    """Context for formula evaluation."""
    
    def __init__(self, data: pd.DataFrame, variables: Optional[Dict[str, Any]] = None):
        self.data = data
        self.variables = variables or {}
        self.current_index = 0
        self.library = IndicatorLibrary()
        
        # Standard column mappings
        self.column_mappings = {
            'open': ['open', 'Open', 'OPEN'],
            'high': ['high', 'High', 'HIGH'],
            'low': ['low', 'Low', 'LOW'],
            'close': ['close', 'Close', 'CLOSE'],
            'volume': ['volume', 'Volume', 'VOLUME'],
            'date': ['date', 'Date', 'DATE', 'timestamp', 'Timestamp']
        }
        
        # Map actual column names
        self.mapped_columns = {}
        for standard_name, possible_names in self.column_mappings.items():
            for col_name in possible_names:
                if col_name in self.data.columns:
                    self.mapped_columns[standard_name] = col_name
                    break
    
    def get_column(self, name: str) -> Optional[pd.Series]:
        """Get column by name with mapping."""
        # Try direct column name
        if name in self.data.columns:
            return self.data[name]
        
        # Try mapped column name
        if name.lower() in self.mapped_columns:
            actual_name = self.mapped_columns[name.lower()]
            return self.data[actual_name]
        
        return None
    
    def set_variable(self, name: str, value: Any):
        """Set variable value."""
        self.variables[name] = value
    
    def get_variable(self, name: str) -> Any:
        """Get variable value."""
        return self.variables.get(name)

class FormulaEvaluator:
    """Evaluates parsed formula AST against market data."""
    
    def __init__(self):
        self.parser = FormulaParser()
        self.library = IndicatorLibrary()
    
    def evaluate(self, formula: str, data: pd.DataFrame, 
                variables: Optional[Dict[str, Any]] = None) -> Union[pd.Series, Any]:
        """
        Evaluate a formula against market data.
        
        Args:
            formula: Formula string to evaluate
            data: Market data DataFrame
            variables: Optional variables dictionary
            
        Returns:
            Result of formula evaluation
        """
        try:
            # Parse the formula
            ast = self.parser.parse(formula)
            
            # Create evaluation context
            context = EvaluationContext(data, variables)
            
            # Evaluate the AST
            result = self._evaluate_node(ast, context)
            
            return result
            
        except Exception as e:
            logger.error(f"Formula evaluation error: {e}")
            raise RuntimeError(f"Formula evaluation failed: {e}")
    
    def _evaluate_node(self, node: ASTNode, context: EvaluationContext) -> Any:
        """Evaluate a single AST node."""
        try:
            if node.type == "number":
                return node.value
            
            elif node.type == "string":
                return node.value
            
            elif node.type == "identifier":
                return self._evaluate_identifier(node, context)
            
            elif node.type == "binary_op":
                return self._evaluate_binary_op(node, context)
            
            elif node.type == "unary_op":
                return self._evaluate_unary_op(node, context)
            
            elif node.type == "function_call":
                return self._evaluate_function_call(node, context)
            
            elif node.type == "conditional":
                return self._evaluate_conditional(node, context)
            
            elif node.type == "assignment":
                return self._evaluate_assignment(node, context)
            
            elif node.type == "array_access":
                return self._evaluate_array_access(node, context)
            
            else:
                raise ValueError(f"Unknown node type: {node.type}")
                
        except Exception as e:
            logger.error(f"Error evaluating node {node.type}: {e}")
            raise
    
    def _evaluate_identifier(self, node: ASTNode, context: EvaluationContext) -> Any:
        """Evaluate identifier (variable or column name)."""
        name = node.value
        
        # Check if it's a variable
        var_value = context.get_variable(name)
        if var_value is not None:
            return var_value
        
        # Check if it's a column
        column = context.get_column(name)
        if column is not None:
            return column
        
        # Check if it's a function/constant
        func = context.library.get_function(name)
        if func is not None:
            return func
        
        raise NameError(f"Undefined identifier: {name}")
    
    def _evaluate_binary_op(self, node: ASTNode, context: EvaluationContext) -> Any:
        """Evaluate binary operation."""
        left = self._evaluate_node(node.children[0], context)
        right = self._evaluate_node(node.children[1], context)
        
        operator = node.value
        
        # Arithmetic operations
        if operator == '+' or operator == TokenType.PLUS:
            return self._safe_operation(left, right, lambda x, y: x + y)
        elif operator == '-' or operator == TokenType.MINUS:
            return self._safe_operation(left, right, lambda x, y: x - y)
        elif operator == '*' or operator == TokenType.MULTIPLY:
            return self._safe_operation(left, right, lambda x, y: x * y)
        elif operator == '/' or operator == TokenType.DIVIDE:
            return self._safe_operation(left, right, lambda x, y: x / y)
        elif operator == '^' or operator == TokenType.POWER:
            return self._safe_operation(left, right, lambda x, y: x ** y)
        elif operator == '%' or operator == TokenType.MODULO:
            return self._safe_operation(left, right, lambda x, y: x % y)
        
        # Comparison operations
        elif operator == '==' or operator == TokenType.EQUAL:
            return self._safe_operation(left, right, lambda x, y: x == y)
        elif operator == '!=' or operator == TokenType.NOT_EQUAL:
            return self._safe_operation(left, right, lambda x, y: x != y)
        elif operator == '<' or operator == TokenType.LESS_THAN:
            return self._safe_operation(left, right, lambda x, y: x < y)
        elif operator == '<=' or operator == TokenType.LESS_EQUAL:
            return self._safe_operation(left, right, lambda x, y: x <= y)
        elif operator == '>' or operator == TokenType.GREATER_THAN:
            return self._safe_operation(left, right, lambda x, y: x > y)
        elif operator == '>=' or operator == TokenType.GREATER_EQUAL:
            return self._safe_operation(left, right, lambda x, y: x >= y)
        
        # Logical operations
        elif operator == '&&' or operator == TokenType.AND:
            return self._safe_operation(left, right, lambda x, y: x & y)
        elif operator == '||' or operator == TokenType.OR:
            return self._safe_operation(left, right, lambda x, y: x | y)
        
        else:
            raise ValueError(f"Unknown binary operator: {operator}")
    
    def _evaluate_unary_op(self, node: ASTNode, context: EvaluationContext) -> Any:
        """Evaluate unary operation."""
        operand = self._evaluate_node(node.children[0], context)
        operator = node.value
        
        if operator == '-' or operator == TokenType.MINUS:
            return -operand
        elif operator == '!' or operator == TokenType.NOT:
            return ~operand if isinstance(operand, pd.Series) else not operand
        else:
            raise ValueError(f"Unknown unary operator: {operator}")
    
    def _evaluate_function_call(self, node: ASTNode, context: EvaluationContext) -> Any:
        """Evaluate function call."""
        func_name = node.value
        
        # Get function from library
        func = context.library.get_function(func_name)
        if func is None:
            raise NameError(f"Unknown function: {func_name}")
        
        # Evaluate arguments
        args = []
        for arg_node in node.children:
            arg_value = self._evaluate_node(arg_node, context)
            args.append(arg_value)
        
        # Call function
        try:
            if callable(func):
                return func(*args)
            else:
                # It's a constant
                return func
        except Exception as e:
            raise RuntimeError(f"Error calling function {func_name}: {e}")
    
    def _evaluate_conditional(self, node: ASTNode, context: EvaluationContext) -> Any:
        """Evaluate conditional expression (ternary operator)."""
        condition = self._evaluate_node(node.children[0], context)
        then_expr = self._evaluate_node(node.children[1], context)
        else_expr = self._evaluate_node(node.children[2], context)
        
        # Handle pandas Series
        if isinstance(condition, pd.Series):
            return pd.Series(np.where(condition, then_expr, else_expr), index=condition.index)
        else:
            return then_expr if condition else else_expr
    
    def _evaluate_assignment(self, node: ASTNode, context: EvaluationContext) -> Any:
        """Evaluate assignment."""
        var_name = node.value
        value = self._evaluate_node(node.children[0], context)
        
        # Store in context
        context.set_variable(var_name, value)
        
        return value
    
    def _evaluate_array_access(self, node: ASTNode, context: EvaluationContext) -> Any:
        """Evaluate array access."""
        array = self._evaluate_node(node.children[0], context)
        index = self._evaluate_node(node.children[1], context)
        
        try:
            if isinstance(array, pd.Series):
                if isinstance(index, int):
                    return array.iloc[index]
                else:
                    return array.loc[index]
            else:
                return array[index]
        except Exception as e:
            raise IndexError(f"Array access error: {e}")
    
    def _safe_operation(self, left: Any, right: Any, operation: callable) -> Any:
        """Safely perform operation handling different data types."""
        try:
            # Handle pandas Series operations
            if isinstance(left, pd.Series) or isinstance(right, pd.Series):
                return operation(left, right)
            
            # Handle numpy arrays
            elif isinstance(left, np.ndarray) or isinstance(right, np.ndarray):
                return operation(left, right)
            
            # Handle scalar operations
            else:
                return operation(left, right)
                
        except Exception as e:
            logger.warning(f"Operation failed: {e}")
            # Return NaN for failed operations
            if isinstance(left, pd.Series):
                return pd.Series([np.nan] * len(left), index=left.index)
            elif isinstance(right, pd.Series):
                return pd.Series([np.nan] * len(right), index=right.index)
            else:
                return np.nan
    
    def validate_formula(self, formula: str) -> Dict[str, Any]:
        """
        Validate a formula without executing it.
        
        Args:
            formula: Formula string to validate
            
        Returns:
            Validation result dictionary
        """
        try:
            # Parse the formula
            ast = self.parser.parse(formula)
            
            # Extract used identifiers
            identifiers = self._extract_identifiers(ast)
            
            # Extract function calls
            function_calls = self._extract_function_calls(ast)
            
            # Check function existence
            unknown_functions = []
            for func_name in function_calls:
                if self.library.get_function(func_name) is None:
                    unknown_functions.append(func_name)
            
            return {
                "valid": len(unknown_functions) == 0,
                "identifiers": identifiers,
                "function_calls": function_calls,
                "unknown_functions": unknown_functions,
                "ast": ast
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "identifiers": [],
                "function_calls": [],
                "unknown_functions": []
            }
    
    def _extract_identifiers(self, node: ASTNode) -> List[str]:
        """Extract all identifiers from AST."""
        identifiers = []
        
        if node.type == "identifier":
            identifiers.append(node.value)
        
        for child in node.children:
            identifiers.extend(self._extract_identifiers(child))
        
        return list(set(identifiers))  # Remove duplicates
    
    def _extract_function_calls(self, node: ASTNode) -> List[str]:
        """Extract all function calls from AST."""
        function_calls = []
        
        if node.type == "function_call":
            function_calls.append(node.value)
        
        for child in node.children:
            function_calls.extend(self._extract_function_calls(child))
        
        return list(set(function_calls))  # Remove duplicates
    
    def get_available_functions(self) -> List[str]:
        """Get list of available functions."""
        return self.library.list_functions()
    
    def get_function_info(self, func_name: str) -> Dict[str, Any]:
        """Get information about a function."""
        return self.library.get_function_info(func_name)
    
    def add_custom_function(self, name: str, func: callable):
        """Add custom function to the evaluator."""
        self.library.add_custom_function(name, func)
    
    def create_sample_data(self, symbol: str = "AAPL", days: int = 252) -> pd.DataFrame:
        """Create sample market data for testing."""
        np.random.seed(42)
        
        # Generate sample price data
        dates = pd.date_range(start='2023-01-01', periods=days, freq='D')
        
        # Simulate realistic price movement
        initial_price = 100.0
        returns = np.random.normal(0.001, 0.02, days)  # 0.1% daily return, 2% volatility
        prices = [initial_price]
        
        for i in range(1, days):
            price = prices[-1] * (1 + returns[i])
            prices.append(price)
        
        # Create OHLC data
        opens = [p * (1 + np.random.normal(0, 0.005)) for p in prices]
        highs = [max(o, p) * (1 + abs(np.random.normal(0, 0.01))) for o, p in zip(opens, prices)]
        lows = [min(o, p) * (1 - abs(np.random.normal(0, 0.01))) for o, p in zip(opens, prices)]
        volumes = [int(np.random.normal(1000000, 200000)) for _ in range(days)]
        
        return pd.DataFrame({
            'date': dates,
            'open': opens,
            'high': highs,
            'low': lows,
            'close': prices,
            'volume': volumes
        })

# Import TokenType at the end to avoid circular import
from .parser import TokenType