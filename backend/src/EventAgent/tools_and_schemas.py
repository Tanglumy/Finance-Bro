from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import json
import re
from langchain_core.tools import tool


class StockPrice(BaseModel):
    """Schema for stock price data."""
    symbol: str
    price: float
    change: float
    change_percent: float
    volume: int
    timestamp: datetime


class MarketNews(BaseModel):
    """Schema for market news articles."""
    title: str
    summary: str
    url: str
    source: str
    published_at: datetime
    sentiment: Optional[str] = None
    relevance_score: Optional[float] = None


class EconomicIndicator(BaseModel):
    """Schema for economic indicators."""
    indicator_name: str
    value: float
    previous_value: float
    forecast: Optional[float] = None
    release_date: datetime
    importance: str  # HIGH, MEDIUM, LOW


class TechnicalIndicator(BaseModel):
    """Schema for technical analysis indicators."""
    symbol: str
    indicator_type: str
    value: float
    signal: str  # BUY, SELL, NEUTRAL
    timestamp: datetime


@tool
async def get_stock_price(symbol: str) -> Dict[str, Any]:
    """
    Get current stock price and basic information for a given symbol.
    
    Args:
        symbol: Stock symbol (e.g., 'AAPL', 'MSFT')
    
    Returns:
        Dictionary with stock price information
    """
    from EventAgent.financial_data_service import get_financial_service
    
    async with await get_financial_service() as service:
        stock_data = await service.get_stock_quote(symbol)
        return {
            "symbol": stock_data.symbol,
            "price": stock_data.price,
            "change": stock_data.change,
            "change_percent": stock_data.change_percent,
            "volume": stock_data.volume,
            "timestamp": stock_data.timestamp.isoformat(),
            "open": stock_data.open_price,
            "high": stock_data.high_price,
            "low": stock_data.low_price,
            "previous_close": stock_data.previous_close,
            "status": "live_data"
        }


