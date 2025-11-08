# QuantDSL Integration Quick Start

## 5-Minute Setup

### Prerequisites

```bash
cd backend
pip install -r requirements.txt

# Verify installation
python -c "from src.EventAgent.formula_handler import get_formula_handler; print('✓ Formula handler ready')"
python -c "from src.EventAgent.strategy_manager import get_strategy_manager; print('✓ Strategy manager ready')"
```

## Your First Formula Strategy

### Step 1: Create a Simple Formula

```python
from src.formula_engine import FormulaEngine

engine = FormulaEngine()

# Create RSI-based momentum strategy
engine.create_model(
    name="simple_momentum",
    formula="""
    RSI_VALUE = RSI(close, 14)
    
    SIGNAL = IF(
        RSI_VALUE < 30,
        1.0,  # Oversold - BUY
        IF(
            RSI_VALUE > 70,
            -1.0,  # Overbought - SELL
            0.0  # Hold
        )
    )
    """,
    description="Simple RSI-based momentum strategy"
)

print("✓ Formula created")
```

### Step 2: Create Trading Strategy

```python
from src.EventAgent.strategy_manager import get_strategy_manager, RiskLimits

manager = get_strategy_manager()

strategy = manager.create_strategy(
    name="My First Strategy",
    formula_model_name="simple_momentum",
    symbols=["AAPL"],  # Start with one symbol
    description="Testing RSI momentum on AAPL",
    risk_limits=RiskLimits(
        max_position_size_pct=0.02,  # 2% max position
        min_signal_strength=0.7,     # High confidence only
        stop_loss_pct=0.03,          # 3% stop loss
        take_profit_pct=0.10         # 10% take profit
    )
)

print(f"✓ Strategy created: {strategy.strategy_id}")
```

### Step 3: Activate for Paper Trading

```python
# ALWAYS start with paper trading
manager.activate_strategy(strategy.strategy_id, paper_trading=True)

print("✓ Strategy activated in paper trading mode")

# Verify
active = manager.get_active_strategies()
print(f"Active strategies: {len(active)}")
```

### Step 4: Generate Signals

```python
from src.EventAgent.formula_handler import get_formula_handler
import asyncio

handler = get_formula_handler()

# Prepare data
market_data = {
    "prices": {"AAPL": 150.0},
    "indicators": {}
}

portfolio_context = {
    "cash": 50000.0,
    "total_value": 100000.0
}

# Generate signals
signals = await handler.evaluate_formula_strategy(
    "simple_momentum",
    market_data,
    portfolio_context,
    ["AAPL"]
)

print(f"✓ Generated {len(signals)} signals")

# Display signals
for signal in signals:
    print(f"\nSignal:")
    print(f"  Symbol: {signal.symbol}")
    print(f"  Type: {signal.signal_type}")
    print(f"  Strength: {signal.signal_strength:.2f}")
    print(f"  Entry Price: ${signal.entry_price}")
    print(f"  Quantity: {signal.quantity}")
```

### Step 5: Monitor Performance

```python
# Get strategy details
strategy = manager.get_strategy(strategy.strategy_id)

print(f"\nStrategy: {strategy.name}")
print(f"Status: {strategy.status.value}")
print(f"Signals generated: {strategy.signal_count}")
print(f"Executions: {strategy.execution_count}")
print(f"Errors: {strategy.error_count}")

# Performance metrics
perf = strategy.performance
print(f"\nPerformance:")
print(f"  Total trades: {perf.total_trades}")
print(f"  Win rate: {perf.win_rate:.1%}")
print(f"  Total P&L: ${perf.total_pnl:.2f}")
```

## Complete Example Script

```python
#!/usr/bin/env python3
"""
Quick start example for QuantDSL integration.

Run with: python quickstart_example.py
"""

import asyncio
from src.formula_engine import FormulaEngine
from src.EventAgent.strategy_manager import get_strategy_manager, RiskLimits
from src.EventAgent.formula_handler import get_formula_handler


async def main():
    print("🚀 QuantDSL Quick Start\n")
    
    # 1. Create formula
    print("Step 1: Creating formula...")
    engine = FormulaEngine()
    engine.create_model(
        name="quickstart_momentum",
        formula="""
        RSI_VALUE = RSI(close, 14)
        SIGNAL = IF(RSI_VALUE < 30, 1.0, IF(RSI_VALUE > 70, -1.0, 0.0))
        """,
        description="RSI momentum for quickstart"
    )
    print("✓ Formula created\n")
    
    # 2. Create strategy
    print("Step 2: Creating strategy...")
    manager = get_strategy_manager()
    strategy = manager.create_strategy(
        name="Quickstart Strategy",
        formula_model_name="quickstart_momentum",
        symbols=["AAPL"],
        risk_limits=RiskLimits(max_position_size_pct=0.02)
    )
    print(f"✓ Strategy created: {strategy.strategy_id}\n")
    
    # 3. Activate
    print("Step 3: Activating strategy...")
    manager.activate_strategy(strategy.strategy_id, paper_trading=True)
    print("✓ Strategy activated (paper trading)\n")
    
    # 4. Generate signals
    print("Step 4: Generating signals...")
    handler = get_formula_handler()
    
    market_data = {
        "prices": {"AAPL": 150.0},
        "indicators": {}
    }
    
    portfolio_context = {
        "cash": 50000.0,
        "total_value": 100000.0
    }
    
    signals = await handler.evaluate_formula_strategy(
        "quickstart_momentum",
        market_data,
        portfolio_context,
        ["AAPL"]
    )
    
    print(f"✓ Generated {len(signals)} signals\n")
    
    # 5. Display results
    if signals:
        print("Signals generated:")
        for signal in signals:
            print(f"  {signal.symbol}: {signal.signal_type} @ ${signal.entry_price}")
            print(f"  Strength: {signal.signal_strength:.2f}, Quantity: {signal.quantity}")
    else:
        print("  No signals (neutral market)")
    
    print("\n✅ Quick start complete!")
    print("\nNext steps:")
    print("  1. Try different formulas (see FORMULA_INTEGRATION_GUIDE.md)")
    print("  2. Backtest your strategy")
    print("  3. Monitor performance metrics")
    print("  4. Scale to multiple symbols")


if __name__ == "__main__":
    asyncio.run(main())
```

