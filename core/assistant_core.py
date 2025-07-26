"""
Core assistant functionality integrating existing features
Enhanced version of the original assistant_ia_personnel.py
"""

import face_recognition
import cv2
import speech_recognition as sr
import pyttsx3
import openai
import numpy as np
import threading
import queue
import time
from typing import Optional, Callable, Any
from dataclasses import dataclass

from config import config
from .event_system import EventSystem
from .logger import GideonLogger

@dataclass
class VoiceCommand:
    """Voice command data structure"""
    text: str
    confidence: float
    timestamp: float

class GideonCore:
    """
    Enhanced Gideon AI Assistant Core
    Integrates existing functionality with new modular architecture
    """
    
    def __init__(self):
        self.logger = GideonLogger()
        self.event_system = EventSystem()
        
        # Initialize AI
        openai.api_key = config.ai.OPENAI_API_KEY
        
        # Initialize TTS
        self.tts = pyttsx3.init()
        self._configure_tts()
        
        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Initialize face recognition
        self.user_encoding = None
        self._load_user_face()
        
        # System state
        self.is_listening = False
        self.is_speaking = False
        self.is_authenticated = False
        self.voice_queue = queue.Queue()
        
        # Threading
        self.voice_thread = None
        self.face_thread = None
        
        self.logger.info("Gideon Core initialized successfully")
    
    def _configure_tts(self):
        """Configure text-to-speech settings"""
        voices = self.tts.getProperty('voices')
        if voices:
            # Prefer female voice if available
            for voice in voices:
                if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                    self.tts.setProperty('voice', voice.id)
                    break
        
        self.tts.setProperty('rate', config.audio.TTS_RATE)
        self.tts.setProperty('volume', config.audio.TTS_VOLUME)
    
    def _load_user_face(self):
        """Load and encode user face from photo"""
        try:
            user_image = face_recognition.load_image_file(config.face_recognition.USER_PHOTO_PATH)
            encodings = face_recognition.face_encodings(user_image)
            
            if encodings:
                self.user_encoding = encodings[0]
                self.logger.info("User face encoding loaded successfully")
            else:
                self.logger.error("No face found in user photo")
                
        except Exception as e:
            self.logger.error(f"Failed to load user face: {e}")
    
    def speak(self, text: str, priority: bool = False):
        """
        Speak text with TTS
        
        Args:
            text: Text to speak
            priority: If True, interrupts current speech
        """
        if priority and self.is_speaking:
            self.tts.stop()
        
        def _speak():
            self.is_speaking = True
            self.event_system.emit('speech_started', {'text': text})
            
            self.logger.info(f"🗣️ Speaking: {text}")
            self.tts.say(text)
            self.tts.runAndWait()
            
            self.is_speaking = False
            self.event_system.emit('speech_ended', {'text': text})
        
        # Run in separate thread to avoid blocking
        threading.Thread(target=_speak, daemon=True).start()
    
    def listen_once(self) -> Optional[VoiceCommand]:
        """
        Listen for a single voice command
        
        Returns:
            VoiceCommand object or None if no speech detected
        """
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
                    confidence=1.0,  # Google API doesn't provide confidence
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
        except sr.RequestError as e:
            self.logger.error(f"Voice recognition error: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error during listening: {e}")
            return None
    
    def start_continuous_listening(self):
        """Start continuous voice command listening in background thread"""
        if self.is_listening:
            return
        
        self.is_listening = True
        
        def _listen_loop():
            while self.is_listening:
                command = self.listen_once()
                if command:
                    self.voice_queue.put(command)
                time.sleep(0.1)  # Small delay to prevent CPU overload
        
        self.voice_thread = threading.Thread(target=_listen_loop, daemon=True)
        self.voice_thread.start()
        
        self.logger.info("Continuous listening started")
    
    def stop_continuous_listening(self):
        """Stop continuous voice command listening"""
        self.is_listening = False
        if self.voice_thread:
            self.voice_thread.join(timeout=2)
        
        self.logger.info("Continuous listening stopped")
    
    def get_next_voice_command(self, timeout: float = None) -> Optional[VoiceCommand]:
        """
        Get next voice command from queue
        
        Args:
            timeout: Maximum time to wait for command
            
        Returns:
            VoiceCommand or None if timeout
        """
        try:
            return self.voice_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def authenticate_user(self) -> bool:
        """
        Authenticate user using face recognition
        
        Returns:
            True if user is authenticated, False otherwise
        """
        if not self.user_encoding:
            self.logger.error("No user face encoding available")
            return False
        
        self.logger.info("Starting face recognition authentication...")
        self.speak("Searching for your face...", priority=True)
        
        webcam = cv2.VideoCapture(0)
        if not webcam.isOpened():
            self.logger.error("Could not open webcam")
            self.speak("Camera access failed")
            return False
        
        authenticated = False
        start_time = time.time()
        
        try:
            while time.time() - start_time < config.face_recognition.DETECTION_TIMEOUT:
                ret, frame = webcam.read()
                if not ret:
                    continue
                
                # Convert BGR to RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Find faces in frame
                face_locations = face_recognition.face_locations(rgb_frame)
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                
                for face_encoding in face_encodings:
                    # Compare with known user face
                    matches = face_recognition.compare_faces(
                        [self.user_encoding], 
                        face_encoding,
                        tolerance=config.face_recognition.TOLERANCE
                    )
                    
                    if matches[0]:
                        authenticated = True
                        break
                
                # Show video feed (optional, for debugging)
                if config.system.DEBUG:
                    cv2.imshow("Face Recognition", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                
                if authenticated:
                    break
                    
        except Exception as e:
            self.logger.error(f"Face recognition error: {e}")
        finally:
            webcam.release()
            cv2.destroyAllWindows()
        
        self.is_authenticated = authenticated
        
        if authenticated:
            self.logger.info("User authenticated successfully")
            self.speak("Hello! Authentication successful. I'm at your service.")
            self.event_system.emit('user_authenticated')
        else:
            self.logger.warning("Authentication failed")
            self.speak("Access denied. Face not recognized.")
            self.event_system.emit('authentication_failed')
        
        return authenticated
    
    def generate_ai_response(self, prompt: str, context: dict = None) -> str:
        """
        Generate AI response using OpenAI API
        
        Args:
            prompt: User prompt
            context: Additional context for the AI
            
        Returns:
            AI generated response
        """
        try:
            messages = [
                {"role": "system", "content": config.ai.SYSTEM_PROMPT}
            ]
            
            if context:
                context_str = f"Context: {context}"
                messages.append({"role": "system", "content": context_str})
            
            messages.append({"role": "user", "content": prompt})
            
            response = openai.ChatCompletion.create(
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
    
    def process_voice_command(self, command: VoiceCommand) -> str:
        """
        Process voice command and generate appropriate response
        
        Args:
            command: Voice command to process
            
        Returns:
            Response text
        """
        command_text = command.text.lower()
        
        self.logger.info(f"Processing command: {command.text}")
        self.event_system.emit('command_processing', {'command': command})
        
        # Built-in commands (from original code)
        if any(phrase in command_text for phrase in ["ouvre vs code", "ouvre visual studio code"]):
            response = "Opening Visual Studio Code."
            self.event_system.emit('system_command', {'action': 'open_vscode'})
            return response
            
        elif "recherche" in command_text:
            search_term = command_text.replace("recherche", "").strip()
            response = f"Searching for: {search_term}"
            self.event_system.emit('web_search', {'query': search_term})
            return response
        
        # Default to AI response
        response = self.generate_ai_response(command.text)
        return response
    
    def shutdown(self):
        """Graceful shutdown of all systems"""
        self.logger.info("Shutting down Gideon Core...")
        
        self.stop_continuous_listening()
        
        if self.tts:
            self.tts.stop()
        
        self.event_system.emit('system_shutdown')
        self.logger.info("Gideon Core shutdown complete") 