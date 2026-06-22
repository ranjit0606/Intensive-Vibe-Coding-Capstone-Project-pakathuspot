import json
import logging
from agents.coordinator import CombinedTripResponse
import ollama

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_ollama")

system_instruction = (
    "You are the Travel Coordinator Agent for PakathuSpot.\n\n"
    "Your task is to combine and optimize the outputs from the Place Agent, Weather Agent, Budget Agent, and Itinerary Agent into a single cohesive, high-quality travel plan.\n"
    "Instructions:\n"
    "* Merge all agent outputs into one coherent response.\n"
    "* Prioritize the best attractions and experiences.\n"
    "* Consider weather conditions when recommending activities.\n"
    "* Ensure the plan stays within budget.\n"
    "* Improve the itinerary if needed.\n"
    "* Provide practical travel tips and recommendations.\n"
    "* Keep the response concise, useful, and well-structured.\n"
    "* Do not mention internal agents.\n"
)

prompt = (
    "User Request:\nPlan a 3-day trip to Chennai under ₹10000 from Bangalore\n\n"
    "Destination: Chennai\n"
    "Duration: 3 days\n"
    "Budget: ₹10000.0\n"
    "Origin: Bangalore\n\n"
    "Places:\n[{'name': 'Chennai Marina Beach', 'description': 'Longest natural urban beach in the country.', 'rating': 4.5, 'address': 'Marina Beach, Chennai', 'latitude': 13.0489, 'longitude': 80.2824, 'best_time_to_visit': '5:00 AM - 9:00 AM', 'entry_fee': 0.0, 'category': 'Nature'}]\n\n"
    "Weather:\n{'forecast': [{'day': 'Day 1', 'temperature': '28C to 35C', 'condition': 'Partly Cloudy', 'advice': 'Keep hydrated'}], 'packing_suggestions': ['Sunscreen']}\n\n"
    "Budget Details:\n{'categories': [{'category': 'Transport', 'amount': 2000.0, 'description': 'Train tickets'}], 'total_estimated': 2000.0, 'currency': 'INR', 'status': 'Within Budget'}\n\n"
    "Draft Itinerary:\n[{'day_number': 1, 'theme': 'Beach day', 'activities': [{'time': '09:00 AM', 'place_name': 'Chennai Marina Beach', 'activity_description': 'Walk on the beach', 'cost': 0.0}]}]\n\n"
    "Please refine and consolidate this entire trip. You must fill out the schema completely.\n"
    "For 'consolidated_report', generate the Markdown report matching the following structure:\n"
    "1. Trip Overview\n"
    "2. Recommended Places\n"
    "3. Budget Summary\n"
    "4. Day-wise Itinerary\n"
    "5. Travel Tips\n"
)

try:
    print("Sending query to local Ollama (qwen2.5:3b)...")
    response = ollama.chat(
        model='qwen2.5:3b',
        messages=[
            {'role': 'system', 'content': system_instruction},
            {'role': 'user', 'content': prompt}
        ],
        format=CombinedTripResponse.model_json_schema()
    )
    print("Ollama response content:")
    print(response.message.content)
except Exception as e:
    print("Error calling Ollama:", e)
