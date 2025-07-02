"""
Interactive Brokers (IBKR) Data Client

Provides real-time and historical market data from Interactive Brokers.
Requires IBKR API connection and appropriate market data subscriptions.
"""

import asyncio
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
import logging
import threading
import time
from dataclasses import dataclass
from queue import Queue, Empty

try:
    from ibapi.client import EClient
    from ibapi.wrapper import EWrapper
    from ibapi.contract import Contract
    from ibapi.order import Order
    from ibapi.common import BarData, TickType
    IBKR_AVAILABLE = True
except ImportError:
    IBKR_AVAILABLE = False
    logging.warning("IBKR API not available. Install ibapi package for real-time data.")

logger = logging.getLogger(__name__)

@dataclass
class IBKRConfig:
    """Configuration for IBKR connection."""
    host: str = "127.0.0.1"
    port: int = 7497  # TWS paper trading port
    client_id: int = 1
    timeout: int = 30
    
@dataclass
class HistoricalDataRequest:
    """Request for historical data."""
    symbol: str
    duration: str = "1 Y"
    bar_size: str = "1 day"
    what_to_show: str = "TRADES"
    use_rth: int = 1  # Regular trading hours only

class IBKRWrapper(EWrapper):
    """IBKR API Wrapper to handle responses."""
    
    def __init__(self):
        EWrapper.__init__(self)
        self.data_queue = Queue()
        self.error_queue = Queue()
        self.historical_data = {}
        self.real_time_data = {}
        self.next_order_id = None
        self.connection_status = False
        
    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=""):
        """Handle API errors."""
        error_msg = f"Request {reqId}: Error {errorCode} - {errorString}"
        logger.error(error_msg)
        self.error_queue.put({
            "reqId": reqId,
            "errorCode": errorCode,
            "errorString": errorString
        })
        
    def connectAck(self):
        """Handle connection acknowledgment."""
        logger.info("IBKR connection established")
        self.connection_status = True
        
    def nextValidId(self, orderId):
        """Handle next valid order ID."""
        self.next_order_id = orderId
        logger.debug(f"Next valid order ID: {orderId}")
        
    def historicalData(self, reqId, bar):
        """Handle historical data bars."""
        if reqId not in self.historical_data:
            self.historical_data[reqId] = []
            
        bar_data = {
            "date": bar.date,
            "open": bar.open,
            "high": bar.high,
            "low": bar.low,
            "close": bar.close,
            "volume": bar.volume,
            "wap": bar.wap,
            "count": bar.count
        }
        self.historical_data[reqId].append(bar_data)
        
    def historicalDataEnd(self, reqId, start, end):
        """Handle end of historical data."""
        logger.debug(f"Historical data request {reqId} completed: {start} to {end}")
        self.data_queue.put({"type": "historical_complete", "reqId": reqId})
        
    def tickPrice(self, reqId, tickType, price, attrib):
        """Handle real-time price ticks."""
        if reqId not in self.real_time_data:
            self.real_time_data[reqId] = {}
            
        tick_name = TickType.to_str(tickType)
        self.real_time_data[reqId][tick_name] = {
            "price": price,
            "timestamp": datetime.now()
        }
        
    def tickSize(self, reqId, tickType, size):
        """Handle real-time size ticks."""
        if reqId not in self.real_time_data:
            self.real_time_data[reqId] = {}
            
        tick_name = TickType.to_str(tickType)
        self.real_time_data[reqId][f"{tick_name}_size"] = {
            "size": size,
            "timestamp": datetime.now()
        }

class IBKRClient(EClient):
    """IBKR API Client."""
    
    def __init__(self, wrapper, config: IBKRConfig):
        EClient.__init__(self, wrapper)
        self.wrapper = wrapper
        self.config = config
        self.connected = False
        self.request_id_counter = 1000
        
    def get_next_request_id(self):
        """Get next available request ID."""
        self.request_id_counter += 1
        return self.request_id_counter

