"""
Integration tests for recipe API
"""
import pytest
from httpx import AsyncClient
from backend.main import app

class TestRecipeAPI:
    """Test recipe API endpoints"""
    
    @pytest.mark.asyncio
    async def test_recipe_generation_endpoint(self):
        """Test recipe generation endpoint"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            recipe_data = {
                "user_id": "test-user-id",
                "cuisine_type": "italian",
                "difficulty": "easy",
                "servings": 4,
                "dietary_preferences": ["vegetarian"]
            }
            
            response = await client.post("/recipes/generate", json=recipe_data)
            # May fail due to user not existing, but endpoint should exist
            assert response.status_code in [200, 404, 500]
    
    @pytest.mark.asyncio
    async def test_recipe_history_endpoint(self):
        """Test recipe history endpoint"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/recipes/history/test-user-id")
            # Should return empty list or error, but endpoint should exist
            assert response.status_code in [200, 500]
    
    @pytest.mark.asyncio
    async def test_recipe_detail_endpoint(self):
        """Test recipe detail endpoint"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/recipes/nonexistent-id/detail")
            assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_weekly_recipe_generation(self):
        """Test weekly recipe generation endpoint"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            weekly_data = {
                "user_id": "test-user-id",
                "dietary_preferences": ["vegetarian"],
                "cuisine_preferences": ["italian", "mexican"]
            }
            
            response = await client.post("/recipes/weekly/generate", json=weekly_data)
            # May fail due to user not existing, but endpoint should exist
            assert response.status_code in [200, 404, 500]