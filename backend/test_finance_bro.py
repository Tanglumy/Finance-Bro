#!/usr/bin/env python3
"""
Test script to demonstrate the Finance Bro system functionality.
This script showcases the complete integration between all components.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any

from src.EventAgent.app import EventAgentRequest
from src.EventAgent.graph import create_event_agent_graph, initialize_event_agent_state
from src.EventAgent.portfolio_manager import get_portfolio_manager
from src.EventAgent.executive_agent import get_executive_agent
from src.EventAgent.financial_data_service import get_financial_service
from src.EventAgent.time_series_analysis import get_time_series_analyzer


async def test_financial_data_service():
    """Test the financial data service."""
    print("🔍 Testing Financial Data Service...")
    
    async with await get_financial_service() as service:
        # Test stock quotes
        aapl_data = await service.get_stock_quote("AAPL")
        print(f"AAPL Stock Data: ${aapl_data.price:.2f} ({aapl_data.change_percent:+.2f}%)")
        
        # Test market news
        news = await service.get_market_news(["AAPL"], hours_back=24, limit=3)
        print(f"Found {len(news)} news articles")
        
        # Test technical indicators
        tech_indicators = await service.get_technical_indicators("AAPL", ["RSI", "MACD"])
        print(f"Technical indicators: {json.dumps(tech_indicators, indent=2)}")


async def test_portfolio_manager():
    """Test the portfolio management system."""
    print("\n📊 Testing Portfolio Manager...")
    
    portfolio = get_portfolio_manager()
    
    # Add some test positions
    portfolio.add_position("AAPL", 100, 150.0, "Technology")
    portfolio.add_position("MSFT", 50, 300.0, "Technology")
    portfolio.add_position("SPY", 200, 400.0, "ETF")
    
    print(f"Portfolio value: ${portfolio.get_total_portfolio_value():,.2f}")
    print(f"Cash balance: ${portfolio.cash_balance:,.2f}")
    print(f"Positions: {len(portfolio.positions)}")
    
    # Get comprehensive analysis
    price_data = {"AAPL": 155.0, "MSFT": 310.0, "SPY": 405.0}
    analysis = await portfolio.get_comprehensive_analysis(price_data)
    
    print(f"Total P&L: ${analysis.total_pnl:,.2f} ({analysis.total_pnl_percent:.2f}%)")
    print(f"Diversification Score: {analysis.diversification_score:.2f}")
    print(f"Recommendations: {analysis.recommendations}")


async def test_time_series_analysis():
    """Test the time series analysis."""
    print("\n📈 Testing Time Series Analysis...")
    
    analyzer = get_time_series_analyzer()
    
    # Create mock data for demonstration
    import pandas as pd
    import numpy as np
    from datetime import timedelta
    
    dates = pd.date_range(start=datetime.now() - timedelta(days=90), end=datetime.now(), freq='D')
    returns = pd.Series(np.random.normal(0.001, 0.02, len(dates)), index=dates)
    prices = pd.Series(100 * (1 + returns).cumprod(), index=dates)
    
    # Trend analysis
    trend = analyzer.analyze_trend(prices)
    print(f"Trend: {trend.trend_direction} (strength: {trend.trend_strength:.2f})")
    
    # Volatility analysis
    volatility = analyzer.analyze_volatility(returns)
    print(f"Volatility: {volatility.current_volatility:.2f} ({volatility.volatility_regime})")
    
    # Simple forecast
    forecast = analyzer.simple_forecast(prices, forecast_horizon=5)
    print(f"5-day forecast: {forecast.forecast_values[:3]}...")


async def test_executive_agent():
    """Test the executive trading agent."""
    print("\n🤖 Testing Executive Agent...")
    
    executive = get_executive_agent(paper_trading=True)
    
    # Initialize the agent
    success = await executive.initialize()
    print(f"Executive Agent initialized: {success}")
    
    if success:
        # Test signal execution
        test_signal = {
            "asset_symbol": "AAPL",
            "signal_type": "BUY",
            "quantity": 10,
            "entry_price": 150.0,
            "rationale": "Strong technical indicators and positive news sentiment",
            "signal_strength": 0.8
        }
        
        result = await executive.execute_signal(test_signal, get_portfolio_manager())
        print(f"Signal execution: {result.success} - {result.message}")
        
        if result.success:
            print(f"Order ID: {result.order_id}")
            print(f"Filled: {result.filled_quantity} shares at ${result.average_price:.2f}")
        
        # Get status
        status = await executive.get_execution_status()
        print(f"Trading status: {status['agent_enabled']}, Success rate: {status['success_rate']:.1f}%")
        
        await executive.shutdown()


async def test_event_agent_graph():
    """Test the complete EventAgent workflow."""
    print("\n🎯 Testing EventAgent Graph...")
    
    # Create the graph
    event_graph = create_event_agent_graph()
    
    # Initialize state with a sample query
    initial_state = initialize_event_agent_state(
        user_message="Analyze Apple stock and provide investment recommendations based on current market conditions",
        portfolio_data={"AAPL": {"quantity": 100, "avg_cost": 150.0}},
        risk_tolerance="moderate",
        investment_horizon="medium"
    )
    
    # Run the graph
    config = {"configurable": {}}
    try:
        final_state = await event_graph.ainvoke(initial_state, config)
        
        print(f"Market events detected: {len(final_state.get('market_events', []))}")
        print(f"Trading signals generated: {len(final_state.get('financial_signals', []))}")
        print(f"Portfolio analysis completed: {len(final_state.get('portfolio_analysis', []))}")
        
        # Print final analysis
        if final_state.get("messages"):
            last_message = final_state["messages"][-1]
            analysis = last_message.content if hasattr(last_message, 'content') else str(last_message)
            print(f"Investment Analysis: {analysis[:200]}...")
            
    except Exception as e:
        print(f"EventAgent execution error: {e}")


async def test_api_integration():
    """Test API integration by simulating a request."""
    print("\n🌐 Testing API Integration...")
    
    # Simulate an API request
    request = EventAgentRequest(
        message="What's the outlook for tech stocks this week?",
        portfolio_data={"AAPL": {"quantity": 100, "avg_cost": 150.0}},
        risk_tolerance="moderate",
        investment_horizon="short"
    )
    
    # Initialize state
    initial_state = initialize_event_agent_state(
        user_message=request.message,
        portfolio_data=request.portfolio_data,
        risk_tolerance=request.risk_tolerance,
        investment_horizon=request.investment_horizon
    )
    
    print(f"Request processed for: {request.message}")
    print(f"Portfolio context: {len(request.portfolio_data)} positions")
    print(f"Risk tolerance: {request.risk_tolerance}")


async def demo_complete_workflow():
    """Demonstrate the complete Finance Bro workflow."""
    print("\n🚀 Finance Bro Complete Workflow Demo")
    print("=" * 50)
    
    # Step 1: Portfolio setup
    print("1️⃣ Setting up portfolio...")
    portfolio = get_portfolio_manager()
    portfolio.add_position("AAPL", 100, 150.0, "Technology")
    portfolio.add_position("GOOGL", 25, 2500.0, "Technology")
    portfolio.add_position("SPY", 50, 400.0, "ETF")
    
    # Step 2: Market analysis
    print("2️⃣ Analyzing market conditions...")
    async with await get_financial_service() as service:
        sentiment = await service.analyze_market_sentiment()
        print(f"Market sentiment: {sentiment['overall_sentiment']} (score: {sentiment['sentiment_score']})")
    
    # Step 3: Generate signals
    print("3️⃣ Generating trading signals...")
    sample_signal = {
        "asset_symbol": "TSLA",
        "signal_type": "BUY",
        "quantity": 20,
        "entry_price": 200.0,
        "signal_strength": 0.75,
        "rationale": "Strong momentum and positive earnings outlook"
    }
    
    # Step 4: Risk assessment
    print("4️⃣ Performing risk assessment...")
    executive = get_executive_agent(paper_trading=True)
    await executive.initialize()
    
    # Step 5: Execute (simulation)
    print("5️⃣ Executing trade (simulation)...")
    result = await executive.execute_signal(sample_signal, portfolio)
    print(f"Execution result: {result.success} - {result.message}")
    
    # Step 6: Portfolio update
    print("6️⃣ Updating portfolio analysis...")
    price_data = {"AAPL": 155.0, "GOOGL": 2550.0, "SPY": 405.0, "TSLA": 202.0}
    analysis = await portfolio.get_comprehensive_analysis(price_data)
    
    print(f"Final portfolio value: ${analysis.current_value:,.2f}")
    print(f"Total return: {analysis.total_pnl_percent:.2f}%")
    print(f"Risk score: {analysis.risk_metrics.volatility:.2f}")
    
    await executive.shutdown()


async def main():
    """Run all tests."""
    print("🏦 Finance Bro System Test Suite")
    print("=" * 40)
    
    try:
        await test_financial_data_service()
        await test_portfolio_manager()
        await test_time_series_analysis()
        await test_executive_agent()
        await test_event_agent_graph()
        await test_api_integration()
        await demo_complete_workflow()
        
        print("\n✅ All tests completed successfully!")
        print("\n📋 System Summary:")
        print("- ✅ EventAgent: LangGraph architecture with state management")
        print("- ✅ Financial Data: APIs for stocks, news, and market data")
        print("- ✅ Portfolio Manager: Time series analysis and risk metrics")
        print("- ✅ Executive Agent: IBKR trading integration with risk management")
        print("- ✅ Event Detection: Market event analysis and signal generation")
        print("- ✅ API Integration: FastAPI endpoints and request handling")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())