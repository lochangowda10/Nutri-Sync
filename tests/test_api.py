"""
NutriSync — Test Suite
Validates all core API endpoints and AI engine logic.
"""

import pytest
from fastapi.testclient import TestClient
from engine.brain import NutriBrain
from main import app


client = TestClient(app)
brain = NutriBrain()


# === Health Check ===
class TestHealthCheck:
    def test_health_endpoint(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["food_database_size"] > 0

    def test_frontend_serves(self):
        response = client.get("/")
        assert response.status_code == 200


# === Food Search ===
class TestFoodSearch:
    def test_search_idli(self):
        response = client.post("/api/search-foods", json={"query": "idli"})
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) > 0
        assert "Idli" in results[0]["name"]

    def test_search_empty(self):
        response = client.post("/api/search-foods", json={"query": ""})
        assert response.status_code == 200
        assert len(response.json()["results"]) > 0

    def test_search_no_results(self):
        response = client.post("/api/search-foods", json={"query": "xyznotfound"})
        assert response.status_code == 200
        assert len(response.json()["results"]) == 0


# === Meal Analysis ===
class TestMealAnalysis:
    def test_healthy_food(self):
        response = client.post("/api/analyze-meal", json={
            "food_name": "Idli (2 pcs)",
            "eating_reason": "hunger",
            "today_calories": 0,
            "today_sugar": 0,
            "today_protein": 0,
            "meals_today": 0,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["found"] is True
        assert data["health_score"] >= 8

    def test_unhealthy_food(self):
        response = client.post("/api/analyze-meal", json={
            "food_name": "Samosa (2 pcs)",
            "eating_reason": "craving",
            "today_calories": 1500,
            "today_sugar": 35,
            "today_protein": 10,
            "meals_today": 4,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["found"] is True
        assert data["severity"] in ("warning", "alert")

    def test_unknown_food(self):
        response = client.post("/api/analyze-meal", json={"food_name": "xyzfood"})
        assert response.status_code == 200
        assert response.json()["found"] is False

    def test_input_validation(self):
        response = client.post("/api/analyze-meal", json={
            "food_name": "",
        })
        assert response.status_code == 422  # Validation error


# === Substitutes ===
class TestSubstitutes:
    def test_samosa_substitutes(self):
        response = client.post("/api/get-substitutes", json={"food_name": "Samosa (2 pcs)"})
        assert response.status_code == 200
        data = response.json()
        assert len(data["alternatives"]) > 0

    def test_unknown_food_fallback(self):
        response = client.post("/api/get-substitutes", json={"food_name": "Unknown Food"})
        assert response.status_code == 200
        assert len(response.json()["alternatives"]) > 0


# === Weekly Report ===
class TestWeeklyReport:
    def test_empty_history(self):
        response = client.post("/api/weekly-report", json={"meal_history": []})
        assert response.status_code == 200

    def test_with_data(self):
        history = [
            {"food_name": "Idli", "calories": 130, "protein": 4, "sugar": 1, "hour": 8, "date": "2026-04-27", "health_score": 9, "reason": "hunger"},
            {"food_name": "Samosa", "calories": 350, "protein": 5, "sugar": 3, "hour": 22, "date": "2026-04-27", "health_score": 3, "reason": "craving"},
        ]
        response = client.post("/api/weekly-report", json={"meal_history": history})
        assert response.status_code == 200
        data = response.json()
        assert data["metrics"]["total_meals"] == 2


# === Eating Reasons ===
class TestEatingReasons:
    def test_returns_reasons(self):
        response = client.get("/api/eating-reasons")
        assert response.status_code == 200
        reasons = response.json()["reasons"]
        assert len(reasons) >= 10


# === Security Headers ===
class TestSecurity:
    def test_security_headers(self):
        response = client.get("/health")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"

    def test_xss_sanitization(self):
        response = client.post("/api/analyze-meal", json={
            "food_name": "<script>alert('xss')</script>",
        })
        assert response.status_code == 200
        assert response.json()["found"] is False


# === Brain Engine Unit Tests ===
class TestNutriBrain:
    def test_food_database_loaded(self):
        assert len(brain.foods) > 50

    def test_fuzzy_search(self):
        results = brain.search_foods("bir")
        names = [r["name"] for r in results]
        assert any("Biryani" in n for n in names)

    def test_categories(self):
        cats = brain.get_food_categories()
        assert "breakfast" in cats
        assert "lunch" in cats
        assert "snack" in cats
