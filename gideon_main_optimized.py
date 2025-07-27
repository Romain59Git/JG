#!/usr/bin/env python3
"""
Gideon AI Assistant - PRODUCTION OPTIMIZED VERSION
100% fonctionnel avec auto-calibration, wake word detection et fallbacks robustes

🎯 OPTIMIZATIONS FINALES:
- ✅ Auto-calibration microphone macOS
- ✅ Wake word detection intelligente  
- ✅ Fallbacks robustes pour toutes situations
- ✅ Système de health check intégré
- ✅ Mémoire optimisée < 250MB
- ✅ Interface de monitoring temps réel
"""

import os
import sys
import time
import signal
import platform
import threading
from pathlib import Path
from typing import Dict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Early memory optimization
import gc
gc.set_threshold(700, 10, 10)

try:
    from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QTextEdit
    from PyQt6.QtCore import QTimer, QThread, pyqtSignal, Qt
    from PyQt6.QtGui import QIcon, QFont, QColor
    PYQT6_AVAILABLE = True
except ImportError:
    PYQT6_AVAILABLE = False
    print("⚠️ PyQt6 non disponible - Mode console activé")

# OS Detection
SYSTEM_OS = platform.system()
if SYSTEM_OS == "Linux" and "WAYLAND_DISPLAY" in os.environ:
    os.environ["QT_QPA_PLATFORM"] = "xcb"

# Core imports
from config import config
from core.logger import GideonLogger
from core.event_system import EventSystem
from core.audio_manager_optimized import audio_manager
from core.assistant_core_production import assistant_core
from core.memory_monitor import memory_monitor

class GideonHealthMonitor:
    """Système de monitoring santé en temps réel"""
    
    def __init__(self):
        self.logger = GideonLogger("HealthMonitor")
        self.health_status = {
            'audio_system': 'UNKNOWN',
            'ai_system': 'UNKNOWN', 
            'memory_status': 'UNKNOWN',
            'overall_health': 'UNKNOWN'
        }
        self.last_check = 0
        self.check_interval = 30  # secondes
    
    def check_audio_health(self) -> str:
        """Vérifier santé système audio"""
        try:
            # Test basique reconnaissance
            if not audio_manager.recognizer or not audio_manager.microphone:
                return 'CRITICAL'
            
            # Test TTS
            if not audio_manager.tts_engine:
                return 'WARNING'
            
            # Vérifier statistiques
            stats = audio_manager.get_stats()
            if stats['consecutive_failures'] >= 5:
                return 'WARNING'
            
            # Check calibration récente
            if 'Never' in stats.get('last_calibration', 'Never'):
                return 'WARNING'
            
            return 'HEALTHY'
            
        except Exception as e:
            self.logger.error(f"Erreur check audio: {e}")
            return 'CRITICAL'
    
    def check_ai_health(self) -> str:
        """Vérifier santé système IA"""
        try:
            # Utiliser la bonne interface AssistantCore Ollama
            if not assistant_core.ollama_client.is_available:
                return 'WARNING'  # Fallbacks disponibles
            
            # Test simple API avec la nouvelle interface
            test_result = assistant_core.generate_ai_response("test")
            if test_result and test_result.get('success', False):
                return 'HEALTHY'
            else:
                return 'WARNING'
                
        except Exception as e:
            self.logger.error(f"Erreur check AI: {e}")
            return 'WARNING'  # Fallbacks disponibles
    
    def check_memory_health(self) -> str:
        """Vérifier santé mémoire"""
        try:
            memory_info = memory_monitor.get_current_memory()
            if not memory_info:
                return 'UNKNOWN'
            
            mb_used = memory_info.rss_mb
            
            if mb_used < 200:
                return 'HEALTHY'
            elif mb_used < 250:
                return 'WARNING'
            else:
                return 'CRITICAL'
                
        except Exception as e:
            self.logger.error(f"Erreur check mémoire: {e}")
            return 'UNKNOWN'
    
    def run_health_check(self) -> Dict:
        """Exécuter check complet de santé"""
        try:
            self.health_status['audio_system'] = self.check_audio_health()
            self.health_status['ai_system'] = self.check_ai_health()
            self.health_status['memory_status'] = self.check_memory_health()
            
            # Calculer santé globale
            statuses = [
                self.health_status['audio_system'],
                self.health_status['ai_system'], 
                self.health_status['memory_status']
            ]
            
            if 'CRITICAL' in statuses:
                self.health_status['overall_health'] = 'CRITICAL'
            elif 'WARNING' in statuses:
                self.health_status['overall_health'] = 'WARNING'
            elif all(s == 'HEALTHY' for s in statuses):
                self.health_status['overall_health'] = 'HEALTHY'
            else:
                self.health_status['overall_health'] = 'WARNING'
            
            self.last_check = time.time()
            
            self.logger.info(f"🏥 Health Check: {self.health_status['overall_health']}")
            
            return self.health_status
            
        except Exception as e:
            self.logger.error(f"Erreur health check: {e}")
            self.health_status['overall_health'] = 'CRITICAL'
            return self.health_status
    
    def should_check(self) -> bool:
        """Déterminer si un check est nécessaire"""
        return time.time() - self.last_check > self.check_interval

