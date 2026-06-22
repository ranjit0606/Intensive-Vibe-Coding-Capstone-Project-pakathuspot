import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def generate_itinerary(
    city: str, 
    days: int, 
    budget_limit: float, 
    places: List[Dict[str, Any]], 
    weather: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Skill: Generates a chronological day-by-day travel itinerary.
    
    Args:
        city (str): Destination city name.
        days (int): Number of days.
        budget_limit (float): Budget constraint.
        places (List[Dict[str, Any]]): List of recommended attractions.
        weather (Dict[str, Any]): Weather forecast.
        
    Returns:
        List[Dict[str, Any]]: Structured list of days, each with themes and hourly activities.
    """
    logger.info(f"Skill executed: generate_itinerary for '{city}' ({days} days)")
    
    # We will distribute the places across the days
    # Let's say we visit 2-3 places per day
    places_to_visit = places.copy()
    
    days_list = []
    
    # Day themes based on city and order
    themes = [
        "Nature & Scenery Discovery",
        "Heritage & Adventure Walk",
        "Culinary & Local Markets",
        "Scenic Waterfalls & Lakes",
        "Cultural Exploration"
    ]
    
    for day_idx in range(days):
        day_num = day_idx + 1
        theme = themes[day_idx % len(themes)]
        
        # Pull 2 places for this day
        day_places = []
        if len(places_to_visit) > 0:
            day_places.append(places_to_visit.pop(0))
        if len(places_to_visit) > 0:
            day_places.append(places_to_visit.pop(0))
            
        activities = []
        
        # Morning Activity (9:00 AM)
        if len(day_places) > 0:
            p = day_places[0]
            activities.append({
                "time": "09:00 AM",
                "place_name": p["name"],
                "activity_description": f"Start the day at the beautiful {p['name']}. {p['description']}",
                "cost": p["entry_fee"]
            })
        else:
            activities.append({
                "time": "09:00 AM",
                "place_name": f"{city.title()} View Point",
                "activity_description": f"Enjoy the morning breeze at the local mountain peak.",
                "cost": 0.0
            })
            
        # Lunch (01:00 PM)
        lunch_cost = 250.0 if budget_limit < 8000 else 600.0
        activities.append({
            "time": "01:00 PM",
            "place_name": "Local Restaurant",
            "activity_description": f"Stop for a traditional lunch. Try the local specialty dishes.",
            "cost": lunch_cost
        })
        
        # Afternoon Activity (02:30 PM)
        if len(day_places) > 1:
            p = day_places[1]
            activities.append({
                "time": "02:30 PM",
                "place_name": p["name"],
                "activity_description": f"Head over to {p['name']}. {p['description']}",
                "cost": p["entry_fee"]
            })
        else:
            activities.append({
                "time": "02:30 PM",
                "place_name": f"{city.title()} Lake Walk",
                "activity_description": "Relax and stroll around the scenic lake views.",
                "cost": 0.0
            })
            
        # Evening Tea/Snacks (05:30 PM)
        activities.append({
            "time": "05:30 PM",
            "place_name": "High Street / Tea Stall",
            "activity_description": f"Enjoy some hot local tea, coffee, and fresh snacks.",
            "cost": 80.0
        })
        
        # Dinner (08:00 PM)
        dinner_cost = 300.0 if budget_limit < 8000 else 700.0
        activities.append({
            "time": "08:00 PM",
            "place_name": "Dine-in Restaurant",
            "activity_description": f"Conclude the day with a relaxed dinner before returning to your hotel.",
            "cost": dinner_cost
        })
        
        days_list.append({
            "day_number": day_num,
            "theme": theme,
            "activities": activities
        })
        
    return days_list
