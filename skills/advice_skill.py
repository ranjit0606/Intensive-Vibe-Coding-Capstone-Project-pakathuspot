import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def travel_advice(weather_data: Dict[str, Any]) -> List[str]:
    """
    Skill: Analyzes weather forecast and outputs safety, clothing and activity advice.
    
    Args:
        weather_data (Dict[str, Any]): The weather forecast data structure.
        
    Returns:
        List[str]: List of warnings, gear recommendations, and tips.
    """
    logger.info(f"Skill executed: travel_advice")
    
    forecasts = weather_data.get("forecast", [])
    advice = []
    
    # Analyze temperature ranges and conditions
    has_rain = False
    min_temp = 100.0
    max_temp = -100.0
    conditions = set()
    
    for f in forecasts:
        conditions.add(f.get("condition", "").lower())
        temp_max = f.get("temp_max", 25.0)
        temp_min = f.get("temp_min", 15.0)
        prob = f.get("precipitation_probability", 0)
        
        if "rain" in f.get("condition", "").lower() or "drizzle" in f.get("condition", "").lower() or prob > 40:
            has_rain = True
            
        if temp_min < min_temp:
            min_temp = temp_min
        if temp_max > max_temp:
            max_temp = temp_max
            
    # Add advice based on temperature
    if min_temp < 15.0:
        advice.append("It gets chilly! Bring a light jacket, sweater, or shawl, especially for evenings.")
    if min_temp < 10.0:
        advice.append("Cold weather warning: Pack heavy woolens, thermal wear, and gloves.")
    if max_temp > 30.0:
        advice.append("Warm weather: Wear breathable cotton clothing, sunglasses, and carry sunblock.")
        
    # Add advice based on conditions
    if has_rain:
        advice.append("Rain expected: Carry an umbrella or high-quality rain poncho. Wear waterproof shoes.")
    if any(c in ["foggy", "depositing rime fog"] for c in conditions):
        advice.append("Foggy conditions: High altitude driving can be dangerous. Travel before sunset and drive with fog lights on.")
    if "thunderstorm" in conditions:
        advice.append("Thunderstorms forecast: Avoid outdoor trekking or standing near tall structures during lightning.")
        
    # General travel tips
    advice.append("Stay hydrated. Carry a reusable water bottle.")
    advice.append("Comfortable walking shoes are highly recommended for sightseeing.")
    
    return advice
