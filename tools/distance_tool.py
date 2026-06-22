import logging
import math
from typing import Dict, Any
from tools.weather_tool import geocode_city

logger = logging.getLogger(__name__)

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on the earth in kilometers.
    """
    # Earth radius in kilometers
    R = 6371.0
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0) ** 2
        
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def calculate_distance_and_cost(
    origin: str, 
    destination: str, 
    transport_mode: str = "car"
) -> Dict[str, Any]:
    """
    Calculate travel distance, time, and cost from origin to destination.
    
    Args:
        origin (str): Start city.
        destination (str): Target city.
        transport_mode (str): Mode of travel ('car', 'bus', 'train', 'flight').
        
    Returns:
        Dict[str, Any]: Object containing distance, duration, and cost breakdown.
    """
    origin_clean = origin.strip()
    dest_clean = destination.strip()
    mode = transport_mode.lower().strip()
    
    logger.info(f"Calculating distance from '{origin_clean}' to '{dest_clean}' via '{mode}'")
    
    # Geocode both locations
    coords_org = geocode_city(origin_clean)
    coords_dst = geocode_city(dest_clean)
    
    # Direct great-circle distance
    straight_distance = haversine_distance(
        coords_org["latitude"], coords_org["longitude"],
        coords_dst["latitude"], coords_dst["longitude"]
    )
    
    # Adjust straight distance to road distance (routing factor of ~1.25 for land routes)
    routing_factor = 1.25 if mode in ["car", "bus", "train"] else 1.05
    road_distance = straight_distance * routing_factor
    
    # Standard values for India travel
    avg_speeds = {
        "car": 55.0,     # km/h
        "bus": 45.0,     # km/h
        "train": 50.0,   # km/h
        "flight": 700.0  # km/h
    }
    speed = avg_speeds.get(mode, 55.0)
    
    # Calculate travel duration (hours)
    duration_hours = road_distance / speed
    # Format duration
    hours = int(duration_hours)
    minutes = int((duration_hours - hours) * 60)
    duration_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
    
    # Calculate estimated costs (in INR)
    # Rates per km per person/vehicle
    rates = {
        "car": 12.0,      # Fuel + Tolls (private vehicle total)
        "bus": 3.0,       # Bus ticket cost per km
        "train": 1.8,     # Train ticket (sleeper/3AC avg)
        "flight": 7.5      # Flight ticket per km (minimum charges apply)
    }
    
    rate = rates.get(mode, 12.0)
    estimated_cost = road_distance * rate
    
    # Handle min ticket costs
    if mode == "flight" and estimated_cost < 3500.0:
        estimated_cost = 3500.0
    elif mode == "train" and estimated_cost < 150.0:
        estimated_cost = 150.0
    elif mode == "bus" and estimated_cost < 200.0:
        estimated_cost = 200.0
        
    # Round estimates
    road_distance = round(road_distance, 1)
    estimated_cost = round(estimated_cost, -1) # Round to nearest 10
    
    return {
        "origin": origin_clean.title(),
        "destination": dest_clean.title(),
        "mode": mode.title(),
        "distance_km": road_distance,
        "duration": duration_str,
        "duration_hours": round(duration_hours, 1),
        "estimated_cost_inr": estimated_cost,
        "notes": f"Estimated via standard route. Toll and fuel costs subject to change."
    }
