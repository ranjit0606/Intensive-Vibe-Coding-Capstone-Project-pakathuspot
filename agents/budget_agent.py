import os
import logging
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from dotenv import load_dotenv, find_dotenv
from skills.budget_skill import estimate_budget

# Load environment variables from the nearest .env file
load_dotenv(find_dotenv(), override=True)

logger = logging.getLogger(__name__)

# Pydantic models for structured Gemini outputs
class BudgetCategoryModel(BaseModel):
    category: str = Field(description="Expense category (e.g. Accommodation, Transport, Food)")
    amount: float = Field(description="Estimated cost in INR")
    description: str = Field(description="Brief explanation of what this covers")

class BudgetAgentResponse(BaseModel):
    categories: List[BudgetCategoryModel] = Field(description="Breakdown of expense categories")
    total_estimated: float = Field(description="Sum of all categories in INR")
    currency: str = Field(description="Currency code (should be INR)")
    status: str = Field(description="Status of the budget (e.g. Within Budget, Optimized to Budget)")

from google.adk import Agent

class BudgetAgent:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        
        # Check for placeholder or empty keys
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            self.has_api_key = False
            logger.warning(
                f"BudgetAgent: GEMINI_API_KEY is not configured. Key value: '{self.api_key}'. "
                f"Falling back to mock mode."
            )
        else:
            self.has_api_key = True
            masked_key = self.api_key[:5] + "..." if len(self.api_key) > 5 else "..."
            logger.info(f"BudgetAgent: Gemini API Key successfully loaded (Masked: {masked_key})")
            
        # Lightweight ADK agent definition
        self.adk_agent = Agent(
            name="BudgetAgent",
            description="Calculates transport costs and stay budgets.",
            tools=[estimate_budget]
        )
        
    def estimate(self, destination: str, days: int, max_budget: float, origin: str = "Bangalore") -> Dict[str, Any]:
        """
        Executes budget estimation and cost breakdown.
        """
        logger.info(f"BudgetAgent: Estimating budget for '{destination}' (days={days}, limit=₹{max_budget})")
        return estimate_budget(destination, days, max_budget, origin)
