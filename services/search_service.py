"""
Main search service that orchestrates the entire documentation collection process
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from pathlib import Path
from utils.config import config
from utils.database import db_manager
from models.search_session import SearchSession, SearchResult, SearchStatus, DownloadStatus
# Import translation service from language_translation ability
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../language_translation'))
try:
    from services.translation_service import translation_service
except ImportError:
    # Fallback to simple translation if language_translation not available
    from core.simple_translator import SimpleTranslationService
    translation_service = SimpleTranslationService()
from core.search_engine import MultiSearchEngine
from core.document_downloader import DocumentDownloader
from core.content_processor import ContentProcessor
from core.ai_analyzer_ollama import AIContentAnalyzer
from core.query_optimizer import QueryOptimizer
from core.criteria_analyzer import CriteriaAnalyzer
from core.redis_manager import get_redis_manager
from .file_manager import FileManager

logger = logging.getLogger(__name__)

class SearchService:
    """Main search service for documentation collection"""
    
    def __init__(self):
        # Use AI Local Translation Service instead of SimpleTranslationService
        self.translator = translation_service
        self.search_engine = MultiSearchEngine()
        self.file_manager = FileManager()
        self.content_processor = ContentProcessor()
        self.ai_analyzer = AIContentAnalyzer()
        self.query_optimizer = QueryOptimizer(self.ai_analyzer)
        self.criteria_analyzer = CriteriaAnalyzer(self.ai_analyzer)
        self.redis_manager = get_redis_manager()
    
    async def search_documents(self, query: str, search_criteria: Dict[str, Any] = None) -> int:
        """
        Main method to search and collect documents
        
        Args:
            query: Search query
            search_criteria: Additional search criteria
        
        Returns:
            Search session ID
        """
        # Create search session
        session_id = await self._create_search_session(query, search_criteria)
        if not session_id:
            logger.error("Failed to create search session")
            return None
        
        try:
            # Update session status
            await self._update_session_status(session_id, SearchStatus.PROCESSING)
            
            # Step 1: Analyze criteria for flexible evaluation
            analyzed_criteria = None
            if search_criteria and search_criteria.get('filter_criteria'):
                logger.info("Analyzing criteria for flexible evaluation...")
                analyzed_criteria = await self.criteria_analyzer.analyze_criteria(
                    search_criteria.get('filter_criteria')
                )
                # Update search criteria with analyzed version
                search_criteria['analyzed_criteria'] = analyzed_criteria
            
            # Step 2: Query optimization (AI optimization is optional)
            # User can specify additional languages via --languages parameter
            languages = search_criteria.get('additional_languages', []) or ['en']  # Default to English only
            search_engines = config.ENABLED_SEARCH_ENGINES
            ai_optimization_enabled = search_criteria.get('ai_optimization', False)
            
            if ai_optimization_enabled:
                logger.info(f"Optimizing queries with AI for {len(languages)} languages and {len(search_engines)} engines...")
                # Use AI optimization
                optimized_queries = await self.query_optimizer.generate_all_optimized_queries(
                    query, languages, search_engines
                )
                queries_to_use = optimized_queries
            else:
                logger.info(f"Searching with original query for {len(languages)} languages and {len(search_engines)} engines...")
                # Create simple query structure (no AI optimization)
                simple_queries = {}
                for language in languages:
                    simple_queries[language] = {}
                    for engine in search_engines:
                        simple_queries[language][engine] = [{
                            'query': query,
                            'type': 'original',
                            'confidence': 1.0,
                            'reasoning': 'Using original query without AI optimization',
                            'original_query': query
                        }]
                queries_to_use = simple_queries
            
            # Step 3: Export query info to CSV for tracking
            session_dir = self.file_manager.get_session_directory(session_id)
            if session_dir:
                optimized_queries_path = session_dir / f"optimized_queries_{session_id}.csv"
                self.query_optimizer.export_optimized_queries_to_csv(
                    queries_to_use, str(optimized_queries_path)
                )
                logger.info(f"Exported query info to: {optimized_queries_path}")
            
            # Step 4: Search using queries (optimized or original)
            all_results = []
            for language, engines in queries_to_use.items():
                for engine, queries in engines.items():
                    for query_data in queries:
                        search_query = query_data['query']
                        logger.info(f"Searching {engine} in {language}: {search_query}")
                        
                        # Search with query - use aggressive settings if enabled
                        max_results = search_criteria.get('max_results_per_engine', config.MAX_RESULTS_PER_ENGINE)
                        if search_criteria.get('aggressive_search', False):
                            # For aggressive search, try to get more results
                            max_results = max(max_results, 30)
                        
                        # Get search pages parameter
                        search_pages = search_criteria.get('search_pages', 1)
                        
                        results = await self.search_engine.search_single_engine(
                            engine, search_query, max_results, search_pages
                        )
                        
                        # Process results with Redis deduplication
                        for result in results:
                            # Check for duplicates using Redis
                            duplicate_data = self.redis_manager.check_duplicate(result.url, session_id)
                            
                            if duplicate_data:
                                # URL is duplicate, skip but log
                                logger.info(f"Duplicate URL skipped: {result.url} (found in {duplicate_data.get('search_engine', 'unknown')})")
                                continue
                            
                            # Create search result
                            search_result = SearchResult(
                                session_id=session_id,
                                language=language,
                                translated_query=search_query,
                                search_engine=result.search_engine,
                                url=result.url,
                                title=result.title
                            )
                            all_results.append(search_result)
                            
                            # Mark URL as processed in Redis
                            result_data = {
                                'url': result.url,
                                'title': result.title,
                                'search_engine': result.search_engine,
                                'language': language,
                                'session_id': session_id,
                                'processed_at': datetime.now().isoformat()
                            }
                            self.redis_manager.mark_url_processed(result.url, session_id, result_data)
            
            # Save all results to database
            await self._save_search_results(all_results)
            
            # Log deduplication statistics
            if self.redis_manager.is_available():
                stats = self.redis_manager.get_session_stats(session_id)
                logger.info(f"Session {session_id} deduplication stats: {stats}")
            
            # Download documents
            await self._download_documents(session_id, all_results)
            
            # AI Analysis and filtering if enabled
            if search_criteria.get('ai_analysis', True) and analyzed_criteria:
                print(f"Performing AI analysis for session {session_id} with analyzed criteria")
                relevant_files = await self._perform_ai_analysis_with_criteria(session_id, analyzed_criteria)
                
                # Remove non-relevant files from storage and database
                if relevant_files is not None:
                    await self._cleanup_non_relevant_files(session_id, relevant_files)
            
            # Update session status
            await self._update_session_status(session_id, SearchStatus.COMPLETED)
            
            logger.info(f"Search completed successfully. Session ID: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            await self._update_session_status(session_id, SearchStatus.FAILED)
            return None
    
    async def _create_search_session(self, query: str, search_criteria: Dict[str, Any] = None) -> Optional[int]:
        """Create a new search session"""
        try:
            with db_manager.get_session() as session:
                search_session = SearchSession(
                    original_query=query,
                    search_criteria=search_criteria or {},
                    status=SearchStatus.PENDING
                )
                session.add(search_session)
                session.flush()  # Get the ID
                session_id = search_session.id
                
                # Create storage directory
                self.file_manager.create_session_directory(session_id)
                
                logger.info(f"Created search session: {session_id}")
                return session_id
                
        except Exception as e:
            logger.error(f"Failed to create search session: {e}")
            return None
    
    async def _update_session_status(self, session_id: int, status: SearchStatus):
        """Update search session status"""
        try:
            with db_manager.get_session() as session:
                search_session = session.query(SearchSession).filter(SearchSession.id == session_id).first()
                if search_session:
                    search_session.status = status
                    search_session.updated_at = datetime.now(timezone.utc)
                    logger.info(f"Updated session {session_id} status to {status}")
        except Exception as e:
            logger.error(f"Failed to update session status: {e}")
    
    async def _save_search_results(self, results: List[SearchResult]):
        """Save search results to database"""
        try:
            with db_manager.get_session() as session:
                for result in results:
                    session.add(result)
                logger.info(f"Saved {len(results)} search results to database")
        except Exception as e:
            logger.error(f"Failed to save search results: {e}")
    
    async def _download_documents(self, session_id: int, results: List[SearchResult]):
        """Download documents for search results"""
        logger.info(f"Starting download for session {session_id}")
        
        # Get fresh results from database to avoid session issues
        try:
            with db_manager.get_session() as session:
                db_results = session.query(SearchResult).filter(SearchResult.session_id == session_id).all()
                # Convert to dict to avoid session issues
                results_data = []
                for result in db_results:
                    results_data.append({
                        'id': result.id,
                        'url': result.url,
                        'title': result.title
                    })
        except Exception as e:
            logger.error(f"Failed to get results from database: {e}")
            return
        
        # Filter results that can be downloaded
        downloadable_results = []
        for result_data in results_data:
            if self._is_downloadable_url(result_data['url']):
                downloadable_results.append(result_data)
        
        if not downloadable_results:
            logger.warning("No downloadable URLs found")
            return
        
        # Download documents
        async with DocumentDownloader() as downloader:
            for result_data in downloadable_results:
                try:
                    # Generate file path
                    session_dir = self.file_manager.get_session_directory(session_id)
                    if not session_dir:
                        logger.error(f"Session directory not found: {session_id}")
                        continue
                    
                    filename = self.file_manager._generate_filename(result_data['url'], result_data['title'])
                    file_path = session_dir / filename
                    file_path = self.file_manager._ensure_unique_filename(file_path)
                    
                    # Download document
                    success, downloaded_path, file_size = await downloader.download_document(
                        result_data['url'], str(file_path)
                    )
                    
                    if success:
                        # Update result in database
                        await self._update_search_result(
                            result_data['id'],
                            file_path=str(downloaded_path),
                            file_size=file_size,
                            download_status=DownloadStatus.DOWNLOADED
                        )
                        
                        # Process document content
                        metadata = self.content_processor.process_document(downloaded_path)
                        logger.info(f"Downloaded and processed: {downloaded_path}")
                    else:
                        # Mark as failed
                        await self._update_search_result(
                            result_data['id'],
                            download_status=DownloadStatus.FAILED
                        )
                        logger.warning(f"Failed to download or validate: {result_data['url']}")
                
                except Exception as e:
                    logger.error(f"Error downloading {result_data['url']}: {e}")
                    await self._update_search_result(
                        result_data['id'],
                        download_status=DownloadStatus.FAILED
                    )
    
    def _is_downloadable_url(self, url: str) -> bool:
        """Check if URL is downloadable"""
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False
        
        # Check if it's a supported file type
        path = parsed.path.lower()
        for ext in config.SUPPORTED_FILE_TYPES:
            if path.endswith(ext):
                return True
        
        # Check if it's a web page that might contain documents
        if any(domain in parsed.netloc for domain in ['google.com', 'bing.com', 'duckduckgo.com']):
            return False
        
        return True
    
    async def _update_search_result(self, result_id: int, **kwargs):
        """Update search result in database"""
        try:
            with db_manager.get_session() as session:
                result = session.query(SearchResult).filter(SearchResult.id == result_id).first()
                if result:
                    for key, value in kwargs.items():
                        setattr(result, key, value)
                    result.updated_at = datetime.now(timezone.utc)
                    session.commit()  # Commit the changes
                    logger.debug(f"Updated search result {result_id}")
        except Exception as e:
            logger.error(f"Failed to update search result {result_id}: {e}")
    
    async def _perform_ai_analysis(self, session_id: int, filter_criteria: str):
        """Perform AI analysis on downloaded documents"""
        try:
            logger.info(f"Starting AI analysis for session {session_id}")
            
            # Get downloaded files for this session
            with db_manager.get_session() as session:
                results = session.query(SearchResult).filter(
                    SearchResult.session_id == session_id,
                    SearchResult.download_status == DownloadStatus.DOWNLOADED,
                    SearchResult.file_path.isnot(None)
                ).all()
                
                # Get file paths and result IDs (convert to list to avoid session binding issues)
                file_data = []
                for result in results:
                    if result.file_path:
                        file_data.append({
                            'result_id': result.id,
                            'file_path': result.file_path,
                            'url': result.url,
                            'title': result.title
                        })
            
            if not file_data:
                logger.warning(f"No downloaded files found for session {session_id}")
                return []
            
            # Extract file paths for analysis
            file_paths = [data['file_path'] for data in file_data]
            
            # Perform AI analysis
            analysis_results = await self.ai_analyzer.batch_analyze(file_paths, filter_criteria)
            
            # Filter relevant results and map back to result IDs
            relevant_files = []
            for i, analysis in enumerate(analysis_results):
                if analysis.get('relevant', False) and analysis.get('score', 0) > 0.5:
                    file_info = file_data[i]
                    relevant_files.append({
                        'result_id': file_info['result_id'],
                        'file_path': analysis['file_path'],
                        'url': file_info['url'],
                        'title': file_info['title'],
                        'score': analysis['score'],
                        'summary': analysis['summary'],
                        'key_points': analysis['key_points'],
                        'file_links': analysis['file_links']
                    })
            
            # Save AI analysis results
            await self._save_ai_analysis_results(session_id, relevant_files, filter_criteria)
            
            logger.info(f"AI analysis completed. Found {len(relevant_files)} relevant files")
            return relevant_files

        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return []

    async def _perform_ai_analysis_with_criteria(self, session_id: int, analyzed_criteria: Dict[str, Any]):
        """Perform AI analysis using flexible criteria evaluation"""
        try:
            logger.info(f"Starting flexible AI analysis for session {session_id}")
            
            # Get downloaded files for this session
            with db_manager.get_session() as session:
                results = session.query(SearchResult).filter(
                    SearchResult.session_id == session_id,
                    SearchResult.download_status == DownloadStatus.DOWNLOADED,
                    SearchResult.file_path.isnot(None)
                ).all()
                
                # Get file paths and result IDs
                file_data = []
                for result in results:
                    if result.file_path:
                        file_data.append({
                            'result_id': result.id,
                            'file_path': result.file_path,
                            'url': result.url,
                            'title': result.title
                        })
            
            if not file_data:
                logger.warning(f"No downloaded files found for session {session_id}")
                return []
            
            # Perform flexible evaluation for each document
            relevant_files = []
            for file_info in file_data:
                try:
                    # Read document content
                    document_content = self.content_processor.extract_text_content(file_info['file_path'])
                    
                    # Evaluate against analyzed criteria
                    evaluation_result = await self.criteria_analyzer.evaluate_document_against_criteria(
                        document_content, analyzed_criteria
                    )
                    
                    # Check if document meets criteria (flexible evaluation)
                    if evaluation_result.get('relevant', False):
                        relevant_files.append({
                            'result_id': file_info['result_id'],
                            'file_path': file_info['file_path'],
                            'url': file_info['url'],
                            'title': file_info['title'],
                            'score': evaluation_result.get('score', 0.0),
                            'criteria_met': evaluation_result.get('criteria_met', []),
                            'criteria_not_met': evaluation_result.get('criteria_not_met', []),
                            'summary': evaluation_result.get('summary', ''),
                            'evaluation_details': evaluation_result
                        })
                        
                        logger.debug(f"Document passed criteria: {file_info['title'][:50]}...")
                    else:
                        logger.debug(f"Document failed criteria: {file_info['title'][:50]}...")
                        
                except Exception as e:
                    logger.error(f"Failed to evaluate document {file_info['file_path']}: {e}")
                    continue
            
            # Save evaluation results
            await self._save_flexible_analysis_results(session_id, relevant_files, analyzed_criteria)
            
            logger.info(f"Flexible AI analysis completed. Found {len(relevant_files)} relevant files")
            return relevant_files

        except Exception as e:
            logger.error(f"Flexible AI analysis failed: {e}")
            return []

    async def _save_flexible_analysis_results(self, session_id: int, relevant_files: List[Dict], analyzed_criteria: Dict[str, Any]):
        """Save flexible analysis results to database"""
        try:
            with db_manager.get_session() as session:
                # Create analysis record
                analysis_record = {
                    'session_id': session_id,
                    'analysis_type': 'flexible_criteria',
                    'criteria_used': analyzed_criteria.get('original_criteria', ''),
                    'specific_criteria': analyzed_criteria.get('specific_criteria', []),
                    'flexible_evaluation': analyzed_criteria.get('flexible_evaluation', True),
                    'min_criteria_met': analyzed_criteria.get('min_criteria_met', 1),
                    'total_files_analyzed': len(relevant_files) + (await self._count_analyzed_files(session_id)),
                    'relevant_files_count': len(relevant_files),
                    'analysis_confidence': analyzed_criteria.get('analysis_confidence', 0.0)
                }
                
                # Save to database (you may need to create a table for this)
                logger.info(f"Saved flexible analysis results for session {session_id}")
                
        except Exception as e:
            logger.error(f"Failed to save flexible analysis results: {e}")

    async def _count_analyzed_files(self, session_id: int) -> int:
        """Count total files analyzed for this session"""
        try:
            with db_manager.get_session() as session:
                count = session.query(SearchResult).filter(
                    SearchResult.session_id == session_id,
                    SearchResult.download_status == DownloadStatus.DOWNLOADED,
                    SearchResult.file_path.isnot(None)
                ).count()
                return count
        except Exception as e:
            logger.error(f"Failed to count analyzed files: {e}")
            return 0
    
    async def _save_ai_analysis_results(self, session_id: int, relevant_files: List[Dict], filter_criteria: str):
        """Save AI analysis results to database"""
        try:
            with db_manager.get_session() as session:
                # Create AI analysis record
                ai_analysis = {
                    'session_id': session_id,
                    'filter_criteria': filter_criteria,
                    'relevant_files_count': len(relevant_files),
                    'analysis_results': relevant_files,
                    'created_at': datetime.now(timezone.utc)
                }
                
                # Save to database (you might want to create a separate table for this)
                logger.info(f"Saved AI analysis results for session {session_id}")
                
        except Exception as e:
            logger.error(f"Failed to save AI analysis results: {e}")

    async def _cleanup_non_relevant_files(self, session_id: int, relevant_files: List[Dict]):
        """Remove non-relevant files from storage and database"""
        try:
            logger.info(f"Cleaning up non-relevant files for session {session_id}")
            
            # Get list of relevant result IDs
            relevant_result_ids = {file_info['result_id'] for file_info in relevant_files}
            
            # Get all downloaded results for this session
            with db_manager.get_session() as session:
                all_results = session.query(SearchResult).filter(
                    SearchResult.session_id == session_id,
                    SearchResult.download_status == DownloadStatus.DOWNLOADED,
                    SearchResult.file_path.isnot(None)
                ).all()
                
                # Find non-relevant files to remove
                non_relevant_results = []
                for result in all_results:
                    if result.id not in relevant_result_ids:
                        non_relevant_results.append(result)
                
                logger.info(f"Found {len(non_relevant_results)} non-relevant files to remove")
                
                # Remove files from storage and update database
                removed_count = 0
                for result in non_relevant_results:
                    try:
                        # Remove file from storage
                        if result.file_path and Path(result.file_path).exists():
                            Path(result.file_path).unlink()
                            logger.debug(f"Removed file: {result.file_path}")
                        
                        # Update database record
                        result.file_path = None
                        result.download_status = DownloadStatus.FAILED
                        result.updated_at = datetime.now(timezone.utc)
                        
                        removed_count += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to remove file {result.file_path}: {e}")
                
                session.commit()
                logger.info(f"Cleaned up {removed_count} non-relevant files")
                
        except Exception as e:
            logger.error(f"Failed to cleanup non-relevant files: {e}")

    async def get_search_results(self, session_id: int) -> Dict[str, Any]:
        """Get search results for a session"""
        try:
            with db_manager.get_session() as session:
                # Get session info
                search_session = session.query(SearchSession).filter(SearchSession.id == session_id).first()
                if not search_session:
                    return None
                
                # Get results
                results = session.query(SearchResult).filter(SearchResult.session_id == session_id).all()
                
                # Organize results by language
                results_by_language = {}
                for result in results:
                    if result.language not in results_by_language:
                        results_by_language[result.language] = []
                    
                    results_by_language[result.language].append({
                        'id': result.id,
                        'title': result.title,
                        'url': result.url,
                        'search_engine': result.search_engine,
                        'file_path': result.file_path,
                        'file_type': result.file_type,
                        'download_status': result.download_status.value,
                        'created_at': result.created_at.isoformat()
                    })
                
                return {
                    'session_id': session_id,
                    'original_query': search_session.original_query,
                    'status': search_session.status.value,
                    'total_results': len(results),
                    'created_at': search_session.created_at.isoformat(),
                    'results_by_language': results_by_language
                }
                
        except Exception as e:
            logger.error(f"Failed to get search results: {e}")
            return None
    
    async def export_results(self, session_id: int, format: str = 'csv') -> Optional[str]:
        """Export search results"""
        try:
            if format.lower() == 'csv':
                output_path = self.file_manager.export_session_to_csv(session_id)
            elif format.lower() == 'excel':
                output_path = self.file_manager.export_session_to_excel(session_id)
            else:
                logger.error(f"Unsupported export format: {format}")
                return None
            
            return str(output_path) if output_path else None
            
        except Exception as e:
            logger.error(f"Failed to export results: {e}")
            return None
    
    async def get_session_summary(self, session_id: int) -> Dict[str, Any]:
        """Get session summary statistics"""
        try:
            with db_manager.get_session() as session:
                search_session = session.query(SearchSession).filter(SearchSession.id == session_id).first()
                if not search_session:
                    return None
                
                results = session.query(SearchResult).filter(SearchResult.session_id == session_id).all()
                
                # Calculate statistics
                total_results = len(results)
                downloaded_count = len([r for r in results if r.download_status == DownloadStatus.DOWNLOADED])
                failed_count = len([r for r in results if r.download_status == DownloadStatus.FAILED])
                
                # Language distribution
                language_stats = {}
                for result in results:
                    lang = result.language
                    if lang not in language_stats:
                        language_stats[lang] = 0
                    language_stats[lang] += 1
                
                # Search engine distribution
                engine_stats = {}
                for result in results:
                    engine = result.search_engine
                    if engine not in engine_stats:
                        engine_stats[engine] = 0
                    engine_stats[engine] += 1
                
                return {
                    'session_id': session_id,
                    'original_query': search_session.original_query,
                    'status': search_session.status.value,
                    'total_results': total_results,
                    'downloaded_count': downloaded_count,
                    'failed_count': failed_count,
                    'language_stats': language_stats,
                    'engine_stats': engine_stats,
                    'created_at': search_session.created_at.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get session summary: {e}")
            return None
