# API Reference Documentation

## Overview
This document provides comprehensive documentation for all API endpoints in the AI Chef application. All endpoints are prefixed with `/api` for proper routing.

## Base Configuration
```javascript
const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;
// All requests: `${API_BASE_URL}/api/endpoint`
```

## Authentication
All protected endpoints require user authentication. The application uses session-based authentication with JWT tokens.

### Authentication Headers
```javascript
headers: {
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${token}` // When applicable
}
```

## Response Format
All API responses follow a consistent format:

### Success Response
```json
{
  "success": true,
  "data": { /* Response data */ },
  "message": "Operation completed successfully"
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": { /* Additional error details */ }
  }
}
```

## Authentication Endpoints

### Register User
Creates a new user account with trial subscription.

```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword",
  "name": "User Name"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid-string",
      "email": "user@example.com",
      "name": "User Name",
      "created_at": "2025-01-01T12:00:00Z",
      "subscription": {
        "status": "trialing",
        "trial_end": "2025-01-08T12:00:00Z"
      }
    },
    "token": "jwt-token-string"
  },
  "message": "User registered successfully"
}
```

**Error Responses:**
- `400` - Invalid input data
- `409` - Email already exists

---

### Login User
Authenticates existing user and returns session token.

```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "userpassword"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid-string",
      "email": "user@example.com",
      "name": "User Name",
      "subscription": {
        "status": "active",
        "current_period_end": "2025-02-01T12:00:00Z"
      }
    },
    "token": "jwt-token-string"
  },
  "message": "Login successful"
}
```

**Error Responses:**
- `400` - Invalid credentials
- `404` - User not found

---

### Health Check
Checks API service health and feature availability.

```http
GET /api/health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "buildyoursmartcart",
  "version": "2.2.1",
  "features": {
    "openai": true,
    "stripe": true,
    "mailjet": true,
    "walmart": true
  },
  "timestamp": "2025-01-01T12:00:00Z"
}
```

## Recipe Management Endpoints

### Generate Recipe
Creates a personalized recipe using AI based on user preferences.

```http
POST /api/recipes/generate
Content-Type: application/json

{
  "user_id": "uuid-string",
  "recipe_type": "cuisine",
  "cuisine_type": "italian",
  "dietary_preferences": ["vegetarian", "gluten-free"],
  "difficulty": "easy",
  "cooking_time": "30 minutes",
  "servings": 4,
  "special_ingredients": "I have tomatoes and basil",
  "meal_type": "dinner"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "recipe-uuid",
    "name": "Margherita Pizza",
    "description": "A classic Italian pizza with fresh tomatoes and basil",
    "ingredients": [
      "2 cups all-purpose flour",
      "1 cup warm water",
      "2 tbsp olive oil",
      "1 tsp salt",
      "1 tsp active dry yeast",
      "1 cup crushed tomatoes",
      "8 oz fresh mozzarella",
      "Fresh basil leaves"
    ],
    "instructions": [
      "Dissolve yeast in warm water and let sit for 5 minutes",
      "Mix flour and salt in a large bowl",
      "Add yeast mixture and olive oil to flour",
      "Knead dough for 10 minutes until smooth",
      "Let rise for 1 hour",
      "Roll out dough and add toppings",
      "Bake at 450°F for 12-15 minutes"
    ],
    "prep_time": "20 minutes",
    "cook_time": "15 minutes",
    "total_time": "35 minutes",
    "servings": 4,
    "difficulty": "easy",
    "cuisine_type": "italian",
    "dietary_info": {
      "vegetarian": true,
      "gluten_free": false,
      "calories_per_serving": 320
    },
    "created_at": "2025-01-01T12:00:00Z"
  },
  "message": "Recipe generated successfully"
}
```

**Error Responses:**
- `400` - Invalid request parameters
- `401` - User not authenticated
- `429` - Rate limit exceeded
- `500` - AI service unavailable

---

### Get Recipe History
Retrieves all recipes created by a user.

```http
GET /api/recipes/history/{user_id}
```

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20)
- `category` (optional): Filter by category ('regular', 'starbucks')
- `cuisine` (optional): Filter by cuisine type

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "recipes": [
      {
        "id": "recipe-uuid-1",
        "title": "Margherita Pizza",
        "description": "A classic Italian pizza",
        "cuisine_type": "italian",
        "prep_time": "20 minutes",
        "cook_time": "15 minutes",
        "servings": 4,
        "difficulty": "easy",
        "created_at": "2025-01-01T12:00:00Z",
        "category": "regular",
        "type": "recipe"
      },
      {
        "id": "starbucks-uuid-1",
        "title": "Vanilla Bean Frappuccino",
        "description": "Creamy vanilla drink",
        "base_drink": "Frappuccino",
        "created_at": "2025-01-01T10:00:00Z",
        "category": "starbucks",
        "type": "starbucks"
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 3,
      "total_count": 25,
      "per_page": 20,
      "has_next": true,
      "has_previous": false
    }
  },
  "message": "Recipe history retrieved successfully"
}
```

