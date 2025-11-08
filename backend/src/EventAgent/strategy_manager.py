"""
Strategy Manager Module for Formula-Based Trading

Manages multiple formula strategies, handles activation/deactivation,
performance tracking, and strategy selection based on market conditions.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)


class StrategyStatus(Enum):
    """Strategy lifecycle status."""
    INACTIVE = "inactive"
    PAPER_TRADING = "paper_trading"
    ACTIVE = "active"
    PAUSED = "paused"
    FAILED = "failed"


class MarketCondition(Enum):
    """Market condition classifications."""
    BULL = "bull"
    BEAR = "bear"
    SIDEWAYS = "sideways"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"


@dataclass
class PerformanceMetrics:
    """Performance metrics for a trading strategy."""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_pct: float = 0.0
    total_return: float = 0.0
    total_return_pct: float = 0.0
    avg_holding_period_hours: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)
    
    def calculate_metrics(self, trades: List[Dict[str, Any]]) -> None:
        """Calculate metrics from trade history."""
        if not trades:
            return
        
        self.total_trades = len(trades)
        winning = [t for t in trades if t.get("pnl", 0) > 0]
        losing = [t for t in trades if t.get("pnl", 0) <= 0]
        
        self.winning_trades = len(winning)
        self.losing_trades = len(losing)
        self.win_rate = self.winning_trades / self.total_trades if self.total_trades > 0 else 0.0
        
        if winning:
            self.avg_win = sum(t["pnl"] for t in winning) / len(winning)
        if losing:
            self.avg_loss = abs(sum(t["pnl"] for t in losing) / len(losing))
        
        self.total_pnl = sum(t.get("pnl", 0) for t in trades)
        
        # Profit factor
        total_wins = sum(t["pnl"] for t in winning)
        total_losses = abs(sum(t["pnl"] for t in losing))
        self.profit_factor = total_wins / total_losses if total_losses > 0 else 0.0
        
        self.last_updated = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["last_updated"] = self.last_updated.isoformat()
        return data


@dataclass
class RiskLimits:
    """Risk management limits for a strategy."""
    max_position_size_pct: float = 0.05  # 5% of portfolio
    max_daily_loss_pct: float = 0.02  # 2% daily loss limit
    max_total_loss_pct: float = 0.10  # 10% total loss limit
    min_signal_strength: float = 0.7  # Minimum confidence to trade
    max_open_positions: int = 5
    stop_loss_pct: float = 0.05
    take_profit_pct: float = 0.15
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class FormulaStrategy:
    """Formula-based trading strategy configuration."""
    strategy_id: str
    name: str
    formula_model_name: str
    description: str = ""
    status: StrategyStatus = StrategyStatus.INACTIVE
    symbols: List[str] = field(default_factory=list)
    market_conditions: List[MarketCondition] = field(default_factory=list)
    risk_limits: RiskLimits = field(default_factory=RiskLimits)
    performance: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    created_at: datetime = field(default_factory=datetime.now)
    activated_at: Optional[datetime] = None
    last_executed: Optional[datetime] = None
    execution_count: int = 0
    signal_count: int = 0
    error_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "strategy_id": self.strategy_id,
            "name": self.name,
            "formula_model_name": self.formula_model_name,
            "description": self.description,
            "status": self.status.value,
            "symbols": self.symbols,
            "market_conditions": [mc.value for mc in self.market_conditions],
            "risk_limits": self.risk_limits.to_dict(),
            "performance": self.performance.to_dict(),
            "created_at": self.created_at.isoformat(),
            "activated_at": self.activated_at.isoformat() if self.activated_at else None,
            "last_executed": self.last_executed.isoformat() if self.last_executed else None,
            "execution_count": self.execution_count,
            "signal_count": self.signal_count,
            "error_count": self.error_count,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FormulaStrategy":
        """Create from dictionary."""
        strategy = cls(
            strategy_id=data["strategy_id"],
            name=data["name"],
            formula_model_name=data["formula_model_name"],
            description=data.get("description", ""),
            status=StrategyStatus(data.get("status", "inactive")),
            symbols=data.get("symbols", []),
            market_conditions=[MarketCondition(mc) for mc in data.get("market_conditions", [])],
            created_at=datetime.fromisoformat(data["created_at"]),
            execution_count=data.get("execution_count", 0),
            signal_count=data.get("signal_count", 0),
            error_count=data.get("error_count", 0),
            metadata=data.get("metadata", {})
        )
        
        if data.get("activated_at"):
            strategy.activated_at = datetime.fromisoformat(data["activated_at"])
        if data.get("last_executed"):
            strategy.last_executed = datetime.fromisoformat(data["last_executed"])
        
        # Restore risk limits
        if "risk_limits" in data:
            strategy.risk_limits = RiskLimits(**data["risk_limits"])
        
        # Restore performance metrics
        if "performance" in data:
            perf_data = data["performance"]
            if "last_updated" in perf_data and isinstance(perf_data["last_updated"], str):
                perf_data["last_updated"] = datetime.fromisoformat(perf_data["last_updated"])
            strategy.performance = PerformanceMetrics(**perf_data)
        
        return strategy


class StrategyManager:
    """Manages formula-based trading strategies."""
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize strategy manager.
        
        Args:
            storage_path: Path to store strategy configurations
        """
        self.strategies: Dict[str, FormulaStrategy] = {}
        self.trade_history: Dict[str, List[Dict[str, Any]]] = {}
        
        if storage_path:
            self.storage_path = Path(storage_path)
            self.storage_path.mkdir(parents=True, exist_ok=True)
        else:
            self.storage_path = Path("~/.finance_bro/strategies").expanduser()
            self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._load_strategies()
    
    def create_strategy(
        self,
        name: str,
        formula_model_name: str,
        symbols: List[str],
        description: str = "",
        market_conditions: Optional[List[MarketCondition]] = None,
        risk_limits: Optional[RiskLimits] = None
    ) -> FormulaStrategy:
        """
        Create a new trading strategy.
        
        Args:
            name: Strategy name
            formula_model_name: Name of the formula model to use
            symbols: List of symbols to trade
            description: Strategy description
            market_conditions: Market conditions where strategy applies
            risk_limits: Risk management limits
        
        Returns:
            Created FormulaStrategy
        """
        strategy_id = str(uuid.uuid4())
        
        strategy = FormulaStrategy(
            strategy_id=strategy_id,
            name=name,
            formula_model_name=formula_model_name,
            description=description,
            symbols=symbols,
            market_conditions=market_conditions or [],
            risk_limits=risk_limits or RiskLimits()
        )
        
        self.strategies[strategy_id] = strategy
        self.trade_history[strategy_id] = []
        self._save_strategy(strategy)
        
        logger.info(f"Created strategy: {name} (ID: {strategy_id})")
        return strategy
    
    def activate_strategy(self, strategy_id: str, paper_trading: bool = True) -> bool:
        """
        Activate a strategy for trading.
        
        Args:
            strategy_id: Strategy ID
            paper_trading: Start in paper trading mode
        
        Returns:
            True if successfully activated
        """
        if strategy_id not in self.strategies:
            logger.error(f"Strategy {strategy_id} not found")
            return False
        
        strategy = self.strategies[strategy_id]
        
        # Validate strategy is ready
        if not self._validate_strategy(strategy):
            logger.error(f"Strategy {strategy.name} validation failed")
            return False
        
        # Set status
        strategy.status = StrategyStatus.PAPER_TRADING if paper_trading else StrategyStatus.ACTIVE
        strategy.activated_at = datetime.now()
        
        self._save_strategy(strategy)
        logger.info(f"Activated strategy: {strategy.name} (paper_trading={paper_trading})")
        return True
    
    def deactivate_strategy(self, strategy_id: str) -> bool:
        """
        Deactivate a strategy.
        
        Args:
            strategy_id: Strategy ID
        
        Returns:
            True if successfully deactivated
        """
        if strategy_id not in self.strategies:
            return False
        
        strategy = self.strategies[strategy_id]
        strategy.status = StrategyStatus.INACTIVE
        self._save_strategy(strategy)
        
        logger.info(f"Deactivated strategy: {strategy.name}")
        return True
    
    def pause_strategy(self, strategy_id: str) -> bool:
        """
        Pause a strategy temporarily.
        
        Args:
            strategy_id: Strategy ID
        
        Returns:
            True if successfully paused
        """
        if strategy_id not in self.strategies:
            return False
        
        strategy = self.strategies[strategy_id]
        strategy.status = StrategyStatus.PAUSED
        self._save_strategy(strategy)
        
        logger.info(f"Paused strategy: {strategy.name}")
        return True
    
    def resume_strategy(self, strategy_id: str) -> bool:
        """
        Resume a paused strategy.
        
        Args:
            strategy_id: Strategy ID
        
        Returns:
            True if successfully resumed
        """
        if strategy_id not in self.strategies:
            return False
        
        strategy = self.strategies[strategy_id]
        if strategy.status != StrategyStatus.PAUSED:
            return False
        
        # Resume to previous status (paper trading or active)
        strategy.status = StrategyStatus.PAPER_TRADING  # Default to paper trading
        self._save_strategy(strategy)
        
        logger.info(f"Resumed strategy: {strategy.name}")
        return True
    
    def get_active_strategies(
        self,
        market_condition: Optional[MarketCondition] = None
    ) -> List[FormulaStrategy]:
        """
        Get all active strategies, optionally filtered by market condition.
        
        Args:
            market_condition: Filter by market condition
        
        Returns:
            List of active strategies
        """
        active = [
            s for s in self.strategies.values()
            if s.status in [StrategyStatus.ACTIVE, StrategyStatus.PAPER_TRADING]
        ]
        
        if market_condition:
            active = [
                s for s in active
                if not s.market_conditions or market_condition in s.market_conditions
            ]
        
        return active
    
    def record_trade(
        self,
        strategy_id: str,
        trade_data: Dict[str, Any]
    ) -> None:
        """
        Record a trade execution for a strategy.
        
        Args:
            strategy_id: Strategy ID
            trade_data: Trade execution details
        """
        if strategy_id not in self.strategies:
            logger.error(f"Strategy {strategy_id} not found")
            return
        
        strategy = self.strategies[strategy_id]
        
        # Add trade to history
        trade_record = {
            **trade_data,
            "timestamp": datetime.now().isoformat(),
            "strategy_id": strategy_id,
            "strategy_name": strategy.name
        }
        
        if strategy_id not in self.trade_history:
            self.trade_history[strategy_id] = []
        
        self.trade_history[strategy_id].append(trade_record)
        
        # Update strategy stats
        strategy.execution_count += 1
        strategy.last_executed = datetime.now()
        
        # Recalculate performance metrics
        strategy.performance.calculate_metrics(self.trade_history[strategy_id])
        
        self._save_strategy(strategy)
    
    def record_signal(
        self,
        strategy_id: str,
        signal_data: Dict[str, Any]
    ) -> None:
        """
        Record a signal generation (not necessarily executed).
        
        Args:
            strategy_id: Strategy ID
            signal_data: Signal details
        """
        if strategy_id not in self.strategies:
            return
        
        strategy = self.strategies[strategy_id]
        strategy.signal_count += 1
        self._save_strategy(strategy)
    
    def record_error(
        self,
        strategy_id: str,
        error: str
    ) -> None:
        """
        Record an error for a strategy.
        
        Args:
            strategy_id: Strategy ID
            error: Error description
        """
        if strategy_id not in self.strategies:
            return
        
        strategy = self.strategies[strategy_id]
        strategy.error_count += 1
        
        # Auto-disable strategy if too many errors
        if strategy.error_count > 10:
            strategy.status = StrategyStatus.FAILED
            logger.error(f"Strategy {strategy.name} failed after {strategy.error_count} errors")
        
        self._save_strategy(strategy)
    
    def get_strategy(self, strategy_id: str) -> Optional[FormulaStrategy]:
        """Get a specific strategy by ID."""
        return self.strategies.get(strategy_id)
    
    def get_strategy_by_name(self, name: str) -> Optional[FormulaStrategy]:
        """Get a strategy by name."""
        for strategy in self.strategies.values():
            if strategy.name == name:
                return strategy
        return None
    
    def list_strategies(self) -> List[FormulaStrategy]:
        """List all strategies."""
        return list(self.strategies.values())
    
    def delete_strategy(self, strategy_id: str) -> bool:
        """
        Delete a strategy.
        
        Args:
            strategy_id: Strategy ID
        
        Returns:
            True if successfully deleted
        """
        if strategy_id not in self.strategies:
            return False
        
        strategy = self.strategies[strategy_id]
        
        # Only allow deletion of inactive strategies
        if strategy.status not in [StrategyStatus.INACTIVE, StrategyStatus.FAILED]:
            logger.error(f"Cannot delete active strategy: {strategy.name}")
            return False
        
        # Remove from memory
        del self.strategies[strategy_id]
        if strategy_id in self.trade_history:
            del self.trade_history[strategy_id]
        
        # Remove from storage
        strategy_file = self.storage_path / f"{strategy_id}.json"
        if strategy_file.exists():
            strategy_file.unlink()
        
        logger.info(f"Deleted strategy: {strategy.name}")
        return True
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get overall performance summary across all strategies.
        
        Returns:
            Performance summary
        """
        total_trades = sum(s.performance.total_trades for s in self.strategies.values())
        total_pnl = sum(s.performance.total_pnl for s in self.strategies.values())
        
        active_count = len([s for s in self.strategies.values() if s.status == StrategyStatus.ACTIVE])
        paper_count = len([s for s in self.strategies.values() if s.status == StrategyStatus.PAPER_TRADING])
        
        return {
            "total_strategies": len(self.strategies),
            "active_strategies": active_count,
            "paper_trading_strategies": paper_count,
            "total_trades": total_trades,
            "total_pnl": total_pnl,
            "timestamp": datetime.now().isoformat()
        }
    
    def _validate_strategy(self, strategy: FormulaStrategy) -> bool:
        """
        Validate strategy configuration.
        
        Args:
            strategy: Strategy to validate
        
        Returns:
            True if valid
        """
        # Check formula model exists (would need formula_engine integration)
        # For now, basic validation
        if not strategy.formula_model_name:
            return False
        
        if not strategy.symbols:
            return False
        
        return True
    
    def _save_strategy(self, strategy: FormulaStrategy) -> None:
        """Save strategy to disk."""
        try:
            strategy_file = self.storage_path / f"{strategy.strategy_id}.json"
            with open(strategy_file, "w") as f:
                json.dump(strategy.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Error saving strategy {strategy.name}: {e}")
    
    def _load_strategies(self) -> None:
        """Load strategies from disk."""
        try:
            for strategy_file in self.storage_path.glob("*.json"):
                try:
                    with open(strategy_file, "r") as f:
                        data = json.load(f)
                    
                    strategy = FormulaStrategy.from_dict(data)
                    self.strategies[strategy.strategy_id] = strategy
                    self.trade_history[strategy.strategy_id] = []
                    
                except Exception as e:
                    logger.error(f"Error loading strategy from {strategy_file}: {e}")
            
            logger.info(f"Loaded {len(self.strategies)} strategies from disk")
            
        except Exception as e:
            logger.error(f"Error loading strategies: {e}")


# Global instance
_strategy_manager = None

def get_strategy_manager() -> StrategyManager:
    """Get the global strategy manager instance."""
    global _strategy_manager
    if _strategy_manager is None:
        _strategy_manager = StrategyManager()
    return _strategy_manager
