#!/usr/bin/env python3
"""
Data Integrity Tests
Tests database consistency, data validation, and business logic integrity
"""

import asyncio
import httpx
import json
import uuid
from datetime import datetime

class TestDataIntegrity:
    def __init__(self):
        self.backend_url = "http://localhost:8001/api"
        self.client = httpx.AsyncClient(timeout=30.0)
        self.demo_user_id = "f99be98f-c1d5-4ccc-a3ad-9b62e01f4731"
        
    async def cleanup(self):
        await self.client.aclose()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def is_valid_uuid(self, uuid_string):
        """Check if string is a valid UUID"""
        try:
            uuid.UUID(uuid_string)
            return True
        except (ValueError, TypeError):
            return False
    
    async def test_recipe_id_consistency(self):
        """Test that recipe IDs are consistent across endpoints"""
        self.log("=== Testing Recipe ID Consistency ===")
        
        try:
            # Get recipe history
            response = await self.client.get(f"{self.backend_url}/recipes/history/{self.demo_user_id}")
            
            if response.status_code != 200:
                self.log(f"❌ Failed to get recipe history: {response.status_code}", "ERROR")
                return False
            
            result = response.json()
            recipes = result.get("recipes", [])[:5]  # Test first 5 recipes
            
            if not recipes:
                self.log("❌ No recipes found for ID consistency test", "ERROR")
                return False
            
            for i, recipe in enumerate(recipes):
                recipe_id = recipe.get("id")
                
                # Verify ID format
                if not self.is_valid_uuid(recipe_id):
                    self.log(f"❌ Recipe {i+1} has invalid UUID format: {recipe_id}", "ERROR")
                    return False
                
                # Test consistency across endpoints
                detail_response = await self.client.get(f"{self.backend_url}/recipes/{recipe_id}/detail")
                
                if detail_response.status_code == 200:
                    detail = detail_response.json()
                    detail_id = detail.get("id")
                    
                    if recipe_id != detail_id:
                        self.log(f"❌ ID mismatch: history={recipe_id}, detail={detail_id}", "ERROR")
                        return False
                    
                    self.log(f"✅ Recipe {i+1}: ID consistency verified")
                else:
                    self.log(f"❌ Detail endpoint failed for {recipe_id}: {detail_response.status_code}", "ERROR")
                    return False
            
            self.log("✅ Recipe ID consistency test passed")
            return True
            
        except Exception as e:
            self.log(f"❌ Recipe ID consistency error: {str(e)}", "ERROR")
            return False
    
    async def test_required_fields_validation(self):
        """Test that all recipes have required fields"""
        self.log("=== Testing Required Fields Validation ===")
        
        required_recipe_fields = [
            "id", "title", "description", "ingredients", "instructions", 
            "cuisine_type", "prep_time", "cook_time", "servings"
        ]
        
        try:
            response = await self.client.get(f"{self.backend_url}/recipes/history/{self.demo_user_id}")
            
            if response.status_code != 200:
                self.log(f"❌ Failed to get recipes: {response.status_code}", "ERROR")
                return False
            
            result = response.json()
            recipes = result.get("recipes", [])[:10]  # Test first 10 recipes
            
            missing_fields_count = 0
            
            for i, recipe in enumerate(recipes):
                recipe_id = recipe.get("id")
                
                # Get detailed recipe data
                detail_response = await self.client.get(f"{self.backend_url}/recipes/{recipe_id}/detail")
                
                if detail_response.status_code != 200:
                    continue
                
                detail = detail_response.json()
                missing_fields = []
                
                for field in required_recipe_fields:
                    if field not in detail or detail[field] is None:
                        missing_fields.append(field)
                
                if missing_fields:
                    missing_fields_count += 1
                    self.log(f"⚠️  Recipe {i+1} missing fields: {', '.join(missing_fields)}", "WARNING")
                else:
                    self.log(f"✅ Recipe {i+1}: All required fields present")
            
            if missing_fields_count == 0:
                self.log("✅ Required fields validation test passed")
                return True
            else:
                self.log(f"❌ {missing_fields_count} recipes missing required fields", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Required fields validation error: {str(e)}", "ERROR")
            return False
    
    async def test_ingredient_data_quality(self):
        """Test ingredient data quality and format"""
        self.log("=== Testing Ingredient Data Quality ===")
        
        try:
            response = await self.client.get(f"{self.backend_url}/recipes/history/{self.demo_user_id}")
            
            if response.status_code != 200:
                self.log(f"❌ Failed to get recipes: {response.status_code}", "ERROR")
                return False
            
            result = response.json()
            recipes = result.get("recipes", [])[:10]
            
            quality_issues = 0
            
            for i, recipe in enumerate(recipes):
                recipe_id = recipe.get("id")
                
                detail_response = await self.client.get(f"{self.backend_url}/recipes/{recipe_id}/detail")
                
                if detail_response.status_code != 200:
                    continue
                
                detail = detail_response.json()
                ingredients = detail.get("ingredients", [])
                
                # Check ingredient count
                if len(ingredients) < 3:
                    quality_issues += 1
                    self.log(f"⚠️  Recipe {i+1} has too few ingredients: {len(ingredients)}", "WARNING")
                    continue
                
                # Check ingredient format
                invalid_ingredients = 0
                for ingredient in ingredients:
                    if not isinstance(ingredient, str) or len(ingredient.strip()) < 3:
                        invalid_ingredients += 1
                
                if invalid_ingredients > 0:
                    quality_issues += 1
                    self.log(f"⚠️  Recipe {i+1} has {invalid_ingredients} invalid ingredients", "WARNING")
                else:
                    self.log(f"✅ Recipe {i+1}: Ingredient quality OK ({len(ingredients)} ingredients)")
            
            if quality_issues == 0:
                self.log("✅ Ingredient data quality test passed")
                return True
            else:
                self.log(f"❌ {quality_issues} recipes have ingredient quality issues", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Ingredient data quality error: {str(e)}", "ERROR")
            return False
    
    async def test_business_logic_validation(self):
        """Test business logic constraints"""
        self.log("=== Testing Business Logic Validation ===")
        
        try:
            response = await self.client.get(f"{self.backend_url}/recipes/history/{self.demo_user_id}")
            
            if response.status_code != 200:
                self.log(f"❌ Failed to get recipes: {response.status_code}", "ERROR")
                return False
            
            result = response.json()
            recipes = result.get("recipes", [])[:10]
            
            logic_violations = 0
            
            for i, recipe in enumerate(recipes):
                recipe_id = recipe.get("id")
                
                detail_response = await self.client.get(f"{self.backend_url}/recipes/{recipe_id}/detail")
                
                if detail_response.status_code != 200:
                    continue
                
                detail = detail_response.json()
                
                # Check servings range
                servings = detail.get("servings", 0)
                if servings < 1 or servings > 20:
                    logic_violations += 1
                    self.log(f"⚠️  Recipe {i+1} has invalid servings: {servings}", "WARNING")
                    continue
                
                # Check time constraints
                prep_time = detail.get("prep_time", 0)
                cook_time = detail.get("cook_time", 0)
                
                if prep_time < 0 or prep_time > 300:  # 0-300 minutes
                    logic_violations += 1
                    self.log(f"⚠️  Recipe {i+1} has invalid prep time: {prep_time}", "WARNING")
                    continue
                
                if cook_time < 0 or cook_time > 480:  # 0-8 hours
                    logic_violations += 1
                    self.log(f"⚠️  Recipe {i+1} has invalid cook time: {cook_time}", "WARNING")
                    continue
                
                # Check difficulty level
                difficulty = detail.get("difficulty", "")
                valid_difficulties = ["easy", "medium", "hard"]
                
                if difficulty not in valid_difficulties:
                    logic_violations += 1
                    self.log(f"⚠️  Recipe {i+1} has invalid difficulty: {difficulty}", "WARNING")
                    continue
                
                self.log(f"✅ Recipe {i+1}: Business logic validation OK")
            
            if logic_violations == 0:
                self.log("✅ Business logic validation test passed")
                return True
            else:
                self.log(f"❌ {logic_violations} recipes have business logic violations", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Business logic validation error: {str(e)}", "ERROR")
            return False
    
    async def test_user_data_isolation(self):
        """Test that user data is properly isolated"""
        self.log("=== Testing User Data Isolation ===")
        
        try:
            # Test with valid user
            valid_response = await self.client.get(f"{self.backend_url}/recipes/history/{self.demo_user_id}")
            
            if valid_response.status_code != 200:
                self.log(f"❌ Failed to get valid user recipes: {valid_response.status_code}", "ERROR")
                return False
            
            valid_result = valid_response.json()
            valid_recipes = valid_result.get("recipes", [])
            
            # Test with invalid user ID
            fake_user_id = "00000000-0000-0000-0000-000000000000"
            invalid_response = await self.client.get(f"{self.backend_url}/recipes/history/{fake_user_id}")
            
            if invalid_response.status_code == 200:
                invalid_result = invalid_response.json()
                invalid_recipes = invalid_result.get("recipes", [])
                
                if len(invalid_recipes) == 0:
                    self.log(f"✅ Invalid user correctly returns empty recipes")
                else:
                    self.log(f"❌ Invalid user incorrectly returns {len(invalid_recipes)} recipes", "ERROR")
                    return False
            elif invalid_response.status_code == 404:
                self.log(f"✅ Invalid user correctly returns 404")
            else:
                self.log(f"⚠️  Invalid user returns unexpected status: {invalid_response.status_code}", "WARNING")
            
            self.log("✅ User data isolation test passed")
            return True
            
        except Exception as e:
            self.log(f"❌ User data isolation error: {str(e)}", "ERROR")
            return False
    
    async def run_all_tests(self):
        """Run all data integrity tests"""
        self.log("🚀 Starting Data Integrity Tests")
        self.log("=" * 50)
        
        tests = [
            ("Recipe ID Consistency", self.test_recipe_id_consistency),
            ("Required Fields", self.test_required_fields_validation),
            ("Ingredient Quality", self.test_ingredient_data_quality),
            ("Business Logic", self.test_business_logic_validation),
            ("User Data Isolation", self.test_user_data_isolation)
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
        
        self.log("=" * 50)
        self.log(f"🎯 Data Integrity Tests Complete: {passed}/{total} passed")
        
        if passed == total:
            self.log("🎉 All data integrity tests PASSED!")
            return True
        else:
            self.log(f"❌ {total - passed} test(s) FAILED")
            return False

async def main():
    tester = TestDataIntegrity()
    try:
        success = await tester.run_all_tests()
        return success
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("\n🎉 Data integrity tests completed successfully!")
    else:
        print("\n❌ Data integrity tests failed!")
        exit(1)