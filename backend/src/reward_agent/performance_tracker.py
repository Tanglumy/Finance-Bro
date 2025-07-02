"""
Performance Tracker

This module tracks and analyzes portfolio performance over time to provide
insights for the reward learning system.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
import json
from collections import deque

from .reward_calculator import RewardScore

logger = logging.getLogger(__name__)


class PerformancePeriod(Enum):
    """Time periods for performance analysis."""
    DAILY = "daily"
    WEEKLY = "weekly" 
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


@dataclass
class PerformanceSnapshot:
    """Snapshot of performance at a specific point in time."""
    timestamp: datetime
    portfolio_value: float
    cash_balance: float
    total_return: float
    daily_return: float
    benchmark_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    reward_score: float
    positions_count: int
    sector_allocation: Dict[str, float]
    top_performers: List[Dict[str, Any]]
    worst_performers: List[Dict[str, Any]]


@dataclass
class PerformanceAnalysis:
    """Comprehensive performance analysis."""
    period: PerformancePeriod
    start_date: datetime
    end_date: datetime
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    calmar_ratio: float
    win_rate: float
    profit_factor: float
    average_win: float
    average_loss: float
    best_day: float
    worst_day: float
    correlation_with_benchmark: float
    beta: float
    alpha: float
    information_ratio: float
    tracking_error: float


class PerformanceTracker:
    """
    Tracks and analyzes portfolio performance metrics over time,
    providing insights for the reward learning system.
    """
    
    def __init__(self, max_history_days: int = 365):
        """
        Initialize the performance tracker.
        
        Args:
            max_history_days: Maximum days of history to keep
        """
        self.max_history_days = max_history_days
        
        # Performance history storage
        self.performance_snapshots: deque = deque(maxlen=max_history_days)
        self.daily_returns: deque = deque(maxlen=max_history_days)
        self.benchmark_returns: deque = deque(maxlen=max_history_days)
        self.portfolio_values: deque = deque(maxlen=max_history_days)
        
        # Performance metrics cache
        self._performance_cache = {}
        self._cache_expiry = {}
        
        # Benchmark data
        self.benchmark_symbol = "SPY"
        self.risk_free_rate = 0.03
        
    def update_performance(self, 
                         portfolio_data: Dict[str, Any], 
                         reward_score: RewardScore,
                         market_data: Optional[Dict[str, Any]] = None):
        """
        Update performance tracking with new data.
        
        Args:
            portfolio_data: Current portfolio information
            reward_score: Latest reward score
            market_data: Optional market data for context
        """
        try:
            timestamp = datetime.now()
            
            # Extract portfolio metrics
            portfolio_value = portfolio_data.get('total_value', 0)
            cash_balance = portfolio_data.get('cash_balance', 0)
            positions = portfolio_data.get('positions', [])
            
            # Calculate returns
            daily_return = 0.0
            if len(self.portfolio_values) > 0:
                previous_value = self.portfolio_values[-1]
                if previous_value > 0:
                    daily_return = (portfolio_value - previous_value) / previous_value
            
            # Mock benchmark return (in real implementation, fetch actual data)
            benchmark_return = np.random.normal(0.0008, 0.015)
            
            # Calculate performance metrics
            volatility = self._calculate_rolling_volatility()
            sharpe_ratio = self._calculate_sharpe_ratio()
            max_drawdown = self._calculate_max_drawdown()
            
            # Analyze positions
            top_performers, worst_performers = self._analyze_position_performance(positions)
            
            # Create performance snapshot
            snapshot = PerformanceSnapshot(
                timestamp=timestamp,
                portfolio_value=portfolio_value,
                cash_balance=cash_balance,
                total_return=self._calculate_total_return(),
                daily_return=daily_return,
                benchmark_return=benchmark_return,
                volatility=volatility,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                reward_score=reward_score.weighted_score,
                positions_count=len(positions),
                sector_allocation=self._calculate_sector_allocation(positions),
                top_performers=top_performers,
                worst_performers=worst_performers
            )
            
            # Store data
            self.performance_snapshots.append(snapshot)
            self.daily_returns.append(daily_return)
            self.benchmark_returns.append(benchmark_return)
            self.portfolio_values.append(portfolio_value)
            
            # Clear cache
            self._clear_expired_cache()
            
            logger.info(f"Performance updated: Return {daily_return:.2%}, Value ${portfolio_value:,.2f}")
            
        except Exception as e:
            logger.error(f"Error updating performance: {e}")
    
    def get_performance_analysis(self, 
                               period: PerformancePeriod = PerformancePeriod.MONTHLY,
                               start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None) -> PerformanceAnalysis:
        """
        Get comprehensive performance analysis for specified period.
        
        Args:
            period: Time period for analysis
            start_date: Optional start date (defaults to period-based calculation)
            end_date: Optional end date (defaults to now)
            
        Returns:
            PerformanceAnalysis: Comprehensive performance metrics
        """
        # Set default dates based on period
        end_date = end_date or datetime.now()
        if start_date is None:
            if period == PerformancePeriod.DAILY:
                start_date = end_date - timedelta(days=1)
            elif period == PerformancePeriod.WEEKLY:
                start_date = end_date - timedelta(weeks=1)
            elif period == PerformancePeriod.MONTHLY:
                start_date = end_date - timedelta(days=30)
            elif period == PerformancePeriod.QUARTERLY:
                start_date = end_date - timedelta(days=90)
            else:  # YEARLY
                start_date = end_date - timedelta(days=365)
        
        # Check cache
        cache_key = f"{period.value}_{start_date.date()}_{end_date.date()}"
        if cache_key in self._performance_cache:
            cache_time = self._cache_expiry.get(cache_key, datetime.min)
            if datetime.now() - cache_time < timedelta(hours=1):  # Cache for 1 hour
                return self._performance_cache[cache_key]
        
        # Filter data for period
        period_snapshots = [
            snapshot for snapshot in self.performance_snapshots
            if start_date <= snapshot.timestamp <= end_date
        ]
        
        period_returns = [snapshot.daily_return for snapshot in period_snapshots]
        period_benchmark = [snapshot.benchmark_return for snapshot in period_snapshots]
        
        if not period_returns:
            # Return empty analysis if no data
            return self._create_empty_analysis(period, start_date, end_date)
        
        # Calculate comprehensive metrics
        analysis = self._calculate_comprehensive_metrics(
            period, start_date, end_date, period_returns, period_benchmark, period_snapshots
        )
        
        # Cache result
        self._performance_cache[cache_key] = analysis
        self._cache_expiry[cache_key] = datetime.now()
        
        return analysis
    
    def _calculate_comprehensive_metrics(self,
                                       period: PerformancePeriod,
                                       start_date: datetime,
                                       end_date: datetime,
                                       returns: List[float],
                                       benchmark_returns: List[float],
                                       snapshots: List[PerformanceSnapshot]) -> PerformanceAnalysis:
        """Calculate comprehensive performance metrics."""
        
        returns_series = pd.Series(returns)
        benchmark_series = pd.Series(benchmark_returns)
        
        # Basic return metrics
        total_return = (1 + returns_series).prod() - 1
        
        # Annualization factor
        days = len(returns)
        if days == 0:
            return self._create_empty_analysis(period, start_date, end_date)
        
        years = days / 252  # Trading days
        annualized_return = (1 + total_return) ** (1/years) - 1 if years > 0 else 0
        
        # Risk metrics
        volatility = returns_series.std() * np.sqrt(252) if len(returns_series) > 1 else 0
        
        # RiOPENAI_API_KEY_REDACTED metrics
        excess_return = annualized_return - self.risk_free_rate
        sharpe_ratio = excess_return / volatility if volatility > 0 else 0
        
        # Sortino ratio
        downside_returns = returns_series[returns_series < 0]
        downside_deviation = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0.001
        sortino_ratio = excess_return / downside_deviation
        
        # Drawdown metrics
        cumulative_returns = (1 + returns_series).cumprod()
        rolling_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - rolling_max) / rolling_max
        max_drawdown = abs(drawdown.min())
        
        # Calmar ratio
        calmar_ratio = annualized_return / max_drawdown if max_drawdown > 0 else 0
        
        # Win/Loss metrics
        winning_days = returns_series[returns_series > 0]
        losing_days = returns_series[returns_series < 0]
        
        win_rate = len(winning_days) / len(returns_series) if len(returns_series) > 0 else 0
        profit_factor = abs(winning_days.sum() / losing_days.sum()) if len(losing_days) > 0 and losing_days.sum() != 0 else 0
        average_win = winning_days.mean() if len(winning_days) > 0 else 0
        average_loss = losing_days.mean() if len(losing_days) > 0 else 0
        
        # Best/worst days
        best_day = returns_series.max() if len(returns_series) > 0 else 0
        worst_day = returns_series.min() if len(returns_series) > 0 else 0
        
        # Benchmark comparison metrics
        correlation_with_benchmark = returns_series.corr(benchmark_series) if len(benchmark_series) > 1 else 0
        
        # Beta calculation
        covariance = np.cov(returns_series, benchmark_series)[0][1] if len(returns_series) > 1 else 0
        benchmark_variance = benchmark_series.var() if len(benchmark_series) > 1 else 1
        beta = covariance / benchmark_variance if benchmark_variance > 0 else 1
        
        # Alpha calculation
        benchmark_return = (1 + benchmark_series).prod() - 1
        benchmark_annualized = (1 + benchmark_return) ** (1/years) - 1 if years > 0 else 0
        alpha = annualized_return - (self.risk_free_rate + beta * (benchmark_annualized - self.risk_free_rate))
        
        # Information ratio and tracking error
        excess_returns = returns_series - benchmark_series
        tracking_error = excess_returns.std() * np.sqrt(252) if len(excess_returns) > 1 else 0
        information_ratio = excess_returns.mean() * 252 / tracking_error if tracking_error > 0 else 0
        
        return PerformanceAnalysis(
            period=period,
            start_date=start_date,
            end_date=end_date,
            total_return=total_return,
            annualized_return=annualized_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_drawdown,
            calmar_ratio=calmar_ratio,
            win_rate=win_rate,
            profit_factor=profit_factor,
            average_win=average_win,
            average_loss=average_loss,
            best_day=best_day,
            worst_day=worst_day,
            correlation_with_benchmark=correlation_with_benchmark,
            beta=beta,
            alpha=alpha,
            information_ratio=information_ratio,
            tracking_error=tracking_error
        )
    
    def get_performance_trends(self, days: int = 30) -> Dict[str, Any]:
        """
        Get performance trends over specified days.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with trend analysis
        """
        if len(self.performance_snapshots) < days:
            return {"error": "Insufficient data for trend analysis"}
        
        recent_snapshots = list(self.performance_snapshots)[-days:]
        
        # Extract time series
        dates = [s.timestamp for s in recent_snapshots]
        values = [s.portfolio_value for s in recent_snapshots]
        returns = [s.daily_return for s in recent_snapshots]
        reward_scores = [s.reward_score for s in recent_snapshots]
        
        # Calculate trends
        value_trend = np.polyfit(range(len(values)), values, 1)[0]  # Slope
        return_trend = np.polyfit(range(len(returns)), returns, 1)[0]
        reward_trend = np.polyfit(range(len(reward_scores)), reward_scores, 1)[0]
        
        # Volatility trend
        volatilities = []
        window = 7  # 7-day rolling volatility
        for i in range(window, len(returns)):
            vol = np.std(returns[i-window:i]) * np.sqrt(252)
            volatilities.append(vol)
        
        volatility_trend = np.polyfit(range(len(volatilities)), volatilities, 1)[0] if volatilities else 0
        
        return {
            "period_days": days,
            "portfolio_value_trend": {
                "direction": "increasing" if value_trend > 0 else "decreasing",
                "slope": value_trend,
                "start_value": values[0],
                "end_value": values[-1],
                "total_change": values[-1] - values[0],
                "percent_change": (values[-1] - values[0]) / values[0] * 100 if values[0] != 0 else 0
            },
            "returns_trend": {
                "direction": "improving" if return_trend > 0 else "declining",
                "slope": return_trend,
                "average_return": np.mean(returns),
                "volatility": np.std(returns) * np.sqrt(252)
            },
            "reward_score_trend": {
                "direction": "improving" if reward_trend > 0 else "declining", 
                "slope": reward_trend,
                "start_score": reward_scores[0],
                "end_score": reward_scores[-1],
                "average_score": np.mean(reward_scores)
            },
            "volatility_trend": {
                "direction": "increasing" if volatility_trend > 0 else "decreasing",
                "slope": volatility_trend,
                "current_volatility": volatilities[-1] if volatilities else 0
            }
        }
    
    def get_performance_comparison(self, 
                                 periods: List[PerformancePeriod] = None) -> Dict[str, Any]:
        """
        Compare performance across different time periods.
        
        Args:
            periods: List of periods to compare
            
        Returns:
            Performance comparison data
        """
        periods = periods or [PerformancePeriod.WEEKLY, PerformancePeriod.MONTHLY, PerformancePeriod.QUARTERLY]
        
        comparison = {}
        
        for period in periods:
            analysis = self.get_performance_analysis(period)
            comparison[period.value] = {
                "total_return": analysis.total_return,
                "annualized_return": analysis.annualized_return,
                "volatility": analysis.volatility,
                "sharpe_ratio": analysis.sharpe_ratio,
                "max_drawdown": analysis.max_drawdown,
                "win_rate": analysis.win_rate,
                "alpha": analysis.alpha,
                "beta": analysis.beta
            }
        
        # Calculate relative performance
        if len(comparison) >= 2:
            base_period = list(comparison.keys())[0]
            for period_name, metrics in comparison.items():
                if period_name != base_period:
                    base_metrics = comparison[base_period]
                    metrics["relative_to_" + base_period] = {
                        "return_difference": metrics["total_return"] - base_metrics["total_return"],
                        "sharpe_difference": metrics["sharpe_ratio"] - base_metrics["sharpe_ratio"],
                        "volatility_difference": metrics["volatility"] - base_metrics["volatility"]
                    }
        
        return comparison
    
    def _calculate_rolling_volatility(self, window: int = 20) -> float:
        """Calculate rolling volatility."""
        if len(self.daily_returns) < window:
            return 0.0
        
        recent_returns = list(self.daily_returns)[-window:]
        return np.std(recent_returns) * np.sqrt(252)
    
    def _calculate_sharpe_ratio(self, window: int = 30) -> float:
        """Calculate rolling Sharpe ratio."""
        if len(self.daily_returns) < window:
            return 0.0
        
        recent_returns = list(self.daily_returns)[-window:]
        mean_return = np.mean(recent_returns) * 252
        volatility = np.std(recent_returns) * np.sqrt(252)
        
        if volatility == 0:
            return 0.0
        
        return (mean_return - self.risk_free_rate) / volatility
    
    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown."""
        if len(self.portfolio_values) < 2:
            return 0.0
        
        values = list(self.portfolio_values)
        peak = values[0]
        max_dd = 0.0
        
        for value in values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            max_dd = max(max_dd, drawdown)
        
        return max_dd
    
    def _calculate_total_return(self) -> float:
        """Calculate total return since start."""
        if len(self.portfolio_values) < 2:
            return 0.0
        
        initial_value = self.portfolio_values[0]
        current_value = self.portfolio_values[-1]
        
        if initial_value == 0:
            return 0.0
        
        return (current_value - initial_value) / initial_value
    
    def _analyze_position_performance(self, positions: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Analyze individual position performance."""
        if not positions:
            return [], []
        
        # Sort positions by performance
        sorted_positions = sorted(
            positions, 
            key=lambda p: p.get('unrealized_pnl_percent', 0), 
            reverse=True
        )
        
        # Top 3 performers
        top_performers = []
        for pos in sorted_positions[:3]:
            top_performers.append({
                "symbol": pos.get('symbol', 'Unknown'),
                "return_percent": pos.get('unrealized_pnl_percent', 0),
                "value": pos.get('market_value', 0),
                "sector": pos.get('sector', 'Unknown')
            })
        
        # Worst 3 performers  
        worst_performers = []
        for pos in sorted_positions[-3:]:
            worst_performers.append({
                "symbol": pos.get('symbol', 'Unknown'),
                "return_percent": pos.get('unrealized_pnl_percent', 0),
                "value": pos.get('market_value', 0),
                "sector": pos.get('sector', 'Unknown')
            })
        
        return top_performers, worst_performers
    
    def _calculate_sector_allocation(self, positions: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate sector allocation percentages."""
        if not positions:
            return {}
        
        total_value = sum(pos.get('market_value', 0) for pos in positions)
        if total_value == 0:
            return {}
        
        sector_allocation = {}
        for pos in positions:
            sector = pos.get('sector', 'Unknown')
            value = pos.get('market_value', 0)
            sector_allocation[sector] = sector_allocation.get(sector, 0) + value
        
        # Convert to percentages
        return {
            sector: (value / total_value) * 100 
            for sector, value in sector_allocation.items()
        }
    
    def _create_empty_analysis(self, 
                             period: PerformancePeriod, 
                             start_date: datetime, 
                             end_date: datetime) -> PerformanceAnalysis:
        """Create empty performance analysis."""
        return PerformanceAnalysis(
            period=period,
            start_date=start_date,
            end_date=end_date,
            total_return=0.0,
            annualized_return=0.0,
            volatility=0.0,
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            max_drawdown=0.0,
            calmar_ratio=0.0,
            win_rate=0.0,
            profit_factor=0.0,
            average_win=0.0,
            average_loss=0.0,
            best_day=0.0,
            worst_day=0.0,
            correlation_with_benchmark=0.0,
            beta=0.0,
            alpha=0.0,
            information_ratio=0.0,
            tracking_error=0.0
        )
    
    def _clear_expired_cache(self):
        """Clear expired cache entries."""
        current_time = datetime.now()
        expired_keys = [
            key for key, expiry_time in self._cache_expiry.items()
            if current_time - expiry_time > timedelta(hours=2)
        ]
        
        for key in expired_keys:
            self._performance_cache.pop(key, None)
            self._cache_expiry.pop(key, None)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of current performance metrics."""
        if not self.performance_snapshots:
            return {"error": "No performance data available"}
        
        latest_snapshot = self.performance_snapshots[-1]
        monthly_analysis = self.get_performance_analysis(PerformancePeriod.MONTHLY)
        trends = self.get_performance_trends(30)
        
        return {
            "current_value": latest_snapshot.portfolio_value,
            "daily_return": latest_snapshot.daily_return,
            "total_return": latest_snapshot.total_return,
            "reward_score": latest_snapshot.reward_score,
            "monthly_performance": {
                "return": monthly_analysis.total_return,
                "volatility": monthly_analysis.volatility,
                "sharpe_ratio": monthly_analysis.sharpe_ratio,
                "max_drawdown": monthly_analysis.max_drawdown,
                "win_rate": monthly_analysis.win_rate
            },
            "trends": trends,
            "top_performers": latest_snapshot.top_performers,
            "sector_allocation": latest_snapshot.sector_allocation,
            "last_updated": latest_snapshot.timestamp.isoformat()
        }


# Global performance tracker instance
_performance_tracker = None

def get_performance_tracker() -> PerformanceTracker:
    """Get the global performance tracker instance."""
    global _performance_tracker
    if _performance_tracker is None:
        _performance_tracker = PerformanceTracker()
    return _performance_tracker