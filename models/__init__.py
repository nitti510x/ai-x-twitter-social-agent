"""Database models and session management."""
from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
from config import SQLALCHEMY_DATABASE_URL, DATABASE_ARGS

Base = declarative_base()

class PendingPost(Base):
    """Model for storing pending Twitter posts."""
    __tablename__ = "pending_posts"
    
    id = Column(Integer, primary_key=True, index=True)
    tweet_text = Column(String)
    article_url = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, default="pending")  # pending, approved, rejected
    posted_tweet_id = Column(String, nullable=True)

# Database setup
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=DATABASE_ARGS)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

def get_db():
    """Dependency for database session management."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
