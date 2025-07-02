"""
Strategy Optimizer

This module implements sophisticated algorithms to adapt and optimize investment strategies
based on reward feedback from portfolio performance.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
from copy import deepcopy
import json

from .reward_calculator import RewardScore, RewardCalculator

logger = logging.getLogger(__name__)


class StrategyType(Enum):
    """Types of investment strategies."""
    GROWTH = "growth"
    VALUE = "value"
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    DEFENSIVE = "defensive"
    AGGRESSIVE = "aggressive"
    BALANCED = "balanced"
    SECTOR_ROTATION = "sector_rotation"
    TREND_FOLLOWING = "trend_following"
    CONTRARIAN = "contrarian"


class OptimizationMethod(Enum):
    """Optimization methods for strategy improvement."""
    GRADIENT_ASCENT = "gradient_ascent"
    GENETIC_ALGORITHM = "genetic_algorithm"
    BAYESIAN_OPTIMIZATION = "bayesian_optimization"
    REINFORCEMENT_LEARNING = "reinforcement_learning"
    ENSEMBLE_LEARNING = "ensemble_learning"


@dataclass
class StrategyParameter:
    """Individual strategy parameter."""
    name: str
    value: float
    min_value: float
    max_value: float
    step_size: float
    description: str
    impact_weight: float = 1.0  # How much this parameter affects strategy performance


@dataclass
class InvestmentStrategy:
    """Complete investment strategy definition."""
    name: str
    strategy_type: StrategyType
    parameters: Dict[str, StrategyParameter]
    allocation_rules: Dict[str, Any]
    risk_controls: Dict[str, Any]
    performance_history: List[Dict[str, Any]] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)
    confidence_score: float = 0.5
    version: int = 1


@dataclass
class OptimizationResult:
    """Result of strategy optimization."""
    original_strategy: InvestmentStrategy
    optimized_strategy: InvestmentStrategy
    improvement_score: float
    optimization_method: OptimizationMethod
    iterations: int
    convergence_achieved: bool
    optimization_time: float
    backtested_performance: Dict[str, Any]
    recommendations: List[str]


class StrategyOptimizer:
    """
    Advanced strategy optimization engine that uses reward feedback to improve
    investment strategies through various optimization algorithms.
    """
    
    def __init__(self, 
                 reward_calculator: Optional[RewardCalculator] = None,
                 optimization_method: OptimizationMethod = OptimizationMethod.GRADIENT_ASCENT,
                 learning_rate: float = 0.01,
                 max_iterations: int = 100):
        """
        Initialize the strategy optimizer.
        
        Args:
            reward_calculator: Instance for calculating strategy rewards
            optimization_method: Method to use for optimization
            learning_rate: Learning rate for gradient-based methods
            max_iterations: Maximum optimization iterations
        """
        self.reward_calculator = reward_calculator or RewardCalculator()
        self.optimization_method = optimization_method
        self.learning_rate = learning_rate
        self.max_iterations = max_iterations
        
        # Optimization history
        self.optimization_history: List[OptimizationResult] = []
        
        # Strategy templates
        self.strategy_templates = self._initialize_strategy_templates()
    
    def optimize_strategy(self,
                         current_strategy: InvestmentStrategy,
                         historical_data: Dict[str, pd.Series],
                         target_improvement: float = 0.1) -> OptimizationResult:
        """
        Optimize an investment strategy based on historical performance and rewards.
        
        Args:
            current_strategy: Current strategy to optimize
            historical_data: Historical market and portfolio data
            target_improvement: Target improvement threshold (0.1 = 10% improvement)
            
        Returns:
            OptimizationResult: Results of optimization process
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting optimization of strategy: {current_strategy.name}")
            
            # Choose optimization method
            if self.optimization_method == OptimizationMethod.GRADIENT_ASCENT:
                result = self._gradient_ascent_optimization(
                    current_strategy, historical_data, target_improvement
                )
            elif self.optimization_method == OptimizationMethod.GENETIC_ALGORITHM:
                result = self._genetic_algorithm_optimization(
                    current_strategy, historical_data, target_improvement
                )
            elif self.optimization_method == OptimizationMethod.BAYESIAN_OPTIMIZATION:
                result = self._bayesian_optimization(
                    current_strategy, historical_data, target_improvement
                )
            elif self.optimization_method == OptimizationMethod.REINFORCEMENT_LEARNING:
                result = self._reinforcement_learning_optimization(
                    current_strategy, historical_data, target_improvement
                )
            else:
                result = self._ensemble_optimization(
                    current_strategy, historical_data, target_improvement
                )
            
            optimization_time = (datetime.now() - start_time).total_seconds()
            result.optimization_time = optimization_time
            
            # Store optimization history
            self.optimization_history.append(result)
            
            logger.info(f"Optimization completed in {optimization_time:.2f}s with {result.improvement_score:.2%} improvement")
            
            return result
            
        except Exception as e:
            logger.error(f"Error during strategy optimization: {e}")
            return self._create_failed_optimization_result(current_strategy, str(e))
    
    def _gradient_ascent_optimization(self,
                                    strategy: InvestmentStrategy,
                                    historical_data: Dict[str, pd.Series],
                                    target_improvement: float) -> OptimizationResult:
        """Optimize strategy using gradient ascent."""
        original_strategy = deepcopy(strategy)
        current_strategy = deepcopy(strategy)
        
        # Calculate baseline performance
        baseline_score = self._evaluate_strategy_performance(current_strategy, historical_data)
        best_score = baseline_score
        best_strategy = deepcopy(current_strategy)
        
        iterations = 0
        convergence_achieved = False
        
        for iteration in range(self.max_iterations):
            iterations += 1
            improved = False
            
            # Try to improve each parameter
            for param_name, param in current_strategy.parameters.items():
                # Calculate gradient by finite differences
                gradient = self._calculate_parameter_gradient(
                    current_strategy, param_name, historical_data
                )
                
                # Update parameter
                old_value = param.value
                new_value = old_value + self.learning_rate * gradient
                
                # Clamp to bounds
                new_value = max(param.min_value, min(param.max_value, new_value))
                param.value = new_value
                
                # Evaluate new strategy
                new_score = self._evaluate_strategy_performance(current_strategy, historical_data)
                
                if new_score > best_score:
                    best_score = new_score
                    best_strategy = deepcopy(current_strategy)
                    improved = True
                else:
                    # Revert change if no improvement
                    param.value = old_value
            
            # Check for convergence
            improvement = (best_score - baseline_score) / baseline_score
            if improvement >= target_improvement:
                convergence_achieved = True
                break
            
            if not improved:
                break
        
        # Generate recommendations
        recommendations = self._generate_optimization_recommendations(
            original_strategy, best_strategy, best_score - baseline_score
        )
        
        return OptimizationResult(
            original_strategy=original_strategy,
            optimized_strategy=best_strategy,
            improvement_score=(best_score - baseline_score) / baseline_score,
            optimization_method=OptimizationMethod.GRADIENT_ASCENT,
            iterations=iterations,
            convergence_achieved=convergence_achieved,
            optimization_time=0,  # Will be set by caller
            backtested_performance=self._backtest_strategy(best_strategy, historical_data),
            recommendations=recommendations
        )
    
    def _genetic_algorithm_optimization(self,
                                      strategy: InvestmentStrategy,
                                      historical_data: Dict[str, pd.Series],
                                      target_improvement: float) -> OptimizationResult:
        """Optimize strategy using genetic algorithm."""
        original_strategy = deepcopy(strategy)
        
        # Genetic algorithm parameters
        population_size = 20
        mutation_rate = 0.1
        crossover_rate = 0.8
        elite_ratio = 0.2
        
        # Initialize population
        population = [self._mutate_strategy(deepcopy(strategy), 0.5) for _ in range(population_size)]
        
        best_strategy = deepcopy(strategy)
        best_score = self._evaluate_strategy_performance(strategy, historical_data)
        baseline_score = best_score
        
        iterations = 0
        convergence_achieved = False
        
        for generation in range(self.max_iterations // 10):  # Fewer generations for GA
            iterations += 1
            
            # Evaluate population
            fitness_scores = []
            for individual in population:
                score = self._evaluate_strategy_performance(individual, historical_data)
                fitness_scores.append(score)
                
                if score > best_score:
                    best_score = score
                    best_strategy = deepcopy(individual)
            
            # Check convergence
            improvement = (best_score - baseline_score) / baseline_score
            if improvement >= target_improvement:
                convergence_achieved = True
                break
            
            # Selection and reproduction
            population = self._genetic_selection_and_reproduction(
                population, fitness_scores, population_size, elite_ratio, crossover_rate, mutation_rate
            )
        
        recommendations = self._generate_optimization_recommendations(
            original_strategy, best_strategy, best_score - baseline_score
        )
        
        return OptimizationResult(
            original_strategy=original_strategy,
            optimized_strategy=best_strategy,
            improvement_score=(best_score - baseline_score) / baseline_score,
            optimization_method=OptimizationMethod.GENETIC_ALGORITHM,
            iterations=iterations,
            convergence_achieved=convergence_achieved,
            optimization_time=0,
            backtested_performance=self._backtest_strategy(best_strategy, historical_data),
            recommendations=recommendations
        )
    
    def _bayesian_optimization(self,
                             strategy: InvestmentStrategy,
                             historical_data: Dict[str, pd.Series],
                             target_improvement: float) -> OptimizationResult:
        """Optimize strategy using Bayesian optimization (simplified implementation)."""
        # For now, implement a simplified version that samples intelligently
        original_strategy = deepcopy(strategy)
        
        # Sample strategies around current one with increasing exploration
        n_samples = min(50, self.max_iterations)
        samples = []
        
        for i in range(n_samples):
            # Exploration factor increases over time
            exploration_factor = 0.1 + 0.4 * (i / n_samples)
            candidate = self._mutate_strategy(deepcopy(strategy), exploration_factor)
            score = self._evaluate_strategy_performance(candidate, historical_data)
            samples.append((candidate, score))
        
        # Find best strategy
        best_strategy, best_score = max(samples, key=lambda x: x[1])
        baseline_score = self._evaluate_strategy_performance(strategy, historical_data)
        
        improvement = (best_score - baseline_score) / baseline_score
        convergence_achieved = improvement >= target_improvement
        
        recommendations = self._generate_optimization_recommendations(
            original_strategy, best_strategy, best_score - baseline_score
        )
        
        return OptimizationResult(
            original_strategy=original_strategy,
            optimized_strategy=best_strategy,
            improvement_score=improvement,
            optimization_method=OptimizationMethod.BAYESIAN_OPTIMIZATION,
            iterations=n_samples,
            convergence_achieved=convergence_achieved,
            optimization_time=0,
            backtested_performance=self._backtest_strategy(best_strategy, historical_data),
            recommendations=recommendations
        )
    
    def _reinforcement_learning_optimization(self,
                                           strategy: InvestmentStrategy,
                                           historical_data: Dict[str, pd.Series],
                                           target_improvement: float) -> OptimizationResult:
        """Optimize strategy using reinforcement learning principles."""
        # Simplified RL: Q-learning for parameter adjustments
        original_strategy = deepcopy(strategy)
        current_strategy = deepcopy(strategy)
        
        # RL parameters
        epsilon = 0.3  # Exploration rate
        gamma = 0.95   # Discount factor
        alpha = 0.1    # Learning rate
        
        # Action space: increase/decrease each parameter
        actions = []
        for param_name in current_strategy.parameters.keys():
            actions.extend([f"increase_{param_name}", f"decrease_{param_name}"])
        
        # Q-table (simplified)
        q_table = {action: 0.0 for action in actions}
        
        baseline_score = self._evaluate_strategy_performance(current_strategy, historical_data)
        best_score = baseline_score
        best_strategy = deepcopy(current_strategy)
        
        iterations = 0
        convergence_achieved = False
        
        for episode in range(self.max_iterations // 5):
            iterations += 1
            episode_strategy = deepcopy(current_strategy)
            
            # Choose action (epsilon-greedy)
            if np.random.random() < epsilon:
                action = np.random.choice(actions)
            else:
                action = max(q_table.keys(), key=lambda a: q_table[a])
            
            # Apply action
            param_name = action.split('_', 1)[1]
            direction = action.split('_')[0]
            
            param = episode_strategy.parameters[param_name]
            step = (param.max_value - param.min_value) * 0.05  # 5% step
            
            if direction == "increase":
                param.value = min(param.max_value, param.value + step)
            else:
                param.value = max(param.min_value, param.value - step)
            
            # Evaluate action
            new_score = self._evaluate_strategy_performance(episode_strategy, historical_data)
            reward = new_score - baseline_score
            
            # Update Q-table
            q_table[action] = q_table[action] + alpha * (reward + gamma * max(q_table.values()) - q_table[action])
            
            # Update best strategy
            if new_score > best_score:
                best_score = new_score
                best_strategy = deepcopy(episode_strategy)
                current_strategy = deepcopy(episode_strategy)
            
            # Check convergence
            improvement = (best_score - baseline_score) / baseline_score
            if improvement >= target_improvement:
                convergence_achieved = True
                break
            
            # Decay exploration
            epsilon *= 0.995
        
        recommendations = self._generate_optimization_recommendations(
            original_strategy, best_strategy, best_score - baseline_score
        )
        
        return OptimizationResult(
            original_strategy=original_strategy,
            optimized_strategy=best_strategy,
            improvement_score=(best_score - baseline_score) / baseline_score,
            optimization_method=OptimizationMethod.REINFORCEMENT_LEARNING,
            iterations=iterations,
            convergence_achieved=convergence_achieved,
            optimization_time=0,
            backtested_performance=self._backtest_strategy(best_strategy, historical_data),
            recommendations=recommendations
        )
    
    def _ensemble_optimization(self,
                             strategy: InvestmentStrategy,
                             historical_data: Dict[str, pd.Series],
                             target_improvement: float) -> OptimizationResult:
        """Optimize strategy using ensemble of multiple methods."""
        original_strategy = deepcopy(strategy)
        
        # Run multiple optimization methods
        methods = [
            OptimizationMethod.GRADIENT_ASCENT,
            OptimizationMethod.GENETIC_ALGORITHM,
            OptimizationMethod.BAYESIAN_OPTIMIZATION
        ]
        
        results = []
        for method in methods:
            temp_optimizer = StrategyOptimizer(
                self.reward_calculator, method, self.learning_rate, self.max_iterations // 3
            )
            result = temp_optimizer.optimize_strategy(strategy, historical_data, target_improvement)
            results.append(result)
        
        # Select best result
        best_result = max(results, key=lambda r: r.improvement_score)
        
        # Combine recommendations
        all_recommendations = []
        for result in results:
            all_recommendations.extend(result.recommendations)
        
        # Remove duplicates and keep top recommendations
        unique_recommendations = list(set(all_recommendations))[:10]
        
        best_result.optimization_method = OptimizationMethod.ENSEMBLE_LEARNING
        best_result.recommendations = unique_recommendations
        best_result.iterations = sum(r.iterations for r in results)
        
        return best_result
    
    def _evaluate_strategy_performance(self,
                                     strategy: InvestmentStrategy,
                                     historical_data: Dict[str, pd.Series]) -> float:
        """
        Evaluate strategy performance using reward calculator.
        
        Args:
            strategy: Strategy to evaluate
            historical_data: Historical market data
            
        Returns:
            Performance score
        """
        try:
            # Simulate strategy performance (simplified)
            portfolio_returns = historical_data.get('portfolio_returns', pd.Series())
            benchmark_returns = historical_data.get('benchmark_returns', pd.Series())
            portfolio_value = historical_data.get('portfolio_value', pd.Series())
            positions_data = historical_data.get('positions_data', [])
            
            if len(portfolio_returns) == 0:
                # Generate mock returns based on strategy parameters
                portfolio_returns = self._simulate_strategy_returns(strategy, 252)  # 1 year
                benchmark_returns = pd.Series(np.random.normal(0.0008, 0.015, 252))
                portfolio_value = pd.Series(100 * (1 + portfolio_returns).cumprod())
                positions_data = []
            
            # Calculate reward score
            reward_score = self.reward_calculator.calculate_comprehensive_reward(
                portfolio_returns, benchmark_returns, portfolio_value, positions_data
            )
            
            return reward_score.weighted_score
            
        except Exception as e:
            logger.error(f"Error evaluating strategy performance: {e}")
            return 0.0
    
    def _simulate_strategy_returns(self, strategy: InvestmentStrategy, n_days: int) -> pd.Series:
        """Simulate returns based on strategy parameters."""
        # Extract key parameters
        risk_level = strategy.parameters.get('risk_level', StrategyParameter('risk_level', 0.5, 0, 1, 0.1, 'Risk level')).value
        return_target = strategy.parameters.get('return_target', StrategyParameter('return_target', 0.08, 0, 0.3, 0.01, 'Return target')).value
        
        # Simulate returns with strategy characteristics
        base_return = return_target / 252
        base_volatility = 0.01 + risk_level * 0.02
        
        returns = np.random.normal(base_return, base_volatility, n_days)
        
        # Add strategy-specific patterns
        if strategy.strategy_type == StrategyType.MOMENTUM:
            # Add momentum effects
            for i in range(1, len(returns)):
                momentum_factor = 0.1 * returns[i-1]
                returns[i] += momentum_factor
        elif strategy.strategy_type == StrategyType.MEAN_REVERSION:
            # Add mean reversion effects
            for i in range(1, len(returns)):
                reversion_factor = -0.05 * returns[i-1]
                returns[i] += reversion_factor
        
        return pd.Series(returns)
    
    def _calculate_parameter_gradient(self,
                                    strategy: InvestmentStrategy,
                                    param_name: str,
                                    historical_data: Dict[str, pd.Series],
                                    epsilon: float = 0.01) -> float:
        """Calculate gradient for a specific parameter."""
        param = strategy.parameters[param_name]
        original_value = param.value
        
        # Calculate finite difference gradient
        param.value = min(param.max_value, original_value + epsilon)
        score_plus = self._evaluate_strategy_performance(strategy, historical_data)
        
        param.value = max(param.min_value, original_value - epsilon)
        score_minus = self._evaluate_strategy_performance(strategy, historical_data)
        
        # Restore original value
        param.value = original_value
        
        gradient = (score_plus - score_minus) / (2 * epsilon)
        return gradient
    
    def _mutate_strategy(self, strategy: InvestmentStrategy, mutation_strength: float) -> InvestmentStrategy:
        """Mutate strategy parameters randomly."""
        mutated_strategy = deepcopy(strategy)
        
        for param in mutated_strategy.parameters.values():
            # Random mutation within bounds
            range_size = param.max_value - param.min_value
            mutation = np.random.normal(0, mutation_strength * range_size)
            param.value = max(param.min_value, min(param.max_value, param.value + mutation))
        
        return mutated_strategy
    
    def _genetic_selection_and_reproduction(self,
                                          population: List[InvestmentStrategy],
                                          fitness_scores: List[float],
                                          population_size: int,
                                          elite_ratio: float,
                                          crossover_rate: float,
                                          mutation_rate: float) -> List[InvestmentStrategy]:
        """Genetic algorithm selection and reproduction."""
        # Sort by fitness
        sorted_indices = sorted(range(len(fitness_scores)), key=lambda i: fitness_scores[i], reverse=True)
        
        new_population = []
        
        # Elite selection
        n_elite = int(population_size * elite_ratio)
        for i in range(n_elite):
            new_population.append(deepcopy(population[sorted_indices[i]]))
        
        # Reproduce to fill remaining population
        while len(new_population) < population_size:
            # Tournament selection
            parent1 = self._tournament_selection(population, fitness_scores)
            parent2 = self._tournament_selection(population, fitness_scores)
            
            # Crossover
            if np.random.random() < crossover_rate:
                child = self._crossover_strategies(parent1, parent2)
            else:
                child = deepcopy(parent1)
            
            # Mutation
            if np.random.random() < mutation_rate:
                child = self._mutate_strategy(child, 0.1)
            
            new_population.append(child)
        
        return new_population[:population_size]
    
    def _tournament_selection(self, population: List[InvestmentStrategy], fitness_scores: List[float]) -> InvestmentStrategy:
        """Tournament selection for genetic algorithm."""
        tournament_size = 3
        tournament_indices = np.random.choice(len(population), tournament_size, replace=False)
        winner_idx = max(tournament_indices, key=lambda i: fitness_scores[i])
        return population[winner_idx]
    
    def _crossover_strategies(self, parent1: InvestmentStrategy, parent2: InvestmentStrategy) -> InvestmentStrategy:
        """Crossover two strategies to create offspring."""
        child = deepcopy(parent1)
        
        for param_name in child.parameters.keys():
            if param_name in parent2.parameters:
                # Random blend crossover
                alpha = np.random.random()
                p1_value = parent1.parameters[param_name].value
                p2_value = parent2.parameters[param_name].value
                child.parameters[param_name].value = alpha * p1_value + (1 - alpha) * p2_value
        
        return child
    
    def _backtest_strategy(self, strategy: InvestmentStrategy, historical_data: Dict[str, pd.Series]) -> Dict[str, Any]:
        """Backtest strategy performance."""
        # Simplified backtesting
        returns = self._simulate_strategy_returns(strategy, 252)
        
        total_return = (1 + returns).prod() - 1
        volatility = returns.std() * np.sqrt(252)
        sharpe_ratio = (returns.mean() * 252 - 0.03) / volatility if volatility > 0 else 0
        max_drawdown = self._calculate_max_drawdown(returns)
        
        return {
            "total_return": total_return,
            "volatility": volatility,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "win_rate": len(returns[returns > 0]) / len(returns)
        }
    
    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """Calculate maximum drawdown."""
        cumulative = (1 + returns).cumprod()
        rolling_max = cumulative.expanding().max()
        drawdown = (cumulative - rolling_max) / rolling_max
        return abs(drawdown.min())
    
    def _generate_optimization_recommendations(self,
                                             original_strategy: InvestmentStrategy,
                                             optimized_strategy: InvestmentStrategy,
                                             improvement: float) -> List[str]:
        """Generate optimization recommendations."""
        recommendations = []
        
        # Parameter change recommendations
        for param_name, original_param in original_strategy.parameters.items():
            optimized_param = optimized_strategy.parameters[param_name]
            change = optimized_param.value - original_param.value
            
            if abs(change) > original_param.step_size:
                direction = "increased" if change > 0 else "decreased"
                change_pct = abs(change) / original_param.value * 100 if original_param.value != 0 else 0
                recommendations.append(
                    f"{param_name} should be {direction} by {change_pct:.1f}% "
                    f"(from {original_param.value:.3f} to {optimized_param.value:.3f})"
                )
        
        # Performance improvement recommendation
        if improvement > 0:
            recommendations.append(f"Overall strategy improvement: {improvement:.1%}")
        else:
            recommendations.append("Strategy shows limited improvement potential with current parameters")
        
        return recommendations
    
    def _create_failed_optimization_result(self, strategy: InvestmentStrategy, error_msg: str) -> OptimizationResult:
        """Create failed optimization result."""
        return OptimizationResult(
            original_strategy=strategy,
            optimized_strategy=strategy,
            improvement_score=0.0,
            optimization_method=self.optimization_method,
            iterations=0,
            convergence_achieved=False,
            optimization_time=0.0,
            backtested_performance={},
            recommendations=[f"Optimization failed: {error_msg}"]
        )
    
    def _initialize_strategy_templates(self) -> Dict[StrategyType, InvestmentStrategy]:
        """Initialize strategy templates for different types."""
        templates = {}
        
        # Growth Strategy Template
        growth_params = {
            "risk_level": StrategyParameter("risk_level", 0.7, 0.3, 1.0, 0.05, "Risk tolerance level"),
            "return_target": StrategyParameter("return_target", 0.15, 0.08, 0.30, 0.01, "Annual return target"),
            "growth_weight": StrategyParameter("growth_weight", 0.8, 0.5, 1.0, 0.05, "Weight towards growth stocks"),
            "momentum_factor": StrategyParameter("momentum_factor", 0.3, 0.0, 0.8, 0.05, "Momentum consideration"),
            "sector_concentration": StrategyParameter("sector_concentration", 0.4, 0.2, 0.8, 0.05, "Max sector concentration")
        }
        
        templates[StrategyType.GROWTH] = InvestmentStrategy(
            name="Growth Strategy",
            strategy_type=StrategyType.GROWTH,
            parameters=growth_params,
            allocation_rules={"max_position_size": 0.1, "cash_target": 0.05},
            risk_controls={"stop_loss": 0.15, "max_drawdown": 0.20}
        )
        
        # Value Strategy Template
        value_params = {
            "risk_level": StrategyParameter("risk_level", 0.5, 0.2, 0.8, 0.05, "Risk tolerance level"),
            "return_target": StrategyParameter("return_target", 0.10, 0.06, 0.20, 0.01, "Annual return target"),
            "value_weight": StrategyParameter("value_weight", 0.8, 0.5, 1.0, 0.05, "Weight towards value stocks"),
            "pe_threshold": StrategyParameter("pe_threshold", 15.0, 5.0, 25.0, 0.5, "Max P/E ratio"),
            "dividend_weight": StrategyParameter("dividend_weight", 0.4, 0.0, 0.8, 0.05, "Dividend stock preference")
        }
        
        templates[StrategyType.VALUE] = InvestmentStrategy(
            name="Value Strategy",
            strategy_type=StrategyType.VALUE,
            parameters=value_params,
            allocation_rules={"max_position_size": 0.08, "cash_target": 0.10},
            risk_controls={"stop_loss": 0.12, "max_drawdown": 0.15}
        )
        
        # Balanced Strategy Template
        balanced_params = {
            "risk_level": StrategyParameter("risk_level", 0.6, 0.3, 0.8, 0.05, "Risk tolerance level"),
            "return_target": StrategyParameter("return_target", 0.12, 0.07, 0.25, 0.01, "Annual return target"),
            "growth_value_balance": StrategyParameter("growth_value_balance", 0.5, 0.2, 0.8, 0.05, "Growth vs Value balance"),
            "international_weight": StrategyParameter("international_weight", 0.3, 0.1, 0.5, 0.05, "International allocation"),
            "bond_allocation": StrategyParameter("bond_allocation", 0.2, 0.0, 0.4, 0.05, "Bond allocation")
        }
        
        templates[StrategyType.BALANCED] = InvestmentStrategy(
            name="Balanced Strategy",
            strategy_type=StrategyType.BALANCED,
            parameters=balanced_params,
            allocation_rules={"max_position_size": 0.06, "cash_target": 0.08},
            risk_controls={"stop_loss": 0.10, "max_drawdown": 0.12}
        )
        
        return templates
    
    def get_strategy_template(self, strategy_type: StrategyType) -> InvestmentStrategy:
        """Get a strategy template for the given type."""
        return deepcopy(self.strategy_templates.get(strategy_type, self.strategy_templates[StrategyType.BALANCED]))
    
    def suggest_strategy_improvements(self, 
                                    strategy: InvestmentStrategy,
                                    recent_performance: Dict[str, Any]) -> List[str]:
        """Suggest specific improvements based on recent performance."""
        suggestions = []
        
        # Analyze performance metrics
        sharpe_ratio = recent_performance.get('sharpe_ratio', 0)
        max_drawdown = recent_performance.get('max_drawdown', 0)
        volatility = recent_performance.get('volatility', 0)
        win_rate = recent_performance.get('win_rate', 0.5)
        
        # Risk-based suggestions
        if max_drawdown > 0.15:
            suggestions.append("Reduce risk level parameter to control drawdowns")
            suggestions.append("Implement tighter stop-loss controls")
        
        if volatility > 0.25:
            suggestions.append("Lower portfolio volatility through better diversification")
            suggestions.append("Reduce position concentration in high-volatility stocks")
        
        # Return-based suggestions
        if sharpe_ratio < 1.0:
            suggestions.append("Improve riOPENAI_API_KEY_REDACTED returns by optimizing position sizing")
            suggestions.append("Consider adjusting return target vs risk level balance")
        
        if win_rate < 0.45:
            suggestions.append("Improve trade timing and entry/exit criteria")
            suggestions.append("Consider mean reversion strategies if momentum isn't working")
        
        # Strategy-specific suggestions
        if strategy.strategy_type == StrategyType.GROWTH and sharpe_ratio < 1.2:
            suggestions.append("Focus on higher quality growth stocks with better fundamentals")
        elif strategy.strategy_type == StrategyType.VALUE and win_rate < 0.5:
            suggestions.append("Improve value stock screening criteria")
        
        return suggestions[:5]  # Return top 5 suggestions


# Global strategy optimizer instance
_strategy_optimizer = None

def get_strategy_optimizer() -> StrategyOptimizer:
    """Get the global strategy optimizer instance."""
    global _strategy_optimizer
    if _strategy_optimizer is None:
        _strategy_optimizer = StrategyOptimizer()
    return _strategy_optimizer