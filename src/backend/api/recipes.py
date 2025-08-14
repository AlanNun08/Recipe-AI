"""
Recipe API routes
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional
from ..models.recipe import RecipeGeneration, WeeklyRecipeGeneration
from ..services.recipe import recipe_service
from ..services.database import get_db_service
import logging

logger = logging.getLogger(__name__)
db_service = get_db_service()
router = APIRouter(prefix="/recipes", tags=["recipes"])

@router.post("/generate")
async def generate_recipe(request: RecipeGeneration):
    """Generate a single recipe"""
    try:
        # Check if user exists
        user = await db_service.users_collection.find_one({"id": request.user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # TODO: Check usage limits here
        
        recipe = await recipe_service.generate_recipe(request)
        return JSONResponse(status_code=200, content=recipe.dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Recipe generation error: {e}")
        raise HTTPException(status_code=500, detail="Recipe generation failed")

@router.post("/weekly/generate")
async def generate_weekly_recipes(request: WeeklyRecipeGeneration):
    """Generate weekly meal plan"""
    try:
        # Check if user exists
        user = await db_service.users_collection.find_one({"id": request.user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # TODO: Check usage limits here
        
        weekly_recipes = await recipe_service.generate_weekly_recipes(request)
        return JSONResponse(status_code=200, content=weekly_recipes.dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Weekly recipe generation error: {e}")
        raise HTTPException(status_code=500, detail="Weekly recipe generation failed")

@router.get("/history/{user_id}")
async def get_recipe_history(user_id: str, limit: Optional[int] = Query(50, ge=1, le=100)):
    """Get user's recipe history"""
    try:
        recipes = await recipe_service.get_user_recipes(user_id, limit)
        starbucks_cursor = db_service.starbucks_recipes_collection.find({"user_id": user_id}).sort("created_at", -1)
        starbucks_recipes = await starbucks_cursor.to_list(length=limit)
        
        # Combine and sort by created_at
        all_recipes = recipes + starbucks_recipes
        all_recipes.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return JSONResponse(status_code=200, content={
            "recipes": all_recipes,
            "total_count": len(all_recipes)
        })
    except Exception as e:
        logger.error(f"Recipe history error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recipe history")

@router.get("/{recipe_id}/detail")
async def get_recipe_detail(recipe_id: str):
    """Get recipe details"""
    try:
        # Try different collections
        recipe = await recipe_service.get_recipe_by_id(recipe_id)
        
        if not recipe:
            # Try starbucks collection
            recipe = await db_service.starbucks_recipes_collection.find_one({"id": recipe_id})
        
        if not recipe:
            # Try curated starbucks collection
            recipe = await db_service.curated_starbucks_recipes_collection.find_one({"id": recipe_id})
        
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        return JSONResponse(status_code=200, content=recipe)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Recipe detail error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recipe details")

@router.delete("/{recipe_id}")
async def delete_recipe(recipe_id: str, user_id: str = Query(...)):
    """Delete user's recipe"""
    try:
        success = await recipe_service.delete_recipe(recipe_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        return JSONResponse(status_code=200, content={
            "success": True,
            "message": "Recipe deleted successfully"
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Recipe deletion error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete recipe")