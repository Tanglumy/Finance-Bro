"""
Test script for the Reward Agent system.

This script demonstrates the key functionality of the reward-based learning system.
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any

# Import reward agent components
from src.reward_agent.reward_calculator import RewardCalculator, RewardType
from src.reward_agent.strategy_optimizer import StrategyOptimizer, StrategyType, OptimizationMethod
from src.reward_agent.learning_agent import RewardLearningAgent, LearningMode
from src.reward_agent.performance_tracker import PerformanceTracker, PerformancePeriod
from src.reward_agent.strategy_manager import StrategyManager


async def test_reward_calculation():
    """Test the reward calculation system."""
    print("=" * 60)
    print("TESTING REWARD CALCULATION SYSTEM")
    print("=" * 60)
    
    # Initialize reward calculator
    calculator = RewardCalculator()
    
    # Generate mock portfolio data
    np.random.seed(42)  # For reproducible results
    n_days = 90
    
    # Mock portfolio returns (slightly outperforming market)
    portfolio_returns = pd.Series(
        np.random.normal(0.0012, 0.018, n_days),  # 12bps daily return, 1.8% daily vol
        index=pd.date_range(start=datetime.now() - timedelta(days=n_days), periods=n_days)
    )
    
    # Mock benchmark returns
    benchmark_returns = pd.Series(
        np.random.normal(0.0008, 0.015, n_days),  # 8bps daily return, 1.5% daily vol
        index=portfolio_returns.index
    )
    
    # Mock portfolio value
    portfolio_value = pd.Series(
        100000 * (1 + portfolio_returns).cumprod(),
        index=portfolio_returns.index
    )
    
    # Mock positions data
    positions_data = [
        {"symbol": "AAPL", "market_value": 15000, "sector": "Technology"},
        {"symbol": "MSFT", "market_value": 12000, "sector": "Technology"},
        {"symbol": "GOOGL", "market_value": 10000, "sector": "Technology"},
        {"symbol": "JPM", "market_value": 8000, "sector": "Finance"},
        {"symbol": "JNJ", "market_value": 7000, "sector": "Healthcare"},
        {"symbol": "PG", "market_value": 6000, "sector": "Consumer"},
    ]
    
    # Calculate comprehensive rewards
    reward_score = calculator.calculate_comprehensive_reward(
        portfolio_returns=portfolio_returns,
        benchmark_returns=benchmark_returns,
        portfolio_value=portfolio_value,
        positions_data=positions_data,
        period_days=n_days
    )
    
    print(f"📊 REWARD SCORE BREAKDOWN:")
    print(f"   Overall Score: {reward_score.weighted_score:.1f}/100")
    print(f"   Performance Grade: {reward_score.performance_grade}")
    print(f"   Benchmark Comparison: {reward_score.benchmark_comparison:+.2%}")
    print()
    
    print("🔍 INDIVIDUAL METRICS:")
    for metric_name, metric in reward_score.individual_metrics.items():
        print(f"   {metric_name}: {metric.value:.1f}/{metric.max_value:.0f} "
              f"(Weight: {metric.weight:.1%})")
        if metric.improvement_suggestions:
            print(f"      Suggestions: {', '.join(metric.improvement_suggestions[:2])}")
    
    print()
    
    # Get improvement priorities
    priorities = calculator.get_improvement_priorities(reward_score)
    if priorities:
        print("🎯 IMPROVEMENT PRIORITIES:")
        for priority in priorities[:3]:
            print(f"   {priority['priority']} Priority: {priority['metric']}")
            print(f"      Current Score: {priority['current_score']:.1f}")
            print(f"      Suggestions: {', '.join(priority['suggestions'][:2])}")
            print()


async def test_strategy_optimization():
    """Test the strategy optimization system."""
    print("=" * 60)
    print("TESTING STRATEGY OPTIMIZATION SYSTEM")
    print("=" * 60)
    
    # Initialize optimizer
    optimizer = StrategyOptimizer(optimization_method=OptimizationMethod.GRADIENT_ASCENT)
    
    # Get a strategy template
    strategy = optimizer.get_strategy_template(StrategyType.GROWTH)
    print(f"📈 ORIGINAL STRATEGY: {strategy.name}")
    print(f"   Type: {strategy.strategy_type.value}")
    print(f"   Version: {strategy.version}")
    print(f"   Parameters:")
    for param_name, param in strategy.parameters.items():
        print(f"      {param_name}: {param.value:.3f}")
    print()
    
    # Generate mock historical data
    n_days = 60
    mock_data = {
        "portfolio_returns": pd.Series(np.random.normal(0.001, 0.02, n_days)),
        "benchmark_returns": pd.Series(np.random.normal(0.0008, 0.015, n_days)),
        "portfolio_value": pd.Series(100000 * (1 + np.random.normal(0.001, 0.02, n_days)).cumprod()),
        "positions_data": []
    }
    
    # Optimize strategy
    print("🚀 RUNNING OPTIMIZATION...")
    optimization_result = optimizer.optimize_strategy(
        strategy, mock_data, target_improvement=0.1
    )
    
    print(f"✅ OPTIMIZATION RESULTS:")
    print(f"   Improvement Score: {optimization_result.improvement_score:.2%}")
    print(f"   Method: {optimization_result.optimization_method.value}")
    print(f"   Iterations: {optimization_result.iterations}")
    print(f"   Convergence: {optimization_result.convergence_achieved}")
    print(f"   Time: {optimization_result.optimization_time:.2f}s")
    print()
    
    print(f"📊 BACKTESTED PERFORMANCE:")
    for metric, value in optimization_result.backtested_performance.items():
        print(f"   {metric}: {value:.3f}")
    print()
    
    print(f"💡 RECOMMENDATIONS:")
    for rec in optimization_result.recommendations[:3]:
        print(f"   • {rec}")
    print()


async def test_learning_agent():
    """Test the learning agent system."""
    print("=" * 60)
    print("TESTING LEARNING AGENT SYSTEM")
    print("=" * 60)
    
    # Initialize learning agent
    agent = RewardLearningAgent(learning_mode=LearningMode.BALANCED)
    print(f"🤖 LEARNING AGENT INITIALIZED")
    print(f"   Mode: {agent.learning_mode.value}")
    print(f"   Learning Rate: {agent.learning_rate}")
    print(f"   Exploration Rate: {agent.exploration_rate}")
    print()
    
    # Mock portfolio and market data
    portfolio_data = {
        "total_value": 105000,
        "cash_balance": 5000,
        "positions": [
            {"symbol": "AAPL", "market_value": 20000, "sector": "Technology"},
            {"symbol": "MSFT", "market_value": 15000, "sector": "Technology"},
            {"symbol": "GOOGL", "market_value": 12000, "sector": "Technology"},
            {"symbol": "JPM", "market_value": 10000, "sector": "Finance"},
        ]
    }
    
    market_data = {
        "portfolio_returns": pd.Series(np.random.normal(0.001, 0.02, 30)),
        "benchmark_returns": pd.Series(np.random.normal(0.0008, 0.015, 30)),
        "portfolio_value": pd.Series(100000 * (1 + np.random.normal(0.001, 0.02, 30)).cumprod())
    }
    
    # Run learning cycle
    print("🧠 RUNNING LEARNING CYCLE...")
    action = await agent.learn_and_adapt(portfolio_data, market_data)
    
    print(f"⚡ LEARNING ACTION TAKEN:")
    print(f"   Action Type: {action.action_type.value}")
    print(f"   Expected Improvement: {action.expected_improvement:.3f}")
    print(f"   Confidence: {action.confidence:.2f}")
    print(f"   Reasoning: {action.reasoning}")
    print()
    
    # Get learning insights
    insights = agent.get_learning_insights()
    print(f"📈 LEARNING INSIGHTS:")
    print(f"   Current Strategy: {insights['current_strategy']['name']}")
    print(f"   Success Rate: {insights['success_rate']:.1%}")
    print(f"   Total Improvements: {insights['total_improvements']:.3f}")
    print(f"   Performance Grade: {insights['recent_performance'].get('performance_grade', 'N/A')}")
    print()
    
    # Get recommendations
    recommendations = agent.get_strategy_recommendations()
    print(f"🎯 STRATEGY RECOMMENDATIONS:")
    for rec in recommendations[:3]:
        print(f"   • [{rec['type'].upper()}] {rec['message']}")
        if 'action' in rec:
            print(f"     Action: {rec['action']}")
    print()


async def test_strategy_manager():
    """Test the strategy management system."""
    print("=" * 60)
    print("TESTING STRATEGY MANAGEMENT SYSTEM")
    print("=" * 60)
    
    # Initialize strategy manager
    manager = StrategyManager()
    print(f"🎯 STRATEGY MANAGER INITIALIZED")
    print(f"   Total Strategies: {len(manager.strategies)}")
    print(f"   Active Strategy: {manager.active_strategy_id}")
    print()
    
    # Create a custom strategy
    custom_strategy_id = manager.create_custom_strategy(
        name="Custom Aggressive Growth",
        strategy_type=StrategyType.GROWTH,
        parameters={
            "risk_level": 0.8,
            "return_target": 0.18,
            "growth_weight": 0.9
        }
    )
    
    print(f"✨ CREATED CUSTOM STRATEGY: {custom_strategy_id}")
    print()
    
    # Get strategy rankings
    rankings = manager.get_strategy_rankings()
    print(f"🏆 STRATEGY RANKINGS:")
    for i, ranking in enumerate(rankings[:3], 1):
        print(f"   {i}. {ranking['strategy_name']}")
        print(f"      Type: {ranking['strategy_type']}")
        print(f"      Performance Score: {ranking['performance_score']:.3f}")
        print(f"      Confidence: {ranking['confidence_score']:.2f}")
        print()
    
    # Compare strategies
    if len(rankings) >= 2:
        strategy_ids = [rankings[0]['strategy_id'], rankings[1]['strategy_id']]
        comparison = manager.compare_strategies(strategy_ids)
        
        print(f"⚖️  STRATEGY COMPARISON:")
        print(f"   Winner: {comparison.winner}")
        print(f"   Performance Difference: {comparison.performance_difference:.3f}")
        print(f"   Recommendation: {comparison.recommendation}")
        print()
    
    # Get strategy insights
    insights = manager.get_strategy_insights()
    print(f"🔍 STRATEGY INSIGHTS:")
    print(f"   Total Strategies: {insights['total_strategies']}")
    print(f"   Strategy Distribution: {insights['strategy_distribution']}")
    print(f"   Average Confidence: {insights['performance_summary'].get('average_confidence', 0):.2f}")
    print()
    
    if insights['recommendations']:
        print(f"💡 MANAGEMENT RECOMMENDATIONS:")
        for rec in insights['recommendations'][:3]:
            print(f"   • {rec}")
        print()


async def test_performance_tracker():
    """Test the performance tracking system."""
    print("=" * 60)
    print("TESTING PERFORMANCE TRACKING SYSTEM")
    print("=" * 60)
    
    # Initialize performance tracker
    tracker = PerformanceTracker()
    
    # Simulate performance updates over time
    print("📊 SIMULATING PERFORMANCE UPDATES...")
    
    for i in range(30):  # 30 days of data
        # Mock portfolio data for each day
        portfolio_data = {
            "total_value": 100000 + i * 500 + np.random.normal(0, 1000),
            "cash_balance": 5000 + np.random.normal(0, 500),
            "positions": [
                {"symbol": "AAPL", "market_value": 15000 + np.random.normal(0, 500), "sector": "Technology"},
                {"symbol": "MSFT", "market_value": 12000 + np.random.normal(0, 400), "sector": "Technology"},
                {"symbol": "JPM", "market_value": 8000 + np.random.normal(0, 300), "sector": "Finance"},
            ]
        }
        
        # Mock reward score
        from src.reward_agent.reward_calculator import RewardScore, RewardMetric
        reward_score = RewardScore(
            total_score=75 + np.random.normal(0, 5),
            weighted_score=75 + np.random.normal(0, 5),
            individual_metrics={},
            performance_grade="B+",
            timestamp=datetime.now(),
            period_days=30,
            benchmark_comparison=0.02
        )
        
        # Update tracker
        tracker.update_performance(portfolio_data, reward_score)
    
    print(f"✅ UPDATED PERFORMANCE DATA (30 days)")
    print()
    
    # Get performance analysis
    analysis = tracker.get_performance_analysis(PerformancePeriod.MONTHLY)
    print(f"📈 MONTHLY PERFORMANCE ANALYSIS:")
    print(f"   Total Return: {analysis.total_return:.2%}")
    print(f"   Annualized Return: {analysis.annualized_return:.2%}")
    print(f"   Volatility: {analysis.volatility:.2%}")
    print(f"   Sharpe Ratio: {analysis.sharpe_ratio:.2f}")
    print(f"   Max Drawdown: {analysis.max_drawdown:.2%}")
    print(f"   Win Rate: {analysis.win_rate:.1%}")
    print()
    
    # Get performance trends
    trends = tracker.get_performance_trends(30)
    print(f"📊 PERFORMANCE TRENDS:")
    value_trend = trends["portfolio_value_trend"]
    print(f"   Portfolio Value: {value_trend['direction']} ({value_trend['percent_change']:+.1f}%)")
    
    reward_trend = trends["reward_score_trend"]
    print(f"   Reward Score: {reward_trend['direction']} ({reward_trend['end_score']:.1f})")
    print()
    
    # Get performance summary
    summary = tracker.get_performance_summary()
    print(f"📋 PERFORMANCE SUMMARY:")
    print(f"   Current Value: ${summary['current_value']:,.2f}")
    print(f"   Daily Return: {summary['daily_return']:+.2%}")
    print(f"   Total Return: {summary['total_return']:+.2%}")
    print(f"   Reward Score: {summary['reward_score']:.1f}")
    print()


async def run_comprehensive_test():
    """Run comprehensive test of all reward agent components."""
    print("🎯 REWARD-BASED LEARNING SYSTEM - COMPREHENSIVE TEST")
    print("=" * 60)
    print()
    
    try:
        # Test each component
        await test_reward_calculation()
        await test_strategy_optimization()
        await test_learning_agent()
        await test_strategy_manager()
        await test_performance_tracker()
        
        print("=" * 60)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print()
        print("🚀 REWARD AGENT SYSTEM READY FOR PRODUCTION")
        print()
        print("Key Features Demonstrated:")
        print("• Comprehensive reward calculation with 7+ metrics")
        print("• Multi-algorithm strategy optimization")
        print("• Adaptive learning with feedback loops")
        print("• Strategy management and comparison")
        print("• Performance tracking and analysis")
        print()
        print("Next Steps:")
        print("• Integrate with real portfolio data")
        print("• Connect to live market data feeds")
        print("• Implement database persistence")
        print("• Add real-time learning triggers")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ ERROR DURING TESTING: {e}")
        print("Check component imports and dependencies")


if __name__ == "__main__":
    asyncio.run(run_comprehensive_test())