"""
Risk Manager

Provides comprehensive risk assessment and management for time series predictions
and portfolio optimization.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

from .predictor import PredictionResponse
from .portfolio_optimizer import PortfolioWeights

logger = logging.getLogger(__name__)

@dataclass
class RiskMetrics:
    """Container for risk metrics."""
    symbol: str
    var_95: float  # Value at Risk (95%)
    var_99: float  # Value at Risk (99%) 
    expected_shortfall_95: float  # Expected Shortfall (95%)
    max_drawdown: float
    volatility: float
    beta: Optional[float] = None
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    
@dataclass
class PortfolioRisk:
    """Portfolio-level risk assessment."""
    portfolio_var_95: float
    portfolio_var_99: float
    portfolio_expected_shortfall: float
    concentration_risk: float
    correlation_risk: float
    liquidity_risk: float
    tail_risk: float
    stress_test_results: Dict[str, float]
    risk_attribution: Dict[str, float]
    
@dataclass
class RiskAlert:
    """Risk alert notification."""
    alert_type: str  # 'high_volatility', 'concentration', 'correlation', 'drawdown'
    severity: str    # 'low', 'medium', 'high', 'critical'
    symbol: Optional[str]
    message: str
    current_value: float
    threshold: float
    timestamp: datetime

class RiskManager:
    """Comprehensive risk management system."""
    
    def __init__(self):
        self.risk_thresholds = {
            'max_position_weight': 0.4,
            'max_sector_weight': 0.6,
            'max_correlation': 0.8,
            'max_volatility': 0.4,
            'max_var_95': 0.05,
            'max_drawdown': 0.2,
            'min_sharpe_ratio': 0.5
        }
        
    def assess_prediction_risk(
        self,
        prediction: PredictionResponse,
        historical_data: Optional[pd.DataFrame] = None
    ) -> RiskMetrics:
        """
        Assess risk metrics for a single prediction.
        
        Args:
            prediction: Prediction response
            historical_data: Historical price data for additional metrics
            
        Returns:
            RiskMetrics object
        """
        try:
            # Extract prediction values
            if 'ensemble_prediction' in prediction.predictions.columns:
                pred_values = prediction.predictions['ensemble_prediction']
            else:
                pred_cols = [col for col in prediction.predictions.columns if col != 'ds']
                pred_values = prediction.predictions[pred_cols[0]] if pred_cols else None
            
            if pred_values is None or len(pred_values) < 2:
                return self._default_risk_metrics(prediction.symbol)
            
            # Calculate returns from predictions
            pred_returns = pred_values.pct_change().dropna()
            
            if len(pred_returns) == 0:
                return self._default_risk_metrics(prediction.symbol)
            
            # Calculate VaR (Value at Risk)
            var_95 = np.percentile(pred_returns, 5)  # 5th percentile for 95% VaR
            var_99 = np.percentile(pred_returns, 1)  # 1st percentile for 99% VaR
            
            # Expected Shortfall (Conditional VaR)
            expected_shortfall_95 = pred_returns[pred_returns <= var_95].mean()
            if np.isnan(expected_shortfall_95):
                expected_shortfall_95 = var_95
            
            # Volatility (annualized)
            volatility = pred_returns.std() * np.sqrt(252)
            
            # Max Drawdown from predictions
            cumulative_returns = (1 + pred_returns).cumprod()
            running_max = cumulative_returns.expanding().max()
            drawdowns = (cumulative_returns - running_max) / running_max
            max_drawdown = abs(drawdowns.min())
            
            # Sharpe Ratio (using prediction returns)
            mean_return = pred_returns.mean() * 252  # Annualized
            risk_free_rate = 0.02  # 2% risk-free rate
            sharpe_ratio = (mean_return - risk_free_rate) / max(volatility, 1e-6)
            
            # Sortino Ratio (downside deviation)
            downside_returns = pred_returns[pred_returns < 0]
            if len(downside_returns) > 0:
                downside_deviation = downside_returns.std() * np.sqrt(252)
                sortino_ratio = (mean_return - risk_free_rate) / max(downside_deviation, 1e-6)
            else:
                sortino_ratio = sharpe_ratio
            
            # Calmar Ratio
            calmar_ratio = mean_return / max(max_drawdown, 1e-6)
            
            # Beta calculation (if historical data provided)
            beta = None
            if historical_data is not None and 'close' in historical_data.columns:
                try:
                    hist_returns = historical_data['close'].pct_change().dropna()
                    if len(hist_returns) > 20:
                        # Use last 20 returns as market proxy
                        market_returns = hist_returns.tail(20)
                        asset_returns = hist_returns.tail(20)
                        if len(asset_returns) == len(market_returns):
                            covariance = np.cov(asset_returns, market_returns)[0, 1]
                            market_variance = np.var(market_returns)
                            beta = covariance / max(market_variance, 1e-6)
                except:
                    pass
            
            return RiskMetrics(
                symbol=prediction.symbol,
                var_95=var_95,
                var_99=var_99,
                expected_shortfall_95=expected_shortfall_95,
                max_drawdown=max_drawdown,
                volatility=volatility,
                beta=beta,
                sharpe_ratio=sharpe_ratio,
                sortino_ratio=sortino_ratio,
                calmar_ratio=calmar_ratio
            )
            
        except Exception as e:
            logger.error(f"Error assessing prediction risk for {prediction.symbol}: {e}")
            return self._default_risk_metrics(prediction.symbol)
    
    def assess_portfolio_risk(
        self,
        portfolio_weights: PortfolioWeights,
        predictions: Dict[str, PredictionResponse],
        correlation_matrix: Optional[pd.DataFrame] = None
    ) -> PortfolioRisk:
        """
        Assess portfolio-level risk metrics.
        
        Args:
            portfolio_weights: Portfolio allocation
            predictions: Individual predictions
            correlation_matrix: Asset correlation matrix
            
        Returns:
            PortfolioRisk object
        """
        try:
            # Calculate individual asset risks
            asset_risks = {}
            for symbol, prediction in predictions.items():
                risk_metrics = self.assess_prediction_risk(prediction)
                asset_risks[symbol] = risk_metrics
            
            # Portfolio VaR calculation
            portfolio_var_95, portfolio_var_99 = self._calculate_portfolio_var(
                portfolio_weights.weights, asset_risks, correlation_matrix
            )
            
            # Expected Shortfall
            portfolio_expected_shortfall = self._calculate_portfolio_expected_shortfall(
                portfolio_weights.weights, asset_risks
            )
            
            # Concentration Risk
            concentration_risk = self._calculate_concentration_risk(portfolio_weights.weights)
            
            # Correlation Risk
            correlation_risk = self._calculate_correlation_risk(
                portfolio_weights.weights, correlation_matrix
            )
            
            # Liquidity Risk (simplified - based on position sizes)
            liquidity_risk = max(portfolio_weights.weights.values())
            
            # Tail Risk
            tail_risk = self._calculate_tail_risk(asset_risks, portfolio_weights.weights)
            
            # Stress Test Results
            stress_test_results = self._perform_stress_tests(
                portfolio_weights.weights, asset_risks
            )
            
            # Risk Attribution
            risk_attribution = self._calculate_risk_attribution(
                portfolio_weights.weights, asset_risks
            )
            
            return PortfolioRisk(
                portfolio_var_95=portfolio_var_95,
                portfolio_var_99=portfolio_var_99,
                portfolio_expected_shortfall=portfolio_expected_shortfall,
                concentration_risk=concentration_risk,
                correlation_risk=correlation_risk,
                liquidity_risk=liquidity_risk,
                tail_risk=tail_risk,
                stress_test_results=stress_test_results,
                risk_attribution=risk_attribution
            )
            
        except Exception as e:
            logger.error(f"Error assessing portfolio risk: {e}")
            return self._default_portfolio_risk()
    
    def generate_risk_alerts(
        self,
        portfolio_weights: PortfolioWeights,
        portfolio_risk: PortfolioRisk,
        asset_risks: Dict[str, RiskMetrics]
    ) -> List[RiskAlert]:
        """
        Generate risk alerts based on current metrics.
        
        Args:
            portfolio_weights: Portfolio allocation
            portfolio_risk: Portfolio risk metrics
            asset_risks: Individual asset risk metrics
            
        Returns:
            List of risk alerts
        """
        alerts = []
        
        try:
            # Check concentration risk
            for symbol, weight in portfolio_weights.weights.items():
                if weight > self.risk_thresholds['max_position_weight']:
                    alerts.append(RiskAlert(
                        alert_type='concentration',
                        severity='high' if weight > 0.5 else 'medium',
                        symbol=symbol,
                        message=f"Position weight {weight:.1%} exceeds threshold",
                        current_value=weight,
                        threshold=self.risk_thresholds['max_position_weight'],
                        timestamp=datetime.now()
                    ))
            
            # Check portfolio VaR
            if portfolio_risk.portfolio_var_95 < -self.risk_thresholds['max_var_95']:
                alerts.append(RiskAlert(
                    alert_type='high_volatility',
                    severity='high',
                    symbol=None,
                    message=f"Portfolio VaR {portfolio_risk.portfolio_var_95:.1%} exceeds threshold",
                    current_value=abs(portfolio_risk.portfolio_var_95),
                    threshold=self.risk_thresholds['max_var_95'],
                    timestamp=datetime.now()
                ))
            
            # Check individual asset volatility
            for symbol, risk_metrics in asset_risks.items():
                if risk_metrics.volatility > self.risk_thresholds['max_volatility']:
                    alerts.append(RiskAlert(
                        alert_type='high_volatility',
                        severity='medium',
                        symbol=symbol,
                        message=f"Asset volatility {risk_metrics.volatility:.1%} is high",
                        current_value=risk_metrics.volatility,
                        threshold=self.risk_thresholds['max_volatility'],
                        timestamp=datetime.now()
                    ))
            
            # Check correlation risk
            if portfolio_risk.correlation_risk > self.risk_thresholds['max_correlation']:
                alerts.append(RiskAlert(
                    alert_type='correlation',
                    severity='medium',
                    symbol=None,
                    message=f"High correlation risk {portfolio_risk.correlation_risk:.1%}",
                    current_value=portfolio_risk.correlation_risk,
                    threshold=self.risk_thresholds['max_correlation'],
                    timestamp=datetime.now()
                ))
            
            # Check Sharpe ratio
            if portfolio_weights.sharpe_ratio < self.risk_thresholds['min_sharpe_ratio']:
                alerts.append(RiskAlert(
                    alert_type='low_return_risk',
                    severity='low',
                    symbol=None,
                    message=f"Low Sharpe ratio {portfolio_weights.sharpe_ratio:.2f}",
                    current_value=portfolio_weights.sharpe_ratio,
                    threshold=self.risk_thresholds['min_sharpe_ratio'],
                    timestamp=datetime.now()
                ))
            
            # Sort alerts by severity
            severity_order = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
            alerts.sort(key=lambda x: severity_order[x.severity], reverse=True)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error generating risk alerts: {e}")
            return []
    
    def calculate_risk_adjusted_returns(
        self,
        predictions: Dict[str, PredictionResponse],
        risk_aversion: float = 2.0
    ) -> Dict[str, float]:
        """
        Calculate riOPENAI_API_KEY_REDACTED expected returns.
        
        Args:
            predictions: Asset predictions
            risk_aversion: Risk aversion parameter
            
        Returns:
            Dictionary of riOPENAI_API_KEY_REDACTED returns
        """
        risk_adjusted_returns = {}
        
        try:
            for symbol, prediction in predictions.items():
                # Get expected return from prediction
                if not prediction.predictions.empty:
                    if 'ensemble_prediction' in prediction.predictions.columns:
                        pred_values = prediction.predictions['ensemble_prediction']
                    else:
                        pred_cols = [col for col in prediction.predictions.columns if col != 'ds']
                        pred_values = prediction.predictions[pred_cols[0]] if pred_cols else None
                    
                    if pred_values is not None and len(pred_values) > 0:
                        # Calculate expected return
                        expected_return = (pred_values.iloc[-1] - pred_values.iloc[0]) / pred_values.iloc[0]
                        expected_return = expected_return / prediction.horizon * 252  # Annualized
                        
                        # Calculate risk
                        returns = pred_values.pct_change().dropna()
                        volatility = returns.std() * np.sqrt(252) if len(returns) > 0 else 0.15
                        
                        # RiOPENAI_API_KEY_REDACTED return
                        risk_adjusted_return = expected_return - 0.5 * risk_aversion * (volatility ** 2)
                        risk_adjusted_returns[symbol] = risk_adjusted_return
                
        except Exception as e:
            logger.error(f"Error calculating riOPENAI_API_KEY_REDACTED returns: {e}")
        
        return risk_adjusted_returns
    
    def _calculate_portfolio_var(
        self,
        weights: Dict[str, float],
        asset_risks: Dict[str, RiskMetrics],
        correlation_matrix: Optional[pd.DataFrame] = None
    ) -> Tuple[float, float]:
        """Calculate portfolio Value at Risk."""
        try:
            # Simple approach: weighted average of individual VaRs
            # More sophisticated approach would use correlation matrix
            
            var_95 = 0
            var_99 = 0
            
            for symbol, weight in weights.items():
                if symbol in asset_risks:
                    var_95 += weight * asset_risks[symbol].var_95
                    var_99 += weight * asset_risks[symbol].var_99
            
            # Apply diversification benefit if correlation matrix available
            if correlation_matrix is not None and len(weights) > 1:
                # Simplified diversification adjustment
                avg_correlation = self._get_average_correlation(correlation_matrix, weights)
                diversification_factor = np.sqrt(avg_correlation)
                var_95 *= diversification_factor
                var_99 *= diversification_factor
            
            return var_95, var_99
            
        except Exception as e:
            logger.error(f"Error calculating portfolio VaR: {e}")
            return -0.05, -0.10  # Default values
    
    def _calculate_portfolio_expected_shortfall(
        self,
        weights: Dict[str, float],
        asset_risks: Dict[str, RiskMetrics]
    ) -> float:
        """Calculate portfolio expected shortfall."""
        try:
            expected_shortfall = 0
            for symbol, weight in weights.items():
                if symbol in asset_risks:
                    expected_shortfall += weight * asset_risks[symbol].expected_shortfall_95
            return expected_shortfall
        except:
            return -0.08  # Default value
    
    def _calculate_concentration_risk(self, weights: Dict[str, float]) -> float:
        """Calculate concentration risk using Herfindahl index."""
        try:
            herfindahl_index = sum(weight ** 2 for weight in weights.values())
            # Normalize to 0-1 scale where 1 is maximum concentration
            max_concentration = 1.0  # All weight in one asset
            min_concentration = 1.0 / len(weights)  # Equal weights
            normalized_concentration = (herfindahl_index - min_concentration) / (max_concentration - min_concentration)
            return max(0, min(1, normalized_concentration))
        except:
            return 0.5  # Default moderate concentration
    
    def _calculate_correlation_risk(
        self,
        weights: Dict[str, float],
        correlation_matrix: Optional[pd.DataFrame] = None
    ) -> float:
        """Calculate correlation risk."""
        if correlation_matrix is None or len(weights) < 2:
            return 0.0
        
        try:
            avg_correlation = self._get_average_correlation(correlation_matrix, weights)
            return max(0, avg_correlation)  # Higher correlation = higher risk
        except:
            return 0.5  # Default moderate correlation
    
    def _get_average_correlation(
        self,
        correlation_matrix: pd.DataFrame,
        weights: Dict[str, float]
    ) -> float:
        """Get weighted average correlation."""
        try:
            symbols = list(weights.keys())
            if len(symbols) < 2:
                return 0.0
            
            total_correlation = 0
            total_weight_pairs = 0
            
            for i, symbol1 in enumerate(symbols):
                for j, symbol2 in enumerate(symbols):
                    if i != j and symbol1 in correlation_matrix.index and symbol2 in correlation_matrix.columns:
                        correlation = correlation_matrix.loc[symbol1, symbol2]
                        weight_product = weights[symbol1] * weights[symbol2]
                        total_correlation += correlation * weight_product
                        total_weight_pairs += weight_product
            
            return total_correlation / max(total_weight_pairs, 1e-6)
        except:
            return 0.5
    
    def _calculate_tail_risk(
        self,
        asset_risks: Dict[str, RiskMetrics],
        weights: Dict[str, float]
    ) -> float:
        """Calculate tail risk measure."""
        try:
            tail_risk = 0
            for symbol, weight in weights.items():
                if symbol in asset_risks:
                    # Use VaR 99% as tail risk proxy
                    tail_risk += weight * abs(asset_risks[symbol].var_99)
            return tail_risk
        except:
            return 0.1  # Default 10% tail risk
    
    def _perform_stress_tests(
        self,
        weights: Dict[str, float],
        asset_risks: Dict[str, RiskMetrics]
    ) -> Dict[str, float]:
        """Perform stress tests on portfolio."""
        try:
            stress_scenarios = {
                'market_crash_2008': -0.30,
                'covid_crash_2020': -0.25,
                'flash_crash': -0.15,
                'interest_rate_shock': -0.10,
                'inflation_shock': -0.08
            }
            
            stress_results = {}
            
            for scenario, market_shock in stress_scenarios.items():
                portfolio_loss = 0
                for symbol, weight in weights.items():
                    if symbol in asset_risks:
                        # Apply beta adjustment if available
                        beta = asset_risks[symbol].beta or 1.0
                        asset_shock = market_shock * beta
                        portfolio_loss += weight * asset_shock
                
                stress_results[scenario] = portfolio_loss
            
            return stress_results
        except:
            return {
                'market_crash_2008': -0.25,
                'covid_crash_2020': -0.20,
                'flash_crash': -0.12
            }
    
    def _calculate_risk_attribution(
        self,
        weights: Dict[str, float],
        asset_risks: Dict[str, RiskMetrics]
    ) -> Dict[str, float]:
        """Calculate risk attribution by asset."""
        try:
            risk_contributions = {}
            total_risk = 0
            
            # Calculate each asset's contribution to portfolio risk
            for symbol, weight in weights.items():
                if symbol in asset_risks:
                    # Simple risk contribution: weight * volatility
                    risk_contribution = weight * asset_risks[symbol].volatility
                    risk_contributions[symbol] = risk_contribution
                    total_risk += risk_contribution
            
            # Normalize to percentages
            if total_risk > 0:
                risk_contributions = {
                    symbol: contrib / total_risk 
                    for symbol, contrib in risk_contributions.items()
                }
            
            return risk_contributions
        except:
            # Equal risk attribution as fallback
            return {symbol: 1.0 / len(weights) for symbol in weights.keys()}
    
    def _default_risk_metrics(self, symbol: str) -> RiskMetrics:
        """Return default risk metrics when calculation fails."""
        return RiskMetrics(
            symbol=symbol,
            var_95=-0.05,
            var_99=-0.10,
            expected_shortfall_95=-0.08,
            max_drawdown=0.15,
            volatility=0.20,
            beta=1.0,
            sharpe_ratio=0.5,
            sortino_ratio=0.6,
            calmar_ratio=0.3
        )
    
    def _default_portfolio_risk(self) -> PortfolioRisk:
        """Return default portfolio risk when calculation fails."""
        return PortfolioRisk(
            portfolio_var_95=-0.05,
            portfolio_var_99=-0.10,
            portfolio_expected_shortfall=-0.08,
            concentration_risk=0.5,
            correlation_risk=0.5,
            liquidity_risk=0.3,
            tail_risk=0.1,
            stress_test_results={
                'market_crash_2008': -0.25,
                'covid_crash_2020': -0.20,
                'flash_crash': -0.12
            },
            risk_attribution={}
        )
    
    def update_risk_thresholds(self, new_thresholds: Dict[str, float]):
        """Update risk thresholds."""
        self.risk_thresholds.update(new_thresholds)
        logger.info(f"Updated risk thresholds: {new_thresholds}")
    
    def get_risk_summary(
        self,
        portfolio_risk: PortfolioRisk,
        alerts: List[RiskAlert]
    ) -> Dict[str, Any]:
        """Get a summary of risk metrics and alerts."""
        return {
            'overall_risk_level': self._classify_risk_level(portfolio_risk),
            'key_metrics': {
                'portfolio_var_95': portfolio_risk.portfolio_var_95,
                'concentration_risk': portfolio_risk.concentration_risk,
                'correlation_risk': portfolio_risk.correlation_risk
            },
            'alert_summary': {
                'total_alerts': len(alerts),
                'high_severity': len([a for a in alerts if a.severity == 'high']),
                'medium_severity': len([a for a in alerts if a.severity == 'medium'])
            },
            'recommendations': self._generate_risk_recommendations(portfolio_risk, alerts)
        }
    
    def _classify_risk_level(self, portfolio_risk: PortfolioRisk) -> str:
        """Classify overall portfolio risk level."""
        risk_score = 0
        
        # VaR contribution
        if portfolio_risk.portfolio_var_95 < -0.08:
            risk_score += 3
        elif portfolio_risk.portfolio_var_95 < -0.05:
            risk_score += 2
        else:
            risk_score += 1
        
        # Concentration contribution
        if portfolio_risk.concentration_risk > 0.7:
            risk_score += 3
        elif portfolio_risk.concentration_risk > 0.5:
            risk_score += 2
        else:
            risk_score += 1
        
        # Correlation contribution
        if portfolio_risk.correlation_risk > 0.8:
            risk_score += 2
        elif portfolio_risk.correlation_risk > 0.6:
            risk_score += 1
        
        # Classify based on total score
        if risk_score >= 7:
            return 'high'
        elif risk_score >= 5:
            return 'medium'
        else:
            return 'low'
    
    def _generate_risk_recommendations(
        self,
        portfolio_risk: PortfolioRisk,
        alerts: List[RiskAlert]
    ) -> List[str]:
        """Generate risk management recommendations."""
        recommendations = []
        
        if portfolio_risk.concentration_risk > 0.6:
            recommendations.append("Consider diversifying concentrated positions")
        
        if portfolio_risk.correlation_risk > 0.7:
            recommendations.append("Add assets with lower correlations to reduce correlation risk")
        
        if portfolio_risk.portfolio_var_95 < -0.08:
            recommendations.append("Consider reducing portfolio risk through position sizing or hedging")
        
        high_alerts = [a for a in alerts if a.severity == 'high']
        if len(high_alerts) > 0:
            recommendations.append("Address high-severity risk alerts immediately")
        
        if not recommendations:
            recommendations.append("Portfolio risk levels are within acceptable ranges")
        
        return recommendations