from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TaskBase(BaseModel):
    """Base schema for Task with common attributes."""
    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, description="Detailed task description")
    priority: Optional[str] = Field("medium", description="Task priority: low, medium, high")
    status: Optional[str] = Field("pending", description="Task status: pending, in_progress, completed, failed")


class TaskCreate(TaskBase):
    """Schema for creating a new task."""
    pass


class TaskUpdate(BaseModel):
    """Schema for updating an existing task. All fields are optional."""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, description="Detailed task description")
    priority: Optional[str] = Field(None, description="Task priority: low, medium, high")
    status: Optional[str] = Field(None, description="Task status: pending, in_progress, completed, failed")


class TaskResponse(TaskBase):
    """Schema for task response with all attributes including database fields."""
    id: int = Field(..., description="Unique task identifier")
    created_at: datetime = Field(..., description="Task creation timestamp")
    updated_at: datetime = Field(..., description="Task last update timestamp")
    ai_id: Optional[int] = Field(None, description="Associated AI agent ID")

    class Config:
        from_attributes = True


class TaskWithAI(TaskResponse):
    """Schema for task response with associated AI agent details."""
    ai_name: Optional[str] = Field(None, description="Name of the associated AI agent")
    ai_model: Optional[str] = Field(None, description="AI model being used")

    class Config:
        from_attributes = True
