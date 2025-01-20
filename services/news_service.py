"""News API integration service."""
import os
import httpx
import logging
from schemas import NewsRequest, NewsResponse
from utils.text_processing import generate_twitter_summary

logger = logging.getLogger(__name__)

async def fetch_news(request: NewsRequest) -> list[NewsResponse]:
    """Fetch news articles from News API."""
    news_api_key = os.getenv("NEWS_API_KEY")
    if not news_api_key:
        raise ValueError("Missing NEWS_API_KEY in environment variables")
    
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": request.q,
        "from": request.from_date,
        "sortBy": request.sortBy,
        "searchIn": request.searchIn,
        "language": request.language,
        "apiKey": news_api_key
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            articles = data.get("articles", [])
            
            return [
                NewsResponse(
                    source=article["source"]["name"],
                    title=article["title"],
                    description=article["description"],
                    url=article["url"],
                    urlToImage=article.get("urlToImage"),
                    publishedAt=article["publishedAt"]
                )
                for article in articles
            ]
    except Exception as e:
        logger.error(f"Error fetching news: {str(e)}")
        raise

def process_article(article: NewsResponse) -> str:
    """Process a news article and generate a tweet-ready summary."""
    return generate_twitter_summary(
        article_url=article.url,
        title=article.title,
        description=article.description
    )
