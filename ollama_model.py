#!/usr/bin/env python3
"""
Ollama Model Module
Handles communication with Ollama API and provides SmolaGents compatibility

Usage:
    from ollama_model import OllamaModel
    model = OllamaModel("qwen2.5-coder:7b")
    response = model("What is 2+2?")
"""

import requests
import logging
from typing import Dict, List, Any, Union

# --- Configuration ---
OLLAMA_BASE = "http://localhost:11434"

# --- Logging Setup ---
logger = logging.getLogger(__name__)

def log_debug(message):
    """Debug logging"""
    debug_msg = f"🔍 DEBUG: {message}"
    print(debug_msg)
    logger.debug(debug_msg)

def log_error(message, exception=None):
    """Enhanced error logging with stack trace"""
    import traceback
    
    error_msg = f"❌ ERROR: {message}"
    print(error_msg)
    
    if exception:
        print(f"Exception type: {type(exception).__name__}")
        print(f"Exception message: {str(exception)}")
        print("Stack trace:")
        traceback.print_exc()
        
        # Also log the full traceback to logger
        logger.error(f"Exception: {exception}", exc_info=True)

# --- Token Usage Object for SmolaGents Compatibility ---
class TokenUsage:
    """Token usage object with attributes (SmolaGents expects attributes, not dict keys)"""
    def __init__(self, prompt_tokens, completion_tokens):
        # OpenAI style
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = prompt_tokens + completion_tokens
        
        # Anthropic style (what SmolaGents expects)
        self.input_tokens = prompt_tokens
        self.output_tokens = completion_tokens
        
        # Generic alternatives
        self.input = prompt_tokens
        self.output = completion_tokens
        self.total = self.total_tokens
    
    def __getitem__(self, key):
        """Allow dict-style access for backward compatibility"""
        return getattr(self, key, 0)
    
    def get(self, key, default=None):
        """Allow dict.get() style access"""
        return getattr(self, key, default)
    
    def keys(self):
        """Allow dict.keys() style access"""
        return ['prompt_tokens', 'completion_tokens', 'total_tokens', 
               'input_tokens', 'output_tokens', 'input', 'output', 'total']

