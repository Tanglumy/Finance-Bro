#!/usr/bin/env python3
"""
End-to-End Test Script for Finance-Bro with Real OpenAI API
Tests all agents with concrete financial scenarios using GPT-5.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import configuration
from config import config
config.validate()

# Test scenarios with concrete financial cases
TEST_SCENARIOS = {
    "market_analysis": {
        "description": "Analyze tech sector during earnings season",
        "input": {
            "message": "Analyze the current market conditions for tech stocks like AAPL, MSFT, GOOGL during Q4 earnings season. What are the key risks and opportunities?",
            "portfolio_data": {
                "holdings": {"AAPL": 100, "MSFT": 50, "GOOGL": 25},
                "cash_balance": 50000,
                "total_value": 150000
            },
            "risk_tolerance": "moderate",
            "investment_horizon": "medium"
        },
        "expected_outputs": ["analysis", "market_events", "trading_signals", "portfolio_recommendations"]
    },
    
    "research_analysis": {
        "description": "Deep research on Apple Inc.",
        "input": {
            "symbol": "AAPL",
            "research_type": "fundamental",
            "include_competitors": True,
            "time_horizon": "12_months"
        },
        "expected_outputs": ["company_overview", "financial_metrics", "competitive_analysis", "price_target"]
    },
    
    "time_series_prediction": {
        "description": "Predict TSLA stock price for next 30 days",
        "input": {
            "symbol": "TSLA",
            "prediction_days": 30,
            "model_type": "ensemble",
            "include_technical_indicators": True
        },
        "expected_outputs": ["predictions", "confidence_intervals", "model_accuracy", "risk_factors"]
    },
    
    "strategy_backtest": {
        "description": "Test momentum strategy on QQQ",
        "input": {
            "strategy_name": "Tech Momentum Strategy",
            "formula": """
