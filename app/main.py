"""AI Task Orchestrator - Main Application

An advanced AI-powered task management system with intelligent
prioritization, natural language processing, and automated workflow orchestration.
"""

import asyncio
import logging
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.routes import tasks, projects, analytics, ai
from app.core.config import settings
from app.core.database import init_db, close_db
from app.services.ai_engine import AIEngine
from app.services.task_scheduler import TaskScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    logger.info("Starting AI Task Orchestrator...")
    await init_db()
    
    # Initialize AI Engine
    app.state.ai_engine = AIEngine()
    await app.state.ai_engine.initialize()
    
    # Initialize Task Scheduler
    app.state.scheduler = TaskScheduler(app.state.ai_engine)
    await app.state.scheduler.start()
    
    logger.info("AI Task Orchestrator started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Task Orchestrator...")
    await app.state.scheduler.stop()
    await close_db()
    logger.info("AI Task Orchestrator shut down successfully")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["tasks"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(ai.router, prefix="/api/v1/ai", tags=["ai"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to AI Task Orchestrator",
        "version": settings.VERSION,
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "ai_engine": "operational",
        "database": "connected"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