**Error Responses:**
- `404` - User not found
- `403` - Access denied

---

### Get Recipe Detail
Retrieves complete details for a specific recipe.

```http
GET /api/recipes/{recipe_id}/detail
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "recipe-uuid",
    "name": "Margherita Pizza",
    "description": "A classic Italian pizza with fresh tomatoes and basil",
    "ingredients": [
      "2 cups all-purpose flour",
      "1 cup warm water",
      "2 tbsp olive oil",
      "1 tsp salt",
      "1 tsp active dry yeast",
      "1 cup crushed tomatoes",
      "8 oz fresh mozzarella",
      "Fresh basil leaves"
    ],
    "instructions": [
      "Dissolve yeast in warm water and let sit for 5 minutes",
      "Mix flour and salt in a large bowl",
      "Add yeast mixture and olive oil to flour",
      "Knead dough for 10 minutes until smooth",
      "Let rise for 1 hour",
      "Roll out dough and add toppings",
      "Bake at 450°F for 12-15 minutes"
    ],
    "prep_time": "20 minutes",
    "cook_time": "15 minutes",
    "total_time": "35 minutes",
    "servings": 4,
    "difficulty": "easy",
    "cuisine_type": "italian",
    "dietary_info": {
      "vegetarian": true,
      "gluten_free": false,
      "calories_per_serving": 320
    },
    "nutritional_info": {
      "calories": 320,
      "protein": "12g",
      "carbohydrates": "45g",
      "fat": "10g",
      "fiber": "3g",
      "sodium": "680mg"
    },
    "user_id": "user-uuid",
    "created_at": "2025-01-01T12:00:00Z",
    "updated_at": "2025-01-01T12:00:00Z"
  },
  "message": "Recipe details retrieved successfully"
}
```

**Error Responses:**
- `404` - Recipe not found
- `403` - Access denied

---

### Delete Recipe
Permanently removes a recipe from user's collection.

```http
DELETE /api/recipes/{recipe_id}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "deleted_recipe_id": "recipe-uuid"
  },
  "message": "Recipe deleted successfully"
}
```

**Error Responses:**
- `404` - Recipe not found
- `403` - Access denied

---

### Get Recipe Cart Options
Generates Walmart shopping cart options for recipe ingredients.

