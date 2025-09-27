"""
Database connection and session management
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
import logging
from .config import config

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database connection manager"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._setup_database()
    
    def _setup_database(self):
        """Setup database connection"""
        try:
            self.engine = create_engine(
                config.DATABASE_URL,
                echo=False,  # Set to True for SQL debugging
                pool_pre_ping=True,
                pool_recycle=300
            )
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            logger.info("Database connection established successfully")
        except Exception as e:
            logger.error(f"Failed to setup database: {e}")
            raise
    
    @contextmanager
    def get_session(self):
        """Get database session with automatic cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def create_tables(self):
        """Create all tables"""
        try:
            from models.search_session import Base
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

# Global database manager instance
db_manager = DatabaseManager()
