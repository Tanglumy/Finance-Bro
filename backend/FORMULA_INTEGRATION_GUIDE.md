# QuantDSL Formula Integration Guide

## Overview

This guide explains how the QuantDSL Formula Engine integrates with Finance-Bro's trading workflow. The integration enables formula-based trading strategies that combine quantitative analysis with event-driven decision making.

## Architecture

### Component Overview

```
User Query
    ↓
EventAgent Graph
    ↓
┌─────────────────────────────────────────────────────────┐
│ 1. Detect Events                                        │
│    - Market data gathering                              │
│    - News analysis                                      │
│    - Economic indicators                                │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ 2. Analyze Portfolio                                    │
│    - Current positions                                  │
│    - Risk metrics                                       │
│    - Performance analysis                               │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ 3. Evaluate Formulas (NEW)                             │
│    - Load active formula strategies                     │
│    - Fetch historical data                              │
│    - Run formula evaluation                             │
│    - Generate formula-based signals                     │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ 4. Generate Signals                                     │
│    - Combine formula signals with LLM analysis          │
│    - Tag signal sources                                 │
│    - Confidence scoring                                 │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ 5. Risk Validation                                      │
│    - Position size limits                               │
│    - Portfolio concentration                            │
│    - Daily loss limits                                  │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ 6. Executive Agent                                      │
│    - Order execution (IBKR)                            │
│    - Protective orders (stop-loss, take-profit)         │
│    - Paper trading support                              │
└─────────────────────────────────────────────────────────┘
```

## Key Components

### 1. FormulaHandler (`src/EventAgent/formula_handler.py`)

Manages formula evaluation and signal generation.

**Key Methods:**
- `evaluate_formula_strategy()`: Evaluates a formula against market data
- `register_formula()`: Registers a formula for active trading
- `evaluate_all_active_formulas()`: Evaluates all active strategies

**Example Usage:**
```python
from src.EventAgent.formula_handler import get_formula_handler

handler = get_formula_handler()

# Register a formula
handler.register_formula(
    "momentum_strategy",
    {
        "symbols": ["AAPL", "GOOGL"],
        "min_signal_strength": 0.7
    }
)

# Evaluate formula
market_data = {
    "prices": {"AAPL": 150.0},
    "indicators": {"RSI": 65}
}

portfolio_context = {
    "cash": 50000.0,
    "total_value": 100000.0
}

signals = await handler.evaluate_formula_strategy(
    "momentum_strategy",
    market_data,
    portfolio_context,
    ["AAPL"]
)
```

### 2. StrategyManager (`src/EventAgent/strategy_manager.py`)

Manages lifecycle of formula strategies.

**Key Features:**
- Strategy creation and configuration
- Activation/deactivation controls
- Performance tracking
- Error monitoring and auto-disable
- Strategy persistence (JSON storage)

**Example Usage:**
```python
from src.EventAgent.strategy_manager import (
    get_strategy_manager,
    StrategyStatus,
    MarketCondition
)

manager = get_strategy_manager()

# Create strategy
strategy = manager.create_strategy(
    name="AAPL Momentum",
    formula_model_name="momentum_strategy",
    symbols=["AAPL"],
    description="Momentum-based strategy for AAPL"
)

# Activate for paper trading
manager.activate_strategy(strategy.strategy_id, paper_trading=True)

# Get active strategies
active = manager.get_active_strategies()

# Record trade execution
manager.record_trade(
    strategy.strategy_id,
    {
        "symbol": "AAPL",
        "action": "BUY",
        "quantity": 50,
        "price": 150.0,
        "pnl": 250.0
    }
)
```

### 3. EventAgent Graph Integration

The `evaluate_formulas` node is inserted into the EventAgent workflow:

**Location in Graph:**
```python
detect_events → analyze_portfolio → evaluate_formulas → generate_signals → investment_reasoning
```

