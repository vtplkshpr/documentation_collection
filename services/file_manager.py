"""
File manager for storage organization and management
"""
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from utils.config import config
from utils.database import db_manager
from models.search_session import SearchSession, SearchResult, DownloadStatus

logger = logging.getLogger(__name__)

class FileManager:
    """File manager for organizing downloaded documents"""
    
    def __init__(self):
        self.base_path = Path(config.STORAGE_BASE_PATH)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def create_session_directory(self, session_id: int) -> Path:
        """
        Create directory structure for a search session
        
        Args:
            session_id: Search session ID
        
        Returns:
            Path to the session directory
        """
        # Create date-based directory
        today = datetime.now().strftime("%Y-%m-%d")
        date_dir = self.base_path / today
        date_dir.mkdir(exist_ok=True)
        
        # Create session directory
        session_dir = date_dir / str(session_id).zfill(3)
        session_dir.mkdir(exist_ok=True)
        
        logger.info(f"Created session directory: {session_dir}")
        return session_dir
    
    def get_session_directory(self, session_id: int) -> Optional[Path]:
        """
        Get existing session directory
        
        Args:
            session_id: Search session ID
        
        Returns:
            Path to session directory or None if not found
        """
        # Search in all date directories
        for date_dir in self.base_path.iterdir():
            if date_dir.is_dir():
                session_dir = date_dir / str(session_id).zfill(3)
                if session_dir.exists():
                    return session_dir
        
        return None
    
    def save_document(self, session_id: int, url: str, title: str, content: bytes, file_extension: str = None) -> Optional[Path]:
        """
        Save downloaded document to session directory
        
        Args:
            session_id: Search session ID
            url: Document URL
            title: Document title
            content: File content
            file_extension: File extension
        
        Returns:
            Path to saved file or None if failed
        """
        try:
            # Get or create session directory
            session_dir = self.get_session_directory(session_id)
            if not session_dir:
                session_dir = self.create_session_directory(session_id)
            
            # Generate filename
            filename = self._generate_filename(url, title, file_extension)
            file_path = session_dir / filename
            
            # Ensure unique filename
            file_path = self._ensure_unique_filename(file_path)
            
            # Save file
            with open(file_path, 'wb') as f:
                f.write(content)
            
            logger.info(f"Saved document: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to save document: {e}")
            return None
    
    def _generate_filename(self, url: str, title: str, file_extension: str = None) -> str:
        """Generate filename from URL and title"""
        from urllib.parse import urlparse, unquote
        
        # Try to get filename from URL
        parsed_url = urlparse(url)
        url_filename = os.path.basename(unquote(parsed_url.path))
        
        if url_filename and '.' in url_filename:
            return url_filename
        
        # Use title if available
        if title:
            # Clean title for filename
            clean_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            clean_title = clean_title[:50]  # Limit length
            if file_extension:
                return f"{clean_title}{file_extension}"
            else:
                return f"{clean_title}.html"
        
        # Fallback to URL-based name
        if file_extension:
            return f"document{file_extension}"
        else:
            return "document.html"
    
    def _ensure_unique_filename(self, file_path: Path) -> Path:
        """Ensure filename is unique by adding number suffix if needed"""
        if not file_path.exists():
            return file_path
        
        base_name = file_path.stem
        extension = file_path.suffix
        directory = file_path.parent
        
        counter = 1
        while True:
            new_name = f"{base_name}_{counter}{extension}"
            new_path = directory / new_name
            if not new_path.exists():
                return new_path
            counter += 1
    
    def get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """Get file information"""
        try:
            stat = file_path.stat()
            return {
                'file_name': file_path.name,
                'file_path': str(file_path),
                'file_size': stat.st_size,
                'created_time': stat.st_ctime,
                'modified_time': stat.st_mtime,
                'file_extension': file_path.suffix.lower()
            }
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            return {}
    
    def cleanup_old_files(self, days_to_keep: int = 30) -> int:
        """
        Clean up old files
        
        Args:
            days_to_keep: Number of days to keep files
        
        Returns:
            Number of files deleted
        """
        deleted_count = 0
        cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
        
        try:
            for date_dir in self.base_path.iterdir():
                if not date_dir.is_dir():
                    continue
                
                # Check if date directory is old
                if date_dir.stat().st_mtime < cutoff_date:
                    # Delete entire date directory
                    import shutil
                    shutil.rmtree(date_dir)
                    deleted_count += 1
                    logger.info(f"Deleted old date directory: {date_dir}")
                else:
                    # Check individual session directories
                    for session_dir in date_dir.iterdir():
                        if session_dir.is_dir() and session_dir.stat().st_mtime < cutoff_date:
                            import shutil
                            shutil.rmtree(session_dir)
                            deleted_count += 1
                            logger.info(f"Deleted old session directory: {session_dir}")
        
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        
        return deleted_count
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        stats = {
            'total_sessions': 0,
            'total_files': 0,
            'total_size': 0,
            'date_directories': 0
        }
        
        try:
            for date_dir in self.base_path.iterdir():
                if not date_dir.is_dir():
                    continue
                
                stats['date_directories'] += 1
                
                for session_dir in date_dir.iterdir():
                    if not session_dir.is_dir():
                        continue
                    
                    stats['total_sessions'] += 1
                    
                    for file_path in session_dir.rglob('*'):
                        if file_path.is_file():
                            stats['total_files'] += 1
                            stats['total_size'] += file_path.stat().st_size
        
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
        
        return stats
    
    def export_session_to_csv(self, session_id: int, output_path: Optional[Path] = None) -> Optional[Path]:
        """
        Export session results to CSV
        
        Args:
            session_id: Search session ID
            output_path: Output CSV path (optional)
        
        Returns:
            Path to exported CSV or None if failed
        """
        try:
            import pandas as pd
            
            # Get session directory
            session_dir = self.get_session_directory(session_id)
            if not session_dir:
                logger.error(f"Session directory not found for ID: {session_id}")
                return None
            
            # Get session data from database
            with db_manager.get_session() as session:
                search_session = session.query(SearchSession).filter(SearchSession.id == session_id).first()
                if not search_session:
                    logger.error(f"Search session not found: {session_id}")
                    return None
                
                # Only get results that were successfully downloaded (AI-approved)
                results = session.query(SearchResult).filter(
                    SearchResult.session_id == session_id,
                    SearchResult.download_status == DownloadStatus.DOWNLOADED,
                    SearchResult.file_path.isnot(None)
                ).all()
                
                # Prepare data for CSV (convert to dict to avoid session issues)
                csv_data = []
                for result in results:
                    csv_data.append({
                        'title': result.title,
                        'url': result.url,
                        'language': result.language,
                        'search_engine': result.search_engine,
                        'file_path': result.file_path,
                        'file_type': result.file_type,
                        'download_status': result.download_status.value,
                        'created_at': result.created_at.isoformat() if result.created_at else ''
                    })
            
            # Create DataFrame and save
            df = pd.DataFrame(csv_data)
            
            if output_path is None:
                output_path = session_dir / f"results_{session_id}.csv"
            
            df.to_csv(output_path, index=False, encoding='utf-8-sig')  # UTF-8 with BOM for Excel compatibility
            logger.info(f"Exported session {session_id} to CSV: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error exporting session to CSV: {e}")
            return None
    
    def export_session_to_excel(self, session_id: int, output_path: Optional[Path] = None) -> Optional[Path]:
        """
        Export session results to Excel
        
        Args:
            session_id: Search session ID
            output_path: Output Excel path (optional)
        
        Returns:
            Path to exported Excel or None if failed
        """
        try:
            import pandas as pd
            
            # Get session data
            with db_manager.get_session() as session:
                search_session = session.query(SearchSession).filter(SearchSession.id == session_id).first()
                if not search_session:
                    logger.error(f"Search session not found: {session_id}")
                    return None
                
                # Only get results that were successfully downloaded (AI-approved)
                results = session.query(SearchResult).filter(
                    SearchResult.session_id == session_id,
                    SearchResult.download_status == DownloadStatus.DOWNLOADED,
                    SearchResult.file_path.isnot(None)
                ).all()
                
                # Prepare data (convert to dict to avoid session issues)
                csv_data = []
                for result in results:
                    csv_data.append({
                        'title': result.title,
                        'url': result.url,
                        'language': result.language,
                        'search_engine': result.search_engine,
                        'file_path': result.file_path,
                        'file_type': result.file_type,
                        'download_status': result.download_status.value,
                        'created_at': result.created_at.isoformat() if result.created_at else ''
                    })
            
            # Create DataFrame and save
            df = pd.DataFrame(csv_data)
            
            if output_path is None:
                session_dir = self.get_session_directory(session_id)
                if session_dir:
                    output_path = session_dir / f"results_{session_id}.xlsx"
                else:
                    output_path = Path(f"results_{session_id}.xlsx")
            
            df.to_excel(output_path, index=False, engine='openpyxl')
            logger.info(f"Exported session {session_id} to Excel: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error exporting session to Excel: {e}")
            return None
