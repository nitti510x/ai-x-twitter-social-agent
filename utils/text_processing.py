"""Text processing utilities for tweet generation."""
import re
from config import TECH_KEYWORDS

def clean_text(text: str) -> str:
    """Clean and normalize text."""
    if not text:
        return ""
    # Remove URLs
    text = re.sub(r'http\S+|www.\S+', '', text, flags=re.MULTILINE)
    # Remove special characters and extra whitespace
    text = re.sub(r'[^\w\s]', ' ', text)
    text = ' '.join(text.split())
    return text

def get_first_sentence(text: str) -> str:
    """Extract the first sentence from text."""
    if not text:
        return ""
    # Split on period followed by space or end of string
    sentences = re.split(r'\.(?:\s|$)', text)
    return sentences[0].strip() if sentences else ""

def find_hashtags(text: str) -> list[str]:
    """Find relevant hashtags based on text content."""
    if not text:
        return []
    
    text = text.lower()
    hashtags = set()
    
    # Look for exact matches
    for keyword, hashtag in TECH_KEYWORDS.items():
        if keyword in text:
            hashtags.add(hashtag)
    
    # Limit to 3 most relevant hashtags
    return list(hashtags)[:3]

def create_summary(title: str, description: str, max_length: int = 180) -> str:
    """Create a concise summary from title and description."""
    if not title:
        return ""
    
    # Clean the texts
    clean_title = clean_text(title)
    clean_desc = clean_text(description) if description else ""
    
    # Start with the title
    summary = clean_title
    
    # If there's room, add first sentence of description
    if clean_desc and len(summary) < max_length:
        first_sentence = get_first_sentence(clean_desc)
        if first_sentence and first_sentence.lower() not in clean_title.lower():
            remaining_length = max_length - len(summary) - 2  # 2 for ". "
            if len(first_sentence) <= remaining_length:
                summary += ". " + first_sentence
    
    return summary

def generate_twitter_summary(article_url: str, title: str, description: str) -> str:
    """Generate a tweet-ready summary with hashtags."""
    # Create initial summary
    summary = create_summary(title, description)
    
    # Find relevant hashtags
    hashtags = find_hashtags(summary)
    hashtag_text = " " + " ".join(hashtags) if hashtags else ""
    
    # Calculate available space for URL
    max_tweet_length = 280
    url_length = len(article_url) + 1  # +1 for space
    
    # Truncate summary if needed to fit URL and hashtags
    available_length = max_tweet_length - url_length - len(hashtag_text)
    if len(summary) > available_length:
        summary = summary[:available_length-3] + "..."
    
    # Combine all elements
    tweet_text = f"{summary} {article_url}{hashtag_text}"
    return tweet_text
