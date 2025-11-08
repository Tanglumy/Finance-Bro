# QuantDSL Integration Proposal

## Executive Summary

This proposal outlines the integration of the QuantDSL Formula Engine into Finance-Bro's trading execution workflow. The goal is to enable formula-based trading strategies that connect market event detection → formula evaluation → signal generation → trade execution.

## Current System Architecture

### Existing Components

1. **Event Detection** (`EventAgent/graph.py`)
   - Detects market events using LLM analysis
   - Gathers market data, news, economic indicators
   - Outputs: `market_events` list

2. **Signal Generation** (`EventAgent/tools_and_schemas.py`)
   - Creates trading signals based on events
   - Uses technical indicators and portfolio analysis
   - Outputs: Trading signals with action, quantity, confidence

3. **Trade Execution** (`EventAgent/executive_agent.py`)
   - `ExecutiveAgent` class handles order execution
   - Risk management via `RiskManager`
   - IBKR connector for actual trading
   - Protective orders (stop-loss, take-profit)

4. **Formula Engine** (`src/formula_engine`)
   - Custom DSL for quantitative models
   - Functions: SMA, EMA, RSI, MACD, Bollinger Bands, etc.
   - Backtesting capabilities
   - Model persistence and evaluation

### Current Workflow

```
User Query → Event Detection → Portfolio Analysis → Signal Generation → Investment Reasoning
                                                           ↓
                                                    execute_trading_signal()
                                                           ↓
                                                    Executive Agent
                                                           ↓
                                                    Risk Checks → IBKR Execution
```

## Proposed Integration Architecture

### Enhanced Workflow with QuantDSL

```
User Query → Event Detection → Portfolio Analysis
                                      ↓
                              QuantDSL Evaluation
                                      ↓
                    [Formula-Based Signal Generation]
                                      ↓
                              Signal Validation
                                      ↓
                              Executive Agent
                                      ↓
                              Risk Checks → IBKR Execution
```

### Integration Points

#### 1. Formula-Based Event Handler
**Location**: `backend/src/EventAgent/formula_handler.py` (NEW)

**Responsibilities**:
- Load and manage trading formula models
- Convert market events and portfolio data to formula inputs
- Evaluate formulas against real-time market data
- Generate signals from formula outputs

**Key Methods**:
```python
- evaluate_formula_strategy(market_data, portfolio_context) → signals
- convert_events_to_formula_input(events) → DataFrame
- generate_signals_from_formula_results(results) → List[TradingSignal]
```

#### 2. Enhanced Signal Generation Tool
**Location**: `backend/src/EventAgent/tools_and_schemas.py`

**New Tool**: `generate_formula_based_signals`

**Purpose**:
- Integrate formula evaluation into existing tool ecosystem
- Make formula-based strategies accessible to LangGraph agents
- Combine formula signals with traditional analysis

#### 3. Formula Strategy Manager
**Location**: `backend/src/EventAgent/strategy_manager.py` (NEW)

**Responsibilities**:
- Manage multiple formula strategies
- Strategy activation/deactivation
- Performance tracking per strategy
- Strategy selection based on market conditions

#### 4. Enhanced Graph Node
**Location**: `backend/src/EventAgent/graph.py`

**New Node**: `evaluate_formulas`
- Insert between `analyze_portfolio` and `generate_signals`
- Evaluate active formula strategies
- Combine formula outputs with LLM-based analysis

#### 5. API Endpoints Integration
**Location**: `backend/comprehensive_api.py`

**Enhanced Endpoints**:
- `/trading/formulas/strategies` - List active trading formulas
- `/trading/formulas/evaluate` - Evaluate formula against current market
- `/trading/formulas/backtest` - Backtest formula strategy
- `/trading/signals/generate` - Generate signals (include formula-based)

## Implementation Plan

### Phase 1: Foundation (Steps 1-3)

**Step 1**: Create Formula Handler Module
- File: `backend/src/EventAgent/formula_handler.py`
- Integrate FormulaEngine with EventAgent
- Data transformation utilities

**Step 2**: Create Strategy Manager
- File: `backend/src/EventAgent/strategy_manager.py`
- Strategy lifecycle management
- Performance tracking

