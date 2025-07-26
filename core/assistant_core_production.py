"""
Gideon AI Assistant Core - PRODUCTION VERSION
100% LOCAL avec Ollama - AUCUNE dépendance OpenAI
"""

import time
import logging
import threading
from typing import Optional, Dict, List
from collections import deque
from dataclasses import dataclass
import json

# Ollama local - AUCUNE dépendance externe
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from config import config


@dataclass
class ConversationContext:
    """Context de conversation pour mémoire intelligente"""
    user_input: str
    ai_response: str
    timestamp: float
    response_time: float
    success: bool = True
    fallback_used: bool = False


class OllamaLocalClient:
    """Client Ollama 100% local - Aucune dépendance externe"""
    
    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.available_models = ["mistral:7b", "llama3:8b", "phi3:mini"]
        self.default_model = "mistral:7b"
        self.is_available = False
        self.logger = logging.getLogger("OllamaClient")
        
        # Test de connectivité Ollama
        self._test_connection()
    
    def _test_connection(self) -> bool:
        """Test si Ollama est disponible"""
        if not HAS_REQUESTS:
            return False
            
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if response.status_code == 200:
                self.is_available = True
                self.logger.info("✅ Ollama connecté et fonctionnel")
                return True
        except Exception as e:
            self.logger.warning(f"⚠️ Ollama non disponible: {e}")
        
        self.is_available = False
        return False
    
    def chat_completion(self, messages: List[Dict], model: str = None) -> Dict:
        """Génère une réponse via Ollama"""
        if not self.is_available or not HAS_REQUESTS:
            return {"error": "Ollama non disponible"}
        
        model = model or self.default_model
        
        # Construire le prompt à partir des messages
        prompt = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                prompt += f"System: {content}\n"
            elif role == "user":
                prompt += f"User: {content}\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n"
        
        prompt += "Assistant: "
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "max_tokens": 150
                    }
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "choices": [{
                        "message": {
                            "content": data.get("response", "")
                        }
                    }]
                }
            else:
                return {"error": f"Ollama HTTP {response.status_code}"}
                
        except Exception as e:
            self.logger.error(f"❌ Erreur Ollama: {e}")
            return {"error": str(e)}


class IntelligentFallbacks:
    """Système de fallbacks intelligents sans aucune dépendance externe"""
    
    def __init__(self):
        self.responses = {
            # Réponses contextuelles
            'greeting': [
                "Hello! I'm Gideon, your local AI assistant. How can I help you today?",
                "Hi there! I'm running entirely on your system. What can I do for you?",
                "Greetings! Your local AI assistant is ready to assist you."
            ],
            'farewell': [
                "Goodbye! Feel free to ask me anything anytime.",
                "See you later! I'll be here when you need me.",
                "Take care! I'm always ready to help."
            ],
            'time': [
                f"The current time is {time.strftime('%H:%M:%S')}",
                f"It's currently {time.strftime('%I:%M %p')}",
                f"Right now it's {time.strftime('%H:%M')}"
            ],
            'weather': [
                "I don't have current weather data, but I can help you find weather services.",
                "For weather information, I'd recommend checking your local weather app.",
                "I can't access weather data right now, but I can help with other tasks."
            ],
            'general': [
                "I'm here to help! Could you be more specific about what you need?",
                "I'm your local AI assistant. How can I assist you today?",
                "I'm ready to help with various tasks. What would you like to do?"
            ],
            'error': [
                "I'm experiencing some technical difficulties. Let me try a different approach.",
                "Something went wrong there. Could you please rephrase your request?",
                "I encountered an issue processing that. Can you try asking differently?"
            ]
        }
    
    def get_contextual_response(self, user_input: str) -> str:
        """Génère une réponse contextuelle intelligente"""
        input_lower = user_input.lower()
        
        # Détection contextuelle simple
        if any(word in input_lower for word in ['hello', 'hi', 'hey', 'greetings']):
            category = 'greeting'
        elif any(word in input_lower for word in ['bye', 'goodbye', 'farewell', 'see you']):
            category = 'farewell'
        elif any(word in input_lower for word in ['time', 'hour', 'clock']):
            category = 'time'
        elif any(word in input_lower for word in ['weather', 'temperature', 'rain', 'sunny']):
            category = 'weather'
        else:
            category = 'general'
        
        # Sélection pseudo-aléatoire basée sur l'input
        import hashlib
        hash_input = f"{user_input}{int(time.time() / 300)}"  # Change toutes les 5 minutes
        hash_val = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        responses = self.responses[category]
        selected = responses[hash_val % len(responses)]
        
        return selected


