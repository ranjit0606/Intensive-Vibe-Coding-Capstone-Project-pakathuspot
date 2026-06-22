import os
import re
import json
import logging
from typing import Dict, Any, Tuple, List
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
import ollama
from dotenv import load_dotenv, find_dotenv

# Load environment variables from the nearest .env file
load_dotenv(find_dotenv(), override=True)

# Import sub-agents and their models
from agents.place_agent import PlaceRecommendationAgent, PlaceModel
from agents.weather_agent import WeatherAgent, WeatherDayModel
from agents.budget_agent import BudgetAgent, BudgetCategoryModel
from agents.itinerary_agent import ItineraryAgent, ItineraryDayModel

logger = logging.getLogger(__name__)

def clean_and_parse_json(text: str) -> Dict[str, Any]:
    """
    Robust JSON extraction and cleaning. Strips markdown code blocks
    and conversational wrappers from LLM outputs.
    """
    cleaned = text.strip()
    
    # 1. Strip markdown code block wrappers (e.g. ```json ... ```)
    if cleaned.startswith("```"):
        first_nl = cleaned.find("\n")
        if first_nl != -1:
            cleaned = cleaned[first_nl:].strip()
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()
            
    # 2. Find the bounding curly braces to ignore any prefix or suffix text
    start_idx = cleaned.find("{")
    end_idx = cleaned.rfind("}")
    if start_idx != -1 and end_idx != -1:
        cleaned = cleaned[start_idx:end_idx + 1]
        
    return json.loads(cleaned)

# Pydantic schema for query parameters extraction
class QueryParameters(BaseModel):
    destination: str = Field(description="The destination city or town (e.g., Ooty, Coorg)")
    days: int = Field(default=2, description="Duration of the trip in days")
    budget_limit: float = Field(default=10000.0, description="Maximum budget limit in INR")
    origin: str = Field(default="Bangalore", description="Starting city / origin of the journey")

# Combined schema for single LLM orchestration call
class CombinedTripResponse(BaseModel):
    recommended_places: List[PlaceModel] = Field(description="Refined list of tourist attractions and places")
    weather_forecast: List[WeatherDayModel] = Field(description="Refined day-wise weather forecast")
    packing_suggestions: List[str] = Field(description="Suggested clothing and items to pack")
    budget_categories: List[BudgetCategoryModel] = Field(description="Breakdown of expense categories")
    budget_total: float = Field(description="Sum of all categories in INR")
    budget_status: str = Field(description="Status of the budget relative to limit")
    itinerary: List[ItineraryDayModel] = Field(description="Day-by-day hourly schedule")
    consolidated_report: str = Field(description="The complete travel guide written in Markdown following the coordinator instructions")

from google.adk import Agent