**Node Implementation:**
```python
def evaluate_formula_strategies(state: EventAgentState, config: Dict[str, Any]):
    # 1. Get active strategies
    active_strategies = strategy_manager.get_active_strategies()
    
    # 2. For each strategy
    for strategy in active_strategies:
        # 3. Evaluate formula
        signals = await formula_handler.evaluate_formula_strategy(
            strategy.formula_model_name,
            market_data,
            portfolio_context,
            strategy.symbols
        )
        
        # 4. Record signals
        state["formula_signals"].extend(signals)
    
    return state
```

## Data Flow

### Signal Generation Process

1. **Market Data Collection**
   ```python
   market_data = {
       "prices": {"AAPL": 150.0, "GOOGL": 2800.0},
       "indicators": {"RSI": 65, "MACD": 1.2},
       "events": [{"type": "earnings", "significance": 0.85}]
   }
   ```

2. **Formula Evaluation**
   ```python
   # Formula returns signal value: >0.5=BUY, <-0.5=SELL
   result = formula_engine.evaluate_model("momentum_strategy", historical_data)
   # result = 0.8 → BUY signal
   ```

3. **Signal Conversion**
   ```python
   signal = TradingSignal(
       symbol="AAPL",
       signal_type="BUY",
       signal_strength=0.8,
       entry_price=150.0,
       quantity=50,  # Calculated based on portfolio
       formula_name="momentum_strategy"
   )
   ```

4. **Signal Merging**
   ```python
   # Combine formula signals with LLM-generated signals
   all_signals = formula_signals + llm_signals
   
   # Tag sources
   for signal in all_signals:
       signal["source"] = "formula_engine" if signal.has("formula_name") else "llm_analysis"
   ```

### State Schema

```python
class EventAgentState(TypedDict):
    messages: Annotated[list, add_messages]
    market_events: Annotated[list, operator.add]
    financial_signals: Annotated[list, operator.add]
    portfolio_analysis: Annotated[list, operator.add]
    
    # Formula integration fields
    formula_signals: Annotated[list, operator.add]  # NEW
    formula_evaluations: Annotated[list, operator.add]  # NEW
    active_formulas: List[str]  # NEW
    
    # Existing fields
    event_loop_count: int
    max_event_loops: int
    current_portfolio: Dict[str, Any]
    risk_tolerance: str
    investment_horizon: str
```

## Formula Strategy Configuration

### Strategy Schema

```python
@dataclass
class FormulaStrategy:
    strategy_id: str
    name: str
    formula_model_name: str
    description: str = ""
    status: StrategyStatus = StrategyStatus.INACTIVE
    symbols: List[str] = field(default_factory=list)
    market_conditions: List[MarketCondition] = field(default_factory=list)
    risk_limits: RiskLimits = field(default_factory=RiskLimits)
    performance: PerformanceMetrics = field(default_factory=PerformanceMetrics)
```

### Risk Limits

```python
@dataclass
class RiskLimits:
    max_position_size_pct: float = 0.05  # 5% of portfolio
    max_daily_loss_pct: float = 0.02  # 2% daily loss limit
    max_total_loss_pct: float = 0.10  # 10% total loss limit
    min_signal_strength: float = 0.7  # Minimum confidence
    max_open_positions: int = 5
    stop_loss_pct: float = 0.05  # 5% stop loss
    take_profit_pct: float = 0.15  # 15% take profit
```

## Usage Examples

### Example 1: Create and Activate Formula Strategy

```python
from src.EventAgent.strategy_manager import get_strategy_manager, RiskLimits
from src.EventAgent.formula_handler import get_formula_handler

# 1. Create strategy
manager = get_strategy_manager()

strategy = manager.create_strategy(
    name="Tech Momentum Strategy",
    formula_model_name="momentum_strategy",
    symbols=["AAPL", "GOOGL", "MSFT"],
    description="Momentum-based trading for tech stocks",
    risk_limits=RiskLimits(
        max_position_size_pct=0.03,  # 3% max
        min_signal_strength=0.75,
        stop_loss_pct=0.04
    )
)

# 2. Activate in paper trading mode
manager.activate_strategy(strategy.strategy_id, paper_trading=True)

# 3. Verify activation
active_strategies = manager.get_active_strategies()
print(f"Active strategies: {len(active_strategies)}")
```

