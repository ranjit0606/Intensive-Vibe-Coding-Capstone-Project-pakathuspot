import logging
from mcp.server.fastmcp import FastMCP
from tools.maps_tool import nearby_places
from tools.weather_tool import get_weather_forecast
from tools.distance_tool import calculate_distance_and_cost

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pakathuspot.mcp")

# Initialize FastMCP Server
mcp = FastMCP("PakathuSpot Travel Companion")

@mcp.tool(name="nearby_places")
def get_nearby_places(destination: str, query: str = "tourist attraction") -> str:
    """
    Retrieve tourist attractions, landmarks, and interesting places in a destination city.
    
    Args:
        destination: The destination city or town name (e.g. 'Ooty', 'Coorg').
        query: The type of places to search, defaults to 'tourist attraction'.
    """
    logger.info(f"MCP Tool call: nearby_places for '{destination}'")
    try:
        places = nearby_places(destination, query)
        return f"Successfully found places in {destination}:\n{places}"
    except Exception as e:
        return f"Error finding places: {str(e)}"

@mcp.tool(name="weather_forecast")
def get_weather(destination: str, days: int = 2) -> str:
    """
    Retrieve real-time weather forecasts for a city, including temperatures and conditions.
    
    Args:
        destination: The city or town name.
        days: Number of days for forecast, typically between 1 and 3.
    """
    logger.info(f"MCP Tool call: weather_forecast for '{destination}' (days={days})")
    try:
        weather = get_weather_forecast(destination, days)
        return f"Weather report for {destination}:\n{weather}"
    except Exception as e:
        return f"Error fetching weather: {str(e)}"

@mcp.tool(name="distance_calculator")
def get_distance_and_cost(origin: str, destination: str, transport_mode: str = "car") -> str:
    """
    Calculate the route distance, travel time, and estimated transport cost between two Indian cities.
    
    Args:
        origin: Starting city.
        destination: Ending city.
        transport_mode: Mode of travel ('car', 'bus', 'train', 'flight'). Default is 'car'.
    """
    logger.info(f"MCP Tool call: distance_calculator from '{origin}' to '{destination}' via '{transport_mode}'")
    try:
        res = calculate_distance_and_cost(origin, destination, transport_mode)
        return f"Route estimation from {origin} to {destination}:\n{res}"
    except Exception as e:
        return f"Error calculating distance: {str(e)}"

if __name__ == "__main__":
    # Start the FastMCP server (stdin/stdout transports by default)
    mcp.run()
