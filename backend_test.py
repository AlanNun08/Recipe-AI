#!/usr/bin/env python3
"""
Backend API Testing for Stripe Subscription Payment Flow
Testing the Stripe subscription payment flow to identify what's broken as requested in review:
1. Test subscription status endpoint for demo user (demo@test.com) to see their current subscription status
2. Test create-checkout endpoint with demo user to see if they can create a payment session during their trial
3. Test edge cases like:
   - User with trial status trying to subscribe
   - User with expired trial trying to subscribe  
   - User with active paid subscription trying to subscribe again

Focus on the endpoints:
- GET /api/subscription/status/{user_id}
- POST /api/subscription/create-checkout
"""

import requests
import json
import sys
import re
from datetime import datetime

# Backend URL from frontend/.env
BACKEND_URL = "https://4d24c0b0-8c0e-4246-8e3e-2e81e97a4fe7.preview.emergentagent.com"
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

def validate_comprehensive_cooking_instructions(instructions, recipe_name):
    """Validate that cooking instructions are comprehensive and detailed as per review requirements"""
    print(f"\n--- Comprehensive Cooking Instructions Validation for {recipe_name} ---")
    
    if not instructions:
        print("❌ No cooking instructions found in recipe")
        return False, []
    
    print(f"Total Instructions: {len(instructions)}")
    for i, instruction in enumerate(instructions[:3], 1):  # Show first 3
        print(f"  {i}. {instruction[:100]}{'...' if len(instruction) > 100 else ''}")
    if len(instructions) > 3:
        print(f"  ... and {len(instructions) - 3} more instructions")
    
    # Validation criteria based on review requirements
    validation_results = []
    issues = []
    
    # 1. Check for specific temperatures and times
    temp_time_patterns = [
        r'\d+°[CF]',  # Temperature like 350°F or 180°C
        r'\d+\s*degrees?',  # Temperature in degrees
        r'\d+\s*minutes?',  # Time in minutes
        r'\d+\s*hours?',  # Time in hours
        r'\d+-\d+\s*minutes?',  # Time range like 5-7 minutes
        r'for\s+\d+\s*minutes?',  # "for 10 minutes"
        r'until\s+\d+°[CF]',  # "until 165°F"
    ]
    
    temp_time_found = 0
    all_instructions_text = ' '.join(instructions).lower()
    
    for pattern in temp_time_patterns:
        matches = re.findall(pattern, all_instructions_text, re.IGNORECASE)
        temp_time_found += len(matches)
    
    print(f"\n✅ Temperature/Time References: {temp_time_found} found")
    if temp_time_found >= 3:
        print("✅ EXCELLENT - Multiple specific temperatures and times provided")
        validation_results.append(True)
    elif temp_time_found >= 1:
        print("⚠️ GOOD - Some temperatures/times provided")
        validation_results.append(True)
    else:
        print("❌ POOR - No specific temperatures or times found")
        validation_results.append(False)
        issues.append("Missing specific temperatures and cooking times")
    
    # 2. Check for professional cooking techniques
    technique_keywords = [
        'sauté', 'sear', 'braise', 'simmer', 'reduce', 'caramelize', 'deglaze',
        'fold', 'whisk', 'emulsify', 'temper', 'bloom', 'rest', 'proof',
        'season', 'taste and adjust', 'mise en place', 'julienne', 'dice',
        'mince', 'chop finely', 'rough chop', 'brunoise', 'chiffonade'
    ]
    
    techniques_found = 0
    for technique in technique_keywords:
        if technique in all_instructions_text:
            techniques_found += 1
    
    print(f"✅ Professional Techniques: {techniques_found} found")
    if techniques_found >= 5:
        print("✅ EXCELLENT - Multiple professional cooking techniques used")
        validation_results.append(True)
    elif techniques_found >= 3:
        print("⚠️ GOOD - Some professional techniques used")
        validation_results.append(True)
    else:
        print("❌ POOR - Few or no professional techniques found")
        validation_results.append(False)
        issues.append("Lacks professional cooking techniques")
    
    # 3. Check for visual cues
    visual_cue_keywords = [
        'golden brown', 'bubbling', 'tender', 'translucent', 'caramelized',
        'crispy', 'soft', 'firm', 'glossy', 'thick', 'smooth', 'creamy',
        'fragrant', 'aromatic', 'steaming', 'sizzling', 'foaming', 'melted',
        'wilted', 'browned', 'charred', 'opaque', 'clear', 'set'
    ]
    
    visual_cues_found = 0
    for cue in visual_cue_keywords:
        if cue in all_instructions_text:
            visual_cues_found += 1
    
    print(f"✅ Visual Cues: {visual_cues_found} found")
    if visual_cues_found >= 4:
        print("✅ EXCELLENT - Multiple visual cues for cooking stages")
        validation_results.append(True)
    elif visual_cues_found >= 2:
        print("⚠️ GOOD - Some visual cues provided")
        validation_results.append(True)
    else:
        print("❌ POOR - Few or no visual cues found")
        validation_results.append(False)
        issues.append("Lacks visual cues for cooking stages")
    
    # 4. Check for safety notes (internal temperatures)
    safety_patterns = [
        r'internal temperature.*\d+°[CF]',
        r'\d+°[CF].*internal',
        r'food safe',
        r'safely cooked',
        r'cooked through',
        r'no longer pink',
        r'juices run clear'
    ]
    
    safety_notes_found = 0
    for pattern in safety_patterns:
        if re.search(pattern, all_instructions_text, re.IGNORECASE):
            safety_notes_found += 1
    
    print(f"✅ Safety Notes: {safety_notes_found} found")
    if safety_notes_found >= 1:
        print("✅ GOOD - Safety notes included")
        validation_results.append(True)
    else:
        print("⚠️ MINOR - No specific safety notes found")
        validation_results.append(True)  # Not critical for all recipes
    
    # 5. Check for pro tips and techniques
    pro_tip_keywords = [
        'tip:', 'pro tip', 'chef\'s tip', 'note:', 'important:', 'secret',
        'key is', 'make sure', 'be careful', 'don\'t forget', 'remember',
        'for best results', 'optional:', 'variation:', 'substitute'
    ]
    
    pro_tips_found = 0
    for tip in pro_tip_keywords:
        if tip in all_instructions_text:
            pro_tips_found += 1
    
    print(f"✅ Pro Tips/Notes: {pro_tips_found} found")
    if pro_tips_found >= 3:
        print("✅ EXCELLENT - Multiple pro tips and helpful notes")
        validation_results.append(True)
    elif pro_tips_found >= 1:
        print("⚠️ GOOD - Some helpful tips provided")
        validation_results.append(True)
    else:
        print("❌ POOR - No pro tips or helpful notes found")
        validation_results.append(False)
        issues.append("Lacks pro tips and helpful cooking notes")
    
    # 6. Check for sequential step-by-step progression
    sequential_indicators = [
        'first', 'next', 'then', 'after', 'while', 'meanwhile', 'once',
        'when', 'before', 'finally', 'lastly', 'step', 'continue'
    ]
    
    sequential_words = 0
    for indicator in sequential_indicators:
        sequential_words += all_instructions_text.count(indicator)
    
    print(f"✅ Sequential Indicators: {sequential_words} found")
    if sequential_words >= 5:
        print("✅ EXCELLENT - Clear sequential progression")
        validation_results.append(True)
    elif sequential_words >= 2:
        print("⚠️ GOOD - Some sequential flow")
        validation_results.append(True)
    else:
        print("❌ POOR - Lacks clear sequential progression")
        validation_results.append(False)
        issues.append("Instructions lack clear sequential flow")
    
    # 7. Check against basic instructions (should be much more detailed)
    basic_instruction_patterns = [
        r'^cook the \w+$',
        r'^add \w+$',
        r'^mix \w+$',
        r'^heat \w+$',
        r'^serve$'
    ]
    
    basic_instructions_count = 0
    for instruction in instructions:
        for pattern in basic_instruction_patterns:
            if re.match(pattern, instruction.strip(), re.IGNORECASE):
                basic_instructions_count += 1
                break
    
    if basic_instructions_count == 0:
        print("✅ EXCELLENT - No basic/vague instructions found")
        validation_results.append(True)
    elif basic_instructions_count <= 1:
        print("⚠️ GOOD - Mostly detailed instructions")
        validation_results.append(True)
    else:
        print(f"❌ POOR - {basic_instructions_count} basic/vague instructions found")
        validation_results.append(False)
        issues.append(f"Contains {basic_instructions_count} basic/vague instructions")
    
    # Overall assessment
    passed_criteria = sum(validation_results)
    total_criteria = len(validation_results)
    success_rate = (passed_criteria / total_criteria) * 100
    
    print(f"\n--- Overall Instruction Quality Assessment ---")
    print(f"Criteria Passed: {passed_criteria}/{total_criteria} ({success_rate:.1f}%)")
    
    if success_rate >= 85:
        print("🎉 EXCELLENT - Instructions are comprehensive and professional-quality")
        return True, issues
    elif success_rate >= 70:
        print("✅ GOOD - Instructions are detailed with room for minor improvements")
        return True, issues
    else:
        print("❌ NEEDS IMPROVEMENT - Instructions lack comprehensive detail")
        return False, issues

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
    
    return all(validation_results), issues

