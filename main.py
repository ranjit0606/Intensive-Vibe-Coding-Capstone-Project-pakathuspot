import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Import Coordinator
from agents.coordinator import TravelCoordinatorAgent

# Load environment variables
load_dotenv(override=True)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pakathuspot.api")

app = FastAPI(
    title="PakathuSpot API",
    description="Multi-Agent Travel Companion Backend",
    version="1.0.0"
)

# Enable CORS for frontend development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for capstone demo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Coordinator
coordinator = TravelCoordinatorAgent()

class ChatRequest(BaseModel):
    message: str

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Handles conversational travel queries, runs the multi-agent pipeline, and returns a full plan.
    """
    logger.info(f"Received API chat prompt: '{request.message}'")
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Query message cannot be empty")
        
    try:
        plan = coordinator.plan_trip(request.message)
        return plan
    except Exception as e:
        logger.exception("Error in Travel Coordinator planning pipeline")
        raise HTTPException(status_code=500, detail=f"Planning pipeline failed: {str(e)}")

@app.get("/api/health")
async def health_check():
    """
    Checks health status of backend and checks API key integration.
    """
    api_key = os.getenv("GEMINI_API_KEY", "")
    has_api_key = api_key not in ["", "your_gemini_api_key_here"]
    return {
        "status": "healthy",
        "gemini_api_key_configured": has_api_key,
        "mcp_server": "active (via tools/mcp_server.py)"
    }

# Mount static files if frontend has been built
frontend_dist_path = os.path.join(os.path.dirname(__file__), "frontend", "dist")

if os.path.exists(frontend_dist_path):
    logger.info(f"Serving static frontend files from: {frontend_dist_path}")
    app.mount("/", StaticFiles(directory=frontend_dist_path, html=True), name="frontend")
else:
    logger.warning(f"Frontend dist directory not found at: {frontend_dist_path}. API endpoints are active, but index page will serve API info.")
    
    @app.get("/")
    async def index_fallback():
        return {
            "name": "PakathuSpot Multi-Agent Travel Assistant API",
            "status": "running",
            "api_endpoints": {
                "chat": "/api/chat (POST)",
                "health": "/api/health (GET)"
            },
            "info": "To view the modern frontend, run the Vite dev server in pakathuspot/frontend, or build it using npm run build."
        }
