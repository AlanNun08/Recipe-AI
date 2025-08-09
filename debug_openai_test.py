#!/usr/bin/env python3
"""
Debug OpenAI API Key and Recipe Generation
"""

import os
import sys
import asyncio
from pathlib import Path

# Add backend to path
sys.path.append('/app/backend')
sys.path.append('/app')

async def test_openai_directly():
    """Test OpenAI API directly"""
    print("=== Testing OpenAI API Directly ===")
    
    try:
        # Load environment variables
        from dotenv import load_dotenv
        env_path = Path('/app/backend/.env')
        load_dotenv(env_path)
        
        openai_key = os.environ.get('OPENAI_API_KEY')
        print(f"OpenAI API Key: {openai_key[:20]}..." if openai_key else "No OpenAI API Key found")
        
        if not openai_key or 'your-' in openai_key.lower() or 'placeholder' in openai_key.lower():
            print("❌ OpenAI API Key is placeholder - this explains the 500 errors")
            return False
            
        # Try to import and use OpenAI
        from openai import OpenAI
        
        client = OpenAI(api_key=openai_key)
        
        # Test a simple completion
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say hello"}
            ],
            max_tokens=10
        )
        
        print("✅ OpenAI API is working!")
        print(f"Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI API Error: {str(e)}")
        return False

async def test_backend_recipe_function():
    """Test the backend recipe generation function directly"""
    print("=== Testing Backend Recipe Function ===")
    
    try:
        # Import the backend modules
        from backend.server import openai_client, RecipeGenRequest, Recipe
        from backend.server import users_collection, recipes_collection
        
        print("✅ Backend modules imported successfully")
        
        # Create a test request
        request = RecipeGenRequest(
            user_id="test-user-123",
            recipe_category="cuisine",
            cuisine_type="Chinese",
            dietary_preferences=[],
            ingredients_on_hand=["yogurt"],
            prep_time_max=30,
            servings=2,
            difficulty="easy"
        )
        
        print(f"Test request: {request}")
        
        # Try to generate a recipe using the same logic as the backend
        prompt = f"""Create a {request.difficulty} {request.cuisine_type} recipe for {request.servings} people.
        
Available ingredients: {', '.join(request.ingredients_on_hand) if request.ingredients_on_hand else 'None specified'}
Maximum prep time: {request.prep_time_max} minutes
Dietary preferences: {', '.join(request.dietary_preferences) if request.dietary_preferences else 'None'}

Please provide a complete recipe with:
1. A creative title
2. Brief description
3. Complete ingredients list (including the available ingredients)
4. Step-by-step instructions
5. Prep and cook times
6. Nutritional information if possible

Format as JSON with these fields:
- title
- description  
- ingredients (array)
- instructions (array)
- prep_time (minutes)
- cook_time (minutes)
- cuisine_type
- difficulty
- calories_per_serving (optional)
"""

        print("Attempting OpenAI API call...")
        
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional chef and recipe developer. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.7
        )
        
        print("✅ OpenAI API call successful!")
        
        # Parse the response
        recipe_json = response.choices[0].message.content.strip()
        print(f"Raw response: {recipe_json[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Backend recipe function error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("🔍 Debugging Recipe Generation Issues")
    print("=" * 50)
    
    # Test 1: OpenAI API directly
    openai_works = await test_openai_directly()
    
    print("\n" + "=" * 50)
    
    # Test 2: Backend recipe function
    if openai_works:
        backend_works = await test_backend_recipe_function()
    else:
        print("Skipping backend test due to OpenAI API issues")
        backend_works = False
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print(f"OpenAI API: {'✅ Working' if openai_works else '❌ Failed'}")
    print(f"Backend Function: {'✅ Working' if backend_works else '❌ Failed'}")
    
    if not openai_works:
        print("\n🔧 SOLUTION: The OpenAI API key is a placeholder.")
        print("This is why recipe generation returns 500 errors.")
        print("The system should fall back to mock data when OpenAI fails.")

if __name__ == "__main__":
    asyncio.run(main())