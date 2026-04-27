"""
NutriSync AI Brain — The core decision engine.
Handles meal analysis, contextual recommendations, substitutes, 
weekly behavior reports, and streak calculations.
"""

import json
import os
import random
from datetime import datetime
from typing import Any


class NutriBrain:
    """AI-powered food decision engine for NutriSync."""

    def __init__(self) -> None:
        data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        try:
            with open(os.path.join(data_dir, "indian_foods.json"), "r", encoding="utf-8") as f:
                data = json.load(f)
            self.foods: list[dict] = data.get("foods", [])
            self.substitutes: dict[str, list[str]] = data.get("substitutes", {})
            self.eating_reasons: list[dict] = data.get("eating_reasons", [])
            self.streaks_def: list[dict] = data.get("streaks", [])
        except Exception:
            self.foods = []
            self.substitutes = {}
            self.eating_reasons = []
            self.streaks_def = []

        self.food_lookup: dict[str, dict] = {f["name"]: f for f in self.foods}

    # ------------------------------------------------------------------
    # Feature 1 & 2: Analyze Meal with Context
    # ------------------------------------------------------------------
    def analyze_meal(
        self,
        food_name: str,
        eating_reason: str,
        hour: int,
        today_calories: int,
        today_sugar: int,
        today_protein: int,
        meals_today: int,
        is_weekend: bool,
    ) -> dict[str, Any]:
        """Analyze a food choice in context and return AI insights."""

        food = self.food_lookup.get(food_name)
        if not food:
            food = self._fuzzy_find(food_name)
        if not food:
            return {
                "found": False,
                "message": f"I don't have nutritional data for '{food_name}' yet. Try selecting from the suggestions.",
            }

        insights: list[str] = []
        severity: str = "good"  # good | warning | alert
        score: int = food["health_score"]

        # --- Context: Time of Day ---
        if hour >= 22 and food["calories"] > 300:
            insights.append(
                f"⏰ It's {hour}:00 — heavy meals this late slow digestion and disrupt sleep."
            )
            severity = "alert"
            score = max(1, score - 2)
        elif hour >= 22:
            insights.append(
                f"🌙 Late-night eating detected. Even lighter options are best consumed before 9 PM."
            )
            severity = "warning"

        # --- Context: Sugar Budget ---
        sugar_budget = 40  # grams per day
        if today_sugar + food["sugar"] > sugar_budget:
            overshoot = today_sugar + food["sugar"] - sugar_budget
            insights.append(
                f"🍬 This adds {food['sugar']}g sugar. You'll exceed your daily limit by {overshoot}g."
            )
            severity = "alert" if overshoot > 15 else "warning"
            score = max(1, score - 2)

        # --- Context: Calorie Budget ---
        calorie_budget = 2000
        if today_calories + food["calories"] > calorie_budget:
            insights.append(
                f"🔥 You've already had {today_calories} cal today. Adding {food['calories']} cal puts you over budget."
            )
            if severity != "alert":
                severity = "warning"

        # --- Context: Protein Balance ---
        protein_goal = 50
        if today_protein < protein_goal * 0.5 and hour >= 18 and food["protein"] < 10:
            insights.append(
                f"💪 You're low on protein today ({today_protein}g / {protein_goal}g). Consider a protein-rich option."
            )

        # --- Context: Eating Reason ---
        reason_data = next(
            (r for r in self.eating_reasons if r["id"] == eating_reason), None
        )
        if reason_data and reason_data["risk"] == "high":
            insights.append(
                f"🧠 You're eating because of: {reason_data['label']}. This is a known trigger for unhealthy patterns."
            )
            if severity != "alert":
                severity = "warning"

        # --- Context: Meal Frequency ---
        if meals_today >= 5:
            insights.append(
                f"📊 This is your {meals_today + 1}th meal/snack today. Consider spacing your meals better."
            )

        # --- Weekend Pattern ---
        if is_weekend and food["health_score"] <= 4 and meals_today >= 3:
            insights.append(
                "📅 Weekend overeating pattern detected. Enjoy, but stay mindful!"
            )

        # --- Positive Reinforcement ---
        if food["health_score"] >= 8:
            insights.append(
                f"✅ Great choice! {food['name']} is nutritious and well-balanced."
            )
            severity = "good"

        if not insights:
            insights.append("👍 Looks like a reasonable choice for this time of day.")

        return {
            "found": True,
            "food": food,
            "severity": severity,
            "health_score": score,
            "insights": insights,
        }

    # ------------------------------------------------------------------
    # Feature 3: Smart Substitutes
    # ------------------------------------------------------------------
    def get_substitutes(self, food_name: str) -> dict[str, Any]:
        """Return healthier alternatives for a given food."""
        subs = self.substitutes.get(food_name, [])
        sub_details = []
        for s in subs:
            detail = self.food_lookup.get(s)
            if detail:
                sub_details.append(detail)
        if not sub_details:
            # Generic healthy suggestions
            sub_details = [
                f for f in self.foods if f["health_score"] >= 8
            ][:3]
        return {
            "original": food_name,
            "alternatives": sub_details,
            "tip": self._get_substitute_tip(food_name),
        }

    # ------------------------------------------------------------------
    # Feature 4 & 7: Streak Calculation & Impact Metrics
    # ------------------------------------------------------------------
    def calculate_streaks(self, meal_history: list[dict]) -> dict[str, Any]:
        """Calculate habit streaks from meal history."""
        streaks: list[dict] = []
        for sdef in self.streaks_def:
            streak_val = self._compute_streak(sdef["id"], meal_history)
            streaks.append({**sdef, "current": streak_val["current"], "best": streak_val["best"]})
        return {"streaks": streaks}

    # ------------------------------------------------------------------
    # Feature 6: Weekly Behavior Report
    # ------------------------------------------------------------------
    def generate_weekly_report(self, meal_history: list[dict]) -> dict[str, Any]:
        """Generate AI behavior insights from a week of meal history."""
        if not meal_history:
            return {"patterns": [], "summary": "No meal data yet. Start logging to get your weekly AI report!"}

        patterns: list[str] = []
        total_meals = len(meal_history)

        # --- Breakfast Analysis ---
        breakfast_days = set()
        for m in meal_history:
            h = m.get("hour", 12)
            if h < 11:
                breakfast_days.add(m.get("date", ""))
        unique_days = len(set(m.get("date", "") for m in meal_history))
        if unique_days > 0:
            breakfast_ratio = len(breakfast_days) / max(unique_days, 1)
            skipped = unique_days - len(breakfast_days)
            if skipped > 0:
                patterns.append(f"🌅 Breakfast skipped {skipped} out of {unique_days} days")

        # --- Late Night Eating ---
        late_meals = [m for m in meal_history if m.get("hour", 0) >= 21]
        if late_meals:
            patterns.append(f"🌙 {len(late_meals)} late-night meals detected (after 9 PM)")

        # --- Sugar Patterns ---
        high_sugar_after_9 = [
            m for m in meal_history
            if m.get("hour", 0) >= 21 and m.get("sugar", 0) > 10
        ]
        if high_sugar_after_9:
            patterns.append(f"🍬 Sugar cravings mostly happen after 9 PM ({len(high_sugar_after_9)} instances)")

        # --- Protein Deficiency ---
        low_protein_days = 0
        days_data: dict[str, int] = {}
        for m in meal_history:
            d = m.get("date", "unknown")
            days_data[d] = days_data.get(d, 0) + m.get("protein", 0)
        for d, p in days_data.items():
            if p < 40:
                low_protein_days += 1
        if low_protein_days > 0:
            patterns.append(f"💪 Low protein intake on {low_protein_days} day(s)")

        # --- Stress/Emotional Eating ---
        stress_meals = [m for m in meal_history if m.get("reason") in ("stress", "emotional", "boredom")]
        if stress_meals:
            patterns.append(f"😰 {len(stress_meals)} meals linked to stress/emotional eating")

        # --- Weekend Overeating ---
        weekend_cals = [m.get("calories", 0) for m in meal_history if m.get("is_weekend")]
        weekday_cals = [m.get("calories", 0) for m in meal_history if not m.get("is_weekend")]
        if weekend_cals and weekday_cals:
            avg_w = sum(weekend_cals) / max(len(weekend_cals), 1)
            avg_d = sum(weekday_cals) / max(len(weekday_cals), 1)
            if avg_w > avg_d * 1.3:
                patterns.append(f"📅 Weekend calorie intake is {int((avg_w/avg_d - 1)*100)}% higher than weekdays")

        # --- Health Score Trend ---
        scores = [m.get("health_score", 5) for m in meal_history]
        avg_score = sum(scores) / max(len(scores), 1)

        # --- Impact Metrics ---
        healthy_choices = len([m for m in meal_history if m.get("health_score", 5) >= 7])
        unhealthy_choices = len([m for m in meal_history if m.get("health_score", 5) <= 4])

        if not patterns:
            patterns.append("🎉 Great eating patterns this week! Keep it up!")

        return {
            "patterns": patterns,
            "metrics": {
                "total_meals": total_meals,
                "avg_health_score": round(avg_score, 1),
                "healthy_choices": healthy_choices,
                "unhealthy_choices": unhealthy_choices,
                "healthy_pct": round(healthy_choices / max(total_meals, 1) * 100),
            },
            "summary": f"Analyzed {total_meals} meals across {unique_days} days.",
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _fuzzy_find(self, query: str) -> dict | None:
        """Simple fuzzy match against food names."""
        q = query.lower().strip()
        for f in self.foods:
            if q in f["name"].lower():
                return f
        return None

    def _get_substitute_tip(self, food_name: str) -> str:
        tips = {
            "Pizza": "Choose thin crust, add veggies, reduce cheese, or try a protein wrap.",
            "Burger": "Swap the bun for lettuce wraps or choose grilled over fried patties.",
            "Maggi": "Poha takes the same time to cook and has half the sodium.",
            "Samosa": "Baked samosas retain the taste with 60% less oil.",
            "Ice Cream": "Frozen yogurt or fruit with dark chocolate satisfy the craving with less sugar.",
        }
        for key, tip in tips.items():
            if key.lower() in food_name.lower():
                return tip
        return "Small changes matter! Swap portions, choose grilled over fried, or add a side salad."

    def _compute_streak(self, streak_id: str, history: list[dict]) -> dict:
        """Compute current and best streak for a given streak type."""
        if not history:
            return {"current": 0, "best": 0}

        days_met: set[str] = set()
        for m in history:
            d = m.get("date", "")
            if streak_id == "no_sugary_drinks":
                if m.get("category") == "beverage" and m.get("sugar", 0) > 15:
                    days_met.discard(d)
                elif d not in days_met:
                    days_met.add(d)
            elif streak_id == "breakfast_done":
                if m.get("hour", 12) < 11:
                    days_met.add(d)
            elif streak_id == "protein_goal":
                pass  # tracked by daily aggregation
            elif streak_id == "no_latenight":
                if m.get("hour", 0) >= 21:
                    days_met.discard(d)
                elif d not in days_met:
                    days_met.add(d)

        current = min(len(days_met), 7)
        best = current
        return {"current": current, "best": max(best, current)}

    def search_foods(self, query: str) -> list[dict]:
        """Search foods by name for autocomplete."""
        q = query.lower().strip()
        if not q:
            return self.foods[:10]
        results = [f for f in self.foods if q in f["name"].lower()]
        return results[:10]

    def get_food_categories(self) -> list[str]:
        """Return unique food categories."""
        return list(set(f["category"] for f in self.foods))
