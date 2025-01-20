"""Main application entry point."""
from fastapi import FastAPI
import uvicorn
import logging
from dotenv import load_dotenv

from api.routes import router
from config import HOST, PORT

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Twitter Social Agent",
    description="An API that processes news articles and posts them to Twitter with relevant hashtags",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Register routes
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)
