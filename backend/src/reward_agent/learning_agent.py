"""
Reward Learning Agent

This module implements the main learning agent that coordinates reward calculation,
strategy optimization, and adaptive learning to continuously improve investment performance.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
import asyncio
from copy import deepcopy
import json

from .reward_calculator import RewardCalculator, RewardScore
from .strategy_optimizer import StrategyOptimizer, InvestmentStrategy, OptimizationResult, StrategyType
from .performance_tracker import PerformanceTracker

logger = logging.getLogger(__name__)


class LearningMode(Enum):
    """Learning modes for the agent."""
    CONSERVATIVE = "conservative"  # Small, safe adjustments
    BALANCED = "balanced"         # Moderate learning rate
    AGGRESSIVE = "aggressive"     # Fast adaptation, higher risk


class ActionType(Enum):
    """Types of actions the learning agent can take."""
    OPTIMIZE_STRATEGY = "optimize_strategy"
    ADJUST_PARAMETERS = "adjust_parameters" 
    REBALANCE_PORTFOLIO = "rebalance_portfolio"
    CHANGE_STRATEGY_TYPE = "change_strategy_type"
    UPDATE_RISK_CONTROLS = "update_risk_controls"
    NO_ACTION = "no_action"


@dataclass
class LearningAction:
    """Action taken by the learning agent."""
    action_type: ActionType
    parameters: Dict[str, Any]
    expected_improvement: float
    confidence: float
    timestamp: datetime
    reasoning: str


@dataclass
class LearningState:
    """Current state of the learning agent."""
    current_strategy: InvestmentStrategy
    recent_performance: Dict[str, Any]
    reward_history: List[RewardScore]
    action_history: List[LearningAction]
    learning_progress: Dict[str, float]
    last_optimization: Optional[datetime] = None
    total_improvements: float = 0.0
    success_rate: float = 0.0


class RewardLearningAgent:
    """
    Main learning agent that uses rewards to continuously adapt and improve
    investment strategies through reinforcement learning principles.
    """
    
    def __init__(self,
                 reward_calculator: Optional[RewardCalculator] = None,
                 strategy_optimizer: Optional[StrategyOptimizer] = None,
                 performance_tracker: Optional[PerformanceTracker] = None,
                 learning_mode: LearningMode = LearningMode.BALANCED,
                 min_improvement_threshold: float = 0.02,
                 optimization_frequency_days: int = 7):
        """
        Initialize the reward learning agent.
        
        Args:
            reward_calculator: Reward calculation system
            strategy_optimizer: Strategy optimization engine
            performance_tracker: Performance tracking system
            learning_mode: Learning aggressiveness
            min_improvement_threshold: Minimum improvement to trigger optimization
            optimization_frequency_days: Days between optimization attempts
        """
        self.reward_calculator = reward_calculator or RewardCalculator()
        self.strategy_optimizer = strategy_optimizer or StrategyOptimizer()
        self.performance_tracker = performance_tracker or PerformanceTracker()
        
        self.learning_mode = learning_mode
        self.min_improvement_threshold = min_improvement_threshold
        self.optimization_frequency_days = optimization_frequency_days
        
        # Learning parameters based on mode
        self._set_learning_parameters()
        
        # Current learning state
        self.learning_state = LearningState(
            current_strategy=self.strategy_optimizer.get_strategy_template(StrategyType.BALANCED),
            recent_performance={},
            reward_history=[],
            action_history=[],
            learning_progress={}
        )
        
        # Learning metrics
        self.exploration_rate = 0.2
        self.exploitation_rate = 0.8
        self.memory_window = 30  # Days to remember for learning
        
    def _set_learning_parameters(self):
        """Set learning parameters based on learning mode."""
        if self.learning_mode == LearningMode.CONSERVATIVE:
            self.learning_rate = 0.005
            self.exploration_rate = 0.1
            self.risk_tolerance = 0.05
        elif self.learning_mode == LearningMode.BALANCED:
            self.learning_rate = 0.01
            self.exploration_rate = 0.2
            self.risk_tolerance = 0.1
        else:  # AGGRESSIVE
            self.learning_rate = 0.02
            self.exploration_rate = 0.3
            self.risk_tolerance = 0.15
    
    async def learn_and_adapt(self,
                            portfolio_data: Dict[str, Any],
                            market_data: Dict[str, pd.Series],
                            force_optimization: bool = False) -> LearningAction:
        """
        Main learning loop: analyze performance, calculate rewards, and adapt strategy.
        
        Args:
            portfolio_data: Current portfolio information
            market_data: Market data for analysis
            force_optimization: Force optimization regardless of timing
            
        Returns:
            LearningAction: Action taken by the agent
        """
        try:
            logger.info("Starting learning and adaptation cycle")
            
            # 1. Calculate current rewards
            reward_score = await self._calculate_current_rewards(portfolio_data, market_data)
            self.learning_state.reward_history.append(reward_score)
            
            # 2. Update performance tracking
            self.performance_tracker.update_performance(portfolio_data, reward_score)
            
            # 3. Analyze learning progress
            learning_insights = self._analyze_learning_progress()
            
            # 4. Decide on action
            action = await self._decide_learning_action(
                reward_score, learning_insights, force_optimization
            )
            
            # 5. Execute action
            await self._execute_learning_action(action, portfolio_data, market_data)
            
            # 6. Update learning state
            self._update_learning_state(action, reward_score)
            
            logger.info(f"Learning cycle completed: {action.action_type.value}")
            return action
            
        except Exception as e:
            logger.error(f"Error in learning cycle: {e}")
            return LearningAction(
                action_type=ActionType.NO_ACTION,
                parameters={},
                expected_improvement=0.0,
                confidence=0.0,
                timestamp=datetime.now(),
                reasoning=f"Error in learning: {str(e)}"
            )
    
    async def _calculate_current_rewards(self,
                                       portfolio_data: Dict[str, Any],
                                       market_data: Dict[str, pd.Series]) -> RewardScore:
        """Calculate current portfolio rewards."""
        # Extract data for reward calculation
        portfolio_returns = market_data.get('portfolio_returns', pd.Series())
        benchmark_returns = market_data.get('benchmark_returns', pd.Series())
        portfolio_value = market_data.get('portfolio_value', pd.Series())
        positions_data = portfolio_data.get('positions', [])
        
        # If no real data, simulate for demonstration
        if len(portfolio_returns) == 0:
            portfolio_returns = self._generate_mock_returns(self.learning_state.current_strategy)
            benchmark_returns = pd.Series(np.random.normal(0.0008, 0.015, len(portfolio_returns)))
            portfolio_value = pd.Series(100000 * (1 + portfolio_returns).cumprod())
        
        reward_score = self.reward_calculator.calculate_comprehensive_reward(
            portfolio_returns=portfolio_returns,
            benchmark_returns=benchmark_returns,
            portfolio_value=portfolio_value,
            positions_data=positions_data,
            period_days=30
        )
        
        return reward_score
    
    def _analyze_learning_progress(self) -> Dict[str, Any]:
        """Analyze recent learning progress and identify trends."""
        insights = {
            "trend": "stable",
            "improvement_rate": 0.0,
            "consistency": 0.5,
            "areas_for_improvement": [],
            "successful_patterns": []
        }
        
        if len(self.learning_state.reward_history) < 3:
            return insights
        
        # Analyze reward trend
        recent_scores = [score.weighted_score for score in self.learning_state.reward_history[-10:]]
        if len(recent_scores) >= 3:
            trend_slope = np.polyfit(range(len(recent_scores)), recent_scores, 1)[0]
            
            if trend_slope > 1:
                insights["trend"] = "improving"
            elif trend_slope < -1:
                insights["trend"] = "declining"
            
            insights["improvement_rate"] = trend_slope
        
        # Analyze consistency
        if len(recent_scores) >= 5:
            insights["consistency"] = 1.0 - (np.std(recent_scores) / np.mean(recent_scores))
        
        # Identify areas for improvement from recent rewards
        latest_reward = self.learning_state.reward_history[-1]
        for metric_name, metric in latest_reward.individual_metrics.items():
            if metric.value < 50:  # Below average performance
                insights["areas_for_improvement"].append({
                    "area": metric_name,
                    "score": metric.value,
                    "suggestions": metric.improvement_suggestions
                })
        
        # Identify successful patterns from action history
        successful_actions = [
            action for action in self.learning_state.action_history[-10:]
            if action.expected_improvement > 0
        ]
        
        if successful_actions:
            action_types = [action.action_type.value for action in successful_actions]
            most_successful = max(set(action_types), key=action_types.count)
            insights["successful_patterns"].append(f"Most successful action: {most_successful}")
        
        return insights
    
    async def _decide_learning_action(self,
                                    current_reward: RewardScore,
                                    learning_insights: Dict[str, Any],
                                    force_optimization: bool) -> LearningAction:
        """Decide what learning action to take based on current state."""
        
        # Check if optimization is due
        should_optimize = force_optimization
        if not should_optimize and self.learning_state.last_optimization:
            days_since_optimization = (datetime.now() - self.learning_state.last_optimization).days
            should_optimize = days_since_optimization >= self.optimization_frequency_days
        
        # Check if performance is poor enough to trigger optimization
        if not should_optimize and current_reward.weighted_score < 40:
            should_optimize = True
        
        # Decide action type based on analysis
        if should_optimize:
            return await self._plan_optimization_action(current_reward, learning_insights)
        elif learning_insights["trend"] == "declining":
            return await self._plan_adjustment_action(current_reward, learning_insights)
        elif len(learning_insights["areas_for_improvement"]) > 3:
            return await self._plan_parameter_tuning_action(current_reward, learning_insights)
        else:
            return self._plan_maintenance_action(current_reward, learning_insights)
    
    async def _plan_optimization_action(self,
                                      reward_score: RewardScore,
                                      insights: Dict[str, Any]) -> LearningAction:
        """Plan a full strategy optimization action."""
        
        # Determine optimization aggressiveness based on performance
        if reward_score.weighted_score < 30:
            target_improvement = 0.3  # Aggressive improvement needed
            confidence = 0.9
        elif reward_score.weighted_score < 50:
            target_improvement = 0.2
            confidence = 0.7
        else:
            target_improvement = 0.1
            confidence = 0.5
        
        return LearningAction(
            action_type=ActionType.OPTIMIZE_STRATEGY,
            parameters={
                "target_improvement": target_improvement,
                "optimization_method": "ensemble" if reward_score.weighted_score < 40 else "gradient_ascent",
                "max_iterations": 100 if self.learning_mode == LearningMode.AGGRESSIVE else 50
            },
            expected_improvement=target_improvement,
            confidence=confidence,
            timestamp=datetime.now(),
            reasoning=f"Performance score {reward_score.weighted_score:.1f} requires optimization. "
                     f"Trend: {insights['trend']}, Areas needing improvement: {len(insights['areas_for_improvement'])}"
        )
    
    async def _plan_adjustment_action(self,
                                    reward_score: RewardScore,
                                    insights: Dict[str, Any]) -> LearningAction:
        """Plan parameter adjustment action for declining performance."""
        
        # Identify worst performing metric
        worst_metric = min(
            reward_score.individual_metrics.items(),
            key=lambda x: x[1].value
        )
        
        adjustments = {}
        
        # Suggest specific parameter adjustments based on worst metric
        if "risk" in worst_metric[0].lower():
            adjustments["risk_level"] = -0.1  # Reduce risk
        elif "return" in worst_metric[0].lower():
            adjustments["return_target"] = 0.02  # Increase return target slightly
        elif "diversification" in worst_metric[0].lower():
            adjustments["max_position_size"] = -0.01  # Reduce position concentration
        
        return LearningAction(
            action_type=ActionType.ADJUST_PARAMETERS,
            parameters={"adjustments": adjustments, "metric_focus": worst_metric[0]},
            expected_improvement=0.05,
            confidence=0.6,
            timestamp=datetime.now(),
            reasoning=f"Declining trend detected. Adjusting parameters to improve {worst_metric[0]} "
                     f"(current score: {worst_metric[1].value:.1f})"
        )
    
    async def _plan_parameter_tuning_action(self,
                                          reward_score: RewardScore,
                                          insights: Dict[str, Any]) -> LearningAction:
        """Plan fine-tuning action for specific areas."""
        
        # Focus on the area with lowest score
        priority_area = min(
            insights["areas_for_improvement"],
            key=lambda x: x["score"]
        )
        
        tuning_params = {
            "focus_area": priority_area["area"],
            "suggestions": priority_area["suggestions"],
            "adjustment_magnitude": 0.05 if self.learning_mode == LearningMode.CONSERVATIVE else 0.1
        }
        
        return LearningAction(
            action_type=ActionType.ADJUST_PARAMETERS,
            parameters=tuning_params,
            expected_improvement=0.03,
            confidence=0.7,
            timestamp=datetime.now(),
            reasoning=f"Fine-tuning strategy to improve {priority_area['area']} "
                     f"(score: {priority_area['score']:.1f})"
        )
    
    def _plan_maintenance_action(self,
                               reward_score: RewardScore,
                               insights: Dict[str, Any]) -> LearningAction:
        """Plan maintenance action when performance is acceptable."""
        
        return LearningAction(
            action_type=ActionType.NO_ACTION,
            parameters={"monitoring": True},
            expected_improvement=0.0,
            confidence=0.8,
            timestamp=datetime.now(),
            reasoning=f"Performance is stable (score: {reward_score.weighted_score:.1f}). "
                     f"Continuing monitoring with current strategy."
        )
    
    async def _execute_learning_action(self,
                                     action: LearningAction,
                                     portfolio_data: Dict[str, Any],
                                     market_data: Dict[str, pd.Series]):
        """Execute the planned learning action."""
        
        try:
            if action.action_type == ActionType.OPTIMIZE_STRATEGY:
                await self._execute_strategy_optimization(action, market_data)
            
            elif action.action_type == ActionType.ADJUST_PARAMETERS:
                await self._execute_parameter_adjustment(action)
            
            elif action.action_type == ActionType.REBALANCE_PORTFOLIO:
                await self._execute_portfolio_rebalancing(action, portfolio_data)
            
            elif action.action_type == ActionType.UPDATE_RISK_CONTROLS:
                await self._execute_risk_control_update(action)
            
            # NO_ACTION requires no execution
            
        except Exception as e:
            logger.error(f"Error executing action {action.action_type}: {e}")
            action.reasoning += f" | Execution error: {str(e)}"
    
    async def _execute_strategy_optimization(self,
                                           action: LearningAction,
                                           market_data: Dict[str, pd.Series]):
        """Execute full strategy optimization."""
        
        target_improvement = action.parameters.get("target_improvement", 0.1)
        optimization_method = action.parameters.get("optimization_method", "gradient_ascent")
        
        # Set optimization method
        from .strategy_optimizer import OptimizationMethod
        method_map = {
            "gradient_ascent": OptimizationMethod.GRADIENT_ASCENT,
            "genetic_algorithm": OptimizationMethod.GENETIC_ALGORITHM,
            "bayesian_optimization": OptimizationMethod.BAYESIAN_OPTIMIZATION,
            "ensemble": OptimizationMethod.ENSEMBLE_LEARNING
        }
        
        self.strategy_optimizer.optimization_method = method_map.get(
            optimization_method, OptimizationMethod.GRADIENT_ASCENT
        )
        
        # Run optimization
        optimization_result = self.strategy_optimizer.optimize_strategy(
            self.learning_state.current_strategy,
            market_data,
            target_improvement
        )
        
        # Update strategy if improvement achieved
        if optimization_result.improvement_score > 0:
            self.learning_state.current_strategy = optimization_result.optimized_strategy
            self.learning_state.last_optimization = datetime.now()
            self.learning_state.total_improvements += optimization_result.improvement_score
            
            logger.info(f"Strategy optimized with {optimization_result.improvement_score:.2%} improvement")
        
        # Update action with actual results
        action.expected_improvement = optimization_result.improvement_score
        action.reasoning += f" | Actual improvement: {optimization_result.improvement_score:.2%}"
    
    async def _execute_parameter_adjustment(self, action: LearningAction):
        """Execute parameter adjustments."""
        
        adjustments = action.parameters.get("adjustments", {})
        
        for param_name, adjustment in adjustments.items():
            if param_name in self.learning_state.current_strategy.parameters:
                param = self.learning_state.current_strategy.parameters[param_name]
                old_value = param.value
                new_value = max(param.min_value, min(param.max_value, old_value + adjustment))
                param.value = new_value
                
                logger.info(f"Adjusted {param_name} from {old_value:.3f} to {new_value:.3f}")
    
    async def _execute_portfolio_rebalancing(self,
                                           action: LearningAction,
                                           portfolio_data: Dict[str, Any]):
        """Execute portfolio rebalancing based on strategy."""
        # This would integrate with portfolio manager for actual rebalancing
        logger.info("Portfolio rebalancing executed based on strategy adjustments")
    
    async def _execute_risk_control_update(self, action: LearningAction):
        """Execute risk control updates."""
        risk_updates = action.parameters.get("risk_controls", {})
        
        current_controls = self.learning_state.current_strategy.risk_controls
        current_controls.update(risk_updates)
        
        logger.info(f"Risk controls updated: {risk_updates}")
    
    def _update_learning_state(self, action: LearningAction, reward_score: RewardScore):
        """Update the learning state after action execution."""
        
        # Add action to history
        self.learning_state.action_history.append(action)
        
        # Update success rate
        if len(self.learning_state.action_history) > 1:
            successful_actions = sum(
                1 for a in self.learning_state.action_history
                if a.expected_improvement > 0
            )
            self.learning_state.success_rate = successful_actions / len(self.learning_state.action_history)
        
        # Update learning progress
        self.learning_state.learning_progress = {
            "total_actions": len(self.learning_state.action_history),
            "successful_optimizations": sum(
                1 for a in self.learning_state.action_history
                if a.action_type == ActionType.OPTIMIZE_STRATEGY and a.expected_improvement > 0
            ),
            "average_improvement": self.learning_state.total_improvements / max(1, len(self.learning_state.action_history)),
            "current_performance": reward_score.weighted_score,
            "performance_grade": reward_score.performance_grade
        }
        
        # Keep only recent history to prevent memory bloat
        max_history = 100
        if len(self.learning_state.reward_history) > max_history:
            self.learning_state.reward_history = self.learning_state.reward_history[-max_history:]
        if len(self.learning_state.action_history) > max_history:
            self.learning_state.action_history = self.learning_state.action_history[-max_history:]
    
    def _generate_mock_returns(self, strategy: InvestmentStrategy, n_days: int = 30) -> pd.Series:
        """Generate mock returns based on current strategy."""
        risk_level = strategy.parameters.get('risk_level', type('param', (), {'value': 0.5})()).value
        return_target = strategy.parameters.get('return_target', type('param', (), {'value': 0.08})()).value
        
        daily_return = return_target / 252
        daily_volatility = 0.01 + risk_level * 0.02
        
        returns = np.random.normal(daily_return, daily_volatility, n_days)
        return pd.Series(returns, index=pd.date_range(start=datetime.now() - timedelta(days=n_days), periods=n_days))
    
    def get_learning_insights(self) -> Dict[str, Any]:
        """Get current learning insights and progress."""
        
        recent_performance = {}
        if self.learning_state.reward_history:
            latest_reward = self.learning_state.reward_history[-1]
            recent_performance = {
                "overall_score": latest_reward.weighted_score,
                "performance_grade": latest_reward.performance_grade,
                "benchmark_comparison": latest_reward.benchmark_comparison,
                "individual_metrics": {
                    name: {
                        "score": metric.value,
                        "max_score": metric.max_value,
                        "suggestions": metric.improvement_suggestions
                    }
                    for name, metric in latest_reward.individual_metrics.items()
                }
            }
        
        return {
            "learning_mode": self.learning_mode.value,
            "current_strategy": {
                "name": self.learning_state.current_strategy.name,
                "type": self.learning_state.current_strategy.strategy_type.value,
                "confidence": self.learning_state.current_strategy.confidence_score,
                "version": self.learning_state.current_strategy.version
            },
            "learning_progress": self.learning_state.learning_progress,
            "recent_performance": recent_performance,
            "success_rate": self.learning_state.success_rate,
            "total_improvements": self.learning_state.total_improvements,
            "last_optimization": self.learning_state.last_optimization.isoformat() if self.learning_state.last_optimization else None,
            "recent_actions": [
                {
                    "type": action.action_type.value,
                    "improvement": action.expected_improvement,
                    "confidence": action.confidence,
                    "timestamp": action.timestamp.isoformat(),
                    "reasoning": action.reasoning
                }
                for action in self.learning_state.action_history[-5:]
            ]
        }
    
    def get_strategy_recommendations(self) -> List[Dict[str, Any]]:
        """Get current strategy recommendations."""
        
        recommendations = []
        
        if not self.learning_state.reward_history:
            return [{"type": "info", "message": "Insufficient data for recommendations"}]
        
        latest_reward = self.learning_state.reward_history[-1]
        
        # Performance-based recommendations
        if latest_reward.weighted_score < 50:
            recommendations.append({
                "type": "urgent",
                "category": "performance",
                "message": "Strategy performance is below average - optimization recommended",
                "action": "Consider running full strategy optimization"
            })
        
        # Individual metric recommendations
        for metric_name, metric in latest_reward.individual_metrics.items():
            if metric.value < 40:
                recommendations.append({
                    "type": "improvement",
                    "category": metric_name.lower().replace(" ", "_"),
                    "message": f"{metric_name} needs attention (score: {metric.value:.1f})",
                    "action": "; ".join(metric.improvement_suggestions[:2])
                })
        
        # Learning progress recommendations
        if self.learning_state.success_rate < 0.5:
            recommendations.append({
                "type": "learning",
                "category": "adaptation",
                "message": "Learning success rate is low - consider adjusting learning mode",
                "action": "Switch to more conservative learning approach"
            })
        
        return recommendations[:10]  # Limit to top 10 recommendations
    
    async def set_learning_mode(self, mode: LearningMode):
        """Update learning mode and parameters."""
        self.learning_mode = mode
        self._set_learning_parameters()
        logger.info(f"Learning mode updated to: {mode.value}")
    
    async def force_strategy_optimization(self,
                                        portfolio_data: Dict[str, Any],
                                        market_data: Dict[str, pd.Series]) -> OptimizationResult:
        """Force immediate strategy optimization."""
        
        optimization_result = self.strategy_optimizer.optimize_strategy(
            self.learning_state.current_strategy,
            market_data,
            target_improvement=0.1
        )
        
        if optimization_result.improvement_score > 0:
            self.learning_state.current_strategy = optimization_result.optimized_strategy
            self.learning_state.last_optimization = datetime.now()
            self.learning_state.total_improvements += optimization_result.improvement_score
        
        return optimization_result


# Global learning agent instance
_learning_agent = None

def get_learning_agent() -> RewardLearningAgent:
    """Get the global learning agent instance."""
    global _learning_agent
    if _learning_agent is None:
        _learning_agent = RewardLearningAgent()
    return _learning_agent