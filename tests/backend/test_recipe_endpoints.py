import pytest
import json
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
from server import app
import uuid
from datetime import datetime

@pytest.fixture
async def client():
    """Create test client for API testing."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def mock_user():
    """Mock user data for testing."""
    return {
        "id": str(uuid.uuid4()),
        "email": "test@example.com",
        "subscription": {
            "status": "active",
            "trial_ends_at": datetime.utcnow().isoformat()
        }
    }

@pytest.fixture
def mock_recipe():
    """Mock recipe data for testing."""
    return {
        "id": str(uuid.uuid4()),
        "name": "Test Recipe",
        "description": "A test recipe for unit testing",
        "ingredients": ["2 cups flour", "1 cup sugar", "3 eggs"],
        "instructions": ["Mix ingredients", "Bake at 350°F", "Cool and serve"],
        "prep_time": "15 minutes",
        "cook_time": "30 minutes",
        "servings": 4,
        "difficulty": "easy",
        "cuisine_type": "american"
    }

class TestRecipeGeneration:
    """Test suite for recipe generation endpoints."""

    @patch('server.users_collection.find_one')
    @patch('server.recipes_collection.insert_one')
    @patch('server.generate_ai_recipe')
    async def test_generate_recipe_success(
        self, 
        mock_generate, 
        mock_insert, 
        mock_find_user, 
        client, 
        mock_user, 
        mock_recipe
    ):
        """Test successful recipe generation."""
        mock_find_user.return_value = mock_user
        mock_generate.return_value = mock_recipe
        mock_insert.return_value = AsyncMock()
        
        request_data = {
            "user_id": mock_user["id"],
            "cuisine_type": "italian",
            "difficulty": "easy",
            "servings": 4,
            "dietary_preferences": ["vegetarian"],
            "ingredients": ["tomatoes", "basil"]
        }
        
        response = await client.post("/api/recipes/generate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Recipe"
        assert data["cuisine_type"] == "american"
        assert len(data["ingredients"]) == 3
        assert len(data["instructions"]) == 3

    @patch('server.users_collection.find_one')
    async def test_generate_recipe_user_not_found(self, mock_find_user, client):
        """Test recipe generation with invalid user."""
        mock_find_user.return_value = None
        
        request_data = {
            "user_id": "invalid-user-id",
            "cuisine_type": "italian",
            "difficulty": "easy",
            "servings": 4
        }
        
        response = await client.post("/api/recipes/generate", json=request_data)
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "User not found"

class TestRecipeHistory:
    """Test suite for recipe history endpoints."""

    @patch('server.recipes_collection.find')
    @patch('server.starbucks_recipes_collection.find')
    async def test_get_recipe_history_success(
        self, 
        mock_starbucks_find, 
        mock_recipes_find, 
        client, 
        mock_user
    ):
        """Test successful recipe history retrieval."""
        mock_recipes = [
            {
                "_id": "obj_id_1",
                "id": "recipe-1",
                "user_id": mock_user["id"],
                "name": "Test Recipe 1",
                "created_at": "2025-01-10T12:00:00Z"
            }
        ]
        mock_starbucks = [
            {
                "_id": "obj_id_2", 
                "id": "starbucks-1",
                "user_id": mock_user["id"],
                "name": "Test Starbucks Drink",
                "created_at": "2025-01-09T14:00:00Z"
            }
        ]
        
        mock_recipes_find.return_value.sort.return_value.to_list = AsyncMock(return_value=mock_recipes)
        mock_starbucks_find.return_value.sort.return_value.to_list = AsyncMock(return_value=mock_starbucks)
        
        response = await client.get(f"/api/recipes/history/{mock_user['id']}")
        
        assert response.status_code == 200
        data = response.json()
        assert "recipes" in data
        assert len(data["recipes"]) == 2
        assert data["total_count"] == 2

class TestRecipeDetail:
    """Test suite for recipe detail endpoints."""

    @patch('server.recipes_collection.find_one')
    async def test_get_recipe_detail_success(
        self, 
        mock_find_one, 
        client, 
        mock_recipe
    ):
        """Test successful recipe detail retrieval."""
        mock_find_one.return_value = {**mock_recipe, "_id": "obj_id"}
        
        response = await client.get(f"/api/recipes/{mock_recipe['id']}/detail")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == mock_recipe["id"]
        assert data["name"] == mock_recipe["name"]
        assert len(data["ingredients"]) == 3
        assert len(data["instructions"]) == 3

    @patch('server.recipes_collection.find_one')
    async def test_get_recipe_detail_not_found(self, mock_find_one, client):
        """Test recipe detail with non-existent recipe."""
        mock_find_one.return_value = None
        
        with patch('server.starbucks_recipes_collection.find_one', return_value=None):
            with patch('server.curated_starbucks_recipes_collection.find_one', return_value=None):
                response = await client.get("/api/recipes/nonexistent-id/detail")
                
                assert response.status_code == 404
                data = response.json()
                assert data["detail"] == "Recipe not found"

__all__ = ['client', 'mock_user', 'mock_recipe']