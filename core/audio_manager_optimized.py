"""
Enhanced Audio Manager for Gideon AI Assistant
Optimized for macOS with intelligent speech recognition and low memory usage
"""

import threading
import time
import logging
import queue
from typing import Optional, Callable
from dataclasses import dataclass, field
import gc

# Audio imports with fallbacks
try:
    import speech_recognition as sr
    HAS_SPEECH_RECOGNITION = True
except ImportError:
    HAS_SPEECH_RECOGNITION = False
    logging.warning("SpeechRecognition not available")

try:
    import sounddevice as sd
    import numpy as np
    HAS_SOUNDDEVICE = True
except ImportError:
    HAS_SOUNDDEVICE = False
    logging.warning("Sounddevice not available")

try:
    import pyttsx3
    HAS_TTS = True
except ImportError:
    HAS_TTS = False
    logging.warning("pyttsx3 not available")

@dataclass
class AudioConfig:
    """Optimized audio configuration for macOS"""
    # Reduced sample rate for lower memory usage
    SAMPLE_RATE: int = 16000  # Down from 44100
    CHUNK_SIZE: int = 1024
    CHANNELS: int = 1  # Mono only
    
    # Smart timeouts
    LISTEN_TIMEOUT: float = 3.0  # Max listening time
    PHRASE_TIMEOUT: float = 8.0  # Max phrase length
    PAUSE_THRESHOLD: float = 0.8  # Silence detection
    
    # Performance settings
    AMBIENT_NOISE_DURATION: float = 0.3  # Reduced from 0.5
    RETRY_DELAY: float = 1.0  # Pause between listen attempts
    MAX_RETRIES: int = 3  # Max consecutive failures
    
    # Language settings
    LANGUAGE: str = "en-US"
    ALTERNATIVE_LANGUAGES: list = field(default_factory=lambda: ["fr-FR", "en-GB"])

@dataclass
class VoiceCommand:
    """Voice command data structure"""
    text: str
    confidence: float
    timestamp: float
    language: str = "en-US"