### Example 2: Manual Signal Generation

```python
from src.EventAgent.formula_handler import get_formula_handler

handler = get_formula_handler()

# Prepare market data
market_data = {
    "prices": {
        "AAPL": 150.25,
        "GOOGL": 2805.50
    },
    "indicators": {
        "RSI": {"AAPL": 68, "GOOGL": 55},
        "MACD": {"AAPL": 1.2, "GOOGL": -0.5}
    }
}

portfolio_context = {
    "cash": 50000.0,
    "total_value": 100000.0,
    "positions": [{"symbol": "AAPL", "quantity": 100}]
}

# Generate signals
signals = await handler.evaluate_formula_strategy(
    "momentum_strategy",
    market_data,
    portfolio_context,
    ["AAPL", "GOOGL"]
)

# Process signals
for signal in signals:
    print(f"{signal.symbol}: {signal.signal_type} @ {signal.entry_price}")
    print(f"Strength: {signal.signal_strength:.2f}")
    print(f"Quantity: {signal.quantity}")
```

### Example 3: End-to-End Workflow

```python
from src.EventAgent.graph import initialize_event_agent_state, create_event_agent_graph
from src.EventAgent.strategy_manager import get_strategy_manager

# 1. Setup strategy
manager = get_strategy_manager()
strategy = manager.create_strategy(
    name="Earnings Momentum",
    formula_model_name="earnings_momentum",
    symbols=["AAPL", "MSFT"]
)
manager.activate_strategy(strategy.strategy_id, paper_trading=True)

# 2. Initialize state
state = initialize_event_agent_state(
    user_message="Analyze current market conditions for tech stocks",
    portfolio_data={"cash": 50000.0, "total_value": 100000.0},
    risk_tolerance="moderate",
    active_formulas=["earnings_momentum"]
)

# 3. Execute graph
graph = create_event_agent_graph()
result = await graph.ainvoke(state)

# 4. Extract signals
formula_signals = result["formula_signals"]
all_signals = result["financial_signals"]

print(f"Formula signals: {len(formula_signals)}")
print(f"Total signals: {len(all_signals)}")

# 5. Execute approved signals (with ExecutiveAgent)
from src.EventAgent.executive_agent import get_executive_agent

executive = get_executive_agent(paper_trading=True)
await executive.initialize()

for signal in all_signals:
    if signal["signal_strength"] > 0.8:
        result = await executive.execute_signal(signal, portfolio_manager)
        print(f"Order {result.order_id}: {result.message}")
```

## Testing

### Running Tests

```bash
cd backend

# Run all formula integration tests
python -m pytest tests/test_formula_integration.py -v

# Run specific test class
python -m pytest tests/test_formula_integration.py::TestFormulaHandler -v

# Run with coverage
python -m pytest tests/test_formula_integration.py --cov=src.EventAgent --cov-report=html
```

### Test Coverage

The test suite covers:

1. **MarketDataTransformer** (3 tests)
   - DataFrame conversion
   - Event feature extraction
   - Historical data fetching

2. **TradingSignal** (2 tests)
   - Signal creation
   - Dictionary serialization

3. **FormulaHandler** (8 tests)
   - Initialization
   - Strategy evaluation
   - Signal generation (BUY/SELL/HOLD)
   - Position sizing
   - Formula registration

4. **StrategyManager** (9 tests)
   - Strategy lifecycle
   - Activation/deactivation
   - Trade recording
   - Error handling
   - Persistence

5. **Graph Integration** (1 test)
   - Node execution
   - State updates

6. **End-to-End Workflows** (2 tests)
   - Complete workflow
   - Execution readiness

## API Integration

