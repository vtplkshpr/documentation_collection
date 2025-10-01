# Translation Integration Between Modules

## Tổng quan

Module `documentation_collection` sử dụng AI translation để dịch query trước khi tìm kiếm trong các ngôn ngữ khác nhau.

## Kiến trúc truyền input

```
documentation_collection/
├── services/
│   └── search_service.py          # Main orchestration
├── core/
│   ├── ai_translation_wrapper.py  # AI translation interface
│   └── language_detector.py       # Language detection
└── main.py                        # CLI entry point
```

## Luồng xử lý

### 1. Input từ User
```python
# main.py
query = "量子传感 军事 应用 filetype:pdf"
```

### 2. Language Detection
```python
# search_service.py -> language_detector.py
detection_result = self.language_detector.detect_language(query)
source_language = detection_result['language']  # "zh"
```

### 3. Translation Process
```python
# search_service.py -> ai_translation_wrapper.py
translated_query = await self.translator.translate_text(
    query,           # "量子传感 军事 应用 filetype:pdf"
    target_language, # "en"
    source_language  # "zh"
)
```

### 4. AI Translation Wrapper
```python
# ai_translation_wrapper.py
async def translate_text(self, text: str, target_language: str, source_language: str = 'auto'):
    # 1. Tạo prompt cho AI model
    prompt = self._create_translation_prompt(text, source_language, target_language)
    
    # 2. Gọi Ollama API
    payload = {
        "model": self.model_name,  # "tinyllama:latest"
        "prompt": prompt,
        "stream": False
    }
    
    # 3. Gửi request đến Ollama
    async with session.post(f"{self.base_url}/api/generate", json=payload) as response:
        result = await response.json()
        translated_text = result.get('response', '').strip()
        
    # 4. Clean up response
    return self._clean_translation_response(translated_text)
```

### 5. Prompt Structure
```python
def _create_translation_prompt(self, text: str, source_lang: str, target_lang: str) -> str:
    return f"""Translate this text from {source_name} to {target_name}. Return only the translation, nothing else.

{text}"""
```

### 6. Output Format
```
Input:  "量子传感 军事 应用 filetype:pdf"
Output: "quantum sensing military applications filetype:pdf"
```

## Cấu trúc dữ liệu truyền

### Input Parameters
```python
{
    "query": str,              # Original query text
    "target_language": str,    # Target language code (e.g., "en", "vi", "ja")
    "source_language": str     # Source language code (e.g., "zh", "en")
}
```

### Translation Request (Ollama API)
```python
{
    "model": "tinyllama:latest",
    "prompt": "Translate this text from Chinese to English. Return only the translation, nothing else.\n\n量子传感 军事 应用 filetype:pdf",
    "stream": false
}
```

### Translation Response (Ollama API)
```python
{
    "response": "quantum sensing military applications filetype:pdf",
    "done": true,
    "context": [...],
    "total_duration": 1234567890,
    "load_duration": 123456,
    "prompt_eval_count": 10,
    "prompt_eval_duration": 123456,
    "eval_count": 5,
    "eval_duration": 123456
}
```

## Error Handling

### 1. Translation Service Unavailable
```python
if not self._initialized:
    logger.error("AI translation not initialized")
    return None
```

### 2. API Errors
```python
if response.status != 200:
    logger.error(f"Translation API error: {response.status}")
    return None
```

### 3. Empty Response
```python
if not translated_text or translated_text == text:
    logger.warning("Translation returned empty or same text")
    return None
```

## Integration Points

### 1. Search Service Integration
```python
# search_service.py
async def _translate_query_for_language(self, query: str, target_language: str, source_language: str = None):
    # Initialize translation service
    if not self._translation_initialized:
        await self.translator.initialize()
        self._translation_initialized = True
    
    # Translate query
    translated_query = await self.translator.translate_text(query, target_language, source_language)
    
    return translated_query
```

### 2. Multi-language Search
```python
# search_service.py
for lang in languages:
    for engine in search_engines:
        translated_query = await self._translate_query_for_language(query, lang, original_query_lang)
        # Use translated_query for search
```

## Configuration

### Ollama Configuration
```python
# ai_translation_wrapper.py
OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "tinyllama:latest"  # or "llama2:latest"
```

### Supported Languages
```python
LANGUAGE_NAMES = {
    'en': 'English',
    'vi': 'Vietnamese',
    'ja': 'Japanese',
    'ko': 'Korean',
    'ru': 'Russian',
    'fa': 'Persian',
    'zh': 'Chinese',
    # ... more languages
}
```

## Performance Considerations

1. **Model Selection**: `tinyllama` nhanh hơn nhưng chất lượng thấp hơn `llama2`
2. **Caching**: Có thể implement caching để tránh dịch lại cùng một query
3. **Timeout**: Có timeout cho API calls để tránh hang
4. **Batch Processing**: Có thể batch multiple translations

## Dependencies

- `aiohttp`: HTTP client cho Ollama API
- `asyncio`: Async/await support
- `logging`: Logging và debugging

## Testing

```bash
# Test với query tiếng Trung
python3 main.py --module documentation_collection --query "量子传感 军事 应用 filetype:pdf" --max-results 2

# Test với query tiếng Anh
python3 main.py --module documentation_collection --query "quantum sensing military applications filetype:pdf" --max-results 2
```
