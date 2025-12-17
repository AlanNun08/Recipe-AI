# Logging Enhancements for Recipe Generator

## Overview
Enhanced logging in both frontend and backend to provide complete visibility into the recipe generation flow.

## Frontend Enhancements (`RecipeGeneratorScreen.js`)

### Request Validation Logging
- Logs all request payload keys
- Validates presence of required fields:
  - `user_id`
  - `cuisine_type`
  - `meal_type`
  - `difficulty`
  - `servings`

### Request/Response Timing
- Records request start time with ISO timestamp
- Tracks total elapsed time for API call
- Logs response status and headers

### Response Validation
- Validates response contains required fields: `name`, `ingredients`, `instructions`
- Counts ingredients and instructions in response
- Logs response object structure

### Error Handling Details
- Full error stack trace
- Request details (method, URL, status, readyState)
- Response details (status, statusText, headers, data, config)
- More granular error messages for debugging

## Backend Enhancements (`server.py`)

### Request Reception
- Logs entire request object as dictionary
- Logs individual fields:
  - Servings
  - Prep time max
  - Dietary preferences
  - Ingredients on hand

### OpenAI API Call
- Logs response object details
- Logs number of choices in response
- Logs token usage (prompt_tokens, completion_tokens, total_tokens)
- Logs first 300 and last 300 characters of AI response

### Recipe Data Processing
- Logs recipe keys before and after data preparation
- Counts ingredients, ingredients_clean, and instructions
- Samples first 2 items of each list for verification

### Database Operations
- Logs database save attempt with recipe name
- Logs inserted ObjectId and its type
- Checks for contamination of response object after database operations
- Logs when `_id` field is removed from response

### JSON Serialization
- Tests JSON serialization before response
- Logs serialized size in bytes
- Identifies problematic keys if serialization fails
- Provides detailed error information for non-serializable objects

### Final Response Validation
- Validates all required fields are present
- Confirms recipe name, ID, and user_id
- Verifies ingredients and instructions are accessible
- Ensures ingredients_clean field exists for Walmart search

## Expected Log Output

### Successful Generation Flow
```
🤖 Recipe generation request for user: [user-id]
🍳 Recipe details: [cuisine] [mealtype] ([difficulty])
📊 Request object received: {...}
📊 Servings: 4, Prep time max: [time]
🥗 Dietary preferences: [list]
🥘 Ingredients on hand: [list]
🤖 Sending request to OpenAI...
✅ OpenAI response received
📊 OpenAI response object: {...}
📊 OpenAI response choices: 1 choices
📊 OpenAI response usage: {...}
📝 Raw AI response length: [length] characters
📝 First 300 chars of response: [json start]
📝 Last 300 chars of response: [json end]
🔄 Parsing JSON response...
✅ JSON parsed successfully
💾 Saving recipe to database: [recipe-name]
💾 Recipe data keys before save: [list of keys]
💾 Recipe ingredients count: [count]
💾 Recipe ingredients_clean count: [count]
💾 Recipe instructions count: [count]
✅ Recipe saved to database with ObjectId: [id]
✅ JSON serialization test passed, size: [bytes] bytes
✅ About to return recipe: [recipe-name]
✅ Recipe ID: [id]
✅ User ID: [user-id]
✅ Recipe generated and saved: [recipe-name]
✅ Returning response with status 200
```

## Debugging Steps

1. **Check Frontend Logs**: Open browser console (F12) and look for the enhanced logs starting with emojis
2. **Check Request**: Verify `📤 Sending request to API:` shows all required fields
3. **Check Response**: Verify `📥 Received response from API:` has complete recipe data
4. **Check Server Logs**: If using local development, check terminal for backend logs
5. **If Missing Data**: Look for warnings like `⚠️ WARNING: ingredients_clean field is missing!`

## Common Issues and Fixes

### Issue: ingredients_clean missing
- **Cause**: OpenAI didn't include it in response
- **Fix**: Check logs for fallback generation message
- **Result**: Should see `✅ Generated X clean ingredients as fallback`

### Issue: ObjectId contamination
- **Cause**: MongoDB operation affecting original response object
- **Fix**: Deep copy created before database operation
- **Result**: Should see `🔧 FIX: Removed _id from response object` if it occurred

### Issue: JSON serialization failure
- **Cause**: Non-serializable objects in recipe_data
- **Fix**: Automatic detection and removal of problematic keys
- **Result**: Should see `🔧 FIX: Removed problematic keys` if it occurred

## Data Flow Verification

The complete data flow can now be verified with these logs:

1. **Frontend sends**: `📤 Sending request to API:` 
2. **Backend receives**: `🤖 Recipe generation request for user:`
3. **OpenAI responds**: `✅ OpenAI response received`
4. **Parsing**: `🔄 Parsing JSON response...` → `✅ JSON parsed successfully`
5. **Database saves**: `✅ Recipe saved to database with ObjectId:`
6. **Response validation**: `🔍 DEBUG: Final recipe_data before JSONResponse:`
7. **Frontend receives**: `📥 Received response from API:`
