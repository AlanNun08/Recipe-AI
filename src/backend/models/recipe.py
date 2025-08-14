"""
Recipe data models
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

class RecipeGeneration(BaseModel):
    user_id: str
    cuisine_type: str
    difficulty: str
    servings: int
    dietary_preferences: Optional[List[str]] = []
    ingredients: Optional[List[str]] = []

class Recipe(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    description: str
    ingredients: List[str]
    instructions: List[str]
    prep_time: str
    cook_time: str
    servings: int
    difficulty: str
    cuisine_type: str
    dietary_preferences: Optional[List[str]] = []
    calories: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class WeeklyRecipeGeneration(BaseModel):
    user_id: str
    dietary_preferences: Optional[List[str]] = []
    cuisine_preferences: Optional[List[str]] = []

class WeeklyRecipe(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    week_id: str  # e.g., "2025-W32"
    recipes: List[Recipe]
    created_at: datetime = Field(default_factory=datetime.utcnow)

class StarbucksRecipe(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    description: str
    ingredients: List[str]
    instructions: List[str]
    category: str = "starbucks"
    created_at: datetime = Field(default_factory=datetime.utcnow)