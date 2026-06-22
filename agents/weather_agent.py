import os
import logging
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from dotenv import load_dotenv, find_dotenv
from tools.weather_tool import get_weather_forecast
from skills.advice_skill import travel_advice

# Load environment variables from the nearest .env file
load_dotenv(find_dotenv(), override=True)

logger = logging.getLogger(__name__)

# Pydantic models for structured Gemini outputs
class WeatherDayModel(BaseModel):
    day: str = Field(description="Date or day description (e.g. Day 1, Monday)")
    temperature: str = Field(description="Formatted temperature (e.g. 15°C - 22°C)")
    condition: str = Field(description="Weather condition (e.g. Clear Sky, Rain expected)")
    advice: str = Field(description="Specific weather advice for this day")

class WeatherAgentResponse(BaseModel):
    forecast: List[WeatherDayModel] = Field(description="Weather forecast list")
    packing_suggestions: List[str] = Field(description="Suggested clothing and items to pack")

from google.adk import Agent

class WeatherAgent:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        
        # Check for placeholder or empty keys
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            self.has_api_key = False
            logger.warning(
                f"WeatherAgent: GEMINI_API_KEY is not configured. Key value: '{self.api_key}'. "
                f"Falling back to mock mode."
            )
        else:
            self.has_api_key = True
            masked_key = self.api_key[:5] + "..." if len(self.api_key) > 5 else "..."
            logger.info(f"WeatherAgent: Gemini API Key successfully loaded (Masked: {masked_key})")
            
        # Lightweight ADK agent definition
        self.adk_agent = Agent(
            name="WeatherAgent",
            description="Retrieves live weather forecasts and compiles daily advice.",
            tools=[get_weather_forecast, travel_advice]
        )
        
    def check_weather(self, destination: str, days: int = 2) -> Dict[str, Any]:
        """
        Retrieves weather forecast and generates advice.
        """
        logger.info(f"WeatherAgent: Checking weather for '{destination}' ({days} days)")
        
        # Get raw forecast
        weather_raw = get_weather_forecast(destination, days)
        
        # Generate raw advice
        advice_list = travel_advice(weather_raw)
        
        # Format the forecast nicely in python first
        formatted_forecast = []
        for idx, f in enumerate(weather_raw.get("forecast", [])):
            formatted_forecast.append({
                "day": f"Day {idx + 1} ({f['date']})",
                "temperature": f"{int(f['temp_min'])}°C to {int(f['temp_max'])}°C",
                "condition": f["condition"],
                "advice": f"Chance of rain is {f['precipitation_probability']}%."
            })
            
        weather_report = {
            "forecast": formatted_forecast,
            "packing_suggestions": advice_list
        }
        return weather_report
