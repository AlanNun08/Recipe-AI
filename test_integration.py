#!/usr/bin/env python3
"""
Integration Tests
Tests full user workflows and integration between different components
"""

import asyncio
import httpx
import json
from datetime import datetime

class TestIntegration:
    def __init__(self):
        self.backend_url = "http://localhost:8001/api"
        self.client = httpx.AsyncClient(timeout=30.0)
        self.demo_user_id = "f99be98f-c1d5-4ccc-a3ad-9b62e01f4731"
        
    async def cleanup(self):
        await self.client.aclose()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def test_complete_recipe_workflow(self):
        """Test complete recipe generation to viewing workflow"""
        self.log("=== Testing Complete Recipe Workflow ===")
        
        try:
            # Step 1: Generate a new recipe
            recipe_data = {
                "user_id": self.demo_user_id,
                "cuisine_type": "Mediterranean",
                "recipe_category": "cuisine",
                "meal_type": "lunch",
                "servings": 4,
                "difficulty": "medium",
                "dietary_preferences": ["Vegetarian"]
            }
            
            self.log("Step 1: Generating new recipe...")
            gen_response = await self.client.post(f"{self.backend_url}/recipes/generate", json=recipe_data)
            
            if gen_response.status_code != 200:
                self.log(f"❌ Recipe generation failed: {gen_response.status_code}", "ERROR")
                return False
            
            new_recipe = gen_response.json()
            recipe_id = new_recipe.get("id")
            recipe_title = new_recipe.get("title")
            
            self.log(f"✅ Generated recipe: {recipe_title} (ID: {recipe_id})")
            
            # Step 2: Verify recipe appears in history
            self.log("Step 2: Checking recipe appears in history...")
            await asyncio.sleep(1)  # Allow database to update
            
            history_response = await self.client.get(f"{self.backend_url}/recipes/history/{self.demo_user_id}")
            
            if history_response.status_code != 200:
                self.log(f"❌ History retrieval failed: {history_response.status_code}", "ERROR")
                return False
            
            history_result = history_response.json()
            history_recipes = history_result.get("recipes", [])
            
            # Find our recipe in history
            found_in_history = False
            for recipe in history_recipes:
                if recipe.get("id") == recipe_id:
                    found_in_history = True
                    if recipe.get("title") == recipe_title:
                        self.log(f"✅ Recipe found in history with correct title")
                    else:
                        self.log(f"❌ Recipe found but title mismatch", "ERROR")
                        return False
                    break
            
            if not found_in_history:
                self.log(f"❌ Recipe not found in history", "ERROR")
                return False
            
            # Step 3: View recipe detail
            self.log("Step 3: Viewing recipe detail...")
            detail_response = await self.client.get(f"{self.backend_url}/recipes/{recipe_id}/detail")
            
            if detail_response.status_code != 200:
                self.log(f"❌ Recipe detail retrieval failed: {detail_response.status_code}", "ERROR")
                return False
            
            detail_recipe = detail_response.json()
            detail_title = detail_recipe.get("title")
            detail_id = detail_recipe.get("id")
            
            if detail_title != recipe_title or detail_id != recipe_id:
                self.log(f"❌ Recipe detail mismatch", "ERROR")
                return False
            
            self.log(f"✅ Recipe detail matches: {detail_title}")
            
            # Step 4: Test Walmart integration
            self.log("Step 4: Testing Walmart cart integration...")
            walmart_response = await self.client.get(f"{self.backend_url}/recipes/{recipe_id}/walmart-cart-options")
            
            if walmart_response.status_code == 200:
                walmart_result = walmart_response.json()
                ingredient_options = walmart_result.get("ingredient_options", [])
                self.log(f"✅ Walmart integration works: {len(ingredient_options)} ingredient options")
            else:
                self.log(f"⚠️  Walmart integration failed: {walmart_response.status_code}", "WARNING")
            
            self.log("✅ Complete recipe workflow test passed")
            return True
            
        except Exception as e:
            self.log(f"❌ Recipe workflow error: {str(e)}", "ERROR")
            return False
    
    async def test_user_authentication_integration(self):
        """Test user authentication integration with recipe system"""
        self.log("=== Testing User Authentication Integration ===")
        
        try:
            # Test login
            login_data = {
                "email": "demo@test.com",
                "password": "password123"
            }
            
            self.log("Testing user login...")
            login_response = await self.client.post(f"{self.backend_url}/users/login", json=login_data)
            
            if login_response.status_code != 200:
                self.log(f"❌ Login failed: {login_response.status_code}", "ERROR")
                return False
            
            login_result = login_response.json()
            authenticated_user_id = login_result.get("user_id")
            
            if authenticated_user_id != self.demo_user_id:
                self.log(f"❌ Login returned wrong user ID", "ERROR")
                return False
            
            self.log(f"✅ User authenticated successfully")
            
            # Test access to user-specific data
            self.log("Testing access to user recipe history...")
            history_response = await self.client.get(f"{self.backend_url}/recipes/history/{authenticated_user_id}")
            
            if history_response.status_code != 200:
                self.log(f"❌ History access failed: {history_response.status_code}", "ERROR")
                return False
            
            history_result = history_response.json()
            user_recipes = history_result.get("recipes", [])
            
            self.log(f"✅ User has access to {len(user_recipes)} recipes")
            
            # Test subscription status
            self.log("Testing subscription status access...")
            sub_response = await self.client.get(f"{self.backend_url}/users/{authenticated_user_id}/subscription-status")
            
            if sub_response.status_code == 200:
                sub_result = sub_response.json()
                sub_status = sub_result.get("subscription_status", "unknown")
                self.log(f"✅ Subscription status accessible: {sub_status}")
            else:
                self.log(f"⚠️  Subscription status failed: {sub_response.status_code}", "WARNING")
            
            self.log("✅ User authentication integration test passed")
            return True
            
        except Exception as e:
            self.log(f"❌ Authentication integration error: {str(e)}", "ERROR")
            return False
    
    async def test_starbucks_recipe_integration(self):
        """Test Starbucks recipe system integration"""
        self.log("=== Testing Starbucks Recipe Integration ===")
        
        try:
            # Generate a Starbucks recipe
            starbucks_data = {
                "user_id": self.demo_user_id,
                "drink_type": "frappuccino",
                "flavor_profile": "sweet",
                "size": "medium"
            }
            
            self.log("Generating Starbucks recipe...")
            starbucks_response = await self.client.post(f"{self.backend_url}/starbucks/generate", json=starbucks_data)
            
            if starbucks_response.status_code != 200:
                self.log(f"❌ Starbucks generation failed: {starbucks_response.status_code}", "ERROR")
                return False
            
            starbucks_recipe = starbucks_response.json()
            drink_name = starbucks_recipe.get("name", "Unknown")
            drink_id = starbucks_recipe.get("id")
            
            self.log(f"✅ Generated Starbucks recipe: {drink_name}")
            
            # Test if Starbucks recipe can be retrieved
            if drink_id:
                detail_response = await self.client.get(f"{self.backend_url}/recipes/{drink_id}/detail")
                
                if detail_response.status_code == 200:
                    detail = detail_response.json()
                    self.log(f"✅ Starbucks recipe detail accessible: {detail.get('title', 'Unknown')}")
                else:
                    self.log(f"⚠️  Starbucks recipe detail failed: {detail_response.status_code}", "WARNING")
            
            self.log("✅ Starbucks recipe integration test passed")
            return True
            
        except Exception as e:
            self.log(f"❌ Starbucks integration error: {str(e)}", "ERROR")
            return False
    
    async def test_cross_cuisine_consistency(self):
        """Test consistency across different cuisine types"""
        self.log("=== Testing Cross-Cuisine Consistency ===")
        
        cuisines_to_test = ["Italian", "Mexican", "Asian", "Indian", "French"]
        generated_recipes = []
        
        try:
            for cuisine in cuisines_to_test:
                recipe_data = {
                    "user_id": self.demo_user_id,
                    "cuisine_type": cuisine,
                    "recipe_category": "cuisine",
                    "meal_type": "dinner",
                    "servings": 4,
                    "difficulty": "medium",
                    "dietary_preferences": []
                }
                
                self.log(f"Testing {cuisine} cuisine...")
                response = await self.client.post(f"{self.backend_url}/recipes/generate", json=recipe_data)
                
                if response.status_code == 200:
                    recipe = response.json()
                    generated_recipes.append({
                        "cuisine": cuisine,
                        "title": recipe.get("title", "Unknown"),
                        "id": recipe.get("id"),
                        "ingredients_count": len(recipe.get("ingredients", [])),
                        "instructions_count": len(recipe.get("instructions", []))
                    })
                    self.log(f"✅ {cuisine}: {recipe.get('title')}")
                else:
                    self.log(f"❌ {cuisine} generation failed: {response.status_code}", "ERROR")
                    return False
                
                # Small delay between requests
                await asyncio.sleep(0.3)
            
            # Verify consistency across cuisines
            issues = 0
            for recipe in generated_recipes:
                # Check minimum ingredient count
                if recipe["ingredients_count"] < 5:
                    self.log(f"⚠️  {recipe['cuisine']} has few ingredients: {recipe['ingredients_count']}", "WARNING")
                    issues += 1
                
                # Check minimum instruction count
                if recipe["instructions_count"] < 5:
                    self.log(f"⚠️  {recipe['cuisine']} has few instructions: {recipe['instructions_count']}", "WARNING")
                    issues += 1
                
                # Check for generic titles
                if "Classic" in recipe["title"] and "Pasta" in recipe["title"]:
                    self.log(f"⚠️  {recipe['cuisine']} has generic title: {recipe['title']}", "WARNING")
                    issues += 1
            
            if issues == 0:
                self.log("✅ All cuisines show consistent quality")
            else:
                self.log(f"⚠️  Found {issues} quality issues across cuisines", "WARNING")
            
            self.log("✅ Cross-cuisine consistency test completed")
            return issues < len(cuisines_to_test)  # Allow some issues but not too many
            
        except Exception as e:
            self.log(f"❌ Cross-cuisine consistency error: {str(e)}", "ERROR")
            return False
    
    async def test_database_consistency(self):
        """Test database consistency across different operations"""
        self.log("=== Testing Database Consistency ===")
        
        try:
            # Get initial recipe count
            initial_response = await self.client.get(f"{self.backend_url}/recipes/history/{self.demo_user_id}")
            
            if initial_response.status_code != 200:
                self.log(f"❌ Could not get initial recipe count", "ERROR")
                return False
            
            initial_result = initial_response.json()
            initial_count = len(initial_result.get("recipes", []))
            
            self.log(f"Initial recipe count: {initial_count}")
            
            # Generate a new recipe
            recipe_data = {
                "user_id": self.demo_user_id,
                "cuisine_type": "Greek",
                "recipe_category": "cuisine",
                "meal_type": "dinner",
                "servings": 4,
                "difficulty": "medium",
                "dietary_preferences": []
            }
            
            gen_response = await self.client.post(f"{self.backend_url}/recipes/generate", json=recipe_data)
            
            if gen_response.status_code != 200:
                self.log(f"❌ Recipe generation failed for consistency test", "ERROR")
                return False
            
            new_recipe = gen_response.json()
            new_recipe_id = new_recipe.get("id")
            
            # Wait for database to update
            await asyncio.sleep(1)
            
            # Check updated recipe count
            updated_response = await self.client.get(f"{self.backend_url}/recipes/history/{self.demo_user_id}")
            
            if updated_response.status_code != 200:
                self.log(f"❌ Could not get updated recipe count", "ERROR")
                return False
            
            updated_result = updated_response.json()
            updated_count = len(updated_result.get("recipes", []))
            
            if updated_count == initial_count + 1:
                self.log(f"✅ Recipe count updated correctly: {initial_count} → {updated_count}")
            else:
                self.log(f"❌ Recipe count inconsistent: {initial_count} → {updated_count}", "ERROR")
                return False
            
            # Verify the new recipe is accessible
            detail_response = await self.client.get(f"{self.backend_url}/recipes/{new_recipe_id}/detail")
            
            if detail_response.status_code == 200:
                self.log(f"✅ New recipe is immediately accessible via detail endpoint")
            else:
                self.log(f"❌ New recipe not accessible: {detail_response.status_code}", "ERROR")
                return False
            
            self.log("✅ Database consistency test passed")
            return True
            
        except Exception as e:
            self.log(f"❌ Database consistency error: {str(e)}", "ERROR")
            return False
    
    async def run_all_tests(self):
        """Run all integration tests"""
        self.log("🚀 Starting Integration Tests")
        self.log("=" * 50)
        
        tests = [
            ("Complete Recipe Workflow", self.test_complete_recipe_workflow),
            ("User Authentication Integration", self.test_user_authentication_integration),
            ("Starbucks Integration", self.test_starbucks_recipe_integration),
            ("Cross-Cuisine Consistency", self.test_cross_cuisine_consistency),
            ("Database Consistency", self.test_database_consistency)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            self.log(f"\n🧪 Running {test_name} test...")
            try:
                result = await test_func()
                if result:
                    passed += 1
                    self.log(f"✅ {test_name} test PASSED")
                else:
                    self.log(f"❌ {test_name} test FAILED")
            except Exception as e:
                self.log(f"❌ {test_name} test ERROR: {str(e)}", "ERROR")
            
            # Delay between integration tests to avoid overwhelming the system
            await asyncio.sleep(1)
        
        self.log("=" * 50)
        self.log(f"🎯 Integration Tests Complete: {passed}/{total} passed")
        
        if passed == total:
            self.log("🎉 All integration tests PASSED!")
            return True
        else:
            self.log(f"❌ {total - passed} test(s) FAILED")
            return False

async def main():
    tester = TestIntegration()
    try:
        success = await tester.run_all_tests()
        return success
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("\n🎉 Integration tests completed successfully!")
    else:
        print("\n❌ Integration tests failed!")
        exit(1)