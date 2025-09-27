"""
AI Criteria Analyzer for flexible document evaluation
"""
import logging
from typing import Dict, List, Any, Optional
import json

logger = logging.getLogger(__name__)

class CriteriaAnalyzer:
    """AI-powered criteria analysis and flexible document evaluation"""
    
    def __init__(self, ai_analyzer):
        self.ai_analyzer = ai_analyzer
    
    async def analyze_criteria(self, criteria_text: str) -> Dict[str, Any]:
        """
        Analyze user criteria and break down into specific, actionable criteria
        
        Args:
            criteria_text: Raw criteria text from user
            
        Returns:
            Dict with analyzed criteria breakdown
        """
        try:
            prompt = self._create_criteria_analysis_prompt(criteria_text)
            response = await self.ai_analyzer.analyze_text_content(prompt, "Criteria analysis")
            
            analyzed_criteria = self._parse_criteria_response(response, criteria_text)
            logger.info(f"Analyzed criteria: {len(analyzed_criteria.get('specific_criteria', []))} specific criteria identified")
            
            return analyzed_criteria
            
        except Exception as e:
            logger.error(f"Criteria analysis failed: {e}")
            # Fallback to original criteria
            return {
                'original_criteria': criteria_text,
                'specific_criteria': [criteria_text],
                'categories': ['general'],
                'flexible_evaluation': True,
                'min_criteria_met': 1,
                'analysis_confidence': 0.5
            }
    
    def _create_criteria_analysis_prompt(self, criteria_text: str) -> str:
        """Create prompt for criteria analysis"""
        
        prompt = f"""
You are an expert document evaluation analyst. Your task is to analyze the following criteria and break it down into specific, actionable evaluation criteria.

ORIGINAL CRITERIA: "{criteria_text}"

ANALYSIS TASK:
1. Break down the criteria into specific, measurable evaluation points
2. Identify different categories/types of criteria
3. Determine if flexible evaluation (meeting ANY criteria) is appropriate
4. Set minimum number of criteria that must be met for a document to be considered relevant

GUIDELINES:
- Each specific criteria should be clear and actionable
- Consider both technical and content-based criteria
- Identify related terms and synonyms
- Consider different levels of specificity (exact match vs. related concepts)
- For technical documents, consider both detailed specifications and general concepts

OUTPUT FORMAT (JSON):
{{
    "original_criteria": "original criteria text",
    "specific_criteria": [
        "specific criterion 1",
        "specific criterion 2",
        ...
    ],
    "categories": [
        "category1",
        "category2",
        ...
    ],
    "flexible_evaluation": true/false,
    "min_criteria_met": number,
    "analysis_confidence": 0.0-1.0,
    "reasoning": "explanation of analysis approach"
}}

IMPORTANT: Return ONLY valid JSON, no additional text.
"""
        return prompt
    
    def _parse_criteria_response(self, response: str, original_criteria: str) -> Dict[str, Any]:
        """Parse AI response for criteria analysis"""
        try:
            # Clean response
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            
            # Parse JSON
            data = json.loads(response)
            
            # Validate and structure response
            result = {
                'original_criteria': original_criteria,
                'specific_criteria': data.get('specific_criteria', [original_criteria]),
                'categories': data.get('categories', ['general']),
                'flexible_evaluation': data.get('flexible_evaluation', True),
                'min_criteria_met': data.get('min_criteria_met', 1),
                'analysis_confidence': float(data.get('analysis_confidence', 0.7)),
                'reasoning': data.get('reasoning', 'AI analyzed criteria')
            }
            
            # Ensure we have at least one specific criteria
            if not result['specific_criteria']:
                result['specific_criteria'] = [original_criteria]
            
            return result
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse criteria analysis response: {e}")
            # Return fallback
            return {
                'original_criteria': original_criteria,
                'specific_criteria': [original_criteria],
                'categories': ['general'],
                'flexible_evaluation': True,
                'min_criteria_met': 1,
                'analysis_confidence': 0.5,
                'reasoning': 'Failed to parse AI response'
            }
    
    async def evaluate_document_against_criteria(self, document_content: str, 
                                               analyzed_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a document against analyzed criteria
        
        Args:
            document_content: Content of the document to evaluate
            analyzed_criteria: Analyzed criteria from analyze_criteria()
            
        Returns:
            Evaluation results
        """
        try:
            specific_criteria = analyzed_criteria.get('specific_criteria', [])
            flexible_evaluation = analyzed_criteria.get('flexible_evaluation', True)
            min_criteria_met = analyzed_criteria.get('min_criteria_met', 1)
            
            # Create evaluation prompt
            prompt = self._create_evaluation_prompt(document_content, specific_criteria, 
                                                  flexible_evaluation, min_criteria_met)
            
            response = await self.ai_analyzer.analyze_text_content(prompt, "Document evaluation")
            
            # Parse evaluation results
            evaluation_result = self._parse_evaluation_response(response, analyzed_criteria)
            
            return evaluation_result
            
        except Exception as e:
            logger.error(f"Document evaluation failed: {e}")
            return {
                'relevant': False,
                'score': 0.0,
                'criteria_met': [],
                'criteria_not_met': analyzed_criteria.get('specific_criteria', []),
                'summary': 'Evaluation failed',
                'confidence': 0.0
            }
    
    def _create_evaluation_prompt(self, document_content: str, specific_criteria: List[str], 
                                flexible_evaluation: bool, min_criteria_met: int) -> str:
        """Create prompt for document evaluation"""
        
        criteria_list = '\n'.join([f"- {criterion}" for criterion in specific_criteria])
        
        prompt = f"""
You are an expert document evaluator. Your task is to evaluate whether this document meets the specified criteria.

DOCUMENT CONTENT (first 2000 characters):
{document_content[:2000]}...

EVALUATION CRITERIA:
{criteria_list}

EVALUATION RULES:
- Flexible evaluation: {flexible_evaluation}
- Minimum criteria to meet: {min_criteria_met}
- Score range: 0.0 (no match) to 1.0 (perfect match)
- Consider both exact matches and related concepts

OUTPUT FORMAT (JSON):
{{
    "relevant": true/false,
    "score": 0.0-1.0,
    "criteria_met": [
        "criterion that was met",
        ...
    ],
    "criteria_not_met": [
        "criterion that was not met",
        ...
    ],
    "summary": "brief explanation of evaluation",
    "confidence": 0.0-1.0
}}

EVALUATION GUIDELINES:
- Be flexible but accurate in matching criteria
- Consider synonyms and related terms
- Focus on content relevance rather than exact wording
- For technical documents, consider both detailed specs and general concepts

IMPORTANT: Return ONLY valid JSON, no additional text.
"""
        return prompt
    
    def _parse_evaluation_response(self, response: str, analyzed_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Parse evaluation response"""
        try:
            # Clean response
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            
            # Parse JSON
            data = json.loads(response)
            
            # Validate and structure response
            result = {
                'relevant': bool(data.get('relevant', False)),
                'score': float(data.get('score', 0.0)),
                'criteria_met': data.get('criteria_met', []),
                'criteria_not_met': data.get('criteria_not_met', []),
                'summary': data.get('summary', 'No summary provided'),
                'confidence': float(data.get('confidence', 0.5)),
                'analysis_metadata': analyzed_criteria
            }
            
            # Validate score range
            result['score'] = max(0.0, min(1.0, result['score']))
            
            return result
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse evaluation response: {e}")
            return {
                'relevant': False,
                'score': 0.0,
                'criteria_met': [],
                'criteria_not_met': analyzed_criteria.get('specific_criteria', []),
                'summary': 'Evaluation parsing failed',
                'confidence': 0.0,
                'analysis_metadata': analyzed_criteria
            }
