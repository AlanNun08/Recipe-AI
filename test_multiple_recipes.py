#!/usr/bin/env python3
import asyncio
import httpx
import json

async def test_multiple_recipes():
    client = httpx.AsyncClient(timeout=30.0)
    try:
        # Login first
        login_data = {'email': 'demo@test.com', 'password': 'password123'}
        login_response = await client.post('https://d14c8dce-243d-4ebb-a34c-aee1807fadfa.preview.emergentagent.com/api/auth/login', json=login_data)
        user_id = login_response.json()['user']['id']
        
        # Get current plan
        plan_response = await client.get(f'https://d14c8dce-243d-4ebb-a34c-aee1807fadfa.preview.emergentagent.com/api/weekly-recipes/current/{user_id}')
        plan_data = plan_response.json()
        meals = plan_data['plan']['meals']
        
        print(f'Testing {len(meals)} recipes from weekly plan...')
        
        for i, meal in enumerate(meals[:3]):  # Test first 3 recipes
            recipe_id = meal['id']
            recipe_name = meal['name']
            
            print(f'Recipe {i+1}: {recipe_name}')
            
            # Get recipe detail
            recipe_response = await client.get(f'https://d14c8dce-243d-4ebb-a34c-aee1807fadfa.preview.emergentagent.com/api/weekly-recipes/recipe/{recipe_id}')
            
            if recipe_response.status_code == 200:
                recipe_data = recipe_response.json()
                cart_ingredients = recipe_data.get('cart_ingredients', [])
                
                print(f'  Status: Accessible')
                print(f'  Ingredients: {len(recipe_data.get("ingredients", []))}')
                print(f'  Cart ingredients: {len(cart_ingredients)}')
                
                # Check if all ingredients have products
                products_found = 0
                for cart_item in cart_ingredients:
                    products = cart_item.get('products', [])
                    if products and products[0].get('id'):
                        products_found += 1
                
                print(f'  Products found: {products_found}/{len(cart_ingredients)}')
                
                # Check for walmart_cart_url
                walmart_cart_url = recipe_data.get('walmart_cart_url')
                if walmart_cart_url:
                    print(f'  Walmart cart URL: Present')
                else:
                    print(f'  Walmart cart URL: Missing')
                    
                # Show first product as example
                if cart_ingredients and cart_ingredients[0].get('products'):
                    first_product = cart_ingredients[0]['products'][0]
                    print(f'  Example: {first_product.get("name")} - ${first_product.get("price")}')
            else:
                print(f'  Status: Not accessible ({recipe_response.status_code})')
        
    finally:
        await client.aclose()

asyncio.run(test_multiple_recipes())