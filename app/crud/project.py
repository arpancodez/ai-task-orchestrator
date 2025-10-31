from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.crud.base import CRUDBase
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


class CRUDProject(CRUDBase[Project, ProjectCreate, ProjectUpdate]):
    """
    CRUD operations for Project model with additional methods for
    owner-based queries and statistics.
    """

    def create_with_owner(
        self, db: Session, *, obj_in: ProjectCreate, owner_id: int
    ) -> Project:
        """
        Create a new project with an owner.
        
        Args:
            db: Database session
            obj_in: Project creation schema
            owner_id: ID of the project owner
            
        Returns:
            Created project instance
        """
        obj_in_data = obj_in.dict()
        db_obj = Project(**obj_in_data, owner_id=owner_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi_by_owner(
        self,
        db: Session,
        *,
        owner_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Project]:
        """
        Retrieve multiple projects by owner.
        
        Args:
            db: Database session
            owner_id: ID of the project owner
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of projects belonging to the owner
        """
        return (
            db.query(Project)
            .filter(Project.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_project_stats(
        self, db: Session, *, project_id: int
    ) -> dict:
        """
        Get statistics for a specific project.
        
        Args:
            db: Database session
            project_id: ID of the project
            
        Returns:
            Dictionary containing project statistics including:
            - total_tasks: Total number of tasks
            - completed_tasks: Number of completed tasks
            - pending_tasks: Number of pending tasks
            - completion_rate: Percentage of completed tasks
        """
        from app.models.task import Task
        
        # Get total tasks count
        total_tasks = (
            db.query(func.count(Task.id))
            .filter(Task.project_id == project_id)
            .scalar()
        ) or 0
        
        # Get completed tasks count
        completed_tasks = (
            db.query(func.count(Task.id))
            .filter(Task.project_id == project_id, Task.status == "completed")
            .scalar()
        ) or 0
        
        # Calculate pending tasks
        pending_tasks = total_tasks - completed_tasks
        
        # Calculate completion rate
        completion_rate = (
            (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
        )
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "pending_tasks": pending_tasks,
            "completion_rate": round(completion_rate, 2),
        }


# Create instance of CRUDProject
project_crud = CRUDProject(Project)
