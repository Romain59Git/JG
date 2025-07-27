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
    """PRODUCTION audio configuration for macOS - FRANÇAIS"""
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
    
    # Language settings - FRANÇAIS PAR DÉFAUT
    LANGUAGE: str = "fr-FR"
    ALTERNATIVE_LANGUAGES: list = field(default_factory=lambda: ["en-US", "en-GB"])
    
    # Wake word settings - FRANÇAIS
    WAKE_WORDS: list = field(default_factory=lambda: [
        "salut gideon", "bonjour gideon", "hey gideon",
        "salut jarvis", "bonjour jarvis", "hey jarvis", 
        "gideon", "jarvis", "ordinateur", "assistant"
    ])
    WAKE_WORD_THRESHOLD: float = 0.75

@dataclass
class VoiceCommand:
    """Voice command data structure with wake word detection - FRANÇAIS"""
    text: str
    confidence: float
    timestamp: float
    language: str = "fr-FR"
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

class FrenchVoiceManager:
    """Gestionnaire de voix françaises pour macOS"""
    
    def __init__(self, tts_engine):
        self.tts_engine = tts_engine
        self.logger = logging.getLogger("FrenchVoice")
        
    def configure_french_voice(self):
        """Configure la meilleure voix française disponible sur macOS"""
        if not self.tts_engine:
            return False
            
        try:
            voices = self.tts_engine.getProperty('voices')
            if not voices:
                self.logger.warning("Aucune voix disponible")
                return False
            
            # Voix françaises prioritaires macOS
            french_voice_priorities = [
                'com.apple.speech.synthesis.voice.thomas',      # Thomas (FR)
                'com.apple.voice.compact.fr-FR.Thomas',
                'com.apple.speech.synthesis.voice.virginie',    # Virginie (FR)
                'com.apple.voice.compact.fr-FR.Virginie',
                'com.apple.eloquence.fr-FR.Grandpa',
                'com.apple.eloquence.fr-FR.Grandma'
            ]
            
            # Recherche voix française par priorité
            for priority_voice in french_voice_priorities:
                for voice in voices:
                    if priority_voice in voice.id:
                        self.tts_engine.setProperty('voice', voice.id)
                        self.logger.info(f"✅ Voix française configurée: {voice.name}")
                        return True
            
            # Fallback: chercher toute voix contenant "fr" ou "French"
            for voice in voices:
                if ('fr' in voice.id.lower() or 
                    'french' in voice.name.lower() or
                    'français' in voice.name.lower()):
                    self.tts_engine.setProperty('voice', voice.id)
                    self.logger.info(f"✅ Voix française trouvée: {voice.name}")
                    return True
            
            # Dernière option: lister toutes les voix pour debug
            self.logger.warning("❌ Aucune voix française trouvée")
            self.logger.info("Voix disponibles:")
            for i, voice in enumerate(voices[:5]):  # Montrer 5 premières
                self.logger.info(f"  {i}: {voice.name} ({voice.id})")
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Erreur configuration voix française: {e}")
            return False
    
    def configure_french_speech_params(self):
        """Configure les paramètres optimaux pour le français"""
        try:
            # Vitesse adaptée au français (plus lent que l'anglais)
            self.tts_engine.setProperty('rate', 160)  # Plus naturel
            
            # Volume optimal
            self.tts_engine.setProperty('volume', 0.8)
            
            self.logger.info("✅ Paramètres vocaux français configurés")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur paramètres français: {e}")
            return False
    
    def test_french_speech(self):
        """Test de la synthèse vocale française"""
        test_phrases = [
            "Bonjour ! Je suis Gideon, votre assistant français.",
            "J'espère que ma voix française vous convient.",
            "Je peux maintenant vous parler en français."
        ]
        
        for phrase in test_phrases:
            try:
                self.logger.info(f"🔊 Test: {phrase}")
                self.tts_engine.say(phrase)
                self.tts_engine.runAndWait()
                time.sleep(0.5)  # Pause entre phrases
            except Exception as e:
                self.logger.error(f"❌ Erreur test vocal: {e}")
                return False
        
        return True


