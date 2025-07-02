"""
Reward Calculator

This module calculates rewards based on portfolio performance metrics.
Rewards are used to reinforce successful investment strategies and penalize poor ones.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RewardType(Enum):
    """Types of rewards in the system."""
    RETURN_BASED = "return_based"
    RISK_ADJUSTED = "risk_adjusted"
    CONSISTENCY = "consistency"
    TIMING = "timing"
    DIVERSIFICATION = "diversification"
    ALPHA_GENERATION = "alpha_generation"
    DRAWDOWN_CONTROL = "drawdown_control"
    VOLATILITY_MANAGEMENT = "volatility_management"


@dataclass
class RewardMetric:
    """Individual reward metric."""
    name: str
    value: float
    weight: float
    max_value: float
    description: str
    improvement_suggestions: List[str]


@dataclass
class RewardScore:
    """Complete reward score with breakdown."""
    total_score: float
    weighted_score: float
    individual_metrics: Dict[str, RewardMetric]
    performance_grade: str
    timestamp: datetime
    period_days: int
    benchmark_comparison: float


class RewardCalculator:
    """
    Calculates sophisticated rewards based on portfolio performance.
    
    The reward system considers multiple dimensions:
    1. Absolute returns
    2. RiOPENAI_API_KEY_REDACTED returns (Sharpe, Sortino)
    3. Consistency and volatility
    4. Alpha generation vs benchmark
    5. Diversification effectiveness
    6. Drawdown control
    7. Market timing quality
    """
    
    def __init__(self, 
                 benchmark_symbol: str = "SPY",
                 risk_free_rate: float = 0.03,
                 reward_weights: Optional[Dict[str, float]] = None):
        """
        Initialize the reward calculator.
        
        Args:
            benchmark_symbol: Market benchmark for comparison
            risk_free_rate: Risk-free rate for Sharpe calculation
            reward_weights: Custom weights for different reward types
        """
        self.benchmark_symbol = benchmark_symbol
        self.risk_free_rate = risk_free_rate
        
        # Default reward weights (should sum to 1.0)
        self.reward_weights = reward_weights or {
            RewardType.RETURN_BASED.value: 0.25,
            RewardType.RISK_ADJUSTED.value: 0.20,
            RewardType.CONSISTENCY.value: 0.15,
            RewardType.ALPHA_GENERATION.value: 0.15,
            RewardType.DIVERSIFICATION.value: 0.10,
            RewardType.DRAWDOWN_CONTROL.value: 0.10,
            RewardType.VOLATILITY_MANAGEMENT.value: 0.05
        }
        
        # Reward scaling parameters
        self.max_reward_per_metric = 100.0
        self.penalty_multiplier = 1.5  # Penalties are stronger than rewards
    
    def calculate_comprehensive_reward(self,
                                     portfolio_returns: pd.Series,
                                     benchmark_returns: pd.Series,
                                     portfolio_value: pd.Series,
                                     positions_data: List[Dict[str, Any]],
                                     period_days: int = 90) -> RewardScore:
        """
        Calculate comprehensive reward score based on multiple performance metrics.
        
        Args:
            portfolio_returns: Daily portfolio returns
            benchmark_returns: Daily benchmark returns
            portfolio_value: Portfolio value over time
            positions_data: Current portfolio positions
            period_days: Evaluation period in days
        
        Returns:
            RewardScore: Comprehensive reward breakdown
        """
        try:
            # Calculate individual reward metrics
            metrics = {}
            
            # 1. Return-based rewards
            metrics[RewardType.RETURN_BASED.value] = self._calculate_return_rewards(
                portfolio_returns, period_days
            )
            
            # 2. RiOPENAI_API_KEY_REDACTED rewards
            metrics[RewardType.RISK_ADJUSTED.value] = self._calculate_risk_adjusted_rewards(
                portfolio_returns, benchmark_returns
            )
            
            # 3. Consistency rewards
            metrics[RewardType.CONSISTENCY.value] = self._calculate_consistency_rewards(
                portfolio_returns
            )
            
            # 4. Alpha generation rewards
            metrics[RewardType.ALPHA_GENERATION.value] = self._calculate_alpha_rewards(
                portfolio_returns, benchmark_returns
            )
            
            # 5. Diversification rewards
            metrics[RewardType.DIVERSIFICATION.value] = self._calculate_diversification_rewards(
                positions_data
            )
            
            # 6. Drawdown control rewards
            metrics[RewardType.DRAWDOWN_CONTROL.value] = self._calculate_drawdown_rewards(
                portfolio_value
            )
            
            # 7. Volatility management rewards
            metrics[RewardType.VOLATILITY_MANAGEMENT.value] = self._calculate_volatility_rewards(
                portfolio_returns, benchmark_returns
            )
            
            # Calculate weighted total score
            total_score = sum(metric.value for metric in metrics.values())
            weighted_score = sum(
                metric.value * self.reward_weights.get(metric_type, 0)
                for metric_type, metric in metrics.items()
            )
            
            # Calculate benchmark comparison
            portfolio_total_return = (1 + portfolio_returns).prod() - 1
            benchmark_total_return = (1 + benchmark_returns).prod() - 1
            benchmark_comparison = portfolio_total_return - benchmark_total_return
            
            # Determine performance grade
            performance_grade = self._calculate_performance_grade(weighted_score)
            
            return RewardScore(
                total_score=total_score,
                weighted_score=weighted_score,
                individual_metrics=metrics,
                performance_grade=performance_grade,
                timestamp=datetime.now(),
                period_days=period_days,
                benchmark_comparison=benchmark_comparison
            )
            
        except Exception as e:
            logger.error(f"Error calculating comprehensive reward: {e}")
            # Return minimal reward score on error
            return self._create_error_reward_score(period_days)
    
    def _calculate_return_rewards(self, 
                                returns: pd.Series, 
                                period_days: int) -> RewardMetric:
        """Calculate rewards based on absolute returns."""
        if len(returns) == 0:
            return RewardMetric("Return Performance", 0, 0.25, 100, "No data", [])
        
        # Annualized return
        total_return = (1 + returns).prod() - 1
        annualized_return = (1 + total_return) ** (252 / len(returns)) - 1
        
        # Reward calculation: positive returns get rewards, negative get penalties
        if annualized_return > 0:
            # Reward scale: 0-15% annual return = 0-100 points
            reward_value = min(annualized_return / 0.15 * self.max_reward_per_metric, 
                             self.max_reward_per_metric)
        else:
            # Penalty for negative returns
            reward_value = max(annualized_return / 0.05 * self.max_reward_per_metric * self.penalty_multiplier,
                             -self.max_reward_per_metric)
        
        suggestions = []
        if annualized_return < 0.05:
            suggestions.append("Consider more growth-oriented positions")
        if annualized_return < 0:
            suggestions.append("Review and exit underperforming positions")
            suggestions.append("Implement better risk management")
        
        return RewardMetric(
            name="Return Performance",
            value=reward_value,
            weight=self.reward_weights[RewardType.RETURN_BASED.value],
            max_value=self.max_reward_per_metric,
            description=f"Annualized return: {annualized_return:.2%}",
            improvement_suggestions=suggestions
        )
    
    def _calculate_risk_adjusted_rewards(self,
                                       portfolio_returns: pd.Series,
                                       benchmark_returns: pd.Series) -> RewardMetric:
        """Calculate rewards based on riOPENAI_API_KEY_REDACTED performance."""
        if len(portfolio_returns) < 30:
            return RewardMetric("RiOPENAI_API_KEY_REDACTED Performance", 0, 0.20, 100, "Insufficient data", [])
        
        # Calculate Sharpe ratio
        excess_returns = portfolio_returns.mean() * 252 - self.risk_free_rate
        volatility = portfolio_returns.std() * np.sqrt(252)
        sharpe_ratio = excess_returns / volatility if volatility > 0 else 0
        
        # Calculate Sortino ratio
        downside_returns = portfolio_returns[portfolio_returns < 0]
        downside_deviation = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0.001
        sortino_ratio = excess_returns / downside_deviation
        
        # Reward based on Sharpe ratio (1.0 = good, 2.0 = excellent)
        sharpe_reward = min(sharpe_ratio / 2.0 * self.max_reward_per_metric, self.max_reward_per_metric)
        sortino_reward = min(sortino_ratio / 2.5 * self.max_reward_per_metric, self.max_reward_per_metric)
        
        # Average the two riOPENAI_API_KEY_REDACTED metrics
        reward_value = (sharpe_reward + sortino_reward) / 2
        
        suggestions = []
        if sharpe_ratio < 1.0:
            suggestions.append("Improve return-to-risk ratio")
            suggestions.append("Consider reducing portfolio volatility")
        if sortino_ratio < 1.5:
            suggestions.append("Focus on reducing downside risk")
        
        return RewardMetric(
            name="RiOPENAI_API_KEY_REDACTED Performance",
            value=reward_value,
            weight=self.reward_weights[RewardType.RISK_ADJUSTED.value],
            max_value=self.max_reward_per_metric,
            description=f"Sharpe: {sharpe_ratio:.2f}, Sortino: {sortino_ratio:.2f}",
            improvement_suggestions=suggestions
        )
    
    def _calculate_consistency_rewards(self, returns: pd.Series) -> RewardMetric:
        """Calculate rewards based on return consistency."""
        if len(returns) == 0:
            return RewardMetric("Consistency", 0, 0.15, 100, "No data", [])
        
        # Consistency metrics
        positive_days_ratio = len(returns[returns > 0]) / len(returns)
        rolling_volatility = returns.rolling(window=20).std().mean() * np.sqrt(252)
        
        # Reward for high percentage of positive days (60%+ is good)
        consistency_reward = min(positive_days_ratio / 0.6 * self.max_reward_per_metric, 
                               self.max_reward_per_metric)
        
        # Penalty for high volatility (>25% annual volatility gets penalty)
        if rolling_volatility > 0.25:
            volatility_penalty = (rolling_volatility - 0.25) / 0.25 * 20
            consistency_reward -= volatility_penalty
        
        reward_value = max(consistency_reward, 0)
        
        suggestions = []
        if positive_days_ratio < 0.5:
            suggestions.append("Improve win rate through better timing")
        if rolling_volatility > 0.3:
            suggestions.append("Reduce portfolio volatility")
            suggestions.append("Consider more defensive positions")
        
        return RewardMetric(
            name="Consistency",
            value=reward_value,
            weight=self.reward_weights[RewardType.CONSISTENCY.value],
            max_value=self.max_reward_per_metric,
            description=f"Win rate: {positive_days_ratio:.1%}, Volatility: {rolling_volatility:.1%}",
            improvement_suggestions=suggestions
        )
    
    def _calculate_alpha_rewards(self,
                               portfolio_returns: pd.Series,
                               benchmark_returns: pd.Series) -> RewardMetric:
        """Calculate rewards based on alpha generation vs benchmark."""
        if len(portfolio_returns) != len(benchmark_returns) or len(portfolio_returns) < 30:
            return RewardMetric("Alpha Generation", 0, 0.15, 100, "Insufficient data", [])
        
        # Calculate alpha using simple regression
        try:
            portfolio_excess = portfolio_returns.mean() * 252 - self.risk_free_rate
            benchmark_excess = benchmark_returns.mean() * 252 - self.risk_free_rate
            
            # Beta calculation
            covariance = np.cov(portfolio_returns, benchmark_returns)[0][1]
            benchmark_variance = benchmark_returns.var()
            beta = covariance / benchmark_variance if benchmark_variance > 0 else 1.0
            
            # Alpha calculation
            alpha = portfolio_excess - beta * benchmark_excess
            
            # Reward positive alpha, penalize negative alpha
            if alpha > 0:
                # 5% annual alpha = max reward
                reward_value = min(alpha / 0.05 * self.max_reward_per_metric, self.max_reward_per_metric)
            else:
                # Penalty for negative alpha
                reward_value = max(alpha / 0.03 * self.max_reward_per_metric * self.penalty_multiplier,
                                 -self.max_reward_per_metric)
            
            suggestions = []
            if alpha < 0:
                suggestions.append("Focus on outperforming the benchmark")
                suggestions.append("Consider more selective stock picking")
            if alpha < 0.02:
                suggestions.append("Improve timing of trades")
                suggestions.append("Research higher conviction positions")
            
            return RewardMetric(
                name="Alpha Generation",
                value=reward_value,
                weight=self.reward_weights[RewardType.ALPHA_GENERATION.value],
                max_value=self.max_reward_per_metric,
                description=f"Alpha: {alpha:.2%}, Beta: {beta:.2f}",
                improvement_suggestions=suggestions
            )
            
        except Exception as e:
            logger.error(f"Error calculating alpha: {e}")
            return RewardMetric("Alpha Generation", 0, 0.15, 100, "Calculation error", [])
    
    def _calculate_diversification_rewards(self, positions_data: List[Dict[str, Any]]) -> RewardMetric:
        """Calculate rewards based on portfolio diversification."""
        if not positions_data:
            return RewardMetric("Diversification", 0, 0.10, 100, "No positions", ["Add positions to portfolio"])
        
        # Calculate diversification metrics
        position_count = len(positions_data)
        
        # Calculate concentration (HHI)
        total_value = sum(pos.get('market_value', 0) for pos in positions_data)
        if total_value == 0:
            return RewardMetric("Diversification", 0, 0.10, 100, "No value", [])
        
        weights = [pos.get('market_value', 0) / total_value for pos in positions_data]
        hhi = sum(w ** 2 for w in weights)
        diversification_score = 1 - hhi
        
        # Sector diversification
        sectors = {}
        for pos in positions_data:
            sector = pos.get('sector', 'Unknown')
            sectors[sector] = sectors.get(sector, 0) + pos.get('market_value', 0)
        
        sector_hhi = sum((value / total_value) ** 2 for value in sectors.values())
        sector_diversification = 1 - sector_hhi
        
        # Reward calculation
        position_reward = min(position_count / 15 * 50, 50)  # 15+ positions = max position reward
        concentration_reward = diversification_score * 25  # Max 25 points for concentration
        sector_reward = sector_diversification * 25  # Max 25 points for sector diversity
        
        reward_value = position_reward + concentration_reward + sector_reward
        
        suggestions = []
        if position_count < 10:
            suggestions.append("Increase number of positions for better diversification")
        if diversification_score < 0.8:
            suggestions.append("Reduce concentration in top holdings")
        if len(sectors) < 5:
            suggestions.append("Add exposure to more sectors")
        
        return RewardMetric(
            name="Diversification",
            value=reward_value,
            weight=self.reward_weights[RewardType.DIVERSIFICATION.value],
            max_value=self.max_reward_per_metric,
            description=f"Positions: {position_count}, Diversification: {diversification_score:.2f}",
            improvement_suggestions=suggestions
        )
    
    def _calculate_drawdown_rewards(self, portfolio_value: pd.Series) -> RewardMetric:
        """Calculate rewards based on drawdown control."""
        if len(portfolio_value) < 2:
            return RewardMetric("Drawdown Control", 0, 0.10, 100, "Insufficient data", [])
        
        # Calculate maximum drawdown
        rolling_max = portfolio_value.expanding().max()
        drawdown = (portfolio_value - rolling_max) / rolling_max
        max_drawdown = abs(drawdown.min())
        
        # Current drawdown
        current_drawdown = abs((portfolio_value.iloc[-1] - rolling_max.iloc[-1]) / rolling_max.iloc[-1])
        
        # Reward inverse of drawdown (lower drawdown = higher reward)
        # 5% max drawdown = max reward, 20%+ = penalty
        if max_drawdown <= 0.05:
            reward_value = self.max_reward_per_metric
        elif max_drawdown <= 0.20:
            reward_value = (0.20 - max_drawdown) / 0.15 * self.max_reward_per_metric
        else:
            reward_value = -(max_drawdown - 0.20) / 0.10 * self.max_reward_per_metric * self.penalty_multiplier
        
        suggestions = []
        if max_drawdown > 0.15:
            suggestions.append("Implement stronger risk management")
            suggestions.append("Consider position sizing rules")
        if current_drawdown > 0.10:
            suggestions.append("Review current positions for recovery potential")
        
        return RewardMetric(
            name="Drawdown Control",
            value=reward_value,
            weight=self.reward_weights[RewardType.DRAWDOWN_CONTROL.value],
            max_value=self.max_reward_per_metric,
            description=f"Max Drawdown: {max_drawdown:.1%}, Current: {current_drawdown:.1%}",
            improvement_suggestions=suggestions
        )
    
    def _calculate_volatility_rewards(self,
                                    portfolio_returns: pd.Series,
                                    benchmark_returns: pd.Series) -> RewardMetric:
        """Calculate rewards based on volatility management."""
        if len(portfolio_returns) < 30:
            return RewardMetric("Volatility Management", 0, 0.05, 100, "Insufficient data", [])
        
        portfolio_vol = portfolio_returns.std() * np.sqrt(252)
        benchmark_vol = benchmark_returns.std() * np.sqrt(252)
        
        # Reward for managing volatility relative to benchmark
        vol_ratio = portfolio_vol / benchmark_vol if benchmark_vol > 0 else 1.0
        
        # Optimal volatility ratio is around 0.8-1.2 of benchmark
        if 0.8 <= vol_ratio <= 1.2:
            reward_value = self.max_reward_per_metric
        elif vol_ratio < 0.8:
            # Too low volatility might mean missing opportunities
            reward_value = self.max_reward_per_metric * 0.7
        else:
            # Penalty for excessive volatility
            reward_value = max(0, self.max_reward_per_metric * (2.0 - vol_ratio))
        
        suggestions = []
        if vol_ratio > 1.5:
            suggestions.append("Reduce portfolio volatility")
            suggestions.append("Consider more stable positions")
        elif vol_ratio < 0.6:
            suggestions.append("Consider adding growth positions for better returns")
        
        return RewardMetric(
            name="Volatility Management",
            value=reward_value,
            weight=self.reward_weights[RewardType.VOLATILITY_MANAGEMENT.value],
            max_value=self.max_reward_per_metric,
            description=f"Portfolio Vol: {portfolio_vol:.1%}, Benchmark: {benchmark_vol:.1%}",
            improvement_suggestions=suggestions
        )
    
    def _calculate_performance_grade(self, weighted_score: float) -> str:
        """Calculate letter grade based on weighted score."""
        if weighted_score >= 85:
            return "A+"
        elif weighted_score >= 80:
            return "A"
        elif weighted_score >= 75:
            return "A-"
        elif weighted_score >= 70:
            return "B+"
        elif weighted_score >= 65:
            return "B"
        elif weighted_score >= 60:
            return "B-"
        elif weighted_score >= 55:
            return "C+"
        elif weighted_score >= 50:
            return "C"
        elif weighted_score >= 45:
            return "C-"
        elif weighted_score >= 40:
            return "D"
        else:
            return "F"
    
    def _create_error_reward_score(self, period_days: int) -> RewardScore:
        """Create a minimal reward score for error cases."""
        error_metric = RewardMetric(
            name="Error",
            value=0,
            weight=1.0,
            max_value=100,
            description="Error in calculation",
            improvement_suggestions=["Check data quality and availability"]
        )
        
        return RewardScore(
            total_score=0,
            weighted_score=0,
            individual_metrics={"error": error_metric},
            performance_grade="F",
            timestamp=datetime.now(),
            period_days=period_days,
            benchmark_comparison=0
        )
    
    def get_improvement_priorities(self, reward_score: RewardScore) -> List[Dict[str, Any]]:
        """
        Get prioritized improvement suggestions based on reward score.
        
        Args:
            reward_score: Recent reward score
            
        Returns:
            List of prioritized improvements
        """
        priorities = []
        
        for metric_name, metric in reward_score.individual_metrics.items():
            if metric.value < 50:  # Low performing metrics
                priority_level = "High" if metric.value < 25 else "Medium"
                
                priorities.append({
                    "metric": metric_name,
                    "current_score": metric.value,
                    "max_score": metric.max_value,
                    "priority": priority_level,
                    "suggestions": metric.improvement_suggestions,
                    "weight": metric.weight
                })
        
        # Sort by priority and weight
        priorities.sort(key=lambda x: (x["priority"] == "High", x["weight"]), reverse=True)
        
        return priorities


# Global reward calculator instance
_reward_calculator = None

def get_reward_calculator() -> RewardCalculator:
    """Get the global reward calculator instance."""
    global _reward_calculator
    if _reward_calculator is None:
        _reward_calculator = RewardCalculator()
    return _reward_calculator