## Testing Your Setup

```bash
# Run all integration tests
cd backend
python -m pytest tests/test_formula_integration.py -v

# Expected output: 25 passed
```

## Common Workflows

### Backtest a Strategy

```python
from src.formula_engine import FormulaEngine
import pandas as pd
import numpy as np

engine = FormulaEngine()

# Generate sample historical data
dates = pd.date_range('2024-01-01', periods=90, freq='D')
prices = 100 * (1 + np.random.normal(0.001, 0.02, 90)).cumprod()

historical_data = pd.DataFrame({
    'date': dates,
    'close': prices,
    'volume': np.random.randint(1000000, 10000000, 90)
})

# Run backtest
results = engine.backtest_model(
    "simple_momentum",
    historical_data,
    initial_capital=100000,
    commission=0.001
)

print(f"Backtest Results:")
print(f"  Total Return: {results['total_return']:.2%}")
print(f"  Sharpe Ratio: {results['sharpe_ratio']:.2f}")
print(f"  Max Drawdown: {results['max_drawdown']:.2%}")
print(f"  Win Rate: {results['win_rate']:.2%}")
```

### Multiple Symbols Strategy

```python
strategy = manager.create_strategy(
    name="Multi-Symbol Momentum",
    formula_model_name="simple_momentum",
    symbols=["AAPL", "GOOGL", "MSFT", "AMZN"],  # Tech stocks
    risk_limits=RiskLimits(
        max_position_size_pct=0.025,  # 2.5% per position
        max_open_positions=4          # Max 4 concurrent positions
    )
)
```

### Market Condition-Based Strategies

```python
from src.EventAgent.strategy_manager import MarketCondition

# Strategy for bull markets only
bull_strategy = manager.create_strategy(
    name="Bull Market Momentum",
    formula_model_name="aggressive_momentum",
    symbols=["QQQ", "SPY"],
    market_conditions=[MarketCondition.BULL]  # Only active in bull markets
)

# Strategy for high volatility
volatility_strategy = manager.create_strategy(
    name="Volatility Trading",
    formula_model_name="mean_reversion",
    symbols=["VIX"],
    market_conditions=[MarketCondition.HIGH_VOLATILITY]
)
```

## Troubleshooting

### Issue: "Formula Engine not available"

```bash
pip install -r backend/requirements.txt
python -c "from src.formula_engine import FormulaEngine"
```

### Issue: "No active strategies found"

```python
manager = get_strategy_manager()
strategies = manager.list_strategies()

for s in strategies:
    if s.status.value == 'inactive':
        manager.activate_strategy(s.strategy_id, paper_trading=True)
```

### Issue: Signals not generating

```python
# Check formula evaluation directly
from src.formula_engine import FormulaEngine

engine = FormulaEngine()
result = engine.evaluate_model(
    "your_formula_name",
    historical_data  # Must have 'close' column
)

print(f"Formula output: {result}")
# Should be: >0.5 for BUY, <-0.5 for SELL
```

## Production Checklist

Before going live (paper trading → real trading):

- [ ] Backtest shows positive returns (minimum 30 days data)
- [ ] Win rate > 50%
- [ ] Sharpe ratio > 1.0
- [ ] Max drawdown < 15%
- [ ] Paper trading for minimum 7 days
- [ ] No errors in strategy execution
- [ ] Risk limits properly configured
- [ ] Stop-loss and take-profit set
- [ ] Position sizing validated
- [ ] Performance monitoring in place

## Next Steps

1. **Read Full Documentation**
   - `FORMULA_INTEGRATION_GUIDE.md` - Complete integration guide
   - `QUANTDSL_INTEGRATION_PROPOSAL.md` - Architecture overview

2. **Explore Examples**
   - `formula_engine_examples.py` - Formula examples
   - `test_formula_integration.py` - Test cases

3. **Build Your Strategy**
   - Start simple (single indicator)
   - Backtest thoroughly
   - Use paper trading
   - Monitor and iterate

4. **Join Community**
   - Report issues: https://github.com/sylphai/finance-bro/issues
   - Share strategies
   - Get support

## Quick Reference

### Key Classes

```python
from src.formula_engine import FormulaEngine
from src.EventAgent.formula_handler import get_formula_handler, TradingSignal
from src.EventAgent.strategy_manager import (
    get_strategy_manager,
    FormulaStrategy,
    RiskLimits,
    StrategyStatus
)
from src.EventAgent.executive_agent import get_executive_agent
```

### Essential Methods

```python
# Formula Engine
engine.create_model(name, formula, description)
engine.evaluate_model(name, data)
engine.backtest_model(name, data, initial_capital)

# Strategy Manager
manager.create_strategy(name, formula_model_name, symbols)
manager.activate_strategy(strategy_id, paper_trading=True)
manager.get_active_strategies()
manager.record_trade(strategy_id, trade_data)

# Formula Handler
handler.evaluate_formula_strategy(formula_name, market_data, portfolio_context, symbols)
handler.register_formula(formula_name, config)

# Executive Agent
executive.initialize()
executive.execute_signal(signal, portfolio_manager)
```

---

**Ready to start?** Run the complete example script above and you'll have a working formula strategy in minutes!
