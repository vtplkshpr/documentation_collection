"""
Simple translation service fallback
"""
import logging
from typing import Dict, List, Optional
from utils.config import config

logger = logging.getLogger(__name__)

class SimpleTranslationService:
    """Simple translation service fallback"""
    
    def __init__(self):
        self.cache = {}
        # Simple translation mappings for testing
        self.translations = {
            'en': {
                'artificial intelligence': 'artificial intelligence',
                'machine learning': 'machine learning',
                'deep learning': 'deep learning',
                'neural network': 'neural network'
            },
            'vi': {
                'artificial intelligence': 'trí tuệ nhân tạo',
                'machine learning': 'học máy',
                'deep learning': 'học sâu',
                'neural network': 'mạng nơ-ron'
            },
            'ja': {
                'artificial intelligence': '人工知能',
                'machine learning': '機械学習',
                'deep learning': '深層学習',
                'neural network': 'ニューラルネットワーク'
            },
            'ko': {
                'artificial intelligence': '인공지능',
                'machine learning': '기계학습',
                'deep learning': '딥러닝',
                'neural network': '신경망'
            },
            'ru': {
                'artificial intelligence': 'искусственный интеллект',
                'machine learning': 'машинное обучение',
                'deep learning': 'глубокое обучение',
                'neural network': 'нейронная сеть'
            },
            'fa': {
                'artificial intelligence': 'هوش مصنوعی',
                'machine learning': 'یادگیری ماشین',
                'deep learning': 'یادگیری عمیق',
                'neural network': 'شبکه عصبی'
            }
        }
    
    async def translate_to_all_languages(self, text: str, source_language: str = 'auto') -> Dict[str, str]:
        """
        Translate text to all supported languages
        
        Args:
            text: Text to translate
            source_language: Source language code
        
        Returns:
            Dictionary mapping language codes to translated text
        """
        translations = {}
        
        for lang in config.SUPPORTED_LANGUAGES:
            if lang == source_language:
                translations[lang] = text
                continue
            
            translated = self._simple_translate(text, lang)
            if translated:
                translations[lang] = translated
            else:
                logger.warning(f"Failed to translate to {lang}")
                translations[lang] = text  # Fallback to original
        
        return translations
    
    async def translate_text(self, text: str, target_language: str) -> str:
        """Async wrapper for translation (for compatibility)"""
        return self._simple_translate(text, target_language)
    
    def _simple_translate(self, text: str, target_language: str) -> str:
        """Simple translation using predefined mappings"""
        text_lower = text.lower().strip()
        
        if target_language in self.translations:
            for key, value in self.translations[target_language].items():
                if key in text_lower:
                    return text.replace(key, value)
        
        # If no translation found, return original text
        return text
