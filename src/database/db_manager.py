from typing import Optional
from src.database.repository import LinkedInRepository


class DatabaseManager:
    """Service layer wrapper for SQLite database operations.

    Ensures single connection instantiation and provides unified access.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        """Initializes the database manager.

        Args:
            db_path: Path to SQLite DB file.
        """
        self.repository = LinkedInRepository(db_path)

    @property
    def db_path(self):
        """Exposes the database path."""
        return self.repository.db_path
