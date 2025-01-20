"""Twitter API integration service."""
import os
from requests_oauthlib import OAuth1Session
import logging
from config import TWITTER_API_URL

logger = logging.getLogger(__name__)

def post_to_twitter(tweet_text: str) -> tuple[str, str]:
    """Post a tweet to Twitter.
    
    Returns:
        tuple: (tweet_id, tweet_url)
    """
    # Get Twitter credentials from environment
    consumer_key = os.getenv("TWITTER_CONSUMER_KEY")
    consumer_secret = os.getenv("TWITTER_CONSUMER_SECRET")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
    
    if not all([consumer_key, consumer_secret, access_token, access_token_secret]):
        raise ValueError("Missing Twitter API credentials in environment variables")
    
    # Create OAuth1 session
    twitter = OAuth1Session(
        consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=access_token,
        resource_owner_secret=access_token_secret
    )
    
    try:
        # Create tweet payload
        payload = {"text": tweet_text}
        
        # Make request to create tweet
        response = twitter.post(TWITTER_API_URL, json=payload)
        response.raise_for_status()
        
        # Parse response
        json_response = response.json()
        tweet_id = json_response["data"]["id"]
        tweet_url = f"https://twitter.com/i/web/status/{tweet_id}"
        
        logger.info(f"Successfully posted tweet: {tweet_url}")
        return tweet_id, tweet_url
        
    except Exception as e:
        logger.error(f"Error posting to Twitter: {str(e)}")
        raise