class IBKRDataClient:
    """High-level IBKR data client."""
    
    def __init__(self, config: Optional[IBKRConfig] = None):
        """
        Initialize IBKR data client.
        
        Args:
            config: IBKR connection configuration
        """
        if not IBKR_AVAILABLE:
            raise ImportError("IBKR API not available. Install ibapi package.")
            
        self.config = config or IBKRConfig()
        self.wrapper = IBKRWrapper()
        self.client = IBKRClient(self.wrapper, self.config)
        self.connected = False
        self.api_thread = None
        
    async def connect(self) -> bool:
        """
        Connect to IBKR API.
        
        Returns:
            True if connected successfully
        """
        try:
            # Start API thread
            self.api_thread = threading.Thread(target=self._run_api, daemon=True)
            self.api_thread.start()
            
            # Wait for connection
            timeout = time.time() + self.config.timeout
            while not self.wrapper.connection_status and time.time() < timeout:
                await asyncio.sleep(0.1)
                
            if self.wrapper.connection_status:
                self.connected = True
                logger.info("Successfully connected to IBKR")
                return True
            else:
                logger.error("Failed to connect to IBKR within timeout")
                return False
                
        except Exception as e:
            logger.error(f"IBKR connection error: {e}")
            return False
    
    def _run_api(self):
        """Run the IBKR API in a separate thread."""
        try:
            self.client.connect(
                self.config.host, 
                self.config.port, 
                self.config.client_id
            )
            self.client.run()
        except Exception as e:
            logger.error(f"IBKR API thread error: {e}")
    
    def disconnect(self):
        """Disconnect from IBKR API."""
        if self.connected:
            self.client.disconnect()
            self.connected = False
            logger.info("Disconnected from IBKR")
    
    def _create_stock_contract(self, symbol: str, exchange: str = "SMART") -> Contract:
        """Create a stock contract."""
        contract = Contract()
        contract.symbol = symbol.upper()
        contract.secType = "STK"
        contract.exchange = exchange
        contract.currency = "USD"
        return contract
    
    async def get_historical_data(
        self,
        symbol: str,
        duration: str = "1 Y",
        bar_size: str = "1 day",
        what_to_show: str = "TRADES"
    ) -> pd.DataFrame:
        """
        Get historical market data.
        
        Args:
            symbol: Stock symbol
            duration: Duration (e.g., "1 Y", "6 M", "30 D")
            bar_size: Bar size (e.g., "1 day", "1 hour", "5 mins")
            what_to_show: Data type (TRADES, MIDPOINT, BID, ASK)
            
        Returns:
            DataFrame with historical data
        """
        if not self.connected:
            raise ConnectionError("Not connected to IBKR")
        
        try:
            # Create contract
            contract = self._create_stock_contract(symbol)
            
            # Get request ID
            req_id = self.client.get_next_request_id()
            
            # Request historical data
            self.client.reqHistoricalData(
                req_id,
                contract,
                "",  # End date (empty = now)
                duration,
                bar_size,
                what_to_show,
                1,  # Use regular trading hours
                1,  # Format date
                False,  # Keep up to date
                []
            )
            
            # Wait for data
            timeout = time.time() + self.config.timeout
            while req_id not in self.wrapper.historical_data and time.time() < timeout:
                try:
                    msg = self.wrapper.data_queue.get(timeout=1)
                    if msg.get("type") == "historical_complete" and msg.get("reqId") == req_id:
                        break
                except Empty:
                    continue
            
            if req_id not in self.wrapper.historical_data:
                raise TimeoutError(f"Historical data request timed out for {symbol}")
            
            # Convert to DataFrame
            data = self.wrapper.historical_data[req_id]
            df = pd.DataFrame(data)
            
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df['symbol'] = symbol
                df = df.sort_values('date').reset_index(drop=True)
            
            # Clean up
            del self.wrapper.historical_data[req_id]
            
            logger.info(f"Retrieved {len(df)} historical bars for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {e}")
            raise
    
    async def get_multiple_historical_data(
        self,
        symbols: List[str],
        duration: str = "1 Y",
        bar_size: str = "1 day"
    ) -> Dict[str, pd.DataFrame]:
        """
        Get historical data for multiple symbols.
        
        Args:
            symbols: List of stock symbols
            duration: Duration for each symbol
            bar_size: Bar size for each symbol
            
        Returns:
            Dictionary mapping symbols to DataFrames
        """
        results = {}
        
        for symbol in symbols:
            try:
                data = await self.get_historical_data(symbol, duration, bar_size)
                results[symbol] = data
                
                # Add small delay to avoid rate limiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Failed to get data for {symbol}: {e}")
                results[symbol] = pd.DataFrame()
        
        return results
    
    async def subscribe_real_time(self, symbol: str) -> int:
        """
        Subscribe to real-time market data.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Request ID for the subscription
        """
        if not self.connected:
            raise ConnectionError("Not connected to IBKR")
        
        try:
            contract = self._create_stock_contract(symbol)
            req_id = self.client.get_next_request_id()
            
            # Request market data
            self.client.reqMktData(
                req_id,
                contract,
                "",  # Generic tick list
                False,  # Snapshot
                False,  # Regulatory snapshot
                []
            )
            
            logger.info(f"Subscribed to real-time data for {symbol} (ID: {req_id})")
            return req_id
            
        except Exception as e:
            logger.error(f"Error subscribing to real-time data for {symbol}: {e}")
            raise
    
    def unsubscribe_real_time(self, req_id: int):
        """
        Unsubscribe from real-time market data.
        
        Args:
            req_id: Request ID from subscription
        """
        try:
            self.client.cancelMktData(req_id)
            if req_id in self.wrapper.real_time_data:
                del self.wrapper.real_time_data[req_id]
            logger.info(f"Unsubscribed from real-time data (ID: {req_id})")
        except Exception as e:
            logger.error(f"Error unsubscribing from real-time data: {e}")
    
    def get_real_time_price(self, req_id: int) -> Optional[Dict[str, Any]]:
        """
        Get latest real-time price data.
        
        Args:
            req_id: Request ID from subscription
            
        Returns:
            Dictionary with latest price data
        """
        if req_id in self.wrapper.real_time_data:
            return self.wrapper.real_time_data[req_id]
        return None
    
    async def get_account_summary(self) -> Dict[str, Any]:
        """
        Get account summary information.
        
        Returns:
            Dictionary with account information
        """
        if not self.connected:
            raise ConnectionError("Not connected to IBKR")
        
        # This would require additional implementation for account data
        # For now, return a placeholder
        return {
            "account_id": "DU123456",
            "net_liquidation": 100000.0,
            "total_cash_value": 50000.0,
            "settled_cash": 50000.0,
            "excess_liquidity": 75000.0,
            "buying_power": 400000.0,
            "gross_position_value": 50000.0
        }
    
    def get_connection_status(self) -> Dict[str, Any]:
        """
        Get connection status information.
        
        Returns:
            Dictionary with connection details
        """
        return {
            "connected": self.connected,
            "host": self.config.host,
            "port": self.config.port,
            "client_id": self.config.client_id,
            "wrapper_status": self.wrapper.connection_status,
            "next_order_id": self.wrapper.next_order_id,
            "active_subscriptions": len(self.wrapper.real_time_data)
        }
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()

