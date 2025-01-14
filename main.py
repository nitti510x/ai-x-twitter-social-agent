from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
import httpx
import os
from dotenv import load_dotenv
from typing import Optional, List
import re
from requests_oauthlib import OAuth1Session
import logging
from sqlalchemy.orm import Session
from models import get_db, PendingPost, PendingPostResponse, PostApproval

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

# Twitter API v2 endpoint
TWITTER_API_URL = "https://api.twitter.com/2/tweets"

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
    'cybersecurity': '#Cybersecurity',
    'nvidia': '#Nvidia',
    'openai': '#OpenAI',
    'microsoft': '#Microsoft',
    'google': '#Google',
    'apple': '#Apple',
    'tesla': '#Tesla',
    'startup': '#Startup',
    'tech': '#Tech'
}

class NewsRequest(BaseModel):
    q: str
    from_date: str
    sortBy: str
    searchIn: str
    language: str

class NewsResponse(BaseModel):
    source: str
    title: str
    description: str
    url: str
    urlToImage: Optional[str]
    publishedAt: str

class PostRequest(BaseModel):
    q: str = Field(..., description="Search query for news articles")
    from_: str = Field(..., alias="from", description="Start date for news search", example="2025-01-10")
    sortBy: str = Field("popularity", description="Sort order for news articles")
    searchIn: str = Field("title,description", description="Where to search for the query")
    language: str = Field("en", description="Language of news articles")

    class Config:
        schema_extra = {
            "example": {
                "q": "ai agents",
                "from": "2025-01-10",
                "sortBy": "popularity",
                "searchIn": "title,description",
                "language": "en"
            }
        }
        allow_population_by_field_name = True

class TwitterResponse(BaseModel):
    tweet_id: str
    tweet_url: str

    class Config:
        schema_extra = {
            "example": {
                "tweet_id": "1234567890",
                "tweet_url": "https://twitter.com/i/web/status/1234567890"
            }
        }

class PendingPostResponse(BaseModel):
    id: int
    tweet_text: str
    article_url: str
    status: str
    posted_tweet_id: Optional[str]

    class Config:
        orm_mode = True

class PostApproval(BaseModel):
    approved: bool

