# backend/app/config.py
import os
from pydantic_settings import BaseSettings
from typing import Optional, List, Any

class Settings(BaseSettings):
    """Application settings."""
    
    # Application name
    APP_NAME: str = "Colliers - Paralegal API"
    
    # Development settings
    DEBUG: bool = False
    DEV_MODE: bool = False
    
    # API prefix - set to / when using subdomains, /api when using paths
    API_PREFIX: str = "/"  # Default root path

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://colliers_user:colliers_pass@localhost/colliers_legal"
    
    # Authentication
    CLERK_SECRET_KEY: Optional[str] = None
    CLERK_PEM_PUBLIC_KEY: Optional[str] = None
    CLERK_PEM_PUBLIC_KEY_PATH: Optional[str] = "/app/clerk_pub.pem"
    CLERK_ISSUER: Optional[str] = None  # Optional - only used for additional JWT validation
    CLERK_WHITELIST_EMAIL: str = "" # Comma-separated list of emails or domains (*.example.com)
    
    # LLM Provider Configuration
    LLM_PROVIDER: str = "openai"  # openai or anthropic
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-opus-20240229"
    
    # Legal Rules Path
    LEGAL_RULES_PATH: str = "/app/data/legal-rules"
    
    # CORS - Use a string for now, we'll process it later
    CORS_ORIGINS_STR: str = "http://localhost:3000,https://legal-colliers.dev.morphing.ai"
    
    # Hard-coded default values
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "https://legal-colliers.dev.morphing.ai"]
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }
    
    def model_post_init(self, __context: Any) -> None:
        """Process settings after initialization."""
        # Override DEBUG and DEV_MODE from environment
        self.DEBUG = os.getenv("DEBUG", "false").lower() == "true"
        self.DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"
        
        # Process CORS origins from environment if available
        cors_env = os.getenv("CORS_ORIGINS_STR", "")
        if cors_env:
            self.CORS_ORIGINS = [origin.strip() for origin in cors_env.split(",") if origin.strip()]

settings = Settings()