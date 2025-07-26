#!/usr/bin/env python3
"""
Jarvis/Gideon AI Assistant - Main Application  
100% LOCAL AI ASSISTANT avec Ollama - VERSION CORRIGÉE
"""

import sys
import signal
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Check for PyQt6 availability
try:
    from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, 
                                 QLabel, QPushButton, QTextEdit, QLineEdit)
    from PyQt6.QtCore import Qt, QTimer
    from PyQt6.QtGui import QFont
    PYQT6_AVAILABLE = True
except ImportError:
    PYQT6_AVAILABLE = False
    print("⚠️ PyQt6 non disponible - Mode console uniquement")

# Core imports with error handling - IMPORT DIRECT
try:
    from core.logger import GideonLogger
    LOGGER_AVAILABLE = True
except ImportError:
    LOGGER_AVAILABLE = False
    print("⚠️ Logger non disponible")

try:
    from core.assistant_core_production import AssistantCore
    ASSISTANT_CORE_AVAILABLE = True
except ImportError as e:
    ASSISTANT_CORE_AVAILABLE = False
    print(f"❌ AssistantCore non disponible: {e}")

try:
    from core.memory_monitor import MemoryMonitor
    MEMORY_MONITOR_AVAILABLE = True
except ImportError:
    MEMORY_MONITOR_AVAILABLE = False
    print("⚠️ Memory Monitor non disponible (psutil manquant)")

try:
    from core.audio_manager_optimized import AudioManager
    AUDIO_MANAGER_AVAILABLE = True
except ImportError:
    AUDIO_MANAGER_AVAILABLE = False
    print("⚠️ Audio Manager non disponible")


class SimpleLogger:
    """Logger simple en cas d'échec du logger principal"""
    def info(self, msg): print(f"ℹ️ {msg}")
    def error(self, msg): print(f"❌ {msg}")
    def debug(self, msg): print(f"🔧 {msg}")


