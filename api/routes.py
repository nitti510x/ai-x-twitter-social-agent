"""API routes for the Twitter Social Agent."""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import logging
from typing import List

from models import get_db, PendingPost
from schemas import (
    PostRequest,
    TwitterResponse,
    PendingPostResponse,
    PostApproval,
    NewsRequest,
    NewsResponse
)
from services.news_service import fetch_news, process_article
from services.twitter_service import post_to_twitter

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/process-news", response_model=PendingPostResponse)
async def process_news(request: PostRequest, db: Session = Depends(get_db)):
    """Generate a tweet for approval based on news search."""
    try:
        # Convert PostRequest to NewsRequest
        news_request = NewsRequest(
            q=request.q,
            from_date=request.from_,
            sortBy=request.sortBy,
            searchIn=request.searchIn,
            language=request.language
        )
        
        logger.info(f"Processing news request: {news_request}")
        
        # Fetch news articles
        articles = await fetch_news(news_request)
        if not articles:
            logger.error("No articles returned from News API")
            raise HTTPException(
                status_code=404,
                detail="No news articles found matching your criteria"
            )
        
        # Process the first article
        article = articles[0]
        logger.info(f"Processing article: {article.title}")
        
        tweet_text = process_article(article)
        if not tweet_text:
            logger.error("Failed to generate tweet text")
            raise HTTPException(
                status_code=500,
                detail="Failed to generate tweet text from article"
            )
        
        # Create pending post
        db_post = PendingPost(
            tweet_text=tweet_text,
            article_url=article.url
        )
        db.add(db_post)
        db.commit()
        db.refresh(db_post)
        
        logger.info(f"Created pending post: {db_post.id}")
        return db_post
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in process_news: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process news request: {str(e)}"
        )

@router.get("/pending-posts", response_model=List[PendingPostResponse])
def get_pending_posts(db: Session = Depends(get_db)):
    """Get all pending posts."""
    return db.query(PendingPost).all()

@router.post("/approve-post/{post_id}", response_model=TwitterResponse)
def approve_post(post_id: int, approval: PostApproval, db: Session = Depends(get_db)):
    """Approve or reject a pending post."""
    post = db.query(PendingPost).filter(PendingPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if not approval.approved:
        post.status = "rejected"
        db.commit()
        return {"tweet_id": "", "tweet_url": ""}
    
    try:
        # Post to Twitter
        tweet_response = post_to_twitter(post.tweet_text)
        
        # Update post status
        post.status = "posted"
        post.posted_tweet_id = tweet_response.tweet_id
        db.commit()
        
        return tweet_response
        
    except Exception as e:
        logger.error(f"Error posting to Twitter: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to post to Twitter: {str(e)}"
        )

@router.post("/post-direct", response_model=TwitterResponse)
async def post_direct(request: PostRequest):
    """Directly post to Twitter without approval workflow."""
    try:
        # Convert PostRequest to NewsRequest
        news_request = NewsRequest(
            q=request.q,
            from_date=request.from_,
            sortBy=request.sortBy,
            searchIn=request.searchIn,
            language=request.language
        )
        
        # Fetch and process news
        articles = await fetch_news(news_request)
        if not articles:
            raise HTTPException(status_code=404, detail="No news articles found")
        
        article = articles[0]
        tweet_text = process_article(article)
        
        # Post directly to Twitter
        return post_to_twitter(tweet_text)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in direct post: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to post directly: {str(e)}"
        )
