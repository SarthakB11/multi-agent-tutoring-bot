"""
MongoDB database utility for the Multi-Agent AI Tutoring System.
"""
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie, Document
from pydantic import Field
import logging

from src.config.settings import MONGODB_URI, MONGODB_DATABASE

logger = logging.getLogger(__name__)

# Define Beanie document models
class ChatMessage(Document):
    """Chat message document model."""
    user_id: str
    content: str
    role: str = "user"  # "user" or "assistant"
    timestamp: Optional[float] = None
    
    class Settings:
        name = "chat_messages"

class UserSession(Document):
    """User session document model."""
    user_id: str
    session_id: str
    active: bool = True
    messages: List[str] = []  # List of message IDs
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Settings:
        name = "user_sessions"

class AgentInteraction(Document):
    """Agent interaction document model."""
    session_id: str
    agent_name: str
    query: str
    response: str
    confidence: float
    tools_used: List[str] = []
    
    class Settings:
        name = "agent_interactions"

# MongoDB client instance
mongodb_client: Optional[AsyncIOMotorClient] = None

@asynccontextmanager
async def get_database():
    """
    Context manager for database connection.
    """
    global mongodb_client
    
    # Create client if it doesn't exist
    if mongodb_client is None:
        logger.info(f"Connecting to MongoDB at {MONGODB_URI}")
        mongodb_client = AsyncIOMotorClient(MONGODB_URI)
        
        # Initialize Beanie with the document models
        await init_beanie(
            database=mongodb_client[MONGODB_DATABASE],
            document_models=[ChatMessage, UserSession, AgentInteraction]
        )
        
        # Test connection
        try:
            # The ping command is lightweight and doesn't require auth
            await mongodb_client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
    
    try:
        yield mongodb_client[MONGODB_DATABASE]
    finally:
        # Connection will be closed when the application shuts down
        pass

async def close_mongodb_connection():
    """
    Close MongoDB connection.
    """
    global mongodb_client
    if mongodb_client is not None:
        logger.info("Closing MongoDB connection")
        mongodb_client.close()
        mongodb_client = None
