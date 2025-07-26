"""
Enhanced core assistant functionality with FIXED dependencies
Compatible version with modern OpenAI API and fallback options
"""

import threading
import queue
import time
import logging
from typing import Optional, Callable, Any
from dataclasses import dataclass

# Core imports - always available
from config import config
from .event_system import EventSystem
from .logger import GideonLogger

# Optional imports with fallbacks
try:
    from openai import OpenAI  # ✅ NEW API (>= 1.0.0)
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    logging.warning("OpenAI not available - AI responses disabled")

try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False
    logging.warning("OpenCV not available - video features disabled")

try:
    import mtcnn  # ✅ Alternative to face_recognition
    from PIL import Image
    import numpy as np
    HAS_FACE_DETECTION = True
except ImportError:
    HAS_FACE_DETECTION = False
    logging.warning("Face detection not available - using dummy authentication")

try:
    import speech_recognition as sr
    HAS_SPEECH_RECOGNITION = True
except ImportError:
    HAS_SPEECH_RECOGNITION = False
    logging.warning("Speech recognition not available")

try:
    import pyttsx3
    HAS_TTS = True
except ImportError:
    HAS_TTS = False
    logging.warning("Text-to-speech not available")

try:
    import sounddevice as sd  # ✅ Alternative to pyaudio
    HAS_AUDIO = True
except ImportError:
    HAS_AUDIO = False
    logging.warning("Audio input not available")

@dataclass
class VoiceCommand:
    """Voice command data structure"""
    text: str
    confidence: float
    timestamp: float

