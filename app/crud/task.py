from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.crud.base import CRUDBase
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate


class CRUDTask(CRUDBase[Task, TaskCreate, TaskUpdate]):
    def create_with_owner(
        self, db: Session, *, obj_in: TaskCreate, owner_id: int
    ) -> Task:
        """Create a new task with an owner."""
        obj_in_data = obj_in.dict()
        db_obj = Task(**obj_in_data, owner_id=owner_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi_by_owner(
        self, db: Session, *, owner_id: int, skip: int = 0, limit: int = 100
    ) -> List[Task]:
        """Get multiple tasks by owner."""
        return (
            db.query(Task)
            .filter(Task.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_project(
        self, db: Session, *, project_id: int, skip: int = 0, limit: int = 100
    ) -> List[Task]:
        """Get tasks by project."""
        return (
            db.query(Task)
            .filter(Task.project_id == project_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_overdue_tasks(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Task]:
        """Get all overdue tasks."""
        current_time = datetime.utcnow()
        return (
            db.query(Task)
            .filter(Task.due_date < current_time)
            .filter(Task.status != "completed")
            .offset(skip)
            .limit(limit)
            .all()
        )


task_crud = CRUDTask(Task)