### New Endpoints

The following endpoints are available in `comprehensive_api.py`:

#### Formula Management

```python
# Get available formula functions
GET /formula/functions

# Validate formula syntax
POST /formula/validate
Body: {"formula": "SMA(close, 20)"}

# Create formula model
POST /formula/models
Body: {
    "name": "momentum_strategy",
    "formula": "IF(RSI(close, 14) > 70, -1.0, IF(RSI(close, 14) < 30, 1.0, 0.0))",
    "description": "RSI-based momentum strategy"
}

# List all models
GET /formula/models

# Get specific model
GET /formula/models/{model_name}

# Delete model
DELETE /formula/models/{model_name}
```

#### Strategy Management

```python
# Generate formula-based signals
POST /trading/signals/generate
Body: {
    "market_data": {...},
    "portfolio_context": {...},
    "formula_names": ["momentum_strategy"]
}

# Create trading strategy
POST /trading/strategies
Body: {
    "name": "Tech Momentum",
    "formula_model_name": "momentum_strategy",
    "symbols": ["AAPL", "GOOGL"],
    "risk_limits": {...}
}

# List strategies
GET /trading/strategies

# Activate strategy
POST /trading/strategies/{strategy_id}/activate
Body: {"paper_trading": true}

# Deactivate strategy
POST /trading/strategies/{strategy_id}/deactivate
```

#### Formula Evaluation

```python
# Evaluate formula against market data
POST /formula/evaluate
Body: {
    "model_name": "momentum_strategy",
    "data": {
        "close": [100, 102, 104, 103, 105],
        "volume": [1000000, 1200000, 1100000, 1300000, 1400000]
    }
}

# Backtest formula
POST /formula/backtest
Body: {
    "model_name": "momentum_strategy",
    "data": {...},
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "initial_capital": 100000
}
```

## Safety Features

### 1. Paper Trading Mode

All new strategies start in paper trading:

```python
# Always use paper trading first
manager.activate_strategy(strategy_id, paper_trading=True)

# Only activate live after validation
# manager.activate_strategy(strategy_id, paper_trading=False)
```

### 2. Risk Validation

Every signal goes through risk checks:

```python
# Position size limits
if position_value > portfolio_value * max_position_size_pct:
    reject_signal()

# Daily loss limits
if daily_loss > portfolio_value * max_daily_loss_pct:
    stop_trading()

# Cash reserve requirements
if cash_after_order < portfolio_value * min_cash_reserve_pct:
    reject_signal()
```

### 3. Auto-Disable on Errors

```python
# Strategy auto-fails after 10 errors
if strategy.error_count > 10:
    strategy.status = StrategyStatus.FAILED
    log_error(f"Strategy {strategy.name} auto-disabled")
```

### 4. Signal Confidence Thresholds

```python
# Only execute high-confidence signals
if signal.signal_strength < strategy.risk_limits.min_signal_strength:
    skip_signal()
```

## Troubleshooting

### Common Issues

#### 1. Formula Engine Not Available

**Error:** `Formula Engine not available - using mock mode`

**Solution:**
```bash
cd backend
pip install -r requirements.txt

# Verify formula engine
python -c "from src.formula_engine import FormulaEngine; print('OK')"
```

#### 2. No Active Strategies

**Error:** `No active formula strategies found`

**Solution:**
```python
# Check strategy status
manager = get_strategy_manager()
strategies = manager.list_strategies()
for s in strategies:
    print(f"{s.name}: {s.status}")

# Activate strategies
for s in strategies:
    if s.status == StrategyStatus.INACTIVE:
        manager.activate_strategy(s.strategy_id, paper_trading=True)
```

#### 3. Import Errors

**Error:** `ModuleNotFoundError: No module named 'EventAgent'`

**Solution:**
```bash
# Add backend to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:/path/to/Finance-Bro/backend

# Or use relative imports
from src.EventAgent.formula_handler import get_formula_handler
```

