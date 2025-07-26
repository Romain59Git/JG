"""
Gideon AI Assistant Core - PRODUCTION VERSION
Optimized AI responses with robust fallbacks and context memory
"""

import time
import logging
import threading
from typing import Optional, Dict, List
from collections import deque
from dataclasses import dataclass
import json

# Safe imports with fallbacks
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

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

class IntelligentFallbacks:
    """Système de fallbacks intelligents pour Gideon"""
    
    def __init__(self):
        self.logger = logging.getLogger("GideonFallbacks")
        
        # Réponses préprogrammées par catégorie
        self.fallback_responses = {
            'greeting': [
                "Hello! I'm Gideon, your AI assistant. How can I help you today?",
                "Greetings! I'm ready to assist you with any questions or tasks.",
                "Hi there! What can I do for you today?"
            ],
            'weather': [
                "I'd need to check the weather service for that information. Please try asking about the weather again in a moment.",
                "Weather services seem to be unavailable right now. Would you like me to help with something else?"
            ],
            'time': [
                f"It's currently {time.strftime('%I:%M %p')} on {time.strftime('%A, %B %d, %Y')}.",
                f"The current time is {time.strftime('%H:%M')} today."
            ],
            'capabilities': [
                "I'm Gideon, an AI assistant inspired by the Flash series. I can help with questions, conversations, and various tasks. What would you like to know?",
                "I can assist with information, answer questions, and have conversations. I'm designed to be helpful, accurate, and efficient."
            ],
            'error': [
                "I'm experiencing some technical difficulties right now. Please try rephrasing your question.",
                "Sorry, I'm having trouble processing that request at the moment. Could you try asking differently?",
                "There seems to be a temporary issue with my AI services. Is there something else I can help with?"
            ],
            'unclear': [
                "I'm not sure I understand completely. Could you provide more details or rephrase your question?",
                "That's an interesting question, but I need a bit more context to give you a helpful answer.",
                "Could you clarify what you're looking for? I want to make sure I give you the right information."
            ],
            'goodbye': [
                "Goodbye! Feel free to call on me anytime you need assistance.",
                "Until next time! I'll be here whenever you need help.",
                "Farewell! Have a great day!"
            ]
        }
    
    def categorize_input(self, user_input: str) -> str:
        """Catégoriser l'input utilisateur pour fallback approprié"""
        input_lower = user_input.lower().strip()
        
        # Greetings
        if any(word in input_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good evening']):
            return 'greeting'
        
        # Weather
        if any(word in input_lower for word in ['weather', 'temperature', 'rain', 'sunny', 'cloudy']):
            return 'weather'
        
        # Time
        if any(word in input_lower for word in ['time', 'date', 'day', 'hour', 'clock']):
            return 'time'
        
        # Capabilities
        if any(word in input_lower for word in ['what can you', 'what do you', 'who are you', 'help me', 'assist']):
            return 'capabilities'
        
        # Goodbye
        if any(word in input_lower for word in ['goodbye', 'bye', 'see you', 'farewell', 'exit']):
            return 'goodbye'
        
        # Default
        return 'unclear'
    
    def get_fallback_response(self, user_input: str, error_type: str = None) -> str:
        """Obtenir réponse fallback intelligente"""
        if error_type == 'api_error':
            category = 'error'
        elif error_type == 'timeout':
            category = 'error'
        else:
            category = self.categorize_input(user_input)
        
        responses = self.fallback_responses.get(category, self.fallback_responses['unclear'])
        
        # Sélection pseudo-aléatoire basée sur timestamp
        import hashlib
        hash_input = f"{user_input}{int(time.time() / 10)}"  # Change toutes les 10 secondes
        hash_val = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        selected_response = responses[hash_val % len(responses)]
        
        self.logger.info(f"📤 Fallback response (category: {category}): {selected_response}")
        return selected_response

class AssistantCore:
    """Core assistant optimisé avec gestion intelligente"""
    
    def __init__(self):
        self.logger = logging.getLogger("GideonCore")
        
        # Plus d'OpenAI - utilisation des fallbacks uniquement 
        self.openai_client = None
        self.api_available = False
        
        # Les fallbacks sont maintenant le système principal
        self.fallbacks = IntelligentFallbacks()
        
        # Mémoire de conversation
        self.context_memory = deque(maxlen=10)
        self.response_cache = {}
        
        # Statistiques
        self.stats = {
            'total_requests': 0,
            'successful_ai_responses': 0,
            'fallback_responses': 0,
            'cached_responses': 0,
            'avg_response_time': 0,
            'api_errors': 0
        }
        
        self.logger.info("✅ Gideon Assistant Core initialisé (mode local uniquement)")
    
    def _test_api_connection(self) -> bool:
        """Test rapide de connexion API"""
        if not self.openai_client:
            return False
        
        try:
            # Test minimal avec timeout court
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=5,
                timeout=3
            )
            self.api_available = True
            self.logger.info("✅ API OpenAI connectée et fonctionnelle")
            return True
            
        except Exception as e:
            self.api_available = False
            self.logger.warning(f"⚠️ API OpenAI non disponible: {e}")
            return False
    
    def _get_cache_key(self, user_input: str) -> str:
        """Générer clé de cache pour input utilisateur"""
        return user_input.lower().strip()[:100]  # Limitée à 100 chars
    
    def _build_context_messages(self, current_input: str) -> List[Dict]:
        """Construire messages avec contexte de conversation"""
        messages = [{"role": "system", "content": config.ai.SYSTEM_PROMPT}]
        
        # Ajouter contexte récent (max 3 derniers échanges)
        recent_context = list(self.context_memory)[-3:]
        for context in recent_context:
            if context.success:  # Seulement les réponses réussies
                messages.append({"role": "user", "content": context.user_input})
                messages.append({"role": "assistant", "content": context.ai_response})
        
        # Message actuel
        messages.append({"role": "user", "content": current_input})
        
        return messages
    
    def generate_ai_response(self, user_input: str) -> str:
        """Générer réponse IA avec fallbacks robustes"""
        start_time = time.time()
        self.stats['total_requests'] += 1
        
        # Validation input
        if not user_input or not user_input.strip():
            return self.fallbacks.get_fallback_response("", "empty_input")
        
        user_input = user_input.strip()
        
        # Check cache d'abord
        cache_key = self._get_cache_key(user_input)
        if cache_key in self.response_cache:
            self.stats['cached_responses'] += 1
            cached_response = self.response_cache[cache_key]
            self.logger.info(f"📋 Réponse en cache: {cached_response[:50]}...")
            
            # Ajouter au contexte
            context = ConversationContext(
                user_input=user_input,
                ai_response=cached_response,
                timestamp=time.time(),
                response_time=0.01,  # Cache très rapide
                success=True,
                fallback_used=False
            )
            self.context_memory.append(context)
            
            return cached_response
        
        # Tentative réponse IA
        ai_response = None
        fallback_used = False
        
        # Fallback si nécessaire
        if not ai_response:
            ai_response = self.fallbacks.get_fallback_response(
                user_input, 
                "api_error" if not self.api_available else "no_response"
            )
            fallback_used = True
            self.stats['fallback_responses'] += 1
        
        # Calculs de performance
        response_time = time.time() - start_time
        
        # Mise à jour moyenne temps de réponse
        total_requests = self.stats['total_requests']
        current_avg = self.stats['avg_response_time']
        self.stats['avg_response_time'] = ((current_avg * (total_requests - 1)) + response_time) / total_requests
        
        # Ajouter au contexte
        context = ConversationContext(
            user_input=user_input,
            ai_response=ai_response,
            timestamp=time.time(),
            response_time=response_time,
            success=not fallback_used,
            fallback_used=fallback_used
        )
        self.context_memory.append(context)
        
        # Log détaillé
        status = "FALLBACK" if fallback_used else "AI"
        self.logger.info(f"🤖 [{status}] Réponse générée en {response_time:.2f}s: {ai_response[:50]}...")
        
        return ai_response
    
    def process_voice_command(self, command_text: str) -> Dict:
        """Traiter commande vocale complète"""
        if not command_text:
            return {
                'success': False,
                'error': 'Empty command',
                'response': 'I didn\'t hear anything. Could you try again?'
            }
        
        try:
            start_time = time.time()
            
            # Générer réponse
            response = self.generate_ai_response(command_text)
            
            processing_time = time.time() - start_time
            
            self.logger.info(f"🎯 Commande traitée: '{command_text}' → '{response}' ({processing_time:.2f}s)")
            
            return {
                'success': True,
                'command': command_text,
                'response': response,
                'processing_time': processing_time,
                'fallback_used': not self.api_available,
                'timestamp': time.time()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erreur traitement commande: {e}")
            
            fallback_response = self.fallbacks.get_fallback_response(command_text, "processing_error")
            
            return {
                'success': False,
                'error': str(e),
                'command': command_text,
                'response': fallback_response,
                'fallback_used': True,
                'timestamp': time.time()
            }
    
    def get_conversation_summary(self) -> Dict:
        """Obtenir résumé de la conversation"""
        total_exchanges = len(self.context_memory)
        successful_exchanges = sum(1 for ctx in self.context_memory if ctx.success)
        
        if total_exchanges > 0:
            avg_response_time = sum(ctx.response_time for ctx in self.context_memory) / total_exchanges
            success_rate = (successful_exchanges / total_exchanges) * 100
        else:
            avg_response_time = 0
            success_rate = 0
        
        return {
            'total_exchanges': total_exchanges,
            'successful_exchanges': successful_exchanges,
            'success_rate': f"{success_rate:.1f}%",
            'avg_response_time': f"{avg_response_time:.2f}s",
            'api_available': self.api_available,
            'cache_size': len(self.response_cache)
        }
    
    def get_stats(self) -> Dict:
        """Obtenir statistiques complètes"""
        return {
            **self.stats,
            'api_available': self.api_available,
            'cache_size': len(self.response_cache),
            'context_memory_size': len(self.context_memory),
            'conversation_summary': self.get_conversation_summary()
        }
    
    def reset_api_connection(self) -> bool:
        """Réinitialiser connexion API"""
        self.logger.info("🔄 Réinitialisation connexion API...")
        
        if self._test_api_connection():
            self.logger.info("✅ Connexion API rétablie")
            return True
        else:
            self.logger.warning("❌ Connexion API toujours indisponible")
            return False
    
    def cleanup_memory_resources(self):
        """Nettoyer ressources mémoire"""
        # Limiter cache
        if len(self.response_cache) > 20:
            # Garder seulement les 20 plus récentes
            items = list(self.response_cache.items())
            self.response_cache = dict(items[-20:])
        
        # Limiter contexte
        if len(self.context_memory) > 5:
            # Garder seulement les 5 plus récents
            recent_contexts = list(self.context_memory)[-5:]
            self.context_memory.clear()
            self.context_memory.extend(recent_contexts)
        
        self.logger.debug("🧹 Nettoyage mémoire assistant terminé")
    
    def cleanup(self):
        """Nettoyage complet"""
        self.cleanup_memory_resources()
        self.logger.info("🧹 Cleanup assistant core terminé")

# Instance globale
assistant_core = AssistantCore() 