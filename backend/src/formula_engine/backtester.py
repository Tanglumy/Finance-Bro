"""
Formula Backtester - Backtesting engine for formula-based strategies
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import logging
from itertools import product

from .evaluator import FormulaEvaluator

logger = logging.getLogger(__name__)

class Position:
    """Represents a trading position."""
    
    def __init__(self, symbol: str, quantity: float, entry_price: float, 
                 entry_date: datetime, direction: str):
        self.symbol = symbol
        self.quantity = quantity
        self.entry_price = entry_price
        self.entry_date = entry_date
        self.direction = direction  # 'long' or 'short'
        self.exit_price = None
        self.exit_date = None
        self.pnl = 0.0
        self.holding_period = 0
        self.is_open = True
    
    def close_position(self, exit_price: float, exit_date: datetime):
        """Close the position."""
        self.exit_price = exit_price
        self.exit_date = exit_date
        self.holding_period = (exit_date - self.entry_date).days
        
        if self.direction == 'long':
            self.pnl = self.quantity * (exit_price - self.entry_price)
        else:  # short
            self.pnl = self.quantity * (self.entry_price - exit_price)
        
        self.is_open = False
    
    def unrealized_pnl(self, current_price: float) -> float:
        """Calculate unrealized P&L."""
        if not self.is_open:
            return self.pnl
        
        if self.direction == 'long':
            return self.quantity * (current_price - self.entry_price)
        else:  # short
            return self.quantity * (self.entry_price - current_price)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert position to dictionary."""
        return {
            'symbol': self.symbol,
            'quantity': self.quantity,
            'entry_price': self.entry_price,
            'entry_date': self.entry_date.isoformat() if self.entry_date else None,
            'direction': self.direction,
            'exit_price': self.exit_price,
            'exit_date': self.exit_date.isoformat() if self.exit_date else None,
            'pnl': self.pnl,
            'holding_period': self.holding_period,
            'is_open': self.is_open
        }