```http
POST /api/recipes/{recipe_id}/cart-options
Content-Type: application/json

{
  "zip_code": "12345" // Optional: for location-based product availability
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "recipe_id": "recipe-uuid",
    "ingredient_matches": [
      {
        "ingredient": "2 cups all-purpose flour",
        "products": [
          {
            "id": "walmart-product-123",
            "name": "Great Value All-Purpose Flour, 5 lb",
            "price": 1.98,
            "image": "https://i5.walmartimages.com/asr/product-image.jpeg",
            "rating": 4.5,
            "review_count": 234,
            "availability": "in_stock",
            "walmart_url": "https://www.walmart.com/ip/product/123"
          },
          {
            "id": "walmart-product-124",
            "name": "Gold Medal All-Purpose Flour, 5 lb",
            "price": 2.48,
            "image": "https://i5.walmartimages.com/asr/product-image.jpeg",
            "rating": 4.7,
            "review_count": 156,
            "availability": "in_stock",
            "walmart_url": "https://www.walmart.com/ip/product/124"
          }
        ]
      },
      {
        "ingredient": "1 cup crushed tomatoes",
        "products": [
          {
            "id": "walmart-product-456",
            "name": "Hunt's Crushed Tomatoes, 14.5 oz",
            "price": 0.98,
            "image": "https://i5.walmartimages.com/asr/product-image.jpeg",
            "rating": 4.3,
            "review_count": 89,
            "availability": "in_stock",
            "walmart_url": "https://www.walmart.com/ip/product/456"
          }
        ]
      }
    ],
    "summary": {
      "total_ingredients": 8,
      "matched_ingredients": 6,
      "total_products": 12,
      "estimated_total": 15.67,
      "estimated_savings": 3.21
    },
    "cart_url": "https://www.walmart.com/cart?items=123,456,789",
    "generated_at": "2025-01-01T12:00:00Z"
  },
  "message": "Cart options generated successfully"
}
```

**Error Responses:**
- `404` - Recipe not found
- `503` - Walmart service unavailable

## Weekly Recipe Endpoints

### Generate Weekly Meal Plan
Creates a 7-day meal plan with recipes and shopping list.

```http
POST /api/weekly-recipes/generate
Content-Type: application/json

{
  "user_id": "uuid-string",
  "dietary_preferences": ["vegetarian"],
  "allergies": ["nuts"],
  "favorite_cuisines": ["italian", "mexican"],
  "budget_range": "moderate", // "budget", "moderate", "premium"
  "family_size": 4,
  "cooking_skill": "intermediate",
  "meal_types": ["dinner"], // ["breakfast", "lunch", "dinner"]
  "force_regeneration": false
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "plan_id": "plan-uuid",
    "user_id": "user-uuid",
    "week_start": "2025-01-06",
    "week_end": "2025-01-12",
    "meals": [
      {
        "day": "monday",
        "date": "2025-01-06",
        "recipe": {
          "id": "recipe-uuid-1",
          "name": "Vegetarian Pasta Primavera",
          "description": "Fresh vegetables with pasta in light cream sauce",
          "prep_time": "20 minutes",
          "cook_time": "25 minutes",
          "servings": 4,
          "difficulty": "easy",
          "cuisine_type": "italian"
        }
      },
      {
        "day": "tuesday",
        "date": "2025-01-07",
        "recipe": {
          "id": "recipe-uuid-2",
          "name": "Black Bean Tacos",
          "description": "Flavorful vegetarian tacos with fresh toppings",
          "prep_time": "15 minutes",
          "cook_time": "20 minutes",
          "servings": 4,
          "difficulty": "easy",
          "cuisine_type": "mexican"
        }
      }
      // ... 5 more days
    ],
    "shopping_list": {
      "produce": [
        "2 bell peppers",
        "1 onion",
        "3 tomatoes",
        "1 bunch cilantro"
      ],
      "pantry": [
        "1 lb pasta",
        "2 cans black beans",
        "8 taco shells"
      ],
      "dairy": [
        "1 cup heavy cream",
        "8 oz cheese"
      ],
      "estimated_cost": 47.89
    },
    "nutritional_summary": {
      "avg_calories_per_meal": 520,
      "protein": "18g",
      "carbohydrates": "65g",
      "fat": "20g"
    },
    "dietary_compliance": {
      "vegetarian": true,
      "nut_free": true,
      "matches_preferences": 100
    },
    "generated_at": "2025-01-01T12:00:00Z"
  },
  "message": "Weekly meal plan generated successfully"
}
```

