"""
Enhanced Audio Manager for Gideon AI Assistant
PRODUCTION OPTIMIZED FOR MACOS - Auto-calibration + Wake Word Detection
"""

import threading
import time
import logging
import queue
import difflib
import platform
from typing import Optional, Callable, List
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
    """PRODUCTION audio configuration for macOS"""
    # Optimized sample rate for macOS
    SAMPLE_RATE: int = 16000
    CHUNK_SIZE: int = 1024
    CHANNELS: int = 1
    
    # Intelligent timeouts
    LISTEN_TIMEOUT: float = 3.0
    PHRASE_TIMEOUT: float = 6.0
    PAUSE_THRESHOLD: float = 0.6
    
    # macOS specific optimizations
    ENERGY_THRESHOLD: int = 250
    DYNAMIC_ENERGY_THRESHOLD: bool = True
    AMBIENT_NOISE_DURATION: float = 0.5
    AUTO_CALIBRATE_INTERVAL: float = 60.0
    
    # Performance settings
    RETRY_DELAY: float = 1.0
    MAX_RETRIES: int = 3
    
    # Language settings
    LANGUAGE: str = "en-US"
    ALTERNATIVE_LANGUAGES: list = field(default_factory=lambda: ["fr-FR", "en-GB"])
    
    # Wake word settings
    WAKE_WORDS: list = field(default_factory=lambda: [
        "hey gideon", "hi gideon", "hello gideon",
        "hey jarvis", "hi jarvis", "hello jarvis", 
        "gideon", "jarvis", "computer", "assistant"
    ])
    WAKE_WORD_THRESHOLD: float = 0.75

@dataclass
class VoiceCommand:
    """Voice command data structure with wake word detection"""
    text: str
    confidence: float
    timestamp: float
    language: str = "en-US"
    is_wake_word: bool = False
    wake_word_matched: str = ""

class MacOSAudioOptimizer:
    """macOS specific audio optimizations"""
    
    @staticmethod
    def check_macos_permissions():
        """Vérifier et optimiser permissions microphone macOS"""
        if platform.system() != "Darwin":
            return True
        
        try:
            # Test rapide d'accès micro
            devices = sd.query_devices()
            
            # Chercher des devices d'entrée
            input_devices = [d for d in devices if d['max_input_channels'] > 0]
            
            if not input_devices:
                logging.warning("❌ Aucun device d'entrée audio détecté sur macOS")
                return False
            
            logging.info(f"✅ {len(input_devices)} devices audio détectés sur macOS")
            return True
            
        except Exception as e:
            logging.error(f"❌ Erreur permissions audio macOS: {e}")
            return False
    
    @staticmethod
    def get_optimal_microphone():
        """Obtenir le meilleur microphone pour macOS"""
        if not HAS_SOUNDDEVICE:
            return sr.Microphone()
        
        try:
            devices = sd.query_devices()
            
            # Priorité aux devices avec "built-in" ou "internal"
            best_device = None
            best_score = 0
            
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    score = 0
                    name_lower = device['name'].lower()
                    
                    # Bonus pour devices intégrés
                    if any(keyword in name_lower for keyword in ['built-in', 'internal', 'macbook']):
                        score += 10
                    
                    # Bonus pour sample rate élevé
                    score += min(device['default_samplerate'] / 1000, 48)
                    
                    # Bonus pour channels
                    score += device['max_input_channels']
                    
                    if score > best_score:
                        best_score = score
                        best_device = i
            
            if best_device is not None:
                device_info = devices[best_device]
                logging.info(f"🎤 Microphone optimal: {device_info['name']} "
                           f"({device_info['default_samplerate']}Hz)")
                return sr.Microphone(device_index=best_device)
            else:
                logging.warning("⚠️ Utilisation microphone par défaut")
                return sr.Microphone()
                
        except Exception as e:
            logging.error(f"❌ Erreur sélection microphone: {e}")
            return sr.Microphone()

class WakeWordDetector:
    """Détecteur de wake word intelligent avec fuzzy matching"""
    
    def __init__(self, wake_words: List[str], threshold: float = 0.75):
        self.wake_words = [word.lower().strip() for word in wake_words]
        self.threshold = threshold
    
    def detect_wake_word(self, text: str) -> tuple:
        """Détecter wake word avec fuzzy matching"""
        if not text:
            return False, ""
        
        text_lower = text.lower().strip()
        
        # Recherche exacte d'abord
        for wake_word in self.wake_words:
            if wake_word in text_lower:
                return True, wake_word
        
        # Fuzzy matching pour variations
        best_match = ""
        best_ratio = 0
        
        for wake_word in self.wake_words:
            # Ratio de similarité
            ratio = difflib.SequenceMatcher(None, wake_word, text_lower).ratio()
            
            if ratio > best_ratio and ratio >= self.threshold:
                best_ratio = ratio
                best_match = wake_word
        
        if best_match:
            return True, f"{best_match} (fuzzy: {best_ratio:.2f})"
        
        return False, ""

