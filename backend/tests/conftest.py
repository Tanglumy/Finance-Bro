"""
Pytest configuration and fixtures for Finance-Bro tests.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import asyncio
from unittest.mock import Mock, AsyncMock
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def sample_market_data():
    """Create sample market data for testing."""
    np.random.seed(42)
    days = 252
    
    # Generate dates
    start_date = datetime(2023, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(days)]
    
    # Generate realistic price data
    initial_price = 100.0
    prices = [initial_price]
    
    for i in range(1, days):
        change = np.random.normal(0.001, 0.02)
        new_price = prices[-1] * (1 + change)
        prices.append(max(new_price, 0.01))
    
    # Create OHLC data
    opens = []
    highs = []
    lows = []
    closes = prices
    volumes = []
    
    for i, close in enumerate(closes):
        if i == 0:
            open_price = close
        else:
            gap = np.random.normal(0, 0.005)
            open_price = closes[i-1] * (1 + gap)
        
        opens.append(open_price)
        
        high_price = max(open_price, close) * (1 + abs(np.random.normal(0, 0.01)))
        low_price = min(open_price, close) * (1 - abs(np.random.normal(0, 0.01)))
        
        highs.append(high_price)
        lows.append(low_price)
        
        base_volume = 1000000
        volume_factor = 1 + abs(close - open_price) / open_price * 2
        volume = int(base_volume * volume_factor * np.random.uniform(0.5, 1.5))
        volumes.append(volume)
    
    return pd.DataFrame({
        'date': dates,
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
        'volume': volumes
    })

@pytest.fixture
def sample_portfolio_data():
    """Create sample portfolio data for testing."""
    return {
        'cash': 50000,
        'positions': {
            'AAPL': {'quantity': 100, 'avg_price': 150.0, 'current_price': 155.0},
            'GOOGL': {'quantity': 50, 'avg_price': 2800.0, 'current_price': 2850.0},
            'MSFT': {'quantity': 75, 'avg_price': 280.0, 'current_price': 285.0}
        },
        'total_value': 185000,
        'daily_pnl': 2500,
        'total_pnl': 15000
    }

@pytest.fixture
def mock_financial_service():
    """Create mock financial service."""
    service = Mock()
    service.get_stock_price = AsyncMock(return_value={
        'symbol': 'AAPL',
        'price': 155.0,
        'change': 2.5,
        'change_percent': 1.64,
        'volume': 50000000
    })
    service.get_market_news = AsyncMock(return_value=[
        {
            'title': 'Market Update',
            'content': 'Markets are up today',
            'timestamp': datetime.now(),
            'sentiment': 'positive'
        }
    ])
    return service

@pytest.fixture
def mock_portfolio_manager():
    """Create mock portfolio manager."""
    manager = Mock()
    manager.get_portfolio_summary = AsyncMock(return_value={
        'total_value': 185000,
        'cash': 50000,
        'positions_value': 135000,
        'daily_pnl': 2500,
        'total_pnl': 15000
    })
    manager.add_position = AsyncMock(return_value=True)
    manager.remove_position = AsyncMock(return_value=True)
    return manager

@pytest.fixture
def formula_engine():
    """Create formula engine instance for testing."""
    try:
        from formula_engine import FormulaEngine
        return FormulaEngine()
    except ImportError:
        pytest.skip("Formula engine not available")

@pytest.fixture
def ts_predictor():
    """Create time series predictor for testing."""
    try:
        from ts_agent.predictor import TimeSeriesPredictor
        return TimeSeriesPredictor()
    except ImportError:
        pytest.skip("Time series predictor not available")

@pytest.fixture
def mock_api_client():
    """Create mock API client for testing."""
    client = Mock()
    client.get = AsyncMock()
    client.post = AsyncMock()
    client.put = AsyncMock()
    client.delete = AsyncMock()
    return client

@pytest.fixture
def test_config():
    """Test configuration settings."""
    return {
        'test_mode': True,
        'db_url': 'sqlite:///test.db',
        'api_keys': {
            'alpha_vantage': 'test_key',
            'nixtla': 'test_key',
            'news_api': 'test_key'
        },
        'timeouts': {
            'api_call': 5,
            'db_query': 2
        }
    }

@pytest.fixture
def mock_database():
    """Create mock database connection."""
    db = Mock()
    db.execute = AsyncMock()
    db.fetch = AsyncMock()
    db.fetchall = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db

@pytest.fixture
def sample_trading_signals():
    """Create sample trading signals."""
    return pd.DataFrame({
        'date': pd.date_range('2023-01-01', periods=100),
        'symbol': ['AAPL'] * 100,
        'signal': np.random.choice(['BUY', 'SELL', 'HOLD'], 100),
        'confidence': np.random.uniform(0.5, 1.0, 100),
        'price': np.random.uniform(100, 200, 100)
    })

@pytest.fixture
def sample_backtest_results():
    """Create sample backtest results."""
    return {
        'total_return': 0.15,
        'annualized_return': 0.12,
        'volatility': 0.18,
        'sharpe_ratio': 0.67,
        'max_drawdown': -0.08,
        'win_rate': 0.55,
        'total_trades': 25,
        'avg_trade_return': 0.006,
        'profit_factor': 1.35
    }

@pytest.fixture(autouse=True)
def clean_cache():
    """Clean up caches after each test."""
    yield
    # Clean up any global caches or state
    import gc
    gc.collect()

# Test markers
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )
    config.addinivalue_line(
        "markers", "api: marks tests as API tests"
    )
    config.addinivalue_line(
        "markers", "formula: marks tests as formula engine tests"
    )
    config.addinivalue_line(
        "markers", "ts: marks tests as time series tests"
    )
    config.addinivalue_line(
        "markers", "portfolio: marks tests as portfolio tests"
    )
    config.addinivalue_line(
        "markers", "network: marks tests requiring network access"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location."""
    for item in items:
        # Add markers based on test file location
        if "test_api" in item.fspath.basename:
            item.add_marker(pytest.mark.api)
        elif "test_formula" in item.fspath.basename:
            item.add_marker(pytest.mark.formula)
        elif "test_ts" in item.fspath.basename:
            item.add_marker(pytest.mark.ts)
        elif "test_portfolio" in item.fspath.basename:
            item.add_marker(pytest.mark.portfolio)
        
        # Add integration marker for integration tests
        if "integration" in item.fspath.basename:
            item.add_marker(pytest.mark.integration)
        else:
            item.add_marker(pytest.mark.unit)
        
        # Add slow marker for slow tests
        if "slow" in item.name or "test_slow" in item.name:
            item.add_marker(pytest.mark.slow)

# Async test utilities
@pytest.fixture
async def async_test_client():
    """Create async test client for API testing."""
    try:
        from httpx import AsyncClient
        from comprehensive_api import app
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client
    except ImportError:
        pytest.skip("httpx not available for async testing")