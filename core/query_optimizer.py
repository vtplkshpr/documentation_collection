"""
AI Query Optimizer for enhancing search effectiveness
"""
import logging
from typing import Dict, List, Any, Optional
import json

logger = logging.getLogger(__name__)

class QueryOptimizer:
    """AI-powered query optimization for different search engines and languages"""
    
    def __init__(self, ai_analyzer):
        self.ai_analyzer = ai_analyzer
    
    async def optimize_query_for_search(self, original_query: str, target_language: str, 
                                      search_engine: str, max_queries: int = 5) -> List[Dict[str, Any]]:
        """
        Optimize query for specific search engine and language
        
        Args:
            original_query: Original user query
            target_language: Target language code
            search_engine: Search engine name (google, bing, duckduckgo)
            max_queries: Maximum number of optimized queries to generate
        
        Returns:
            List of optimized queries with metadata
        """
        try:
            # Create optimization prompt
            prompt = self._create_optimization_prompt(original_query, target_language, search_engine, max_queries)
            
            # Get AI response
            response = await self.ai_analyzer.analyze_text_content(prompt, "Query optimization")
            
            # Parse optimized queries
            optimized_queries = self._parse_optimization_response(response, original_query)
            
            logger.info(f"Generated {len(optimized_queries)} optimized queries for {search_engine} in {target_language}")
            return optimized_queries
            
        except Exception as e:
            logger.error(f"Query optimization failed: {e}")
            # Fallback to simple translation
            return [{
                'query': original_query,
                'language': target_language,
                'engine': search_engine,
                'optimization_type': 'fallback',
                'confidence': 0.5,
                'reasoning': 'Fallback due to optimization error'
            }]
    
    def _create_optimization_prompt(self, original_query: str, target_language: str, 
                                  search_engine: str, max_queries: int) -> str:
        """Create prompt for query optimization"""
        
        language_names = {
            'en': 'English',
            'vi': 'Vietnamese', 
            'ja': 'Japanese',
            'ko': 'Korean',
            'ru': 'Russian',
            'fa': 'Persian'
        }
        
        target_lang_name = language_names.get(target_language, target_language)
        
        prompt = f"""
You are an expert search query optimizer. Your task is to optimize the following query for better search results on {search_engine} in {target_lang_name}.

ORIGINAL QUERY: "{original_query}"

TARGET: {search_engine} search engine in {target_lang_name}
MAX QUERIES: {max_queries}

OPTIMIZATION GUIDELINES:
1. Break down complex queries into simpler, more searchable terms
2. Use keywords that are commonly used in {target_lang_name} for the topic
3. Create variations with different levels of specificity (broad to specific)
4. Consider synonyms and alternative terms in {target_lang_name}
5. Adapt for {search_engine}'s search behavior and indexing
6. Include both general and specific technical terms where relevant

SEARCH ENGINE SPECIFIC CONSIDERATIONS:
- Google: Prefer natural language, support complex queries
- Bing: Good with technical terms, prefer shorter queries
- DuckDuckGo: Similar to Google but more privacy-focused

OUTPUT FORMAT (JSON):
{{
    "optimized_queries": [
        {{
            "query": "optimized search query",
            "type": "broad|specific|technical|alternative",
            "confidence": 0.0-1.0,
            "reasoning": "why this query should work better"
        }}
    ]
}}

IMPORTANT: Return ONLY valid JSON, no additional text.
"""
        return prompt
    
    def _parse_optimization_response(self, response: str, original_query: str) -> List[Dict[str, Any]]:
        """Parse AI response to extract optimized queries"""
        try:
            # Clean response
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            
            # Parse JSON
            data = json.loads(response)
            optimized_queries = data.get('optimized_queries', [])
            
            # Validate and add metadata
            result = []
            for query_data in optimized_queries:
                if isinstance(query_data, dict) and 'query' in query_data:
                    result.append({
                        'query': query_data['query'],
                        'type': query_data.get('type', 'optimized'),
                        'confidence': float(query_data.get('confidence', 0.7)),
                        'reasoning': query_data.get('reasoning', 'AI optimized'),
                        'original_query': original_query
                    })
            
            # Ensure we have at least one query
            if not result:
                result.append({
                    'query': original_query,
                    'type': 'fallback',
                    'confidence': 0.5,
                    'reasoning': 'No optimization generated',
                    'original_query': original_query
                })
            
            return result
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse optimization response: {e}")
            # Return fallback
            return [{
                'query': original_query,
                'type': 'fallback',
                'confidence': 0.5,
                'reasoning': 'Failed to parse AI response',
                'original_query': original_query
            }]
    
    async def generate_all_optimized_queries(self, original_query: str, 
                                           languages: List[str], 
                                           search_engines: List[str]) -> Dict[str, Dict[str, List[Dict]]]:
        """
        Generate optimized queries for all language-engine combinations
        
        Returns:
            Dict structure: {language: {engine: [optimized_queries]}}
        """
        all_optimized = {}
        
        for language in languages:
            all_optimized[language] = {}
            for engine in search_engines:
                try:
                    optimized = await self.optimize_query_for_search(original_query, language, engine)
                    all_optimized[language][engine] = optimized
                except Exception as e:
                    logger.error(f"Failed to optimize for {language}-{engine}: {e}")
                    all_optimized[language][engine] = [{
                        'query': original_query,
                        'type': 'fallback',
                        'confidence': 0.5,
                        'reasoning': 'Optimization failed',
                        'original_query': original_query
                    }]
        
        return all_optimized
    
    def export_optimized_queries_to_csv(self, optimized_queries: Dict[str, Dict[str, List[Dict]]], 
                                      output_path: str) -> str:
        """Export optimized queries to CSV for analysis"""
        try:
            import pandas as pd
            
            # Flatten the data structure
            flattened_data = []
            for language, engines in optimized_queries.items():
                for engine, queries in engines.items():
                    for query_data in queries:
                        flattened_data.append({
                            'original_query': query_data.get('original_query', ''),
                            'optimized_query': query_data.get('query', ''),
                            'language': language,
                            'search_engine': engine,
                            'optimization_type': query_data.get('type', ''),
                            'confidence': query_data.get('confidence', 0.0),
                            'reasoning': query_data.get('reasoning', '')
                        })
            
            # Create DataFrame and save
            df = pd.DataFrame(flattened_data)
            df.to_csv(output_path, index=False, encoding='utf-8-sig')  # UTF-8 with BOM for Excel compatibility
            
            logger.info(f"Exported {len(flattened_data)} optimized queries to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to export optimized queries: {e}")
            return ""
