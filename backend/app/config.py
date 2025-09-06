# backend/app/config.py
import os
from pydantic_settings import BaseSettings
from typing import Optional, List, Any

class Settings(BaseSettings):
    """Application settings."""
    
    # Application name
    APP_NAME: str = "Morphing Digital Paralegal API"
    
    # Development settings
    DEBUG: bool = False
    DEV_MODE: bool = False
    
    # API prefix - set to / when using subdomains, /api when using paths
    API_PREFIX: str = "/api"  # Default to /api for path-based routing

    # Database
    DATABASE_URL: Optional[str] = None
    
    # Authentication
    CLERK_SECRET_KEY: Optional[str] = None
    CLERK_PEM_PUBLIC_KEY: Optional[str] = None
    CLERK_PEM_PUBLIC_KEY_PATH: Optional[str] = "/app/clerk_pub.pem"
    CLERK_ISSUER: Optional[str] = None  # Optional - only used for additional JWT validation
    CLERK_WHITELIST_EMAIL: str = "" # Comma-separated list of emails or domains (*.example.com)
    
    # LLM Provider Configuration
    LLM_PROVIDER: str = "azure_openai"  # azure_openai, openai, or anthropic
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_API_VERSION: str = "2024-02-15-preview"
    AZURE_OPENAI_DEPLOYMENT: Optional[str] = None
    AZURE_OPENAI_MODEL: Optional[str] = None
    
    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    
    # Anthropic Configuration
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-opus-20240229"
    
    # Legal Rules Path
    LEGAL_RULES_PATH: str = "/app/data/legal-rules"
    
    # CORS - Use a string for now, we'll process it later
    CORS_ORIGINS_STR: str = "http://localhost:3000,https://legal-colliers.dev.morphing.ai"
    
    # Hard-coded default values
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "https://legal-colliers.dev.morphing.ai"]
    
    model_config = {
        "env_file": "/app/.env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }
    
    def model_post_init(self, __context: Any) -> None:
        """Process settings after initialization."""
        # Validate DATABASE_URL is set
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable is required")
        
        # Process CORS origins from environment if available
        if self.CORS_ORIGINS_STR:
            self.CORS_ORIGINS = [origin.strip() for origin in self.CORS_ORIGINS_STR.split(",") if origin.strip()]
    
settings = Settings()