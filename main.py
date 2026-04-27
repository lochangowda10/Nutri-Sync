from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from engine.brain import NutriBrain
from integrations.google_connector import GoogleAPIService

# Load environment variables
load_dotenv()

# Initialize FastAPI App
app = FastAPI(
    title="NutriSync API",
    description="Contextual food assistant backend for AMD Slingshot Hackathon",
    version="1.0.0"
)

# Initialize Services
google_service = GoogleAPIService()
brain = NutriBrain()

# Serve static files for the frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

# Pydantic Models for strict typing and API validation
class LocationRequest(BaseModel):
    lat: float
    lng: float

class RecommendationResponse(BaseModel):
    fatigue_level: str
    decision: str

@app.get("/")
async def serve_frontend():
    """Serves the main HTML page."""
    return FileResponse("static/index.html")

@app.post("/api/evaluate", response_model=RecommendationResponse)
async def evaluate_context(request: LocationRequest):
    """
    Evaluates the user's context based on location and calendar fatigue.
    Returns a dietary recommendation.
    """
    try:
        # 1. Fetch Context
        fatigue_level = google_service.fetch_calendar_fatigue_context()
        
        # 2. Scan for options
        nearby_options = google_service.find_nearby_healthy_food(request.lat, request.lng)
        
        # 3. Make Decision
        decision = brain.evaluate(fatigue_level, nearby_options)
        
        return RecommendationResponse(
            fatigue_level=fatigue_level,
            decision=decision
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
