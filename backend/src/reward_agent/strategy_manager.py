"""
Strategy Manager

This module manages different investment strategies, their execution,
and coordination with the reward learning system.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
import json
from copy import deepcopy

from .strategy_optimizer import InvestmentStrategy, StrategyType, StrategyParameter
from .learning_agent import RewardLearningAgent, LearningMode
from .performance_tracker import PerformanceTracker

logger = logging.getLogger(__name__)


class StrategyStatus(Enum):
    """Status of a strategy."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    TESTING = "testing"
    DEPRECATED = "deprecated"


class ExecutionMode(Enum):
    """Strategy execution modes."""
    LIVE = "live"
    PAPER = "paper"
    SIMULATION = "simulation"


@dataclass
class StrategyExecution:
    """Strategy execution tracking."""
    strategy_id: str
    execution_mode: ExecutionMode
    start_time: datetime
    end_time: Optional[datetime] = None
    total_trades: int = 0
    successful_trades: int = 0
    total_return: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    execution_notes: List[str] = field(default_factory=list)


@dataclass
class StrategyComparison:
    """Comparison between strategies."""
    strategy_a_id: str
    strategy_b_id: str
    comparison_period: int
    winner: str
    performance_difference: float
    metrics_comparison: Dict[str, Any]
    recommendation: str


