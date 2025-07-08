"""
Formula Engine - DSL for Financial Modeling

This module provides a domain-specific language (DSL) for expressing financial models
and indicators. It allows users to write formulas like:

    price = MA(close, 20) + momentum(volume)
    signal = RSI(14) > 70 ? SELL : RSI(14) < 30 ? BUY : HOLD

The engine supports:
- Technical indicators (MA, RSI, MACD, etc.)
- Mathematical operations
- Conditional logic
- Backtesting capabilities
- Custom functions
"""

from .parser import FormulaParser
from .evaluator import FormulaEvaluator
from .engine import FormulaEngine
from .functions import IndicatorLibrary
from .backtester import FormulaBacktester

__all__ = [
    'FormulaParser',
    'FormulaEvaluator', 
    'FormulaEngine',
    'IndicatorLibrary',
    'FormulaBacktester'
]