class SimpleJarvisApp:
    """Application Jarvis avec Ollama"""
    
    def __init__(self):
        # Logger
        if LOGGER_AVAILABLE:
            self.logger = GideonLogger("JarvisApp")
        else:
            self.logger = SimpleLogger()
            
        self.running = False
        self.audio_manager = None
        self.assistant_core = None
        self.memory_monitor = None
        
        self.logger.info("🤖 Jarvis App initialisé (100% LOCAL avec Ollama)")
    
    def test_ollama_connection(self):
        """Test rapide de connexion Ollama"""
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            if response.status_code == 200:
                models = response.json().get("models", [])
                self.logger.info(f"✅ Ollama disponible avec {len(models)} modèles")
                return True
            else:
                self.logger.error("❌ Ollama inaccessible")
                return False
        except Exception as e:
            self.logger.error(f"❌ Ollama test échoué: {e}")
            return False
    
    def initialize_core_systems(self):
        """Initialise les systèmes core disponibles"""
        try:
            # Test Ollama d'abord
            ollama_ok = self.test_ollama_connection()
            if not ollama_ok:
                self.logger.error("❌ Ollama non disponible - mode fallback")
            
            # Memory monitor (optionnel)
            if MEMORY_MONITOR_AVAILABLE:
                try:
                    self.memory_monitor = MemoryMonitor()
                    self.memory_monitor.start_monitoring()
                    self.logger.info("✅ Memory monitor démarré")
                except Exception as e:
                    self.logger.error(f"⚠️ Memory monitor: {e}")
            
            # Audio manager (optionnel)
            if AUDIO_MANAGER_AVAILABLE:
                try:
                    self.audio_manager = AudioManager()
                    self.logger.info("✅ Audio manager initialisé")
                except Exception as e:
                    self.logger.error(f"⚠️ Audio manager: {e}")
            
            # Assistant core (CRITIQUE)
            if ASSISTANT_CORE_AVAILABLE:
                try:
                    self.assistant_core = AssistantCore()
                    self.logger.info("✅ Assistant core avec Ollama")
                except Exception as e:
                    self.logger.error(f"❌ Assistant core: {e}")
                    return False
            else:
                self.logger.error("❌ Assistant core non disponible")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur initialisation: {e}")
            return False
    
    def start_cli_mode(self):
        """Mode CLI avec Ollama"""
        print("""
╔══════════════════════════════════════════════════════════════╗
║            🤖 JARVIS AI ASSISTANT - OLLAMA LOCAL             ║
║                     Version Corrigée                         ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        self.logger.info("🖥️ Démarrage mode CLI avec Ollama")
        
        if not self.initialize_core_systems():
            print("❌ Échec initialisation")
            print("💡 Vérifiez qu'Ollama fonctionne: ollama serve")
            return False
        
        print("✅ Jarvis est prêt avec Ollama!")
        print("💬 Tapez votre message, 'help' pour l'aide, 'quit' pour quitter")
        print("🔧 Tapez 'test' pour tester Ollama directement")
        
        # CLI loop
        try:
            while True:
                user_input = input("\n🤖 Vous: ").strip()
                
                if not user_input:
                    continue
                    
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("👋 Au revoir!")
                    break
                    
                if user_input.lower() == 'help':
                    self.show_help()
                    continue
                    
                if user_input.lower() == 'status':
                    self.show_status()
                    continue
                    
                if user_input.lower() == 'test':
                    self.test_ollama_direct()
                    continue
                
                # Process with assistant core
                self.process_user_input(user_input)
                
        except KeyboardInterrupt:
            print("\n👋 Arrêt sur interruption clavier")
        except Exception as e:
            self.logger.error(f"❌ Erreur CLI: {e}")
            print(f"❌ Erreur: {e}")
        
        self.cleanup()
        return True
    
    def test_ollama_direct(self):
        """Test direct Ollama"""
        print("🔧 Test direct Ollama...")
        try:
            import requests
            
            url = "http://localhost:11434/api/generate"
            data = {
                "model": "mistral:7b",
                "prompt": "Say hello briefly",
                "stream": False
            }
            
            print("📡 Envoi requête à Ollama...")
            response = requests.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                ollama_response = result.get("response", "")
                print(f"✅ Ollama répond: {ollama_response}")
            else:
                print(f"❌ Ollama erreur HTTP: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Test Ollama échoué: {e}")
    
    def process_user_input(self, user_input):
        """Traite l'entrée utilisateur avec Ollama"""
        try:
            if self.assistant_core:
                print("🤖 Traitement avec Ollama...")
                
                result = self.assistant_core.generate_ai_response(user_input)
                
                if result['success']:
                    response = result['response']
                    method = result.get('method', 'unknown')
                    response_time = result.get('response_time', 0)
                    
                    print(f"🤖 Jarvis ({method}, {response_time:.1f}s): {response}")
                    
                    # TTS si disponible
                    if self.audio_manager and len(response) < 200:
                        try:
                            self.audio_manager.speak(response)
                        except Exception as e:
                            self.logger.debug(f"TTS: {e}")
                else:
                    print(f"❌ Erreur: {result.get('error', 'Erreur inconnue')}")
            else:
                print("🤖 Jarvis: Assistant core non disponible")
                
        except Exception as e:
            self.logger.error(f"❌ Erreur traitement: {e}")
            print(f"❌ Erreur traitement: {e}")
    
    def show_help(self):
        """Affiche l'aide"""
        print("""
🤖 COMMANDES JARVIS OLLAMA:
- Tapez votre question ou commande naturellement
- 'status' - Affiche le statut des systèmes
- 'test' - Test direct d'Ollama
- 'help' - Affiche cette aide
- 'quit' - Quitte l'application

EXEMPLES:
- "Hello Jarvis"
- "What time is it?"
- "Tell me about AI"

ℹ️ Jarvis utilise Ollama (mistral:7b) pour des réponses
        """)
    
    def show_status(self):
        """Affiche le statut des systèmes"""
        print("\n📊 STATUT DES SYSTÈMES:")
        
        # Test Ollama en temps réel
        ollama_ok = self.test_ollama_connection()
        
        status_ok = "✅ Disponible"
        status_ko = "❌ Non disponible"
        
        print(f"🧠 Ollama Local: {status_ok if ollama_ok else status_ko}")
        print(f"🧠 Assistant Core: {status_ok if ASSISTANT_CORE_AVAILABLE else status_ko}")
        print(f"🎤 Audio: {status_ok if self.audio_manager else status_ko}")
        print(f"📊 Monitor: {status_ok if MEMORY_MONITOR_AVAILABLE else status_ko}")
        
        if self.memory_monitor:
            try:
                memory_info = self.memory_monitor.get_current_memory()
                if memory_info:
                    print(f"💾 Mémoire: {memory_info.rss_mb:.1f}MB")
            except Exception:
                print("💾 Mémoire: Info non disponible")
                
        # Stats assistant
        if self.assistant_core and hasattr(self.assistant_core, 'stats'):
            stats = self.assistant_core.stats
            print(f"📈 Requêtes: {stats['total_requests']}")
            print(f"📈 Ollama: {stats['ollama_responses']}")
            print(f"📈 Fallbacks: {stats['fallback_responses']}")
    
    def start_gui_mode(self):
        """Mode GUI simple"""
        if not PYQT6_AVAILABLE:
            print("❌ PyQt6 non disponible, passage en mode CLI")
            return self.start_cli_mode()
        
        try:
            app = QApplication(sys.argv)
            app.setApplicationName("Jarvis AI Assistant - Ollama")
            
            window = self.create_main_window()
            window.show()
            
            self.logger.info("🖥️ GUI démarré avec Ollama")
            return app.exec()
            
        except Exception as e:
            self.logger.error(f"❌ Erreur GUI: {e}")
            print(f"❌ Erreur GUI: {e}, passage en mode CLI")
            return self.start_cli_mode()
    
    def create_main_window(self):
        """Fenêtre principale avec chat Ollama"""
        window = QWidget()
        window.setWindowTitle("🤖 Jarvis AI Assistant - Ollama Local")
        window.setGeometry(200, 200, 800, 600)
        
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("🤖 JARVIS AI ASSISTANT - OLLAMA LOCAL")
        header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Status
        self.status_label = QLabel("Initialisation...")
        layout.addWidget(self.status_label)
        
        # Chat area
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setFont(QFont("Consolas", 10))
        layout.addWidget(self.chat_area)
        
        # Input area
        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("Tapez votre message ici...")
        self.input_line.returnPressed.connect(self.gui_process_input)
        layout.addWidget(self.input_line)
        
        # Send button
        send_btn = QPushButton("🚀 Envoyer")
        send_btn.clicked.connect(self.gui_process_input)
        layout.addWidget(send_btn)
        
        window.setLayout(layout)
        
        # Auto initialize
        QTimer.singleShot(500, self.gui_start_jarvis)
        
        return window
    
    def gui_start_jarvis(self):
        """Démarre Jarvis GUI"""
        try:
            self.status_label.setText("🚀 Démarrage...")
            self.chat_area.append("🤖 Initialisation de Jarvis avec Ollama...")
            
            if self.initialize_core_systems():
                self.status_label.setText("✅ Jarvis prêt avec Ollama!")
                self.chat_area.append("✅ Jarvis est prêt! Tapez votre message ci-dessous.")
                self.logger.info("✅ Jarvis démarré avec succès")
            else:
                self.status_label.setText("❌ Erreur de démarrage")
                self.chat_area.append("❌ Erreur. Vérifiez qu'Ollama fonctionne.")
                
        except Exception as e:
            self.status_label.setText(f"❌ Erreur: {e}")
            self.chat_area.append(f"❌ Erreur: {e}")
            self.logger.error(f"❌ Erreur démarrage GUI: {e}")
    
    def gui_process_input(self):
        """Traite input GUI"""
        user_input = self.input_line.text().strip()
        if not user_input:
            return
            
        # Affiche input
        self.chat_area.append(f"\n🤖 Vous: {user_input}")
        self.input_line.clear()
        
        # Traite commande
        try:
            if self.assistant_core:
                self.chat_area.append("🤖 Traitement avec Ollama...")
                
                result = self.assistant_core.generate_ai_response(user_input)
                
                if result['success']:
                    response = result['response']
                    method = result.get('method', 'unknown')
                    response_time = result.get('response_time', 0)
                    
                    self.chat_area.append(f"🤖 Jarvis ({method}, {response_time:.1f}s): {response}")
                else:
                    self.chat_area.append(f"❌ Erreur: {result.get('error', 'Erreur inconnue')}")
            else:
                self.chat_area.append("❌ Assistant core non disponible")
                
        except Exception as e:
            self.chat_area.append(f"❌ Erreur: {e}")
            self.logger.error(f"❌ Erreur GUI: {e}")
        
        # Scroll vers le bas
        self.chat_area.verticalScrollBar().setValue(
            self.chat_area.verticalScrollBar().maximum()
        )
    
    def cleanup(self):
        """Nettoyage des ressources"""
        try:
            if self.memory_monitor:
                self.memory_monitor.stop_monitoring()
            
            if self.audio_manager:
                self.audio_manager.cleanup()
                
            self.logger.info("🧹 Nettoyage terminé")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur nettoyage: {e}")


def main():
    """Point d'entrée principal"""
    print("🚀 Démarrage Jarvis AI Assistant avec Ollama...")
    
    # Signal handlers
    def signal_handler(signum, frame):
        print("\n📡 Signal d'arrêt reçu...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create app
    jarvis_app = SimpleJarvisApp()
    
    # Check arguments
    if len(sys.argv) > 1 and sys.argv[1] == '--cli':
        # Force CLI mode
        return jarvis_app.start_cli_mode()
    else:
        # Try GUI, fallback to CLI
        return jarvis_app.start_gui_mode()


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code or 0)
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        sys.exit(1) 