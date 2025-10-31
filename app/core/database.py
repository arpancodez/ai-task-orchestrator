from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool, QueuePool
from typing import AsyncGenerator
import logging
import os

logger = logging.getLogger(__name__)

# Database URL from environment variable
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://user:password@localhost:5432/ai_task_orchestrator"
)

# SQLAlchemy Base class for models
Base = declarative_base()

# Async engine with connection pooling
engine = None
SessionLocal = None


def get_engine_config():
    """Get engine configuration with proper connection pooling."""
    config = {
        "echo": os.getenv("SQL_ECHO", "false").lower() == "true",
        "future": True,
    }
    
    # Configure connection pool based on environment
    if os.getenv("TESTING", "false").lower() == "true":
        # Use NullPool for testing to avoid connection issues
        config["poolclass"] = NullPool
    else:
        # Production connection pooling settings
        config["poolclass"] = QueuePool
        config["pool_size"] = int(os.getenv("DB_POOL_SIZE", "10"))
        config["max_overflow"] = int(os.getenv("DB_MAX_OVERFLOW", "20"))
        config["pool_timeout"] = int(os.getenv("DB_POOL_TIMEOUT", "30"))
        config["pool_recycle"] = int(os.getenv("DB_POOL_RECYCLE", "3600"))
        config["pool_pre_ping"] = True  # Verify connections before use
    
    return config


async def init_db() -> None:
    """Initialize the database engine and session maker.
    
    This function should be called once at application startup.
    It creates the async engine and session maker with proper
    connection pooling and error handling.
    
    Raises:
        Exception: If database initialization fails
    """
    global engine, SessionLocal
    
    try:
        logger.info(f"Initializing database connection to {DATABASE_URL.split('@')[-1]}")
        
        # Create async engine with connection pooling
        engine_config = get_engine_config()
        engine = create_async_engine(DATABASE_URL, **engine_config)
        
        # Create session maker
        SessionLocal = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        
        # Test the connection
        async with engine.begin() as conn:
            await conn.run_sync(lambda _: None)
        
        logger.info("Database connection initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise


async def close_db() -> None:
    """Close the database connection and dispose of the engine.
    
    This function should be called at application shutdown to properly
    clean up database connections and resources.
    """
    global engine
    
    if engine is not None:
        try:
            logger.info("Closing database connection")
            await engine.dispose()
            logger.info("Database connection closed successfully")
        except Exception as e:
            logger.error(f"Error closing database connection: {str(e)}")
            raise
        finally:
            engine = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency function to get database session.
    
    This function should be used as a dependency in FastAPI routes
    to get a database session that is automatically closed after use.
    
    Yields:
        AsyncSession: An async database session
        
    Example:
        @app.get("/items")
        async def read_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    if SessionLocal is None:
        raise RuntimeError(
            "Database not initialized. Call init_db() at application startup."
        )
    
    session = SessionLocal()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"Database session error: {str(e)}")
        raise
    finally:
        await session.close()


async def create_tables() -> None:
    """Create all tables defined in SQLAlchemy models.
    
    This function should be called after init_db() if you want to
    create tables programmatically. In production, consider using
    Alembic migrations instead.
    
    Raises:
        RuntimeError: If database is not initialized
    """
    if engine is None:
        raise RuntimeError(
            "Database not initialized. Call init_db() first."
        )
    
    try:
        logger.info("Creating database tables")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create tables: {str(e)}")
        raise
