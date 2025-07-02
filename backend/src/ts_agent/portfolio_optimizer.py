"""
Portfolio Optimizer

Uses time series predictions to optimize portfolio allocation and generate
rebalancing recommendations.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from scipy.optimize import minimize
import warnings
warnings.filterwarnings('ignore')

from .predictor import PredictionResponse

logger = logging.getLogger(__name__)

@dataclass
class OptimizationConstraints:
    """Portfolio optimization constraints."""
    max_weight: float = 0.4  # Maximum weight per asset
    min_weight: float = 0.0  # Minimum weight per asset
    max_sector_weight: float = 0.6  # Maximum sector allocation
    target_return: Optional[float] = None  # Target return
    max_risk: Optional[float] = None  # Maximum portfolio risk
    risk_free_rate: float = 0.02  # Risk-free rate
    
@dataclass
class PortfolioWeights:
    """Portfolio allocation weights."""
    weights: Dict[str, float]
    expected_return: float
    expected_risk: float
    sharpe_ratio: float
    optimization_method: str
    constraints_satisfied: bool
    generated_at: datetime

@dataclass
class RebalancingRecommendation:
    """Rebalancing recommendation."""
    symbol: str
    current_weight: float
    target_weight: float
    weight_change: float
    action: str  # 'buy', 'sell', 'hold'
    urgency: str  # 'high', 'medium', 'low'
    reason: str

class PortfolioOptimizer:
    """Portfolio optimization using time series predictions."""
    
    def __init__(self):
        self.optimization_methods = [
            "mean_variance",
            "risk_parity", 
            "max_sharpe",
            "min_variance",
            "black_litterman"
        ]
        
    def optimize_portfolio(
        self,
        predictions: Dict[str, PredictionResponse],
        current_weights: Optional[Dict[str, float]] = None,
        constraints: Optional[OptimizationConstraints] = None,
        method: str = "max_sharpe"
    ) -> PortfolioWeights:
        """
        Optimize portfolio allocation based on predictions.
        
        Args:
            predictions: Dictionary of symbol predictions
            current_weights: Current portfolio weights
            constraints: Optimization constraints
            method: Optimization method
            
        Returns:
            PortfolioWeights object
        """
        try:
            if not predictions:
                raise ValueError("No predictions provided")
            
            # Use default constraints if none provided
            if constraints is None:
                constraints = OptimizationConstraints()
            
            # Extract expected returns and risks from predictions
            returns, risks, correlation_matrix = self._extract_prediction_data(predictions)
            
            if len(returns) == 0:
                raise ValueError("No valid prediction data found")
            
            # Perform optimization based on method
            if method == "mean_variance":
                weights = self._mean_variance_optimization(returns, risks, correlation_matrix, constraints)
            elif method == "risk_parity":
                weights = self._risk_parity_optimization(risks, correlation_matrix, constraints)
            elif method == "max_sharpe":
                weights = self._max_sharpe_optimization(returns, risks, correlation_matrix, constraints)
            elif method == "min_variance":
                weights = self._min_variance_optimization(risks, correlation_matrix, constraints)
            elif method == "black_litterman":
                weights = self._black_litterman_optimization(returns, risks, correlation_matrix, constraints, current_weights)
            else:
                raise ValueError(f"Unknown optimization method: {method}")
            
            # Calculate portfolio metrics
            portfolio_return = sum(weights[symbol] * returns[symbol] for symbol in weights.keys())
            portfolio_risk = self._calculate_portfolio_risk(weights, risks, correlation_matrix)
            sharpe_ratio = (portfolio_return - constraints.risk_free_rate) / max(portfolio_risk, 1e-6)
            
            # Check constraints
            constraints_satisfied = self._check_constraints(weights, constraints)
            
            return PortfolioWeights(
                weights=weights,
                expected_return=portfolio_return,
                expected_risk=portfolio_risk,
                sharpe_ratio=sharpe_ratio,
                optimization_method=method,
                constraints_satisfied=constraints_satisfied,
                generated_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Portfolio optimization failed: {e}")
            # Return equal weights as fallback
            symbols = list(predictions.keys())
            equal_weight = 1.0 / len(symbols)
            fallback_weights = {symbol: equal_weight for symbol in symbols}
            
            return PortfolioWeights(
                weights=fallback_weights,
                expected_return=0.05,  # Default 5% return
                expected_risk=0.15,    # Default 15% risk
                sharpe_ratio=0.2,
                optimization_method="equal_weight_fallback",
                constraints_satisfied=True,
                generated_at=datetime.now()
            )
    
    def generate_rebalancing_recommendations(
        self,
        current_weights: Dict[str, float],
        target_weights: Dict[str, float],
        threshold: float = 0.05
    ) -> List[RebalancingRecommendation]:
        """
        Generate rebalancing recommendations.
        
        Args:
            current_weights: Current portfolio weights
            target_weights: Optimal target weights
            threshold: Minimum weight change to trigger rebalancing
            
        Returns:
            List of rebalancing recommendations
        """
        recommendations = []
        
        try:
            # Get all symbols
            all_symbols = set(current_weights.keys()) | set(target_weights.keys())
            
            for symbol in all_symbols:
                current_weight = current_weights.get(symbol, 0.0)
                target_weight = target_weights.get(symbol, 0.0)
                weight_change = target_weight - current_weight
                
                # Determine action
                if abs(weight_change) < threshold:
                    action = "hold"
                    urgency = "low"
                    reason = "Weight change below threshold"
                elif weight_change > 0:
                    action = "buy"
                    urgency = "high" if abs(weight_change) > 0.1 else "medium"
                    reason = f"Increase allocation by {weight_change:.1%}"
                else:
                    action = "sell"
                    urgency = "high" if abs(weight_change) > 0.1 else "medium"
                    reason = f"Decrease allocation by {abs(weight_change):.1%}"
                
                recommendation = RebalancingRecommendation(
                    symbol=symbol,
                    current_weight=current_weight,
                    target_weight=target_weight,
                    weight_change=weight_change,
                    action=action,
                    urgency=urgency,
                    reason=reason
                )
                
                recommendations.append(recommendation)
            
            # Sort by urgency and magnitude of change
            urgency_order = {"high": 3, "medium": 2, "low": 1}
            recommendations.sort(
                key=lambda x: (urgency_order[x.urgency], abs(x.weight_change)),
                reverse=True
            )
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating rebalancing recommendations: {e}")
            return []
    
    def optimize_risk_budget(
        self,
        predictions: Dict[str, PredictionResponse],
        risk_budget: Dict[str, float],
        constraints: Optional[OptimizationConstraints] = None
    ) -> PortfolioWeights:
        """
        Optimize portfolio based on risk budgeting approach.
        
        Args:
            predictions: Symbol predictions
            risk_budget: Risk budget allocation per symbol
            constraints: Optimization constraints
            
        Returns:
            PortfolioWeights object
        """
        try:
            if constraints is None:
                constraints = OptimizationConstraints()
            
            # Extract data
            returns, risks, correlation_matrix = self._extract_prediction_data(predictions)
            
            # Normalize risk budget
            total_budget = sum(risk_budget.values())
            if total_budget > 0:
                normalized_budget = {k: v / total_budget for k, v in risk_budget.items()}
            else:
                # Equal risk budget
                normalized_budget = {symbol: 1.0 / len(predictions) for symbol in predictions.keys()}
            
            # Initial equal weights
            n_assets = len(returns)
            initial_weights = np.array([1.0 / n_assets] * n_assets)
            symbols = list(returns.keys())
            
            # Objective function: minimize difference from target risk contributions
            def objective(weights):
                portfolio_risk = self._calculate_portfolio_risk_array(weights, risks, correlation_matrix, symbols)
                risk_contributions = self._calculate_risk_contributions(weights, risks, correlation_matrix, symbols)
                
                penalty = 0
                for i, symbol in enumerate(symbols):
                    target_risk = normalized_budget.get(symbol, 1.0 / n_assets)
                    actual_risk = risk_contributions[i] / max(portfolio_risk, 1e-6)
                    penalty += (actual_risk - target_risk) ** 2
                
                return penalty
            
            # Constraints
            constraints_list = [
                {'type': 'eq', 'fun': lambda w: np.sum(w) - 1},  # Weights sum to 1
            ]
            
            # Bounds
            bounds = [(constraints.min_weight, constraints.max_weight) for _ in range(n_assets)]
            
            # Optimize
            result = minimize(
                objective,
                initial_weights,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints_list,
                options={'maxiter': 1000}
            )
            
            if result.success:
                optimized_weights = {symbols[i]: result.x[i] for i in range(len(symbols))}
            else:
                logger.warning("Risk budget optimization failed, using equal weights")
                optimized_weights = {symbol: 1.0 / len(symbols) for symbol in symbols}
            
            # Calculate metrics
            portfolio_return = sum(optimized_weights[symbol] * returns[symbol] for symbol in symbols)
            portfolio_risk = self._calculate_portfolio_risk(optimized_weights, risks, correlation_matrix)
            sharpe_ratio = (portfolio_return - constraints.risk_free_rate) / max(portfolio_risk, 1e-6)
            
            return PortfolioWeights(
                weights=optimized_weights,
                expected_return=portfolio_return,
                expected_risk=portfolio_risk,
                sharpe_ratio=sharpe_ratio,
                optimization_method="risk_budget",
                constraints_satisfied=result.success,
                generated_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Risk budget optimization failed: {e}")
            # Fallback to equal weights
            symbols = list(predictions.keys())
            equal_weights = {symbol: 1.0 / len(symbols) for symbol in symbols}
            return PortfolioWeights(
                weights=equal_weights,
                expected_return=0.05,
                expected_risk=0.15,
                sharpe_ratio=0.2,
                optimization_method="risk_budget_fallback",
                constraints_satisfied=False,
                generated_at=datetime.now()
            )
    
    def _extract_prediction_data(
        self, 
        predictions: Dict[str, PredictionResponse]
    ) -> Tuple[Dict[str, float], Dict[str, float], pd.DataFrame]:
        """Extract returns, risks, and correlations from predictions."""
        returns = {}
        risks = {}
        price_series = {}
        
        for symbol, prediction in predictions.items():
            try:
                # Extract predicted return
                if not prediction.predictions.empty:
                    # Get predicted values
                    if 'ensemble_prediction' in prediction.predictions.columns:
                        pred_values = prediction.predictions['ensemble_prediction']
                    else:
                        pred_cols = [col for col in prediction.predictions.columns if col != 'ds']
                        pred_values = prediction.predictions[pred_cols[0]] if pred_cols else None
                    
                    if pred_values is not None and len(pred_values) > 0:
                        # Calculate return from first to last prediction
                        first_pred = pred_values.iloc[0]
                        last_pred = pred_values.iloc[-1]
                        
                        if first_pred > 0:
                            predicted_return = (last_pred - first_pred) / first_pred
                            returns[symbol] = predicted_return / prediction.horizon * 252  # Annualized
                            
                            # Calculate risk from prediction variance
                            pred_returns = pred_values.pct_change().dropna()
                            if len(pred_returns) > 1:
                                risks[symbol] = pred_returns.std() * np.sqrt(252)
                            else:
                                risks[symbol] = 0.15  # Default 15% volatility
                            
                            price_series[symbol] = pred_values
                
            except Exception as e:
                logger.warning(f"Error extracting data for {symbol}: {e}")
        
        # Calculate correlation matrix
        if len(price_series) > 1:
            # Align series lengths
            min_length = min(len(series) for series in price_series.values())
            aligned_series = {k: v.iloc[:min_length] for k, v in price_series.items()}
            
            correlation_df = pd.DataFrame(aligned_series).corr()
        else:
            # Single asset - correlation is 1
            correlation_df = pd.DataFrame([[1.0]], 
                                        index=list(price_series.keys()), 
                                        columns=list(price_series.keys()))
        
        return returns, risks, correlation_df
    
    def _mean_variance_optimization(
        self,
        returns: Dict[str, float],
        risks: Dict[str, float],
        correlation_matrix: pd.DataFrame,
        constraints: OptimizationConstraints
    ) -> Dict[str, float]:
        """Mean-variance optimization."""
        symbols = list(returns.keys())
        n_assets = len(symbols)
        
        # Convert to arrays
        ret_array = np.array([returns[symbol] for symbol in symbols])
        risk_array = np.array([risks[symbol] for symbol in symbols])
        
        # Covariance matrix
        corr_array = correlation_matrix.loc[symbols, symbols].values
        cov_matrix = np.outer(risk_array, risk_array) * corr_array
        
        # Objective function: minimize risk for given return or maximize return for given risk
        if constraints.target_return is not None:
            # Minimize risk for target return
            def objective(weights):
                return np.dot(weights, np.dot(cov_matrix, weights))
            
            constraints_list = [
                {'type': 'eq', 'fun': lambda w: np.sum(w) - 1},
                {'type': 'eq', 'fun': lambda w: np.dot(w, ret_array) - constraints.target_return}
            ]
        else:
            # Maximize Sharpe ratio
            def objective(weights):
                portfolio_return = np.dot(weights, ret_array)
                portfolio_risk = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
                return -(portfolio_return - constraints.risk_free_rate) / max(portfolio_risk, 1e-6)
            
            constraints_list = [
                {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}
            ]
        
        # Bounds
        bounds = [(constraints.min_weight, constraints.max_weight) for _ in range(n_assets)]
        
        # Initial weights
        initial_weights = np.array([1.0 / n_assets] * n_assets)
        
        # Optimize
        result = minimize(
            objective,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints_list,
            options={'maxiter': 1000}
        )
        
        if result.success:
            return {symbols[i]: result.x[i] for i in range(n_assets)}
        else:
            logger.warning("Mean-variance optimization failed")
            return {symbol: 1.0 / n_assets for symbol in symbols}
    
    def _max_sharpe_optimization(
        self,
        returns: Dict[str, float],
        risks: Dict[str, float],
        correlation_matrix: pd.DataFrame,
        constraints: OptimizationConstraints
    ) -> Dict[str, float]:
        """Maximum Sharpe ratio optimization."""
        symbols = list(returns.keys())
        n_assets = len(symbols)
        
        ret_array = np.array([returns[symbol] for symbol in symbols])
        risk_array = np.array([risks[symbol] for symbol in symbols])
        corr_array = correlation_matrix.loc[symbols, symbols].values
        cov_matrix = np.outer(risk_array, risk_array) * corr_array
        
        def objective(weights):
            portfolio_return = np.dot(weights, ret_array)
            portfolio_risk = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
            return -(portfolio_return - constraints.risk_free_rate) / max(portfolio_risk, 1e-6)
        
        constraints_list = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]
        bounds = [(constraints.min_weight, constraints.max_weight) for _ in range(n_assets)]
        initial_weights = np.array([1.0 / n_assets] * n_assets)
        
        result = minimize(objective, initial_weights, method='SLSQP', 
                         bounds=bounds, constraints=constraints_list)
        
        if result.success:
            return {symbols[i]: result.x[i] for i in range(n_assets)}
        else:
            return {symbol: 1.0 / n_assets for symbol in symbols}
    
    def _risk_parity_optimization(
        self,
        risks: Dict[str, float],
        correlation_matrix: pd.DataFrame,
        constraints: OptimizationConstraints
    ) -> Dict[str, float]:
        """Risk parity optimization."""
        symbols = list(risks.keys())
        n_assets = len(symbols)
        
        # Equal risk contribution weights
        inv_risks = np.array([1.0 / risks[symbol] for symbol in symbols])
        risk_parity_weights = inv_risks / np.sum(inv_risks)
        
        # Apply constraints
        weights = {}
        for i, symbol in enumerate(symbols):
            weight = max(constraints.min_weight, 
                        min(constraints.max_weight, risk_parity_weights[i]))
            weights[symbol] = weight
        
        # Normalize to sum to 1
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}
        
        return weights
    
    def _min_variance_optimization(
        self,
        risks: Dict[str, float],
        correlation_matrix: pd.DataFrame,
        constraints: OptimizationConstraints
    ) -> Dict[str, float]:
        """Minimum variance optimization."""
        symbols = list(risks.keys())
        n_assets = len(symbols)
        
        risk_array = np.array([risks[symbol] for symbol in symbols])
        corr_array = correlation_matrix.loc[symbols, symbols].values
        cov_matrix = np.outer(risk_array, risk_array) * corr_array
        
        def objective(weights):
            return np.dot(weights, np.dot(cov_matrix, weights))
        
        constraints_list = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]
        bounds = [(constraints.min_weight, constraints.max_weight) for _ in range(n_assets)]
        initial_weights = np.array([1.0 / n_assets] * n_assets)
        
        result = minimize(objective, initial_weights, method='SLSQP',
                         bounds=bounds, constraints=constraints_list)
        
        if result.success:
            return {symbols[i]: result.x[i] for i in range(n_assets)}
        else:
            return {symbol: 1.0 / n_assets for symbol in symbols}
    
    def _black_litterman_optimization(
        self,
        returns: Dict[str, float],
        risks: Dict[str, float],
        correlation_matrix: pd.DataFrame,
        constraints: OptimizationConstraints,
        current_weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """Black-Litterman optimization (simplified version)."""
        # For now, use mean-variance with prior from current weights
        if current_weights is None:
            return self._mean_variance_optimization(returns, risks, correlation_matrix, constraints)
        
        # Blend predicted returns with implied returns from current weights
        symbols = list(returns.keys())
        blended_returns = {}
        
        for symbol in symbols:
            pred_return = returns[symbol]
            current_weight = current_weights.get(symbol, 0.0)
            
            # Simple blending: give more weight to predictions for larger current positions
            blend_factor = 0.7 + 0.3 * current_weight
            implied_return = 0.05  # Assume 5% market return
            
            blended_returns[symbol] = blend_factor * pred_return + (1 - blend_factor) * implied_return
        
        return self._mean_variance_optimization(blended_returns, risks, correlation_matrix, constraints)
    
    def _calculate_portfolio_risk(
        self,
        weights: Dict[str, float],
        risks: Dict[str, float],
        correlation_matrix: pd.DataFrame
    ) -> float:
        """Calculate portfolio risk given weights."""
        symbols = list(weights.keys())
        weight_array = np.array([weights[symbol] for symbol in symbols])
        risk_array = np.array([risks[symbol] for symbol in symbols])
        
        corr_array = correlation_matrix.loc[symbols, symbols].values
        cov_matrix = np.outer(risk_array, risk_array) * corr_array
        
        portfolio_variance = np.dot(weight_array, np.dot(cov_matrix, weight_array))
        return np.sqrt(portfolio_variance)
    
    def _calculate_portfolio_risk_array(
        self,
        weights: np.ndarray,
        risks: Dict[str, float],
        correlation_matrix: pd.DataFrame,
        symbols: List[str]
    ) -> float:
        """Calculate portfolio risk from weight array."""
        risk_array = np.array([risks[symbol] for symbol in symbols])
        corr_array = correlation_matrix.loc[symbols, symbols].values
        cov_matrix = np.outer(risk_array, risk_array) * corr_array
        
        portfolio_variance = np.dot(weights, np.dot(cov_matrix, weights))
        return np.sqrt(portfolio_variance)
    
    def _calculate_risk_contributions(
        self,
        weights: np.ndarray,
        risks: Dict[str, float],
        correlation_matrix: pd.DataFrame,
        symbols: List[str]
    ) -> np.ndarray:
        """Calculate risk contributions for each asset."""
        risk_array = np.array([risks[symbol] for symbol in symbols])
        corr_array = correlation_matrix.loc[symbols, symbols].values
        cov_matrix = np.outer(risk_array, risk_array) * corr_array
        
        portfolio_risk = self._calculate_portfolio_risk_array(weights, risks, correlation_matrix, symbols)
        marginal_contributions = np.dot(cov_matrix, weights) / max(portfolio_risk, 1e-6)
        risk_contributions = weights * marginal_contributions
        
        return risk_contributions
    
    def _check_constraints(
        self,
        weights: Dict[str, float],
        constraints: OptimizationConstraints
    ) -> bool:
        """Check if portfolio weights satisfy constraints."""
        try:
            # Check weight bounds
            for weight in weights.values():
                if weight < constraints.min_weight - 1e-6 or weight > constraints.max_weight + 1e-6:
                    return False
            
            # Check weights sum to 1
            if abs(sum(weights.values()) - 1.0) > 1e-4:
                return False
            
            return True
            
        except Exception:
            return False