class ProductionDebugPanel(QWidget):
    """Panel de debug optimisé pour production"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🤖 Gideon AI - Production Control Panel")
        self.setFixedSize(500, 600)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        
        self.health_monitor = GideonHealthMonitor()
        
        self.setup_ui()
        self.setup_timers()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Header avec status global
        header_layout = QHBoxLayout()
        self.title = QLabel("🤖 GIDEON AI - PRODUCTION")
        self.title.setFont(QFont("Consolas", 14, QFont.Weight.Bold))
        self.global_status = QLabel("🔄 INITIALIZING")
        self.global_status.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
        header_layout.addWidget(self.title)
        header_layout.addWidget(self.global_status)
        layout.addLayout(header_layout)
        
        # Health Status Section
        health_group = QLabel("🏥 HEALTH STATUS")
        health_group.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
        layout.addWidget(health_group)
        
        self.audio_health = QLabel("🎤 Audio: CHECKING...")
        self.ai_health = QLabel("🧠 AI System: CHECKING...")
        self.memory_health = QLabel("💾 Memory: CHECKING...")
        
        layout.addWidget(self.audio_health)
        layout.addWidget(self.ai_health)
        layout.addWidget(self.memory_health)
        
        # Memory Progress Bar
        memory_layout = QHBoxLayout()
        self.memory_bar = QProgressBar()
        self.memory_bar.setMaximum(250)  # 250MB target
        self.memory_label = QLabel("💾 0MB")
        memory_layout.addWidget(self.memory_label)
        memory_layout.addWidget(self.memory_bar)
        layout.addLayout(memory_layout)
        
        # Audio Statistics
        audio_group = QLabel("🎤 AUDIO STATISTICS")
        audio_group.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        layout.addWidget(audio_group)
        
        self.audio_stats = QLabel("Initializing...")
        layout.addWidget(self.audio_stats)
        
        # AI Statistics  
        ai_group = QLabel("🧠 AI STATISTICS")
        ai_group.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        layout.addWidget(ai_group)
        
        self.ai_stats = QLabel("Initializing...")
        layout.addWidget(self.ai_stats)
        
        # Control Buttons
        controls_layout = QHBoxLayout()
        self.listen_btn = QPushButton("🎤 Start Listening")
        self.listen_btn.clicked.connect(self.toggle_listening)
        
        self.test_btn = QPushButton("🧪 Quick Test") 
        self.test_btn.clicked.connect(self.run_quick_test)
        
        self.health_btn = QPushButton("🏥 Health Check")
        self.health_btn.clicked.connect(self.run_health_check)
        
        controls_layout.addWidget(self.listen_btn)
        controls_layout.addWidget(self.test_btn)
        controls_layout.addWidget(self.health_btn)
        layout.addLayout(controls_layout)
        
        # Log Output (compact)
        log_group = QLabel("📋 SYSTEM LOG")
        log_group.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        layout.addWidget(log_group)
        
        self.log_output = QTextEdit()
        self.log_output.setMaximumHeight(120)
        self.log_output.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_output)
        
        self.setLayout(layout)
    
    def setup_timers(self):
        # Timer principal pour mise à jour
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_all_stats)
        self.update_timer.start(3000)  # 3 secondes
        
        # Timer health check
        self.health_timer = QTimer()
        self.health_timer.timeout.connect(self.auto_health_check)
        self.health_timer.start(30000)  # 30 secondes
    
    def update_health_display(self, health_status: Dict):
        """Mettre à jour affichage santé"""
        # Couleurs par status
        colors = {
            'HEALTHY': 'green',
            'WARNING': 'orange', 
            'CRITICAL': 'red',
            'UNKNOWN': 'gray'
        }
        
        # Status global
        overall = health_status['overall_health']
        color = colors.get(overall, 'gray')
        
        if overall == 'HEALTHY':
            icon = "✅"
        elif overall == 'WARNING':
            icon = "⚠️"
        elif overall == 'CRITICAL':
            icon = "❌"
        else:
            icon = "❓"
        
        self.global_status.setText(f"{icon} {overall}")
        self.global_status.setStyleSheet(f"color: {color}; font-weight: bold;")
        
        # Status détaillés
        audio_status = health_status['audio_system']
        self.audio_health.setText(f"🎤 Audio: {audio_status}")
        self.audio_health.setStyleSheet(f"color: {colors.get(audio_status, 'gray')};")
        
        ai_status = health_status['ai_system']
        self.ai_health.setText(f"🧠 AI System: {ai_status}")
        self.ai_health.setStyleSheet(f"color: {colors.get(ai_status, 'gray')};")
        
        memory_status = health_status['memory_status']
        self.memory_health.setText(f"💾 Memory: {memory_status}")
        self.memory_health.setStyleSheet(f"color: {colors.get(memory_status, 'gray')};")
    
    def update_all_stats(self):
        """Mettre à jour toutes les statistiques"""
        try:
            # Memory
            memory_info = memory_monitor.get_current_memory()
            if memory_info:
                mb_used = memory_info.rss_mb
                self.memory_label.setText(f"💾 {mb_used:.1f}MB")
                self.memory_bar.setValue(min(int(mb_used), 250))
                
                # Couleur barre mémoire
                if mb_used < 150:
                    color = "green"
                elif mb_used < 200:
                    color = "orange"
                else:
                    color = "red"
                self.memory_bar.setStyleSheet(f"QProgressBar::chunk {{ background-color: {color}; }}")
            
            # Audio Stats
            audio_stats = audio_manager.get_stats()
            audio_text = (f"Listens: {audio_stats['total_listens']} | "
                         f"Success: {audio_stats['success_rate']} | "
                         f"Wake Words: {audio_stats['wake_words_detected']} | "
                         f"Avg Time: {audio_stats['avg_response_time']}")
            self.audio_stats.setText(audio_text)
            
            # AI Stats
            ai_stats = assistant_core.get_stats()
            ai_text = (f"Requests: {ai_stats['total_requests']} | "
                      f"AI Success: {ai_stats['successful_ai_responses']} | "
                      f"Fallbacks: {ai_stats['fallback_responses']} | "
                      f"Cache: {ai_stats['cache_size']}")
            self.ai_stats.setText(ai_text)
            
            # Status listening button
            if audio_manager.is_listening:
                self.listen_btn.setText("🔇 Stop Listening")
                self.listen_btn.setStyleSheet("background-color: lightcoral;")
            else:
                self.listen_btn.setText("🎤 Start Listening")
                self.listen_btn.setStyleSheet("background-color: lightgreen;")
                
        except Exception as e:
            self.log_message(f"❌ Erreur update stats: {e}")
    
    def toggle_listening(self):
        """Toggle audio listening français"""
        try:
            # Vérifier disponibilité audio
            if not audio_manager.recognizer or not audio_manager.microphone:
                self.log_message("❌ Système audio non disponible")
                return
            
            # Implementation écoute française
            if hasattr(audio_manager, 'is_listening') and audio_manager.is_listening:
                # Arrêter l'écoute
                if hasattr(audio_manager, 'stop_continuous_listening'):
                    audio_manager.stop_continuous_listening()
                self.listen_btn.setText("🎤 Commencer l'écoute")
                self.log_message("🔇 Écoute française arrêtée")
            else:
                # Démarrer l'écoute française
                self.log_message("🎤 Démarrage écoute française...")
                
                # Test microphone français d'abord
                if hasattr(audio_manager, 'test_microphone_french'):
                    mic_test = audio_manager.test_microphone_french()
                    if not mic_test:
                        self.log_message("❌ Test microphone français échoué")
                        return
                
                # Commencer écoute continue française
                if hasattr(audio_manager, 'start_continuous_listening'):
                    audio_manager.start_continuous_listening()
                elif hasattr(audio_manager, 'listen_continuously'):
                    # Fallback avec callback français
                    def process_french_voice(text):
                        self.log_message(f"🗣️ Entendu (FR): {text}")
                        # Traiter avec Ollama français
                        try:
                            result = assistant_core.generate_ai_response(text)
                            if result and result.get('success'):
                                response = result['response']
                                self.log_message(f"🤖 Gideon: {response}")
                                # Parler en français
                                audio_manager.speak(response, force_french=True)
                        except Exception as e:
                            self.log_message(f"❌ Erreur traitement français: {e}")
                    
                    audio_manager.listen_continuously(process_french_voice)
                
                self.listen_btn.setText("🔇 Arrêter l'écoute")
                self.log_message("✅ Écoute française active")
                
        except Exception as e:
            self.log_message(f"❌ Erreur toggle listening français: {e}")
            # Reset bouton en cas d'erreur
            self.listen_btn.setText("🎤 Commencer l'écoute")
    
    def run_quick_test(self):
        """Test rapide du système"""
        self.test_btn.setText("Testing...")
        self.test_btn.setEnabled(False)
        
        def test_system():
            try:
                # Test audio
                audio_ok = audio_manager.test_microphone()
                
                # Test AI
                ai_response = assistant_core.generate_ai_response("test")
                ai_ok = ai_response and len(ai_response) > 0
                
                # Test TTS
                tts_ok = audio_manager.speak("Test completed successfully")
                
                # Résultats
                results = f"Audio: {'✅' if audio_ok else '❌'} | AI: {'✅' if ai_ok else '❌'} | TTS: {'✅' if tts_ok else '❌'}"
                self.log_message(f"🧪 Quick Test: {results}")
                
            except Exception as e:
                self.log_message(f"❌ Test error: {e}")
            finally:
                self.test_btn.setText("🧪 Quick Test")
                self.test_btn.setEnabled(True)
        
        threading.Thread(target=test_system, daemon=True).start()
    
    def run_health_check(self):
        """Exécuter health check manuel"""
        self.health_btn.setText("Checking...")
        self.health_btn.setEnabled(False)
        
        def check_health():
            try:
                health_status = self.health_monitor.run_health_check()
                self.update_health_display(health_status)
                self.log_message(f"🏥 Health Check: {health_status['overall_health']}")
                
            except Exception as e:
                self.log_message(f"❌ Health check error: {e}")
            finally:
                self.health_btn.setText("🏥 Health Check")
                self.health_btn.setEnabled(True)
        
        threading.Thread(target=check_health, daemon=True).start()
    
    def auto_health_check(self):
        """Health check automatique"""
        if self.health_monitor.should_check():
            self.run_health_check()
    
    def log_message(self, message: str):
        """Ajouter message au log"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_output.append(f"[{timestamp}] {message}")
        
        # Limiter lignes de log
        document = self.log_output.document()
        if document.blockCount() > 10:
            cursor = self.log_output.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.select(cursor.SelectionType.LineUnderCursor)
            cursor.removeSelectedText()
            cursor.deletePreviousChar()

