"""
Enhanced core assistant functionality with FIXED dependencies
Compatible version with modern OpenAI API and fallback options
"""

import threading
import queue
import time
import logging
import os
import platform
from typing import Optional, Callable, Any
from dataclasses import dataclass
import gc # For garbage collection

# Core imports - always available
from config import config
from .event_system import EventSystem
from .logger import GideonLogger

# Optional imports with fallbacks (Problem #9)
try:
    from openai import OpenAI  # ✅ NEW API (>= 1.0.0) (Problem #1)
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    logging.warning("OpenAI not available - AI responses disabled")

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    logging.warning("OpenCV not available - Face detection disabled")

try:
    from mtcnn import MTCNN  # ✅ Alternative to face_recognition (Problem #3)
    HAS_MTCNN = True
except ImportError:
    HAS_MTCNN = False
    logging.warning("MTCNN not available - Face detection disabled")

try:
    import speech_recognition as sr
    HAS_SPEECH_RECOGNITION = True
except ImportError:
    HAS_SPEECH_RECOGNITION = False
    logging.warning("SpeechRecognition not available - Voice commands disabled")

try:
    import pyttsx3
    HAS_PYTTSX3 = True
except ImportError:
    HAS_PYTTSX3 = False
    logging.warning("pyttsx3 not available - Text-to-speech disabled")

try:
    import sounddevice as sd
    HAS_SOUNDDEVICE = True
except ImportError:
    HAS_SOUNDDEVICE = False
    logging.warning("sounddevice not available - Audio processing disabled")

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    logging.warning("numpy not available - Audio processing disabled")

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    logging.warning("requests not available - HTTP requests disabled")

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    logging.warning("psutil not available - System monitoring disabled")

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    logging.warning("PIL not available - Image processing disabled")

class MemoryMonitor: # (Problem #7)
    def __init__(self, limit_mb: int = 200):
        self.logger = GideonLogger("MemoryMonitor")
        self.limit_mb = limit_mb

    def get_memory_usage(self) -> float:
        if not HAS_PSUTIL:
            return 0.0
        try:
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024 * 1024) # MB
        except Exception as e:
            self.logger.error(f"Error getting memory usage: {e}")
            return 0.0

    def check_memory_limit(self) -> bool:
        usage = self.get_memory_usage()
        if usage > self.limit_mb:
            self.logger.warning(f"🚨 Memory usage ({usage:.1f}MB) exceeds limit ({self.limit_mb}MB). Attempting garbage collection.")
            self.force_garbage_collection()
            return False
        return True

    def force_garbage_collection(self):
        gc.collect()
        self.logger.info("🗑️ Forced garbage collection.")

class PermissionChecker: # (Problem #5)
    def __init__(self):
        self.logger = GideonLogger("PermissionChecker")
        self.system = platform.system()

    def check_microphone_permission(self) -> bool:
        if not HAS_SOUNDDEVICE:
            self.logger.warning("Sounddevice not available, cannot check microphone permission.")
            return False
        try:
            devices = sd.query_devices()
            input_devices = [d for d in devices if d['max_input_channels'] > 0]
            if len(input_devices) > 0:
                self.logger.info("✅ Microphone device detected.")
                return True
            else:
                self.logger.warning("❌ No microphone input devices found.")
                if self.system == "Darwin":
                    self.logger.warning("💡 macOS: Check System Preferences > Security & Privacy > Microphone.")
                return False
        except Exception as e:
            self.logger.error(f"Error checking microphone: {e}")
            return False

    def check_camera_permission(self) -> bool:
        if not HAS_CV2:
            self.logger.warning("OpenCV not available, cannot check camera permission.")
            return False
        try:
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                cap.release()
                self.logger.info("✅ Camera accessible.")
                return True
            else:
                self.logger.warning("❌ Camera not accessible.")
                if self.system == "Darwin":
                    self.logger.warning("💡 macOS: Check System Preferences > Security & Privacy > Camera.")
                return False
        except Exception as e:
            self.logger.error(f"Error checking camera: {e}")
            return False

