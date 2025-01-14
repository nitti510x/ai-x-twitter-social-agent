from sqlalchemy import Column, Integer, String, DateTime, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
from typing import Optional
from pydantic import BaseModel

Base = declarative_base()

class PendingPost(Base):
    __tablename__ = "pending_posts"
    
    id = Column(Integer, primary_key=True, index=True)
    tweet_text = Column(String)
    article_url = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, default="pending")  # pending, approved, rejected
    posted_tweet_id = Column(String, nullable=True)

# Pydantic models for API
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

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./social_agent.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
