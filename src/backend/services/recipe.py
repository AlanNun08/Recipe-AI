"""
Recipe generation service
"""
import os
import json
import logging
import random
from typing import List, Dict, Any, Optional
from datetime import datetime
from openai import OpenAI
from ..models.recipe import RecipeGeneration, Recipe, WeeklyRecipeGeneration, WeeklyRecipe
from .database import db_service

logger = logging.getLogger(__name__)

class RecipeService:
    """Recipe generation and management service"""
    
    def __init__(self):
        self.openai_client = None
        api_key = os.environ.get('OPENAI_API_KEY')
        
        if api_key and not any(placeholder in api_key for placeholder in ['your-', 'placeholder', 'here']):
            self.openai_client = OpenAI(api_key=api_key)
            self.ai_enabled = True
        else:
            self.ai_enabled = False
            logger.info("OpenAI not configured, using fallback recipes")
    
    async def generate_recipe(self, request: RecipeGeneration) -> Recipe:
        """Generate a single recipe"""
        if self.ai_enabled:
            return await self._generate_ai_recipe(request)
        else:
            return await self._generate_fallback_recipe(request)
    
    async def generate_weekly_recipes(self, request: WeeklyRecipeGeneration) -> WeeklyRecipe:
        """Generate weekly meal plan"""
        recipes = []
        week_id = datetime.now().strftime("%Y-W%W")
        
        # Generate 7 different recipes for the week
        cuisines = ["Italian", "Mexican", "Asian", "American", "Mediterranean", "Indian", "French"]
        difficulties = ["easy", "medium", "hard"]
        
        for i, cuisine in enumerate(cuisines):
            recipe_request = RecipeGeneration(
                user_id=request.user_id,
                cuisine_type=cuisine,
                difficulty=random.choice(difficulties),
                servings=4,
                dietary_preferences=request.dietary_preferences or []
            )
            
            recipe = await self.generate_recipe(recipe_request)
            recipes.append(recipe)
        
        # Create weekly recipe plan
        weekly_recipe = WeeklyRecipe(
            user_id=request.user_id,
            week_id=week_id,
            recipes=recipes
        )
        
        # Save to database
        await db_service.weekly_recipes_collection.insert_one(weekly_recipe.dict())
        
        return weekly_recipe
    
    async def _generate_ai_recipe(self, request: RecipeGeneration) -> Recipe:
        """Generate recipe using OpenAI"""
        try:
            dietary_text = ", ".join(request.dietary_preferences) if request.dietary_preferences else "no specific dietary restrictions"
            ingredients_text = ", ".join(request.ingredients) if request.ingredients else "any suitable ingredients"
            
            prompt = f"""
            Create a detailed {request.cuisine_type} recipe with the following requirements:
            - Difficulty: {request.difficulty}
            - Servings: {request.servings}
            - Dietary preferences: {dietary_text}
            - Include these ingredients if possible: {ingredients_text}
            
            Return a JSON object with:
            - name: recipe name
            - description: brief description
            - ingredients: array of ingredients with measurements
            - instructions: array of step-by-step instructions
            - prep_time: preparation time
            - cook_time: cooking time
            - calories: estimated calories per serving
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            
            recipe_data = json.loads(response.choices[0].message.content)
            
            # Create recipe object
            recipe = Recipe(
                user_id=request.user_id,
                name=recipe_data["name"],
                description=recipe_data["description"],
                ingredients=recipe_data["ingredients"],
                instructions=recipe_data["instructions"],
                prep_time=recipe_data["prep_time"],
                cook_time=recipe_data["cook_time"],
                servings=request.servings,
                difficulty=request.difficulty,
                cuisine_type=request.cuisine_type,
                dietary_preferences=request.dietary_preferences,
                calories=recipe_data.get("calories")
            )
            
            # Save to database
            await db_service.recipes_collection.insert_one(recipe.dict())
            
            return recipe
            
        except Exception as e:
            logger.error(f"AI recipe generation failed: {e}")
            return await self._generate_fallback_recipe(request)
    
    async def _generate_fallback_recipe(self, request: RecipeGeneration) -> Recipe:
        """Generate fallback recipe when AI is not available"""
        fallback_recipes = {
            "italian": {
                "name": "Classic Spaghetti Carbonara",
                "description": "Traditional Italian pasta dish with eggs, cheese, and pancetta",
                "ingredients": [
                    "400g spaghetti",
                    "200g pancetta or bacon, diced",
                    "4 large eggs",
                    "100g Pecorino Romano cheese, grated",
                    "2 cloves garlic, minced",
                    "Black pepper to taste",
                    "Salt for pasta water"
                ],
                "instructions": [
                    "Bring a large pot of salted water to boil and cook spaghetti until al dente",
                    "While pasta cooks, fry pancetta in a large pan until crispy",
                    "In a bowl, whisk eggs with grated cheese and black pepper",
                    "Drain pasta, reserving 1 cup pasta water",
                    "Add hot pasta to pan with pancetta",
                    "Remove from heat and quickly mix in egg mixture, adding pasta water as needed",
                    "Serve immediately with extra cheese and pepper"
                ],
                "prep_time": "10 minutes",
                "cook_time": "15 minutes",
                "calories": 650
            },
            "mexican": {
                "name": "Chicken Tacos with Lime Crema",
                "description": "Flavorful chicken tacos with fresh lime crema and vegetables",
                "ingredients": [
                    "500g chicken breast, sliced",
                    "8 corn tortillas",
                    "1 red onion, sliced",
                    "2 bell peppers, sliced",
                    "1/2 cup sour cream",
                    "2 limes, juiced",
                    "1 tsp cumin",
                    "1 tsp chili powder",
                    "Salt and pepper to taste",
                    "Fresh cilantro for garnish"
                ],
                "instructions": [
                    "Season chicken with cumin, chili powder, salt, and pepper",
                    "Cook chicken in a hot pan until golden brown and cooked through",
                    "Sauté onions and peppers until softened",
                    "Mix sour cream with lime juice to make crema",
                    "Warm tortillas in a dry pan",
                    "Assemble tacos with chicken, vegetables, and lime crema",
                    "Garnish with fresh cilantro and serve"
                ],
                "prep_time": "15 minutes",
                "cook_time": "20 minutes",
                "calories": 520
            }
        }
        
        # Get recipe template based on cuisine
        cuisine_key = request.cuisine_type.lower()
        if cuisine_key not in fallback_recipes:
            cuisine_key = "italian"  # Default fallback
        
        template = fallback_recipes[cuisine_key]
        
        # Create recipe object
        recipe = Recipe(
            user_id=request.user_id,
            name=template["name"],
            description=template["description"],
            ingredients=template["ingredients"],
            instructions=template["instructions"],
            prep_time=template["prep_time"],
            cook_time=template["cook_time"],
            servings=request.servings,
            difficulty=request.difficulty,
            cuisine_type=request.cuisine_type,
            dietary_preferences=request.dietary_preferences,
            calories=template["calories"]
        )
        
        # Save to database
        await db_service.recipes_collection.insert_one(recipe.dict())
        
        return recipe
    
    async def get_user_recipes(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's recipe history"""
        cursor = db_service.recipes_collection.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
        recipes = await cursor.to_list(length=limit)
        return recipes
    
    async def get_recipe_by_id(self, recipe_id: str) -> Optional[Dict[str, Any]]:
        """Get recipe by ID"""
        return await db_service.recipes_collection.find_one({"id": recipe_id})
    
    async def delete_recipe(self, recipe_id: str, user_id: str) -> bool:
        """Delete user's recipe"""
        result = await db_service.recipes_collection.delete_one({
            "id": recipe_id,
            "user_id": user_id
        })
        return result.deleted_count > 0

# Create service instance
recipe_service = RecipeService()