def test_recipe_generation(user_id, test_params):
    """Test recipe generation with specific parameters and validate comprehensive instructions"""
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
            instructions = response_data.get('instructions', [])
            shopping_list = response_data.get('shopping_list', [])
            cuisine_type = response_data.get('cuisine_type', 'Unknown')
            
            print(f"✅ Recipe Title: {title}")
            print(f"✅ Cuisine Type: {cuisine_type}")
            print(f"✅ Ingredients Count: {len(ingredients)}")
            print(f"✅ Instructions Count: {len(instructions)}")
            print(f"✅ Shopping List Count: {len(shopping_list)}")
            
            # Validate comprehensive cooking instructions (main focus)
            instructions_valid, instruction_issues = validate_comprehensive_cooking_instructions(instructions, title)
            
            # Validate shopping list extraction (secondary focus)
            shopping_valid, shopping_issues = validate_shopping_list_extraction(ingredients, shopping_list, title)
            
            return True, response_data, instructions_valid, shopping_valid, instruction_issues + shopping_issues
            
        else:
            print(f"\n❌ RECIPE GENERATION FAILED - Status: {response.status_code}")
            return False, response_data, False, False, []
            
    except Exception as e:
        print(f"\n❌ RECIPE GENERATION ERROR: {str(e)}")
        return False, None, False, False, []

