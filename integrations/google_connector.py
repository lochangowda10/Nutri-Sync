import os
import requests
import datetime

class GoogleAPIService:
    def __init__(self):
        self.places_api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        # In a full implementation, we'd initialize the Google Calendar OAuth client here.
        # For this prototype/hackathon scope, we will simulate the calendar events if no key is found.

    def fetch_calendar_fatigue_context(self) -> tuple[str, str]:
        """
        Connects to Google Calendar API to read today's events.
        Determines mental fatigue based on total hours of events.
        """
        # Hackathon Prototype Logic: Simulate calendar retrieval
        current_hour = datetime.datetime.now().hour
        
        # Simple heuristic for prototype: Late in the day = high fatigue
        if current_hour >= 17:
            return "high", f"It's {current_hour}:00. After a full day of work/lectures, your mental bandwidth is low."
        elif 12 <= current_hour < 17:
            return "medium", f"It's {current_hour}:00. You've completed half your day; focus is starting to dip."
        else:
            return "low", f"It's {current_hour}:00. You're in your peak productivity window with fresh energy."

    def find_nearby_healthy_food(self, lat: float, lng: float, radius: int = 500) -> list:
        """
        Uses Google Maps Places API to find healthy food vendors within a radius.
        """
        if not self.places_api_key:
            # Fallback mock data if API key is not set (useful for local testing)
            print("⚠️ GOOGLE_PLACES_API_KEY not set. Using simulated Places data.")
            return [
                {"name": "Green Bowl Co.", "vicinity": "123 Health St."},
                {"name": "Smoothie Haven", "vicinity": "456 Wellness Ave."}
            ]

        # Actual API call (Text Search or Nearby Search for healthy food)
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {
            "location": f"{lat},{lng}",
            "radius": radius,
            "keyword": "healthy food OR salad OR vegan",
            "type": "restaurant",
            "key": self.places_api_key
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            results = response.json().get("results", [])
            # Return top 3 options
            return results[:3]
        except Exception as e:
            print(f"❌ Error fetching places: {e}")
            return []