**Step 3**: Add Formula-Based Signal Generation Tool
- Update: `backend/src/EventAgent/tools_and_schemas.py`
- New tool: `generate_formula_based_signals`
- Integration with existing tools

### Phase 2: Graph Integration (Steps 4-5)

**Step 4**: Enhance EventAgent Graph
- Update: `backend/src/EventAgent/graph.py`
- Add `evaluate_formulas` node
- Update state to include formula results

**Step 5**: Update State Schema
- Update: `backend/src/EventAgent/state.py`
- Add formula evaluation state
- Formula strategy tracking

### Phase 3: Execution Integration (Steps 6-7)

**Step 6**: Enhanced Signal Execution
- Update: `backend/src/EventAgent/executive_agent.py`
- Formula-aware risk management
- Strategy-specific execution parameters

**Step 7**: Risk Management for Formula Strategies
- Update: `backend/src/EventAgent/executive_agent.py`
- Formula-specific risk parameters
- Backtesting validation requirements

### Phase 4: API & Testing (Steps 8-10)

**Step 8**: API Endpoints
- Update: `backend/comprehensive_api.py`
- Add formula strategy management endpoints
- Real-time evaluation endpoints

**Step 9**: Integration Tests
- File: `backend/tests/test_formula_integration.py`
- End-to-end formula strategy testing
- Mock execution validation

**Step 10**: Documentation
- Update: `backend/FORMULA_INTEGRATION_GUIDE.md`
- Usage examples
- Best practices

## Technical Specifications

### Data Flow

```python
# Input: Market Events + Portfolio Data
market_data = {
    "prices": {"AAPL": 150.0, "GOOGL": 2800.0},
    "indicators": {"RSI": 65, "MACD": 1.2},
    "events": ["earnings_beat", "fed_announcement"]
}

portfolio_context = {
    "positions": [{"symbol": "AAPL", "quantity": 100}],
    "cash": 10000.0,
    "risk_tolerance": "moderate"
}

# Formula Evaluation
formula_results = formula_engine.evaluate_model(
    model_name="momentum_strategy",
    data=market_data
)

# Signal Generation
signals = [
    {
        "asset_symbol": "AAPL",
        "signal_type": "BUY",
        "quantity": 50,
        "entry_price": 150.0,
        "signal_strength": 0.85,
        "rationale": "Formula: momentum_strategy, Score: 0.85",
        "source": "formula",
        "formula_name": "momentum_strategy"
    }
]

# Risk Validation
risk_result = risk_manager.check_order_risk(signal, portfolio_value)

# Execution
if risk_result.approved:
    execution_result = executive_agent.execute_signal(signal)
```

### Formula Strategy Schema

```python
class FormulaStrategy(BaseModel):
    strategy_id: str
    name: str
    formula_model_name: str
    active: bool = True
    risk_parameters: RiskParameters
    min_signal_strength: float = 0.7
    max_position_size: float = 0.1
    symbols: List[str]  # Applicable symbols
    conditions: Dict[str, Any]  # Market condition filters
    created_at: datetime
    last_executed: Optional[datetime] = None
    performance_metrics: Dict[str, float] = {}
```

### Signal Source Types

```python
class SignalSource(Enum):
    LLM_ANALYSIS = "llm_analysis"  # Existing
    FORMULA_ENGINE = "formula_engine"  # New
    TECHNICAL_INDICATOR = "technical_indicator"  # Existing
    HYBRID = "hybrid"  # Combination
```

## Safety & Risk Management

### Formula Validation Requirements

1. **Backtesting Mandatory**
   - Minimum 30 days historical performance
   - Sharpe ratio > 1.0
   - Max drawdown < 15%
   - Win rate > 50%

2. **Paper Trading First**
   - All new formulas start in simulation mode
   - Minimum 7 days paper trading
   - Manual review before live activation

3. **Risk Limits**
   - Per-formula position size limits
   - Daily loss limits per formula
   - Automatic deactivation on poor performance

4. **Monitoring**
   - Real-time performance tracking
   - Deviation alerts from backtest results
   - Anomaly detection

## Example Use Cases

