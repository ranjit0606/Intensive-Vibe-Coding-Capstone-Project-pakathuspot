import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Mock database of tourist attractions for popular destinations
MOCK_ATTRACTIONS: Dict[str, List[Dict[str, Any]]] = {
    "ooty": [
        {
            "name": "Government Botanical Garden",
            "description": "A lush, green 22-hectare botanical garden featuring exotic plants, lawns, and a 20-million-year-old fossilized tree trunk.",
            "rating": 4.5,
            "address": "Vannarapettai, Ooty, Tamil Nadu 643001",
            "latitude": 11.4183,
            "longitude": 76.7118,
            "best_time_to_visit": "9:00 AM - 6:00 PM (Morning preferred)",
            "entry_fee": 30.0,
            "category": "Nature"
        },
        {
            "name": "Ooty Lake & Boat House",
            "description": "A scenic artificial lake built in 1824, offering rowboats, paddleboats, motorboats, and a miniature train ride.",
            "rating": 4.2,
            "address": "Ooty Lake, Ooty, Tamil Nadu 643001",
            "latitude": 11.4085,
            "longitude": 76.6853,
            "best_time_to_visit": "9:00 AM - 5:30 PM (Sunset preferred)",
            "entry_fee": 15.0,
            "category": "Adventure"
        },
        {
            "name": "Doddabetta Peak",
            "description": "The highest mountain in the Nilgiri Hills (2,637m), offering breathtaking panoramic views of the valley and a telescope house.",
            "rating": 4.6,
            "address": "Ooty-Kotagiri Road, Ooty, Tamil Nadu 643002",
            "latitude": 11.4011,
            "longitude": 76.7371,
            "best_time_to_visit": "7:00 AM - 6:00 PM (Early morning for clear views)",
            "entry_fee": 10.0,
            "category": "Sightseeing"
        },
        {
            "name": "Government Rose Garden",
            "description": "The largest rose garden in India, spanning 4 hectares on the slopes of Elk Hill, containing over 20,000 varieties of roses.",
            "rating": 4.4,
            "address": "Bombay Castle, Ooty, Tamil Nadu 643001",
            "latitude": 11.4069,
            "longitude": 76.7145,
            "best_time_to_visit": "9:00 AM - 6:00 PM (March to June is peak bloom)",
            "entry_fee": 30.0,
            "category": "Nature"
        },
        {
            "name": "Pykara Waterfalls & Lake",
            "description": "A majestic waterfall flowing over flat rocks, surrounded by pine forests. Offers speed boating on the pykara reservoir nearby.",
            "rating": 4.7,
            "address": "Pykara, Ooty, Tamil Nadu 643103",
            "latitude": 11.5312,
            "longitude": 76.5982,
            "best_time_to_visit": "9:00 AM - 5:00 PM (After monsoon)",
            "entry_fee": 20.0,
            "category": "Nature"
        },
        {
            "name": "Stone House",
            "description": "The first bungalow built in Ooty in 1822 by John Sullivan. Now serves as the Government Arts College and a historic monument.",
            "rating": 4.1,
            "address": "Stone House Area, Ooty, Tamil Nadu 643002",
            "latitude": 11.4178,
            "longitude": 76.7161,
            "best_time_to_visit": "10:00 AM - 5:00 PM",
            "entry_fee": 15.0,
            "category": "History"
        }
    ],
    "coorg": [
        {
            "name": "Abbey Falls",
            "description": "A stunning waterfall located amidst coffee plantations and spice estates, with a hanging bridge for photos.",
            "rating": 4.5,
            "address": "Abbey Falls Rd, Madikeri, Karnataka 571201",
            "latitude": 12.4578,
            "longitude": 75.7198,
            "best_time_to_visit": "9:00 AM - 5:00 PM",
            "entry_fee": 15.0,
            "category": "Nature"
        },
        {
            "name": "Namdroling Monastery (Golden Temple)",
            "description": "The largest teaching center of the Nyingma lineage of Tibetan Buddhism in the world, featuring massive gold statues.",
            "rating": 4.8,
            "address": "Arlikumari, Bylakuppe, Karnataka 571104",
            "latitude": 12.4294,
            "longitude": 75.9678,
            "best_time_to_visit": "9:00 AM - 6:00 PM",
            "entry_fee": 0.0,
            "category": "History"
        },
        {
            "name": "Raja's Seat",
            "description": "A scenic garden atop a hill where the Kings of Coorg watched sunsets. Features musical fountains in the evening.",
            "rating": 4.4,
            "address": "Madikeri, Karnataka 571201",
            "latitude": 12.4149,
            "longitude": 75.7381,
            "best_time_to_visit": "5:30 PM - 7:30 PM (Sunset)",
            "entry_fee": 10.0,
            "category": "Sightseeing"
        }
    ]
}

def nearby_places(destination: str, query: str = "tourist attraction") -> List[Dict[str, Any]]:
    """
    Search for interesting places or attractions in a given destination.
    
    Args:
        destination (str): The name of the city or town (e.g. 'Ooty', 'Coorg').
        query (str): The type of places to search (e.g., 'tourist attraction', 'restaurants').
        
    Returns:
        List[Dict[str, Any]]: A list of places, each with description, rating, coordinates, etc.
    """
    city = destination.lower().strip()
    logger.info(f"Searching places in '{city}' matching query '{query}'")
    
    # Try mock database first
    if city in MOCK_ATTRACTIONS:
        return MOCK_ATTRACTIONS[city]
    
    # Dynamic fallback generator for any city if not in database
    logger.warning(f"Destination '{destination}' not in mock database. Generating simulated coordinates/places.")
    
    # Generate generic coordinates based on hash of the destination name
    import hashlib
    h = hashlib.md5(city.encode('utf-8')).hexdigest()
    # Pseudorandom but deterministic coordinates in India
    lat = 10.0 + (int(h[:4], 16) % 1500) / 100.0  # Between 10.0 and 25.0
    lon = 75.0 + (int(h[4:8], 16) % 1000) / 100.0  # Between 75.0 and 85.0
    
    return [
        {
            "name": f"{destination.title()} View Point",
            "description": "A scenic lookout spot popular with travelers, offering panoramic views of the city landscape.",
            "rating": 4.4,
            "address": f"Hills Road, {destination.title()}",
            "latitude": lat,
            "longitude": lon,
            "best_time_to_visit": "6:00 AM - 6:00 PM",
            "entry_fee": 0.0,
            "category": "Sightseeing"
        },
        {
            "name": f"{destination.title()} Heritage Temple",
            "description": "An ancient temple showcasing local architecture, rich heritage, and intricate stone carvings.",
            "rating": 4.6,
            "address": f"Temple Street, {destination.title()}",
            "latitude": lat + 0.015,
            "longitude": lon - 0.012,
            "best_time_to_visit": "7:00 AM - 8:00 PM",
            "entry_fee": 0.0,
            "category": "History"
        },
        {
            "name": f"{destination.title()} Local Market",
            "description": "A lively marketplace where visitors can shop for local crafts, spices, clothes, and try street food.",
            "rating": 4.2,
            "address": f"Market Square, {destination.title()}",
            "latitude": lat - 0.012,
            "longitude": lon + 0.018,
            "best_time_to_visit": "4:00 PM - 9:00 PM",
            "entry_fee": 0.0,
            "category": "Shopping"
        }
    ]