class AudioManager:
    """PRODUCTION Audio Manager with macOS optimizations"""
    
    def __init__(self, config: AudioConfig = None):
        self.config = config or AudioConfig()
        self.logger = logging.getLogger("AudioManagerPRO")
        
        # State management
        self.is_listening = False
        self.is_speaking = False
        self.consecutive_failures = 0
        self.last_successful_recognition = 0
        self.last_calibration = 0
        
        # Components
        self.recognizer = None
        self.microphone = None
        self.tts_engine = None
        self.voice_queue = queue.Queue()
        self.listen_thread = None
        
        # macOS optimizations
        self.macos_optimizer = MacOSAudioOptimizer()
        self.wake_word_detector = WakeWordDetector(
            self.config.WAKE_WORDS, 
            self.config.WAKE_WORD_THRESHOLD
        )
        
        # Performance monitoring
        self.stats = {
            'total_listens': 0,
            'successful_recognitions': 0,
            'wake_words_detected': 0,
            'failures': 0,
            'avg_response_time': 0,
            'calibrations': 0
        }
        
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize components with macOS optimizations"""
        self.logger.info("🔧 Initialisation composants audio pour macOS...")
        
        # Vérifier permissions macOS
        if not self.macos_optimizer.check_macos_permissions():
            self.logger.warning("⚠️ Problèmes de permissions audio macOS détectés")
        
        # Initialize speech recognition
        if HAS_SPEECH_RECOGNITION:
            try:
                self.recognizer = sr.Recognizer()
                
                # Configuration optimisée macOS
                self.recognizer.energy_threshold = self.config.ENERGY_THRESHOLD
                self.recognizer.dynamic_energy_threshold = self.config.DYNAMIC_ENERGY_THRESHOLD
                self.recognizer.pause_threshold = self.config.PAUSE_THRESHOLD
                self.recognizer.operation_timeout = self.config.LISTEN_TIMEOUT
                
                # Microphone optimal
                self.microphone = self.macos_optimizer.get_optimal_microphone()
                
                if self.microphone:
                    # Auto-calibration initiale
                    self.auto_calibrate_microphone()
                    self.logger.info("✅ Speech recognition initialisé avec succès")
                else:
                    self.logger.warning("⚠️ Microphone non disponible")
                    
            except Exception as e:
                self.logger.error(f"❌ Échec initialisation speech recognition: {e}")
                self.recognizer = None
                self.microphone = None
        
        # Initialize TTS avec optimisations
        if HAS_TTS:
            try:
                self.tts_engine = pyttsx3.init()
                
                # Configuration TTS optimisée
                voices = self.tts_engine.getProperty('voices')
                if voices:
                    # Préférer voix système
                    for voice in voices:
                        if 'english' in voice.name.lower() or 'us' in voice.id.lower():
                            self.tts_engine.setProperty('voice', voice.id)
                            break
                
                # Paramètres optimaux
                self.tts_engine.setProperty('rate', 180)  # Vitesse optimale
                self.tts_engine.setProperty('volume', 0.9)
                
                self.logger.info("✅ TTS engine initialisé avec optimisations")
                
            except Exception as e:
                self.logger.error(f"❌ Échec initialisation TTS: {e}")
                self.tts_engine = None
    
    def auto_calibrate_microphone(self) -> bool:
        """Auto-calibration intelligente du microphone pour macOS"""
        if not self.recognizer or not self.microphone:
            return False
        
        try:
            self.logger.info("🔧 Auto-calibration microphone macOS...")
            
            with self.microphone as source:
                # Calibration ambiante
                old_threshold = self.recognizer.energy_threshold
                
                self.recognizer.adjust_for_ambient_noise(
                    source, 
                    duration=self.config.AMBIENT_NOISE_DURATION
                )
                
                new_threshold = self.recognizer.energy_threshold
                
                # Validation du threshold
                if new_threshold < 100:
                    self.recognizer.energy_threshold = 200
                    self.logger.warning("⚠️ Threshold trop bas, ajusté à 200")
                elif new_threshold > 1000:
                    self.recognizer.energy_threshold = 800
                    self.logger.warning("⚠️ Threshold trop haut, ajusté à 800")
                
                self.last_calibration = time.time()
                self.stats['calibrations'] += 1
                
                self.logger.info(f"✅ Calibration terminée: {old_threshold} → {self.recognizer.energy_threshold}")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Erreur calibration: {e}")
            return False
    
    def _should_recalibrate(self) -> bool:
        """Déterminer si une re-calibration est nécessaire"""
        # Re-calibration périodique
        if time.time() - self.last_calibration > self.config.AUTO_CALIBRATE_INTERVAL:
            return True
        
        # Re-calibration après échecs multiples
        if self.consecutive_failures >= 3:
            return True
        
        return False
    
    def test_microphone(self) -> bool:
        """Test microphone avec auto-calibration"""
        if not self.recognizer or not self.microphone:
            return False
        
        try:
            with self.microphone as source:
                self.logger.info("🎤 Test microphone avec auto-calibration...")
                
                # Auto-calibration si nécessaire
                if self._should_recalibrate():
                    self.auto_calibrate_microphone()
                
                # Test d'écoute court
                audio = self.recognizer.listen(source, timeout=2, phrase_time_limit=3)
                
                # Tentative de reconnaissance
                text = self.recognizer.recognize_google(audio, language=self.config.LANGUAGE)
                
                self.logger.info(f"✅ Test micro réussi: '{text}'")
                return True
                
        except sr.WaitTimeoutError:
            self.logger.warning("⏰ Test micro timeout - aucune parole détectée")
            return False
        except sr.UnknownValueError:
            self.logger.info("✅ Micro fonctionne - parole non comprise (normal)")
            return True
        except Exception as e:
            self.logger.error(f"❌ Test micro échoué: {e}")
            return False
    
    def listen_once(self) -> Optional[VoiceCommand]:
        """Listen optimisé avec wake word detection"""
        if not self.recognizer or not self.microphone:
            return None
        
        start_time = time.time()
        self.stats['total_listens'] += 1
        
        try:
            # Auto-calibration si nécessaire
            if self._should_recalibrate():
                self.auto_calibrate_microphone()
            
            with self.microphone as source:
                # Listen avec timeouts optimisés
                audio = self.recognizer.listen(
                    source,
                    timeout=self.config.LISTEN_TIMEOUT,
                    phrase_time_limit=self.config.PHRASE_TIMEOUT
                )
                
                # Reconnaissance avec langues multiples
                text = None
                for language in [self.config.LANGUAGE] + self.config.ALTERNATIVE_LANGUAGES:
                    try:
                        text = self.recognizer.recognize_google(audio, language=language)
                        break
                    except sr.UnknownValueError:
                        continue
                    except sr.RequestError:
                        continue
                
                if not text:
                    return None
                
                # Success metrics
                response_time = time.time() - start_time
                self.last_successful_recognition = time.time()
                self.consecutive_failures = 0
                self.stats['successful_recognitions'] += 1
                
                # Update average response time
                total_success = self.stats['successful_recognitions']
                current_avg = self.stats['avg_response_time']
                self.stats['avg_response_time'] = ((current_avg * (total_success - 1)) + response_time) / total_success
                
                # Wake word detection
                is_wake, wake_matched = self.wake_word_detector.detect_wake_word(text)
                if is_wake:
                    self.stats['wake_words_detected'] += 1
                
                command = VoiceCommand(
                    text=text,
                    confidence=1.0,
                    timestamp=time.time(),
                    language=self.config.LANGUAGE,
                    is_wake_word=is_wake,
                    wake_word_matched=wake_matched
                )
                
                self.logger.info(f"🎤 Reconnu: '{text}' ({response_time:.2f}s)"
                                + (f" WAKE: {wake_matched}" if is_wake else ""))
                return command
                
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            self.logger.debug("❓ Parole détectée mais non reconnue")
            return None
        except sr.RequestError as e:
            self.logger.error(f"❌ Erreur service reconnaissance: {e}")
            self.consecutive_failures += 1
        except Exception as e:
            self.logger.error(f"❌ Erreur inattendue reconnaissance: {e}")
            self.consecutive_failures += 1
        
        # Gestion des échecs
        self.stats['failures'] += 1
        
        # Pause prolongée après échecs multiples
        if self.consecutive_failures >= self.config.MAX_RETRIES:
            self.logger.warning(f"⚠️ {self.consecutive_failures} échecs consécutifs - pause prolongée")
            time.sleep(5.0)
            self.consecutive_failures = 0
        
        return None
    
    def start_continuous_listening(self):
        """Start optimized continuous listening with wake word detection"""
        if not self.recognizer or not self.microphone:
            self.logger.warning("❌ Impossible d'écouter - reconnaissance vocale indisponible")
            return
        
        if self.is_listening:
            self.logger.warning("⚠️ Déjà en écoute")
            return
        
        def _intelligent_listen_loop():
            self.logger.info("🎤 Démarrage écoute intelligente avec wake word...")
            
            while self.is_listening:
                # Vérification état et pause si nécessaire
                if self.consecutive_failures >= self.config.MAX_RETRIES:
                    time.sleep(self.config.RETRY_DELAY * 2)
                    continue
                
                # Écoute de commande
                command = self.listen_once()
                
                if command:
                    # Mettre en queue pour traitement
                    self.voice_queue.put(command)
                    
                    # Log spécial pour wake words
                    if command.is_wake_word:
                        self.logger.info(f"🎯 WAKE WORD détecté: {command.wake_word_matched}")
                    
                    # Pause courte après succès
                    time.sleep(0.3)
                else:
                    # Délai intelligent basé sur taux d'échec
                    delay = self.config.RETRY_DELAY
                    if self.consecutive_failures > 0:
                        delay *= (1 + self.consecutive_failures * 0.3)
                    
                    time.sleep(min(delay, 3.0))
                
                # Nettoyage mémoire périodique
                if self.stats['total_listens'] % 50 == 0:
                    gc.collect()
        
        self.is_listening = True
        self.listen_thread = threading.Thread(target=_intelligent_listen_loop, daemon=True)
        self.listen_thread.start()
        
        self.logger.info("🎤 Écoute continue démarrée avec optimisations macOS")
    
    def stop_continuous_listening(self):
        """Stop continuous listening"""
        if not self.is_listening:
            return
        
        self.is_listening = False
        
        if self.listen_thread:
            self.listen_thread.join(timeout=2.0)
        
        self.logger.info("🔇 Écoute continue arrêtée")
    
    def speak(self, text: str) -> bool:
        """TTS optimisé avec gestion concurrence"""
        if not self.tts_engine:
            self.logger.info(f"🔊 [PAS DE TTS] {text}")
            return False
        
        if self.is_speaking:
            self.logger.warning("⚠️ Déjà en train de parler - ignoré")
            return False
        
        try:
            self.is_speaking = True
            
            # TTS dans thread séparé pour éviter blocage
            def _speak():
                try:
                    self.tts_engine.say(text)
                    self.tts_engine.runAndWait()
                except Exception as e:
                    self.logger.error(f"❌ Erreur TTS: {e}")
                finally:
                    self.is_speaking = False
            
            speak_thread = threading.Thread(target=_speak, daemon=True)
            speak_thread.start()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur TTS: {e}")
            self.is_speaking = False
            return False
    
    def get_next_command(self, timeout: float = None) -> Optional[VoiceCommand]:
        """Get next voice command from queue"""
        try:
            return self.voice_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def get_stats(self) -> dict:
        """Get enhanced performance statistics"""
        success_rate = 0
        wake_word_rate = 0
        
        if self.stats['total_listens'] > 0:
            success_rate = (self.stats['successful_recognitions'] / self.stats['total_listens']) * 100
        
        if self.stats['successful_recognitions'] > 0:
            wake_word_rate = (self.stats['wake_words_detected'] / self.stats['successful_recognitions']) * 100
        
        return {
            'total_listens': self.stats['total_listens'],
            'successful_recognitions': self.stats['successful_recognitions'],
            'wake_words_detected': self.stats['wake_words_detected'],
            'failures': self.stats['failures'],
            'calibrations': self.stats['calibrations'],
            'success_rate': f"{success_rate:.1f}%",
            'wake_word_rate': f"{wake_word_rate:.1f}%",
            'avg_response_time': f"{self.stats['avg_response_time']:.2f}s",
            'consecutive_failures': self.consecutive_failures,
            'is_listening': self.is_listening,
            'is_speaking': self.is_speaking,
            'energy_threshold': getattr(self.recognizer, 'energy_threshold', 0),
            'last_calibration': f"{time.time() - self.last_calibration:.1f}s ago" if self.last_calibration else "Never"
        }
    
    def cleanup(self):
        """Enhanced cleanup with macOS optimizations"""
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
        
        self.logger.info("🧹 Audio manager cleanup terminé (optimisé macOS)")

# Global audio manager instance
audio_manager = AudioManager() 