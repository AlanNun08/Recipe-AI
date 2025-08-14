"""
Unit tests for recipe service
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.services.recipe import RecipeService
from backend.models.recipe import RecipeGeneration, WeeklyRecipeGeneration

class TestRecipeService:
    """Test recipe service"""
    
    @pytest.mark.asyncio
    @patch('backend.services.recipe.db_service')
    async def test_generate_fallback_recipe(self, mock_db):
        """Test fallback recipe generation"""
        # Setup mocks
        mock_db.recipes_collection.insert_one = AsyncMock()
        
        # Create service instance
        service = RecipeService()
        service.ai_enabled = False
        
        # Test recipe generation
        request = RecipeGeneration(
            user_id="test-user-id",
            cuisine_type="italian",
            difficulty="easy",
            servings=4
        )
        
        recipe = await service.generate_recipe(request)
        
        assert recipe.user_id == "test-user-id"
        assert recipe.cuisine_type == "italian"
        assert recipe.difficulty == "easy"
        assert recipe.servings == 4
        assert len(recipe.ingredients) > 0
        assert len(recipe.instructions) > 0
        mock_db.recipes_collection.insert_one.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('backend.services.recipe.db_service')
    @patch('backend.services.recipe.OpenAI')
    async def test_generate_ai_recipe(self, mock_openai_class, mock_db):
        """Test AI recipe generation"""
        # Setup mocks
        mock_db.recipes_collection.insert_one = AsyncMock()
        
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"name": "AI Recipe", "description": "AI generated", "ingredients": ["ingredient 1"], "instructions": ["step 1"], "prep_time": "10 min", "cook_time": "20 min", "calories": 300}'
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        # Create service instance with AI enabled
        service = RecipeService()
        service.ai_enabled = True
        service.openai_client = mock_client
        
        # Test recipe generation
        request = RecipeGeneration(
            user_id="test-user-id",
            cuisine_type="italian",
            difficulty="easy",
            servings=4
        )
        
        recipe = await service.generate_recipe(request)
        
        assert recipe.name == "AI Recipe"
        assert recipe.description == "AI generated"
        assert recipe.calories == 300
        mock_db.recipes_collection.insert_one.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('backend.services.recipe.db_service')
    async def test_get_user_recipes(self, mock_db):
        """Test getting user recipes"""
        # Setup mock
        mock_recipes = [
            {"id": "recipe1", "name": "Recipe 1"},
            {"id": "recipe2", "name": "Recipe 2"}
        ]
        
        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=mock_recipes)
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        
        mock_db.recipes_collection.find.return_value = mock_cursor
        
        # Create service instance
        service = RecipeService()
        
        # Test getting recipes
        recipes = await service.get_user_recipes("test-user-id", 10)
        
        assert len(recipes) == 2
        assert recipes[0]["name"] == "Recipe 1"
        mock_db.recipes_collection.find.assert_called_once_with({"user_id": "test-user-id"})
    
    @pytest.mark.asyncio
    @patch('backend.services.recipe.db_service')
    async def test_delete_recipe_success(self, mock_db):
        """Test successful recipe deletion"""
        # Setup mock
        mock_result = MagicMock()
        mock_result.deleted_count = 1
        mock_db.recipes_collection.delete_one = AsyncMock(return_value=mock_result)
        
        # Create service instance
        service = RecipeService()
        
        # Test deletion
        success = await service.delete_recipe("recipe-id", "user-id")
        
        assert success is True
        mock_db.recipes_collection.delete_one.assert_called_once_with({
            "id": "recipe-id",
            "user_id": "user-id"
        })
    
    @pytest.mark.asyncio
    @patch('backend.services.recipe.db_service')
    async def test_delete_recipe_not_found(self, mock_db):
        """Test recipe deletion when recipe not found"""
        # Setup mock
        mock_result = MagicMock()
        mock_result.deleted_count = 0
        mock_db.recipes_collection.delete_one = AsyncMock(return_value=mock_result)
        
        # Create service instance
        service = RecipeService()
        
        # Test deletion
        success = await service.delete_recipe("recipe-id", "user-id")
        
        assert success is False