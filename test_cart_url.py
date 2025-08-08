#!/usr/bin/env python3
import asyncio
import httpx
import json

async def test_cart_url():
    client = httpx.AsyncClient(timeout=30.0)
    
    # Get backend URL
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                backend_url = line.split('=', 1)[1].strip() + '/api'
                break
    
    # Test data with real product IDs from the previous test
    test_data = {
        'products': [
            {
                'ingredient_name': 'pasta',
                'product_id': '32247486',
                'name': 'Barilla Gluten Free Penne Pasta, 12 oz',
                'price': 2.56,
                'quantity': 1
            },
            {
                'ingredient_name': 'ground beef',
                'product_id': '15136790',
                'name': '73% Lean / 27% Fat Ground Beef, 1 lb Roll',
                'price': 6.24,
                'quantity': 1
            }
        ]
    }
    
    print(f'Backend URL: {backend_url}')
    print(f'Request data: {json.dumps(test_data, indent=2)}')
    
    print('Testing cart URL generation with real product IDs...')
    response = await client.post(f'{backend_url}/grocery/generate-cart-url', json=test_data)
    
    print(f'Status: {response.status_code}')
    if response.status_code == 200:
        data = response.json()
        print(f'Cart URL: {data.get("cart_url", "Not found")}')
        print(f'Total Price: ${data.get("total_price", 0)}')
        print(f'Total Items: {data.get("total_items", 0)}')
        print(f'Message: {data.get("message", "No message")}')
    else:
        print(f'Error: {response.text}')
    
    await client.aclose()

asyncio.run(test_cart_url())