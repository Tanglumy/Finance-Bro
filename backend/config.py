"""
Configuration management for Finance-Bro backend
"""
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5")
    
    # Other API Keys
    ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
    POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
    FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./finance_bro.db")
    
    # Server Configuration
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # WebSocket Configuration
    WS_HEARTBEAT_INTERVAL = int(os.getenv("WS_HEARTBEAT_INTERVAL", "30"))
    WS_MAX_CONNECTIONS = int(os.getenv("WS_MAX_CONNECTIONS", "100"))
    
    # Cache Configuration
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))
    
    # Security
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "development-secret-key")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required. Please set it in .env file")
        
        # Validate API key format
        if not cls.OPENAI_API_KEY.startswith("sk-"):
            raise ValueError("Invalid OPENAI_API_KEY format")
        
        return True

# Create global config instance
config = Config()