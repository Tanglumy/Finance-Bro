#!/usr/bin/env python3
"""
Finance Bro Setup Script
Initializes the system with sample data and configurations.
"""

import asyncio
import os
from pathlib import Path
from src.EventAgent.portfolio_manager import get_portfolio_manager
from src.EventAgent.executive_agent import get_executive_agent


async def setup_environment():
    """Setup environment variables and configurations."""
    print("🔧 Setting up environment...")
    
    # Create .env file template
    env_template = """
# Finance Bro Configuration
# Copy this to .env and fill in your API keys

# Financial Data APIs
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here
POLYGON_API_KEY=your_polygon_key_here
NEWS_API_KEY=your_news_api_key_here
FRED_API_KEY=your_fred_key_here

# Google Gemini API
GOOGLE_API_KEY=your_google_api_key_here

# Interactive Brokers
IBKR_GATEWAY_HOST=127.0.0.1
IBKR_GATEWAY_PORT=7497
IBKR_CLIENT_ID=1

# Risk Management
DEFAULT_POSITION_SIZE_PCT=0.1
DEFAULT_STOP_LOSS_PCT=0.05
DEFAULT_TAKE_PROFIT_PCT=0.15

# System Settings
PAPER_TRADING=true
LOG_LEVEL=INFO
"""
    
    env_file = Path(".env.template")
    with open(env_file, "w") as f:
        f.write(env_template)
    
    print(f"✅ Created {env_file}")
    print("📝 Please copy .env.template to .env and add your API keys")


async def setup_sample_portfolio():
    """Setup a sample portfolio for testing."""
    print("\n📊 Setting up sample portfolio...")
    
    portfolio = get_portfolio_manager()
    
    # Add sample positions
    sample_positions = [
        ("AAPL", 100, 150.0, "Technology"),
        ("MSFT", 50, 300.0, "Technology"),
        ("GOOGL", 20, 2500.0, "Technology"),
        ("AMZN", 15, 3000.0, "Consumer Discretionary"),
        ("TSLA", 30, 200.0, "Consumer Discretionary"),
        ("SPY", 100, 400.0, "ETF"),
        ("QQQ", 50, 350.0, "ETF"),
        ("VTI", 75, 200.0, "ETF"),
    ]
    
    for symbol, quantity, price, sector in sample_positions:
        portfolio.add_position(symbol, quantity, price, sector)
        print(f"  Added: {quantity} shares of {symbol} @ ${price:.2f}")
    
    total_value = portfolio.get_total_portfolio_value()
    print(f"\n✅ Sample portfolio created with ${total_value:,.2f} total value")
    print(f"💰 Cash balance: ${portfolio.cash_balance:,.2f}")
    print(f"📈 Positions: {len(portfolio.positions)}")


async def setup_executive_agent():
    """Setup and test the executive agent."""
    print("\n🤖 Setting up Executive Agent...")
    
    executive = get_executive_agent(paper_trading=True)
    
    # Initialize the agent
    success = await executive.initialize()
    if success:
        print("✅ Executive Agent initialized successfully")
        
        # Get status
        status = await executive.get_execution_status()
        print(f"📊 Agent Status:")
        print(f"  - Paper Trading: {status['paper_trading']}")
        print(f"  - Enabled: {status['agent_enabled']}")
        print(f"  - Risk Parameters:")
        print(f"    - Max Position Size: {status['risk_parameters']['max_position_size_pct']:.1%}")
        print(f"    - Stop Loss: {status['risk_parameters']['stop_loss_pct']:.1%}")
        print(f"    - Take Profit: {status['risk_parameters']['take_profit_pct']:.1%}")
        
        await executive.shutdown()
    else:
        print("❌ Failed to initialize Executive Agent")


