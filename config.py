"""Configuration settings for the AI Twitter Social Agent."""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Endpoints
TWITTER_API_URL = "https://api.twitter.com/2/tweets"

# Database settings
SQLALCHEMY_DATABASE_URL = "sqlite:///./social_agent.db"
DATABASE_ARGS = {"check_same_thread": False}

# Common tech keywords for hashtag generation
TECH_KEYWORDS = {
    'ai': '#AI',
    'artificial intelligence': '#AI',
    'machine learning': '#ML',
    'deep learning': '#DeepLearning',
    'neural network': '#NeuralNetworks',
    'data science': '#DataScience',
    'blockchain': '#Blockchain',
    'crypto': '#Crypto',
    'cryptocurrency': '#Crypto',
    'bitcoin': '#Bitcoin',
    'ethereum': '#Ethereum',
    'web3': '#Web3',
    'metaverse': '#Metaverse',
    'virtual reality': '#VR',
    'augmented reality': '#AR',
    'robotics': '#Robotics',
    'automation': '#Automation',
    'cloud': '#Cloud',
}

# API Configuration
PORT = int(os.getenv("PORT", 8000))
HOST = "0.0.0.0"