#### 4. State Initialization Issues

**Error:** `KeyError: 'formula_signals'`

**Solution:**
```python
# Always use initialize_event_agent_state
from src.EventAgent.graph import initialize_event_agent_state

state = initialize_event_agent_state(
    user_message="Your query",
    active_formulas=["momentum_strategy"]  # Include this
)
```

## Performance Optimization

### 1. Batch Evaluation

```python
# Evaluate multiple symbols at once
signals = await handler.evaluate_all_active_formulas(
    market_data,
    portfolio_context
)
```

### 2. Cache Historical Data

```python
# Cache historical data for reuse
historical_cache = {}

for symbol in symbols:
    if symbol not in historical_cache:
        historical_cache[symbol] = await fetch_historical_data(symbol)
    
    result = formula_engine.evaluate_model(
        formula_name,
        historical_cache[symbol]
    )
```

### 3. Async Execution

```python
# Evaluate strategies concurrently
import asyncio

tasks = [
    handler.evaluate_formula_strategy(s.formula_model_name, data, context, s.symbols)
    for s in active_strategies
]

results = await asyncio.gather(*tasks)
```

## Best Practices

### 1. Strategy Design

✅ **DO:**
- Start with simple formulas (single indicator)
- Backtest thoroughly (minimum 30 days)
- Use paper trading for validation (7+ days)
- Set conservative risk limits
- Monitor performance metrics

❌ **DON'T:**
- Over-optimize formulas (curve fitting)
- Skip backtesting
- Use high leverage
- Ignore warning signals
- Deploy without testing

### 2. Risk Management

```python
# Conservative risk limits
risk_limits = RiskLimits(
    max_position_size_pct=0.03,  # 3% max per position
    max_daily_loss_pct=0.01,  # 1% daily loss limit
    min_signal_strength=0.80,  # High confidence only
    stop_loss_pct=0.03,  # Tight 3% stop loss
    take_profit_pct=0.10  # 10% take profit
)
```

### 3. Monitoring

```python
# Regular performance checks
for strategy in manager.list_strategies():
    perf = strategy.performance
    
    if perf.win_rate < 0.5 or perf.profit_factor < 1.2:
        # Pause underperforming strategy
        manager.pause_strategy(strategy.strategy_id)
        alert_admin(f"Strategy {strategy.name} paused due to poor performance")
```

### 4. Error Handling

```python
try:
    signals = await handler.evaluate_formula_strategy(...)
except Exception as e:
    # Log error
    logger.error(f"Formula evaluation failed: {e}")
    
    # Record error
    manager.record_error(strategy.strategy_id, str(e))
    
    # Alert if critical
    if "timeout" in str(e).lower():
        alert_admin(f"Formula evaluation timeout: {strategy.name}")
```

## Next Steps

1. **Learn QuantDSL Formula Syntax**
   - See `formula_engine` documentation
   - Study example formulas
   - Practice with sample data

2. **Create Your First Strategy**
   - Start with simple momentum formula
   - Backtest on historical data
   - Deploy in paper trading mode

3. **Monitor and Iterate**
   - Track performance metrics
   - Adjust risk parameters
   - Refine formulas based on results

4. **Scale Gradually**
   - Add more symbols incrementally
   - Diversify across strategies
   - Increase position sizes cautiously

## Support

- **Documentation**: See `QUANTDSL_INTEGRATION_PROPOSAL.md` for architecture details
- **Issues**: Report bugs at `https://github.com/sylphai/finance-bro/issues`
- **Tests**: Run `pytest tests/test_formula_integration.py -v`
- **Examples**: See `backend/formula_engine_examples.py`

## Conclusion

The QuantDSL integration provides a powerful framework for systematic, data-driven trading. By combining formula-based signals with LLM analysis and comprehensive risk management, you can build robust trading strategies that adapt to market conditions while maintaining strict safety controls.

Remember: Always start with paper trading, backtest thoroughly, and monitor performance continuously.
