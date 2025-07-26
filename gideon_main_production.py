#!/usr/bin/env python3
"""
Gideon AI Assistant - Main Production Application
Version finale avec résolution complète des 10 problèmes critiques

Nouvelles fonctionnalités:
- ✅ Détection automatique OS et adaptations (Problème #6)
- ✅ Fallbacks intelligents pour tous composants (Problème #9)
- ✅ Monitoring mémoire en temps réel (Problème #7)
- ✅ Tests de permissions automatiques (Problème #5)
- ✅ Interface adaptative selon capacités système
"""

import os
import sys
import time
import signal
import platform
from pathlib import Path

# Ajout du répertoire racine au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

try:
    from PyQt6.QtWidgets import QApplication, QSystemTrayIcon
    from PyQt6.QtCore import QTimer, QThread, pyqtSignal
    from PyQt6.QtGui import QIcon
    PYQT6_AVAILABLE = True
except ImportError:
    PYQT6_AVAILABLE = False
    print("⚠️ PyQt6 non disponible - Mode console activé")

# Détection et adaptation OS (Problème #6)
SYSTEM_OS = platform.system()
if SYSTEM_OS == "Linux" and "WAYLAND_DISPLAY" in os.environ:
    # Force X11 pour system tray Wayland
    os.environ["QT_QPA_PLATFORM"] = "xcb"
    print("🐧 Wayland détecté - Basculement vers X11 pour system tray")

from core.assistant_core_production import GideonCoreProduction
from core.event_system import EventSystem
from core.logger import GideonLogger
from config import config

# UI conditionnelle
if PYQT6_AVAILABLE:
    try:
        from ui.overlay import GideonOverlay
        from ui.audio_visualizer import AudioVisualizer
        UI_AVAILABLE = True
    except ImportError as e:
        UI_AVAILABLE = False
        print(f"⚠️ Interface UI non disponible: {e}")
else:
    UI_AVAILABLE = False

# Modules optionnels
try:
    from modules.smart_home import SmartHomeModule
    SMART_HOME_AVAILABLE = True
except ImportError:
    SMART_HOME_AVAILABLE = False