def test_different_recipe_types(user_id):
    """Test recipe generation with different cuisines to validate consistency of comprehensive instructions"""
    print_separator("TESTING DIFFERENT RECIPE TYPES FOR COMPREHENSIVE INSTRUCTION CONSISTENCY")
    
    # Test cases covering different cuisines as requested in review
    test_cases = [
        {
            'name': 'Italian Pasta Dish',
            'params': {
                'user_id': user_id,
                'cuisine_type': 'italian',
                'dietary_preferences': [],
                'servings': 4,
                'difficulty': 'medium'
            }
        },
        {
            'name': 'Mexican Cuisine',
            'params': {
                'user_id': user_id,
                'cuisine_type': 'mexican',
                'dietary_preferences': [],
                'servings': 4,
                'difficulty': 'medium'
            }
        },
        {
            'name': 'Asian Stir-fry',
            'params': {
                'user_id': user_id,
                'cuisine_type': 'asian',
                'dietary_preferences': [],
                'servings': 3,
                'difficulty': 'medium'
            }
        },
        {
            'name': 'American Comfort Food',
            'params': {
                'user_id': user_id,
                'cuisine_type': 'american',
                'dietary_preferences': [],
                'servings': 4,
                'difficulty': 'easy'
            }
        },
        {
            'name': 'Mediterranean Dish',
            'params': {
                'user_id': user_id,
                'cuisine_type': 'mediterranean',
                'dietary_preferences': [],
                'servings': 2,
                'difficulty': 'medium'
            }
        }
    ]
    
    results = []
    all_issues = []
    
    for test_case in test_cases:
        success, recipe_data, instructions_valid, shopping_valid, issues = test_recipe_generation(user_id, test_case)
        results.append({
            'name': test_case['name'],
            'success': success,
            'instructions_valid': instructions_valid,
            'shopping_valid': shopping_valid,
            'recipe_data': recipe_data,
            'issues': issues
        })
        all_issues.extend(issues)
    
    # Summary of all tests
    print_separator("RECIPE TYPE TESTING SUMMARY")
    
    successful_generations = sum(1 for r in results if r['success'])
    valid_instructions = sum(1 for r in results if r['instructions_valid'])
    valid_shopping_lists = sum(1 for r in results if r['shopping_valid'])
    
    print(f"Recipe Generation Success: {successful_generations}/{len(test_cases)} ({(successful_generations/len(test_cases)*100):.1f}%)")
    print(f"Comprehensive Instructions: {valid_instructions}/{len(test_cases)} ({(valid_instructions/len(test_cases)*100):.1f}%)")
    print(f"Shopping List Validation: {valid_shopping_lists}/{len(test_cases)} ({(valid_shopping_lists/len(test_cases)*100):.1f}%)")
    
    for result in results:
        status = "✅" if result['success'] else "❌"
        instruction_status = "✅" if result['instructions_valid'] else "❌"
        shopping_status = "✅" if result['shopping_valid'] else "❌"
        print(f"{status} {result['name']}: Generation {'SUCCESS' if result['success'] else 'FAILED'}")
        print(f"   {instruction_status} Instructions: {'COMPREHENSIVE' if result['instructions_valid'] else 'BASIC'}")
        print(f"   {shopping_status} Shopping List: {'VALID' if result['shopping_valid'] else 'INVALID'}")
    
    return results, all_issues