@tool
async def get_market_news(
    symbols: Optional[List[str]] = None, 
    hours_back: int = 24,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Get market news articles related to specific symbols or general market news.
    
    Args:
        symbols: List of stock symbols to filter news for
        hours_back: How many hours back to search for news
        limit: Maximum number of news articles to return
    
    Returns:
        List of news articles with metadata
    """
    from EventAgent.financial_data_service import get_financial_service
    
    async with await get_financial_service() as service:
        news_articles = await service.get_market_news(symbols, hours_back, limit)
        return [
            {
                "title": article.title,
                "description": article.description,
                "url": article.url,
                "source": article.source,
                "published_at": article.published_at.isoformat(),
                "sentiment": article.sentiment,
                "relevance_score": article.relevance_score,
                "status": "live_data"
            }
            for article in news_articles
        ]


@tool
async def get_economic_calendar(days_ahead: int = 7) -> List[Dict[str, Any]]:
    """
    Get upcoming economic events and indicators.
    
    Args:
        days_ahead: Number of days ahead to look for economic events
    
    Returns:
        List of economic events and indicators
    """
    from EventAgent.financial_data_service import get_financial_service
    
    async with await get_financial_service() as service:
        indicators = await service.get_economic_calendar(days_ahead)
        return [
            {
                "indicator_name": indicator.indicator_name,
                "value": indicator.value,
                "previous_value": indicator.previous_value,
                "forecast": indicator.forecast,
                "release_date": indicator.release_date.isoformat(),
                "importance": indicator.importance,
                "status": "live_data"
            }
            for indicator in indicators
        ]


@tool
async def calculate_technical_indicators(
    symbol: str, 
    indicators: List[str],
    period: int = 14
) -> List[Dict[str, Any]]:
    """
    Calculate technical indicators for a given symbol.
    
    Args:
        symbol: Stock symbol
        indicators: List of indicators to calculate (RSI, MACD, SMA, etc.)
        period: Period for calculation
    
    Returns:
        List of technical indicator values and signals
    """
    from EventAgent.financial_data_service import get_financial_service
    
    async with await get_financial_service() as service:
        technical_data = await service.get_technical_indicators(symbol, indicators, period)
        results = []
        
        for indicator, data in technical_data.items():
            # Determine signal based on indicator value
            signal = "NEUTRAL"
            if indicator.upper() == "RSI":
                if data["value"] > 70:
                    signal = "SELL"
                elif data["value"] < 30:
                    signal = "BUY"
            elif indicator.upper() == "MACD":
                if data["value"] > 0:
                    signal = "BUY"
                elif data["value"] < 0:
                    signal = "SELL"
            
            results.append({
                "symbol": symbol,
                "indicator_type": indicator,
                "value": data["value"],
                "signal": signal,
                "timestamp": data["timestamp"],
                "status": "live_data"
            })
        
        return results


@tool
async def analyze_market_sentiment(
    sources: List[str] = ["news", "social", "analyst_ratings"]
) -> Dict[str, Any]:
    """
    Analyze overall market sentiment from various sources.
    
    Args:
        sources: List of sources to analyze sentiment from
    
    Returns:
        Market sentiment analysis results
    """
    from EventAgent.financial_data_service import get_financial_service
    
    async with await get_financial_service() as service:
        sentiment_data = await service.analyze_market_sentiment()
        sentiment_data["sources_analyzed"] = sources
        sentiment_data["status"] = "live_data"
        return sentiment_data


@tool
def detect_market_events(
    event_types: List[str] = ["earnings", "fed_announcements", "geopolitical"],
    significance_threshold: float = 0.7
) -> List[Dict[str, Any]]:
    """
    Detect significant market events that could impact trading decisions.
    
    Args:
        event_types: Types of events to monitor
        significance_threshold: Minimum significance score to include events
    
    Returns:
        List of detected market events
    """
    # TODO: Implement actual event detection logic
    return [
        {
            "event_id": "evt_001",
            "timestamp": datetime.now().isoformat(),
            "event_type": "earnings",
            "description": "Apple Inc. reports quarterly earnings",
            "affected_markets": ["AAPL", "QQQ", "SPY"],
            "severity": "medium",
            "significance_score": 0.8,
            "source": "earnings_calendar",
            "status": "mock_data"
        }
    ]


@tool
async def get_portfolio_metrics(portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate portfolio performance metrics and risk analysis.
    
    Args:
        portfolio_data: Current portfolio holdings and values
    
    Returns:
        Portfolio metrics and analysis
    """
    from EventAgent.portfolio_manager import get_portfolio_manager
    from EventAgent.financial_data_service import get_financial_service
    
    portfolio_manager = get_portfolio_manager()
    
    # Get current prices for all positions
    symbols = list(portfolio_manager.positions.keys())
    price_data = {}
    
    if symbols:
        async with await get_financial_service() as service:
            for symbol in symbols:
                stock_data = await service.get_stock_quote(symbol)
                price_data[symbol] = stock_data.price
    
    # Get comprehensive analysis
    analysis = await portfolio_manager.get_comprehensive_analysis(price_data)
    
    return {
        "total_value": analysis.current_value,
        "cash_balance": analysis.cash_balance,
        "invested_capital": analysis.invested_capital,
        "total_pnl": analysis.total_pnl,
        "daily_pnl_percent": analysis.total_pnl_percent,
        "risk_metrics": {
            "beta": analysis.risk_metrics.beta,
            "sharpe_ratio": analysis.risk_metrics.sharpe_ratio,
            "max_drawdown": analysis.risk_metrics.max_drawdown,
            "volatility": analysis.risk_metrics.volatility,
            "value_at_risk_95": analysis.risk_metrics.value_at_risk_95,
            "sortino_ratio": analysis.risk_metrics.sortino_ratio
        },
        "performance_metrics": {
            "total_return": analysis.performance_metrics.total_return,
            "annualized_return": analysis.performance_metrics.annualized_return,
            "ytd_return": analysis.performance_metrics.ytd_return,
            "win_rate": analysis.performance_metrics.win_rate,
            "profit_factor": analysis.performance_metrics.profit_factor
        },
        "diversification_score": analysis.diversification_score,
        "concentration_risk": analysis.concentration_risk,
        "sector_allocation": analysis.sector_allocation,
        "rebalancing_needed": analysis.rebalancing_needed,
        "recommendations": analysis.recommendations,
        "positions": [
            {
                "symbol": pos.symbol,
                "quantity": pos.quantity,
                "current_price": pos.current_price,
                "market_value": pos.market_value,
                "unrealized_pnl": pos.unrealized_pnl,
                "unrealized_pnl_percent": pos.unrealized_pnl_percent,
                "sector": pos.sector
            }
            for pos in analysis.positions
        ],
        "status": "live_data"
    }


@tool
async def add_portfolio_position(
    symbol: str, 
    quantity: float, 
    price: float,
    sector: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add a new position to the portfolio.
    
    Args:
        symbol: Stock symbol
        quantity: Number of shares
        price: Price per share
        sector: Optional sector classification
    
    Returns:
        Updated portfolio summary
    """
    from EventAgent.portfolio_manager import get_portfolio_manager
    
    portfolio_manager = get_portfolio_manager()
    portfolio_manager.add_position(symbol, quantity, price, sector)
    
    return {
        "action": "position_added",
        "symbol": symbol,
        "quantity": quantity,
        "price": price,
        "total_cost": quantity * price,
        "portfolio_value": portfolio_manager.get_total_portfolio_value(),
        "cash_balance": portfolio_manager.cash_balance,
        "positions_count": len(portfolio_manager.positions)
    }


@tool
async def remove_portfolio_position(
    symbol: str, 
    quantity: float, 
    price: float
) -> Dict[str, Any]:
    """
    Remove or reduce a position in the portfolio.
    
    Args:
        symbol: Stock symbol
        quantity: Number of shares to sell
        price: Price per share
    
    Returns:
        Updated portfolio summary
    """
    from EventAgent.portfolio_manager import get_portfolio_manager
    
    portfolio_manager = get_portfolio_manager()
    success = portfolio_manager.remove_position(symbol, quantity, price)
    
    if success:
        return {
            "action": "position_removed",
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
            "proceeds": quantity * price,
            "portfolio_value": portfolio_manager.get_total_portfolio_value(),
            "cash_balance": portfolio_manager.cash_balance,
            "positions_count": len(portfolio_manager.positions)
        }
    else:
        return {
            "action": "failed",
            "error": "Insufficient shares or position not found",
            "symbol": symbol,
            "requested_quantity": quantity
        }


@tool
async def analyze_time_series(
    symbol: str,
    analysis_type: str = "trend",
    period_days: int = 90
) -> Dict[str, Any]:
    """
    Perform time series analysis on a stock or portfolio.
    
    Args:
        symbol: Stock symbol or 'PORTFOLIO' for portfolio analysis
        analysis_type: Type of analysis ('trend', 'seasonality', 'volatility', 'forecast')
        period_days: Number of days to analyze
    
    Returns:
        Time series analysis results
    """
    from EventAgent.time_series_analysis import get_time_series_analyzer
    from EventAgent.financial_data_service import get_financial_service
    import pandas as pd
    import numpy as np
    
    analyzer = get_time_series_analyzer()
    
    # Generate mock historical data for now
    # In a real implementation, this would fetch actual historical data
    dates = pd.date_range(
        start=datetime.now() - timedelta(days=period_days), 
        end=datetime.now(), 
        freq='D'
    )
    
    # Mock price data with some realistic patterns
    if symbol == "PORTFOLIO":
        # Portfolio returns
        returns = pd.Series(np.random.normal(0.0008, 0.015, len(dates)), index=dates)
        prices = pd.Series(100 * (1 + returns).cumprod(), index=dates)
    else:
        # Individual stock data
        returns = pd.Series(np.random.normal(0.001, 0.02, len(dates)), index=dates)
        prices = pd.Series(100 * (1 + returns).cumprod(), index=dates)
    
    results = {}
    
    if analysis_type == "trend":
        trend_analysis = analyzer.analyze_trend(prices)
        results = {
            "analysis_type": "trend",
            "trend_direction": trend_analysis.trend_direction,
            "trend_strength": trend_analysis.trend_strength,
            "trend_slope": trend_analysis.trend_slope,
            "r_squared": trend_analysis.r_squared,
            "support_level": trend_analysis.support_level,
            "resistance_level": trend_analysis.resistance_level
        }
    
    elif analysis_type == "seasonality":
        seasonality_analysis = analyzer.analyze_seasonality(returns)
        results = {
            "analysis_type": "seasonality",
            "has_seasonality": seasonality_analysis.has_seasonality,
            "seasonal_pattern": seasonality_analysis.seasonal_pattern,
            "seasonal_strength": seasonality_analysis.seasonal_strength,
            "best_performing_period": seasonality_analysis.best_performing_period,
            "worst_performing_period": seasonality_analysis.worst_performing_period
        }
    
    elif analysis_type == "volatility":
        volatility_analysis = analyzer.analyze_volatility(returns)
        results = {
            "analysis_type": "volatility",
            "current_volatility": volatility_analysis.current_volatility,
            "volatility_percentile": volatility_analysis.volatility_percentile,
            "volatility_regime": volatility_analysis.volatility_regime,
            "volatility_clustering": volatility_analysis.volatility_clustering
        }
    
    elif analysis_type == "forecast":
        forecast = analyzer.simple_forecast(prices, forecast_horizon=10)
        results = {
            "analysis_type": "forecast",
            "method": forecast.method,
            "forecast_values": forecast.forecast_values,
            "forecast_dates": forecast.forecast_dates,
            "confidence_intervals": forecast.confidence_intervals,
            "accuracy_metrics": forecast.accuracy_metrics
        }
    
    elif analysis_type == "metrics":
        metrics = analyzer.calculate_metrics(returns)
        results = {
            "analysis_type": "comprehensive_metrics",
            "mean_return": metrics.mean_return,
            "volatility": metrics.volatility,
            "skewness": metrics.skewness,
            "kurtosis": metrics.kurtosis,
            "is_stationary": metrics.is_stationary,
            "max_drawdown": metrics.max_drawdown,
            "calmar_ratio": metrics.calmar_ratio,
            "autocorrelation_lag1": metrics.autocorrelation_lag1
        }
    
    results.update({
        "symbol": symbol,
        "period_days": period_days,
        "data_points": len(prices),
        "current_price": prices.iloc[-1] if len(prices) > 0 else 0,
        "status": "analysis_complete"
    })
    
    return results


@tool
async def execute_trading_signal(
    signal_data: Dict[str, Any],
    enable_execution: bool = False
) -> Dict[str, Any]:
    """
    Execute a trading signal through the Executive Agent.
    
    Args:
        signal_data: Trading signal with asset, action, quantity, etc.
        enable_execution: Safety flag to enable actual execution
    
    Returns:
        Execution result and status
    """
    from EventAgent.executive_agent import get_executive_agent
    from EventAgent.portfolio_manager import get_portfolio_manager
    
    executive_agent = get_executive_agent(paper_trading=True)
    portfolio_manager = get_portfolio_manager()
    
    if not enable_execution:
        return {
            "action": "simulation_only",
            "message": "Signal processed in simulation mode - no actual trades executed",
            "signal_data": signal_data,
            "enable_execution_flag": False
        }
    
    # Initialize agent if not already done
    if not executive_agent.enabled:
        init_success = await executive_agent.initialize()
        if not init_success:
            return {
                "action": "failed",
                "error": "Failed to initialize Executive Agent",
                "signal_data": signal_data
            }
    
    # Execute the signal
    execution_result = await executive_agent.execute_signal(signal_data, portfolio_manager)
    
    return {
        "action": "execution_attempt",
        "success": execution_result.success,
        "order_id": execution_result.order_id,
        "message": execution_result.message,
        "filled_quantity": execution_result.filled_quantity,
        "average_price": execution_result.average_price,
        "commission": execution_result.commission,
        "error_code": execution_result.error_code,
        "signal_data": signal_data
    }


@tool
async def get_trading_status() -> Dict[str, Any]:
    """
    Get current trading status and execution statistics.
    
    Returns:
        Trading agent status and performance metrics
    """
    from EventAgent.executive_agent import get_executive_agent
    
    executive_agent = get_executive_agent(paper_trading=True)
    status = await executive_agent.get_execution_status()
    
    return {
        "trading_status": status,
        "last_updated": datetime.now().isoformat()
    }


@tool
async def emergency_trading_stop() -> Dict[str, Any]:
    """
    Emergency stop all trading activities.
    
    Returns:
        Emergency stop confirmation and cancelled orders
    """
    from EventAgent.executive_agent import get_executive_agent
    
    executive_agent = get_executive_agent(paper_trading=True)
    stop_result = await executive_agent.emergency_stop()
    
    return {
        "emergency_stop": stop_result,
        "timestamp": datetime.now().isoformat()
    }


@tool
async def update_risk_parameters(
    max_position_size_pct: Optional[float] = None,
    stop_loss_pct: Optional[float] = None,
    take_profit_pct: Optional[float] = None,
    max_daily_loss_pct: Optional[float] = None
) -> Dict[str, Any]:
    """
    Update risk management parameters for trading.
    
    Args:
        max_position_size_pct: Maximum position size as percentage of portfolio
        stop_loss_pct: Stop loss percentage
        take_profit_pct: Take profit percentage
        max_daily_loss_pct: Maximum daily loss percentage
    
    Returns:
        Updated risk parameters
    """
    from EventAgent.executive_agent import get_executive_agent, RiskParameters
    
    executive_agent = get_executive_agent(paper_trading=True)
    
    # Update parameters if provided
    if max_position_size_pct is not None:
        executive_agent.risk_params.max_position_size_pct = max_position_size_pct
    if stop_loss_pct is not None:
        executive_agent.risk_params.stop_loss_pct = stop_loss_pct
    if take_profit_pct is not None:
        executive_agent.risk_params.take_profit_pct = take_profit_pct
    if max_daily_loss_pct is not None:
        executive_agent.risk_params.max_daily_loss_pct = max_daily_loss_pct
    
    return {
        "action": "risk_parameters_updated",
        "current_parameters": {
            "max_position_size_pct": executive_agent.risk_params.max_position_size_pct,
            "stop_loss_pct": executive_agent.risk_params.stop_loss_pct,
            "take_profit_pct": executive_agent.risk_params.take_profit_pct,
            "max_daily_loss_pct": executive_agent.risk_params.max_daily_loss_pct,
            "min_cash_reserve_pct": executive_agent.risk_params.min_cash_reserve_pct,
            "max_sector_concentration_pct": executive_agent.risk_params.max_sector_concentration_pct
        },
        "timestamp": datetime.now().isoformat()
    }


@tool
async def generate_formula_based_signals(
    market_data: Dict[str, Any],
    portfolio_context: Dict[str, Any],
    formula_names: Optional[List[str]] = None,
    symbols: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Generate trading signals using formula-based strategies.
    
    Args:
        market_data: Current market data (prices, indicators, etc.)
        portfolio_context: Portfolio information for position sizing
        formula_names: List of formula names to evaluate (None = all active)
        symbols: List of symbols to evaluate (None = all available)
    
    Returns:
        List of trading signals from formula evaluation
    """
    from EventAgent.formula_handler import get_formula_handler
    from EventAgent.strategy_manager import get_strategy_manager
    
    try:
        formula_handler = get_formula_handler()
        strategy_manager = get_strategy_manager()
        
        signals = []
        
        # If specific formulas provided, evaluate those
        if formula_names:
            for formula_name in formula_names:
                try:
                    formula_signals = await formula_handler.evaluate_formula_strategy(
                        formula_name,
                        market_data,
                        portfolio_context,
                        symbols
                    )
                    signals.extend(formula_signals)
                except Exception as e:
                    logger.error(f"Error evaluating formula {formula_name}: {e}")
        else:
            # Evaluate all active formula strategies
            active_strategies = strategy_manager.get_active_strategies()
            
            for strategy in active_strategies:
                try:
                    strategy_symbols = strategy.symbols if strategy.symbols else symbols
                    
                    formula_signals = await formula_handler.evaluate_formula_strategy(
                        strategy.formula_model_name,
                        market_data,
                        portfolio_context,
                        strategy_symbols
                    )
                    
                    # Record signal generation
                    for signal in formula_signals:
                        strategy_manager.record_signal(
                            strategy.strategy_id,
                            signal.to_dict()
                        )
                    
                    signals.extend(formula_signals)
                    
                except Exception as e:
                    logger.error(f"Error with strategy {strategy.name}: {e}")
                    strategy_manager.record_error(strategy.strategy_id, str(e))
        
        # Convert signals to dictionary format
        return [signal.to_dict() for signal in signals]
        
    except Exception as e:
        logger.error(f"Error generating formula-based signals: {e}")
        return []


# Export all tools for easy import
FINANCIAL_TOOLS = [
    get_stock_price,
    get_market_news,
    get_economic_calendar,
    calculate_technical_indicators,
    analyze_market_sentiment,
    detect_market_events,
    get_portfolio_metrics,
    add_portfolio_position,
    remove_portfolio_position,
    analyze_time_series,
    execute_trading_signal,
    get_trading_status,
    emergency_trading_stop,
    update_risk_parameters,
    generate_formula_based_signals,
]
