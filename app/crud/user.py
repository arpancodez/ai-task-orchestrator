from typing import Optional
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """
    CRUD operations for User model with authentication functionality.
    """

    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """
        Get user by email address.
        
        Args:
            db: Database session
            email: User's email address
            
        Returns:
            User object if found, None otherwise
        """
        return db.query(User).filter(User.email == email).first()

    def get_by_username(self, db: Session, *, username: str) -> Optional[User]:
        """
        Get user by username.
        
        Args:
            db: Database session
            username: User's username
            
        Returns:
            User object if found, None otherwise
        """
        return db.query(User).filter(User.username == username).first()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        """
        Create new user with hashed password.
        
        Args:
            db: Database session
            obj_in: User creation schema with plain password
            
        Returns:
            Created User object
        """
        db_obj = User(
            email=obj_in.email,
            username=obj_in.username,
            hashed_password=self._hash_password(obj_in.password),
            full_name=obj_in.full_name,
            is_active=obj_in.is_active,
            is_superuser=obj_in.is_superuser,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def authenticate(self, db: Session, *, email: str, password: str) -> Optional[User]:
        """
        Authenticate user with email and password.
        
        Args:
            db: Database session
            email: User's email address
            password: Plain text password
            
        Returns:
            User object if authentication successful, None otherwise
        """
        user = self.get_by_email(db, email=email)
        if not user:
            return None
        if not self._verify_password(password, user.hashed_password):
            return None
        return user

    def is_active(self, user: User) -> bool:
        """
        Check if user account is active.
        
        Args:
            user: User object
            
        Returns:
            True if user is active, False otherwise
        """
        return user.is_active

    def is_superuser(self, user: User) -> bool:
        """
        Check if user has superuser privileges.
        
        Args:
            user: User object
            
        Returns:
            True if user is superuser, False otherwise
        """
        return user.is_superuser

    def _hash_password(self, password: str) -> str:
        """
        Hash a plain text password.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        return pwd_context.hash(password)

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain text password against hashed password.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password from database
            
        Returns:
            True if password matches, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)


# Create user_crud instance
user_crud = CRUDUser(User)
