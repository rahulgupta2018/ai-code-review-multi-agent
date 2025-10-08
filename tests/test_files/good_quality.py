
"""
User management utilities with proper documentation and clean structure.
"""

from typing import List, Optional, Dict
import logging

logger = logging.getLogger(__name__)


class User:
    """Represents a user in the system."""
    
    def __init__(self, user_id: int, username: str, email: str):
        """
        Initialize a new User.
        
        Args:
            user_id: Unique identifier for the user
            username: The user's username
            email: The user's email address
        """
        self.user_id = user_id
        self.username = username
        self.email = email
        
    def is_valid_email(self) -> bool:
        """Check if the user's email is valid."""
        return "@" in self.email and "." in self.email
        
    def to_dict(self) -> Dict[str, str]:
        """Convert user to dictionary representation."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email
        }


class UserManager:
    """Manages user operations with proper error handling."""
    
    def __init__(self):
        """Initialize the user manager."""
        self._users: List[User] = []
        logger.info("UserManager initialized")
    
    def add_user(self, user: User) -> bool:
        """
        Add a user to the system.
        
        Args:
            user: The user to add
            
        Returns:
            True if user was added successfully, False otherwise
        """
        if not user.is_valid_email():
            logger.warning(f"Invalid email for user {user.username}")
            return False
            
        self._users.append(user)
        logger.info(f"Added user {user.username}")
        return True
    
    def find_user(self, username: str) -> Optional[User]:
        """Find a user by username."""
        for user in self._users:
            if user.username == username:
                return user
        return None
    
    def get_user_count(self) -> int:
        """Get the total number of users."""
        return len(self._users)
