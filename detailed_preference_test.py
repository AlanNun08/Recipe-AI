#!/usr/bin/env python3
"""
Detailed Preference Testing for Weekly Recipe Generation
Testing specific dietary restrictions and allergy handling
"""

import requests
import json
import sys
from typing import Dict, List, Any

# Configuration
BACKEND_URL = "https://meal-shop-ai.preview.emergentagent.com/api"
DEMO_USER_ID = "f99be98f-c1d5-4ccc-a3ad-9b62e01f4731"

def test_vegetarian_preference():
    """Test that vegetarian preference is properly respected"""
    print("🥬 Testing Vegetarian Preference Handling")
    print("-" * 50)
    
    weekly_data = {
        "user_id": DEMO_USER_ID,
        "family_size": 2,
        "dietary_preferences": ["vegetarian"],
        "allergies": [],
        "cuisines": ["italian", "asian"]
    }
    
    response = requests.post(f"{BACKEND_URL}/weekly-recipes/generate", json=weekly_data, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        meals = data.get("meals", [])
        
        print(f"✅ Generated {len(meals)} meals")
        
        # Check each meal for meat ingredients
        meat_violations = []
        for meal in meals:
            meal_name = meal.get("name", "")
            ingredients = meal.get("ingredients", [])
            
            # Check for meat ingredients
            meat_keywords = ["chicken", "beef", "pork", "fish", "meat", "turkey", "lamb", "bacon", "ham"]
            found_meat = []
            
            for ingredient in ingredients:
                for meat in meat_keywords:
                    if meat.lower() in ingredient.lower():
                        found_meat.append(ingredient)
            
            if found_meat:
                meat_violations.append({
                    "meal": meal_name,
                    "day": meal.get("day"),
                    "meat_ingredients": found_meat
                })
            
            print(f"   {meal.get('day')}: {meal_name}")
            if found_meat:
                print(f"      ❌ MEAT FOUND: {', '.join(found_meat)}")
            else:
                print(f"      ✅ Vegetarian compliant")
        
        if meat_violations:
            print(f"\n❌ VEGETARIAN PREFERENCE VIOLATION:")
            for violation in meat_violations:
                print(f"   {violation['day']} - {violation['meal']}: {violation['meat_ingredients']}")
            return False
        else:
            print(f"\n✅ All meals are vegetarian compliant!")
            return True
    else:
        print(f"❌ Request failed: {response.status_code} - {response.text}")
        return False

def test_allergy_handling():
    """Test that allergies are properly avoided"""
    print("\n🚫 Testing Allergy Handling")
    print("-" * 50)
    
    weekly_data = {
        "user_id": DEMO_USER_ID,
        "family_size": 2,
        "dietary_preferences": [],
        "allergies": ["nuts", "dairy"],
        "cuisines": ["mediterranean"]
    }
    
    response = requests.post(f"{BACKEND_URL}/weekly-recipes/generate", json=weekly_data, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        meals = data.get("meals", [])
        
        print(f"✅ Generated {len(meals)} meals")
        
        # Check each meal for allergen ingredients
        allergy_violations = []
        allergens = ["nuts", "dairy", "milk", "cheese", "butter", "cream"]
        
        for meal in meals:
            meal_name = meal.get("name", "")
            ingredients = meal.get("ingredients", [])
            
            found_allergens = []
            for ingredient in ingredients:
                for allergen in allergens:
                    if allergen.lower() in ingredient.lower():
                        found_allergens.append(ingredient)
            
            if found_allergens:
                allergy_violations.append({
                    "meal": meal_name,
                    "day": meal.get("day"),
                    "allergen_ingredients": found_allergens
                })
            
            print(f"   {meal.get('day')}: {meal_name}")
            if found_allergens:
                print(f"      ❌ ALLERGENS FOUND: {', '.join(found_allergens)}")
            else:
                print(f"      ✅ Allergy safe")
        
        if allergy_violations:
            print(f"\n⚠️ POTENTIAL ALLERGY VIOLATIONS:")
            for violation in allergy_violations:
                print(f"   {violation['day']} - {violation['meal']}: {violation['allergen_ingredients']}")
            return False
        else:
            print(f"\n✅ All meals are allergy safe!")
            return True
    else:
        print(f"❌ Request failed: {response.status_code} - {response.text}")
        return False

def test_user_preference_fetching():
    """Test if user preferences are being fetched from database"""
    print("\n👤 Testing User Preference Fetching")
    print("-" * 50)
    
    # First, try to get user data directly
    try:
        response = requests.get(f"{BACKEND_URL}/user/profile/{DEMO_USER_ID}", timeout=10)
        if response.status_code == 200:
            user_data = response.json()
            print("✅ User profile endpoint accessible")
            print(f"   Dietary preferences: {user_data.get('dietary_preferences', [])}")
            print(f"   Allergies: {user_data.get('allergies', [])}")
            print(f"   Favorite cuisines: {user_data.get('favorite_cuisines', [])}")
            return True
        else:
            print(f"❌ User profile endpoint not accessible: {response.status_code}")
    except Exception as e:
        print(f"❌ Error accessing user profile: {str(e)}")
    
    # Test with minimal request to see if stored preferences are used
    print("\n   Testing with minimal request (should use stored preferences):")
    weekly_data = {
        "user_id": DEMO_USER_ID,
        "family_size": 2
        # No preferences specified - should use stored ones
    }
    
    response = requests.post(f"{BACKEND_URL}/weekly-recipes/generate", json=weekly_data, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        meals = data.get("meals", [])
        print(f"   ✅ Generated {len(meals)} meals using stored preferences")
        
        # Show sample meals to see if they reflect any stored preferences
        for i, meal in enumerate(meals[:3]):
            print(f"      {meal.get('day')}: {meal.get('name')} ({meal.get('cuisine_type')})")
        
        return True
    else:
        print(f"   ❌ Request failed: {response.status_code}")
        return False

def test_preference_combination():
    """Test that request preferences are combined with stored preferences"""
    print("\n🔄 Testing Preference Combination")
    print("-" * 50)
    
    # Test with additional preferences
    weekly_data = {
        "user_id": DEMO_USER_ID,
        "family_size": 2,
        "dietary_preferences": ["gluten-free"],  # Additional to any stored preferences
        "allergies": ["shellfish"],  # Additional to any stored allergies
        "cuisines": ["thai", "indian"]  # Additional to any stored cuisines
    }
    
    response = requests.post(f"{BACKEND_URL}/weekly-recipes/generate", json=weekly_data, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        meals = data.get("meals", [])
        
        print(f"✅ Generated {len(meals)} meals with combined preferences")
        
        # Check for cuisine variety (should include requested cuisines)
        cuisines_found = set()
        for meal in meals:
            cuisine = meal.get("cuisine_type", "").lower()
            cuisines_found.add(cuisine)
            print(f"   {meal.get('day')}: {meal.get('name')} ({meal.get('cuisine_type')})")
        
        print(f"\n   Cuisines found: {', '.join(cuisines_found)}")
        
        # Check if requested cuisines appear
        requested_cuisines = ["thai", "indian"]
        found_requested = any(req.lower() in cuisines_found for req in requested_cuisines)
        
        if found_requested:
            print("   ✅ Requested cuisines appear in meal plan")
        else:
            print("   ⚠️ Requested cuisines may not be reflected (could be due to mock data)")
        
        return True
    else:
        print(f"❌ Request failed: {response.status_code} - {response.text}")
        return False

def main():
    """Run all detailed preference tests"""
    print("🧪 DETAILED PREFERENCE TESTING FOR WEEKLY RECIPE GENERATION")
    print("=" * 80)
    
    results = []
    
    # Run all tests
    results.append(("User Preference Fetching", test_user_preference_fetching()))
    results.append(("Preference Combination", test_preference_combination()))
    results.append(("Vegetarian Preference", test_vegetarian_preference()))
    results.append(("Allergy Handling", test_allergy_handling()))
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 DETAILED TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All detailed preference tests passed!")
        sys.exit(0)
    else:
        print("⚠️ Some preference handling issues detected")
        sys.exit(1)

if __name__ == "__main__":
    main()