**Error Responses:**
- `400` - Invalid parameters
- `401` - User not authenticated
- `429` - Generation limit exceeded

---

### Get Weekly Meal Plan
Retrieves current or specific weekly meal plan for user.

```http
GET /api/weekly-recipes/{user_id}
```

**Query Parameters:**
- `week_start` (optional): Start date for specific week (YYYY-MM-DD)

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "plan_id": "plan-uuid",
    "user_id": "user-uuid",
    "week_start": "2025-01-06",
    "week_end": "2025-01-12",
    "meals": [
      // ... same structure as generate response
    ],
    "shopping_list": {
      // ... shopping list data
    },
    "status": "active",
    "created_at": "2025-01-01T12:00:00Z"
  },
  "message": "Weekly meal plan retrieved successfully"
}
```

---

### Get Individual Weekly Recipe
Retrieves detailed information for a specific recipe from a weekly plan.

```http
GET /api/weekly-recipes/recipe/{recipe_id}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "recipe-uuid",
    "name": "Vegetarian Pasta Primavera",
    "description": "Fresh vegetables with pasta in light cream sauce",
    "ingredients": [
      "1 lb penne pasta",
      "2 bell peppers, sliced",
      "1 zucchini, diced",
      "1 cup cherry tomatoes",
      "1/2 cup heavy cream",
      "1/4 cup parmesan cheese",
      "2 cloves garlic, minced",
      "2 tbsp olive oil"
    ],
    "instructions": [
      "Cook pasta according to package directions",
      "Heat olive oil in large pan",
      "Sauté garlic and vegetables until tender",
      "Add cream and simmer",
      "Toss with cooked pasta and cheese",
      "Serve immediately"
    ],
    "prep_time": "20 minutes",
    "cook_time": "25 minutes",
    "total_time": "45 minutes",
    "servings": 4,
    "difficulty": "easy",
    "cuisine_type": "italian",
    "meal_plan_info": {
      "plan_id": "plan-uuid",
      "day": "monday",
      "date": "2025-01-06"
    }
  },
  "message": "Weekly recipe retrieved successfully"
}
```

---

### Get Weekly Cart Options
Generates comprehensive Walmart shopping cart for entire weekly meal plan.

```http
POST /api/v2/walmart/weekly-cart-options
Query Parameters: recipe_id={recipe_id}

Content-Type: application/json

{
  "zip_code": "12345" // Optional
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "plan_id": "plan-uuid",
    "ingredient_matches": [
      {
        "ingredient": "1 lb penne pasta",
        "recipe_count": 2, // Used in 2 recipes this week
        "products": [
          {
            "id": "walmart-product-789",
            "name": "Barilla Penne Pasta, 1 lb",
            "price": 1.24,
            "image": "https://i5.walmartimages.com/asr/product-image.jpeg",
            "rating": 4.6,
            "review_count": 445,
            "availability": "in_stock"
          }
        ]
      }
      // ... more ingredients
    ],
    "summary": {
      "total_ingredients": 45,
      "matched_ingredients": 42,
      "total_products": 67,
      "estimated_total": 156.78,
      "estimated_savings": 23.45,
      "cost_per_meal": 22.40
    },
    "cart_url": "https://www.walmart.com/cart?items=789,456,123",
    "delivery_options": {
      "pickup_available": true,
      "delivery_available": true,
      "estimated_pickup_time": "2 hours",
      "estimated_delivery_time": "Same day"
    }
  },
  "message": "Weekly cart options generated successfully"
}
```

## Starbucks Recipe Endpoints

### Generate Starbucks Recipe
Creates a custom Starbucks drink recipe based on preferences.

```http
POST /api/starbucks/generate
Content-Type: application/json