class TravelCoordinatorAgent:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        
        # Check for placeholder or empty keys
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            self.has_api_key = False
            logger.warning(
                f"Coordinator: GEMINI_API_KEY is not configured. Key value: '{self.api_key}'. "
                f"Falling back to mock mode."
            )
        else:
            self.has_api_key = True
            masked_key = self.api_key[:5] + "..." if len(self.api_key) > 5 else "..."
            logger.info(f"Coordinator: Gemini API Key successfully loaded (Masked: {masked_key})")
        
        # Initialize sub-agents
        self.place_agent = PlaceRecommendationAgent()
        self.weather_agent = WeatherAgent()
        self.budget_agent = BudgetAgent()
        self.itinerary_agent = ItineraryAgent()
        
        # Lightweight ADK agent definition orchestrating other agents
        self.adk_agent = Agent(
            name="TravelCoordinatorAgent",
            description="Orchestrates PlaceAgent, WeatherAgent, BudgetAgent, and ItineraryAgent to build a consolidated travel plan.",
            sub_agents=[
                self.place_agent.adk_agent,
                self.weather_agent.adk_agent,
                self.budget_agent.adk_agent,
                self.itinerary_agent.adk_agent
            ]
        )
        
    def _extract_parameters_regex(self, prompt: str) -> Tuple[str, int, float, str]:
        """
        Regex-based fallback parameter extractor when Gemini is not configured.
        """
        # Default parameters
        destination = "Ooty"
        days = 2
        budget_limit = 10000.0
        origin = "Bangalore"
        
        prompt_lower = prompt.lower()
        
        # 1. Extract destination
        # Match popular destinations first
        cities = ["ooty", "coorg", "munnar", "wayanad", "goa", "chennai", "bangalore", "pondicherry"]
        found_city = False
        for city in cities:
            if city in prompt_lower:
                destination = city.title()
                found_city = True
                break
                
        if not found_city:
            # Match "to [city]"
            match_to = re.search(r'\bto\s+([a-zA-Z\s]+?)(?:\s+under|\s+from|\s+for|\s+budget|\b)', prompt)
            if match_to:
                destination = match_to.group(1).strip().title()
                
        # 2. Extract days
        match_days = re.search(r'(\d+)\s*(?:-|–)?\s*days?', prompt_lower)
        if not match_days:
            match_days = re.search(r'(\d+)\s*(?:-|–)?\s*day', prompt_lower)
        if match_days:
            days = int(match_days.group(1))
            
        # 3. Extract budget
        # Match RS, INR, ₹ followed or preceded by numbers
        match_budget = re.search(r'(?:under|below|budget|rs\.?|inr|₹)\s*(\d+)', prompt_lower)
        if not match_budget:
            match_budget = re.search(r'(\d+)\s*(?:rs|inr|rupees|bucks)', prompt_lower)
        if match_budget:
            budget_limit = float(match_budget.group(1))
            
        # 4. Extract origin
        match_origin = re.search(r'\bfrom\s+([a-zA-Z\s]+?)(?:\s+to|\s+under|\s+for|\s+budget|\b)', prompt)
        if match_origin:
            origin = match_origin.group(1).strip().title()
            
        return destination, days, budget_limit, origin

    def extract_query_parameters(self, prompt: str) -> Tuple[str, int, float, str]:
        """
        Parses intent parameters using Gemini or regex fallback.
        """
        if not self.has_api_key:
            return self._extract_parameters_regex(prompt)
            
        try:
            from google import genai
            from google.genai import types
            import json
            
            client = genai.Client(api_key=self.api_key)
            system_instruction = (
                "You are an expert NLP parser. Extract parameters from the user's travel request. "
                "Default destination to Ooty, days to 2, budget_limit to 10000, and origin to Bangalore "
                "if they are not specified."
            )
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=QueryParameters,
                    temperature=0.0
                )
            )
            
            if response.text is None:
                raise ValueError("Gemini returned empty or null response text")
            parsed = json.loads(response.text)
            logger.info(f"Coordinator: Extracted parameters using Gemini: {parsed}")
            return (
                parsed.get("destination", "Ooty"),
                parsed.get("days", 2),
                parsed.get("budget_limit", 10000.0),
                parsed.get("origin", "Bangalore")
            )
        except Exception as e:
            logger.error(f"Coordinator: Error parsing with Gemini: {e}. Falling back to regex.")
            return self._extract_parameters_regex(prompt)

    def plan_trip(self, user_prompt: str) -> Dict[str, Any]:
        """
        Orchestration loop: User Request -> Parameters -> Places -> Weather -> Budget -> Itinerary -> Aggregation.
        Optimized to perform exactly 1 LLM call for the entire request, with local Ollama fallback.
        """
        logger.info(f"Coordinator: Received request: '{user_prompt}'")
        
        # 1. Parse parameters using robust Regex (0 LLM calls)
        dest, days, budget_limit, origin = self._extract_parameters_regex(user_prompt)
        logger.info(f"Coordinator: Parameters Resolved -> Destination: {dest}, Days: {days}, Budget: ₹{budget_limit}, Origin: {origin}")
        
        # 2. Call Place Recommendation Agent (0 LLM calls)
        recommended_places = self.place_agent.recommend(dest)
        
        # 3. Call Weather Agent (0 LLM calls)
        weather_report = self.weather_agent.check_weather(dest, days)
        
        # 4. Call Budget Agent (0 LLM calls)
        budget_breakdown = self.budget_agent.estimate(dest, days, budget_limit, origin)
        
        # 5. Call Itinerary Agent (0 LLM calls)
        itinerary = self.itinerary_agent.create_itinerary(dest, days, budget_limit, recommended_places, weather_report)
        
        # 6. Gather general travel advice (merges weather/packing advice and coordinator advice)
        travel_advice = weather_report.get("packing_suggestions") or []
        travel_advice.append(f"Always keep soft copies of your ID cards and tickets.")
        travel_advice.append(f"Keep local cash handy, as network coverage in remote hill stations can be patchy.")
        
        # 7. Generate everything using a single LLM call (Gemini with Ollama fallback)
        consolidated_report = ""
        success_llm = False
        parsed_data = {}
        
        # If the destination is not pre-configured in the mock database (Ooty/Coorg),
        # we pass None to the LLM to prevent it from copying simulated placeholders.
        is_mock_places = dest.lower().strip() not in ["ooty", "coorg"]
        places_input = "None (Please generate real, actual popular tourist attractions for this destination from your knowledge.)" if is_mock_places else recommended_places
        
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
            "* Discard generic mock/simulated placeholders (such as containing 'View Point', 'Heritage Temple', etc.) and generate real, actual popular tourist attractions for the destination.\n"
        )
        
        prompt = (
            f"User Request:\n{user_prompt}\n\n"
            f"Destination: {dest}\n"
            f"Duration: {days} days\n"
            f"Budget: ₹{budget_limit}\n"
            f"Origin: {origin}\n\n"
            f"Places:\n{places_input}\n\n"
            f"Weather:\n{weather_report}\n\n"
            f"Budget Details:\n{budget_breakdown}\n\n"
            f"Draft Itinerary:\n{itinerary}\n\n"
            f"Please refine and consolidate this entire trip. You must fill out the schema completely.\n"
            f"For 'consolidated_report', generate the Markdown report matching the following structure:\n"
            f"1. Trip Overview\n"
            f"2. Recommended Places\n"
            f"3. Budget Summary\n"
            f"4. Day-wise Itinerary\n"
            f"5. Travel Tips\n"
        )

        if self.has_api_key:
            try:
                from google import genai
                from google.genai import types
                import json
                
                logger.info("Coordinator: Attempting to generate trip plan using Gemini API...")
                client = genai.Client(api_key=self.api_key)
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json",
                        response_schema=CombinedTripResponse,
                        temperature=0.2
                    )
                )
                
                if response.text is None:
                    raise ValueError("Gemini returned empty or null response text")
                
                parsed_data = clean_and_parse_json(response.text)
                success_llm = True
                logger.info("Coordinator: Successfully generated trip plan using Gemini API.")
            except Exception as e:
                logger.warning(f"Coordinator: Gemini API failed: {e}. Attempting Ollama fallback...")

        if not success_llm:
            try:
                import ollama
                import json
                logger.info("Coordinator: Attempting to generate trip plan using local Ollama (model: qwen2.5:3b)...")
                
                response = ollama.chat(
                    model='qwen2.5:3b',
                    messages=[
                        {'role': 'system', 'content': system_instruction},
                        {'role': 'user', 'content': prompt}
                    ],
                    format=CombinedTripResponse.model_json_schema()
                )
                
                content = response.message.content
                if not content:
                    raise ValueError("Ollama returned empty response content")
                    
                parsed_data = clean_and_parse_json(content)
                success_llm = True
                logger.info("Coordinator: Successfully generated trip plan using local Ollama (qwen2.5:3b).")
            except Exception as ollama_err:
                logger.error(f"Coordinator: Local Ollama execution failed: {ollama_err}")

        if success_llm:
            try:
                # Update our variables with refined, AI-generated results
                raw_places = parsed_data.get("recommended_places", [])
                recommended_places = [p if isinstance(p, dict) else p.model_dump() for p in raw_places] if raw_places else recommended_places
                
                raw_weather_forecast = parsed_data.get("weather_forecast", [])
                weather_forecast = [w if isinstance(w, dict) else w.model_dump() for w in raw_weather_forecast] if raw_weather_forecast else weather_report.get("forecast")
                
                weather_report = {
                    "forecast": weather_forecast,
                    "packing_suggestions": parsed_data.get("packing_suggestions", weather_report.get("packing_suggestions"))
                }
                
                raw_budget_categories = parsed_data.get("budget_categories", [])
                budget_categories = [b if isinstance(b, dict) else b.model_dump() for b in raw_budget_categories] if raw_budget_categories else budget_breakdown.get("categories")
                
                budget_breakdown = {
                    "categories": budget_categories,
                    "total_estimated": parsed_data.get("budget_total", budget_breakdown.get("total_estimated")),
                    "currency": "INR",
                    "status": parsed_data.get("budget_status", budget_breakdown.get("status"))
                }
                
                raw_itinerary = parsed_data.get("itinerary", [])
                itinerary = [i if isinstance(i, dict) else i.model_dump() for i in raw_itinerary] if raw_itinerary else itinerary
                
                travel_advice = parsed_data.get("packing_suggestions", travel_advice)
                consolidated_report = parsed_data.get("consolidated_report", "")
            except Exception as parse_err:
                logger.error(f"Coordinator: Error parsing LLM response: {parse_err}. Using fallback mock report.")
                success_llm = False

        if not success_llm:
            # Fallback mock report when both Gemini and Ollama fail
            consolidated_report = (
                f"# Trip Overview\n\nPlan for {dest} from {origin} for {days} days under ₹{budget_limit}.\n\n"
                f"# Top Attractions\n\n" + "\n".join([f"- {p.get('name')}: {p.get('description')}" for p in (recommended_places or [])]) + "\n\n"
                f"# Weather Insights\n\nForecast: " + ", ".join([f"{f.get('day')}: {f.get('condition')}" for f in (weather_report.get('forecast') or [])]) + "\n\n"
                f"# Budget Analysis\n\nTotal Estimated: ₹{budget_breakdown.get('total_estimated')}\n\n"
                f"# Day-by-Day Itinerary\n\nDetailed day-by-day sequence has been generated in the Itinerary tab.\n\n"
                f"# Travel Tips\n\n" + "\n".join([f"- {adv}" for adv in (travel_advice or [])]) + "\n\n"
                f"# Final Recommendation\n\nHave a safe and enjoyable trip to {dest}!"
            )

        # Combine everything into the final response
        final_plan = {
            "destination": dest,
            "days": days,
            "budget_limit": budget_limit,
            "origin": origin,
            "recommended_places": recommended_places,
            "budget_breakdown": budget_breakdown,
            "weather_report": weather_report,
            "itinerary": itinerary,
            "travel_advice": travel_advice,
            "consolidated_report": consolidated_report
        }
        
        logger.info(f"Coordinator: Finished planning trip for {dest} successfully.")
        return final_plan
