from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Association table for many-to-many relationship between tasks and tags
task_tags = Table(
    'task_tags',
    Base.metadata,
    Column('task_id', Integer, ForeignKey('tasks.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)


class Task(Base):
    """SQLAlchemy Task model for managing tasks in the orchestrator.
    
    Attributes:
        id: Primary key identifier
        title: Task title/name
        description: Detailed task description
        status: Current status (e.g., 'pending', 'in_progress', 'completed', 'cancelled')
        priority: Task priority level (e.g., 'low', 'medium', 'high', 'critical')
        deadline: Task deadline timestamp
        created_at: Timestamp when task was created
        updated_at: Timestamp when task was last updated
        user_id: Foreign key reference to the user who owns/created the task
        project_id: Foreign key reference to the project this task belongs to
        tags: Many-to-many relationship with Tag model
        user: Relationship to User model
        project: Relationship to Project model
    """
    __tablename__ = 'tasks'
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Core task information
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default='pending', index=True)
    priority = Column(String(50), nullable=False, default='medium', index=True)
    
    # Time-related fields
    deadline = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=True, index=True)
    
    # Relationships
    user = relationship('User', back_populates='tasks')
    project = relationship('Project', back_populates='tasks')
    tags = relationship('Tag', secondary=task_tags, back_populates='tasks')
    
    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status}', priority='{self.priority}')>"
    
    def to_dict(self):
        """Convert task instance to dictionary representation."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'user_id': self.user_id,
            'project_id': self.project_id,
            'tags': [tag.name for tag in self.tags] if self.tags else []
        }


class Tag(Base):
    """Tag model for categorizing tasks."""
    __tablename__ = 'tags'
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    tasks = relationship('Task', secondary=task_tags, back_populates='tags')
    
    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.name}')>"