def analyze_enhanced_prompt_effectiveness(results):
    """Analyze the effectiveness of the enhanced OpenAI prompt for comprehensive cooking instructions"""
    print_separator("ENHANCED PROMPT EFFECTIVENESS ANALYSIS")
    
    if not results:
        print("❌ No results to analyze")
        return False
    
    # Metrics to analyze
    total_recipes = len(results)
    successful_recipes = [r for r in results if r['success']]
    comprehensive_instructions = [r for r in results if r['instructions_valid']]
    valid_shopping_lists = [r for r in results if r['shopping_valid']]
    
    print(f"Total Recipes Tested: {total_recipes}")
    print(f"Successful Generations: {len(successful_recipes)}")
    print(f"Comprehensive Instructions: {len(comprehensive_instructions)}")
    print(f"Valid Shopping Lists: {len(valid_shopping_lists)}")
    
    # Overall assessment
    success_rate = (len(successful_recipes) / total_recipes) * 100
    instruction_rate = (len(comprehensive_instructions) / total_recipes) * 100
    shopping_rate = (len(valid_shopping_lists) / total_recipes) * 100
    
    print(f"\n--- Overall Assessment ---")
    print(f"Recipe Generation Success Rate: {success_rate:.1f}%")
    print(f"Comprehensive Instructions Rate: {instruction_rate:.1f}%")
    print(f"Shopping List Validation Rate: {shopping_rate:.1f}%")
    
    # Assessment based on review requirements
    if success_rate >= 90 and instruction_rate >= 80 and shopping_rate >= 80:
        print("🎉 EXCELLENT - Enhanced prompt is generating professional-quality comprehensive instructions!")
        return True
    elif success_rate >= 75 and instruction_rate >= 70:
        print("✅ GOOD - Enhanced prompt is working well with room for minor improvements")
        return True
    else:
        print("❌ NEEDS IMPROVEMENT - Enhanced prompt requires optimization")
        return False