class AudioManager:
    """Optimized audio manager with intelligent speech recognition"""
    
    def __init__(self, config: AudioConfig = None):
        self.config = config or AudioConfig()
        self.logger = logging.getLogger("AudioManager")
        
        # State management
        self.is_listening = False
        self.is_speaking = False
        self.consecutive_failures = 0
        self.last_successful_recognition = 0
        
        # Components
        self.recognizer = None
        self.microphone = None
        self.tts_engine = None
        self.voice_queue = queue.Queue()
        self.listen_thread = None
        
        # Performance monitoring
        self.stats = {
            'total_listens': 0,
            'successful_recognitions': 0,
            'failures': 0,
            'avg_response_time': 0
        }
        
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize audio components with error handling"""
        # Initialize speech recognition
        if HAS_SPEECH_RECOGNITION:
            try:
                self.recognizer = sr.Recognizer()
                
                # Optimized recognizer settings
                self.recognizer.energy_threshold = 300  # Adjust for ambient noise
                self.recognizer.dynamic_energy_threshold = True
                self.recognizer.pause_threshold = self.config.PAUSE_THRESHOLD
                self.recognizer.operation_timeout = self.config.LISTEN_TIMEOUT
                
                # Get the best microphone
                self.microphone = self._get_optimal_microphone()
                
                if self.microphone:
                    self.logger.info("✅ Speech recognition initialized successfully")
                else:
                    self.logger.warning("⚠️ No suitable microphone found")
                    
            except Exception as e:
                self.logger.error(f"❌ Failed to initialize speech recognition: {e}")
                self.recognizer = None
                self.microphone = None
        
        # Initialize TTS
        if HAS_TTS:
            try:
                self.tts_engine = pyttsx3.init()
                
                # Optimize TTS settings
                rate = self.tts_engine.getProperty('rate')
                self.tts_engine.setProperty('rate', max(150, rate - 50))  # Slightly slower
                
                volume = self.tts_engine.getProperty('volume')
                self.tts_engine.setProperty('volume', min(1.0, volume + 0.1))
                
                self.logger.info("✅ TTS engine initialized successfully")
                
            except Exception as e:
                self.logger.error(f"❌ Failed to initialize TTS: {e}")
                self.tts_engine = None
    
    def _get_optimal_microphone(self) -> Optional[sr.Microphone]:
        """Find the best microphone device"""
        if not HAS_SOUNDDEVICE:
            return sr.Microphone()  # Use default
        
        try:
            devices = sd.query_devices()
            
            # Find microphones with highest sample rate
            best_device = None
            best_rate = 0
            
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:  # Input device
                    if device['default_samplerate'] > best_rate:
                        best_rate = device['default_samplerate']
                        best_device = i
            
            if best_device is not None:
                self.logger.info(f"📱 Using microphone: {devices[best_device]['name']}")
                return sr.Microphone(device_index=best_device)
            else:
                self.logger.warning("⚠️ No input devices found, using default")
                return sr.Microphone()
                
        except Exception as e:
            self.logger.error(f"❌ Error selecting microphone: {e}")
            return sr.Microphone()  # Fallback to default
    
    def test_microphone(self) -> bool:
        """Test microphone functionality"""
        if not self.recognizer or not self.microphone:
            return False
        
        try:
            with self.microphone as source:
                self.logger.info("🎤 Testing microphone - speak something...")
                
                # Quick ambient noise adjustment
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # Short test listen
                audio = self.recognizer.listen(source, timeout=2, phrase_time_limit=3)
                
                # Try to recognize
                text = self.recognizer.recognize_google(audio, language=self.config.LANGUAGE)
                
                self.logger.info(f"✅ Microphone test successful: '{text}'")
                return True
                
        except sr.WaitTimeoutError:
            self.logger.warning("⏰ Microphone test timeout - no speech detected")
            return False
        except sr.UnknownValueError:
            self.logger.warning("❓ Microphone working but speech not understood")
            return True  # Microphone works, just didn't understand
        except Exception as e:
            self.logger.error(f"❌ Microphone test failed: {e}")
            return False
    
    def listen_once(self) -> Optional[VoiceCommand]:
        """Listen for a single voice command with optimizations"""
        if not self.recognizer or not self.microphone:
            return None
        
        start_time = time.time()
        self.stats['total_listens'] += 1
        
        try:
            with self.microphone as source:
                # Quick ambient adjustment only if needed
                if time.time() - self.last_successful_recognition > 30:
                    self.recognizer.adjust_for_ambient_noise(source, 
                                                           duration=self.config.AMBIENT_NOISE_DURATION)
                
                # Listen with optimized timeouts
                audio = self.recognizer.listen(
                    source,
                    timeout=self.config.LISTEN_TIMEOUT,
                    phrase_time_limit=self.config.PHRASE_TIMEOUT
                )
                
                # Try recognition with primary language
                text = self.recognizer.recognize_google(
                    audio, 
                    language=self.config.LANGUAGE
                )
                
                # Success!
                response_time = time.time() - start_time
                self.last_successful_recognition = time.time()
                self.consecutive_failures = 0
                self.stats['successful_recognitions'] += 1
                
                # Update average response time
                total_success = self.stats['successful_recognitions']
                current_avg = self.stats['avg_response_time']
                self.stats['avg_response_time'] = ((current_avg * (total_success - 1)) + response_time) / total_success
                
                command = VoiceCommand(
                    text=text,
                    confidence=1.0,  # Google API doesn't provide confidence
                    timestamp=time.time(),
                    language=self.config.LANGUAGE
                )
                
                self.logger.info(f"🎤 Recognized: '{text}' ({response_time:.2f}s)")
                return command
                
        except sr.WaitTimeoutError:
            # Normal timeout - not an error
            return None
            
        except sr.UnknownValueError:
            # Speech was detected but not understood
            self.logger.debug("❓ Speech detected but not recognized")
            return None
            
        except sr.RequestError as e:
            self.logger.error(f"❌ Speech recognition service error: {e}")
            self.consecutive_failures += 1
            
        except Exception as e:
            self.logger.error(f"❌ Unexpected error in speech recognition: {e}")
            self.consecutive_failures += 1
        
        # Handle failures
        self.stats['failures'] += 1
        
        # If too many consecutive failures, take a longer break
        if self.consecutive_failures >= self.config.MAX_RETRIES:
            self.logger.warning(f"⚠️ {self.consecutive_failures} consecutive failures, taking extended break")
            time.sleep(5.0)  # Longer break
            self.consecutive_failures = 0
        
        return None
    
    def start_continuous_listening(self):
        """Start optimized continuous listening"""
        if not self.recognizer or not self.microphone:
            self.logger.warning("❌ Cannot start listening - speech recognition not available")
            return
        
        if self.is_listening:
            self.logger.warning("⚠️ Already listening")
            return
        
        def _optimized_listen_loop():
            self.logger.info("🎤 Starting optimized listening loop...")
            
            while self.is_listening:
                # Check if we should take a break
                if self.consecutive_failures >= self.config.MAX_RETRIES:
                    time.sleep(self.config.RETRY_DELAY * 2)  # Extended break
                    continue
                
                # Listen for command
                command = self.listen_once()
                
                if command:
                    # Put command in queue for processing
                    self.voice_queue.put(command)
                    
                    # Short break after successful recognition
                    time.sleep(0.5)
                else:
                    # Intelligent retry delay based on failure rate
                    delay = self.config.RETRY_DELAY
                    if self.consecutive_failures > 0:
                        delay *= (1 + self.consecutive_failures * 0.5)
                    
                    time.sleep(min(delay, 5.0))  # Cap at 5 seconds
                
                # Periodic memory cleanup
                if self.stats['total_listens'] % 100 == 0:
                    gc.collect()
        
        self.is_listening = True
        self.listen_thread = threading.Thread(target=_optimized_listen_loop, daemon=True)
        self.listen_thread.start()
        
        self.logger.info("🎤 Continuous listening started with optimizations")
    
    def stop_continuous_listening(self):
        """Stop continuous listening"""
        if not self.is_listening:
            return
        
        self.is_listening = False
        
        if self.listen_thread:
            self.listen_thread.join(timeout=2.0)
        
        self.logger.info("🔇 Continuous listening stopped")
    
    def speak(self, text: str) -> bool:
        """Text-to-speech with optimization"""
        if not self.tts_engine:
            self.logger.info(f"🔊 [NO TTS] {text}")
            return False
        
        if self.is_speaking:
            self.logger.warning("⚠️ Already speaking, skipping")
            return False
        
        try:
            self.is_speaking = True
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
            return True
            
        except Exception as e:
            self.logger.error(f"❌ TTS error: {e}")
            return False
            
        finally:
            self.is_speaking = False
    
    def get_next_command(self, timeout: float = None) -> Optional[VoiceCommand]:
        """Get next voice command from queue"""
        try:
            return self.voice_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def get_stats(self) -> dict:
        """Get performance statistics"""
        success_rate = 0
        if self.stats['total_listens'] > 0:
            success_rate = (self.stats['successful_recognitions'] / self.stats['total_listens']) * 100
        
        return {
            'total_listens': self.stats['total_listens'],
            'successful_recognitions': self.stats['successful_recognitions'],
            'failures': self.stats['failures'],
            'success_rate': f"{success_rate:.1f}%",
            'avg_response_time': f"{self.stats['avg_response_time']:.2f}s",
            'consecutive_failures': self.consecutive_failures,
            'is_listening': self.is_listening,
            'is_speaking': self.is_speaking
        }
    
    def cleanup(self):
        """Clean up resources"""
        self.stop_continuous_listening()
        
        if self.tts_engine:
            try:
                self.tts_engine.stop()
            except:
                pass
        
        # Clear queue
        while not self.voice_queue.empty():
            try:
                self.voice_queue.get_nowait()
            except queue.Empty:
                break
        
        self.logger.info("🧹 Audio manager cleanup completed")

# Global audio manager instance
audio_manager = AudioManager() 