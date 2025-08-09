#!/usr/bin/env python3
"""
Frontend Scenario Test - Simulate the exact frontend workflow
"""

import asyncio
import httpx
import json
from datetime import datetime

BACKEND_URL = "https://2c83b5a7-3245-4a38-a9d6-ccc45cb3ba91.preview.emergentagent.com/api"

async def test_frontend_scenario():
    """Test the exact scenario that frontend would experience"""
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("🧪 Testing Frontend Scenario - Walmart Integration")
        print("=" * 60)
        
        # Step 1: Register and verify user (simulating frontend flow)
        print("Step 1: User Registration & Verification")
        
        # Clear any existing test data
        await client.delete(f"{BACKEND_URL}/debug/cleanup-test-data")
        
        # Register user
        user_data = {
            "first_name": "Frontend",
            "last_name": "Test",
            "email": "frontend.test@example.com",
            "password": "testpass123",
            "dietary_preferences": [],
            "allergies": [],
            "favorite_cuisines": ["Italian"]
        }
        
        reg_response = await client.post(f"{BACKEND_URL}/auth/register", json=user_data)
        if reg_response.status_code != 200:
            print(f"❌ Registration failed: {reg_response.text}")
            return False
        
        user_id = reg_response.json()["user_id"]
        print(f"✅ User registered: {user_id}")
        
        # Get verification code and verify
        debug_response = await client.get(f"{BACKEND_URL}/debug/verification-codes/frontend.test@example.com")
        if debug_response.status_code == 200:
            codes = debug_response.json().get("codes", [])
            if codes:
                verify_data = {
                    "email": "frontend.test@example.com",
                    "code": codes[0]["code"]
                }
                verify_response = await client.post(f"{BACKEND_URL}/auth/verify", json=verify_data)
                if verify_response.status_code == 200:
                    print("✅ User verified")
                else:
                    print(f"⚠️ Verification failed: {verify_response.text}")
        
        # Step 2: Generate Recipe (simulating frontend recipe generation)
        print("\nStep 2: Recipe Generation")
        
        recipe_data = {
            "user_id": user_id,
            "recipe_category": "cuisine",
            "cuisine_type": "Italian",
            "dietary_preferences": [],
            "ingredients_on_hand": [],
            "prep_time_max": 30,
            "servings": 4,
            "difficulty": "medium"
        }
        
        recipe_response = await client.post(f"{BACKEND_URL}/recipes/generate", json=recipe_data)
        if recipe_response.status_code != 200:
            print(f"❌ Recipe generation failed: {recipe_response.text}")
            return False
        
        recipe = recipe_response.json()
        recipe_id = recipe["id"]
        recipe_title = recipe["title"]
        shopping_list = recipe.get("shopping_list", [])
        
        print(f"✅ Recipe generated: {recipe_title}")
        print(f"   Recipe ID: {recipe_id}")
        print(f"   Shopping list: {shopping_list}")
        
        # Step 3: Get Cart Options (the exact call frontend makes)
        print("\nStep 3: Walmart Cart Options (Frontend Call)")
        
        # This is the EXACT call that frontend makes
        params = {
            "recipe_id": recipe_id,
            "user_id": user_id
        }
        
        print(f"Making POST to /grocery/cart-options with params: {params}")
        
        cart_response = await client.post(f"{BACKEND_URL}/grocery/cart-options", params=params)
        
        print(f"Response Status: {cart_response.status_code}")
        
        if cart_response.status_code == 200:
            cart_data = cart_response.json()
            
            print("✅ Cart options response received")
            print(f"   Recipe ID: {cart_data.get('recipe_id')}")
            print(f"   User ID: {cart_data.get('user_id')}")
            print(f"   Total products: {cart_data.get('total_products', 0)}")
            print(f"   Ingredient options: {len(cart_data.get('ingredient_options', []))}")
            
            if cart_data.get('message'):
                print(f"   Message: {cart_data['message']}")
            
            # Show detailed results
            ingredient_options = cart_data.get('ingredient_options', [])
            if ingredient_options:
                print("\n📦 Product Details:")
                for option in ingredient_options:
                    ingredient_name = option.get('ingredient_name')
                    products = option.get('options', [])
                    print(f"   {ingredient_name}: {len(products)} products")
                    for product in products[:2]:  # Show first 2
                        print(f"     - {product.get('name')} - ${product.get('price')}")
                
                print(f"\n🎉 SUCCESS: Found {cart_data.get('total_products', 0)} total products!")
                return True
            else:
                print("\n❌ ISSUE: No ingredient options returned")
                print("This matches the frontend issue reported!")
                return False
        else:
            print(f"❌ Cart options request failed: {cart_response.text}")
            return False

async def main():
    result = await test_frontend_scenario()
    
    print("\n" + "=" * 60)
    if result:
        print("🎉 FRONTEND SCENARIO TEST: PASSED")
        print("✅ Walmart integration is working correctly")
        print("✅ Frontend should be able to get products successfully")
    else:
        print("❌ FRONTEND SCENARIO TEST: FAILED")
        print("❌ This confirms the frontend issue exists")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())