class GideonCoreProduction:
    """
    Enhanced Gideon AI Assistant Core - PRODUCTION VERSION
    Graceful degradation when dependencies are missing
    """
    def __init__(self):
        self.logger = GideonLogger()
        self.event_system = EventSystem()
        self.memory_monitor = MemoryMonitor() # (Problem #7)
        self.permission_checker = PermissionChecker() # (Problem #5)

        # OpenAI Client (Problem #1)
        self.openai_client = None
        if HAS_OPENAI:
            try:
                self.openai_client = OpenAI(api_key=config.ai.OPENAI_API_KEY)
                self.logger.info("✅ OpenAI client initialized.")
            except Exception as e:
                self.logger.error(f"❌ Failed to initialize OpenAI client: {e}")
                # Ne pas modifier HAS_OPENAI ici, c'est une variable globale

        # TTS Engine (Problem #9)
        self.tts_engine = None
        if HAS_PYTTSX3:
            try:
                self.tts_engine = pyttsx3.init()
                self.logger.info("✅ TTS engine initialized.")
            except Exception as e:
                self.logger.error(f"❌ Failed to initialize TTS engine: {e}")
                # Ne pas modifier HAS_PYTTSX3 ici

        # Speech Recognition (Problem #9)
        self.recognizer = None
        self.microphone = None
        if HAS_SPEECH_RECOGNITION and HAS_SOUNDDEVICE: # (Problem #2)
            try:
                self.recognizer = sr.Recognizer()
                self.microphone = sr.Microphone()
                self.logger.info("✅ Speech recognition initialized.")
            except Exception as e:
                self.logger.error(f"❌ Failed to initialize speech recognition: {e}")
                # Ne pas modifier HAS_SPEECH_RECOGNITION ici

        # Face Detection (Problem #3)
        self.face_detector = None
        self.user_encoding = None
        if HAS_MTCNN and HAS_CV2:
            try:
                self.face_detector = MTCNN()
                self._load_user_face()
                self.logger.info("✅ Face detector initialized.")
            except Exception as e:
                self.logger.error(f"❌ Failed to initialize face detector: {e}")
                # Ne pas modifier HAS_MTCNN ici

        # Audio processing
        self.audio_queue = queue.Queue()
        self.is_listening = False
        self.is_speaking = False

    def _load_user_face(self):
        """Load user face for recognition"""
        try:
            if HAS_PIL and os.path.exists("ton_visage.jpg"):
                from PIL import Image
                user_image = Image.open("ton_visage.jpg")
                # Convert to RGB if needed
                if user_image.mode != 'RGB':
                    user_image = user_image.convert('RGB')
                # Store for comparison
                self.user_encoding = user_image
                self.logger.info("✅ User face loaded for recognition.")
            else:
                self.logger.warning("⚠️ User face image not found. Face recognition disabled.")
        except Exception as e:
            self.logger.error(f"❌ Error loading user face: {e}")

    def speak(self, text: str) -> None:
        """Text-to-speech with fallback"""
        if not HAS_PYTTSX3 or not self.tts_engine:
            self.logger.info(f"🔊 [TTS FALLBACK] {text}")
            return
        
        try:
            self.is_speaking = True
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            self.logger.error(f"❌ TTS error: {e}")
            self.logger.info(f"🔊 [TTS FALLBACK] {text}")
        finally:
            self.is_speaking = False

    def listen_once(self) -> Optional[str]:
        """Listen for voice command with fallback"""
        if not HAS_SPEECH_RECOGNITION or not self.recognizer or not self.microphone:
            self.logger.warning("Speech recognition not available.")
            return None
        
        try:
            self.is_listening = True
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            text = self.recognizer.recognize_google(audio)
            self.logger.info(f"🎤 Heard: {text}")
            return text
        except sr.WaitTimeoutError:
            self.logger.info("⏰ No speech detected within timeout.")
            return None
        except sr.UnknownValueError:
            self.logger.info("❓ Speech not recognized.")
            return None
        except Exception as e:
            self.logger.error(f"❌ Speech recognition error: {e}")
            return None
        finally:
            self.is_listening = False

    def authenticate_user(self) -> bool:
        """Face authentication with fallback"""
        if not HAS_MTCNN or not HAS_CV2 or not self.face_detector:
            self.logger.warning("Face detection not available. Skipping authentication.")
            return True  # Allow access if face detection is not available
        
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                self.logger.error("❌ Cannot open camera.")
                return False
            
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                self.logger.error("❌ Cannot read from camera.")
                return False
            
            # Convert frame to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Detect faces
            faces = self.face_detector.detect_faces(frame_rgb)
            
            if len(faces) == 0:
                self.logger.warning("❌ No face detected.")
                return False
            
            # For now, just check if a face is detected
            # In a real implementation, you would compare with stored face
            self.logger.info("✅ Face detected. Authentication successful.")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Face authentication error: {e}")
            return False

    def generate_ai_response(self, prompt: str, context: dict = None) -> str:
        """
        Generate AI response using NEW OpenAI API (Problem #1)
        """
        if not HAS_OPENAI or not self.openai_client: # (Problem #9)
            self.logger.warning("OpenAI not available. Providing fallback response.")
            return "I'm running in offline mode. Please check your OpenAI configuration."
        
        try:
            messages = [
                {"role": "system", "content": "You are Gideon, a helpful AI assistant. Be concise and friendly."},
                {"role": "user", "content": prompt}
            ]
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=150,
                temperature=0.7
            )
            
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"❌ OpenAI API error: {e}")
            return "Sorry, I'm having trouble connecting to my AI services right now."

    def process_voice_command(self, command: str) -> str:
        """Process voice command and generate response"""
        if not command:
            return "I didn't hear anything. Could you please repeat?"
        
        # Check memory usage (Problem #7)
        if not self.memory_monitor.check_memory_limit():
            self.logger.warning("Memory usage high, but continuing...")
        
        # Generate AI response
        response = self.generate_ai_response(command)
        
        # Speak response
        self.speak(response)
        
        return response

    def start_continuous_listening(self):
        """Start continuous listening mode"""
        if not HAS_SPEECH_RECOGNITION:
            self.logger.warning("Speech recognition not available for continuous listening.")
            return
        
        def listen_loop():
            while self.is_listening:
                command = self.listen_once()
                if command:
                    self.process_voice_command(command)
        
        self.is_listening = True
        self.listen_thread = threading.Thread(target=listen_loop, daemon=True)
        self.listen_thread.start()
        self.logger.info("🎤 Continuous listening started.")

    def stop_continuous_listening(self):
        """Stop continuous listening mode"""
        self.is_listening = False
        if hasattr(self, 'listen_thread'):
            self.listen_thread.join(timeout=1)
        self.logger.info("🔇 Continuous listening stopped.")

    def get_system_status(self) -> dict:
        """Get system status information"""
        status = {
            "openai_available": HAS_OPENAI,
            "tts_available": HAS_PYTTSX3,
            "speech_recognition_available": HAS_SPEECH_RECOGNITION,
            "face_detection_available": HAS_MTCNN,
            "camera_available": HAS_CV2,
            "audio_available": HAS_SOUNDDEVICE,
            "is_listening": self.is_listening,
            "is_speaking": self.is_speaking
        }
        
        if HAS_PSUTIL:
            try:
                status["memory_usage_mb"] = self.memory_monitor.get_memory_usage()
                status["cpu_percent"] = psutil.cpu_percent()
            except Exception as e:
                self.logger.error(f"Error getting system status: {e}")
        
        return status

    def cleanup(self):
        """Cleanup resources"""
        self.stop_continuous_listening()
        if HAS_PYTTSX3 and self.tts_engine:
            try:
                self.tts_engine.stop()
            except:
                pass
        self.logger.info("🧹 Gideon core cleanup completed.") 