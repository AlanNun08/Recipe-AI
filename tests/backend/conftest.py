"""Pytest configuration and shared fixtures."""
import pytest
import asyncio
import uuid
from datetime import datetime
from typing import AsyncGenerator, Generator
from motor.motor_asyncio import AsyncIOMotorClient
from httpx import AsyncClient
from server import app

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def test_client() -> AsyncGenerator[AsyncClient, None]:
    """Create a test client for the FastAPI application."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
async def test_database() -> AsyncGenerator[AsyncIOMotorClient, None]:
    """Create an isolated test database."""
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db_name = f"test_db_{uuid.uuid4().hex[:8]}"
    db = client[db_name]
    
    yield db
    
    # Cleanup after test
    await client.drop_database(db_name)
    client.close()

@pytest.fixture
def mock_user_data() -> dict:
    """Create mock user data for testing."""
    return {
        "id": str(uuid.uuid4()),
        "email": "test@example.com",
        "password": "testpassword123",
        "is_verified": True,
        "subscription": {
            "status": "active",
            "trial_starts_at": datetime.utcnow().isoformat(),
            "trial_ends_at": datetime.utcnow().isoformat(),
            "customer_id": "cus_test123",
            "subscription_id": "sub_test123"
        },
        "preferences": {
            "dietary_preferences": ["vegetarian"],
            "allergies": ["nuts"],
            "favorite_cuisines": ["italian", "mexican"]
        },
        "created_at": datetime.utcnow().isoformat()
    }

@pytest.fixture
def mock_recipe_data() -> dict:
    """Create mock recipe data for testing."""
    return {
        "id": str(uuid.uuid4()),
        "user_id": "test-user-id",
        "name": "Test Recipe",
        "description": "A delicious test recipe",
        "ingredients": [
            "2 cups flour",
            "1 cup sugar", 
            "3 large eggs",
            "1 tsp vanilla extract"
        ],
        "instructions": [
            "Preheat oven to 350°F (175°C)",
            "Mix dry ingredients in a large bowl",
            "In separate bowl, beat eggs and add vanilla",
            "Combine wet and dry ingredients",
            "Bake for 25-30 minutes"
        ],
        "prep_time": "15 minutes",
        "cook_time": "30 minutes",
        "servings": 4,
        "difficulty": "easy",
        "cuisine_type": "american",
        "created_at": datetime.utcnow().isoformat()
    }

@pytest.fixture
def mock_weekly_recipe_data() -> dict:
    """Create mock weekly recipe data for testing."""
    return {
        "id": str(uuid.uuid4()),
        "user_id": "test-user-id",
        "week_of": "2025-W02",
        "plan_name": "Test Weekly Plan",
        "meals": {
            "monday": {
                "id": str(uuid.uuid4()),
                "name": "Monday Test Meal",
                "day": "Monday",
                "cuisine": "italian",
                "prep_time": "20 minutes",
                "cook_time": "25 minutes",
                "servings": 2,
                "ingredients": ["pasta", "tomatoes", "basil"],
                "instructions": ["Boil pasta", "Add sauce", "Serve hot"]
            }
        },
        "total_budget": 85.50,
        "created_at": datetime.utcnow().isoformat()
    }

@pytest.fixture
def mock_starbucks_recipe_data() -> dict:
    """Create mock Starbucks recipe data for testing."""
    return {
        "id": str(uuid.uuid4()),
        "user_id": "test-user-id",
        "name": "Test Frappuccino",
        "description": "A test Starbucks drink recipe",
        "instructions": [
            "Add ice to blender",
            "Pour coffee and milk",
            "Add flavorings",
            "Blend until smooth"
        ],
        "category": "frappuccino",
        "difficulty": "easy",
        "created_at": datetime.utcnow().isoformat()
    }

# Utility functions for test setup
async def create_test_user(db, user_data: dict) -> str:
    """Create a test user in the database."""
    result = await db.users.insert_one(user_data)
    return user_data["id"]

async def create_test_recipe(db, recipe_data: dict) -> str:
    """Create a test recipe in the database."""
    result = await db.recipes.insert_one(recipe_data)
    return recipe_data["id"]

async def cleanup_test_collections(db, collections: list = None):
    """Clean up test collections."""
    if collections is None:
        collections = ["users", "recipes", "weekly_recipes", "starbucks_recipes"]
    
    for collection_name in collections:
        await db[collection_name].delete_many({})

# Mock external services
@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    return {
        "choices": [{
            "message": {
                "content": '{"name": "Mock Recipe", "description": "A mock recipe for testing", "ingredients": ["ingredient1", "ingredient2"], "instructions": ["step1", "step2"], "prep_time": "10 minutes", "cook_time": "15 minutes", "servings": 2, "difficulty": "easy", "cuisine_type": "test"}'
            }
        }]
    }

@pytest.fixture
def mock_walmart_response():
    """Mock Walmart API response."""
    return {
        "items": [
            {
                "itemId": "123456789",
                "name": "Test Product",
                "salePrice": 2.99,
                "mediumImage": "https://example.com/image.jpg",
                "brandName": "Test Brand",
                "customerRating": 4.5
            }
        ]
    }

@pytest.fixture
def mock_stripe_response():
    """Mock Stripe API response."""
    return {
        "id": "cs_test_123456789",
        "url": "https://checkout.stripe.com/pay/test_session",
        "payment_status": "unpaid",
        "customer": "cus_test123"
    }