#!/usr/bin/env python3
"""
Jarvis/Gideon AI Assistant - Main Application  
100% LOCAL AI ASSISTANT - Version Simplifiée Fonctionnelle
"""

import sys
import signal
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Check for PyQt6 availability
try:
    from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, 
                                 QLabel, QPushButton)
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont
    PYQT6_AVAILABLE = True
except ImportError:
    PYQT6_AVAILABLE = False
    print("⚠️ PyQt6 non disponible - Mode console uniquement")

# Core imports with error handling
try:
    from core.logger import GideonLogger
    from core.memory_monitor import MemoryMonitor
    from core.audio_manager_optimized import AudioManager
    from core.assistant_core_production import AssistantCore
except ImportError as e:
    print(f"❌ Erreur import core: {e}")
    sys.exit(1)

# Local modules availability check
try:
    import modules.llm_local
    LLM_AVAILABLE = True
except ImportError:
    print("⚠️ Module LLM local non disponible")
    LLM_AVAILABLE = False

try:
    import modules.memory_local
    MEMORY_AVAILABLE = True
except ImportError:
    print("⚠️ Module mémoire local non disponible") 
    MEMORY_AVAILABLE = False

try:
    import modules.vision_local
    VISION_AVAILABLE = True
except ImportError:
    print("⚠️ Module vision local non disponible")
    VISION_AVAILABLE = False

try:
    import modules.commands_local  # noqa: F401
    COMMANDS_AVAILABLE = True
except ImportError:
    print("⚠️ Module commandes local non disponible")
    COMMANDS_AVAILABLE = False


class SimpleJarvisApp:
    """Application Jarvis simplifiée et fonctionnelle"""
    
    def __init__(self):
        self.logger = GideonLogger("JarvisApp")
        self.running = False
        
        # Initialize available components
        self.audio_manager = None
        self.assistant_core = None
        self.memory_monitor = None
        
        self.logger.info("🤖 Jarvis App initialisé")
    
    def initialize_core_systems(self):
        """Initialise les systèmes core disponibles"""
        try:
            # Memory monitor
            self.memory_monitor = MemoryMonitor()
            self.memory_monitor.start_monitoring()
            self.logger.info("✅ Memory monitor démarré")
            
            # Audio manager
            self.audio_manager = AudioManager()
            self.logger.info("✅ Audio manager initialisé")
            
            # Assistant core
            self.assistant_core = AssistantCore()
            self.logger.info("✅ Assistant core initialisé")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur initialisation core: {e}")
            return False
    
    def start_cli_mode(self):
        """Démarre en mode CLI simple"""
        print("""
╔══════════════════════════════════════════════════════════════╗
║                🤖 JARVIS AI ASSISTANT                        ║
║                 Version Simplifiée                           ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        self.logger.info("🖥️ Démarrage mode CLI")
        
        if not self.initialize_core_systems():
            print("❌ Échec initialisation systèmes")
            return False
        
        print("✅ Jarvis est prêt!")
        print("💬 Tapez votre message, 'help' pour l'aide, 'quit' pour quitter")
        
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
                
                # Process with assistant core
                self.process_user_input(user_input)
                
        except KeyboardInterrupt:
            print("\n👋 Arrêt sur interruption clavier")
        except Exception as e:
            self.logger.error(f"❌ Erreur CLI: {e}")
            print(f"❌ Erreur: {e}")
        
        self.cleanup()
        return True
    
    def process_user_input(self, user_input):
        """Traite l'entrée utilisateur"""
        try:
            if self.assistant_core:
                result = self.assistant_core.process_voice_command(user_input)
                
                if result['success']:
                    response = result['response']
                    print(f"🤖 Jarvis: {response}")
                    
                    # TTS si disponible
                    if self.audio_manager:
                        try:
                            self.audio_manager.speak(response)
                        except Exception as e:
                            self.logger.debug(f"TTS non disponible: {e}")
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
🤖 COMMANDES JARVIS:
- Tapez votre question ou commande naturellement
- 'status' - Affiche le statut des systèmes
- 'help' - Affiche cette aide
- 'quit' - Quitte l'application

EXEMPLES:
- "Hello Jarvis"
- "What time is it?"
- "Tell me a joke"
        """)
    
    def show_status(self):
        """Affiche le statut des systèmes"""
        print("\n📊 STATUT DES SYSTÈMES:")
        
        status_available = "✅ Disponible"
        status_unavailable = "❌ Non disponible"
        
        print(f"🧠 LLM Local: {status_available if LLM_AVAILABLE else status_unavailable}")
        print(f"🗃️ Mémoire: {status_available if MEMORY_AVAILABLE else status_unavailable}")
        print(f"👁️ Vision: {status_available if VISION_AVAILABLE else status_unavailable}")
        print(f"⚙️ Commandes: {status_available if COMMANDS_AVAILABLE else status_unavailable}")
        print(f"🎤 Audio: {status_available if self.audio_manager else status_unavailable}")
        print(f"🧠 Assistant: {status_available if self.assistant_core else status_unavailable}")
        
        if self.memory_monitor:
            try:
                memory_info = self.memory_monitor.get_current_memory()
                if memory_info:
                    print(f"💾 Mémoire: {memory_info.rss_mb:.1f}MB")
            except Exception:
                print("💾 Mémoire: Info non disponible")
    
    def start_gui_mode(self):
        """Démarre en mode GUI simple"""
        if not PYQT6_AVAILABLE:
            print("❌ PyQt6 non disponible, passage en mode CLI")
            return self.start_cli_mode()
        
        try:
            app = QApplication(sys.argv)
            app.setApplicationName("Jarvis AI Assistant")
            
            window = self.create_main_window()
            window.show()
            
            self.logger.info("🖥️ GUI démarré")
            return app.exec()
            
        except Exception as e:
            self.logger.error(f"❌ Erreur GUI: {e}")
            print(f"❌ Erreur GUI: {e}, passage en mode CLI")
            return self.start_cli_mode()
    
    def create_main_window(self):
        """Crée la fenêtre principale simple"""
        window = QWidget()
        window.setWindowTitle("🤖 Jarvis AI Assistant")
        window.setGeometry(200, 200, 600, 400)
        
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("🤖 JARVIS AI ASSISTANT")
        header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Status
        self.status_label = QLabel("Initialisation...")
        layout.addWidget(self.status_label)
        
        # Start button
        start_btn = QPushButton("🚀 Démarrer Jarvis")
        start_btn.clicked.connect(self.gui_start_jarvis)
        layout.addWidget(start_btn)
        
        window.setLayout(layout)
        
        # Auto initialize
        self.gui_start_jarvis()
        
        return window
    
    def gui_start_jarvis(self):
        """Démarre Jarvis depuis l'interface GUI"""
        try:
            self.status_label.setText("🚀 Démarrage...")
            
            if self.initialize_core_systems():
                self.status_label.setText("✅ Jarvis est prêt!")
                self.logger.info("✅ Jarvis démarré avec succès")
            else:
                self.status_label.setText("❌ Erreur de démarrage")
                
        except Exception as e:
            self.status_label.setText(f"❌ Erreur: {e}")
            self.logger.error(f"❌ Erreur démarrage GUI: {e}")
    
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
    print("🚀 Démarrage Jarvis AI Assistant...")
    
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