async def create_documentation():
    """Create system documentation."""
    print("\n📚 Creating documentation...")
    
    readme_content = """# Finance Bro - AI-Powered Trading System

## Overview
Finance Bro is a comprehensive AI-powered trading and investment system that combines:
- Event-driven market analysis
- Portfolio management with time series analysis
- Automated trading execution via Interactive Brokers
- Risk management and compliance

## Architecture

### 1. EventAgent (Core Intelligence)
- **LangGraph-based workflow** for complex financial reasoning
- **Market event detection** from news, economic data, and technical indicators
- **Signal generation** with confidence scoring and rationale
- **Portfolio impact analysis** for existing positions

### 2. Financial Data Integration
- **Real-time market data** via Alpha Vantage, Polygon APIs
- **News sentiment analysis** from multiple sources
- **Economic calendar** integration with FRED
- **Technical indicators** calculation (RSI, MACD, etc.)

### 3. Portfolio Management
- **Position tracking** with cost basis and P&L calculation
- **Risk metrics** including Sharpe ratio, VaR, drawdown analysis
- **Performance attribution** and sector allocation
- **Time series analysis** with trend detection and forecasting

### 4. Executive Agent (Trading Automation)
- **IBKR integration** for order execution
- **Risk management** with position sizing and stop losses
- **Order types** including market, limit, stop, and protective orders
- **Paper trading mode** for safe testing

### 5. Safety Features
- **Multi-layer risk checks** before order execution
- **Emergency stop** functionality
- **Paper trading** by default
- **Comprehensive logging** and audit trails

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API Keys**
   ```bash
   cp .env.template .env
   # Edit .env with your API keys
   ```

3. **Setup Sample Portfolio**
   ```bash
   python setup_finance_bro.py
   ```

4. **Run Tests**
   ```bash
   python test_finance_bro.py
   ```

5. **Start the API Server**
   ```bash
   uvicorn src.EventAgent.app:app --reload
   ```

## API Endpoints

### EventAgent Analysis
- `POST /analyze` - Analyze market conditions and generate recommendations
- `GET /health` - Health check
- `GET /config` - Get current configuration

### Portfolio Management
- `GET /portfolio/metrics` - Get portfolio performance metrics
- `POST /portfolio/position` - Add/modify portfolio position
- `DELETE /portfolio/position` - Remove portfolio position

### Trading Execution
- `POST /trading/execute` - Execute trading signal
- `GET /trading/status` - Get trading status
- `POST /trading/emergency-stop` - Emergency stop all trading

## Safety Guidelines

⚠️ **IMPORTANT SAFETY NOTES**:
1. **Paper Trading First**: Always test with paper trading enabled
2. **Start Small**: Begin with small position sizes
3. **Monitor Closely**: Review all automated decisions
4. **Risk Management**: Set appropriate stop losses and position limits
5. **API Security**: Keep API keys secure and use read-only keys when possible

## Risk Management

The system includes multiple layers of risk management:
- **Position size limits** (default: 10% of portfolio)
- **Stop loss orders** (default: 5% below entry)
- **Daily loss limits** (default: 2% of portfolio)
- **Cash reserve requirements** (default: 5% in cash)
- **Sector concentration limits** (default: 30% max in one sector)

## Components Status

✅ **Completed Features**:
- EventAgent core LangGraph architecture
- Financial data APIs integration
- Portfolio management with time series analysis
- Executive Agent for IBKR trading
- Event detection and signal generation
- API endpoints and request handling
- Risk management system
- Paper trading mode

🚧 **In Development**:
- Database persistence layer
- Advanced machine learning models
- Frontend dashboard interface
- Real-time streaming data
- Advanced backtesting framework

## License
MIT License - See LICENSE file for details

## Disclaimer
This software is for educational and research purposes. Trading involves substantial risk of loss. Past performance does not guarantee future results. Users are responsible for their own trading decisions.
"""
    
    with open("README.md", "w") as f:
        f.write(readme_content)
    
    print("✅ Created README.md")


async def main():
    """Run the complete setup process."""
    print("🏦 Finance Bro Setup")
    print("=" * 30)
    
    try:
        await setup_environment()
        await setup_sample_portfolio()
        await setup_executive_agent()
        await create_documentation()
        
        print("\n🎉 Setup completed successfully!")
        print("\n📋 Next Steps:")
        print("1. Copy .env.template to .env and add your API keys")
        print("2. Run 'python test_finance_bro.py' to test the system")
        print("3. Start the API server with 'uvicorn src.EventAgent.app:app --reload'")
        print("4. Visit http://localhost:8000/docs for API documentation")
        print("\n⚠️  Remember: Always use paper trading mode first!")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())