from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import os
from dotenv import load_dotenv
from typing import Optional
import re
from requests_oauthlib import OAuth1Session

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Twitter API v2 endpoint
TWITTER_API_URL = "https://api.twitter.com/2/tweets"

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

def clean_text(text: str) -> str:
    # Remove special characters and extra spaces
    text = re.sub(r'[^\w\s#@]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

async def generate_twitter_summary(article_url: str, title: str, description: str) -> str:
    try:
        # Clean the title and description
        clean_title = clean_text(title)
        
        # Extract relevant hashtags
        hashtags = []
        if 'AI' in title or 'ai' in title:
            hashtags.append('#AI')
        if 'tech' in title.lower():
            hashtags.append('#Tech')
        if 'nvidia' in title.lower():
            hashtags.append('#Nvidia')
        
        # Create a summary that includes the title and hashtags
        summary = f"{clean_title}"
        
        # Add URL
        summary += f"\n{article_url}"
        
        # Add hashtags
        if hashtags:
            summary += f"\n{' '.join(hashtags)}"
        
        # Ensure the summary is under 280 characters
        if len(summary) > 280:
            summary = summary[:277] + "..."
            
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

@app.post("/process-news")
async def process_news():
    # Prepare the news API request
    news_api_url = "https://ai-marketing-researcher.onrender.com/fetch-news"
    news_payload = {
        "q": "ai agents",
        "from": "2024-12-12",
        "sortBy": "popularity",
        "searchIn": "title,description",
        "language": "en"
    }

    try:
        # Make request to news API
        async with httpx.AsyncClient() as client:
            response = await client.post(news_api_url, json=news_payload)
            response.raise_for_status()
            news_data = response.json()

            # Generate Twitter summary
            twitter_summary = await generate_twitter_summary(
                news_data["url"],
                news_data["title"],
                news_data["description"]
            )

            # Post to Twitter
            tweet_result = await post_to_twitter(twitter_summary)

            return {
                "news_article": news_data,
                "twitter_summary": twitter_summary,
                "tweet_details": tweet_result
            }

    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Error fetching news: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
