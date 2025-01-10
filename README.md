# News Article Summarizer API

This service fetches news articles and generates Twitter-ready summaries using GPT-4.

## Setup

1. Create a `.env` file in the root directory with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the service:
```bash
uvicorn main:app --reload
```

## API Endpoints

### POST /process-news

Fetches news articles about AI agents and generates a Twitter-ready summary using GPT-4.

#### Response Format:
```json
{
    "news_article": {
        "source": "string",
        "title": "string",
        "description": "string",
        "url": "string",
        "urlToImage": "string",
        "publishedAt": "string"
    },
    "twitter_summary": "string"
}
```

## Deployment

This application is designed to be deployed on render.com. Make sure to:

1. Set the OPENAI_API_KEY environment variable in your Render dashboard
2. Use Python 3.9+ as the runtime
3. Set the build command to: `pip install -r requirements.txt`
4. Set the start command to: `uvicorn main:app --host 0.0.0.0 --port $PORT`
