#!/usr/bin/env python3
"""
Database connection test script
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.config import config
from utils.database import db_manager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_connection():
    """Test database connection"""
    try:
        print(f"Testing connection to: {config.DATABASE_URL}")
        
        if db_manager.test_connection():
            print("✓ Database connection successful!")
            return True
        else:
            print("✗ Database connection failed!")
            return False
            
    except Exception as e:
        print(f"✗ Connection error: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
