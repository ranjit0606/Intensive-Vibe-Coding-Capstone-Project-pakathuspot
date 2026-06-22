import os
import logging
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from dotenv import load_dotenv, find_dotenv
from skills.itinerary_skill import generate_itinerary

# Load environment variables from the nearest .env file
load_dotenv(find_dotenv(), override=True)

logger = logging.getLogger(__name__)

# Pydantic models for structured Gemini outputs
class ActivityModel(BaseModel):
    time: str = Field(description="Formatted time of the activity (e.g. 09:00 AM)")
    place_name: str = Field(description="Name of the location visited")
    activity_description: str = Field(description="Enriching description of what the traveler will do")
    cost: float = Field(description="Estimated cost in INR")

class ItineraryDayModel(BaseModel):
    day_number: int = Field(description="The index number of the day (e.g. 1, 2)")
    theme: str = Field(description="Theme of the day (e.g. Exploring Waterfalls)")
    activities: List[ActivityModel] = Field(description="List of scheduled activities")

class ItineraryAgentResponse(BaseModel):
    itinerary: List[ItineraryDayModel] = Field(description="Structured day-by-day itinerary")

from google.adk import Agent

class ItineraryAgent:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        
        # Check for placeholder or empty keys
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            self.has_api_key = False
            logger.warning(
                f"ItineraryAgent: GEMINI_API_KEY is not configured. Key value: '{self.api_key}'. "
                f"Falling back to mock mode."
            )
        else:
            self.has_api_key = True
            masked_key = self.api_key[:5] + "..." if len(self.api_key) > 5 else "..."
            logger.info(f"ItineraryAgent: Gemini API Key successfully loaded (Masked: {masked_key})")
            
        # Lightweight ADK agent definition
        self.adk_agent = Agent(
            name="ItineraryAgent",
            description="Creates a day-by-day structured hourly travel itinerary based on places and weather.",
            tools=[generate_itinerary]
        )
        
    def create_itinerary(
        self, 
        city: str, 
        days: int, 
        budget_limit: float, 
        places: List[Dict[str, Any]], 
        weather: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Creates a day-by-day itinerary.
        """
        logger.info(f"ItineraryAgent: Generating itinerary for '{city}' ({days} days)")
        return generate_itinerary(city, days, budget_limit, places, weather)
