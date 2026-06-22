import os
import logging
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from dotenv import load_dotenv, find_dotenv
from skills.recommendation_skill import recommend_places

# Load environment variables from the nearest .env file
load_dotenv(find_dotenv(), override=True)

logger = logging.getLogger(__name__)

# Pydantic models for structured Gemini outputs
class PlaceModel(BaseModel):
    name: str = Field(description="Name of the place")
    description: str = Field(description="Brief engaging description of the attraction")
    rating: float = Field(description="Rating out of 5.0")
    address: str = Field(description="Physical address of the location")
    latitude: float = Field(description="Latitude coordinate")
    longitude: float = Field(description="Longitude coordinate")
    best_time_to_visit: str = Field(description="Best hours or season to visit")
    entry_fee: float = Field(description="Entry fee in INR (0 if free)")
    category: str = Field(description="Category (e.g. Nature, Sightseeing, Adventure, History)")

class PlaceAgentResponse(BaseModel):
    places: List[PlaceModel] = Field(description="List of recommended places")

from google.adk import Agent

class PlaceRecommendationAgent:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        
        # Check for placeholder or empty keys
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            self.has_api_key = False
            logger.warning(
                f"PlaceAgent: GEMINI_API_KEY is not configured. Key value: '{self.api_key}'. "
                f"Falling back to mock mode."
            )
        else:
            self.has_api_key = True
            masked_key = self.api_key[:5] + "..." if len(self.api_key) > 5 else "..."
            logger.info(f"PlaceAgent: Gemini API Key successfully loaded (Masked: {masked_key})")
            
        # Lightweight ADK agent definition
        self.adk_agent = Agent(
            name="PlaceAgent",
            description="Recommends tourist attractions for a given destination.",
            tools=[recommend_places]
        )
        
    def recommend(self, destination: str) -> List[Dict[str, Any]]:
        """
        Executes the place recommendation process.
        """
        logger.info(f"PlaceAgent: Recommending places for '{destination}'")
        return recommend_places(destination)
