import logging
import requests
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Fallback coordinates for geocoding
CITY_COORDINATES: Dict[str, Dict[str, float]] = {
    "ooty": {"latitude": 11.4102, "longitude": 76.6950},
    "coorg": {"latitude": 12.4244, "longitude": 75.7382},
    "bangalore": {"latitude": 12.9716, "longitude": 77.5946},
    "chennai": {"latitude": 13.0827, "longitude": 80.2707},
    "munnar": {"latitude": 10.0889, "longitude": 77.0595},
    "wayanad": {"latitude": 11.6854, "longitude": 76.1320},
    "goa": {"latitude": 15.2993, "longitude": 74.1240},
}

# WMO Weather interpretation codes (https://open-meteo.com/en/docs)
WEATHER_CODES = {
    0: "Clear Sky",
    1: "Mainly Clear",
    2: "Partly Cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing Rime Fog",
    51: "Light Drizzle",
    53: "Moderate Drizzle",
    55: "Dense Drizzle",
    61: "Slight Rain",
    63: "Moderate Rain",
    65: "Heavy Rain",
    71: "Slight Snow Fall",
    73: "Moderate Snow Fall",
    75: "Heavy Snow Fall",
    80: "Slight Rain Showers",
    81: "Moderate Rain Showers",
    82: "Violent Rain Showers",
    95: "Thunderstorm",
    96: "Thunderstorm with Slight Hail",
    99: "Thunderstorm with Heavy Hail"
}

def geocode_city(city_name: str) -> Dict[str, float]:
    """
    Resolve a city name to latitude and longitude coordinates.
    """
    city_key = city_name.lower().strip()
    
    # Try Nominatim API
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={city_name}&format=json&limit=1"
        headers = {"User-Agent": "PakathuSpot/1.0 (ranjit@gemini.com)"}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data:
                lat = float(data[0]["lat"])
                lon = float(data[0]["lon"])
                logger.info(f"Geocoded '{city_name}' online: {lat}, {lon}")
                return {"latitude": lat, "longitude": lon}
    except Exception as e:
        logger.warning(f"Failed online geocoding for '{city_name}': {e}")
        
    # Try local database fallback
    if city_key in CITY_COORDINATES:
        logger.info(f"Using local coordinates for '{city_name}'")
        return CITY_COORDINATES[city_key]
        
    # Default fallback to India center coordinates if unknown
    logger.warning(f"Unknown city '{city_name}'. Returning default coordinates.")
    return {"latitude": 20.5937, "longitude": 78.9629}

def get_weather_forecast(destination: str, days: int = 2) -> Dict[str, Any]:
    """
    Get the weather forecast for a destination.
    
    Args:
        destination (str): Name of the destination city.
        days (int): Number of days for forecast (1-7).
        
    Returns:
        Dict[str, Any]: Structured weather forecast.
    """
    coords = geocode_city(destination)
    lat = coords["latitude"]
    lon = coords["longitude"]
    days = max(1, min(7, days)) # Bound check between 1 and 7 days
    
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,weathercode,precipitation_probability_max&timezone=auto"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            daily = data.get("daily", {})
            
            forecast_list = []
            for i in range(days):
                if i < len(daily.get("time", [])):
                    code = daily["weathercode"][i]
                    forecast_list.append({
                        "date": daily["time"][i],
                        "temp_max": daily["temperature_2m_max"][i],
                        "temp_min": daily["temperature_2m_min"][i],
                        "condition": WEATHER_CODES.get(code, "Unknown"),
                        "precipitation_probability": daily["precipitation_probability_max"][i]
                    })
            
            logger.info(f"Retrieved weather forecast online for '{destination}'")
            return {
                "destination": destination.title(),
                "latitude": lat,
                "longitude": lon,
                "forecast": forecast_list
            }
    except Exception as e:
        logger.error(f"Failed to retrieve weather for '{destination}': {e}")
        
    # Return mock forecast if API call fails
    import datetime
    logger.warning(f"Returning mock weather forecast for '{destination}'")
    today = datetime.date.today()
    
    # Customize mock weather slightly based on destination temperature profiles
    city_key = destination.lower().strip()
    is_hill_station = city_key in ["ooty", "coorg", "munnar", "wayanad"]
    base_temp = 16 if is_hill_station else 28
    
    forecast_list = []
    for i in range(days):
        day_date = today + datetime.timedelta(days=i)
        forecast_list.append({
            "date": day_date.strftime("%Y-%m-%d"),
            "temp_max": base_temp + (i % 3),
            "temp_min": base_temp - 6 - (i % 2),
            "condition": "Partly Cloudy" if i % 2 == 0 else "Clear Sky",
            "precipitation_probability": 10 if i % 2 == 0 else 0
        })
        
    return {
        "destination": destination.title(),
        "latitude": lat,
        "longitude": lon,
        "forecast": forecast_list
    }