class StrategyManager:
    """
    Manages multiple investment strategies, their execution, and performance comparison.
    Coordinates with the reward learning system to continuously improve strategies.
    """
    
    def __init__(self, 
                 learning_agent: Optional[RewardLearningAgent] = None,
                 performance_tracker: Optional[PerformanceTracker] = None,
                 max_strategies: int = 10):
        """
        Initialize the strategy manager.
        
        Args:
            learning_agent: Reward learning agent for strategy optimization
            performance_tracker: Performance tracking system
            max_strategies: Maximum number of strategies to manage
        """
        self.learning_agent = learning_agent or RewardLearningAgent()
        self.performance_tracker = performance_tracker or PerformanceTracker()
        self.max_strategies = max_strategies
        
        # Strategy storage
        self.strategies: Dict[str, InvestmentStrategy] = {}
        self.strategy_executions: Dict[str, List[StrategyExecution]] = {}
        self.strategy_comparisons: List[StrategyComparison] = []
        
        # Active strategy management
        self.active_strategy_id: Optional[str] = None
        self.execution_mode = ExecutionMode.PAPER
        
        # Strategy performance tracking
        self.strategy_rankings: List[str] = []
        self.last_rebalance: Optional[datetime] = None
        
        # Initialize with default strategies
        self._initialize_default_strategies()
    
    def _initialize_default_strategies(self):
        """Initialize with default strategy templates."""
        from .strategy_optimizer import get_strategy_optimizer
        optimizer = get_strategy_optimizer()
        
        # Create default strategies
        default_types = [StrategyType.BALANCED, StrategyType.GROWTH, StrategyType.VALUE]
        
        for strategy_type in default_types:
            strategy = optimizer.get_strategy_template(strategy_type)
            strategy_id = f"default_{strategy_type.value}_{datetime.now().strftime('%Y%m%d')}"
            
            self.strategies[strategy_id] = strategy
            self.strategy_executions[strategy_id] = []
            
            logger.info(f"Initialized default strategy: {strategy_id}")
        
        # Set balanced as initial active strategy
        balanced_id = f"default_{StrategyType.BALANCED.value}_{datetime.now().strftime('%Y%m%d')}"
        if balanced_id in self.strategies:
            self.active_strategy_id = balanced_id
    
    def create_custom_strategy(self,
                             name: str,
                             strategy_type: StrategyType,
                             parameters: Dict[str, float],
                             allocation_rules: Optional[Dict[str, Any]] = None,
                             risk_controls: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a custom investment strategy.
        
        Args:
            name: Strategy name
            strategy_type: Type of strategy
            parameters: Strategy parameters
            allocation_rules: Asset allocation rules
            risk_controls: Risk management controls
            
        Returns:
            Strategy ID
        """
        try:
            # Generate unique ID
            strategy_id = f"custom_{name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create strategy parameters
            strategy_params = {}
            
            # Default parameter ranges based on strategy type
            default_ranges = self._get_default_parameter_ranges(strategy_type)
            
            for param_name, value in parameters.items():
                if param_name in default_ranges:
                    min_val, max_val, step = default_ranges[param_name]
                    strategy_params[param_name] = StrategyParameter(
                        name=param_name,
                        value=value,
                        min_value=min_val,
                        max_value=max_val,
                        step_size=step,
                        description=f"Custom {param_name} parameter"
                    )
            
            # Create strategy
            strategy = InvestmentStrategy(
                name=name,
                strategy_type=strategy_type,
                parameters=strategy_params,
                allocation_rules=allocation_rules or {"max_position_size": 0.1, "cash_target": 0.05},
                risk_controls=risk_controls or {"stop_loss": 0.10, "max_drawdown": 0.15},
                performance_history=[],
                last_updated=datetime.now(),
                confidence_score=0.5,
                version=1
            )
            
            # Store strategy
            self.strategies[strategy_id] = strategy
            self.strategy_executions[strategy_id] = []
            
            logger.info(f"Created custom strategy: {strategy_id}")
            return strategy_id
            
        except Exception as e:
            logger.error(f"Error creating custom strategy: {e}")
            raise
    
    def optimize_strategy(self, 
                         strategy_id: str,
                         market_data: Dict[str, pd.Series],
                         target_improvement: float = 0.1) -> Dict[str, Any]:
        """
        Optimize a specific strategy using the learning agent.
        
        Args:
            strategy_id: ID of strategy to optimize
            market_data: Market data for optimization
            target_improvement: Target improvement threshold
            
        Returns:
            Optimization results
        """
        if strategy_id not in self.strategies:
            raise ValueError(f"Strategy {strategy_id} not found")
        
        try:
            strategy = self.strategies[strategy_id]
            
            # Use learning agent's strategy optimizer
            optimization_result = self.learning_agent.strategy_optimizer.optimize_strategy(
                strategy, market_data, target_improvement
            )
            
            # Update strategy if improvement achieved
            if optimization_result.improvement_score > 0:
                # Create new version
                new_strategy = deepcopy(optimization_result.optimized_strategy)
                new_strategy.version = strategy.version + 1
                new_strategy.last_updated = datetime.now()
                new_strategy.confidence_score = min(1.0, strategy.confidence_score + optimization_result.improvement_score)
                
                # Store optimized strategy
                optimized_id = f"{strategy_id}_v{new_strategy.version}"
                self.strategies[optimized_id] = new_strategy
                self.strategy_executions[optimized_id] = []
                
                logger.info(f"Strategy optimized: {strategy_id} -> {optimized_id} "
                           f"(improvement: {optimization_result.improvement_score:.2%})")
                
                return {
                    "success": True,
                    "original_strategy_id": strategy_id,
                    "optimized_strategy_id": optimized_id,
                    "improvement_score": optimization_result.improvement_score,
                    "recommendations": optimization_result.recommendations,
                    "backtested_performance": optimization_result.backtested_performance
                }
            else:
                return {
                    "success": False,
                    "message": "No significant improvement achieved",
                    "current_performance": optimization_result.backtested_performance
                }
                
        except Exception as e:
            logger.error(f"Error optimizing strategy {strategy_id}: {e}")
            return {"success": False, "error": str(e)}
    
    def compare_strategies(self,
                          strategy_ids: List[str],
                          comparison_period_days: int = 30,
                          metrics: Optional[List[str]] = None) -> StrategyComparison:
        """
        Compare performance of multiple strategies.
        
        Args:
            strategy_ids: List of strategy IDs to compare
            comparison_period_days: Period for comparison
            metrics: Metrics to compare (default: all)
            
        Returns:
            Strategy comparison results
        """
        if len(strategy_ids) < 2:
            raise ValueError("Need at least 2 strategies to compare")
        
        metrics = metrics or ["total_return", "sharpe_ratio", "max_drawdown", "volatility", "win_rate"]
        
        # Simulate performance for each strategy
        strategy_performances = {}
        
        for strategy_id in strategy_ids:
            if strategy_id not in self.strategies:
                continue
                
            strategy = self.strategies[strategy_id]
            
            # Simulate strategy performance
            performance = self._simulate_strategy_performance(strategy, comparison_period_days)
            strategy_performances[strategy_id] = performance
        
        # Find best performing strategy
        best_strategy_id = max(
            strategy_performances.keys(),
            key=lambda sid: strategy_performances[sid]["sharpe_ratio"]
        )
        
        # Create comparison
        primary_id = strategy_ids[0]
        secondary_id = strategy_ids[1]
        
        primary_performance = strategy_performances.get(primary_id, {})
        secondary_performance = strategy_performances.get(secondary_id, {})
        
        # Calculate performance difference
        performance_diff = (
            primary_performance.get("total_return", 0) - 
            secondary_performance.get("total_return", 0)
        )
        
        winner = primary_id if performance_diff > 0 else secondary_id
        
        # Detailed metrics comparison
        metrics_comparison = {}
        for metric in metrics:
            metrics_comparison[metric] = {
                primary_id: primary_performance.get(metric, 0),
                secondary_id: secondary_performance.get(metric, 0),
                "difference": (primary_performance.get(metric, 0) - 
                             secondary_performance.get(metric, 0)),
                "winner": primary_id if primary_performance.get(metric, 0) > secondary_performance.get(metric, 0) else secondary_id
            }
        
        # Generate recommendation
        recommendation = self._generate_strategy_recommendation(
            strategy_performances, best_strategy_id, metrics_comparison
        )
        
        comparison = StrategyComparison(
            strategy_a_id=primary_id,
            strategy_b_id=secondary_id,
            comparison_period=comparison_period_days,
            winner=winner,
            performance_difference=abs(performance_diff),
            metrics_comparison=metrics_comparison,
            recommendation=recommendation
        )
        
        self.strategy_comparisons.append(comparison)
        return comparison
    
    def set_active_strategy(self, strategy_id: str) -> bool:
        """
        Set the active strategy for execution.
        
        Args:
            strategy_id: ID of strategy to activate
            
        Returns:
            Success status
        """
        if strategy_id not in self.strategies:
            logger.error(f"Strategy {strategy_id} not found")
            return False
        
        self.active_strategy_id = strategy_id
        logger.info(f"Active strategy set to: {strategy_id}")
        return True
    
    def get_active_strategy(self) -> Optional[InvestmentStrategy]:
        """Get the currently active strategy."""
        if self.active_strategy_id and self.active_strategy_id in self.strategies:
            return self.strategies[self.active_strategy_id]
        return None
    
    def execute_strategy_rebalancing(self,
                                   portfolio_data: Dict[str, Any],
                                   market_data: Dict[str, pd.Series]) -> Dict[str, Any]:
        """
        Execute portfolio rebalancing based on active strategy.
        
        Args:
            portfolio_data: Current portfolio data
            market_data: Current market data
            
        Returns:
            Rebalancing recommendations
        """
        active_strategy = self.get_active_strategy()
        if not active_strategy:
            return {"error": "No active strategy set"}
        
        try:
            # Analyze current portfolio vs strategy targets
            current_allocation = self._analyze_current_allocation(portfolio_data)
            target_allocation = self._calculate_target_allocation(active_strategy, market_data)
            
            # Generate rebalancing actions
            rebalancing_actions = self._generate_rebalancing_actions(
                current_allocation, target_allocation, active_strategy
            )
            
            # Execute in paper mode
            execution_result = self._execute_rebalancing_actions(
                rebalancing_actions, portfolio_data
            )
            
            # Track execution
            if self.active_strategy_id:
                execution = StrategyExecution(
                    strategy_id=self.active_strategy_id,
                    execution_mode=self.execution_mode,
                    start_time=datetime.now(),
                    total_trades=len(rebalancing_actions),
                    execution_notes=[f"Rebalancing executed with {len(rebalancing_actions)} actions"]
                )
                
                self.strategy_executions[self.active_strategy_id].append(execution)
            
            self.last_rebalance = datetime.now()
            
            return {
                "success": True,
                "strategy_id": self.active_strategy_id,
                "rebalancing_actions": rebalancing_actions,
                "execution_result": execution_result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error executing strategy rebalancing: {e}")
            return {"success": False, "error": str(e)}
    
    def get_strategy_rankings(self, 
                            period_days: int = 30,
                            metric: str = "sharpe_ratio") -> List[Dict[str, Any]]:
        """
        Get strategy rankings based on performance metrics.
        
        Args:
            period_days: Evaluation period
            metric: Ranking metric
            
        Returns:
            Ranked list of strategies
        """
        rankings = []
        
        for strategy_id, strategy in self.strategies.items():
            # Simulate performance
            performance = self._simulate_strategy_performance(strategy, period_days)
            
            rankings.append({
                "strategy_id": strategy_id,
                "strategy_name": strategy.name,
                "strategy_type": strategy.strategy_type.value,
                "performance_score": performance.get(metric, 0),
                "total_return": performance.get("total_return", 0),
                "sharpe_ratio": performance.get("sharpe_ratio", 0),
                "max_drawdown": performance.get("max_drawdown", 0),
                "confidence_score": strategy.confidence_score,
                "version": strategy.version,
                "last_updated": strategy.last_updated.isoformat()
            })
        
        # Sort by performance metric
        rankings.sort(key=lambda x: x["performance_score"], reverse=True)
        
        # Update internal rankings
        self.strategy_rankings = [r["strategy_id"] for r in rankings]
        
        return rankings
    
    def get_strategy_insights(self) -> Dict[str, Any]:
        """Get insights about strategy performance and management."""
        
        insights = {
            "total_strategies": len(self.strategies),
            "active_strategy": self.active_strategy_id,
            "execution_mode": self.execution_mode.value,
            "last_rebalance": self.last_rebalance.isoformat() if self.last_rebalance else None,
            "strategy_distribution": {},
            "performance_summary": {},
            "recommendations": []
        }
        
        # Strategy type distribution
        strategy_types = {}
        for strategy in self.strategies.values():
            strategy_type = strategy.strategy_type.value
            strategy_types[strategy_type] = strategy_types.get(strategy_type, 0) + 1
        insights["strategy_distribution"] = strategy_types
        
        # Performance summary
        if self.strategies:
            total_confidence = sum(s.confidence_score for s in self.strategies.values())
            avg_confidence = total_confidence / len(self.strategies)
            
            insights["performance_summary"] = {
                "average_confidence": avg_confidence,
                "total_executions": sum(len(execs) for execs in self.strategy_executions.values()),
                "total_comparisons": len(self.strategy_comparisons)
            }
        
        # Generate recommendations
        recommendations = []
        
        if not self.active_strategy_id:
            recommendations.append("No active strategy set - consider activating a strategy")
        
        if self.last_rebalance is None or (datetime.now() - self.last_rebalance).days > 30:
            recommendations.append("Portfolio rebalancing may be needed")
        
        if len(self.strategies) < 3:
            recommendations.append("Consider creating more strategy variants for comparison")
        
        low_confidence_strategies = [
            s.name for s in self.strategies.values() if s.confidence_score < 0.3
        ]
        if low_confidence_strategies:
            recommendations.append(f"Low confidence strategies need optimization: {', '.join(low_confidence_strategies)}")
        
        insights["recommendations"] = recommendations
        
        return insights
    
    def _get_default_parameter_ranges(self, strategy_type: StrategyType) -> Dict[str, Tuple[float, float, float]]:
        """Get default parameter ranges for strategy type."""
        
        if strategy_type == StrategyType.GROWTH:
            return {
                "risk_level": (0.3, 1.0, 0.05),
                "return_target": (0.08, 0.30, 0.01),
                "growth_weight": (0.5, 1.0, 0.05),
                "momentum_factor": (0.0, 0.8, 0.05)
            }
        elif strategy_type == StrategyType.VALUE:
            return {
                "risk_level": (0.2, 0.8, 0.05),
                "return_target": (0.06, 0.20, 0.01),
                "value_weight": (0.5, 1.0, 0.05),
                "pe_threshold": (5.0, 25.0, 0.5)
            }
        else:  # BALANCED and others
            return {
                "risk_level": (0.3, 0.8, 0.05),
                "return_target": (0.07, 0.25, 0.01),
                "growth_value_balance": (0.2, 0.8, 0.05),
                "international_weight": (0.1, 0.5, 0.05)
            }
    
    def _simulate_strategy_performance(self, 
                                     strategy: InvestmentStrategy, 
                                     days: int) -> Dict[str, float]:
        """Simulate strategy performance."""
        
        # Extract strategy parameters
        risk_level = strategy.parameters.get('risk_level', type('', (), {'value': 0.5})()).value
        return_target = strategy.parameters.get('return_target', type('', (), {'value': 0.08})()).value
        
        # Generate returns based on strategy
        daily_return = return_target / 252
        daily_volatility = 0.01 + risk_level * 0.02
        
        returns = np.random.normal(daily_return, daily_volatility, days)
        
        # Add strategy-specific effects
        if strategy.strategy_type == StrategyType.MOMENTUM:
            # Add momentum persistence
            for i in range(1, len(returns)):
                momentum = 0.1 * returns[i-1]
                returns[i] += momentum
        elif strategy.strategy_type == StrategyType.MEAN_REVERSION:
            # Add mean reversion
            for i in range(1, len(returns)):
                reversion = -0.05 * returns[i-1]
                returns[i] += reversion
        
        # Calculate performance metrics
        total_return = (1 + pd.Series(returns)).prod() - 1
        volatility = pd.Series(returns).std() * np.sqrt(252)
        
        # Sharpe ratio
        excess_return = pd.Series(returns).mean() * 252 - 0.03
        sharpe_ratio = excess_return / volatility if volatility > 0 else 0
        
        # Max drawdown
        cumulative = (1 + pd.Series(returns)).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = abs(drawdown.min())
        
        # Win rate
        win_rate = len(returns[returns > 0]) / len(returns)
        
        return {
            "total_return": total_return,
            "volatility": volatility,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "win_rate": win_rate
        }
    
    def _analyze_current_allocation(self, portfolio_data: Dict[str, Any]) -> Dict[str, float]:
        """Analyze current portfolio allocation."""
        positions = portfolio_data.get('positions', [])
        total_value = portfolio_data.get('total_value', 1)
        
        allocation = {}
        for position in positions:
            symbol = position.get('symbol', 'Unknown')
            value = position.get('market_value', 0)
            allocation[symbol] = value / total_value
        
        # Add cash allocation
        cash_balance = portfolio_data.get('cash_balance', 0)
        allocation['CASH'] = cash_balance / total_value
        
        return allocation
    
    def _calculate_target_allocation(self, 
                                   strategy: InvestmentStrategy,
                                   market_data: Dict[str, pd.Series]) -> Dict[str, float]:
        """Calculate target allocation based on strategy."""
        
        # Simplified target allocation based on strategy type
        if strategy.strategy_type == StrategyType.GROWTH:
            return {
                "GROWTH_STOCKS": 0.7,
                "TECH_ETFS": 0.2,
                "CASH": 0.1
            }
        elif strategy.strategy_type == StrategyType.VALUE:
            return {
                "VALUE_STOCKS": 0.6,
                "DIVIDEND_ETFS": 0.25,
                "CASH": 0.15
            }
        else:  # BALANCED
            return {
                "BROAD_MARKET": 0.5,
                "INTERNATIONAL": 0.2,
                "BONDS": 0.2,
                "CASH": 0.1
            }
    
    def _generate_rebalancing_actions(self,
                                    current_allocation: Dict[str, float],
                                    target_allocation: Dict[str, float],
                                    strategy: InvestmentStrategy) -> List[Dict[str, Any]]:
        """Generate rebalancing actions."""
        
        actions = []
        threshold = 0.05  # 5% threshold for rebalancing
        
        for asset, target_weight in target_allocation.items():
            current_weight = current_allocation.get(asset, 0)
            difference = target_weight - current_weight
            
            if abs(difference) > threshold:
                action_type = "BUY" if difference > 0 else "SELL"
                actions.append({
                    "action": action_type,
                    "asset": asset,
                    "current_weight": current_weight,
                    "target_weight": target_weight,
                    "weight_difference": difference,
                    "priority": abs(difference)  # Higher difference = higher priority
                })
        
        # Sort by priority (largest differences first)
        actions.sort(key=lambda x: x["priority"], reverse=True)
        
        return actions
    
    def _execute_rebalancing_actions(self,
                                   actions: List[Dict[str, Any]],
                                   portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute rebalancing actions (simulation)."""
        
        execution_result = {
            "executed_actions": len(actions),
            "total_value_moved": 0,
            "estimated_fees": 0,
            "execution_time": datetime.now().isoformat(),
            "success_rate": 1.0  # Assuming 100% success in simulation
        }
        
        total_value = portfolio_data.get('total_value', 100000)
        
        for action in actions:
            value_to_move = abs(action["weight_difference"]) * total_value
            execution_result["total_value_moved"] += value_to_move
            execution_result["estimated_fees"] += value_to_move * 0.001  # 0.1% estimated fee
        
        return execution_result
    
    def _generate_strategy_recommendation(self,
                                        strategy_performances: Dict[str, Dict[str, float]],
                                        best_strategy_id: str,
                                        metrics_comparison: Dict[str, Any]) -> str:
        """Generate strategy recommendation based on comparison."""
        
        best_performance = strategy_performances[best_strategy_id]
        
        recommendation = f"Recommended strategy: {best_strategy_id} "
        
        if best_performance["sharpe_ratio"] > 1.5:
            recommendation += "(Excellent riOPENAI_API_KEY_REDACTED returns)"
        elif best_performance["sharpe_ratio"] > 1.0:
            recommendation += "(Good riOPENAI_API_KEY_REDACTED returns)"
        else:
            recommendation += "(Moderate performance - consider optimization)"
        
        if best_performance["max_drawdown"] > 0.15:
            recommendation += ". Warning: High drawdown risk detected."
        
        return recommendation


# Global strategy manager instance
_strategy_manager = None

def get_strategy_manager() -> StrategyManager:
    """Get the global strategy manager instance."""
    global _strategy_manager
    if _strategy_manager is None:
        _strategy_manager = StrategyManager()
    return _strategy_manager