def clean_text(text: str) -> str:
    """Clean and normalize text."""
    # Remove special characters except periods and basic punctuation
    text = re.sub(r'[^\w\s.!?,]', ' ', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Remove multiple periods
    text = re.sub(r'\.{2,}', '.', text)
    return text

def get_first_sentence(text: str) -> str:
    """Extract the first sentence from text."""
    # Simple sentence splitting on common endings
    for end in ['. ', '! ', '? ']:
        if end in text:
            return text.split(end)[0] + end.strip()
    return text

def find_hashtags(text: str) -> list[str]:
    """Find relevant hashtags based on text content."""
    hashtags = set()
    text_lower = text.lower()
    
    # Check for tech keywords
    for keyword, hashtag in TECH_KEYWORDS.items():
        if keyword in text_lower:
            hashtags.add(hashtag)
    
    # Get words that might be good hashtags (longer than 3 letters)
    words = [word for word in text_lower.split() if len(word) > 3]
    for word in words:
        # Remove any non-letter characters
        word = re.sub(r'[^a-z]', '', word)
        if word and word not in TECH_KEYWORDS and len(word) > 3:
            hashtag = '#' + word.capitalize()
            hashtags.add(hashtag)
    
    # Limit to top 4 most relevant hashtags
    return list(hashtags)[:4]

def create_summary(title: str, description: str, max_length: int = 180) -> str:
    """Create a concise summary from title and description."""
    # Clean the texts
    clean_title = clean_text(title)
    clean_desc = clean_text(description)
    
    # Get the first sentence of the description
    first_desc_sentence = get_first_sentence(clean_desc)
    
    # If title ends with period, remove it for better flow
    if clean_title.endswith('.'):
        clean_title = clean_title[:-1]
    
    # Create summary variants and choose the best one
    variants = [
        f"{clean_title}: {first_desc_sentence}",
        f"{clean_title}",
        f"{first_desc_sentence}"
    ]
    
    # Choose the longest variant that fits within max_length
    for variant in variants:
        if len(variant) <= max_length:
            return variant
    
    # If no variant fits, truncate the first one
    return variants[0][:max_length-3] + "..."

def generate_twitter_summary(article_url: str, title: str, description: str) -> str:
    try:
        # Create main summary
        main_summary = create_summary(title, description)
        
        # Find relevant hashtags
        hashtags = find_hashtags(title + " " + description)
        
        # Combine components
        components = [
            main_summary,
            article_url,
            " ".join(hashtags)
        ]
        
        # Join components and ensure total length is under 280 characters
        summary = "\n\n".join(components)
        if len(summary) > 280:
            # If too long, shorten the main summary
            excess = len(summary) - 280 + 3  # +3 for ellipsis
            main_summary = main_summary[:-excess] + "..."
            summary = "\n\n".join([main_summary, article_url, " ".join(hashtags)])
        
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")

async def post_to_twitter(tweet_text: str) -> dict:
    try:
        # Create OAuth1 session
        twitter = OAuth1Session(
            client_key=os.getenv("TWITTER_API_KEY"),
            client_secret=os.getenv("TWITTER_API_SECRET"),
            resource_owner_key=os.getenv("TWITTER_ACCESS_TOKEN"),
            resource_owner_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        )
        
        # Prepare tweet data
        data = {
            "text": tweet_text
        }
        
        # Post to Twitter API v2
        response = twitter.post(TWITTER_API_URL, json=data)
        response.raise_for_status()
        tweet_data = response.json()
        tweet_id = tweet_data['data']['id']
        
        return {
            "tweet_id": tweet_id,
            "tweet_url": f"https://twitter.com/i/web/status/{tweet_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error posting to Twitter: {str(e)}")

@app.post("/generate", response_model=PendingPostResponse)
async def process_news(request: PostRequest, db: Session = Depends(get_db)):
    """Generate a tweet for approval based on news search."""
    try:
        async with httpx.AsyncClient() as client:
            news_api_key = os.getenv("NEWS_API_KEY")
            if not news_api_key:
                raise HTTPException(status_code=500, detail="NEWS_API_KEY not configured")
            
            # Convert the request model to dict and handle the "from" field
            params = request.model_dump(by_alias=True)
            params["apiKey"] = news_api_key
            
            response = await client.get(
                "https://newsapi.org/v2/everything",
                params=params
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="News API request failed")
            
            data = response.json()
            if not data.get("articles"):
                raise HTTPException(status_code=404, detail="No articles found")
            
            article = data["articles"][0]
            tweet_text = generate_twitter_summary(
                article["url"],
                article["title"],
                article.get("description", "")
            )
            
            # Create pending post in database
            pending_post = PendingPost(
                tweet_text=tweet_text,
                article_url=article["url"]
            )
            db.add(pending_post)
            db.commit()
            db.refresh(pending_post)
            
            return pending_post
            
    except Exception as e:
        logger.error(f"Error processing news: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pending", response_model=List[PendingPostResponse])
async def get_pending_posts(db: Session = Depends(get_db)):
    """Get all pending posts."""
    return db.query(PendingPost).filter(PendingPost.status == "pending").all()

@app.post("/approve/{post_id}", response_model=PendingPostResponse)
async def approve_post(post_id: int, approval: PostApproval, db: Session = Depends(get_db)):
    """Approve or reject a pending post."""
    post = db.query(PendingPost).filter(PendingPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post.status != "pending":
        raise HTTPException(status_code=400, detail=f"Post is already {post.status}")
    
    if approval.approved:
        # Post to Twitter
        tweet_response = post_to_twitter(post.tweet_text)
        post.posted_tweet_id = tweet_response["tweet_id"]
        post.status = "approved"
    else:
        post.status = "rejected"
    
    db.commit()
    db.refresh(post)
    return post

@app.post("/post-direct", response_model=TwitterResponse)
async def post_direct(request: PostRequest):
    """Directly post to Twitter without approval workflow."""
    try:
        async with httpx.AsyncClient() as client:
            news_api_key = os.getenv("NEWS_API_KEY")
            if not news_api_key:
                raise HTTPException(status_code=500, detail="NEWS_API_KEY not configured")
            
            # Convert the request model to dict and handle the "from" field
            params = request.model_dump(by_alias=True)
            params["apiKey"] = news_api_key
            
            response = await client.get(
                "https://newsapi.org/v2/everything",
                params=params
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="News API request failed")
            
            data = response.json()
            if not data.get("articles"):
                raise HTTPException(status_code=404, detail="No articles found")
            
            article = data["articles"][0]
            tweet_text = generate_twitter_summary(
                article["url"],
                article["title"],
                article.get("description", "")
            )
            
            # Post directly to Twitter
            return await post_to_twitter(tweet_text)
            
    except Exception as e:
        logger.error(f"Error processing news: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
