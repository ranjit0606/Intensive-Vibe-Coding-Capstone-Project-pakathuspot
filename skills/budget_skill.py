import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

def estimate_budget(destination: str, days: int, max_budget: float, origin: str = "Bangalore") -> Dict[str, Any]:
    """
    Skill: Computes a budget breakdown, adjusting categories to fit the limit.
    
    Args:
        destination (str): Target city.
        days (int): Trip duration in days.
        max_budget (float): Maximum budget constraint (INR).
        origin (str): Origin city for travel cost estimation.
        
    Returns:
        Dict[str, Any]: Budget breakdown and status.
    """
    logger.info(f"Skill executed: estimate_budget for '{destination}' (days={days}, limit={max_budget})")
    
    # Calculate travel distance cost (from distance_tool dynamically or mock estimate)
    # We will import distance tool here
    from tools.distance_tool import calculate_distance_and_cost
    
    # Select transport mode based on budget and distance
    # For low budgets, prefer train/bus. For higher budgets, car/flight.
    try:
        if max_budget < 8000:
            transport_mode = "bus"
        elif max_budget < 15000:
            transport_mode = "train"
        else:
            transport_mode = "car"
            
        dist_res = calculate_distance_and_cost(origin, destination, transport_mode)
        travel_cost = dist_res["estimated_cost_inr"]
    except Exception as e:
        logger.error(f"Error calculating distance cost: {e}")
        travel_cost = 1200.0  # Fallback
        transport_mode = "Bus"
        dist_res = {"mode": "Bus", "distance_km": 300, "duration": "6h"}
        
    # Scale accommodation and food tiers based on remaining budget
    remaining = max_budget - travel_cost
    nights = max(1, days - 1)
    
    # Cost per night accommodation tier thresholds
    if remaining <= 0:
        # Extremely tight budget
        hotel_rate = 800.0    # Hostel / Dormitory
        food_rate = 300.0     # Street food / local eateries
        activity_rate = 150.0  # Free/low-cost sights
    elif remaining / days < 1500:
        hotel_rate = 1200.0   # Budget Homestay / Guesthouse
        food_rate = 400.0     # Budget restaurants
        activity_rate = 250.0
    elif remaining / days < 3500:
        hotel_rate = 2200.0   # 3-Star Hotel
        food_rate = 700.0     # Mid-range restaurants
        activity_rate = 500.0
    else:
        hotel_rate = 4500.0   # Luxury Resort / 4-Star
        food_rate = 1500.0    # Fine dining
        activity_rate = 1000.0
        
    accommodation_total = hotel_rate * nights
    food_total = food_rate * days
    activities_total = activity_rate * days
    emergency_total = round(max_budget * 0.08, -1) # 8% buffer
    
    total_estimated = travel_cost + accommodation_total + food_total + activities_total + emergency_total
    
    # Adjust to keep under budget if exceeded
    status = "Within Budget"
    if total_estimated > max_budget:
        status = "Slightly Over Budget"
        # Scale back to fit under budget
        hotel_rate = max(600.0, hotel_rate * 0.75)
        food_rate = max(250.0, food_rate * 0.8)
        activities_total *= 0.7
        accommodation_total = hotel_rate * nights
        food_total = food_rate * days
        total_estimated = travel_cost + accommodation_total + food_total + activities_total + emergency_total
        if total_estimated <= max_budget:
            status = "Optimized to Budget"
            
    categories = [
        {
            "category": "Transport",
            "amount": travel_cost,
            "description": f"Round trip from {origin.title()} to {destination.title()} via {dist_res.get('mode', transport_mode.title())} ({dist_res.get('distance_km', 'N/A')} km)."
        },
        {
            "category": "Accommodation",
            "amount": accommodation_total,
            "description": f"{nights} night(s) in a {get_hotel_tier_name(hotel_rate)} (₹{int(hotel_rate)}/night)."
        },
        {
            "category": "Food & Dining",
            "amount": food_total,
            "description": f"{days} days of meals. Estimated at ₹{int(food_rate)}/day."
        },
        {
            "category": "Sightseeing & Entry Fees",
            "amount": activities_total,
            "description": f"Entry fees and local activities at ₹{int(activity_rate)}/day."
        },
        {
            "category": "Emergency Fund",
            "amount": emergency_total,
            "description": "8% safety buffer for unplanned expenses, local transit, or tips."
        }
    ]
    
    return {
        "categories": categories,
        "total_estimated": total_estimated,
        "currency": "INR",
        "status": status,
        "limit": max_budget
    }

def get_hotel_tier_name(rate: float) -> str:
    if rate < 1000:
        return "Hostel Dorm / Backpackers Stay"
    if rate < 1800:
        return "Budget Homestay / Guesthouse"
    if rate < 3000:
        return "Standard 3-Star Hotel"
    return "Premium 4-Star Resort"