class Portfolio:
    """Represents a trading portfolio."""
    
    def __init__(self, initial_capital: float, commission: float = 0.001):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.commission = commission
        self.positions = []
        self.closed_positions = []
        self.equity_curve = []
        self.trades = []
        self.current_date = None
    
    def open_position(self, symbol: str, quantity: float, price: float, 
                     date: datetime, direction: str = 'long'):
        """Open a new position."""
        # Calculate commission
        commission_cost = abs(quantity) * price * self.commission
        
        # Check if we have enough cash
        cost = abs(quantity) * price + commission_cost
        if cost > self.cash:
            logger.warning(f"Insufficient cash for position: {cost} > {self.cash}")
            return None
        
        # Create position
        position = Position(symbol, quantity, price, date, direction)
        self.positions.append(position)
        
        # Update cash
        self.cash -= cost
        
        # Record trade
        self.trades.append({
            'date': date,
            'symbol': symbol,
            'action': 'open',
            'quantity': quantity,
            'price': price,
            'direction': direction,
            'commission': commission_cost
        })
        
        return position
    
    def close_position(self, position: Position, price: float, date: datetime):
        """Close a position."""
        if position.is_open:
            # Calculate commission
            commission_cost = abs(position.quantity) * price * self.commission
            
            # Close position
            position.close_position(price, date)
            
            # Update cash
            proceeds = abs(position.quantity) * price - commission_cost
            self.cash += proceeds + position.pnl
            
            # Move to closed positions
            self.positions.remove(position)
            self.closed_positions.append(position)
            
            # Record trade
            self.trades.append({
                'date': date,
                'symbol': position.symbol,
                'action': 'close',
                'quantity': position.quantity,
                'price': price,
                'direction': position.direction,
                'commission': commission_cost,
                'pnl': position.pnl
            })
    
    def get_total_value(self, current_prices: Dict[str, float]) -> float:
        """Get total portfolio value."""
        total_value = self.cash
        
        for position in self.positions:
            if position.symbol in current_prices:
                current_price = current_prices[position.symbol]
                total_value += position.unrealized_pnl(current_price)
                total_value += abs(position.quantity) * position.entry_price
        
        return total_value
    
    def update_equity_curve(self, date: datetime, current_prices: Dict[str, float]):
        """Update equity curve."""
        total_value = self.get_total_value(current_prices)
        
        self.equity_curve.append({
            'date': date,
            'total_value': total_value,
            'cash': self.cash,
            'positions_value': total_value - self.cash
        })
        
        self.current_date = date
    
    def get_metrics(self) -> Dict[str, Any]:
        """Calculate portfolio metrics."""
        if not self.equity_curve:
            return {}
        
        # Convert to DataFrame for calculations
        df = pd.DataFrame(self.equity_curve)
        df['returns'] = df['total_value'].pct_change()
        
        # Basic metrics
        total_return = (df['total_value'].iloc[-1] - self.initial_capital) / self.initial_capital
        
        # Annualized return
        days = (df['date'].iloc[-1] - df['date'].iloc[0]).days
        years = days / 365.25
        annualized_return = (1 + total_return) ** (1/years) - 1 if years > 0 else 0
        
        # Volatility
        volatility = df['returns'].std() * np.sqrt(252)
        
        # Sharpe ratio (assuming 2% risk-free rate)
        risk_free_rate = 0.02
        excess_return = annualized_return - risk_free_rate
        sharpe_ratio = excess_return / volatility if volatility > 0 else 0
        
        # Maximum drawdown
        peak = df['total_value'].expanding().max()
        drawdown = (df['total_value'] - peak) / peak
        max_drawdown = drawdown.min()
        
        # Win rate
        winning_trades = [t for t in self.trades if t.get('pnl', 0) > 0]
        losing_trades = [t for t in self.trades if t.get('pnl', 0) < 0]
        total_trades = len(winning_trades) + len(losing_trades)
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        
        # Average win/loss
        avg_win = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['pnl'] for t in losing_trades]) if losing_trades else 0
        
        # Profit factor
        gross_profit = sum(t['pnl'] for t in winning_trades)
        gross_loss = abs(sum(t['pnl'] for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'final_value': df['total_value'].iloc[-1],
            'initial_capital': self.initial_capital
        }

class FormulaBacktester:
    """Backtesting engine for formula-based strategies."""
    
    def __init__(self):
        self.evaluator = FormulaEvaluator()
    
    def run_backtest(self, formula: str, data: pd.DataFrame,
                    start_date: Optional[str] = None,
                    end_date: Optional[str] = None,
                    initial_capital: float = 100000,
                    commission: float = 0.001,
                    variables: Optional[Dict[str, Any]] = None,
                    position_size: float = 0.1) -> Dict[str, Any]:
        """
        Run backtest for a formula-based strategy.
        
        Args:
            formula: Trading formula
            data: Historical market data
            start_date: Backtest start date
            end_date: Backtest end date
            initial_capital: Initial capital
            commission: Commission rate
            variables: Optional variables
            position_size: Position size as fraction of capital
            
        Returns:
            Backtest results
        """
        try:
            # Filter data by date range
            if start_date or end_date:
                data = self._filter_data_by_date(data, start_date, end_date)
            
            # Evaluate formula
            signals = self.evaluator.evaluate(formula, data, variables)
            
            # Create portfolio
            portfolio = Portfolio(initial_capital, commission)
            
            # Track signals
            if isinstance(signals, pd.Series):
                signals_df = pd.DataFrame({
                    'date': data['date'] if 'date' in data.columns else data.index,
                    'signal': signals,
                    'close': data['close']
                })
            else:
                # Convert scalar to series
                signals_df = pd.DataFrame({
                    'date': data['date'] if 'date' in data.columns else data.index,
                    'signal': [signals] * len(data),
                    'close': data['close']
                })
            
            # Run simulation
            current_position = None
            symbol = "SYMBOL"  # Default symbol name
            
            for idx, row in signals_df.iterrows():
                date = pd.to_datetime(row['date'])
                signal = row['signal']
                price = row['close']
                
                # Update portfolio equity curve
                current_prices = {symbol: price}
                portfolio.update_equity_curve(date, current_prices)
                
                # Handle signals
                if current_position is None:
                    # No position, look for entry
                    if self._is_buy_signal(signal):
                        # Calculate position size
                        position_value = portfolio.cash * position_size
                        quantity = position_value / price
                        
                        current_position = portfolio.open_position(
                            symbol, quantity, price, date, 'long'
                        )
                    elif self._is_sell_signal(signal):
                        # Short position
                        position_value = portfolio.cash * position_size
                        quantity = position_value / price
                        
                        current_position = portfolio.open_position(
                            symbol, -quantity, price, date, 'short'
                        )
                else:
                    # Have position, look for exit
                    if (current_position.direction == 'long' and self._is_sell_signal(signal)) or \
                       (current_position.direction == 'short' and self._is_buy_signal(signal)) or \
                       self._is_exit_signal(signal):
                        
                        portfolio.close_position(current_position, price, date)
                        current_position = None
            
            # Close any remaining positions
            if current_position:
                final_price = signals_df['close'].iloc[-1]
                final_date = pd.to_datetime(signals_df['date'].iloc[-1])
                portfolio.close_position(current_position, final_price, final_date)
            
            # Calculate metrics
            metrics = portfolio.get_metrics()
            
            # Create results
            results = {
                'metrics': metrics,
                'equity_curve': portfolio.equity_curve,
                'trades': portfolio.trades,
                'positions': [pos.to_dict() for pos in portfolio.closed_positions],
                'signals': signals_df.to_dict('records'),
                'backtest_config': {
                    'formula': formula,
                    'initial_capital': initial_capital,
                    'commission': commission,
                    'position_size': position_size,
                    'start_date': start_date,
                    'end_date': end_date,
                    'data_points': len(data)
                }
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Backtest error: {e}")
            raise
    
    def optimize_parameters(self, formula: str, data: pd.DataFrame,
                           parameter_ranges: Dict[str, tuple],
                           objective: str = "sharpe_ratio",
                           max_iterations: int = 100) -> Dict[str, Any]:
        """
        Optimize parameters for a formula.
        
        Args:
            formula: Base formula with parameter placeholders
            data: Historical data
            parameter_ranges: Parameter ranges for optimization
            objective: Optimization objective
            max_iterations: Maximum iterations
            
        Returns:
            Optimization results
        """
        try:
            best_params = None
            best_score = float('-inf')
            results = []
            
            # Generate parameter combinations
            param_names = list(parameter_ranges.keys())
            param_values = []
            
            for param_name in param_names:
                param_range = parameter_ranges[param_name]
                if len(param_range) == 3:  # (start, end, step)
                    values = list(np.arange(param_range[0], param_range[1], param_range[2]))
                else:  # List of values
                    values = param_range
                param_values.append(values)
            
            # Limit combinations
            combinations = list(product(*param_values))
            if len(combinations) > max_iterations:
                combinations = combinations[:max_iterations]
            
            # Test each combination
            for combination in combinations:
                # Create parameter dictionary
                params = dict(zip(param_names, combination))
                
                # Substitute parameters in formula
                test_formula = formula
                for param_name, param_value in params.items():
                    test_formula = test_formula.replace(f"{{{param_name}}}", str(param_value))
                
                try:
                    # Run backtest
                    backtest_result = self.run_backtest(test_formula, data)
                    
                    # Get objective value
                    score = backtest_result['metrics'].get(objective, 0)
                    
                    # Track results
                    results.append({
                        'parameters': params,
                        'score': score,
                        'metrics': backtest_result['metrics']
                    })
                    
                    # Update best
                    if score > best_score:
                        best_score = score
                        best_params = params
                        
                except Exception as e:
                    logger.warning(f"Optimization iteration failed: {e}")
                    continue
            
            # Sort results by score
            results.sort(key=lambda x: x['score'], reverse=True)
            
            return {
                'best_parameters': best_params,
                'best_score': best_score,
                'objective': objective,
                'total_iterations': len(results),
                'all_results': results[:20],  # Top 20 results
                'optimization_summary': {
                    'parameter_ranges': parameter_ranges,
                    'formula': formula,
                    'data_points': len(data)
                }
            }
            
        except Exception as e:
            logger.error(f"Optimization error: {e}")
            raise
    
    def walk_forward_analysis(self, formula: str, data: pd.DataFrame,
                             window_size: int = 252,
                             step_size: int = 63) -> Dict[str, Any]:
        """
        Perform walk-forward analysis.
        
        Args:
            formula: Trading formula
            data: Historical data
            window_size: Size of each window (days)
            step_size: Step size between windows (days)
            
        Returns:
            Walk-forward analysis results
        """
        try:
            results = []
            
            # Generate windows
            for i in range(0, len(data) - window_size, step_size):
                window_data = data.iloc[i:i + window_size]
                
                # Run backtest on window
                backtest_result = self.run_backtest(formula, window_data)
                
                # Store results
                results.append({
                    'window_start': i,
                    'window_end': i + window_size,
                    'start_date': window_data.iloc[0]['date'] if 'date' in window_data.columns else window_data.index[0],
                    'end_date': window_data.iloc[-1]['date'] if 'date' in window_data.columns else window_data.index[-1],
                    'metrics': backtest_result['metrics'],
                    'trades': len(backtest_result['trades'])
                })
            
            # Calculate aggregate metrics
            all_returns = [r['metrics']['total_return'] for r in results]
            all_sharpe = [r['metrics']['sharpe_ratio'] for r in results if not np.isnan(r['metrics']['sharpe_ratio'])]
            all_drawdowns = [r['metrics']['max_drawdown'] for r in results]
            
            aggregate_metrics = {
                'avg_return': np.mean(all_returns),
                'std_return': np.std(all_returns),
                'avg_sharpe': np.mean(all_sharpe) if all_sharpe else 0,
                'avg_drawdown': np.mean(all_drawdowns),
                'win_rate': sum(1 for r in all_returns if r > 0) / len(all_returns),
                'total_windows': len(results)
            }
            
            return {
                'window_results': results,
                'aggregate_metrics': aggregate_metrics,
                'analysis_config': {
                    'formula': formula,
                    'window_size': window_size,
                    'step_size': step_size,
                    'total_data_points': len(data)
                }
            }
            
        except Exception as e:
            logger.error(f"Walk-forward analysis error: {e}")
            raise
    
    def _filter_data_by_date(self, data: pd.DataFrame, start_date: Optional[str], 
                           end_date: Optional[str]) -> pd.DataFrame:
        """Filter data by date range."""
        if 'date' not in data.columns:
            return data
        
        filtered_data = data.copy()
        
        if start_date:
            filtered_data = filtered_data[filtered_data['date'] >= start_date]
        
        if end_date:
            filtered_data = filtered_data[filtered_data['date'] <= end_date]
        
        return filtered_data
    
    def _is_buy_signal(self, signal: Any) -> bool:
        """Check if signal is a buy signal."""
        if isinstance(signal, (int, float)):
            return signal > 0
        elif isinstance(signal, bool):
            return signal
        elif isinstance(signal, str):
            return signal.upper() in ['BUY', 'LONG', 'TRUE']
        return False
    
    def _is_sell_signal(self, signal: Any) -> bool:
        """Check if signal is a sell signal."""
        if isinstance(signal, (int, float)):
            return signal < 0
        elif isinstance(signal, bool):
            return not signal
        elif isinstance(signal, str):
            return signal.upper() in ['SELL', 'SHORT', 'FALSE']
        return False
    
    def _is_exit_signal(self, signal: Any) -> bool:
        """Check if signal is an exit signal."""
        if isinstance(signal, str):
            return signal.upper() in ['EXIT', 'CLOSE', 'HOLD']
        return False
    
    def monte_carlo_simulation(self, formula: str, data: pd.DataFrame,
                              num_simulations: int = 1000,
                              noise_level: float = 0.01) -> Dict[str, Any]:
        """
        Run Monte Carlo simulation on strategy.
        
        Args:
            formula: Trading formula
            data: Historical data
            num_simulations: Number of simulations
            noise_level: Noise level for price perturbation
            
        Returns:
            Monte Carlo simulation results
        """
        try:
            simulation_results = []
            
            for i in range(num_simulations):
                # Add noise to prices
                perturbed_data = data.copy()
                noise = np.random.normal(0, noise_level, len(data))
                
                for price_col in ['open', 'high', 'low', 'close']:
                    if price_col in perturbed_data.columns:
                        perturbed_data[price_col] = perturbed_data[price_col] * (1 + noise)
                
                # Run backtest
                try:
                    backtest_result = self.run_backtest(formula, perturbed_data)
                    simulation_results.append(backtest_result['metrics'])
                except Exception as e:
                    logger.warning(f"Monte Carlo simulation {i} failed: {e}")
                    continue
            
            # Calculate statistics
            if simulation_results:
                returns = [r['total_return'] for r in simulation_results]
                sharpe_ratios = [r['sharpe_ratio'] for r in simulation_results 
                               if not np.isnan(r['sharpe_ratio'])]
                max_drawdowns = [r['max_drawdown'] for r in simulation_results]
                
                monte_carlo_stats = {
                    'num_simulations': len(simulation_results),
                    'return_stats': {
                        'mean': np.mean(returns),
                        'std': np.std(returns),
                        'min': np.min(returns),
                        'max': np.max(returns),
                        'percentile_5': np.percentile(returns, 5),
                        'percentile_95': np.percentile(returns, 95)
                    },
                    'sharpe_stats': {
                        'mean': np.mean(sharpe_ratios) if sharpe_ratios else 0,
                        'std': np.std(sharpe_ratios) if sharpe_ratios else 0,
                        'min': np.min(sharpe_ratios) if sharpe_ratios else 0,
                        'max': np.max(sharpe_ratios) if sharpe_ratios else 0
                    },
                    'drawdown_stats': {
                        'mean': np.mean(max_drawdowns),
                        'std': np.std(max_drawdowns),
                        'min': np.min(max_drawdowns),
                        'max': np.max(max_drawdowns)
                    },
                    'positive_returns_rate': sum(1 for r in returns if r > 0) / len(returns)
                }
                
                return {
                    'monte_carlo_stats': monte_carlo_stats,
                    'all_results': simulation_results,
                    'simulation_config': {
                        'formula': formula,
                        'num_simulations': num_simulations,
                        'noise_level': noise_level,
                        'data_points': len(data)
                    }
                }
            else:
                return {'error': 'No successful simulations'}
                
        except Exception as e:
            logger.error(f"Monte Carlo simulation error: {e}")
            raise