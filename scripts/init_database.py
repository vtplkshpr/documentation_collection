#!/usr/bin/env python3
"""
Database initialization script
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.config import config
from utils.database import db_manager
from models.search_session import Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize database tables"""
    try:
        # Test connection first
        if not db_manager.test_connection():
            logger.error("Database connection failed!")
            return False
        
        # Create tables
        db_manager.create_tables()
        logger.info("Database initialized successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

if __name__ == "__main__":
    print("Initializing database...")
    success = init_database()
    if success:
        print("✓ Database initialized successfully!")
    else:
        print("✗ Database initialization failed!")
        sys.exit(1)