class EnhancedAudioManager:
    """PRODUCTION Audio Manager with macOS optimizations - FRANÇAIS INTÉGRÉ"""
    
    def __init__(self):
        self.logger = logging.getLogger("AudioManagerPRO")
        self.config = AudioConfig()
        
        # Components
        self.recognizer = None
        self.microphone = None
        self.tts_engine = None
        self.french_voice_manager = None  # Nouveau gestionnaire français
        
        # State management
        self.is_calibrated = False
        self.last_calibration = 0
        self.consecutive_failures = 0
        
        # Statistiques
        self.stats = {
            'total_listens': 0,
            'successful_recognitions': 0,
            'failed_recognitions': 0,
            'wake_words_detected': 0,
            'last_calibration': 'Never',
            'consecutive_failures': 0
        }
        
        # Optimisations macOS
        self.macos_optimizer = MacOSAudioOptimizer()
        
        # Initialize
        self._initialize_components()
        
    def _initialize_components(self):
        """Initialise tous les composants audio français"""
        # Speech recognition optimisé
        if HAS_SPEECH_RECOGNITION:
            try:
                self.recognizer = sr.Recognizer()
                
                # Configuration française optimisée
                self.recognizer.energy_threshold = self.config.ENERGY_THRESHOLD
                self.recognizer.dynamic_energy_threshold = self.config.DYNAMIC_ENERGY_THRESHOLD
                self.recognizer.pause_threshold = self.config.PAUSE_THRESHOLD
                self.recognizer.phrase_threshold = 0.3  # Optimisé pour français
                
                # Microphone optimal
                self.microphone = self.macos_optimizer.get_optimal_microphone()
                
                if self.microphone:
                    # Auto-calibration initiale
                    self.auto_calibrate_microphone()
                    self.logger.info("✅ Speech recognition français initialisé")
                else:
                    self.logger.warning("⚠️ Microphone non disponible")
                    
            except Exception as e:
                self.logger.error(f"❌ Échec speech recognition: {e}")
                self.recognizer = None
                self.microphone = None
        
        # TTS français avec optimisations
        if HAS_TTS:
            try:
                self.tts_engine = pyttsx3.init()
                
                # Gestionnaire de voix françaises
                self.french_voice_manager = FrenchVoiceManager(self.tts_engine)
                
                # Configuration voix française
                voice_configured = self.french_voice_manager.configure_french_voice()
                if voice_configured:
                    self.french_voice_manager.configure_french_speech_params()
                    self.logger.info("✅ TTS français configuré avec voix française")
                else:
                    # Fallback configuration
                    self.tts_engine.setProperty('rate', 160)
                    self.tts_engine.setProperty('volume', 0.8)
                    self.logger.warning("⚠️ TTS configuré sans voix française spécifique")
                
            except Exception as e:
                self.logger.error(f"❌ Échec TTS français: {e}")
                self.tts_engine = None
                self.french_voice_manager = None
    
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
    
    def speak(self, text: str, force_french: bool = True) -> bool:
        """Synthèse vocale française optimisée"""
        if not self.tts_engine:
            self.logger.error("❌ TTS engine non disponible")
            return False
        
        try:
            # Traitement du texte pour le français
            if force_french and text:
                # Nettoyage du texte pour meilleure prononciation française
                processed_text = self._process_french_text(text)
            else:
                processed_text = text
            
            self.logger.info(f"🔊 Gideon dit (FR): {processed_text}")
            
            # Synthèse vocale
            self.tts_engine.say(processed_text)
            self.tts_engine.runAndWait()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur synthèse vocale française: {e}")
            return False
    
    def _process_french_text(self, text: str) -> str:
        """Améliore le texte pour la synthèse vocale française"""
        if not text:
            return text
        
        # Remplacements pour meilleure prononciation française
        replacements = {
            ' IA ': ' intelligence artificielle ',
            ' AI ': ' intelligence artificielle ',
            ' OK ': ' d\'accord ',
            ' email ': ' courriel ',
            ' emails ': ' courriels ',
            ' web ': ' ouèbe ',
            ' wifi ': ' wi-fi ',
            ' bluetooth ': ' bluetooth ',
            '°C': ' degrés Celsius',
            '°F': ' degrés Fahrenheit',
            ' USD ': ' dollars américains ',
            ' EUR ': ' euros ',
        }
        
        processed = text
        for old, new in replacements.items():
            processed = processed.replace(old, new)
        
        return processed
    
    def test_french_audio_complete(self) -> bool:
        """Test complet du système audio français"""
        self.logger.info("🇫🇷 Test Audio Français Complet")
        
        success = True
        
        # Test 1: Configuration voix française
        if self.french_voice_manager:
            voice_test = self.french_voice_manager.test_french_speech()
            if not voice_test:
                success = False
        else:
            self.logger.warning("⚠️ Gestionnaire voix française non disponible")
            success = False
        
        # Test 2: Reconnaissance vocale française
        if self.recognizer and self.microphone:
            self.logger.info("🎤 Test reconnaissance vocale française")
            self.logger.info("Dites quelque chose en français dans 3 secondes...")
            time.sleep(3)
            
            mic_test = self.test_microphone_french()
            if not mic_test:
                success = False
        else:
            self.logger.warning("⚠️ Reconnaissance vocale non disponible")
            success = False
        
        # Test 3: Synthèse de phrases françaises complexes
        test_phrases = [
            "Bonjour ! Je suis votre assistant Gideon.",
            "Je peux maintenant vous parler parfaitement en français.",
            "Ma reconnaissance vocale française fonctionne correctement.",
            "Voulez-vous tester d'autres fonctionnalités ?"
        ]
        
        for phrase in test_phrases:
            if not self.speak(phrase, force_french=True):
                success = False
                break
            time.sleep(1)  # Pause entre phrases
        
        if success:
            self.logger.info("✅ Test audio français complet RÉUSSI")
        else:
            self.logger.error("❌ Test audio français complet ÉCHOUÉ")
        
        return success
    
    def test_microphone_french(self) -> bool:
        """Test microphone spécifiquement pour le français"""
        if not self.recognizer or not self.microphone:
            return False
        
        try:
            with self.microphone as source:
                self.logger.info("🎤 Parlez en français maintenant...")
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=3)
            
            # Reconnaissance française
            text = self.recognizer.recognize_google(audio, language="fr-FR")
            self.logger.info(f"✅ Reconnu en français: '{text}'")
            
            # Confirmer par synthèse vocale
            confirmation = f"J'ai entendu: {text}"
            self.speak(confirmation, force_french=True)
            
            return True
            
        except sr.WaitTimeoutError:
            self.logger.warning("⏰ Timeout - aucune parole française détectée")
            return False
        except sr.UnknownValueError:
            self.logger.warning("❓ Parole française non comprise")
            return False
        except Exception as e:
            self.logger.error(f"❌ Erreur test micro français: {e}")
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

# Instance globale corrigée pour le français
audio_manager = EnhancedAudioManager() 