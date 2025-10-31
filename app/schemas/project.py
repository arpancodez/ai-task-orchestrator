from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ProjectBase(BaseModel):
    """Base schema for Project with common attributes."""
    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    is_active: bool = Field(default=True, description="Whether the project is active")


class ProjectCreate(ProjectBase):
    """Schema for creating a new Project."""
    pass


class ProjectUpdate(BaseModel):
    """Schema for updating an existing Project."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    is_active: Optional[bool] = Field(None, description="Whether the project is active")


class ProjectResponse(ProjectBase):
    """Schema for Project response."""
    id: int = Field(..., description="Project ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class ProjectWithStats(ProjectResponse):
    """Schema for Project response with statistics."""
    total_tasks: int = Field(default=0, description="Total number of tasks in the project")
    completed_tasks: int = Field(default=0, description="Number of completed tasks")
    pending_tasks: int = Field(default=0, description="Number of pending tasks")
    in_progress_tasks: int = Field(default=0, description="Number of in-progress tasks")

    class Config:
        from_attributes = True