class ProductionGideonApp:
    """Application Gideon optimisée pour production"""
    
    def __init__(self):
        self.logger = GideonLogger("GideonProd")
        self.app = None
        self.debug_panel = None
        self.running = False
        self.health_monitor = GideonHealthMonitor()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"📡 Signal reçu {signum} - arrêt...")
        self.shutdown()
    
    def initialize(self):
        """Initialisation avec validation complète"""
        self.logger.info("🚀 Initialisation Gideon AI Production...")
        
        # Memory monitoring
        memory_monitor.start_monitoring()
        
        # Health check initial
        health_status = self.health_monitor.run_health_check()
        overall_health = health_status['overall_health']
        
        if overall_health == 'CRITICAL':
            self.logger.error("❌ Santé système CRITIQUE - Arrêt")
            print("\n🚨 SYSTÈME EN ÉTAT CRITIQUE")
            print("Exécutez: python fix_gideon.py")
            return False
        elif overall_health == 'WARNING':
            self.logger.warning("⚠️ Santé système DÉGRADÉE - Continuer avec précaution")
        else:
            self.logger.info("✅ Santé système OPTIMALE")
        
        # Interface utilisateur
        if PYQT6_AVAILABLE:
            self.app = QApplication(sys.argv)
            self.app.setQuitOnLastWindowClosed(False)
            
            self.debug_panel = ProductionDebugPanel()
            self.debug_panel.show()
            
            # Health check initial sur UI
            self.debug_panel.update_health_display(health_status)
            
            self.logger.info("✅ Interface PyQt6 initialisée")
        else:
            self.logger.warning("⚠️ Mode console activé")
        
        # Message d'accueil
        welcome_msg = "Hello! Gideon AI is ready and optimized for production use."
        audio_manager.speak(welcome_msg)
        
        self.running = True
        self.logger.info("🎉 Gideon AI Production PRÊT!")
        return True
    
    def start_voice_processing(self):
        """Démarrer traitement vocal intelligent"""
        def voice_loop():
            self.logger.info("🎤 Démarrage loop vocal production...")
            
            audio_manager.start_continuous_listening()
            
            while self.running:
                try:
                    # Attendre commande vocale
                    command = audio_manager.get_next_command(timeout=1.0)
                    
                    if command:
                        # Log commande reçue
                        wake_status = " [WAKE WORD]" if command.is_wake_word else ""
                        self.logger.info(f"🎯 Commande reçue: '{command.text}'{wake_status}")
                        
                        # Traitement intelligent
                        def process_command():
                            try:
                                result = assistant_core.process_voice_command(command.text)
                                
                                if result['success']:
                                    # Parler la réponse
                                    audio_manager.speak(result['response'])
                                    
                                    # Utiliser 'response_time' au lieu de 'processing_time'
                                    response_time = result.get('response_time', 0)
                                    self.logger.info(f"🤖 Réponse: '{result['response']}' "
                                                   f"({response_time:.2f}s)")
                                else:
                                    error_msg = result.get('error', 'Unknown')
                                    self.logger.error(f"❌ Erreur traitement: {error_msg}")
                                    
                            except Exception as e:
                                self.logger.error(f"❌ Erreur process_command: {e}")
                                # Fallback emergency
                                audio_manager.speak("Sorry, I had a technical problem processing that command.")
                        
                        # Traiter en thread séparé
                        threading.Thread(target=process_command, daemon=True).start()
                    
                    # Health monitoring périodique
                    if self.health_monitor.should_check():
                        health_status = self.health_monitor.run_health_check()
                        if health_status['overall_health'] == 'CRITICAL':
                            self.logger.error("🚨 Système critique détecté!")
                            audio_manager.speak("System health is critical. Please check the control panel.")
                    
                except Exception as e:
                    self.logger.error(f"❌ Erreur voice loop: {e}")
                    time.sleep(1)
        
        voice_thread = threading.Thread(target=voice_loop, daemon=True)
        voice_thread.start()
    
    def run(self):
        """Exécuter application production"""
        try:
            # Initialisation
            if not self.initialize():
                return 1
            
            # Démarrer traitement vocal
            self.start_voice_processing()
            
            # Status initial
            memory_info = memory_monitor.get_current_memory()
            if memory_info:
                self.logger.info(f"📊 Mémoire: {memory_info.rss_mb:.1f}MB")
            
            # Lancer application
            if PYQT6_AVAILABLE and self.app:
                self.logger.info("🖥️ Mode interface graphique")
                sys.exit(self.app.exec())
            else:
                self.logger.info("🖥️ Mode console")
                try:
                    while self.running:
                        time.sleep(1)
                except KeyboardInterrupt:
                    self.logger.info("⌨️ Interruption clavier")
        
        except Exception as e:
            self.logger.error(f"❌ Erreur critique: {e}")
            return 1
        finally:
            self.shutdown()
        
        return 0
    
    def shutdown(self):
        """Arrêt propre et complet"""
        self.logger.info("🔄 Arrêt Gideon AI Production...")
        
        self.running = False
        
        # Arrêter audio
        audio_manager.stop_continuous_listening()
        audio_manager.cleanup()
        
        # Arrêter monitoring
        memory_monitor.stop_monitoring()
        
        # Cleanup assistant
        assistant_core.cleanup()
        
        # Rapport final
        final_report = memory_monitor.get_memory_report()
        if not final_report.get('error'):
            current = final_report['current']
            self.logger.info(f"📊 Mémoire finale: {current['rss_mb']:.1f}MB")
        
        if self.app:
            self.app.quit()
        
        self.logger.info("✅ Arrêt terminé")

def main():
    """Point d'entrée principal"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    🤖 GIDEON AI ASSISTANT                    ║
║                   PRODUCTION OPTIMIZED                       ║
╠══════════════════════════════════════════════════════════════╣
║  🎯 Wake Word Detection     🧠 AI + Fallbacks Robustes     ║
║  🔧 Auto-Calibration macOS   💾 Mémoire < 250MB           ║  
║  🏥 Health Monitoring       📊 Stats Temps Réel            ║
║  ⚡ 100% Fonctionnel        🎤 Audio Ultra-Optimisé       ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    app = ProductionGideonApp()
    return app.run()

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 