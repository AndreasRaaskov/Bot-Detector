# main.py - FastAPI application entry point for the Bot Detector API
# This file sets up our web server that will handle HTTP requests for bot analysis

# Import FastAPI - this is our web framework for building APIs
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional
import uvicorn

# Import our custom modules
from bot_detector import BotDetector
from models import UserAnalysisRequest, UserAnalysisResponse
from config import Config

# Create the FastAPI application instance
# This is the main object that will handle all our web requests
app = FastAPI(
    title="Bot Detector API",
    description="API for detecting bots on Bluesky using multiple analysis methods",
    version="1.0.0"
)

# Add CORS middleware to allow frontend applications to call our API
# CORS (Cross-Origin Resource Sharing) allows web browsers to make requests
# from one domain (our frontend) to another domain (our backend API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from any origin (for development)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Initialize configuration and create bot detector instance
# Load configuration from config.json and environment variables
config = Config()

# Create a single instance of our bot detector that will be shared across requests
# This pattern is called a "singleton" and helps us reuse connections and configurations
bot_detector = BotDetector(config)

# Define API endpoints (routes) that clients can call

@app.get("/")
async def root():
    """
    Root endpoint - returns a simple message to confirm the API is running
    This is useful for basic health checks and testing
    """
    return {"message": "Bot Detector API is running"}

@app.get("/health")
async def health_check():
    """
    Health check endpoint - used by monitoring systems to verify the service is healthy
    This is a standard practice for production APIs
    """
    return {
        "status": "healthy", 
        "service": "bot-detector",
        "capabilities": {
            "bluesky_access": config.has_bluesky_credentials(),
            "llm_providers": list(config.get_llm_keys().keys())
        }
    }

@app.get("/config")
async def get_config():
    """
    Configuration summary endpoint - shows what capabilities are available
    This helps with debugging and setup verification
    Note: No sensitive data is exposed
    """
    return config.get_summary()

@app.options("/analyze")
async def analyze_preflight():
    """
    Handle CORS preflight requests for the analyze endpoint
    This allows browsers to make cross-origin POST requests to /analyze
    """
    return {"message": "OK"}

@app.post("/analyze", response_model=UserAnalysisResponse)
async def analyze_user(request: UserAnalysisRequest):
    """
    Main analysis endpoint - takes a Bluesky handle and returns bot detection scores
    
    Args:
        request: UserAnalysisRequest object containing the Bluesky handle to analyze
        
    Returns:
        UserAnalysisResponse: Contains all the bot detection scores and analysis results
        
    Raises:
        HTTPException: If there's an error during analysis (500 status code)
    """
    try:
        # Call our bot detector to analyze the user
        # This is where the main logic happens (we'll implement this next)
        result = await bot_detector.analyze_user(request.bluesky_handle)
        return result
    except Exception as e:
        # If anything goes wrong, return an HTTP error with details
        # This helps with debugging and provides useful error messages to clients
        raise HTTPException(status_code=500, detail=str(e))

# This block runs only when the file is executed directly (not imported)
# It starts the development server
if __name__ == "__main__":
    # uvicorn is an ASGI server that runs our FastAPI application
    # Use configuration values for host and port
    uvicorn.run(
        app, 
        host=config.api_host, 
        port=config.api_port,
        reload=config.debug_mode  # Auto-reload in debug mode
    )