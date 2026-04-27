import json
import os
import random

class NutriBrain:
    def __init__(self):
        # Load the heuristic rules
        rules_path = os.path.join(os.path.dirname(__file__), "..", "data", "habit_rules.json")
        try:
            with open(rules_path, "r") as f:
                self.rules = json.load(f)
        except Exception as e:
            print(f"⚠️ Warning: Could not load habit rules. Using fallback. ({e})")
            self.rules = {
                "recovery_meals": ["Banana and Nuts"],
                "general_tips": ["Drink water!"],
                "distance_limit_meters": 500
            }

    def evaluate(self, fatigue_level: str, nearby_options: list) -> str:
        """
        The core decision engine.
        Weighs fatigue against distance and availability of healthy food.
        """
        if not nearby_options:
            meal = random.choice(self.rules.get("recovery_meals", ["A quick healthy snack"]))
            return f"🏡 It's best to stay in. Try making a quick 3-ingredient recovery meal: \n👉 {meal}"

        # Sort options by distance/prominence (assuming first is closest/best for now)
        best_option = nearby_options[0]
        vendor_name = best_option.get('name', 'a healthy spot')
        vendor_address = best_option.get('vicinity', 'nearby')

        if fatigue_level == "high":
            # High fatigue: Only suggest going out if there's an excellent, very close option.
            # In a real app, we'd check if the distance is < 100m. Here we assume we just suggest staying in.
            meal = random.choice(self.rules.get("recovery_meals", ["A quick healthy snack"]))
            return (f"🔋 Your calendar shows high mental fatigue today.\n"
                    f"🏡 Skip the line and oily takeout. Make a quick recovery meal:\n"
                    f"👉 {meal}\n"
                    f"💡 (Or if you really want to step out, {vendor_name} is at {vendor_address})")
        else:
            # Low/Medium fatigue: Encourage walking to get fresh air and a good meal.
            tip = random.choice(self.rules.get("general_tips", ["Stay healthy!"]))
            return (f"🚶 You have energy today! We suggest walking to a nearby healthy vendor.\n"
                    f"🎯 Top Pick: {vendor_name}\n"
                    f"📍 Location: {vendor_address}\n"
                    f"💡 Tip: {tip}")
