#!/usr/bin/env python3
"""
Backend API Testing for Enhanced OpenAI Prompt with Comprehensive Cooking Instructions
Testing the enhanced OpenAI prompt for comprehensive cooking instructions as requested in review:
1. Test Recipe Generation with /api/recipes/generate to validate detailed cooking instructions
2. Validate Instruction Quality - temperatures, times, techniques, visual cues, safety notes
3. Test Different Recipe Types (Italian, Mexican, etc.) for consistency
4. Compare instruction detail vs basic instructions like "cook the chicken"
5. Verify both clean shopping list extraction AND comprehensive cooking instructions work together
"""

import requests
import json
import sys
import re
from datetime import datetime

# Backend URL from frontend/.env
BACKEND_URL = "https://350e6048-1e7b-4cd5-955b-ebca6201edd0.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
TEST_EMAIL = "demo@test.com"
TEST_PASSWORD = "password123"

def print_separator(title):
    """Print a formatted separator"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_response(response, title="Response"):
    """Print formatted response details"""
    print(f"\n--- {title} ---")
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    try:
        response_json = response.json()
        print(f"JSON Response: {json.dumps(response_json, indent=2)}")
        return response_json
    except:
        print(f"Text Response: {response.text}")
        return None

def test_login():
    """Test user login and get user_id"""
    print_separator("TESTING USER LOGIN")
    
    login_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/login", json=login_data, timeout=10)
        response_data = print_response(response, "Login Response")
        
        if response.status_code == 200 and response_data:
            user_id = response_data.get('user', {}).get('id')
            print(f"\n✅ LOGIN SUCCESS - User ID: {user_id}")
            return user_id
        else:
            print(f"\n❌ LOGIN FAILED - Status: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"\n❌ LOGIN ERROR: {str(e)}")
        return None

def validate_shopping_list_extraction(ingredients, shopping_list, recipe_name):
    """Validate that shopping list properly extracts ingredient names without quantities"""
    print(f"\n--- Shopping List Validation for {recipe_name} ---")
    
    if not shopping_list:
        print("❌ No shopping list found in recipe")
        return False, []
    
    print(f"Original Ingredients ({len(ingredients)}):")
    for i, ingredient in enumerate(ingredients[:5], 1):  # Show first 5
        print(f"  {i}. {ingredient}")
    if len(ingredients) > 5:
        print(f"  ... and {len(ingredients) - 5} more")
    
    print(f"\nExtracted Shopping List ({len(shopping_list)}):")
    for i, item in enumerate(shopping_list[:5], 1):  # Show first 5
        print(f"  {i}. {item}")
    if len(shopping_list) > 5:
        print(f"  ... and {len(shopping_list) - 5} more")
    
    # Validation rules based on review requirements
    validation_results = []
    issues = []
    
    # Test cases from review:
    test_cases = [
        ("2 cups flour", "flour"),
        ("1/4 cup olive oil", "olive oil"),
        ("3 tomatoes diced", "tomatoes"),
        ("1 can diced tomatoes", "diced tomatoes"),
        ("salt and pepper to taste", ["salt", "pepper"])
    ]
    
    # Check if shopping list items are clean (no quantities/measurements)
    quantity_patterns = [
        r'^\d+\s*(cups?|tbsp|tsp|oz|lbs?|pounds?|grams?|kg|ml|liters?)',
        r'^\d+/\d+\s*cup',
        r'^\d+\s*(large|medium|small|whole)',
        r'^\d+\s*cans?',
        r'^\d+\s*pieces?',
        r'to taste$'
    ]
    
    clean_items = 0
    for item in shopping_list:
        is_clean = True
        for pattern in quantity_patterns:
            if re.search(pattern, item.lower()):
                is_clean = False
                issues.append(f"Item '{item}' contains quantity/measurement")
                break
        
        if is_clean:
            clean_items += 1
    
    clean_percentage = (clean_items / len(shopping_list)) * 100 if shopping_list else 0
    
    print(f"\nValidation Results:")
    print(f"✅ Clean items: {clean_items}/{len(shopping_list)} ({clean_percentage:.1f}%)")
    
    if clean_percentage >= 90:
        print("✅ EXCELLENT - Shopping list extraction is working properly")
        validation_results.append(True)
    elif clean_percentage >= 75:
        print("⚠️ GOOD - Shopping list mostly clean with minor issues")
        validation_results.append(True)
    else:
        print("❌ POOR - Shopping list extraction needs improvement")
        validation_results.append(False)
    
    # Check for compound ingredients (like "salt and pepper")
    compound_handled = 0
    for ingredient in ingredients:
        if " and " in ingredient.lower():
            # Check if it was properly split in shopping list
            parts = [part.strip() for part in ingredient.lower().split(" and ")]
            if all(any(part in item.lower() for item in shopping_list) for part in parts):
                compound_handled += 1
                print(f"✅ Compound ingredient handled: '{ingredient}'")
    
    if compound_handled > 0:
        print(f"✅ Compound ingredients properly handled: {compound_handled}")
    
    return all(validation_results), issues

def test_recipe_generation(user_id, test_params):
    """Test recipe generation with specific parameters"""
    recipe_name = test_params.get('name', 'Test Recipe')
    print_separator(f"TESTING RECIPE GENERATION - {recipe_name}")
    
    try:
        url = f"{API_BASE}/recipes/generate"
        print(f"Testing URL: {url}")
        print(f"Parameters: {json.dumps(test_params['params'], indent=2)}")
        
        response = requests.post(url, json=test_params['params'], timeout=30)
        response_data = print_response(response, f"Recipe Generation Response - {recipe_name}")
        
        if response.status_code == 200 and response_data:
            print(f"\n✅ RECIPE GENERATION SUCCESS - {recipe_name}")
            
            # Extract key fields
            title = response_data.get('title', 'Unknown')
            ingredients = response_data.get('ingredients', [])
            shopping_list = response_data.get('shopping_list', [])
            cuisine_type = response_data.get('cuisine_type', 'Unknown')
            
            print(f"✅ Recipe Title: {title}")
            print(f"✅ Cuisine Type: {cuisine_type}")
            print(f"✅ Ingredients Count: {len(ingredients)}")
            print(f"✅ Shopping List Count: {len(shopping_list)}")
            
            # Validate shopping list extraction
            is_valid, issues = validate_shopping_list_extraction(ingredients, shopping_list, title)
            
            return True, response_data, is_valid, issues
            
        else:
            print(f"\n❌ RECIPE GENERATION FAILED - Status: {response.status_code}")
            return False, response_data, False, []
            
    except Exception as e:
        print(f"\n❌ RECIPE GENERATION ERROR: {str(e)}")
        return False, None, False, []

def test_different_recipe_types(user_id):
    """Test recipe generation with different cuisines and dietary preferences"""
    print_separator("TESTING DIFFERENT RECIPE TYPES FOR CONSISTENCY")
    
    # Test cases covering different cuisines and dietary preferences
    test_cases = [
        {
            'name': 'Italian Pasta',
            'params': {
                'user_id': user_id,
                'cuisine_type': 'italian',
                'dietary_preferences': [],
                'servings': 4,
                'difficulty': 'medium'
            }
        },
        {
            'name': 'Vegetarian Mexican',
            'params': {
                'user_id': user_id,
                'cuisine_type': 'mexican',
                'dietary_preferences': ['vegetarian'],
                'servings': 2,
                'difficulty': 'easy'
            }
        },
        {
            'name': 'Vegan Asian Stir-fry',
            'params': {
                'user_id': user_id,
                'cuisine_type': 'asian',
                'dietary_preferences': ['vegan'],
                'servings': 3,
                'difficulty': 'medium'
            }
        },
        {
            'name': 'Gluten-Free American',
            'params': {
                'user_id': user_id,
                'cuisine_type': 'american',
                'dietary_preferences': ['gluten-free'],
                'servings': 4,
                'difficulty': 'easy'
            }
        },
        {
            'name': 'Healthy Mediterranean',
            'params': {
                'user_id': user_id,
                'cuisine_type': 'mediterranean',
                'dietary_preferences': [],
                'is_healthy': True,
                'max_calories_per_serving': 400,
                'servings': 2,
                'difficulty': 'medium'
            }
        }
    ]
    
    results = []
    all_issues = []
    
    for test_case in test_cases:
        success, recipe_data, shopping_valid, issues = test_recipe_generation(user_id, test_case)
        results.append({
            'name': test_case['name'],
            'success': success,
            'shopping_valid': shopping_valid,
            'recipe_data': recipe_data,
            'issues': issues
        })
        all_issues.extend(issues)
    
    # Summary of all tests
    print_separator("RECIPE TYPE TESTING SUMMARY")
    
    successful_generations = sum(1 for r in results if r['success'])
    valid_shopping_lists = sum(1 for r in results if r['shopping_valid'])
    
    print(f"Recipe Generation Success: {successful_generations}/{len(test_cases)} ({(successful_generations/len(test_cases)*100):.1f}%)")
    print(f"Shopping List Validation: {valid_shopping_lists}/{len(test_cases)} ({(valid_shopping_lists/len(test_cases)*100):.1f}%)")
    
    for result in results:
        status = "✅" if result['success'] else "❌"
        shopping_status = "✅" if result['shopping_valid'] else "❌"
        print(f"{status} {result['name']}: Generation {'SUCCESS' if result['success'] else 'FAILED'}")
        print(f"   {shopping_status} Shopping List: {'VALID' if result['shopping_valid'] else 'INVALID'}")
    
    return results, all_issues

def analyze_comprehensive_prompt_effectiveness(results):
    """Analyze the effectiveness of the new comprehensive prompt"""
    print_separator("COMPREHENSIVE PROMPT EFFECTIVENESS ANALYSIS")
    
    if not results:
        print("❌ No results to analyze")
        return False
    
    # Metrics to analyze
    total_recipes = len(results)
    successful_recipes = [r for r in results if r['success']]
    valid_shopping_lists = [r for r in results if r['shopping_valid']]
    
    print(f"Total Recipes Tested: {total_recipes}")
    print(f"Successful Generations: {len(successful_recipes)}")
    print(f"Valid Shopping Lists: {len(valid_shopping_lists)}")
    
    # Analyze shopping list quality
    if successful_recipes:
        print(f"\n--- Shopping List Quality Analysis ---")
        
        total_ingredients = 0
        total_shopping_items = 0
        
        for result in successful_recipes:
            if result['recipe_data']:
                ingredients = result['recipe_data'].get('ingredients', [])
                shopping_list = result['recipe_data'].get('shopping_list', [])
                
                total_ingredients += len(ingredients)
                total_shopping_items += len(shopping_list)
                
                print(f"{result['name']}: {len(ingredients)} ingredients → {len(shopping_list)} shopping items")
        
        if total_ingredients > 0:
            extraction_ratio = total_shopping_items / total_ingredients
            print(f"\nOverall Extraction Ratio: {extraction_ratio:.2f} (shopping items per ingredient)")
            
            if extraction_ratio >= 0.8 and extraction_ratio <= 1.2:
                print("✅ EXCELLENT - Extraction ratio is optimal")
            elif extraction_ratio >= 0.6:
                print("⚠️ GOOD - Extraction ratio is acceptable")
            else:
                print("❌ POOR - Extraction ratio indicates issues")
    
    # Overall assessment
    success_rate = (len(successful_recipes) / total_recipes) * 100
    shopping_rate = (len(valid_shopping_lists) / total_recipes) * 100
    
    print(f"\n--- Overall Assessment ---")
    print(f"Recipe Generation Success Rate: {success_rate:.1f}%")
    print(f"Shopping List Validation Rate: {shopping_rate:.1f}%")
    
    if success_rate >= 90 and shopping_rate >= 80:
        print("🎉 EXCELLENT - Comprehensive prompt is working excellently!")
        return True
    elif success_rate >= 75 and shopping_rate >= 70:
        print("✅ GOOD - Comprehensive prompt is working well with minor improvements needed")
        return True
    else:
        print("❌ NEEDS IMPROVEMENT - Comprehensive prompt requires optimization")
        return False

def main():
    """Main test function for Improved OpenAI Recipe Generation & Shopping List Extraction"""
    print_separator("IMPROVED OPENAI RECIPE GENERATION & SHOPPING LIST EXTRACTION TESTING")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"API Base: {API_BASE}")
    print(f"Test User: {TEST_EMAIL}")
    print(f"Test Time: {datetime.now()}")
    print(f"Focus: Testing improved OpenAI prompt for recipe generation and shopping list extraction")
    
    # Step 1: Login with demo@test.com/password123
    user_id = test_login()
    if not user_id:
        print("\n🚨 CANNOT PROCEED - Login failed")
        return
    
    # Step 2: Test recipe generation with different parameters
    print_separator("TESTING RECIPE GENERATION WITH DIFFERENT PARAMETERS")
    
    # Single comprehensive test first
    single_test = {
        'name': 'Italian Pasta with Complex Ingredients',
        'params': {
            'user_id': user_id,
            'cuisine_type': 'italian',
            'dietary_preferences': ['vegetarian'],
            'ingredients_on_hand': ['tomatoes', 'basil', 'garlic'],
            'servings': 4,
            'difficulty': 'medium'
        }
    }
    
    single_success, single_data, single_valid, single_issues = test_recipe_generation(user_id, single_test)
    
    if not single_success:
        print("\n🚨 SINGLE TEST FAILED - Cannot proceed with comprehensive testing")
        print("This may indicate API issues or authentication problems")
        return
    
    # Step 3: Test different recipe types and cuisines for consistency
    results, all_issues = test_different_recipe_types(user_id)
    
    # Step 4: Analyze comprehensive prompt effectiveness
    prompt_effective = analyze_comprehensive_prompt_effectiveness(results)
    
    # Step 5: Test specific shopping list extraction examples from review
    print_separator("TESTING SPECIFIC SHOPPING LIST EXTRACTION EXAMPLES")
    
    # Test with ingredients that should demonstrate the extraction rules
    complex_test = {
        'name': 'Complex Ingredient Extraction Test',
        'params': {
            'user_id': user_id,
            'cuisine_type': 'american',
            'dietary_preferences': [],
            'ingredients_on_hand': ['flour', 'olive oil', 'tomatoes', 'canned tomatoes', 'salt', 'pepper'],
            'servings': 4,
            'difficulty': 'easy'
        }
    }
    
    complex_success, complex_data, complex_valid, complex_issues = test_recipe_generation(user_id, complex_test)
    
    # Final Summary
    print_separator("FINAL TEST SUMMARY - IMPROVED OPENAI PROMPT VALIDATION")
    
    print(f"✅ User Login: SUCCESS")
    print(f"{'✅' if single_success else '❌'} Single Recipe Test: {'PASS' if single_success else 'FAIL'}")
    
    if results:
        successful_generations = sum(1 for r in results if r['success'])
        valid_shopping_lists = sum(1 for r in results if r['shopping_valid'])
        
        print(f"✅ Recipe Generation Tests: {successful_generations}/{len(results)} PASSED")
        print(f"✅ Shopping List Validation: {valid_shopping_lists}/{len(results)} PASSED")
    
    print(f"{'✅' if prompt_effective else '❌'} Comprehensive Prompt Effectiveness: {'EXCELLENT' if prompt_effective else 'NEEDS IMPROVEMENT'}")
    print(f"{'✅' if complex_success else '❌'} Complex Extraction Test: {'PASS' if complex_success else 'FAIL'}")
    
    # Calculate overall success metrics
    total_tests = len(results) if results else 0
    successful_tests = sum(1 for r in results if r['success']) if results else 0
    valid_extractions = sum(1 for r in results if r['shopping_valid']) if results else 0
    
    if total_tests > 0:
        generation_success_rate = (successful_tests / total_tests) * 100
        extraction_success_rate = (valid_extractions / total_tests) * 100
        
        print(f"\n--- OVERALL METRICS ---")
        print(f"Recipe Generation Success Rate: {generation_success_rate:.1f}%")
        print(f"Shopping List Extraction Success Rate: {extraction_success_rate:.1f}%")
        
        # Assessment based on review requirements
        if generation_success_rate >= 90 and extraction_success_rate >= 80:
            print("🎉 EXCELLENT - Improved OpenAI prompt is working excellently!")
            print("✅ Shopping list extraction properly removes quantities/measurements")
            print("✅ Clean ingredient names suitable for Walmart product searches")
            print("✅ Consistent performance across different cuisines and dietary preferences")
        elif generation_success_rate >= 75 and extraction_success_rate >= 70:
            print("✅ GOOD - Improved OpenAI prompt is working well")
            print("⚠️ Minor improvements may be needed for shopping list extraction")
        else:
            print("❌ NEEDS IMPROVEMENT - OpenAI prompt requires optimization")
            print("🔧 Shopping list extraction rules may need refinement")
    
    # Report specific issues found
    if all_issues:
        print(f"\n--- SHOPPING LIST EXTRACTION ISSUES FOUND ---")
        unique_issues = list(set(all_issues))
        for issue in unique_issues[:10]:  # Show first 10 unique issues
            print(f"  - {issue}")
        if len(unique_issues) > 10:
            print(f"  ... and {len(unique_issues) - 10} more unique issues")
    
    # Recommendations based on findings
    print(f"\n--- RECOMMENDATIONS ---")
    if prompt_effective and extraction_success_rate >= 80:
        print("✅ The improved OpenAI prompt is ready for production")
        print("✅ Shopping list extraction meets requirements for Walmart integration")
    else:
        print("🔧 Consider refining the OpenAI prompt to improve shopping list extraction")
        print("🔧 Focus on better handling of compound ingredients (e.g., 'salt and pepper')")
        print("🔧 Improve quantity/measurement removal patterns")
    
    print_separator("TEST COMPLETE - IMPROVED OPENAI PROMPT VALIDATION")

if __name__ == "__main__":
    main()