"""
Test configuration and fixtures
"""
import pytest
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from httpx import AsyncClient
import uuid
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from backend.main import app
from backend.services.database import DatabaseService

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def test_db():
    """Create isolated test database for each test"""
    test_db_name = f"test_{uuid.uuid4().hex[:8]}"
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client[test_db_name]
    
    yield db
    
    # Cleanup
    await client.drop_database(test_db_name)
    client.close()

@pytest.fixture(scope="function")
async def test_client():
    """Create test client for API testing"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def sample_user():
    """Sample user data for testing"""
    return {
        "id": str(uuid.uuid4()),
        "email": "test@example.com",
        "password": "testpassword123",
        "is_verified": True,
        "subscription": {
            "status": "trialing",
            "trial_starts_at": "2025-01-01T00:00:00Z",
            "trial_ends_at": "2025-01-08T00:00:00Z"
        },
        "usage_limits": {
            "weekly_recipes": {"used": 0, "limit": 2},
            "individual_recipes": {"used": 0, "limit": 10},
            "starbucks_drinks": {"used": 0, "limit": 10}
        }
    }

@pytest.fixture
def sample_recipe():
    """Sample recipe data for testing"""
    return {
        "id": str(uuid.uuid4()),
        "user_id": str(uuid.uuid4()),
        "name": "Test Recipe",
        "description": "A test recipe for unit testing",
        "ingredients": ["2 cups flour", "1 cup sugar", "3 eggs"],
        "instructions": ["Mix ingredients", "Bake at 350°F", "Cool and serve"],
        "prep_time": "15 minutes",
        "cook_time": "30 minutes",
        "servings": 4,
        "difficulty": "easy",
        "cuisine_type": "american",
        "calories": 300
    }