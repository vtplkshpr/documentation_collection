"""
AI Content Analyzer using Ollama (Local AI)
"""
import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from utils.config import config

logger = logging.getLogger(__name__)

class AIContentAnalyzer:
    """AI-powered content analyzer using Ollama local AI"""
    
    def __init__(self):
        self.ollama_client = None
        self._setup_ollama()
    
    def _setup_ollama(self):
        """Setup Ollama AI client"""
        try:
            from .ollama_client import OllamaClient
            self.ollama_client = OllamaClient()
            logger.info("Ollama AI initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Ollama AI: {e}")
            self.ollama_client = None
    
    async def analyze_content(self, file_path: str, search_criteria: str) -> Dict[str, Any]:
        """
        Analyze content of a downloaded file against search criteria
        
        Args:
            file_path: Path to the downloaded file
            search_criteria: User's search criteria for filtering
            
        Returns:
            Analysis result with relevance score and summary
        """
        if not self.ollama_client:
            return {
                'relevant': False,
                'score': 0.0,
                'summary': 'AI analysis not available',
                'reason': 'Ollama client not configured'
            }
        
        try:
            # Read file content
            content = self._read_file_content(file_path)
            if not content:
                return {
                    'relevant': False,
                    'score': 0.0,
                    'summary': 'Could not read file content',
                    'reason': 'File read error'
                }
            
            # Prepare prompt for Ollama
            prompt = self._create_analysis_prompt(content, search_criteria)
            
            # Get AI analysis
            response = await self.ollama_client.analyze_text_content(prompt, "Content analysis")
            
            # Parse response
            analysis = self._parse_ai_response(response)
            
            logger.info(f"AI analysis completed for {file_path}")
            return analysis
            
        except Exception as e:
            logger.error(f"AI analysis failed for {file_path}: {e}")
            return {
                'relevant': False,
                'score': 0.0,
                'summary': f'Analysis failed: {str(e)}',
                'reason': 'AI analysis error'
            }
    
    async def analyze_text_content(self, text_content: str, analysis_type: str = "Content analysis") -> str:
        """
        Analyze text content directly (for query optimization and criteria analysis)
        
        Args:
            text_content: Text content to analyze
            analysis_type: Type of analysis being performed
            
        Returns:
            AI response as string
        """
        if not self.ollama_client:
            return "AI analysis not available"
        
        try:
            # Use Ollama client for analysis
            response = await self.ollama_client.analyze_text_content(text_content, analysis_type)
            return response if response else "No response generated"
            
        except Exception as e:
            logger.error(f"Text analysis failed: {e}")
            return f"Analysis failed: {e}"
    
    def _read_file_content(self, file_path: str) -> Optional[str]:
        """Read content from various file types"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return None
            
            # Read based on file extension
            if file_path.suffix.lower() == '.pdf':
                return self._read_pdf(file_path)
            elif file_path.suffix.lower() in ['.html', '.htm']:
                return self._read_html(file_path)
            elif file_path.suffix.lower() in ['.txt', '.md']:
                return self._read_text(file_path)
            else:
                # Try to read as text
                return self._read_text(file_path)
                
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return None
    
    def _read_pdf(self, file_path: Path) -> Optional[str]:
        """Read PDF content"""
        try:
            import PyPDF2
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text[:5000]  # Limit to 5000 chars for AI processing
        except ImportError:
            logger.warning("PyPDF2 not installed. PDF content cannot be read.")
            return None
        except Exception as e:
            logger.error(f"Failed to read PDF {file_path}: {e}")
            return None
    
    def _read_html(self, file_path: Path) -> Optional[str]:
        """Read HTML content"""
        try:
            from bs4 import BeautifulSoup
            with open(file_path, 'r', encoding='utf-8') as file:
                soup = BeautifulSoup(file.read(), 'html.parser')
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                text = soup.get_text()
                # Clean up whitespace
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = ' '.join(chunk for chunk in chunks if chunk)
                return text[:5000]  # Limit to 5000 chars
        except ImportError:
            logger.warning("BeautifulSoup not installed. HTML content cannot be parsed.")
            return None
        except Exception as e:
            logger.error(f"Failed to read HTML {file_path}: {e}")
            return None
    
    def _read_text(self, file_path: Path) -> Optional[str]:
        """Read text content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                return content[:5000]  # Limit to 5000 chars
        except Exception as e:
            logger.error(f"Failed to read text file {file_path}: {e}")
            return None
    
    def _create_analysis_prompt(self, content: str, search_criteria: str) -> str:
        """Create prompt for AI analysis"""
        return f"""You are an expert document analyzer. Analyze the following content and determine if it's relevant to the search criteria.

SEARCH CRITERIA: {search_criteria}

CONTENT:
{content}

Please provide your analysis in the following JSON format:
{{
    "relevant": true/false,
    "score": 0.0-1.0,
    "summary": "Brief summary of the content",
    "reason": "Why it is or isn't relevant",
    "key_points": ["point1", "point2", "point3"],
    "file_links": ["any downloadable file links found in the content"]
}}

Focus on:
1. Whether the content matches the search criteria
2. Quality and depth of information
3. Any downloadable files or resources mentioned
4. Key points that make it relevant or irrelevant

Respond only with valid JSON. Do not include any other text or explanation."""

    def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """Parse AI response and extract analysis"""
        try:
            import json
            # Clean up response text
            response_text = response_text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            analysis = json.loads(response_text)
            
            # Ensure required fields
            return {
                'relevant': analysis.get('relevant', False),
                'score': float(analysis.get('score', 0.0)),
                'summary': analysis.get('summary', ''),
                'reason': analysis.get('reason', ''),
                'key_points': analysis.get('key_points', []),
                'file_links': analysis.get('file_links', [])
            }
            
        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            return {
                'relevant': False,
                'score': 0.0,
                'summary': 'Failed to parse AI response',
                'reason': 'JSON parsing error',
                'key_points': [],
                'file_links': []
            }
    
    async def batch_analyze(self, file_paths: List[str], search_criteria: str) -> List[Dict[str, Any]]:
        """Analyze multiple files in batch"""
        results = []
        
        for file_path in file_paths:
            try:
                analysis = await self.analyze_content(file_path, search_criteria)
                analysis['file_path'] = file_path
                results.append(analysis)
            except Exception as e:
                logger.error(f"Batch analysis failed for {file_path}: {e}")
                results.append({
                    'file_path': file_path,
                    'relevant': False,
                    'score': 0.0,
                    'summary': f'Analysis failed: {str(e)}',
                    'reason': 'Batch analysis error',
                    'key_points': [],
                    'file_links': []
                })
        
        return results