# Fallback mock client for when IBKR is not available
class MockIBKRDataClient:
    """Mock IBKR client for testing and fallback."""
    
    def __init__(self, config: Optional[IBKRConfig] = None):
        self.config = config or IBKRConfig()
        self.connected = False
        logger.warning("Using mock IBKR client - no real data available")
    
    async def connect(self) -> bool:
        """Mock connection."""
        await asyncio.sleep(0.1)
        self.connected = True
        return True
    
    def disconnect(self):
        """Mock disconnection."""
        self.connected = False
    
    async def get_historical_data(
        self,
        symbol: str,
        duration: str = "1 Y",
        bar_size: str = "1 day",
        what_to_show: str = "TRADES"
    ) -> pd.DataFrame:
        """Mock historical data."""
        # Generate mock data
        import yfinance as yf
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1y")
            data.reset_index(inplace=True)
            data.columns = data.columns.str.lower()
            data['symbol'] = symbol
            return data
        except:
            # Fallback mock data
            dates = pd.date_range(end=datetime.now(), periods=252, freq='D')
            data = pd.DataFrame({
                'date': dates,
                'open': np.random.uniform(100, 200, 252),
                'high': np.random.uniform(100, 200, 252),
                'low': np.random.uniform(100, 200, 252),
                'close': np.random.uniform(100, 200, 252),
                'volume': np.random.randint(1000000, 10000000, 252),
                'symbol': symbol
            })
            return data
    
    async def get_multiple_historical_data(
        self,
        symbols: List[str],
        duration: str = "1 Y",
        bar_size: str = "1 day"
    ) -> Dict[str, pd.DataFrame]:
        """Mock multiple historical data."""
        results = {}
        for symbol in symbols:
            results[symbol] = await self.get_historical_data(symbol, duration, bar_size)
        return results
    
    async def subscribe_real_time(self, symbol: str) -> int:
        """Mock real-time subscription."""
        return hash(symbol) % 10000
    
    def unsubscribe_real_time(self, req_id: int):
        """Mock unsubscribe."""
        pass
    
    def get_real_time_price(self, req_id: int) -> Optional[Dict[str, Any]]:
        """Mock real-time price."""
        return {
            "LAST": {"price": np.random.uniform(100, 200), "timestamp": datetime.now()},
            "BID": {"price": np.random.uniform(100, 200), "timestamp": datetime.now()},
            "ASK": {"price": np.random.uniform(100, 200), "timestamp": datetime.now()}
        }
    
    async def get_account_summary(self) -> Dict[str, Any]:
        """Mock account summary."""
        return {
            "account_id": "MOCK123456",
            "net_liquidation": 100000.0,
            "total_cash_value": 50000.0,
            "settled_cash": 50000.0,
            "excess_liquidity": 75000.0,
            "buying_power": 400000.0,
            "gross_position_value": 50000.0
        }
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Mock connection status."""
        return {
            "connected": self.connected,
            "host": self.config.host,
            "port": self.config.port,
            "client_id": self.config.client_id,
            "mock_mode": True
        }

# Factory function to create appropriate client
def create_ibkr_client(config: Optional[IBKRConfig] = None, use_mock: bool = False):
    """
    Create IBKR client (real or mock).
    
    Args:
        config: IBKR configuration
        use_mock: Force use of mock client
        
    Returns:
        IBKR client instance
    """
    if use_mock or not IBKR_AVAILABLE:
        return MockIBKRDataClient(config)
    else:
        return IBKRDataClient(config)