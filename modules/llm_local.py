#!/usr/bin/env python3
"""
Local LLM Manager - Ollama Integration
100% Local AI responses with robust fallbacks
"""

import requests
import json
import logging
import time
from typing import Iterator, Optional, Dict, Any, List
from dataclasses import dataclass

from config import config


@dataclass
class LLMResponse:
    """Structured LLM response with metadata"""
    content: str
    model: str
    tokens_used: int
    response_time: float
    is_fallback: bool = False
    error: Optional[str] = None


class OllamaManager:
    """Manager for local Ollama LLM interactions"""
    
    def __init__(self):
        self.logger = logging.getLogger("OllamaManager")
        self.host = config.ai.OLLAMA_HOST
        self.default_model = config.ai.DEFAULT_MODEL
        self.session = requests.Session()
        
        # Connection state
        self.is_available = False
        self.last_check = 0
        self.check_interval = 60  # Check every minute
        
        # Performance tracking
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'avg_response_time': 0,
            'total_tokens': 0
        }
        
        # Fallback responses for common scenarios
        self.fallback_responses = {
            'greeting': [
                "Hello! I'm Jarvis, your local AI assistant. How can I help you?",
                "Hi there! I'm running locally on your system. What can I do for you?",
                "Greetings! Your local AI assistant is ready to help."
            ],
            'general': [
                "I'm having trouble connecting to my AI processing unit right now. Let me try to help with what I know.",
                "My advanced AI capabilities are temporarily offline, but I can still assist you with basic tasks.",
                "I'm operating in limited mode right now, but I'll do my best to help you."
            ],
            'error': [
                "I encountered a technical issue processing that request. Could you try rephrasing it?",
                "Something went wrong with my processing. Please try again in a moment.",
                "I'm having difficulty with that request. Could you be more specific?"
            ]
        }
        
        self.logger.info("🤖 Ollama Manager initialized")
        self._check_availability()
    
    def _check_availability(self) -> bool:
        """Check if Ollama service is available"""
        try:
            response = self.session.get(
                f"{self.host}/api/tags", 
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                available_models = [model["name"] for model in data.get("models", [])]
                
                self.is_available = True
                self.last_check = time.time()
                
                if self.default_model not in available_models:
                    self.logger.warning(f"⚠️ Default model {self.default_model} not found")
                    if available_models:
                        self.default_model = available_models[0]
                        self.logger.info(f"✅ Using available model: {self.default_model}")
                
                self.logger.info(f"✅ Ollama available with {len(available_models)} models")
                return True
            else:
                self.is_available = False
                return False
                
        except Exception as e:
            self.is_available = False
            self.logger.warning(f"❌ Ollama unavailable: {e}")
            return False
    
    def should_check_availability(self) -> bool:
        """Determine if we should check availability"""
        return time.time() - self.last_check > self.check_interval
    
    def list_models(self) -> List[str]:
        """Get list of available models"""
        if not self.is_available and self.should_check_availability():
            self._check_availability()
        
        if not self.is_available:
            return []
        
        try:
            response = self.session.get(f"{self.host}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
        except Exception as e:
            self.logger.error(f"Error listing models: {e}")
        
        return []
    
    def _get_fallback_response(self, prompt: str, category: str = 'general') -> str:
        """Get intelligent fallback response"""
        import hashlib
        
        # Simple categorization
        if any(word in prompt.lower() for word in ['hello', 'hi', 'hey', 'greetings']):
            category = 'greeting'
        elif len(prompt.strip()) == 0:
            category = 'error'
        
        responses = self.fallback_responses.get(category, self.fallback_responses['general'])
        
        # Pseudo-random selection based on prompt
        hash_input = f"{prompt}{int(time.time() / 300)}"  # Changes every 5 minutes
        hash_val = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        selected = responses[hash_val % len(responses)]
        
        self.logger.info(f"📤 Fallback response ({category}): {selected}")
        return selected
    
    def generate_response(
        self, 
        prompt: str, 
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None
    ) -> LLMResponse:
        """Generate AI response with fallback support"""
        
        start_time = time.time()
        self.stats['total_requests'] += 1
        
        # Validation
        if not prompt or not prompt.strip():
            return LLMResponse(
                content=self._get_fallback_response("", "error"),
                model="fallback",
                tokens_used=0,
                response_time=time.time() - start_time,
                is_fallback=True,
                error="Empty prompt"
            )
        
        # Check Ollama availability
        if not self.is_available and self.should_check_availability():
            self._check_availability()
        
        # Try Ollama if available
        if self.is_available:
            try:
                return self._ollama_request(
                    prompt, model, max_tokens, temperature, system_prompt, start_time
                )
            except Exception as e:
                self.logger.error(f"❌ Ollama request failed: {e}")
                self.is_available = False
                self.stats['failed_requests'] += 1
        
        # Fallback response
        fallback_content = self._get_fallback_response(prompt)
        response_time = time.time() - start_time
        
        return LLMResponse(
            content=fallback_content,
            model="fallback",
            tokens_used=0,
            response_time=response_time,
            is_fallback=True,
            error="Ollama unavailable"
        )
    
    def _ollama_request(
        self, 
        prompt: str, 
        model: Optional[str], 
        max_tokens: Optional[int],
        temperature: Optional[float], 
        system_prompt: Optional[str],
        start_time: float
    ) -> LLMResponse:
        """Make actual Ollama API request"""
        
        # Prepare request
        model = model or self.default_model
        max_tokens = max_tokens or config.ai.MAX_TOKENS
        temperature = temperature or config.ai.TEMPERATURE
        system_prompt = system_prompt or config.ai.SYSTEM_PROMPT
        
        # Build messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        payload = {
            "model": model,
            "messages": messages,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
                "stop": ["<|im_end|>", "</s>"]
            },
            "stream": False
        }
        
        # Make request
        response = self.session.post(
            f"{self.host}/api/chat",
            json=payload,
            timeout=config.ai.TIMEOUT
        )
        
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}: {response.text}")
        
        # Parse response
        data = response.json()
        content = data.get("message", {}).get("content", "").strip()
        
        if not content:
            raise Exception("Empty response from Ollama")
        
        # Calculate metrics
        response_time = time.time() - start_time
        tokens_used = len(content.split())  # Rough estimate
        
        # Update stats
        self.stats['successful_requests'] += 1
        self.stats['total_tokens'] += tokens_used
        
        # Update average response time
        total_success = self.stats['successful_requests']
        current_avg = self.stats['avg_response_time']
        self.stats['avg_response_time'] = (
            (current_avg * (total_success - 1) + response_time) / total_success
        )
        
        self.logger.info(f"🤖 Ollama response: {len(content)} chars in {response_time:.2f}s")
        
        return LLMResponse(
            content=content,
            model=model,
            tokens_used=tokens_used,
            response_time=response_time,
            is_fallback=False
        )
    
    def stream_response(
        self, 
        prompt: str, 
        model: Optional[str] = None
    ) -> Iterator[str]:
        """Stream response from Ollama (for real-time display)"""
        
        if not self.is_available:
            if self.should_check_availability():
                self._check_availability()
            
            if not self.is_available:
                # Stream fallback response word by word
                fallback = self._get_fallback_response(prompt)
                for word in fallback.split():
                    yield word + " "
                    time.sleep(0.1)  # Simulate streaming
                return
        
        try:
            model = model or self.default_model
            
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": config.ai.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                "stream": True
            }
            
            response = self.session.post(
                f"{self.host}/api/chat",
                json=payload,
                stream=True,
                timeout=config.ai.TIMEOUT
            )
            
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}")
            
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            chunk = data["message"]["content"]
                            if chunk:
                                yield chunk
                        
                        if data.get("done", False):
                            break
                            
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            self.logger.error(f"❌ Streaming error: {e}")
            # Fallback to word-by-word streaming
            fallback = self._get_fallback_response(prompt)
            for word in fallback.split():
                yield word + " "
                time.sleep(0.1)
    
    def chat_with_context(
        self, 
        messages: List[Dict[str, str]], 
        model: Optional[str] = None
    ) -> LLMResponse:
        """Chat with conversation context"""
        
        start_time = time.time()
        self.stats['total_requests'] += 1
        
        if not self.is_available and self.should_check_availability():
            self._check_availability()
        
        if not self.is_available:
            # Create context-aware fallback
            last_user_message = ""
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    last_user_message = msg.get("content", "")
                    break
            
            fallback_content = self._get_fallback_response(last_user_message)
            return LLMResponse(
                content=fallback_content,
                model="fallback",
                tokens_used=0,
                response_time=time.time() - start_time,
                is_fallback=True,
                error="Ollama unavailable"
            )
        
        try:
            model = model or self.default_model
            
            # Ensure system message is first
            formatted_messages = []
            system_added = False
            
            for msg in messages:
                if msg.get("role") == "system" and not system_added:
                    formatted_messages.append(msg)
                    system_added = True
                elif msg.get("role") in ["user", "assistant"]:
                    formatted_messages.append(msg)
            
            # Add default system message if none provided
            if not system_added:
                formatted_messages.insert(0, {
                    "role": "system", 
                    "content": config.ai.SYSTEM_PROMPT
                })
            
            payload = {
                "model": model,
                "messages": formatted_messages,
                "options": {
                    "num_predict": config.ai.MAX_TOKENS,
                    "temperature": config.ai.TEMPERATURE
                },
                "stream": False
            }
            
            response = self.session.post(
                f"{self.host}/api/chat",
                json=payload,
                timeout=config.ai.TIMEOUT
            )
            
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
            
            data = response.json()
            content = data.get("message", {}).get("content", "").strip()
            
            if not content:
                raise Exception("Empty response from Ollama")
            
            response_time = time.time() - start_time
            tokens_used = len(content.split())
            
            self.stats['successful_requests'] += 1
            self.stats['total_tokens'] += tokens_used
            
            return LLMResponse(
                content=content,
                model=model,
                tokens_used=tokens_used,
                response_time=response_time,
                is_fallback=False
            )
            
        except Exception as e:
            self.logger.error(f"❌ Context chat error: {e}")
            self.stats['failed_requests'] += 1
            
            # Extract last user message for fallback
            last_user_message = ""
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    last_user_message = msg.get("content", "")
                    break
            
            fallback_content = self._get_fallback_response(last_user_message)
            return LLMResponse(
                content=fallback_content,
                model="fallback",
                tokens_used=0,
                response_time=time.time() - start_time,
                is_fallback=True,
                error=str(e)
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        success_rate = 0
        if self.stats['total_requests'] > 0:
            success_rate = (self.stats['successful_requests'] / self.stats['total_requests']) * 100
        
        return {
            **self.stats,
            'success_rate': f"{success_rate:.1f}%",
            'is_available': self.is_available,
            'default_model': self.default_model,
            'last_check': self.last_check
        }
    
    def reset_connection(self) -> bool:
        """Reset and test Ollama connection"""
        self.logger.info("🔄 Resetting Ollama connection...")
        
        self.is_available = False
        self.last_check = 0
        
        return self._check_availability()
    
    def cleanup(self):
        """Cleanup resources"""
        if self.session:
            self.session.close()
        
        self.logger.info("🧹 Ollama Manager cleanup completed")


# Global instance
ollama_manager = OllamaManager() 