{
  "user_id": "uuid-string",
  "drink_type": "frappuccino", // "hot", "cold", "frappuccino", "tea"
  "flavor_profile": "sweet", // "sweet", "bitter", "fruity", "creamy"
  "caffeine_level": "medium", // "none", "low", "medium", "high"
  "dietary_preferences": ["dairy-free"],
  "size": "grande",
  "special_requests": "extra foam, light ice"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "starbucks-recipe-uuid",
    "drink_name": "Vanilla Bean Coconut Frappuccino",
    "description": "A creamy dairy-free frappuccino with vanilla and coconut flavors",
    "base_drink": "Vanilla Bean Frappuccino",
    "size": "grande",
    "modifications": [
      "Substitute coconut milk",
      "Add 1 pump vanilla syrup",
      "Add coconut flakes",
      "Light ice",
      "Extra whipped coconut cream"
    ],
    "instructions": [
      "Order a Grande Vanilla Bean Frappuccino",
      "Ask for coconut milk instead of regular milk",
      "Add 1 pump of vanilla syrup",
      "Request coconut flakes blended in",
      "Ask for light ice",
      "Top with coconut whipped cream"
    ],
    "estimated_cost": 5.85,
    "calories": 280,
    "caffeine_content": "75mg",
    "dietary_info": {
      "dairy_free": true,
      "vegan": false,
      "sugar_content": "high"
    },
    "popularity_score": 8.5,
    "difficulty": "easy",
    "category": "starbucks",
    "created_at": "2025-01-01T12:00:00Z"
  },
  "message": "Starbucks recipe generated successfully"
}
```

---

### Get Popular Starbucks Recipes
Retrieves trending and popular custom Starbucks recipes.

```http
GET /api/starbucks/popular
```

**Query Parameters:**
- `drink_type` (optional): Filter by drink type
- `limit` (optional): Number of recipes to return (default: 20)

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "popular_recipes": [
      {
        "id": "starbucks-recipe-1",
        "drink_name": "TikTok Pink Drink Remix",
        "description": "Viral pink drink with tropical twist",
        "base_drink": "Pink Drink",
        "popularity_score": 9.2,
        "user_ratings": 4.8,
        "order_count": 1547,
        "trending": true
      }
      // ... more recipes
    ],
    "trending_modifications": [
      "Brown sugar syrup",
      "Oat milk substitute",
      "Extra shot espresso",
      "Vanilla cold foam"
    ]
  },
  "message": "Popular recipes retrieved successfully"
}
```

## Subscription & Payment Endpoints

### Get Subscription Status
Retrieves current subscription information for user.

```http
GET /api/subscription/status/{user_id}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "subscription": {
      "id": "sub_stripe_id",
      "status": "active", // "active", "trialing", "canceled", "past_due"
      "current_period_start": "2025-01-01T12:00:00Z",
      "current_period_end": "2025-02-01T12:00:00Z",
      "trial_end": null, // null if not in trial
      "cancel_at_period_end": false,
      "plan": {
        "id": "premium_monthly",
        "name": "Premium Monthly",
        "price": 9.99,
        "currency": "usd",
        "interval": "month"
      }
    },
    "usage": {
      "recipes_generated": 45,
      "weekly_plans_generated": 6,
      "recipes_saved": 23,
      "monthly_limit": 100
    },
    "features": {
      "unlimited_recipes": true,
      "weekly_meal_plans": true,
      "walmart_integration": true,
      "priority_support": true
    }
  },
  "message": "Subscription status retrieved successfully"
}
```

---

### Create Subscription
Upgrades user from trial to paid subscription.

```http
POST /api/subscription/create
Content-Type: application/json

{
  "user_id": "uuid-string",
  "payment_method_id": "pm_stripe_payment_method_id",
  "plan_id": "premium_monthly" // "premium_monthly", "premium_yearly"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "subscription": {
      "id": "sub_stripe_id",
      "status": "active",
      "current_period_start": "2025-01-01T12:00:00Z",
      "current_period_end": "2025-02-01T12:00:00Z",
      "plan": {
        "id": "premium_monthly",
        "price": 9.99,
        "currency": "usd"
      }
    },
    "invoice": {
      "id": "in_stripe_invoice_id",
      "amount_paid": 999,
      "currency": "usd",
      "status": "paid"
    }
  },
  "message": "Subscription created successfully"
}
```

