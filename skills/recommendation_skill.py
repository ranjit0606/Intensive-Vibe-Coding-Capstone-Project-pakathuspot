import logging
from typing import List, Dict, Any
from tools.maps_tool import nearby_places

logger = logging.getLogger(__name__)

def recommend_places(destination: str) -> List[Dict[str, Any]]:
    """
    Skill: Recommends and groups places for a destination city.
    
    Args:
        destination (str): The target city.
        
    Returns:
        List[Dict[str, Any]]: Recommended places with details.
    """
    logger.info(f"Skill executed: recommend_places for '{destination}'")
    
    # Retrieve places from maps tool
    places = nearby_places(destination)
    
    # Ensure they have standard format and fields
    enriched_places = []
    for p in places:
        enriched_places.append({
            "name": p.get("name"),
            "description": p.get("description"),
            "rating": p.get("rating", 4.0),
            "address": p.get("address"),
            "latitude": p.get("latitude"),
            "longitude": p.get("longitude"),
            "best_time_to_visit": p.get("best_time_to_visit", "Anytime"),
            "entry_fee": p.get("entry_fee", 0.0),
            "category": p.get("category", "Sightseeing")
        })
        
    # Sort by rating descending
    enriched_places.sort(key=lambda x: x["rating"], reverse=True)
    return enriched_places
