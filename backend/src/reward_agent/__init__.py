"""
Reward Agent Module

This module implements a sophisticated reward-based learning system that uses portfolio
performance metrics to continuously adapt and improve investment strategies.

Key Components:
- Performance evaluation and reward calculation
- Strategy adaptation algorithms
- Learning feedback loops
- Portfolio optimization based on rewards
"""

from .reward_calculator import RewardCalculator
from .strategy_optimizer import StrategyOptimizer
from .learning_agent import RewardLearningAgent
from .performance_tracker import PerformanceTracker
from .strategy_manager import StrategyManager

__all__ = [
    'RewardCalculator',
    'StrategyOptimizer', 
    'RewardLearningAgent',
    'PerformanceTracker',
    'StrategyManager'
]