class AssistantCore:
    """Core Assistant 100% LOCAL - Aucune dépendance externe pour fonctionner"""
    
    def __init__(self):
        self.logger = logging.getLogger("GideonCore")
        
        # Client Ollama local - PRIORITÉ
        self.ollama_client = OllamaLocalClient()
        
        # Fallbacks intelligents - TOUJOURS DISPONIBLES
        self.fallbacks = IntelligentFallbacks()
        
        # Mémoire de conversation
        self.context_memory = deque(maxlen=10)
        self.response_cache = {}
        
        # Statistiques
        self.stats = {
            'total_requests': 0,
            'ollama_responses': 0,
            'fallback_responses': 0,
            'cached_responses': 0,
            'avg_response_time': 0,
            'errors': 0
        }
        
        self.logger.info("✅ Gideon Assistant Core initialisé (100% LOCAL avec Ollama)")
    
    def _test_api_connection(self) -> bool:
        """Test de connectivité - Ollama uniquement"""
        return self.ollama_client._test_connection()
    
    def generate_ai_response(self, user_input: str, context: Dict = None) -> Dict:
        """Génère réponse IA - Ollama prioritaire avec fallbacks intelligents"""
        start_time = time.time()
        self.stats['total_requests'] += 1
        
        # Cache check
        cache_key = f"{user_input.lower()}_{len(self.context_memory)}"
        if cache_key in self.response_cache:
            self.stats['cached_responses'] += 1
            cached_response = self.response_cache[cache_key]
            return {
                'success': True,
                'response': cached_response,
                'method': 'cache',
                'response_time': time.time() - start_time,
                'cached': True
            }
        
        ai_response = None
        method_used = "unknown"
        fallback_used = False
        
        # 1. Essayer Ollama en priorité
        if self.ollama_client.is_available:
            try:
                messages = self._build_context_messages(user_input)
                
                ollama_response = self.ollama_client.chat_completion(messages)
                
                if "choices" in ollama_response and ollama_response["choices"]:
                    ai_response = ollama_response["choices"][0]["message"]["content"].strip()
                    method_used = "ollama"
                    self.stats['ollama_responses'] += 1
                    
                    # Cache si réponse substantielle
                    if len(ai_response) > 10:
                        self.response_cache[cache_key] = ai_response
                        
                        # Limiter taille cache
                        if len(self.response_cache) > 50:
                            oldest_key = next(iter(self.response_cache))
                            del self.response_cache[oldest_key]
                
            except Exception as e:
                self.logger.error(f"❌ Erreur Ollama: {e}")
                self.stats['errors'] += 1
        
        # 2. Fallback intelligent si Ollama échoue
        if not ai_response:
            ai_response = self.fallbacks.get_contextual_response(user_input)
            method_used = "fallback"
            fallback_used = True
            self.stats['fallback_responses'] += 1
        
        # Calcul temps de réponse
        response_time = time.time() - start_time
        
        # Mise à jour statistiques moyennes
        total = self.stats['total_requests']
        current_avg = self.stats['avg_response_time']
        self.stats['avg_response_time'] = (current_avg * (total - 1) + response_time) / total
        
        # Ajout au contexte
        context_entry = ConversationContext(
            user_input=user_input,
            ai_response=ai_response,
            timestamp=time.time(),
            response_time=response_time,
            success=True,
            fallback_used=fallback_used
        )
        self.context_memory.append(context_entry)
        
        self.logger.info(f"🤖 Réponse générée via {method_used} en {response_time:.2f}s")
        
        return {
            'success': True,
            'response': ai_response,
            'method': method_used,
            'response_time': response_time,
            'fallback_used': fallback_used,
            'cached': False
        }
    
    def _build_context_messages(self, user_input: str) -> List[Dict]:
        """Construit messages avec contexte pour Ollama"""
        messages = [
            {
                "role": "system",
                "content": "You are Gideon, a helpful AI assistant running locally. Be concise, friendly, and helpful. Respond in the same language as the user."
            }
        ]
        
        # Ajout contexte récent (3 derniers échanges)
        recent_context = list(self.context_memory)[-3:]
        for ctx in recent_context:
            messages.append({"role": "user", "content": ctx.user_input})
            messages.append({"role": "assistant", "content": ctx.ai_response})
        
        # Message actuel
        messages.append({"role": "user", "content": user_input})
        
        return messages
    
    def process_voice_command(self, command: str) -> Dict:
        """Traite commande vocale"""
        self.logger.info(f"🎤 Commande vocale reçue: {command}")
        
        # Génération réponse
        result = self.generate_ai_response(command)
        
        if result['success']:
            return {
                'success': True,
                'response': result['response'],
                'method': result['method'],
                'response_time': result['response_time'],
                'fallback_used': result.get('fallback_used', False)
            }
        else:
            error_response = "I couldn't process that command right now. Please try again."
            return {
                'success': False,
                'response': error_response,
                'error': result.get('error', 'Unknown error'),
                'fallback_used': True
            }
    
    def get_system_status(self) -> Dict:
        """Status système"""
        return {
            'ollama_available': self.ollama_client.is_available,
            'total_requests': self.stats['total_requests'],
            'ollama_success_rate': (self.stats['ollama_responses'] / max(1, self.stats['total_requests'])) * 100,
            'fallback_usage': (self.stats['fallback_responses'] / max(1, self.stats['total_requests'])) * 100,
            'avg_response_time': self.stats['avg_response_time'],
            'conversation_length': len(self.context_memory),
            'cache_size': len(self.response_cache)
        }
    
    def reset_conversation(self):
        """Reset conversation context"""
        self.context_memory.clear()
        self.response_cache.clear()
        self.logger.info("🔄 Conversation context reset")
    
    def cleanup_memory_resources(self):
        """Nettoyage mémoire"""
        self.context_memory.clear()
        self.response_cache.clear()
        
    def cleanup(self):
        """Nettoyage complet"""
        self.cleanup_memory_resources()
        self.logger.info("🧹 Cleanup assistant core terminé")


# Instance globale
assistant_core = AssistantCore() 