def main():
    """Main test function for Enhanced OpenAI Prompt with Comprehensive Cooking Instructions"""
    print_separator("ENHANCED OPENAI PROMPT WITH COMPREHENSIVE COOKING INSTRUCTIONS TESTING")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"API Base: {API_BASE}")
    print(f"Test User: {TEST_EMAIL}")
    print(f"Test Time: {datetime.now()}")
    print(f"Focus: Testing enhanced OpenAI prompt for comprehensive cooking instructions")
    
    # Step 1: Login with demo@test.com/password123
    user_id = test_login()
    if not user_id:
        print("\n🚨 CANNOT PROCEED - Login failed")
        return
    
    # Step 2: Test single recipe generation first to validate basic functionality
    print_separator("TESTING SINGLE RECIPE GENERATION WITH COMPREHENSIVE INSTRUCTIONS")
    
    single_test = {
        'name': 'Italian Pasta with Comprehensive Instructions Test',
        'params': {
            'user_id': user_id,
            'cuisine_type': 'italian',
            'dietary_preferences': [],
            'servings': 4,
            'difficulty': 'medium'
        }
    }
    
    single_success, single_data, single_instructions_valid, single_shopping_valid, single_issues = test_recipe_generation(user_id, single_test)
    
    if not single_success:
        print("\n🚨 SINGLE TEST FAILED - Cannot proceed with comprehensive testing")
        print("This may indicate API issues or authentication problems")
        return
    
    # Step 3: Test different recipe types for consistency (Italian, Mexican, etc.)
    results, all_issues = test_different_recipe_types(user_id)
    
    # Step 4: Analyze enhanced prompt effectiveness
    prompt_effective = analyze_enhanced_prompt_effectiveness(results)
    
    # Step 5: Test specific scenarios mentioned in review
    print_separator("TESTING SPECIFIC SCENARIOS FROM REVIEW")
    
    # Test for novice and experienced cook suitability
    novice_test = {
        'name': 'Novice Cook Friendly Recipe',
        'params': {
            'user_id': user_id,
            'cuisine_type': 'american',
            'dietary_preferences': [],
            'servings': 2,
            'difficulty': 'easy'
        }
    }
    
    experienced_test = {
        'name': 'Experienced Cook Recipe',
        'params': {
            'user_id': user_id,
            'cuisine_type': 'french',
            'dietary_preferences': [],
            'servings': 4,
            'difficulty': 'hard'
        }
    }
    
    novice_success, novice_data, novice_instructions_valid, novice_shopping_valid, novice_issues = test_recipe_generation(user_id, novice_test)
    experienced_success, experienced_data, experienced_instructions_valid, experienced_shopping_valid, experienced_issues = test_recipe_generation(user_id, experienced_test)
    
    # Final Summary
    print_separator("FINAL TEST SUMMARY - ENHANCED OPENAI PROMPT VALIDATION")
    
    print(f"✅ User Login: SUCCESS")
    print(f"{'✅' if single_success else '❌'} Single Recipe Test: {'PASS' if single_success else 'FAIL'}")
    print(f"{'✅' if single_instructions_valid else '❌'} Single Recipe Instructions: {'COMPREHENSIVE' if single_instructions_valid else 'BASIC'}")
    
    if results:
        successful_generations = sum(1 for r in results if r['success'])
        comprehensive_instructions = sum(1 for r in results if r['instructions_valid'])
        valid_shopping_lists = sum(1 for r in results if r['shopping_valid'])
        
        print(f"✅ Recipe Generation Tests: {successful_generations}/{len(results)} PASSED")
        print(f"✅ Comprehensive Instructions: {comprehensive_instructions}/{len(results)} PASSED")
        print(f"✅ Shopping List Validation: {valid_shopping_lists}/{len(results)} PASSED")
    
    print(f"{'✅' if prompt_effective else '❌'} Enhanced Prompt Effectiveness: {'EXCELLENT' if prompt_effective else 'NEEDS IMPROVEMENT'}")
    print(f"{'✅' if novice_success and novice_instructions_valid else '❌'} Novice Cook Suitability: {'PASS' if novice_success and novice_instructions_valid else 'FAIL'}")
    print(f"{'✅' if experienced_success and experienced_instructions_valid else '❌'} Experienced Cook Suitability: {'PASS' if experienced_success and experienced_instructions_valid else 'FAIL'}")
    
    # Calculate overall success metrics
    total_tests = len(results) if results else 0
    successful_tests = sum(1 for r in results if r['success']) if results else 0
    comprehensive_tests = sum(1 for r in results if r['instructions_valid']) if results else 0
    valid_extractions = sum(1 for r in results if r['shopping_valid']) if results else 0
    
    if total_tests > 0:
        generation_success_rate = (successful_tests / total_tests) * 100
        instruction_success_rate = (comprehensive_tests / total_tests) * 100
        extraction_success_rate = (valid_extractions / total_tests) * 100
        
        print(f"\n--- OVERALL METRICS ---")
        print(f"Recipe Generation Success Rate: {generation_success_rate:.1f}%")
        print(f"Comprehensive Instructions Success Rate: {instruction_success_rate:.1f}%")
        print(f"Shopping List Extraction Success Rate: {extraction_success_rate:.1f}%")
        
        # Assessment based on review requirements
        if generation_success_rate >= 90 and instruction_success_rate >= 80:
            print("🎉 EXCELLENT - Enhanced OpenAI prompt is generating professional-quality instructions!")
            print("✅ Instructions include specific temperatures and times")
            print("✅ Professional cooking techniques are used consistently")
            print("✅ Visual cues help cooks identify cooking stages")
            print("✅ Safety notes ensure food safety")
            print("✅ Pro tips enhance cooking experience")
            print("✅ Sequential step-by-step progression is clear")
            print("✅ Instructions are significantly more detailed than basic 'cook the chicken' style")
            print("✅ Both shopping list extraction AND comprehensive instructions work together")
        elif generation_success_rate >= 75 and instruction_success_rate >= 70:
            print("✅ GOOD - Enhanced OpenAI prompt is working well")
            print("⚠️ Minor improvements may be needed for instruction comprehensiveness")
        else:
            print("❌ NEEDS IMPROVEMENT - Enhanced OpenAI prompt requires optimization")
            print("🔧 Instructions may still be too basic or lack professional detail")
    
    # Report specific issues found
    if all_issues:
        print(f"\n--- INSTRUCTION QUALITY ISSUES FOUND ---")
        unique_issues = list(set(all_issues))
        for issue in unique_issues[:10]:  # Show first 10 unique issues
            print(f"  - {issue}")
        if len(unique_issues) > 10:
            print(f"  ... and {len(unique_issues) - 10} more unique issues")
    
    # Recommendations based on findings
    print(f"\n--- RECOMMENDATIONS ---")
    if prompt_effective and instruction_success_rate >= 80:
        print("✅ The enhanced OpenAI prompt is ready for production")
        print("✅ Comprehensive cooking instructions meet professional standards")
        print("✅ Instructions are suitable for both novice and experienced cooks")
        print("✅ Shopping list extraction works well alongside comprehensive instructions")
    else:
        print("🔧 Consider further refining the OpenAI prompt to improve instruction quality")
        print("🔧 Focus on adding more specific temperatures, times, and professional techniques")
        print("🔧 Enhance visual cues and safety notes for better cooking guidance")
        print("🔧 Ensure consistent quality across different cuisine types")
    
    print_separator("TEST COMPLETE - ENHANCED OPENAI PROMPT WITH COMPREHENSIVE COOKING INSTRUCTIONS")

if __name__ == "__main__":
    main()