# Tech sector momentum strategy
BUY_SIGNAL = (RSI(14) < 30) AND (SMA(10) > SMA(50)) AND (VOLUME > SMA_VOL(20) * 1.5)
SELL_SIGNAL = (RSI(14) > 70) OR (SMA(10) < SMA(50))
POSITION_SIZE = 0.1  # 10% of portfolio
""",
            "symbol": "QQQ",
            "backtest_period": "1Y",
            "initial_capital": 100000
        },
        "expected_outputs": ["total_return", "sharpe_ratio", "max_drawdown", "win_rate", "trade_history"]
    },
    
    "reward_optimization": {
        "description": "Optimize portfolio allocation using reward learning",
        "input": {
            "current_portfolio": {
                "AAPL": 0.3,
                "MSFT": 0.25,
                "GOOGL": 0.2,
                "AMZN": 0.15,
                "CASH": 0.1
            },
            "risk_budget": 0.15,
            "return_target": 0.12,
            "rebalance_frequency": "monthly"
        },
        "expected_outputs": ["optimal_allocation", "expected_return", "risk_metrics", "rebalancing_schedule"]
    }
}

class E2ETestRunner:
    """End-to-end test runner for Finance-Bro agents"""
    
    def __init__(self):
        self.results = {}
        self.errors = []
        
    async def test_event_agent(self, scenario_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test EventAgent with market analysis scenario"""
        logger.info("Testing EventAgent with real GPT-5...")
        
        try:
            # Import and initialize EventAgent
            from src.EventAgent.app import EventAgentApp
            from src.EventAgent.configuration import EventAgentConfiguration
            
            # Create configuration with our API key
            config_data = EventAgentConfiguration()
            app = EventAgentApp(config_data)
            
            # Run analysis
            input_data = scenario_data["input"]
            result = await app.analyze_market(
                message=input_data["message"],
                portfolio_data=input_data.get("portfolio_data"),
                risk_tolerance=input_data.get("risk_tolerance"),
                investment_horizon=input_data.get("investment_horizon")
            )
            
            # Validate expected outputs
            expected = scenario_data["expected_outputs"]
            validation = self._validate_outputs(result, expected)
            
            return {
                "status": "success",
                "result": result,
                "validation": validation,
                "test_case": "EventAgent - Tech sector analysis during earnings"
            }
            
        except Exception as e:
            error_msg = f"EventAgent test failed: {str(e)}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return {"status": "error", "error": error_msg}
    
    async def test_research_agent(self, scenario_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test Research_Agent with stock research scenario"""
        logger.info("Testing Research_Agent with real GPT-5...")
        
        try:
            from src.Research_Agent.app import ResearchAgentApp
            from src.Research_Agent.configuration import Configuration
            
            config_data = Configuration()
            app = ResearchAgentApp(config_data)
            
            input_data = scenario_data["input"]
            result = await app.research_stock(
                symbol=input_data["symbol"],
                research_type=input_data.get("research_type"),
                include_competitors=input_data.get("include_competitors"),
                time_horizon=input_data.get("time_horizon")
            )
            
            expected = scenario_data["expected_outputs"]
            validation = self._validate_outputs(result, expected)
            
            return {
                "status": "success",
                "result": result,
                "validation": validation,
                "test_case": "Research_Agent - AAPL fundamental analysis"
            }
            
        except Exception as e:
            error_msg = f"Research_Agent test failed: {str(e)}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return {"status": "error", "error": error_msg}
    
    async def test_ts_agent(self, scenario_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test time series prediction agent"""
        logger.info("Testing ts_agent with real market data...")
        
        try:
            from src.ts_agent.predictor import TimeSeriesPredictor
            from src.ts_agent.data_manager import DataManager
            
            data_manager = DataManager()
            predictor = TimeSeriesPredictor()
            
            input_data = scenario_data["input"]
            
            # Get historical data
            historical_data = data_manager.get_stock_data(
                symbol=input_data["symbol"],
                period="2Y"  # 2 years of data for training
            )
            
            # Make prediction
            result = await predictor.predict(
                data=historical_data,
                symbol=input_data["symbol"],
                prediction_days=input_data["prediction_days"],
                model_type=input_data.get("model_type", "ensemble")
            )
            
            expected = scenario_data["expected_outputs"]
            validation = self._validate_outputs(result, expected)
            
            return {
                "status": "success",
                "result": result,
                "validation": validation,
                "test_case": "ts_agent - TSLA 30-day price prediction"
            }
            
        except Exception as e:
            error_msg = f"ts_agent test failed: {str(e)}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return {"status": "error", "error": error_msg}
    
    async def test_formula_engine(self, scenario_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test formula engine with strategy backtesting"""
        logger.info("Testing formula_engine with momentum strategy...")
        
        try:
            from src.formula_engine.engine import FormulaEngine
            from src.formula_engine.backtester import Backtester
            
            engine = FormulaEngine()
            backtester = Backtester()
            
            input_data = scenario_data["input"]
            
            # Parse and validate formula
            parsed_strategy = engine.parse_formula(input_data["formula"])
            
            # Run backtest
            result = await backtester.run_backtest(
                strategy=parsed_strategy,
                symbol=input_data["symbol"],
                period=input_data["backtest_period"],
                initial_capital=input_data["initial_capital"]
            )
            
            expected = scenario_data["expected_outputs"]
            validation = self._validate_outputs(result, expected)
            
            return {
                "status": "success",
                "result": result,
                "validation": validation,
                "test_case": "formula_engine - QQQ momentum strategy backtest"
            }
            
        except Exception as e:
            error_msg = f"formula_engine test failed: {str(e)}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return {"status": "error", "error": error_msg}
    
    async def test_reward_agent(self, scenario_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test reward agent with portfolio optimization"""
        logger.info("Testing reward_agent with portfolio optimization...")
        
        try:
            from src.reward_agent.strategy_optimizer import StrategyOptimizer
            from src.reward_agent.learning_agent import LearningAgent
            
            optimizer = StrategyOptimizer()
            learning_agent = LearningAgent()
            
            input_data = scenario_data["input"]
            
            # Optimize portfolio
            result = await optimizer.optimize_portfolio(
                current_allocation=input_data["current_portfolio"],
                risk_budget=input_data["risk_budget"],
                return_target=input_data["return_target"],
                rebalance_frequency=input_data["rebalance_frequency"]
            )
            
            expected = scenario_data["expected_outputs"]
            validation = self._validate_outputs(result, expected)
            
            return {
                "status": "success",
                "result": result,
                "validation": validation,
                "test_case": "reward_agent - Portfolio optimization with risk constraints"
            }
            
        except Exception as e:
            error_msg = f"reward_agent test failed: {str(e)}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return {"status": "error", "error": error_msg}
    
    def _validate_outputs(self, result: Any, expected_keys: List[str]) -> Dict[str, bool]:
        """Validate that result contains expected output keys"""
        validation = {}
        
        if isinstance(result, dict):
            for key in expected_keys:
                validation[key] = key in result and result[key] is not None
        else:
            # For non-dict results, check if they exist and are not None
            validation["result_exists"] = result is not None
            
        return validation
    
    async def run_full_e2e_test(self) -> Dict[str, Any]:
        """Run complete end-to-end test suite"""
        logger.info("Starting full E2E test suite with real OpenAI GPT-5...")
        
        start_time = datetime.now()
        
        # Test each agent
        test_functions = [
            ("EventAgent", self.test_event_agent, TEST_SCENARIOS["market_analysis"]),
            ("Research_Agent", self.test_research_agent, TEST_SCENARIOS["research_analysis"]),
            ("ts_agent", self.test_ts_agent, TEST_SCENARIOS["time_series_prediction"]),
            ("formula_engine", self.test_formula_engine, TEST_SCENARIOS["strategy_backtest"]),
            ("reward_agent", self.test_reward_agent, TEST_SCENARIOS["reward_optimization"])
        ]
        
        for agent_name, test_func, scenario in test_functions:
            logger.info(f"Testing {agent_name}...")
            try:
                self.results[agent_name] = await test_func(scenario)
            except Exception as e:
                self.results[agent_name] = {
                    "status": "error",
                    "error": f"Failed to test {agent_name}: {str(e)}"
                }
                self.errors.append(f"{agent_name}: {str(e)}")
        
        end_time = datetime.now()
        test_duration = (end_time - start_time).total_seconds()
        
        # Generate summary
        summary = self._generate_test_summary(test_duration)
        
        return {
            "summary": summary,
            "detailed_results": self.results,
            "errors": self.errors,
            "test_duration_seconds": test_duration,
            "timestamp": end_time.isoformat()
        }
    
    def _generate_test_summary(self, duration: float) -> Dict[str, Any]:
        """Generate test execution summary"""
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results.values() if r.get("status") == "success")
        failed_tests = total_tests - successful_tests
        
        return {
            "total_agents_tested": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": failed_tests,
            "success_rate": f"{(successful_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%",
            "test_duration": f"{duration:.2f} seconds",
            "api_key_configured": bool(config.OPENAI_API_KEY),
            "model_used": "gpt-5"
        }

async def main():
    """Main test execution function"""
    logger.info("Finance-Bro E2E Test Suite Starting...")
    logger.info(f"Using OpenAI API Key: {'✓ Configured' if config.OPENAI_API_KEY else '✗ Missing'}")
    logger.info(f"Using Model: gpt-5")
    
    test_runner = E2ETestRunner()
    
    try:
        results = await test_runner.run_full_e2e_test()
        
        # Save results to file
        results_file = f"e2e_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Print summary
        print("\n" + "="*60)
        print("FINANCE-BRO E2E TEST RESULTS")
        print("="*60)
        print(f"Total Agents Tested: {results['summary']['total_agents_tested']}")
        print(f"Successful Tests: {results['summary']['successful_tests']}")
        print(f"Failed Tests: {results['summary']['failed_tests']}")
        print(f"Success Rate: {results['summary']['success_rate']}")
        print(f"Test Duration: {results['summary']['test_duration']}")
        print(f"Model Used: {results['summary']['model_used']}")
        print(f"Results saved to: {results_file}")
        
        if results['errors']:
            print(f"\nERRORS ({len(results['errors'])}):")
            for error in results['errors']:
                print(f"  - {error}")
        
        print("\nDetailed test cases executed:")
        for agent, result in results['detailed_results'].items():
            status = "✓" if result.get("status") == "success" else "✗"
            test_case = result.get("test_case", "Unknown test case")
            print(f"  {status} {agent}: {test_case}")
        
        return results['summary']['failed_tests'] == 0
        
    except Exception as e:
        logger.error(f"E2E test suite failed: {str(e)}")
        print(f"\nFATAL ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)