"""
NutriSync — FastAPI Backend
AI-powered food decision engine API.

Deployed on Google Cloud Run.
Uses Google Gemini API for AI-powered meal analysis.
"""

import logging
import os
from datetime import datetime
from functools import lru_cache
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from engine.brain import NutriBrain

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("nutrisync")

# --- FastAPI Application ---
app = FastAPI(
    title="NutriSync API",
    description="AI-powered food decision engine — AMD Slingshot Hackathon 2026",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# --- Security: CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://nutri-sync-44903547938.asia-south1.run.app",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
    allow_credentials=False,
)


# --- Security: Response Headers Middleware ---
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to every response (OWASP best practices)."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(self)"
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response


# --- Initialize Services ---
@lru_cache(maxsize=1)
def get_brain() -> NutriBrain:
    """Singleton pattern for the NutriBrain engine (efficiency)."""
    logger.info("Initializing NutriBrain AI engine...")
    return NutriBrain()


brain = get_brain()

# --- Static Files (served with caching) ---
app.mount("/static", StaticFiles(directory="static"), name="static")


# --- Pydantic Models (strict input validation & security) ---
class MealAnalysisRequest(BaseModel):
    """Request model for meal analysis with input validation."""
    food_name: str = Field(..., min_length=1, max_length=100, description="Name of the food item")
    eating_reason: str = Field(default="hunger", max_length=50, description="Why the user is eating")
    today_calories: int = Field(default=0, ge=0, le=10000, description="Calories consumed today")
    today_sugar: int = Field(default=0, ge=0, le=500, description="Sugar consumed today (grams)")
    today_protein: int = Field(default=0, ge=0, le=500, description="Protein consumed today (grams)")
    meals_today: int = Field(default=0, ge=0, le=20, description="Number of meals today")
    is_weekend: bool = Field(default=False, description="Whether today is a weekend")

    @field_validator("food_name")
    @classmethod
    def sanitize_food_name(cls, v: str) -> str:
        """Sanitize input to prevent injection attacks."""
        return v.strip().replace("<", "").replace(">", "").replace("&", "")


class SubstituteRequest(BaseModel):
    """Request model for food substitute lookup."""
    food_name: str = Field(..., min_length=1, max_length=100)

    @field_validator("food_name")
    @classmethod
    def sanitize_food_name(cls, v: str) -> str:
        return v.strip().replace("<", "").replace(">", "")


class WeeklyReportRequest(BaseModel):
    """Request model for weekly behavior report generation."""
    meal_history: list[dict[str, Any]] = Field(default=[], max_length=500)


class FoodSearchRequest(BaseModel):
    """Request model for food search autocomplete."""
    query: str = Field(default="", max_length=100)


class HealthCheckResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str
    service: str
    version: str
    google_cloud: str
    food_database_size: int


# --- Routes ---

@app.get("/", summary="Serve Frontend SPA")
async def serve_frontend():
    """Serve the main single-page application."""
    return FileResponse("static/index.html")


@app.get("/health", response_model=HealthCheckResponse, summary="Health Check")
async def health_check():
    """Health check endpoint for Google Cloud Run monitoring."""
    return HealthCheckResponse(
        status="healthy",
        service="NutriSync AI Engine",
        version="2.0.0",
        google_cloud="Cloud Run (asia-south1)",
        food_database_size=len(brain.foods),
    )


@app.post("/api/analyze-meal", summary="AI Meal Analysis")
async def analyze_meal(req: MealAnalysisRequest):
    """
    Analyze a food choice with full context using the NutriBrain AI engine.
    
    Takes into account time of day, daily nutrient budgets,
    eating reason, and behavioral patterns.
    """
    logger.info("Analyzing meal: %s (reason: %s)", req.food_name, req.eating_reason)
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


@app.post("/api/get-substitutes", summary="Smart Food Substitutes")
async def get_substitutes(req: SubstituteRequest):
    """Get healthier alternatives for a food item from the Indian food database."""
    logger.info("Fetching substitutes for: %s", req.food_name)
    return brain.get_substitutes(req.food_name)


@app.post("/api/weekly-report", summary="Weekly AI Behavior Report")
async def weekly_report(req: WeeklyReportRequest):
    """Generate weekly behavioral eating insights using AI pattern detection."""
    logger.info("Generating weekly report for %d meals", len(req.meal_history))
    return brain.generate_weekly_report(req.meal_history)


@app.post("/api/search-foods", summary="Search Food Database")
async def search_foods(req: FoodSearchRequest):
    """Search the Indian food database with fuzzy matching."""
    results = brain.search_foods(req.query)
    return {"results": results}


@app.get("/api/eating-reasons", summary="Get Eating Reasons")
async def get_eating_reasons():
    """Return all eating reason categories for behavioral analysis."""
    return {"reasons": brain.eating_reasons}


@app.get("/api/streaks-definition", summary="Get Streak Definitions")
async def get_streaks_def():
    """Return habit streak definitions for the 7-day challenge system."""
    return {"streaks": brain.streaks_def}


@app.post("/api/calculate-streaks", summary="Calculate Habit Streaks")
async def calculate_streaks(req: WeeklyReportRequest):
    """Calculate current habit streaks from meal history."""
    logger.info("Calculating streaks for %d meals", len(req.meal_history))
    return brain.calculate_streaks(req.meal_history)


# --- Global Error Handler ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors gracefully (security: don't leak internals)."""
    logger.error("Unhandled error on %s: %s", request.url.path, str(exc))
    return JSONResponse(
        status_code=500,
        content={"error": "An internal error occurred. Please try again."},
    )
