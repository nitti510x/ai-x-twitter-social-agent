"""News API integration service."""
import httpx
import logging
from fastapi import HTTPException
from schemas import NewsRequest, NewsResponse
from utils.text_processing import generate_twitter_summary

logger = logging.getLogger(__name__)

async def fetch_news(request: NewsRequest) -> list[NewsResponse]:
    """Fetch news articles from AI Marketing Researcher API."""
    url = "https://ai-marketing-researcher.onrender.com/fetch-news"
    
    payload = {
        "q": request.q,
        "from": request.from_date,
        "sortBy": request.sortBy,
        "searchIn": request.searchIn,
        "language": request.language
    }
    
    logger.info(f"Making request to AI Marketing Researcher API")
    logger.info(f"Request payload: {payload}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            logger.info(f"API Status Code: {response.status_code}")
            
            if response.status_code != 200:
                error_msg = f"API error: {response.text}"
                logger.error(error_msg)
                raise HTTPException(status_code=response.status_code, detail=error_msg)
            
            # Log raw response
            raw_response = response.text
            logger.info(f"Raw API response: {raw_response}")
            
            data = response.json()
            logger.info(f"Parsed response data: {data}")
            
            # The API returns a single article, not a list
            if not isinstance(data, dict):
                logger.error(f"Unexpected response format: {data}")
                raise HTTPException(status_code=500, detail="Unexpected response format from API")
            
            # Convert single article response to NewsResponse
            if not all(k in data for k in ["source", "title", "description", "url", "publishedAt"]):
                logger.error(f"Missing required fields in article: {data}")
                raise HTTPException(status_code=500, detail="Article missing required fields")
                
            article = NewsResponse(
                source=data["source"],
                title=data["title"],
                description=data["description"],
                url=data["url"],
                urlToImage=data.get("urlToImage"),
                publishedAt=data["publishedAt"]
            )
            
            logger.info(f"Successfully processed article: {article.title}")
            return [article]  # Return as list for compatibility
            
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error fetching news: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

def process_article(article: NewsResponse) -> str:
    """Process a news article and generate a tweet-ready summary."""
    if not article.title or not article.description:
        raise ValueError("Article must have both title and description")
    
    logger.info(f"Processing article: {article.title}")
    return generate_twitter_summary(
        article_url=article.url,
        title=article.title,
        description=article.description
    )