class SystemCompatibilityChecker:
    """Vérificateur de compatibilité système complet"""
    
    def __init__(self):
        self.logger = GideonLogger("CompatibilityChecker")
        self.system_info = {
            'os': platform.system(),
            'os_version': platform.release(),
            'architecture': platform.machine(),
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        }
    
    def run_full_check(self) -> dict:
        """Exécuter vérification complète de compatibilité"""
        self.logger.info("🔍 Vérification compatibilité système...")
        
        results = {
            'system_info': self.system_info,
            'compatibility': self._check_compatibility(),
            'performance': self._check_performance(),
            'permissions': self._check_permissions(),
            'recommendations': []
        }
        
        # Générer recommandations
        results['recommendations'] = self._generate_recommendations(results)
        
        # Logger résultats
        self._log_results(results)
        
        return results
    
    def _check_performance(self) -> dict:
        """Vérifier performance système"""
        import psutil
        
        performance = {
            'total_memory_gb': psutil.virtual_memory().total / (1024**3),
            'available_memory_gb': psutil.virtual_memory().available / (1024**3),
            'cpu_cores': psutil.cpu_count(),
            'cpu_usage_percent': psutil.cpu_percent(interval=1),
            'disk_space_gb': psutil.disk_usage('/').free / (1024**3) if platform.system() != 'Windows' else psutil.disk_usage('C:').free / (1024**3)
        }
        
        return performance
    
    def _check_compatibility(self) -> dict:
        """Vérifier compatibilité système"""
        compatibility = {
            'python_version': sys.version_info >= (3, 8),
            'openai_available': False,
            'audio_available': False,
            'speech_recognition_available': False,
            'tts_available': False,
            'opencv_available': False,
            'face_detection_available': False,
            'memory_sufficient': True
        }
        
        # Test imports
        try:
            from openai import OpenAI
            compatibility['openai_available'] = True
        except ImportError:
            pass
        
        try:
            import sounddevice as sd
            compatibility['audio_available'] = True
        except ImportError:
            pass
        
        try:
            import speech_recognition as sr
            compatibility['speech_recognition_available'] = True
        except ImportError:
            pass
        
        try:
            import pyttsx3
            compatibility['tts_available'] = True
        except ImportError:
            pass
        
        try:
            import cv2
            compatibility['opencv_available'] = True
        except ImportError:
            pass
        
        try:
            from mtcnn import MTCNN
            compatibility['face_detection_available'] = True
        except ImportError:
            pass
        
        # Test mémoire
        try:
            import psutil
            available_memory = psutil.virtual_memory().available
            compatibility['memory_sufficient'] = available_memory > 500 * 1024 * 1024  # 500MB
        except ImportError:
            pass
        
        return compatibility

    def _check_permissions(self) -> dict:
        """Vérifier permissions spécifiques à l'OS"""
        permissions = {
            'file_system': True,  # Supposé OK si script s'exécute
            'network': True,      # Supposé OK
            'microphone': False,
            'camera': False
        }
        
        # Test microphone basique
        try:
            if PYQT6_AVAILABLE:
                import sounddevice as sd
                devices = sd.query_devices()
                permissions['microphone'] = any(d['max_input_channels'] > 0 for d in devices)
        except:
            pass
        
        # Test caméra basique
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            permissions['camera'] = cap.isOpened()
            if cap.isOpened():
                cap.release()
        except:
            pass
        
        return permissions
    
    def _generate_recommendations(self, results: dict) -> list:
        """Générer recommandations d'amélioration"""
        recommendations = []
        
        compatibility = results['compatibility']
        performance = results['performance']
        permissions = results['permissions']
        
        # Recommandations dépendances
        if not compatibility['openai_available']:
            recommendations.append("Installer OpenAI: pip install openai>=1.0.0")
        
        if not compatibility['audio_available']:
            recommendations.append("Installer audio: pip install sounddevice soundfile")
        
        if not compatibility['face_detection_available']:
            recommendations.append("Installer détection faciale: pip install mtcnn tensorflow-cpu")
        
        # Recommandations performance
        if performance['available_memory_gb'] < 1.0:
            recommendations.append("Libérer de la mémoire RAM (minimum 1GB recommandé)")
        
        if performance['cpu_usage_percent'] > 80:
            recommendations.append("Réduire charge CPU pour performances optimales")
        
        # Recommandations permissions
        if not permissions['microphone']:
            if self.system_info['os'] == 'Darwin':
                recommendations.append("Autoriser microphone: System Preferences > Security & Privacy > Microphone")
            else:
                recommendations.append("Vérifier permissions microphone système")
        
        if not permissions['camera']:
            if self.system_info['os'] == 'Darwin':
                recommendations.append("Autoriser caméra: System Preferences > Security & Privacy > Camera")
            else:
                recommendations.append("Vérifier permissions caméra système")
        
        return recommendations
    
    def _log_results(self, results: dict):
        """Logger résultats de compatibilité"""
        self.logger.info("📊 Résultats compatibilité:")
        self.logger.info(f"  OS: {results['system_info']['os']} {results['system_info']['os_version']}")
        self.logger.info(f"  Python: {results['system_info']['python_version']}")
        self.logger.info(f"  Mémoire disponible: {results['performance']['available_memory_gb']:.1f}GB")
        
        # Compter composants OK
        ok_count = sum(1 for v in results['compatibility'].values() if v)
        total_count = len(results['compatibility'])
        self.logger.info(f"  Compatibilité: {ok_count}/{total_count} composants OK")
        
        if results['recommendations']:
            self.logger.info("💡 Recommandations:")
            for rec in results['recommendations']:
                self.logger.info(f"    • {rec}")

