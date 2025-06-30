"""
Portfolio Management System with time series analysis capabilities.
This module provides comprehensive portfolio tracking, analysis, and optimization.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from pydantic import BaseModel
import json
import asyncio


@dataclass
class Position:
    """Represents a single position in the portfolio."""
    symbol: str
    quantity: float
    average_cost: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_percent: float
    sector: Optional[str] = None
    entry_date: Optional[datetime] = None
    
    @property
    def cost_basis(self) -> float:
        """Calculate the total cost basis of the position."""
        return self.quantity * self.average_cost
    
    @property
    def weight_percent(self) -> float:
        """Calculate position weight as percentage of total portfolio."""
        # This will be set by the portfolio manager
        return 0.0


@dataclass
class Transaction:
    """Represents a portfolio transaction."""
    transaction_id: str
    symbol: str
    action: str  # BUY, SELL
    quantity: float
    price: float
    timestamp: datetime
    fees: float = 0.0
    notes: Optional[str] = None


@dataclass
class PortfolioSnapshot:
    """Represents a portfolio state at a specific point in time."""
    timestamp: datetime
    total_value: float
    cash_balance: float
    positions: Dict[str, Position]
    daily_pnl: float
    daily_pnl_percent: float


class RiskMetrics(BaseModel):
    """Risk analysis metrics for the portfolio."""
    volatility: float
    beta: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    value_at_risk_95: float
    expected_shortfall_95: float
    correlation_with_market: float


class PerformanceMetrics(BaseModel):
    """Performance metrics for the portfolio."""
    total_return: float
    annualized_return: float
    ytd_return: float
    monthly_returns: List[float]
    win_rate: float
    profit_factor: float
    average_win: float
    average_loss: float
    largest_win: float
    largest_loss: float
    total_trades: int
    winning_trades: int
    losing_trades: int


class PortfolioAnalysis(BaseModel):
    """Complete portfolio analysis results."""
    current_value: float
    cash_balance: float
    invested_capital: float
    total_pnl: float
    total_pnl_percent: float
    positions: List[Position]
    sector_allocation: Dict[str, float]
    risk_metrics: RiskMetrics
    performance_metrics: PerformanceMetrics
    diversification_score: float
    concentration_risk: float
    rebalancing_needed: bool
    recommendations: List[str]


class PortfolioManager:
    """Advanced portfolio management system with time series analysis."""
    
    def __init__(self, initial_capital: float = 100000.0):
        """Initialize the portfolio manager."""
        self.initial_capital = initial_capital
        self.cash_balance = initial_capital
        self.positions: Dict[str, Position] = {}
        self.transactions: List[Transaction] = []
        self.snapshots: List[PortfolioSnapshot] = []
        self.benchmark_symbol = "SPY"  # S&P 500 as default benchmark
    
    def add_position(
        self, 
        symbol: str, 
        quantity: float, 
        price: float,
        sector: Optional[str] = None
    ) -> None:
        """Add or update a position in the portfolio."""
        cost = quantity * price
        
        if symbol in self.positions:
            # Update existing position
            existing = self.positions[symbol]
            total_quantity = existing.quantity + quantity
            total_cost = existing.cost_basis + cost
            new_avg_cost = total_cost / total_quantity if total_quantity > 0 else 0
            
            self.positions[symbol].quantity = total_quantity
            self.positions[symbol].average_cost = new_avg_cost
        else:
            # Create new position
            self.positions[symbol] = Position(
                symbol=symbol,
                quantity=quantity,
                average_cost=price,
                current_price=price,
                market_value=cost,
                unrealized_pnl=0.0,
                unrealized_pnl_percent=0.0,
                sector=sector,
                entry_date=datetime.now()
            )
        
        # Update cash balance
        self.cash_balance -= cost
        
        # Record transaction
        self.transactions.append(Transaction(
            transaction_id=f"txn_{len(self.transactions)+1}",
            symbol=symbol,
            action="BUY",
            quantity=quantity,
            price=price,
            timestamp=datetime.now()
        ))
    
    def remove_position(self, symbol: str, quantity: float, price: float) -> bool:
        """Remove or reduce a position in the portfolio."""
        if symbol not in self.positions:
            return False
        
        position = self.positions[symbol]
        if quantity > position.quantity:
            return False
        
        # Calculate proceeds
        proceeds = quantity * price
        
        # Update position
        if quantity == position.quantity:
            # Close entire position
            del self.positions[symbol]
        else:
            # Reduce position
            self.positions[symbol].quantity -= quantity
        
        # Update cash balance
        self.cash_balance += proceeds
        
        # Record transaction
        self.transactions.append(Transaction(
            transaction_id=f"txn_{len(self.transactions)+1}",
            symbol=symbol,
            action="SELL",
            quantity=quantity,
            price=price,
            timestamp=datetime.now()
        ))
        
        return True
    
    async def update_positions(self, price_data: Dict[str, float]) -> None:
        """Update all positions with current market prices."""
        for symbol, position in self.positions.items():
            if symbol in price_data:
                current_price = price_data[symbol]
                position.current_price = current_price
                position.market_value = position.quantity * current_price
                position.unrealized_pnl = position.market_value - position.cost_basis
                position.unrealized_pnl_percent = (
                    position.unrealized_pnl / position.cost_basis * 100 
                    if position.cost_basis > 0 else 0
                )
    
    def get_total_portfolio_value(self) -> float:
        """Calculate total portfolio value."""
        positions_value = sum(pos.market_value for pos in self.positions.values())
        return positions_value + self.cash_balance
    
    def get_sector_allocation(self) -> Dict[str, float]:
        """Get portfolio allocation by sector."""
        total_value = self.get_total_portfolio_value()
        sector_values = {}
        
        for position in self.positions.values():
            sector = position.sector or "Unknown"
            if sector not in sector_values:
                sector_values[sector] = 0
            sector_values[sector] += position.market_value
        
        # Convert to percentages
        return {
            sector: (value / total_value * 100) 
            for sector, value in sector_values.items()
        }
    
    def calculate_risk_metrics(self, returns_data: pd.Series, benchmark_returns: pd.Series) -> RiskMetrics:
        """Calculate comprehensive risk metrics."""
        if len(returns_data) < 30:  # Need sufficient data
            return RiskMetrics(
                volatility=0.0, beta=0.0, sharpe_ratio=0.0, sortino_ratio=0.0,
                max_drawdown=0.0, value_at_risk_95=0.0, expected_shortfall_95=0.0,
                correlation_with_market=0.0
            )
        
        # Volatility (annualized)
        volatility = returns_data.std() * np.sqrt(252)
        
        # Beta
        covariance = np.cov(returns_data, benchmark_returns)[0][1]
        benchmark_variance = benchmark_returns.var()
        beta = covariance / benchmark_variance if benchmark_variance > 0 else 0
        
        # Sharpe Ratio (assuming 3% risk-free rate)
        risk_free_rate = 0.03
        excess_returns = returns_data.mean() * 252 - risk_free_rate
        sharpe_ratio = excess_returns / volatility if volatility > 0 else 0
        
        # Sortino Ratio
        downside_returns = returns_data[returns_data < 0]
        downside_deviation = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0
        sortino_ratio = excess_returns / downside_deviation if downside_deviation > 0 else 0
        
        # Maximum Drawdown
        cumulative_returns = (1 + returns_data).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Value at Risk (95% confidence)
        var_95 = np.percentile(returns_data, 5)
        
        # Expected Shortfall (95% confidence)
        es_95 = returns_data[returns_data <= var_95].mean()
        
        # Correlation with market
        correlation = np.corrcoef(returns_data, benchmark_returns)[0][1]
        
        return RiskMetrics(
            volatility=volatility,
            beta=beta,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=abs(max_drawdown),
            value_at_risk_95=abs(var_95),
            expected_shortfall_95=abs(es_95),
            correlation_with_market=correlation
        )
    
    def calculate_performance_metrics(self, returns_data: pd.Series) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics."""
        if len(returns_data) == 0:
            return PerformanceMetrics(
                total_return=0.0, annualized_return=0.0, ytd_return=0.0,
                monthly_returns=[], win_rate=0.0, profit_factor=0.0,
                average_win=0.0, average_loss=0.0, largest_win=0.0,
                largest_loss=0.0, total_trades=0, winning_trades=0, losing_trades=0
            )
        
        # Total return
        total_return = (1 + returns_data).prod() - 1
        
        # Annualized return
        trading_days = len(returns_data)
        years = trading_days / 252
        annualized_return = (1 + total_return) ** (1/years) - 1 if years > 0 else 0
        
        # YTD return (assuming data includes current year)
        ytd_return = total_return  # Simplified for now
        
        # Monthly returns
        monthly_returns = returns_data.groupby(returns_data.index.to_period('M')).sum().tolist()
        
        # Win/Loss analysis
        winning_days = returns_data[returns_data > 0]
        losing_days = returns_data[returns_data < 0]
        
        win_rate = len(winning_days) / len(returns_data) * 100 if len(returns_data) > 0 else 0
        
        average_win = winning_days.mean() if len(winning_days) > 0 else 0
        average_loss = abs(losing_days.mean()) if len(losing_days) > 0 else 0
        
        profit_factor = (winning_days.sum() / abs(losing_days.sum()) 
                        if len(losing_days) > 0 and losing_days.sum() != 0 else 0)
        
        return PerformanceMetrics(
            total_return=total_return,
            annualized_return=annualized_return,
            ytd_return=ytd_return,
            monthly_returns=monthly_returns,
            win_rate=win_rate,
            profit_factor=profit_factor,
            average_win=average_win,
            average_loss=average_loss,
            largest_win=returns_data.max(),
            largest_loss=abs(returns_data.min()),
            total_trades=len(self.transactions),
            winning_trades=len(winning_days),
            losing_trades=len(losing_days)
        )
    
    def calculate_diversification_score(self) -> float:
        """Calculate portfolio diversification score (0-1)."""
        if len(self.positions) == 0:
            return 0.0
        
        total_value = self.get_total_portfolio_value()
        position_weights = [
            pos.market_value / total_value for pos in self.positions.values()
        ]
        
        # Herfindahl-Hirschman Index (inverted for diversification)
        hhi = sum(weight ** 2 for weight in position_weights)
        max_hhi = 1.0  # Maximum concentration (all in one asset)
        diversification_score = 1 - hhi
        
        return min(max(diversification_score, 0.0), 1.0)
    
    def calculate_concentration_risk(self) -> float:
        """Calculate concentration risk as percentage in top 3 positions."""
        if len(self.positions) == 0:
            return 0.0
        
        total_value = self.get_total_portfolio_value()
        position_values = [pos.market_value for pos in self.positions.values()]
        position_values.sort(reverse=True)
        
        top_3_value = sum(position_values[:3])
        return (top_3_value / total_value * 100) if total_value > 0 else 0
    
    def needs_rebalancing(self, max_position_weight: float = 20.0) -> bool:
        """Check if portfolio needs rebalancing."""
        total_value = self.get_total_portfolio_value()
        
        for position in self.positions.values():
            weight_percent = (position.market_value / total_value * 100) if total_value > 0 else 0
            if weight_percent > max_position_weight:
                return True
        
        return False
    
    def generate_recommendations(self) -> List[str]:
        """Generate portfolio optimization recommendations."""
        recommendations = []
        
        # Check concentration risk
        concentration = self.calculate_concentration_risk()
        if concentration > 60:
            recommendations.append("High concentration risk: Consider reducing largest positions")
        
        # Check diversification
        diversification = self.calculate_diversification_score()
        if diversification < 0.5:
            recommendations.append("Low diversification: Consider adding positions in different sectors")
        
        # Check cash allocation
        total_value = self.get_total_portfolio_value()
        cash_percent = (self.cash_balance / total_value * 100) if total_value > 0 else 0
        
        if cash_percent > 20:
            recommendations.append("High cash allocation: Consider investing excess cash")
        elif cash_percent < 5:
            recommendations.append("Low cash reserves: Consider maintaining higher cash buffer")
        
        # Check rebalancing
        if self.needs_rebalancing():
            recommendations.append("Portfolio needs rebalancing: Some positions exceed target weights")
        
        return recommendations
    
    async def get_comprehensive_analysis(
        self, 
        price_data: Dict[str, float],
        historical_returns: Optional[pd.Series] = None,
        benchmark_returns: Optional[pd.Series] = None
    ) -> PortfolioAnalysis:
        """Get complete portfolio analysis."""
        # Update positions with current prices
        await self.update_positions(price_data)
        
        # Calculate basic metrics
        total_value = self.get_total_portfolio_value()
        invested_capital = sum(pos.cost_basis for pos in self.positions.values())
        total_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        total_pnl_percent = (total_pnl / invested_capital * 100) if invested_capital > 0 else 0
        
        # Generate mock historical data if not provided
        if historical_returns is None:
            dates = pd.date_range(start=datetime.now() - timedelta(days=252), end=datetime.now(), freq='D')
            historical_returns = pd.Series(np.random.normal(0.001, 0.02, len(dates)), index=dates)
        
        if benchmark_returns is None:
            benchmark_returns = pd.Series(np.random.normal(0.0008, 0.015, len(historical_returns)), 
                                        index=historical_returns.index)
        
        # Calculate metrics
        risk_metrics = self.calculate_risk_metrics(historical_returns, benchmark_returns)
        performance_metrics = self.calculate_performance_metrics(historical_returns)
        sector_allocation = self.get_sector_allocation()
        diversification_score = self.calculate_diversification_score()
        concentration_risk = self.calculate_concentration_risk()
        rebalancing_needed = self.needs_rebalancing()
        recommendations = self.generate_recommendations()
        
        return PortfolioAnalysis(
            current_value=total_value,
            cash_balance=self.cash_balance,
            invested_capital=invested_capital,
            total_pnl=total_pnl,
            total_pnl_percent=total_pnl_percent,
            positions=list(self.positions.values()),
            sector_allocation=sector_allocation,
            risk_metrics=risk_metrics,
            performance_metrics=performance_metrics,
            diversification_score=diversification_score,
            concentration_risk=concentration_risk,
            rebalancing_needed=rebalancing_needed,
            recommendations=recommendations
        )
    
    def save_snapshot(self) -> None:
        """Save current portfolio state as a snapshot."""
        total_value = self.get_total_portfolio_value()
        
        # Calculate daily P&L (simplified)
        daily_pnl = 0.0
        daily_pnl_percent = 0.0
        
        if len(self.snapshots) > 0:
            previous_value = self.snapshots[-1].total_value
            daily_pnl = total_value - previous_value
            daily_pnl_percent = (daily_pnl / previous_value * 100) if previous_value > 0 else 0
        
        snapshot = PortfolioSnapshot(
            timestamp=datetime.now(),
            total_value=total_value,
            cash_balance=self.cash_balance,
            positions=self.positions.copy(),
            daily_pnl=daily_pnl,
            daily_pnl_percent=daily_pnl_percent
        )
        
        self.snapshots.append(snapshot)
    
    def get_time_series_data(self) -> pd.DataFrame:
        """Get portfolio time series data as DataFrame."""
        if not self.snapshots:
            return pd.DataFrame()
        
        data = []
        for snapshot in self.snapshots:
            data.append({
                'timestamp': snapshot.timestamp,
                'total_value': snapshot.total_value,
                'cash_balance': snapshot.cash_balance,
                'daily_pnl': snapshot.daily_pnl,
                'daily_pnl_percent': snapshot.daily_pnl_percent,
                'positions_count': len(snapshot.positions)
            })
        
        return pd.DataFrame(data).set_index('timestamp')


# Global portfolio manager instance
_portfolio_manager = None

def get_portfolio_manager() -> PortfolioManager:
    """Get the global portfolio manager instance."""
    global _portfolio_manager
    if _portfolio_manager is None:
        _portfolio_manager = PortfolioManager()
    return _portfolio_manager