"""Configuration management using Pydantic BaseSettings.

This module provides comprehensive settings management for the AI Task Orchestrator
application, including database configuration, API keys, JWT settings, and model
configurations. All settings can be configured via environment variables.
"""

from typing import List, Optional
from pydantic import BaseSettings, validator, Field
import os


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Project Information
    PROJECT_NAME: str = Field(
        default="AI Task Orchestrator",
        description="Name of the project"
    )
    PROJECT_DESCRIPTION: str = Field(
        default="Advanced AI-powered task management system with intelligent prioritization, natural language processing, and automated workflow orchestration",
        description="Description of the project"
    )
    VERSION: str = Field(
        default="1.0.0",
        description="Application version"
    )
    
    # Server Configuration
    HOST: str = Field(
        default="0.0.0.0",
        description="Host address for the server"
    )
    PORT: int = Field(
        default=8000,
        description="Port number for the server"
    )
    DEBUG: bool = Field(
        default=True,
        description="Enable debug mode"
    )
    
    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:8000",
            "http://localhost:8080",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8000",
            "http://127.0.0.1:8080"
        ],
        description="List of allowed CORS origins"
    )
    
    # Database Configuration
    DATABASE_URL: str = Field(
        default="postgresql://user:password@localhost:5432/ai_task_orchestrator",
        description="PostgreSQL database connection URL"
    )
    
    # Redis Configuration
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for caching and task queue"
    )
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = Field(
        default="",
        description="OpenAI API key for AI features"
    )
    
    # JWT Configuration
    JWT_SECRET_KEY: str = Field(
        default="your-secret-key-change-this-in-production",
        description="Secret key for JWT token encoding/decoding"
    )
    JWT_ALGORITHM: str = Field(
        default="HS256",
        description="Algorithm used for JWT encoding"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="Access token expiration time in minutes"
    )
    
    # Model Configuration
    AI_MODEL_NAME: str = Field(
        default="gpt-4",
        description="Default OpenAI model for AI tasks"
    )
    AI_MODEL_TEMPERATURE: float = Field(
        default=0.7,
        description="Temperature setting for AI model responses",
        ge=0.0,
        le=2.0
    )
    AI_MODEL_MAX_TOKENS: int = Field(
        default=2000,
        description="Maximum tokens for AI model responses",
        ge=1,
        le=8000
    )
    AI_MODEL_TOP_P: float = Field(
        default=1.0,
        description="Top P sampling parameter",
        ge=0.0,
        le=1.0
    )
    AI_MODEL_FREQUENCY_PENALTY: float = Field(
        default=0.0,
        description="Frequency penalty for AI responses",
        ge=-2.0,
        le=2.0
    )
    AI_MODEL_PRESENCE_PENALTY: float = Field(
        default=0.0,
        description="Presence penalty for AI responses",
        ge=-2.0,
        le=2.0
    )
    
    # Task Processing Configuration
    MAX_TASK_QUEUE_SIZE: int = Field(
        default=1000,
        description="Maximum number of tasks in queue",
        ge=1
    )
    TASK_TIMEOUT_SECONDS: int = Field(
        default=300,
        description="Timeout for task processing in seconds",
        ge=1
    )
    MAX_RETRIES: int = Field(
        default=3,
        description="Maximum number of retries for failed tasks",
        ge=0
    )
    
    # Logging Configuration
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level"
    )
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log message format"
    )
    
    @validator("ALLOWED_ORIGINS", pre=True)
    def parse_allowed_origins(cls, v):
        """Parse ALLOWED_ORIGINS from environment variable."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("DATABASE_URL")
    def validate_database_url(cls, v):
        """Validate database URL format."""
        if not v.startswith(("postgresql://", "postgres://")):
            raise ValueError("DATABASE_URL must be a valid PostgreSQL connection string")
        return v
    
    @validator("REDIS_URL")
    def validate_redis_url(cls, v):
        """Validate Redis URL format."""
        if not v.startswith("redis://"):
            raise ValueError("REDIS_URL must be a valid Redis connection string")
        return v
    
    @validator("JWT_SECRET_KEY")
    def validate_jwt_secret(cls, v):
        """Validate JWT secret key."""
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters long for security")
        return v
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        
        # Allow environment variable override
        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_secret_settings,
        ):
            return (
                env_settings,
                init_settings,
                file_secret_settings,
            )


# Create global settings instance
settings = Settings()


# Export commonly used settings
__all__ = [
    "Settings",
    "settings",
]