# --- Response Wrapper for SmolaGents Compatibility ---
class StringWithContent(str):
    """String subclass that mimics LLM response for SmolaGents compatibility"""
    def __new__(cls, content):
        obj = str.__new__(cls, content)
        obj.content = content
        
        # Create token usage as an object with attributes (not a dictionary)
        word_count = len(content.split()) if content else 0
        prompt_tokens = max(10, word_count // 2)  # Rough estimate
        completion_tokens = word_count
        
        obj.token_usage = TokenUsage(prompt_tokens, completion_tokens)
        obj.usage = obj.token_usage  # Alternative name for token usage
        
        # Add other potential attributes SmolaGents might expect
        obj.model = "ollama-local"
        obj.choices = [{'message': {'content': content, 'role': 'assistant'}}]
        obj.response_metadata = {'model': 'ollama-local', 'usage': obj.token_usage}
        
        # Additional LLM response attributes
        obj.id = f"ollama-{hash(content) % 1000000}"
        obj.object = "chat.completion"
        obj.created = 1234567890
        obj.finish_reason = "stop"
        obj.system_fingerprint = "ollama-local"
        
        return obj

# --- Main Ollama Model Class ---
class OllamaModel:
    """
    Ollama model wrapper with SmolaGents compatibility.
    
    Supports both chat and generate endpoints with automatic format conversion.
    """
    
    def __init__(self, model_name: str, base_url: str = OLLAMA_BASE):
        self.model_name = model_name
        self.base_url = base_url
        self.test_connection()
    
    def test_connection(self):
        """Test Ollama connection and model availability"""
        try:
            # Check if Ollama is running
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            
            # Check if model exists
            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]
            
            if self.model_name not in model_names:
                print(f"❌ Model {self.model_name} not found in Ollama")
                print(f"📋 Available models: {model_names}")
                print(f"💡 Try: ollama pull {self.model_name}")
                raise Exception(f"Model {self.model_name} not available")
            
            print(f"✅ Ollama model {self.model_name} ready")
            
        except requests.exceptions.ConnectionError:
            log_error(f"Cannot connect to Ollama at {self.base_url}")
            print("💡 Make sure Ollama is running: ollama serve")
            raise
        except Exception as e:
            log_error(f"Ollama setup error", e)
            raise
    
    def _make_request(self, endpoint: str, payload: dict) -> str:
        """Make request to Ollama API and return response text with SmolaGents compatibility"""
        try:
            log_debug(f"Making request to {self.base_url}{endpoint}")
            log_debug(f"Payload keys: {list(payload.keys())}")
            
            response = requests.post(
                f"{self.base_url}{endpoint}",
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            
            result = response.json()
            log_debug(f"Response keys: {list(result.keys())}")
            
            # Handle different endpoint response formats
            if endpoint == "/api/generate":
                response_text = result.get("response", "")
            elif endpoint == "/api/chat":
                response_text = result.get("message", {}).get("content", "")
            else:
                # Fallback for any other endpoint
                response_text = result.get("message", {}).get("content", "") or result.get("response", "")
            
            log_debug(f"Response text length: {len(response_text)}")
            
            # Return StringWithContent for SmolaGents compatibility
            return StringWithContent(response_text)
                
        except Exception as e:
            log_error(f"Ollama request error", e)
            # Add more debugging info
            if hasattr(e, 'response') and e.response is not None:
                print(f"❌ Response status: {e.response.status_code}")
                print(f"❌ Response text: {e.response.text[:200]}...")
            raise Exception(f"Ollama request failed: {e}")
    
    def __call__(self, prompt) -> str:
        """Generate response using Ollama - main method"""
        try:
            log_debug(f"Ollama model called with prompt type: {type(prompt)}")
            log_debug(f"Prompt preview: {str(prompt)[:200]}...")
            
            # Handle different prompt formats
            if isinstance(prompt, str):
                # Simple string prompt - use generate API
                payload = {
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "top_p": 0.9,
                        "num_predict": 2000
                    }
                }
                return self._make_request("/api/generate", payload)
                
            elif isinstance(prompt, list):
                # Message list format - use chat API
                payload = {
                    "model": self.model_name,
                    "messages": self._convert_messages(prompt),
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "top_p": 0.9,
                        "num_predict": 2000
                    }
                }
                return self._make_request("/api/chat", payload)
            else:
                # Convert other types to string
                return self.__call__(str(prompt))
                
        except Exception as e:
            log_error(f"Ollama generation error", e)
            raise
    
    def _convert_messages(self, messages) -> List[Dict]:
        """Convert message format to Ollama chat format"""
        log_debug(f"Converting {len(messages)} messages to Ollama format")
        
        converted = []
        for msg in messages:
            if isinstance(msg, dict):
                # Extract role and content
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                # Handle content that might be a list (with text/image parts)
                if isinstance(content, list):
                    # For now, just extract text content
                    text_content = ""
                    for part in content:
                        if isinstance(part, dict) and part.get("type") == "text":
                            text_content += part.get("text", "")
                    content = text_content
                
                converted.append({
                    "role": role,
                    "content": str(content)
                })
            else:
                converted.append({
                    "role": "user",
                    "content": str(msg)
                })
        
        log_debug(f"Converted to {len(converted)} messages")
        return converted

    # --- SmolaGents Compatibility Methods ---
    
    def generate(self, prompt, **kwargs):
        """Generate method for SmolaGents compatibility"""
        log_debug("generate() method called")
        return self.__call__(prompt)
    
    def chat_completion(self, messages, **kwargs):
        """Chat completion method for SmolaGents compatibility"""
        log_debug("chat_completion() method called")
        return self.__call__(messages)
    
    def complete(self, prompt, **kwargs):
        """Complete method for compatibility"""
        log_debug("complete() method called")
        return self.__call__(prompt)
    
    def invoke(self, prompt, **kwargs):
        """Invoke method for compatibility"""
        log_debug("invoke() method called")
        return self.__call__(prompt)
    
    # --- Model Information Methods ---
    
    def get_model_info(self) -> Dict:
        """Get information about the current model"""
        try:
            response = requests.post(f"{self.base_url}/api/show", 
                                   json={"name": self.model_name}, 
                                   timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            log_error(f"Failed to get model info", e)
            return {"error": str(e)}
    
    def list_available_models(self) -> List[str]:
        """List all available models in Ollama"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            models = response.json().get("models", [])
            return [m["name"] for m in models]
        except Exception as e:
            log_error(f"Failed to list models", e)
            return []
    
    # --- Advanced Generation Methods ---
    
    def generate_with_options(self, prompt: str, temperature: float = 0.1, 
                            top_p: float = 0.9, max_tokens: int = 2000) -> str:
        """Generate with custom options"""
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "top_p": top_p,
                    "num_predict": max_tokens
                }
            }
            return self._make_request("/api/generate", payload)
        except Exception as e:
            log_error(f"Generation with options failed", e)
            raise
    
    def chat_with_options(self, messages: List[Dict], temperature: float = 0.1,
                         top_p: float = 0.9, max_tokens: int = 2000) -> str:
        """Chat with custom options"""
        try:
            payload = {
                "model": self.model_name,
                "messages": self._convert_messages(messages),
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "top_p": top_p,
                    "num_predict": max_tokens
                }
            }
            return self._make_request("/api/chat", payload)
        except Exception as e:
            log_error(f"Chat with options failed", e)
            raise

# --- Utility Functions ---

def get_available_models(base_url: str = OLLAMA_BASE) -> List[str]:
    """Get list of available Ollama models"""
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        response.raise_for_status()
        models = response.json().get("models", [])
        return [m["name"] for m in models]
    except Exception as e:
        log_error(f"Failed to get available models", e)
        return []

def find_best_model(preferred_models: List[str], base_url: str = OLLAMA_BASE) -> str:
    """Find the best available model from a preference list"""
    available = get_available_models(base_url)
    
    if not available:
        raise Exception("No models available in Ollama")
    
    # Find the best model from preference list
    for preferred in preferred_models:
        if preferred in available:
            print(f"✅ Found preferred model: {preferred}")
            return preferred
    
    # If no preferred models found, use the first available
    model_name = available[0]
    print(f"⚠️ No preferred models found, using: {model_name}")
    return model_name

def test_ollama_connection(base_url: str = OLLAMA_BASE) -> bool:
    """Test if Ollama is running and accessible"""
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        response.raise_for_status()
        print(f"✅ Ollama is running at {base_url}")
        return True
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to Ollama at {base_url}")
        print("💡 Make sure Ollama is running: ollama serve")
        return False
    except Exception as e:
        print(f"❌ Ollama connection test failed: {e}")
        return False

if __name__ == "__main__":
    print("Ollama Model Module")
    
    # Test connection
    if test_ollama_connection():
        # List available models
        models = get_available_models()
        print(f"📋 Available models: {models}")
        
        # Test with first available model if any
        if models:
            test_model = OllamaModel(models[0])
            test_response = test_model("Hello! Can you count to 3?")
            print(f"🧪 Test response: {test_response}")
        else:
            print("⚠️ No models available for testing")
    else:
        print("⚠️ Cannot test - Ollama not accessible")