**Error Responses:**
- `400` - Invalid payment method
- `402` - Payment required/failed
- `409` - User already has active subscription

---

### Cancel Subscription
Cancels user's subscription at the end of current billing period.

```http
POST /api/subscription/cancel
Content-Type: application/json

{
  "user_id": "uuid-string",
  "cancel_immediately": false, // true to cancel immediately
  "cancellation_reason": "Too expensive" // optional feedback
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "subscription": {
      "id": "sub_stripe_id",
      "status": "active",
      "cancel_at_period_end": true,
      "canceled_at": "2025-01-01T12:00:00Z",
      "current_period_end": "2025-02-01T12:00:00Z"
    }
  },
  "message": "Subscription will be canceled at the end of the current period"
}
```

## Error Handling

### Standard Error Codes

| HTTP Code | Error Type | Description |
|-----------|------------|-------------|
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Access denied |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource already exists |
| 422 | Validation Error | Request validation failed |
| 429 | Rate Limited | Too many requests |
| 500 | Internal Error | Server error |
| 502 | Bad Gateway | External service error |
| 503 | Service Unavailable | Service temporarily down |

### Error Response Examples

#### Validation Error (422)
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": {
      "field_errors": {
        "email": ["Email format is invalid"],
        "servings": ["Must be between 1 and 12"]
      }
    }
  }
}
```

#### Rate Limited (429)
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMITED",
    "message": "Too many requests. Please try again later.",
    "details": {
      "retry_after": 60,
      "limit": 100,
      "remaining": 0,
      "reset_at": "2025-01-01T13:00:00Z"
    }
  }
}
```

#### Service Unavailable (503)
```json
{
  "success": false,
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "OpenAI service is temporarily unavailable",
    "details": {
      "service": "openai",
      "fallback_available": true,
      "estimated_recovery": "2025-01-01T12:30:00Z"
    }
  }
}
```

## Rate Limiting

### Rate Limit Headers
All responses include rate limiting information:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Reset: 1640995200
X-RateLimit-Window: 3600
```

### Rate Limits by Endpoint

| Endpoint Category | Limit | Window |
|-------------------|-------|--------|
| Authentication | 10 requests | 15 minutes |
| Recipe Generation | 20 requests | 1 hour |
| Recipe Retrieval | 100 requests | 1 hour |
| Weekly Plans | 5 requests | 1 hour |
| Starbucks Generation | 15 requests | 1 hour |
| General API | 1000 requests | 1 hour |

## Webhook Endpoints

### Stripe Webhooks
Handles Stripe payment events for subscription management.

```http
POST /api/webhooks/stripe
Content-Type: application/json
Stripe-Signature: signature_header

{
  "id": "evt_stripe_event_id",
  "object": "event",
  "type": "invoice.payment_succeeded",
  "data": {
    "object": {
      "id": "in_stripe_invoice_id",
      "customer": "cus_stripe_customer_id",
      "amount_paid": 999,
      "currency": "usd"
    }
  }
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Webhook processed successfully"
}
```

## API Versioning

The API uses URL path versioning for major changes:
- `v1` (default): `/api/endpoint`
- `v2`: `/api/v2/endpoint`

### Version 2 Endpoints

#### Walmart Integration V2
Enhanced Walmart integration with better product matching.

```http
POST /api/v2/walmart/weekly-cart-options?recipe_id={recipe_id}
```

Response includes enhanced product data and better matching algorithms.

## SDK Examples

### JavaScript/React
```javascript
// API client setup
class AIChefAPI {
  constructor(baseURL, token = null) {
    this.baseURL = baseURL;
    this.token = token;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}/api${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...(this.token && { Authorization: `Bearer ${this.token}` }),
      ...options.headers
    };

    const response = await fetch(url, {
      ...options,
      headers
    });

