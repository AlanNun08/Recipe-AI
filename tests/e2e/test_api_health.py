"""
End-to-end tests for API health and basic functionality
"""
import pytest
from httpx import AsyncClient
from backend.main import app

class TestAPIHealth:
    """Test API health and basic functionality"""
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """Test health check endpoint"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code in [200, 503]
            
            data = response.json()
            assert "status" in data
            assert "service" in data
            assert "version" in data
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self):
        """Test root endpoint"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/")
            assert response.status_code == 200
            
            data = response.json()
            assert "message" in data
            assert "version" in data
            assert "features" in data
    
    @pytest.mark.asyncio
    async def test_docs_endpoint(self):
        """Test API documentation endpoint"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/docs")
            # Should be available in development
            assert response.status_code in [200, 404]
    
    @pytest.mark.asyncio
    async def test_nonexistent_endpoint(self):
        """Test handling of nonexistent endpoints"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/nonexistent")
            assert response.status_code == 404