class GideonApplication:
    """Application principale Gideon avec gestion complète des erreurs"""
    
    def __init__(self):
        self.logger = GideonLogger("GideonApp")
        self.compatibility_checker = SystemCompatibilityChecker()
        
        # Composants système
        self.app = None
        self.gideon_core = None
        self.overlay = None
        self.tray_icon = None
        self.smart_home = None
        
        # État application
        self.running = False
        self.compatibility_results = None
        
        # Setup signal handlers pour arrêt propre
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Gestionnaire signaux pour arrêt propre"""
        self.logger.info(f"📡 Signal reçu: {signum}")
        self.shutdown()
    
    def initialize(self) -> bool:
        """Initialiser application avec vérifications complètes"""
        self.logger.info("🚀 Initialisation Gideon AI Assistant Production")
        
        # Vérification compatibilité système
        self.compatibility_results = self.compatibility_checker.run_full_check()
        
        # Afficher informations système
        self._print_startup_banner()
        
        # Initialiser PyQt6 si disponible
        if PYQT6_AVAILABLE:
            try:
                self.app = QApplication(sys.argv)
                self.app.setApplicationName("Gideon AI Assistant")
                self.app.setApplicationVersion("1.0.0")
                self.logger.info("✅ PyQt6 application initialisée")
            except Exception as e:
                self.logger.error(f"❌ Erreur initialisation PyQt6: {e}")
                return False
        
        # Initialiser core assistant
        try:
            self.gideon_core = GideonCoreProduction()
            self.logger.info("✅ Core assistant initialisé")
        except Exception as e:
            self.logger.error(f"❌ Erreur initialisation core: {e}")
            return False
        
        # Initialiser interface UI si disponible
        if UI_AVAILABLE and self.app:
            try:
                self.overlay = GideonOverlay(self.gideon_core)
                self.logger.info("✅ Interface overlay initialisée")
            except Exception as e:
                self.logger.warning(f"⚠️ Interface overlay non disponible: {e}")
        
        # Initialiser system tray si possible
        if self.app and QSystemTrayIcon.isSystemTrayAvailable():
            try:
                self._setup_system_tray()
                self.logger.info("✅ System tray configuré")
            except Exception as e:
                self.logger.warning(f"⚠️ System tray non disponible: {e}")
        
        # Initialiser modules optionnels
        if SMART_HOME_AVAILABLE:
            try:
                self.smart_home = SmartHomeModule()
                self.logger.info("✅ Module smart home initialisé")
            except Exception as e:
                self.logger.warning(f"⚠️ Smart home non disponible: {e}")
        
        # Démarrer tâches de fond
        self._start_background_tasks()
        
        self.logger.info("🎉 Gideon AI Assistant prêt !")
        return True
    
    def _print_startup_banner(self):
        """Afficher bannière de démarrage avec informations système"""
        print("\n" + "="*60)
        print("🤖 GIDEON AI ASSISTANT - PRODUCTION VERSION")
        print("="*60)
        
        # Informations système
        sys_info = self.compatibility_results['system_info']
        print(f"💻 Système: {sys_info['os']} {sys_info['os_version']} ({sys_info['architecture']})")
        print(f"🐍 Python: {sys_info['python_version']}")
        
        # Statut compatibilité
        compatibility = self.compatibility_results['compatibility']
        ok_count = sum(1 for v in compatibility.values() if v)
        total_count = len(compatibility)
        print(f"✅ Compatibilité: {ok_count}/{total_count} composants")
        
        # Performance
        perf = self.compatibility_results['performance']
        print(f"💾 Mémoire: {perf['available_memory_gb']:.1f}GB disponible")
        print(f"⚡ CPU: {perf['cpu_cores']} cœurs ({perf['cpu_usage_percent']:.1f}% usage)")
        
        # Recommandations importantes
        if self.compatibility_results['recommendations']:
            print("\n💡 RECOMMANDATIONS:")
            for rec in self.compatibility_results['recommendations'][:3]:  # Top 3
                print(f"  • {rec}")
        
        print("="*60 + "\n")
    
    def _setup_system_tray(self):
        """Configurer system tray avec menu contextuel"""
        self.tray_icon = QSystemTrayIcon(self.app)
        
        # Icône par défaut (à remplacer par icône personnalisée)
        icon = self.app.style().standardIcon(self.app.style().StandardPixmap.SP_ComputerIcon)
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip("Gideon AI Assistant")
        
        # Menu contextuel
        from PyQt6.QtWidgets import QMenu
        tray_menu = QMenu()
        
        # Actions menu
        show_action = tray_menu.addAction("Afficher Gideon")
        show_action.triggered.connect(self._show_overlay)
        
        status_action = tray_menu.addAction("Statut Système")
        status_action.triggered.connect(self._show_system_status)
        
        tray_menu.addSeparator()
        
        settings_action = tray_menu.addAction("Paramètres")
        settings_action.triggered.connect(self._show_settings)
        
        tray_menu.addSeparator()
        
        quit_action = tray_menu.addAction("Quitter")
        quit_action.triggered.connect(self.shutdown)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
    
    def _show_overlay(self):
        """Afficher interface overlay"""
        if self.overlay:
            self.overlay.show()
            self.overlay.raise_()
            self.overlay.activateWindow()
    
    def _show_system_status(self):
        """Afficher statut système"""
        if self.gideon_core:
            status = self.gideon_core.get_system_status()
            status_text = f"Gideon AI Assistant\n\n"
            status_text += f"OpenAI: {'✅' if status.openai else '❌'}\n"
            status_text += f"Audio: {'✅' if status.audio_input else '❌'}\n"
            status_text += f"Reconnaissance faciale: {'✅' if status.face_detection else '❌'}\n"
            status_text += f"Mémoire: {status.memory_usage_mb:.1f}MB\n"
            
            if self.app:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(None, "Statut Système", status_text)
            else:
                print(status_text)
    
    def _show_settings(self):
        """Afficher paramètres (placeholder)"""
        if self.app:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(None, "Paramètres", "Interface de paramètres à implémenter.")
        else:
            print("Interface de paramètres non disponible en mode console.")
    
    def _start_background_tasks(self):
        """Démarrer tâches de fond"""
        if self.gideon_core:
            # Monitoring mémoire périodique
            if self.app:
                self.memory_timer = QTimer()
                self.memory_timer.timeout.connect(self._check_memory_usage)
                self.memory_timer.start(30000)  # Toutes les 30 secondes
            
            # Démarrer écoute continue si audio disponible
            status = self.gideon_core.get_system_status()
            if status.get('speech_recognition_available', False):
                self.gideon_core.start_continuous_listening()
    
    def _check_memory_usage(self):
        """Vérification périodique de l'usage mémoire"""
        if self.gideon_core:
            memory_mb = self.gideon_core.memory_monitor.get_memory_usage()
            if memory_mb > 250:  # Seuil d'alerte
                self.logger.warning(f"🚨 Utilisation mémoire élevée: {memory_mb:.1f}MB")
                # Forcer nettoyage
                self.gideon_core.memory_monitor.force_garbage_collection()
    
    def run(self) -> int:
        """Boucle principale application"""
        if not self.initialize():
            self.logger.error("❌ Échec initialisation - Arrêt")
            return 1
        
        self.running = True
        
        try:
            if self.app:
                # Mode GUI
                self.logger.info("🖥️ Démarrage mode interface graphique")
                
                # Afficher overlay au démarrage si disponible
                if self.overlay:
                    self.overlay.show()
                
                # Authentification utilisateur
                if self.gideon_core:
                    self._perform_user_authentication()
                
                # Boucle principale PyQt6
                return self.app.exec()
            else:
                # Mode console
                self.logger.info("💻 Démarrage mode console")
                return self._run_console_mode()
                
        except KeyboardInterrupt:
            self.logger.info("⌨️ Interruption clavier - Arrêt")
            return 0
        except Exception as e:
            self.logger.error(f"❌ Erreur application: {e}")
            return 1
        finally:
            self.shutdown()
    
    def _perform_user_authentication(self):
        """Effectuer authentification utilisateur"""
        if self.gideon_core:
            try:
                self.gideon_core.speak("Bonjour ! Authentification en cours...")
                success = self.gideon_core.authenticate_user()
                
                if success:
                    self.gideon_core.speak("Authentification réussie. Je suis à votre service !")
                else:
                    self.gideon_core.speak("Authentification échouée. Mode invité activé.")
                    
            except Exception as e:
                self.logger.error(f"❌ Erreur authentification: {e}")
    
    def _run_console_mode(self) -> int:
        """Mode console interactif"""
        print("\n🤖 GIDEON AI ASSISTANT - MODE CONSOLE")
        print("Tapez 'aide' pour la liste des commandes, 'quit' pour quitter\n")
        
        # Authentification en mode console
        if self.gideon_core:
            self._perform_user_authentication()
        
        while self.running:
            try:
                user_input = input("🎯 Commande > ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', 'quitter']:
                    break
                
                elif user_input.lower() in ['aide', 'help']:
                    self._show_console_help()
                
                elif user_input.lower() in ['statut', 'status']:
                    self._show_console_status()
                
                else:
                    # Traiter comme commande IA
                    if self.gideon_core:
                        response = self.gideon_core.generate_ai_response(user_input)
                        print(f"🤖 Gideon: {response}\n")
                    else:
                        print("❌ Core assistant non disponible\n")
                
            except EOFError:
                break
            except Exception as e:
                self.logger.error(f"❌ Erreur console: {e}")
        
        return 0
    
    def _show_console_help(self):
        """Afficher aide mode console"""
        help_text = """
🤖 COMMANDES GIDEON CONSOLE:

  aide / help     - Afficher cette aide
  statut / status - Afficher statut système
  quit / exit     - Quitter Gideon
  
  Toute autre entrée sera traitée comme une question pour l'IA.
  
Exemples:
  > Quelle heure est-il ?
  > Ouvre VS Code
  > Quel temps fait-il ?
"""
        print(help_text)
    
    def _show_console_status(self):
        """Afficher statut en mode console"""
        if self.gideon_core:
            status = self.gideon_core.get_system_status()
            print(f"\n📊 STATUT SYSTÈME:")
            print(f"  OpenAI: {'✅ Actif' if status.openai else '❌ Inactif'}")
            print(f"  Audio Input: {'✅ Disponible' if status.audio_input else '❌ Indisponible'}")
            print(f"  Audio Output: {'✅ Disponible' if status.audio_output else '❌ Indisponible'}")
            print(f"  Reconnaissance vocale: {'✅ Active' if status.speech_recognition else '❌ Inactive'}")
            print(f"  Détection faciale: {'✅ Active' if status.face_detection else '❌ Inactive'}")
            print(f"  Mémoire utilisée: {status.memory_usage_mb:.1f}MB")
            print(f"  Authentifié: {'✅ Oui' if self.gideon_core.is_authenticated else '❌ Non'}")
            print()
        else:
            print("❌ Core assistant non initialisé")
    
    def shutdown(self):
        """Arrêt propre de l'application"""
        if not self.running:
            return
            
        self.logger.info("🔄 Arrêt Gideon AI Assistant...")
        self.running = False
        
        # Arrêter core assistant
        if self.gideon_core:
            self.gideon_core.shutdown()
        
        # Arrêter modules
        if self.smart_home:
            try:
                # Arrêt smart home si méthode disponible
                if hasattr(self.smart_home, 'shutdown'):
                    self.smart_home.shutdown()
            except:
                pass
        
        # Fermer interface
        if self.overlay:
            self.overlay.close()
        
        # Masquer system tray
        if self.tray_icon:
            self.tray_icon.hide()
        
        # Quitter application PyQt6
        if self.app:
            self.app.quit()
        
        self.logger.info("✅ Gideon AI Assistant arrêté proprement")

def main():
    """Point d'entrée principal"""
    app = GideonApplication()
    return app.run()

if __name__ == "__main__":
    sys.exit(main()) 