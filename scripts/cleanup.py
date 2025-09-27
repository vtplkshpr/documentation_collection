#!/usr/bin/env python3
"""
Cleanup script for old files and data
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from services.file_manager import FileManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_old_files(days_to_keep=30):
    """Clean up old files"""
    try:
        file_manager = FileManager()
        
        print(f"Cleaning up files older than {days_to_keep} days...")
        deleted_count = file_manager.cleanup_old_files(days_to_keep)
        
        if deleted_count > 0:
            print(f"✓ Cleaned up {deleted_count} old directories")
        else:
            print("✓ No old files to clean up")
        
        return True
        
    except Exception as e:
        print(f"✗ Cleanup error: {e}")
        return False

def show_storage_stats():
    """Show storage statistics"""
    try:
        file_manager = FileManager()
        stats = file_manager.get_storage_stats()
        
        print("\nStorage Statistics:")
        print(f"Total Sessions: {stats['total_sessions']}")
        print(f"Total Files: {stats['total_files']}")
        print(f"Total Size: {stats['total_size'] / (1024*1024):.2f} MB")
        print(f"Date Directories: {stats['date_directories']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error getting storage stats: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Cleanup old files and show storage stats")
    parser.add_argument("--days", type=int, default=30, help="Days to keep files")
    parser.add_argument("--stats", action="store_true", help="Show storage statistics")
    parser.add_argument("--cleanup", action="store_true", help="Clean up old files")
    
    args = parser.parse_args()
    
    if args.stats:
        show_storage_stats()
    
    if args.cleanup:
        cleanup_old_files(args.days)
    
    if not args.stats and not args.cleanup:
        # Default: show stats and cleanup
        show_storage_stats()
        cleanup_old_files(args.days)
