"""
Tests for API endpoints.
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock

@pytest.mark.api
@pytest.mark.asyncio
class TestAPIEndpoints:
    """Test suite for API endpoints."""
    
    async def test_health_endpoint(self, async_test_client):
        """Test health endpoint."""
        response = await async_test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    async def test_config_endpoint(self, async_test_client):
        """Test config endpoint."""
        response = await async_test_client.get("/config")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "features" in data
    
    @patch("comprehensive_api.FORMULA_ENGINE_AVAILABLE", True)
    async def test_formula_functions_endpoint(self, async_test_client):
        """Test formula functions endpoint."""
        response = await async_test_client.get("/formula/functions")
        assert response.status_code == 200
        data = response.json()
        assert "functions" in data
        assert isinstance(data["functions"], list)
    
    @patch("comprehensive_api.FORMULA_ENGINE_AVAILABLE", True)
    async def test_formula_validate_endpoint(self, async_test_client):
        """Test formula validation endpoint."""
        payload = {"formula": "close > open"}
        response = await async_test_client.post("/formula/validate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "valid" in data
    
    @patch("comprehensive_api.FORMULA_ENGINE_AVAILABLE", True)
    async def test_formula_models_crud(self, async_test_client):
        """Test formula models CRUD operations."""
        # Create model
        model_data = {
            "name": "test_model",
            "formula": "close > open",
            "description": "Test model",
            "variables": {}
        }
        response = await async_test_client.post("/formula/models", json=model_data)
        assert response.status_code == 200
        
        # List models
        response = await async_test_client.get("/formula/models")
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        
        # Get specific model
        response = await async_test_client.get("/formula/models/test_model")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test_model"
        
        # Delete model
        response = await async_test_client.delete("/formula/models/test_model")
        assert response.status_code == 200
    
    @patch("comprehensive_api.FORMULA_ENGINE_AVAILABLE", False)
    async def test_formula_endpoints_unavailable(self, async_test_client):
        """Test formula endpoints when formula engine is unavailable."""
        response = await async_test_client.get("/formula/functions")
        assert response.status_code == 503
    
    async def test_portfolio_summary_endpoint(self, async_test_client):
        """Test portfolio summary endpoint."""
        with patch("comprehensive_api.get_portfolio_manager") as mock_manager:
            mock_manager.return_value.get_portfolio_summary = AsyncMock(return_value={
                "total_value": 100000,
                "cash": 25000,
                "positions_value": 75000
            })
            
            response = await async_test_client.get("/portfolio/summary")
            assert response.status_code == 200
            data = response.json()
            assert "total_value" in data
    
    async def test_market_quotes_endpoint(self, async_test_client):
        """Test market quotes endpoint."""
        with patch("comprehensive_api.get_stock_price") as mock_price:
            mock_price.ainvoke = AsyncMock(return_value={
                "symbol": "AAPL",
                "price": 150.0,
                "change": 2.5
            })
            
            response = await async_test_client.get("/market/quotes?symbols=AAPL")
            assert response.status_code == 200
            data = response.json()
            assert "quotes" in data
    
    async def test_websocket_connection(self, async_test_client):
        """Test WebSocket connection."""
        with async_test_client.websocket_connect("/ws") as websocket:
            # Test connection established
            data = await websocket.receive_json()
            assert data["type"] == "connection_established"
    
    async def test_error_handling(self, async_test_client):
        """Test API error handling."""
        # Test 404 for non-existent endpoint
        response = await async_test_client.get("/nonexistent")
        assert response.status_code == 404
        
        # Test 422 for invalid request body
        response = await async_test_client.post("/formula/validate", json={})
        assert response.status_code == 422

@pytest.mark.api
class TestAPIValidation:
    """Test suite for API request validation."""
    
    @pytest.mark.asyncio
    async def test_formula_model_validation(self, async_test_client):
        """Test formula model validation."""
        # Test missing required fields
        invalid_payload = {"name": "test"}
        response = await async_test_client.post("/formula/models", json=invalid_payload)
        assert response.status_code == 422
        
        # Test invalid data types
        invalid_payload = {"name": 123, "formula": "close > open"}
        response = await async_test_client.post("/formula/models", json=invalid_payload)
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_backtest_request_validation(self, async_test_client):
        """Test backtest request validation."""
        # Test valid request
        valid_payload = {
            "model_name": "test_model",
            "data": {"close": [100, 101, 102], "open": [99, 100, 101]},
            "initial_capital": 100000
        }
        
        with patch("comprehensive_api.FORMULA_ENGINE_AVAILABLE", True):
            response = await async_test_client.post("/formula/backtest", json=valid_payload)
            # Should not be 422 (validation error)
            assert response.status_code != 422
    
    @pytest.mark.asyncio
    async def test_parameter_validation(self, async_test_client):
        """Test API parameter validation."""
        # Test invalid parameter values
        response = await async_test_client.get("/market/quotes?symbols=")
        assert response.status_code in [400, 422]

@pytest.mark.api
@pytest.mark.integration
class TestAPIIntegration:
    """Integration tests for API endpoints."""
    
    @pytest.mark.asyncio
    async def test_formula_workflow_integration(self, async_test_client):
        """Test complete formula workflow through API."""
        with patch("comprehensive_api.FORMULA_ENGINE_AVAILABLE", True):
            # 1. Create model
            model_data = {
                "name": "integration_model",
                "formula": "MA(close, 10) > MA(close, 20)",
                "description": "Integration test model"
            }
            response = await async_test_client.post("/formula/models", json=model_data)
            assert response.status_code == 200
            
            # 2. Validate formula
            validate_data = {"formula": "MA(close, 10) > MA(close, 20)"}
            response = await async_test_client.post("/formula/validate", json=validate_data)
            assert response.status_code == 200
            assert response.json()["valid"] is True
            
            # 3. Get model info
            response = await async_test_client.get("/formula/models/integration_model")
            assert response.status_code == 200
            assert response.json()["name"] == "integration_model"
            
            # 4. Get function info
            response = await async_test_client.get("/formula/functions/MA")
            assert response.status_code == 200
            
            # 5. Clean up
            response = await async_test_client.delete("/formula/models/integration_model")
            assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_market_data_flow(self, async_test_client):
        """Test market data flow through API."""
        with patch("comprehensive_api.get_stock_price") as mock_price:
            mock_price.ainvoke = AsyncMock(return_value={
                "symbol": "AAPL",
                "price": 150.0,
                "change": 2.5,
                "volume": 1000000
            })
            
            # Get quotes
            response = await async_test_client.get("/market/quotes?symbols=AAPL")
            assert response.status_code == 200
            
            # Get trends
            response = await async_test_client.get("/market/trends?symbols=AAPL")
            assert response.status_code == 200
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_performance_under_load(self, async_test_client):
        """Test API performance under load."""
        import asyncio
        
        async def make_request():
            response = await async_test_client.get("/health")
            return response.status_code
        
        # Make 10 concurrent requests
        tasks = [make_request() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        # All requests should succeed
        assert all(status == 200 for status in results)

@pytest.mark.api
@pytest.mark.network
class TestAPINetworking:
    """Test suite for API networking and external dependencies."""
    
    @pytest.mark.asyncio
    async def test_external_api_integration(self, async_test_client):
        """Test integration with external APIs."""
        # Mock external API calls
        with patch("comprehensive_api.get_stock_price") as mock_price:
            mock_price.ainvoke = AsyncMock(return_value={
                "symbol": "AAPL",
                "price": 150.0
            })
            
            response = await async_test_client.get("/market/quotes?symbols=AAPL")
            assert response.status_code == 200
            mock_price.ainvoke.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, async_test_client):
        """Test timeout handling for slow requests."""
        with patch("comprehensive_api.get_stock_price") as mock_price:
            mock_price.ainvoke = AsyncMock(side_effect=asyncio.TimeoutError())
            
            response = await async_test_client.get("/market/quotes?symbols=AAPL")
            # Should handle timeout gracefully
            assert response.status_code in [500, 503, 504]
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, async_test_client):
        """Test API rate limiting behavior."""
        # This would test rate limiting if implemented
        # For now, just verify the endpoint responds
        response = await async_test_client.get("/health")
        assert response.status_code == 200