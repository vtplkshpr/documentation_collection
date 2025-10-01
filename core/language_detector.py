"""
Language detection utility for query analysis
"""
import logging
import re
from typing import Optional, Dict, Any
from utils.config import config

logger = logging.getLogger(__name__)

class LanguageDetector:
    """Language detection for user queries"""
    
    def __init__(self):
        # Language detection patterns
        self.language_patterns = {
            'zh': {
                'name': 'Chinese',
                'patterns': [
                    r'[\u4e00-\u9fff]',  # CJK Unified Ideographs
                    r'[\u3400-\u4dbf]',  # CJK Extension A
                    r'[\u20000-\u2a6df]'  # CJK Extension B
                ],
                'keywords': ['的', '是', '在', '有', '和', '与', '或', '但', '因为', '所以']
            },
            'ja': {
                'name': 'Japanese',
                'patterns': [
                    r'[\u3040-\u309f]',  # Hiragana
                    r'[\u30a0-\u30ff]',  # Katakana
                    r'[\u4e00-\u9fff]'   # Kanji (shared with Chinese)
                ],
                'keywords': ['です', 'ます', 'である', 'する', 'ある', 'いる', 'です', 'でした']
            },
            'ko': {
                'name': 'Korean',
                'patterns': [
                    r'[\uac00-\ud7af]',  # Hangul Syllables
                    r'[\u1100-\u11ff]',  # Hangul Jamo
                    r'[\u3130-\u318f]'   # Hangul Compatibility Jamo
                ],
                'keywords': ['이다', '있다', '하다', '되다', '이다', '입니다', '합니다']
            },
            'ar': {
                'name': 'Arabic',
                'patterns': [
                    r'[\u0600-\u06ff]',  # Arabic
                    r'[\u0750-\u077f]',  # Arabic Supplement
                    r'[\u08a0-\u08ff]'   # Arabic Extended-A
                ],
                'keywords': ['في', 'من', 'إلى', 'على', 'هذا', 'هذه', 'التي', 'الذي']
            },
            'fa': {
                'name': 'Persian',
                'patterns': [
                    r'[\u0600-\u06ff]',  # Arabic (Persian uses Arabic script)
                    r'[\u0750-\u077f]',  # Arabic Supplement
                    r'[\u08a0-\u08ff]'   # Arabic Extended-A
                ],
                'keywords': ['است', 'هست', 'می', 'خواهد', 'بود', 'شد', 'کرد', 'گفت']
            },
            'ru': {
                'name': 'Russian',
                'patterns': [
                    r'[\u0400-\u04ff]',  # Cyrillic
                    r'[\u0500-\u052f]'   # Cyrillic Supplement
                ],
                'keywords': ['и', 'в', 'на', 'с', 'по', 'для', 'от', 'до', 'что', 'как']
            },
            'vi': {
                'name': 'Vietnamese',
                'patterns': [
                    r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]',
                    r'[ÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]'
                ],
                'keywords': ['và', 'của', 'trong', 'với', 'cho', 'từ', 'đến', 'là', 'có', 'được']
            },
            'en': {
                'name': 'English',
                'patterns': [
                    r'[a-zA-Z]'
                ],
                'keywords': ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
            }
        }
    
    def detect_language(self, text: str) -> Dict[str, Any]:
        """
        Detect language of input text
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary with language detection results
        """
        if not text or not text.strip():
            return {
                'language': 'en',
                'confidence': 0.0,
                'reasoning': 'Empty text, defaulting to English'
            }
        
        text = text.strip()
        scores = {}
        
        # Calculate scores for each language
        for lang_code, lang_info in self.language_patterns.items():
            score = 0.0
            
            # Check pattern matches
            pattern_score = 0.0
            for pattern in lang_info['patterns']:
                matches = len(re.findall(pattern, text))
                if matches > 0:
                    pattern_score += matches / len(text)  # Normalize by text length
            
            # Check keyword matches
            keyword_score = 0.0
            text_lower = text.lower()
            for keyword in lang_info['keywords']:
                if keyword in text_lower:
                    keyword_score += 1.0
            
            # Combine scores (patterns weighted more heavily)
            score = (pattern_score * 0.7) + (keyword_score * 0.3)
            scores[lang_code] = score
        
        # Find best match
        if not scores:
            return {
                'language': 'en',
                'confidence': 0.0,
                'reasoning': 'No patterns matched, defaulting to English'
            }
        
        best_lang = max(scores, key=scores.get)
        best_score = scores[best_lang]
        
        # Calculate confidence (0.0 to 1.0)
        confidence = min(best_score, 1.0)
        
        # If confidence is too low, default to English
        if confidence < 0.1:
            best_lang = 'en'
            confidence = 0.0
            reasoning = 'Low confidence in detection, defaulting to English'
        else:
            reasoning = f"Detected {self.language_patterns[best_lang]['name']} with confidence {confidence:.2f}"
        
        logger.info(f"Language detection: '{text[:50]}...' -> {best_lang} (confidence: {confidence:.2f})")
        
        return {
            'language': best_lang,
            'confidence': confidence,
            'reasoning': reasoning,
            'all_scores': scores
        }
    
    def is_mixed_language(self, text: str) -> bool:
        """
        Check if text contains multiple languages
        
        Args:
            text: Input text to analyze
            
        Returns:
            True if text contains multiple languages
        """
        scores = {}
        
        for lang_code, lang_info in self.language_patterns.items():
            score = 0.0
            for pattern in lang_info['patterns']:
                matches = len(re.findall(pattern, text))
                if matches > 0:
                    score += matches / len(text)
            scores[lang_code] = score
        
        # Count languages with significant presence (>0.1)
        significant_langs = [lang for lang, score in scores.items() if score > 0.1]
        
        return len(significant_langs) > 1
    
    def extract_language_specific_parts(self, text: str) -> Dict[str, str]:
        """
        Extract language-specific parts from mixed language text
        
        Args:
            text: Mixed language text
            
        Returns:
            Dictionary mapping language codes to text parts
        """
        parts = {}
        
        for lang_code, lang_info in self.language_patterns.items():
            lang_text = ""
            for pattern in lang_info['patterns']:
                matches = re.findall(pattern, text)
                if matches:
                    lang_text += " ".join(matches) + " "
            
            if lang_text.strip():
                parts[lang_code] = lang_text.strip()
        
        return parts
