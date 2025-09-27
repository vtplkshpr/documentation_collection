"""
Ollama client for AI content analysis in documentation collection
"""
import logging
import httpx
import hashlib
import json
import asyncio
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class OllamaClient:
    """Client for interacting with Ollama local AI models"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model = "llama2"
        self.cache = {}  # Simple in-memory cache
        self.max_cache_size = 1000
        self.semaphore = asyncio.Semaphore(2)  # Limit concurrent requests for 4 CPU machine
        
        # Template-based optimization
        self.query_templates = {
            "technical": ["technical specifications", "engineering details", "design documents"],
            "military": ["military equipment", "defense systems", "naval vessels"],
            "ship": ["ship design", "vessel specifications", "maritime engineering"],
            "malaysia": ["Malaysian", "Malaysia", "Royal Malaysian Navy"]
        }
        
    async def is_available(self) -> bool:
        """Check if Ollama server is available"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = data.get("models", [])
                    logger.info(f"Ollama server available with {len(models)} models")
                    return len(models) > 0
                return False
        except Exception as e:
            logger.error(f"Ollama server not available: {e}")
            return False
    
    def _get_cache_key(self, prompt: str) -> str:
        """Generate cache key for prompt"""
        return hashlib.md5(prompt.encode()).hexdigest()
    
    def _get_from_cache(self, prompt: str) -> Optional[str]:
        """Get response from cache"""
        key = self._get_cache_key(prompt)
        return self.cache.get(key)
    
    def _save_to_cache(self, prompt: str, response: str):
        """Save response to cache"""
        key = self._get_cache_key(prompt)
        
        # Simple LRU: remove oldest if cache is full
        if len(self.cache) >= self.max_cache_size:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        
        self.cache[key] = response
    
    async def analyze_text_content(self, prompt: str, analysis_type: str = "Content analysis") -> str:
        """
        Analyze text content using Ollama with caching
        
        Args:
            prompt: Text prompt for analysis
            analysis_type: Type of analysis being performed
            
        Returns:
            AI response as string
        """
        # Check cache first
        cached_response = self._get_from_cache(prompt)
        if cached_response:
            logger.info("Using cached response")
            return cached_response
        
        if not await self.is_available():
            return "Ollama server not available"
        
        try:
            # Use semaphore to limit concurrent requests
            async with self.semaphore:
                # Prepare the request payload
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Lower temperature for consistency
                        "top_p": 0.8,
                        "max_tokens": 200,   # Much shorter responses for speed
                        "repeat_penalty": 1.0,
                        "num_ctx": 2048,     # Smaller context window
                        "num_predict": 100   # Limit prediction tokens
                    }
                }
                
                async with httpx.AsyncClient(timeout=120.0) as client:
                    response = await client.post(
                        f"{self.base_url}/api/generate",
                        json=payload
                    )
                    
                    if response.status_code == 200:
                        try:
                            result = response.json()
                            ai_response = result.get("response", "")
                            if ai_response and ai_response.strip():
                                logger.info(f"Ollama response received: {len(ai_response)} characters")
                                response_text = ai_response.strip()
                                # Cache successful responses
                                self._save_to_cache(prompt, response_text)
                                return response_text
                            else:
                                logger.warning("Empty or whitespace-only response from Ollama")
                                return "No response generated"
                        except Exception as json_error:
                            logger.error(f"Failed to parse Ollama response JSON: {json_error}")
                            logger.error(f"Raw response: {response.text[:200]}...")
                            return "Failed to parse response"
                    else:
                        logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                        return f"Analysis failed: HTTP {response.status_code}"
                    
        except Exception as e:
            logger.error(f"Text analysis failed: {e}")
            logger.error(f"Exception type: {type(e)}")
            logger.error(f"Exception details: {str(e)}")
            return f"Analysis failed: {e}"
    
    async def analyze_text_content_streaming(self, prompt: str, analysis_type: str = "Content analysis") -> str:
        """
        Analyze text content using Ollama with streaming for faster response
        """
        if not await self.is_available():
            return "Ollama server not available"
        
        try:
            # Prepare the request payload for streaming
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": True,  # Enable streaming
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.8,
                    "max_tokens": 200,
                    "repeat_penalty": 1.0,
                    "num_ctx": 2048,
                    "num_predict": 100
                }
            }
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                full_response = ""
                async with client.stream(
                    'POST',
                    f"{self.base_url}/api/generate",
                    json=payload
                ) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            if line.strip():
                                try:
                                    import json
                                    data = json.loads(line)
                                    if data.get("response"):
                                        full_response += data["response"]
                                    if data.get("done", False):
                                        break
                                except json.JSONDecodeError:
                                    continue
                        
                        if full_response.strip():
                            logger.info(f"Ollama streaming response received: {len(full_response)} characters")
                            return full_response.strip()
                        else:
                            logger.warning("Empty streaming response from Ollama")
                            return "No response generated"
                    else:
                        logger.error(f"Ollama streaming API error: {response.status_code}")
                        return f"Analysis failed: HTTP {response.status_code}"
                        
        except Exception as e:
            logger.error(f"Streaming analysis failed: {e}")
            return f"Analysis failed: {e}"
    
    async def generate_optimized_queries(self, original_query: str, target_language: str, search_engine: str, max_queries: int = 3) -> list:
        """
        Generate optimized search queries using Ollama
        
        Args:
            original_query: Original search query
            target_language: Target language for search
            search_engine: Search engine name
            max_queries: Maximum number of queries to generate
            
        Returns:
            List of optimized queries
        """
        prompt = self._create_query_optimization_prompt(original_query, target_language, search_engine, max_queries)
        response = await self.analyze_text_content(prompt, "Query optimization")
        return self._parse_query_response(response, original_query, max_queries)
    
    async def analyze_criteria(self, criteria_text: str) -> Dict[str, Any]:
        """
        Analyze and break down criteria using Ollama
        
        Args:
            criteria_text: Raw criteria text
            
        Returns:
            Analyzed criteria dictionary
        """
        prompt = self._create_criteria_analysis_prompt(criteria_text)
        response = await self.analyze_text_content(prompt, "Criteria analysis")
        return self._parse_criteria_response(response, criteria_text)
    
    async def evaluate_document(self, document_content: str, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate document against criteria using Ollama
        
        Args:
            document_content: Document text content
            criteria: Analyzed criteria dictionary
            
        Returns:
            Evaluation result dictionary
        """
        prompt = self._create_evaluation_prompt(document_content, criteria)
        response = await self.analyze_text_content(prompt, "Document evaluation")
        return self._parse_evaluation_response(response, criteria)
    
    def _detect_query_type(self, query: str) -> str:
        """Detect query type for template-based optimization"""
        query_lower = query.lower()
        
        # Check for technical terms
        technical_terms = ["kỹ thuật", "technical", "specifications", "design", "engineering", "tính toán"]
        if any(term in query_lower for term in technical_terms):
            return "technical"
        
        # Check for military terms
        military_terms = ["quân sự", "military", "naval", "defense", "tàu", "ship", "vessel"]
        if any(term in query_lower for term in military_terms):
            return "military"
        
        # Check for ship-related terms
        ship_terms = ["tàu", "ship", "vessel", "naval", "maritime", "hộ tống"]
        if any(term in query_lower for term in ship_terms):
            return "ship"
        
        # Check for Malaysia
        if "malaysia" in query_lower or "malaysian" in query_lower:
            return "malaysia"
        
        return "general"
    
    def _create_query_optimization_prompt(self, original_query: str, target_language: str, search_engine: str, max_queries: int) -> str:
        """Create prompt for query optimization - template-based for speed"""
        # Truncate long queries to avoid timeout
        if len(original_query) > 100:
            original_query = original_query[:100] + "..."
        
        # Use template-based optimization
        query_type = self._detect_query_type(original_query)
        if query_type in self.query_templates:
            template_terms = self.query_templates[query_type]
            return f"""Q: "{original_query}" 
Type: {query_type} Terms: {template_terms[0]}
L: {target_language} E: {search_engine}
Return: ["q1", "q2"]"""
        
        return f"""Q: "{original_query}" 
L: {target_language} E: {search_engine}
Return: ["q1", "q2"]"""

    def _chunk_criteria(self, criteria_text: str) -> List[str]:
        """Split criteria into smaller chunks for better processing"""
        # Split by semicolons and periods
        chunks = []
        for delimiter in [';', '.', '\n']:
            if delimiter in criteria_text:
                chunks = [chunk.strip() for chunk in criteria_text.split(delimiter) if chunk.strip()]
                break
        
        # If no delimiters found, split by length
        if not chunks:
            max_length = 100
            words = criteria_text.split()
            current_chunk = ""
            for word in words:
                if len(current_chunk + " " + word) <= max_length:
                    current_chunk += " " + word if current_chunk else word
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = word
            if current_chunk:
                chunks.append(current_chunk)
        
        # Limit to 3 chunks maximum
        return chunks[:3]
    
    def _create_criteria_analysis_prompt(self, criteria_text: str) -> str:
        """Create prompt for criteria analysis - chunked for speed"""
        # Use chunking for long criteria
        chunks = self._chunk_criteria(criteria_text)
        
        if len(chunks) > 1:
            # Use first chunk for analysis
            criteria_chunk = chunks[0]
        else:
            criteria_chunk = criteria_text
        
        # Truncate if still too long
        if len(criteria_chunk) > 150:
            criteria_chunk = criteria_chunk[:150] + "..."
        
        return f"""C: "{criteria_chunk}"
Return: {{"specific_criteria": ["c1", "c2"], "flexible_evaluation": true, "min_criteria_met": 1}}"""

    def _create_evaluation_prompt(self, document_content: str, criteria: Dict[str, Any]) -> str:
        """Create prompt for document evaluation - simplified for speed"""
        specific_criteria = criteria.get("specific_criteria", [])
        criteria_text = " ".join(specific_criteria)
        
        # Further limit content for speed
        content_preview = document_content[:500] + "..." if len(document_content) > 500 else document_content
        criteria_text = criteria_text[:100] + "..." if len(criteria_text) > 100 else criteria_text
        
        return f"""Doc: {content_preview}
C: {criteria_text}
Return: {{"is_relevant": true/false, "score": 0.5, "reason": "brief"}}"""

    def _parse_query_response(self, response: str, original_query: str, max_queries: int) -> list:
        """Parse query optimization response with better error handling"""
        try:
            import json
            import re

            # Clean response
            response = response.strip()
            logger.info(f"Parsing query response (length: {len(response)}): {response[:200]}...")

            # Handle empty or error responses
            if not response or "No response generated" in response or "Analysis failed" in response:
                logger.warning("Empty or error response, using original query")
                return [original_query]

            # Try multiple parsing strategies
            parsing_strategies = [
                # Strategy 1: Direct JSON array
                lambda r: json.loads(r) if r.startswith('[') and r.endswith(']') else None,
                
                # Strategy 2: Extract JSON array with regex
                lambda r: self._extract_json_array_regex(r),
                
                # Strategy 3: Extract from code blocks
                lambda r: self._extract_from_code_blocks(r),
                
                # Strategy 4: Split by common delimiters
                lambda r: self._extract_from_delimiters(r),
                
                # Strategy 5: Extract quoted strings
                lambda r: self._extract_quoted_strings(r)
            ]

            for strategy in parsing_strategies:
                try:
                    result = strategy(response)
                    if result and isinstance(result, list) and len(result) > 0:
                        logger.info(f"Successfully parsed {len(result)} queries using strategy")
                        return result[:max_queries]
                except Exception as e:
                    logger.debug(f"Strategy failed: {e}")
                    continue

            # Final fallback: generate variations of original query
            logger.warning(f"All parsing strategies failed, generating query variations from: {original_query}")
            return self._generate_query_variations(original_query, max_queries)

        except Exception as e:
            logger.error(f"Failed to parse query response: {e}")
            return [original_query]

    def _extract_json_array_regex(self, response: str) -> list:
        """Extract JSON array using regex"""
        import json
        import re
        
        # Try to find JSON array patterns
        patterns = [
            r'\[[\s\S]*?\]',  # Standard JSON array
            r'```json\s*\[[\s\S]*?\]\s*```',  # JSON in code block
            r'```\s*\[[\s\S]*?\]\s*```',  # Array in code block
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response, re.DOTALL)
            for match in matches:
                try:
                    result = json.loads(match)
                    if isinstance(result, list):
                        return result
                except json.JSONDecodeError:
                    continue
        return None

    def _extract_from_code_blocks(self, response: str) -> list:
        """Extract queries from code blocks"""
        import json
        import re
        
        # Look for code blocks
        code_blocks = re.findall(r'```[\s\S]*?```', response)
        for block in code_blocks:
            content = block.replace('```', '').strip()
            try:
                # Try to parse as JSON
                if content.startswith('['):
                    result = json.loads(content)
                    if isinstance(result, list):
                        return result
            except json.JSONDecodeError:
                # Try to split by lines
                lines = [line.strip().strip('"\'') for line in content.split('\n') if line.strip()]
                if lines:
                    return lines
        return None

    def _extract_from_delimiters(self, response: str) -> list:
        """Extract queries by splitting on common delimiters"""
        # Try different delimiters
        delimiters = ['\n', ',', ';', '|']
        
        for delimiter in delimiters:
            if delimiter in response:
                parts = [part.strip().strip('"\'[]') for part in response.split(delimiter) if part.strip()]
                if len(parts) > 1:
                    return parts
        return None

    def _extract_quoted_strings(self, response: str) -> list:
        """Extract quoted strings from response"""
        import re
        
        # Find all quoted strings
        quoted_strings = re.findall(r'"([^"]*)"', response)
        if quoted_strings:
            return [q.strip() for q in quoted_strings if q.strip()]
        
        # Find single quoted strings
        single_quoted = re.findall(r"'([^']*)'", response)
        if single_quoted:
            return [q.strip() for q in single_quoted if q.strip()]
        
        return None

    def _generate_query_variations(self, original_query: str, max_queries: int) -> list:
        """Generate simple query variations when parsing fails"""
        variations = [original_query]
        
        # Add simple variations based on common patterns
        if len(original_query.split()) > 1:
            # Add without articles
            words = original_query.split()
            filtered_words = [w for w in words if w.lower() not in ['the', 'a', 'an', 'of', 'in', 'on', 'at', 'to', 'for']]
            if filtered_words and len(filtered_words) != len(words):
                variations.append(' '.join(filtered_words))
            
            # Add with "specifications" if not present
            if 'specification' not in original_query.lower():
                variations.append(f"{original_query} specifications")
            
            # Add with "details" if not present
            if 'detail' not in original_query.lower():
                variations.append(f"{original_query} details")
        
        return variations[:max_queries]
    
    def _parse_criteria_response(self, response: str, original_criteria: str) -> Dict[str, Any]:
        """Parse criteria analysis response with better error handling"""
        try:
            import json
            import re
            
            # Clean response
            response = response.strip()
            logger.info(f"Parsing criteria response (length: {len(response)}): {response[:200]}...")

            # Try multiple parsing strategies
            parsing_strategies = [
                # Strategy 1: Direct JSON object
                lambda r: json.loads(r) if r.startswith('{') and r.endswith('}') else None,
                
                # Strategy 2: Extract JSON object with regex
                lambda r: self._extract_json_object_regex(r),
                
                # Strategy 3: Extract from code blocks
                lambda r: self._extract_json_from_code_blocks(r),
                
                # Strategy 4: Parse key-value pairs
                lambda r: self._parse_key_value_pairs(r)
            ]

            for strategy in parsing_strategies:
                try:
                    result = strategy(response)
                    if result and isinstance(result, dict):
                        logger.info(f"Successfully parsed criteria using strategy")
                        return result
                except Exception as e:
                    logger.debug(f"Criteria parsing strategy failed: {e}")
                    continue

            # Final fallback
            logger.warning(f"All criteria parsing strategies failed, using fallback for: {original_criteria}")
            return {
                "specific_criteria": [original_criteria],
                "flexible_evaluation": True,
                "min_criteria_met": 1
            }

        except Exception as e:
            logger.error(f"Failed to parse criteria response: {e}")
            return {
                "specific_criteria": [original_criteria],
                "flexible_evaluation": True,
                "min_criteria_met": 1
            }

    def _extract_json_object_regex(self, response: str) -> dict:
        """Extract JSON object using regex"""
        import json
        import re
        
        # Try to find JSON object patterns
        patterns = [
            r'\{[\s\S]*?\}',  # Standard JSON object
            r'```json\s*\{[\s\S]*?\}\s*```',  # JSON in code block
            r'```\s*\{[\s\S]*?\}\s*```',  # Object in code block
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response, re.DOTALL)
            for match in matches:
                try:
                    result = json.loads(match)
                    if isinstance(result, dict):
                        return result
                except json.JSONDecodeError:
                    continue
        return None

    def _extract_json_from_code_blocks(self, response: str) -> dict:
        """Extract JSON from code blocks"""
        import json
        import re
        
        # Look for code blocks
        code_blocks = re.findall(r'```[\s\S]*?```', response)
        for block in code_blocks:
            content = block.replace('```', '').strip()
            try:
                if content.startswith('{'):
                    result = json.loads(content)
                    if isinstance(result, dict):
                        return result
            except json.JSONDecodeError:
                continue
        return None

    def _parse_key_value_pairs(self, response: str) -> dict:
        """Parse key-value pairs from response"""
        import re
        
        # Look for common patterns
        patterns = {
            "specific_criteria": r'criteria[:\s]*\[(.*?)\]',
            "flexible_evaluation": r'flexible[:\s]*(true|false)',
            "min_criteria_met": r'min[:\s]*(\d+)'
        }
        
        result = {}
        
        # Extract specific criteria
        criteria_match = re.search(patterns["specific_criteria"], response, re.IGNORECASE)
        if criteria_match:
            criteria_text = criteria_match.group(1)
            criteria_list = [c.strip().strip('"\'') for c in criteria_text.split(',') if c.strip()]
            result["specific_criteria"] = criteria_list
        
        # Extract flexible evaluation
        flexible_match = re.search(patterns["flexible_evaluation"], response, re.IGNORECASE)
        if flexible_match:
            result["flexible_evaluation"] = flexible_match.group(1).lower() == 'true'
        
        # Extract min criteria met
        min_match = re.search(patterns["min_criteria_met"], response, re.IGNORECASE)
        if min_match:
            result["min_criteria_met"] = int(min_match.group(1))
        
        if result:
            # Fill missing fields with defaults
            result.setdefault("specific_criteria", ["general criteria"])
            result.setdefault("flexible_evaluation", True)
            result.setdefault("min_criteria_met", 1)
            return result
        
        return None
    
    def _parse_evaluation_response(self, response: str, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Parse document evaluation response with better error handling"""
        try:
            import json
            import re
            
            # Clean response
            response = response.strip()
            logger.info(f"Parsing evaluation response (length: {len(response)}): {response[:200]}...")

            # Try multiple parsing strategies
            parsing_strategies = [
                # Strategy 1: Direct JSON object
                lambda r: json.loads(r) if r.startswith('{') and r.endswith('}') else None,
                
                # Strategy 2: Extract JSON object with regex
                lambda r: self._extract_json_object_regex(r),
                
                # Strategy 3: Extract from code blocks
                lambda r: self._extract_json_from_code_blocks(r),
                
                # Strategy 4: Parse key-value pairs for evaluation
                lambda r: self._parse_evaluation_key_value_pairs(r)
            ]

            for strategy in parsing_strategies:
                try:
                    result = strategy(response)
                    if result and isinstance(result, dict):
                        logger.info(f"Successfully parsed evaluation using strategy")
                        # Ensure required fields
                        return self._normalize_evaluation_result(result)
                except Exception as e:
                    logger.debug(f"Evaluation parsing strategy failed: {e}")
                    continue

            # Final fallback
            logger.warning(f"All evaluation parsing strategies failed, using fallback")
            return {
                "is_relevant": False,
                "criteria_met": [],
                "confidence_score": 0.0,
                "reasoning": "Failed to parse AI response"
            }

        except Exception as e:
            logger.error(f"Failed to parse evaluation response: {e}")
            return {
                "is_relevant": False,
                "criteria_met": [],
                "confidence_score": 0.0,
                "reasoning": f"Parse error: {e}"
            }

    def _parse_evaluation_key_value_pairs(self, response: str) -> dict:
        """Parse evaluation key-value pairs from response"""
        import re
        
        result = {}
        
        # Look for relevance indicators
        relevance_patterns = [
            r'is_relevant[:\s]*(true|false)',
            r'relevant[:\s]*(true|false)',
            r'yes|no|true|false'
        ]
        
        for pattern in relevance_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                value = match.group(1) if len(match.groups()) > 0 else match.group(0)
                if value.lower() in ['true', 'yes']:
                    result["is_relevant"] = True
                elif value.lower() in ['false', 'no']:
                    result["is_relevant"] = False
                break
        
        # Look for score
        score_patterns = [
            r'score[:\s]*([0-9.]+)',
            r'confidence[:\s]*([0-9.]+)',
            r'([0-9.]+)/10',
            r'([0-9.]+)%'
        ]
        
        for pattern in score_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                try:
                    score = float(match.group(1))
                    # Normalize score to 0-1 range
                    if score > 10:
                        score = score / 10
                    elif score > 1:
                        score = score / 100
                    result["confidence_score"] = min(1.0, max(0.0, score))
                    break
                except ValueError:
                    continue
        
        # Look for reasoning
        reasoning_patterns = [
            r'reason[:\s]*["\']?([^"\'\n]+)["\']?',
            r'explanation[:\s]*["\']?([^"\'\n]+)["\']?',
            r'because[:\s]*["\']?([^"\'\n]+)["\']?'
        ]
        
        for pattern in reasoning_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                result["reasoning"] = match.group(1).strip()
                break
        
        return result if result else None

    def _normalize_evaluation_result(self, result: dict) -> dict:
        """Normalize evaluation result to ensure required fields"""
        normalized = {
            "is_relevant": result.get("is_relevant", False),
            "criteria_met": result.get("criteria_met", []),
            "confidence_score": float(result.get("confidence_score", 0.0)),
            "reasoning": result.get("reasoning", "AI evaluation")
        }
        
        # Ensure confidence score is in valid range
        normalized["confidence_score"] = max(0.0, min(1.0, normalized["confidence_score"]))
        
        # Ensure criteria_met is a list
        if not isinstance(normalized["criteria_met"], list):
            normalized["criteria_met"] = []
        
        return normalized
