"""
NutriSync — FastAPI Backend
AI-powered food decision engine API.
"""

from datetime import datetime
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from engine.brain import NutriBrain

app = FastAPI(
    title="NutriSync API",
    description="AI-powered food decision engine for AMD Slingshot Hackathon",
    version="2.0.0",
)

brain = NutriBrain()

# --- Static files ---
app.mount("/static", StaticFiles(directory="static"), name="static")


# --- Pydantic Models ---
class MealAnalysisRequest(BaseModel):
    food_name: str
    eating_reason: str = "hunger"
    today_calories: int = 0
    today_sugar: int = 0
    today_protein: int = 0
    meals_today: int = 0
    is_weekend: bool = False


class SubstituteRequest(BaseModel):
    food_name: str


class WeeklyReportRequest(BaseModel):
    meal_history: list[dict] = []


class FoodSearchRequest(BaseModel):
    query: str = ""


# --- Routes ---
@app.get("/")
async def serve_frontend():
    """Serve the main SPA."""
    return FileResponse("static/index.html")


@app.post("/api/analyze-meal")
async def analyze_meal(req: MealAnalysisRequest):
    """Analyze a food choice with full context."""
    now = datetime.now()
    result = brain.analyze_meal(
        food_name=req.food_name,
        eating_reason=req.eating_reason,
        hour=now.hour,
        today_calories=req.today_calories,
        today_sugar=req.today_sugar,
        today_protein=req.today_protein,
        meals_today=req.meals_today,
        is_weekend=req.is_weekend,
    )
    return result


@app.post("/api/get-substitutes")
async def get_substitutes(req: SubstituteRequest):
    """Get healthier alternatives for a food item."""
    return brain.get_substitutes(req.food_name)


@app.post("/api/weekly-report")
async def weekly_report(req: WeeklyReportRequest):
    """Generate weekly behavior insights."""
    return brain.generate_weekly_report(req.meal_history)


@app.post("/api/search-foods")
async def search_foods(req: FoodSearchRequest):
    """Search Indian food database."""
    results = brain.search_foods(req.query)
    return {"results": results}


@app.get("/api/eating-reasons")
async def get_eating_reasons():
    """Return all eating reason options."""
    return {"reasons": brain.eating_reasons}


@app.get("/api/streaks-definition")
async def get_streaks_def():
    """Return streak definitions."""
    return {"streaks": brain.streaks_def}


@app.post("/api/calculate-streaks")
async def calculate_streaks(req: WeeklyReportRequest):
    """Calculate habit streaks from history."""
    return brain.calculate_streaks(req.meal_history)