    if (!response.ok) {
      const error = await response.json();
      throw new APIError(error.error.message, response.status, error);
    }

    return response.json();
  }

  // Authentication
  async login(email, password) {
    const response = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
    this.token = response.data.token;
    return response.data;
  }

  // Recipe generation
  async generateRecipe(recipeData) {
    return this.request('/recipes/generate', {
      method: 'POST',
      body: JSON.stringify(recipeData)
    });
  }

  // Recipe history
  async getRecipeHistory(userId, page = 1) {
    return this.request(`/recipes/history/${userId}?page=${page}`);
  }
}

// Usage
const api = new AIChefAPI(process.env.REACT_APP_BACKEND_URL);

// Login and generate recipe
try {
  const { user, token } = await api.login('user@example.com', 'password');
  
  const recipe = await api.generateRecipe({
    user_id: user.id,
    cuisine_type: 'italian',
    difficulty: 'easy',
    servings: 4
  });
  
  console.log('Generated recipe:', recipe.data);
} catch (error) {
  console.error('API Error:', error.message);
}
```

### Python
```python
import httpx
import json
from typing import Optional, Dict, Any

class AIChefAPI:
    def __init__(self, base_url: str, token: Optional[str] = None):
        self.base_url = base_url
        self.token = token
        self.client = httpx.AsyncClient()

    async def request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict[Any, Any]:
        url = f"{self.base_url}/api{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        response = await self.client.request(
            method=method,
            url=url,
            headers=headers,
            json=data
        )

        if not response.is_success:
            error_data = response.json()
            raise APIError(error_data["error"]["message"], response.status_code)

        return response.json()

    async def login(self, email: str, password: str) -> Dict[Any, Any]:
        response = await self.request("/auth/login", "POST", {
            "email": email,
            "password": password
        })
        self.token = response["data"]["token"]
        return response["data"]

    async def generate_recipe(self, recipe_data: Dict[Any, Any]) -> Dict[Any, Any]:
        return await self.request("/recipes/generate", "POST", recipe_data)

# Usage
api = AIChefAPI("http://localhost:8001")

async def example():
    user_data = await api.login("user@example.com", "password")
    
    recipe = await api.generate_recipe({
        "user_id": user_data["user"]["id"],
        "cuisine_type": "italian",
        "difficulty": "easy",
        "servings": 4
    })
    
    print("Generated recipe:", recipe["data"]["name"])
```

## Testing API Endpoints

### Using curl
```bash
# Health check
curl -X GET "http://localhost:8001/api/health"

# Login
curl -X POST "http://localhost:8001/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@test.com","password":"password123"}'

# Generate recipe (with auth token)
curl -X POST "http://localhost:8001/api/recipes/generate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "user_id": "user-id",
    "cuisine_type": "italian",
    "difficulty": "easy",
    "servings": 4
  }'

# Get recipe history
curl -X GET "http://localhost:8001/api/recipes/history/USER_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Using Postman
Import the following collection:

```json
{
  "info": {
    "name": "AI Chef API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "variable": [
    {
      "key": "baseUrl",
      "value": "http://localhost:8001"
    },
    {
      "key": "token",
      "value": ""
    }
  ],
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "header": [],
        "url": "{{baseUrl}}/api/health"
      }
    },
    {
      "name": "Login",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"email\": \"demo@test.com\",\n  \"password\": \"password123\"\n}"
        },
        "url": "{{baseUrl}}/api/auth/login"
      }
    }
  ]
}
```

## Changelog

### Version 2.2.1 (Current)
- Enhanced weekly meal plan generation
- Improved Walmart product matching
- Added nutritional information
- Better error handling for external APIs

### Version 2.1.0
- Added Starbucks recipe generation
- Implemented subscription management
- Enhanced recipe filtering and search

### Version 2.0.0
- Major API restructure
- Added weekly meal planning
- Walmart integration V2
- Improved authentication system

---

**Last Updated**: January 2025
**API Version**: 2.2.1