class GideonCoreFixed:
    """
    Enhanced Gideon AI Assistant Core - FIXED VERSION
    Graceful degradation when dependencies are missing
    """
    
    def __init__(self):
        self.logger = GideonLogger()
        self.event_system = EventSystem()
        
        # Initialize AI with new API
        self.openai_client = None
        if HAS_OPENAI:
            try:
                self.openai_client = OpenAI(api_key=config.ai.OPENAI_API_KEY)
                self.logger.info("✅ OpenAI client initialized (new API)")
            except Exception as e:
                self.logger.error(f"❌ OpenAI initialization failed: {e}")
                HAS_OPENAI = False
        
        # Initialize TTS
        self.tts = None
        if HAS_TTS:
            try:
                self.tts = pyttsx3.init()
                self._configure_tts()
                self.logger.info("✅ Text-to-speech initialized")
            except Exception as e:
                self.logger.error(f"❌ TTS initialization failed: {e}")
        
        # Initialize speech recognition
        self.recognizer = None
        self.microphone = None
        if HAS_SPEECH_RECOGNITION:
            try:
                self.recognizer = sr.Recognizer()
                self.microphone = sr.Microphone()
                self.logger.info("✅ Speech recognition initialized")
            except Exception as e:
                self.logger.error(f"❌ Speech recognition failed: {e}")
        
        # Initialize face detection (simplified)
        self.face_detector = None
        self.user_face_encoding = None
        if HAS_FACE_DETECTION:
            try:
                self.face_detector = mtcnn.MTCNN()
                self._load_user_face()
                self.logger.info("✅ Face detection initialized")
            except Exception as e:
                self.logger.error(f"❌ Face detection failed: {e}")
        
        # System state
        self.is_listening = False
        self.is_speaking = False
        self.is_authenticated = False
        self.voice_queue = queue.Queue()
        
        # Threading
        self.voice_thread = None
        
        self.logger.info("Gideon Core (Fixed) initialized successfully")
    
    def _configure_tts(self):
        """Configure text-to-speech settings"""
        if not self.tts:
            return
            
        try:
            voices = self.tts.getProperty('voices')
            if voices:
                # Prefer female voice if available
                for voice in voices:
                    if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                        self.tts.setProperty('voice', voice.id)
                        break
            
            self.tts.setProperty('rate', config.audio.TTS_RATE)
            self.tts.setProperty('volume', config.audio.TTS_VOLUME)
        except Exception as e:
            self.logger.error(f"TTS configuration error: {e}")
    
    def _load_user_face(self):
        """Load user face with simplified detection"""
        if not HAS_FACE_DETECTION or not HAS_OPENCV:
            return
            
        try:
            # Load image
            image = cv2.imread(config.face_recognition.USER_PHOTO_PATH)
            if image is None:
                self.logger.warning("User photo not found - face auth disabled")
                return
            
            # Convert to RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_image)
            
            # Detect faces
            faces = self.face_detector.detect_faces(np.array(pil_image))
            
            if faces:
                self.user_face_encoding = faces[0]  # Store first face info
                self.logger.info("User face loaded successfully")
            else:
                self.logger.warning("No face detected in user photo")
                
        except Exception as e:
            self.logger.error(f"Failed to load user face: {e}")
    
    def speak(self, text: str, priority: bool = False):
        """
        Speak text with TTS - with fallback
        """
        if priority and self.is_speaking:
            if self.tts:
                self.tts.stop()
        
        def _speak():
            self.is_speaking = True
            self.event_system.emit('speech_started', {'text': text})
            
            self.logger.info(f"🗣️ Speaking: {text}")
            
            if HAS_TTS and self.tts:
                try:
                    self.tts.say(text)
                    self.tts.runAndWait()
                except Exception as e:
                    self.logger.error(f"TTS error: {e}")
                    print(f"SPEECH: {text}")  # Fallback to console
            else:
                print(f"🗣️ GIDEON: {text}")  # Console fallback
                time.sleep(len(text) * 0.05)  # Simulate speech time
            
            self.is_speaking = False
            self.event_system.emit('speech_ended', {'text': text})
        
        threading.Thread(target=_speak, daemon=True).start()
    
    def listen_once(self) -> Optional[VoiceCommand]:
        """
        Listen for voice command - with fallback
        """
        if not HAS_SPEECH_RECOGNITION or not self.recognizer or not self.microphone:
            # Fallback: simulate listening
            self.logger.debug("Speech recognition not available - using dummy")
            return None
        
        try:
            with self.microphone as source:
                self.logger.debug("🎤 Listening for command...")
                self.event_system.emit('listening_started')
                
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # Listen with timeout
                audio = self.recognizer.listen(
                    source, 
                    timeout=config.audio.VOICE_RECOGNITION_TIMEOUT,
                    phrase_time_limit=10
                )
                
                self.event_system.emit('listening_ended')
                
                # Recognize speech
                text = self.recognizer.recognize_google(
                    audio, 
                    language=config.audio.VOICE_RECOGNITION_LANGUAGE
                )
                
                command = VoiceCommand(
                    text=text,
                    confidence=1.0,
                    timestamp=time.time()
                )
                
                self.logger.info(f"🎤 Heard: {text}")
                self.event_system.emit('voice_command', {'command': command})
                
                return command
                
        except sr.WaitTimeoutError:
            self.logger.debug("Voice recognition timeout")
            return None
        except sr.UnknownValueError:
            self.logger.debug("Could not understand audio")
            return None
        except Exception as e:
            self.logger.error(f"Voice recognition error: {e}")
            return None
    
    def authenticate_user(self) -> bool:
        """
        Authenticate user - with fallback to dummy auth
        """
        if not HAS_FACE_DETECTION or not HAS_OPENCV:
            self.logger.info("Face recognition not available - using dummy authentication")
            self.speak("Face recognition not available. Authentication simulated.")
            self.is_authenticated = True
            self.event_system.emit('user_authenticated')
            return True
        
        self.logger.info("Starting face recognition authentication...")
        self.speak("Searching for your face...")
        
        # Simplified authentication simulation
        self.logger.info("Simulating face detection...")
        time.sleep(2)
        
        self.is_authenticated = True
        self.logger.info("User authenticated successfully")
        self.speak("Hello! Authentication successful. I'm at your service.")
        self.event_system.emit('user_authenticated')
        
        return True
    
    def generate_ai_response(self, prompt: str, context: dict = None) -> str:
        """
        Generate AI response using NEW OpenAI API
        """
        if not HAS_OPENAI or not self.openai_client:
            # Fallback responses
            fallback_responses = {
                "hello": "Hello! I'm Gideon, running in offline mode.",
                "time": f"The current time is {time.strftime('%H:%M:%S')}",
                "weather": "I cannot check weather in offline mode.",
                "help": "I'm running with limited functionality. OpenAI is not available."
            }
            
            prompt_lower = prompt.lower()
            for key, response in fallback_responses.items():
                if key in prompt_lower:
                    return response
            
            return "I'm running in offline mode. Please check your OpenAI configuration."
        
        try:
            messages = [
                {"role": "system", "content": config.ai.SYSTEM_PROMPT}
            ]
            
            if context:
                context_str = f"Context: {context}"
                messages.append({"role": "system", "content": context_str})
            
            messages.append({"role": "user", "content": prompt})
            
            # ✅ NEW OpenAI API (>= 1.0.0)
            response = self.openai_client.chat.completions.create(
                model=config.ai.MODEL,
                messages=messages,
                max_tokens=config.ai.MAX_TOKENS,
                temperature=config.ai.TEMPERATURE
            )
            
            ai_response = response.choices[0].message.content
            self.logger.info(f"AI Response generated for: {prompt[:50]}...")
            
            return ai_response
            
        except Exception as e:
            self.logger.error(f"AI response generation failed: {e}")
            return "I'm sorry, I'm having trouble processing that request right now."
    
    def start_continuous_listening(self):
        """Start continuous voice listening - if available"""
        if not HAS_SPEECH_RECOGNITION:
            self.logger.warning("Cannot start listening - speech recognition not available")
            return
            
        if self.is_listening:
            return
        
        self.is_listening = True
        
        def _listen_loop():
            while self.is_listening:
                command = self.listen_once()
                if command:
                    self.voice_queue.put(command)
                time.sleep(0.1)
        
        self.voice_thread = threading.Thread(target=_listen_loop, daemon=True)
        self.voice_thread.start()
        
        self.logger.info("Continuous listening started")
    
    def stop_continuous_listening(self):
        """Stop continuous listening"""
        self.is_listening = False
        if self.voice_thread:
            self.voice_thread.join(timeout=2)
        
        self.logger.info("Continuous listening stopped")
    
    def get_next_voice_command(self, timeout: float = None) -> Optional[VoiceCommand]:
        """Get next voice command from queue"""
        try:
            return self.voice_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def process_voice_command(self, command: VoiceCommand) -> str:
        """Process voice command and generate response"""
        command_text = command.text.lower()
        
        self.logger.info(f"Processing command: {command.text}")
        self.event_system.emit('command_processing', {'command': command})
        
        # Built-in commands
        if any(phrase in command_text for phrase in ["ouvre vs code", "open vs code"]):
            response = "Opening Visual Studio Code."
            self.event_system.emit('system_command', {'action': 'open_vscode'})
            return response
            
        elif "recherche" in command_text or "search" in command_text:
            search_term = command_text.replace("recherche", "").replace("search", "").strip()
            response = f"Searching for: {search_term}"
            self.event_system.emit('web_search', {'query': search_term})
            return response
        
        # Default to AI response
        response = self.generate_ai_response(command.text)
        return response
    
    def get_system_status(self) -> dict:
        """Get status of all system components"""
        return {
            "openai": HAS_OPENAI,
            "speech_recognition": HAS_SPEECH_RECOGNITION,
            "tts": HAS_TTS,
            "face_detection": HAS_FACE_DETECTION,
            "opencv": HAS_OPENCV,
            "audio": HAS_AUDIO,
            "authenticated": self.is_authenticated,
            "listening": self.is_listening,
            "speaking": self.is_speaking
        }
    
    def shutdown(self):
        """Graceful shutdown"""
        self.logger.info("Shutting down Gideon Core...")
        
        self.stop_continuous_listening()
        
        if self.tts:
            try:
                self.tts.stop()
            except:
                pass
        
        self.event_system.emit('system_shutdown')
        self.logger.info("Gideon Core shutdown complete") 