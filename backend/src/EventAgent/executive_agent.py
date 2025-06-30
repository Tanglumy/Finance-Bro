"""
Executive Agent for automated trading execution via Interactive Brokers (IBKR).
This module provides safe and controlled trading automation with comprehensive risk management.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from pydantic import BaseModel
from enum import Enum
import uuid


class OrderType(Enum):
    """Order types supported by the Executive Agent."""
    MARKET = "MKT"
    LIMIT = "LMT"
    STOP = "STP"
    STOP_LIMIT = "STP_LMT"
    TRAIL = "TRAIL"


class OrderAction(Enum):
    """Order actions."""
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(Enum):
    """Order execution status."""
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    PARTIAL = "PARTIAL"


class RiskCheckResult(Enum):
    """Risk check results."""
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"


@dataclass
class TradingOrder:
    """Represents a trading order."""
    order_id: str
    symbol: str
    action: OrderAction
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: str = "DAY"
    created_at: datetime = field(default_factory=datetime.now)
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    average_fill_price: float = 0.0
    commission: float = 0.0
    notes: str = ""


@dataclass
class RiskParameters:
    """Risk management parameters."""
    max_position_size_pct: float = 0.1  # 10% max position size
    max_daily_loss_pct: float = 0.02    # 2% max daily loss
    max_portfolio_leverage: float = 1.0  # No leverage by default
    min_cash_reserve_pct: float = 0.05  # 5% cash reserve
    max_correlation_threshold: float = 0.7  # Max correlation between positions
    max_sector_concentration_pct: float = 0.3  # 30% max in one sector
    stop_loss_pct: float = 0.05  # 5% stop loss
    take_profit_pct: float = 0.15  # 15% take profit


@dataclass
class ExecutionResult:
    """Result of order execution."""
    success: bool
    order_id: Optional[str] = None
    message: str = ""
    filled_quantity: float = 0.0
    average_price: float = 0.0
    commission: float = 0.0
    error_code: Optional[str] = None


class IBKRConnector:
    """Mock IBKR API connector for demonstration purposes."""
    
    def __init__(self, paper_trading: bool = True):
        """Initialize IBKR connector."""
        self.paper_trading = paper_trading
        self.connected = False
        self.account_id = "DU123456" if paper_trading else "U123456"
        self.orders: Dict[str, TradingOrder] = {}
        
    async def connect(self) -> bool:
        """Connect to IBKR API."""
        # In a real implementation, this would establish connection to IBKR
        self.connected = True
        logging.info(f"Connected to IBKR {'Paper' if self.paper_trading else 'Live'} Trading")
        return True
    
    async def disconnect(self) -> None:
        """Disconnect from IBKR API."""
        self.connected = False
        logging.info("Disconnected from IBKR")
    
    async def submit_order(self, order: TradingOrder) -> ExecutionResult:
        """Submit order to IBKR."""
        if not self.connected:
            return ExecutionResult(
                success=False,
                message="Not connected to IBKR",
                error_code="NOT_CONNECTED"
            )
        
        # Simulate order processing
        order.status = OrderStatus.SUBMITTED
        self.orders[order.order_id] = order
        
        # Simulate immediate fill for market orders (simplified)
        if order.order_type == OrderType.MARKET:
            await asyncio.sleep(0.1)  # Simulate network delay
            order.status = OrderStatus.FILLED
            order.filled_quantity = order.quantity
            order.average_fill_price = order.price or 100.0  # Mock price
            order.commission = order.quantity * 0.005  # Mock commission
        
        return ExecutionResult(
            success=True,
            order_id=order.order_id,
            message="Order submitted successfully",
            filled_quantity=order.filled_quantity,
            average_price=order.average_fill_price,
            commission=order.commission
        )
    
    async def cancel_order(self, order_id: str) -> ExecutionResult:
        """Cancel an existing order."""
        if order_id in self.orders:
            order = self.orders[order_id]
            if order.status in [OrderStatus.PENDING, OrderStatus.SUBMITTED]:
                order.status = OrderStatus.CANCELLED
                return ExecutionResult(
                    success=True,
                    order_id=order_id,
                    message="Order cancelled successfully"
                )
            else:
                return ExecutionResult(
                    success=False,
                    message=f"Cannot cancel order in status: {order.status.value}",
                    error_code="INVALID_STATUS"
                )
        else:
            return ExecutionResult(
                success=False,
                message="Order not found",
                error_code="ORDER_NOT_FOUND"
            )
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information."""
        # Mock account data
        return {
            "account_id": self.account_id,
            "total_cash": 100000.0,
            "buying_power": 100000.0,
            "net_liquidation": 100000.0,
            "day_trades_remaining": 3,
            "currency": "USD"
        }
    
    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get current positions."""
        # Mock positions data
        return [
            {
                "symbol": "AAPL",
                "position": 100,
                "avg_cost": 150.0,
                "market_price": 155.0,
                "market_value": 15500.0,
                "unrealized_pnl": 500.0
            }
        ]


class RiskManager:
    """Risk management system for trading orders."""
    
    def __init__(self, risk_params: RiskParameters):
        """Initialize risk manager."""
        self.risk_params = risk_params
        
    async def check_order_risk(
        self, 
        order: TradingOrder,
        portfolio_value: float,
        current_positions: List[Dict[str, Any]],
        account_info: Dict[str, Any]
    ) -> Tuple[RiskCheckResult, str]:
        """Perform comprehensive risk checks on an order."""
        
        # Check 1: Position size limit
        order_value = order.quantity * (order.price or 100.0)
        position_size_pct = order_value / portfolio_value
        
        if position_size_pct > self.risk_params.max_position_size_pct:
            return (
                RiskCheckResult.REJECTED,
                f"Position size {position_size_pct:.2%} exceeds limit of {self.risk_params.max_position_size_pct:.2%}"
            )
        
        # Check 2: Cash reserve requirement
        cash_available = account_info.get("total_cash", 0)
        if order.action == OrderAction.BUY:
            cash_after_order = cash_available - order_value
            min_cash_required = portfolio_value * self.risk_params.min_cash_reserve_pct
            
            if cash_after_order < min_cash_required:
                return (
                    RiskCheckResult.REJECTED,
                    f"Insufficient cash reserve. Required: ${min_cash_required:,.2f}, Available after order: ${cash_after_order:,.2f}"
                )
        
        # Check 3: Sector concentration
        # This would require sector classification data
        # For now, simplified check
        
        # Check 4: Daily loss limit
        # This would require tracking daily P&L
        
        # Check 5: Correlation limits
        # This would require correlation analysis with existing positions
        
        return (RiskCheckResult.APPROVED, "All risk checks passed")
    
    def calculate_stop_loss_price(self, entry_price: float, action: OrderAction) -> float:
        """Calculate stop loss price based on risk parameters."""
        if action == OrderAction.BUY:
            return entry_price * (1 - self.risk_params.stop_loss_pct)
        else:  # SELL
            return entry_price * (1 + self.risk_params.stop_loss_pct)
    
    def calculate_take_profit_price(self, entry_price: float, action: OrderAction) -> float:
        """Calculate take profit price based on risk parameters."""
        if action == OrderAction.BUY:
            return entry_price * (1 + self.risk_params.take_profit_pct)
        else:  # SELL
            return entry_price * (1 - self.risk_params.take_profit_pct)


class ExecutiveAgent:
    """Main Executive Agent for automated trading."""
    
    def __init__(
        self, 
        paper_trading: bool = True,
        risk_params: Optional[RiskParameters] = None
    ):
        """Initialize Executive Agent."""
        self.paper_trading = paper_trading
        self.risk_params = risk_params or RiskParameters()
        self.ibkr_connector = IBKRConnector(paper_trading)
        self.risk_manager = RiskManager(self.risk_params)
        self.active_orders: Dict[str, TradingOrder] = {}
        self.execution_log: List[Dict[str, Any]] = []
        self.enabled = False  # Safety switch
        
    async def initialize(self) -> bool:
        """Initialize the Executive Agent."""
        try:
            success = await self.ibkr_connector.connect()
            if success:
                self.enabled = True
                logging.info("Executive Agent initialized successfully")
                return True
            else:
                logging.error("Failed to connect to IBKR")
                return False
        except Exception as e:
            logging.error(f"Failed to initialize Executive Agent: {e}")
            return False
    
    async def shutdown(self) -> None:
        """Shutdown the Executive Agent."""
        self.enabled = False
        await self.ibkr_connector.disconnect()
        logging.info("Executive Agent shutdown complete")
    
    async def execute_signal(
        self, 
        signal: Dict[str, Any],
        portfolio_manager=None
    ) -> ExecutionResult:
        """Execute a trading signal with full risk management."""
        
        if not self.enabled:
            return ExecutionResult(
                success=False,
                message="Executive Agent is disabled",
                error_code="AGENT_DISABLED"
            )
        
        try:
            # Extract signal information
            symbol = signal.get("asset_symbol", "")
            signal_type = signal.get("signal_type", "")
            quantity = signal.get("quantity", 0)
            price = signal.get("entry_price")
            
            if not all([symbol, signal_type, quantity]):
                return ExecutionResult(
                    success=False,
                    message="Invalid signal: missing required fields",
                    error_code="INVALID_SIGNAL"
                )
            
            # Convert signal to order
            action = OrderAction.BUY if signal_type.upper() == "BUY" else OrderAction.SELL
            
            order = TradingOrder(
                order_id=str(uuid.uuid4()),
                symbol=symbol,
                action=action,
                order_type=OrderType.MARKET if price is None else OrderType.LIMIT,
                quantity=quantity,
                price=price,
                notes=f"Signal execution: {signal.get('rationale', '')}"
            )
            
            # Get account and portfolio information
            account_info = await self.ibkr_connector.get_account_info()
            current_positions = await self.ibkr_connector.get_positions()
            
            # Calculate portfolio value
            portfolio_value = account_info.get("net_liquidation", 100000.0)
            
            # Perform risk checks
            risk_result, risk_message = await self.risk_manager.check_order_risk(
                order, portfolio_value, current_positions, account_info
            )
            
            if risk_result == RiskCheckResult.REJECTED:
                return ExecutionResult(
                    success=False,
                    message=f"Risk check failed: {risk_message}",
                    error_code="RISK_REJECTED"
                )
            
            # Execute the order
            execution_result = await self.ibkr_connector.submit_order(order)
            
            if execution_result.success:
                self.active_orders[order.order_id] = order
                
                # Create protective orders (stop loss, take profit)
                if order.status == OrderStatus.FILLED:
                    await self._create_protective_orders(order)
                
                # Log execution
                self._log_execution(order, execution_result, signal)
                
                # Update portfolio manager if provided
                if portfolio_manager and execution_result.filled_quantity > 0:
                    if action == OrderAction.BUY:
                        portfolio_manager.add_position(
                            symbol, 
                            execution_result.filled_quantity, 
                            execution_result.average_price
                        )
                    else:
                        portfolio_manager.remove_position(
                            symbol, 
                            execution_result.filled_quantity, 
                            execution_result.average_price
                        )
            
            return execution_result
            
        except Exception as e:
            logging.error(f"Error executing signal: {e}")
            return ExecutionResult(
                success=False,
                message=f"Execution error: {str(e)}",
                error_code="EXECUTION_ERROR"
            )
    
    async def _create_protective_orders(self, primary_order: TradingOrder) -> None:
        """Create stop loss and take profit orders."""
        try:
            entry_price = primary_order.average_fill_price
            
            # Stop loss order
            stop_price = self.risk_manager.calculate_stop_loss_price(
                entry_price, primary_order.action
            )
            
            stop_order = TradingOrder(
                order_id=str(uuid.uuid4()),
                symbol=primary_order.symbol,
                action=OrderAction.SELL if primary_order.action == OrderAction.BUY else OrderAction.BUY,
                order_type=OrderType.STOP,
                quantity=primary_order.filled_quantity,
                stop_price=stop_price,
                notes=f"Stop loss for order {primary_order.order_id}"
            )
            
            # Take profit order
            profit_price = self.risk_manager.calculate_take_profit_price(
                entry_price, primary_order.action
            )
            
            profit_order = TradingOrder(
                order_id=str(uuid.uuid4()),
                symbol=primary_order.symbol,
                action=OrderAction.SELL if primary_order.action == OrderAction.BUY else OrderAction.BUY,
                order_type=OrderType.LIMIT,
                quantity=primary_order.filled_quantity,
                price=profit_price,
                notes=f"Take profit for order {primary_order.order_id}"
            )
            
            # Submit protective orders
            await self.ibkr_connector.submit_order(stop_order)
            await self.ibkr_connector.submit_order(profit_order)
            
            self.active_orders[stop_order.order_id] = stop_order
            self.active_orders[profit_order.order_id] = profit_order
            
        except Exception as e:
            logging.error(f"Error creating protective orders: {e}")
    
    def _log_execution(
        self, 
        order: TradingOrder, 
        result: ExecutionResult, 
        signal: Dict[str, Any]
    ) -> None:
        """Log order execution details."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "order_id": order.order_id,
            "symbol": order.symbol,
            "action": order.action.value,
            "quantity": order.quantity,
            "price": order.price,
            "filled_quantity": result.filled_quantity,
            "average_price": result.average_price,
            "commission": result.commission,
            "success": result.success,
            "message": result.message,
            "signal_rationale": signal.get("rationale", ""),
            "signal_strength": signal.get("signal_strength", 0.0)
        }
        
        self.execution_log.append(log_entry)
        logging.info(f"Order executed: {json.dumps(log_entry, indent=2)}")
    
    async def get_execution_status(self) -> Dict[str, Any]:
        """Get current execution status and statistics."""
        total_orders = len(self.execution_log)
        successful_orders = sum(1 for log in self.execution_log if log["success"])
        
        return {
            "agent_enabled": self.enabled,
            "paper_trading": self.paper_trading,
            "total_orders": total_orders,
            "successful_orders": successful_orders,
            "success_rate": (successful_orders / total_orders * 100) if total_orders > 0 else 0,
            "active_orders": len(self.active_orders),
            "account_info": await self.ibkr_connector.get_account_info() if self.enabled else {},
            "risk_parameters": {
                "max_position_size_pct": self.risk_params.max_position_size_pct,
                "max_daily_loss_pct": self.risk_params.max_daily_loss_pct,
                "stop_loss_pct": self.risk_params.stop_loss_pct,
                "take_profit_pct": self.risk_params.take_profit_pct
            }
        }
    
    async def emergency_stop(self) -> Dict[str, Any]:
        """Emergency stop - cancel all pending orders and disable trading."""
        self.enabled = False
        cancelled_orders = []
        
        for order_id, order in self.active_orders.items():
            if order.status in [OrderStatus.PENDING, OrderStatus.SUBMITTED]:
                result = await self.ibkr_connector.cancel_order(order_id)
                if result.success:
                    cancelled_orders.append(order_id)
        
        return {
            "emergency_stop_activated": True,
            "cancelled_orders": cancelled_orders,
            "timestamp": datetime.now().isoformat()
        }


# Global executive agent instance
_executive_agent = None

def get_executive_agent(paper_trading: bool = True) -> ExecutiveAgent:
    """Get the global executive agent instance."""
    global _executive_agent
    if _executive_agent is None:
        _executive_agent = ExecutiveAgent(paper_trading=paper_trading)
    return _executive_agent