### Use Case 1: Momentum Trading Strategy

```python
# Formula Definition
momentum_formula = """
SIGNAL = IF(
    AND(
        RSI(close, 14) > 50,
        CROSS_OVER(SMA(close, 10), SMA(close, 50)),
        volume > SMA(volume, 20) * 1.5
    ),
    1.0,  # BUY signal
    IF(
        OR(
            RSI(close, 14) < 30,
            CROSS_UNDER(SMA(close, 10), SMA(close, 50))
        ),
        -1.0,  # SELL signal
        0.0  # NEUTRAL
    )
)

STRENGTH = ABS(SIGNAL) * (
    (RSI(close, 14) - 50) / 50
)
"""

# Integration Flow
1. Market event detected: "Tech sector showing momentum"
2. Formula evaluates: momentum_formula on AAPL, GOOGL, MSFT
3. Signals generated: AAPL=BUY(0.85), GOOGL=BUY(0.72)
4. Risk checks pass
5. Orders executed via ExecutiveAgent
```

### Use Case 2: Mean Reversion Strategy

```python
mean_reversion_formula = """
BB_UPPER, BB_MIDDLE, BB_LOWER = BBANDS(close, 20, 2)
PRICE_POSITION = (close - BB_LOWER) / (BB_UPPER - BB_LOWER)

SIGNAL = IF(
    PRICE_POSITION < 0.2,  # Near lower band
    1.0,  # Oversold - BUY
    IF(
        PRICE_POSITION > 0.8,  # Near upper band
        -1.0,  # Overbought - SELL
        0.0
    )
)

STRENGTH = ABS(1.0 - 2 * PRICE_POSITION)
"""
```

## Benefits

1. **Systematic Trading**: Reduce emotional decision-making
2. **Backtesting**: Validate strategies before live trading
3. **Consistency**: Reproducible trading logic
4. **Speed**: Automated signal generation
5. **Flexibility**: Easy strategy modification and testing
6. **Hybrid Approach**: Combine formula-based + LLM analysis
7. **Risk Management**: Formula-specific risk controls
8. **Performance Tracking**: Strategy-level analytics

## Risks & Mitigation

### Technical Risks

1. **Formula Bugs**
   - Mitigation: Comprehensive testing, validation framework
   - Code review for all formulas

2. **Data Quality**
   - Mitigation: Data validation, anomaly detection
   - Fallback to safe defaults

3. **Execution Delays**
   - Mitigation: Performance monitoring, timeouts
   - Async execution patterns

### Trading Risks

1. **Over-optimization**
   - Mitigation: Out-of-sample testing, walk-forward analysis
   - Parameter stability checks

2. **Market Regime Change**
   - Mitigation: Adaptive parameters, multiple strategies
   - Performance monitoring and auto-deactivation

3. **Correlation Breakdown**
   - Mitigation: Regular correlation analysis
   - Strategy diversification

## Success Metrics

1. **Technical Metrics**
   - Formula evaluation latency < 100ms
   - Signal generation success rate > 95%
   - System uptime > 99.5%

2. **Trading Metrics**
   - Sharpe ratio > 1.5
   - Max drawdown < 10%
   - Win rate > 55%
   - Profit factor > 1.5

3. **Integration Metrics**
   - API response time < 200ms
   - Error rate < 1%
   - Test coverage > 80%

## Timeline

- **Week 1**: Phase 1 (Foundation) - Steps 1-3
- **Week 2**: Phase 2 (Graph Integration) - Steps 4-5
- **Week 3**: Phase 3 (Execution Integration) - Steps 6-7
- **Week 4**: Phase 4 (API & Testing) - Steps 8-10
- **Week 5**: Integration testing and refinement
- **Week 6**: Documentation and deployment

## Next Steps

1. Review and approve proposal
2. Begin Phase 1 implementation
3. Set up monitoring and logging infrastructure
4. Create sample formula strategies for testing
5. Establish code review process

## Conclusion

Integrating QuantDSL into the trading workflow will enable systematic, data-driven trading strategies while maintaining the flexibility of LLM-based analysis. The phased approach ensures safe, tested integration with comprehensive risk management at every step.
