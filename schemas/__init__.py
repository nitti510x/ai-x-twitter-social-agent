"""Pydantic models for API request/response validation."""
from pydantic import BaseModel, Field
from typing import Optional
import datetime

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

class PendingPostCreate(BaseModel):
    tweet_text: str
    article_url: str

class PendingPostResponse(BaseModel):
    id: int
    tweet_text: str
    article_url: str
    created_at: datetime.datetime
    status: str
    posted_tweet_id: Optional[str] = None

    class Config:
        from_attributes = True

class PostApproval(BaseModel):
    approved: bool
    feedback: Optional[str] = None
