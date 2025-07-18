from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Stock Analysis Platform"
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=True)
    
    # Database
    MONGODB_URI: str = Field(default="mongodb://localhost:27017")
    DATABASE_NAME: str = Field(default="stock_analysis")
    
    # Authentication
    SECRET_KEY: str = Field(min_length=32)
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)
    
    # CORS
    CORS_ORIGINS: List[str] = Field(default=["http://localhost:3000"])
    ALLOWED_HOSTS: List[str] = Field(default=["localhost", "127.0.0.1"])
    
    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379")
    
    # External APIs
    KITE_API_KEY: Optional[str] = None
    KITE_API_SECRET: Optional[str] = None
    ALPHA_VANTAGE_API_KEY: Optional[str] = None
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60)
    
    # WebSocket
    WEBSOCKET_PING_INTERVAL: int = Field(default=30)
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()