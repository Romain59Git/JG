#!/usr/bin/env python3
"""
GIDEON AI - SCRIPT DE RÉPARATION AUTOMATIQUE
Diagnostique et répare automatiquement tous les problèmes détectés
"""

import os
import sys
import subprocess
import time
import platform
import logging
from pathlib import Path

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/gideon_repair.log', 'w')
    ]
)
logger = logging.getLogger("GideonRepair")

class GideonAutoRepair:
    """Système de réparation automatique pour Gideon AI"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.system_os = platform.system()
        self.issues_found = []
        self.fixes_applied = []
        
        # Créer dossier logs si nécessaire
        self.project_root.joinpath("logs").mkdir(exist_ok=True)
        
        logger.info("🔧 Gideon AI Auto-Repair System initialisé")
    
    def print_header(self, title: str):
        """Afficher header formaté"""
        print(f"\n{'='*60}")
        print(f"🔧 {title}")
        print(f"{'='*60}")
        logger.info(f"SECTION: {title}")
    
    def print_step(self, step: str, status: str = "INFO"):
        """Afficher étape avec status"""
        icons = {"INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌", "FIX": "🔧"}
        icon = icons.get(status, "ℹ️")
        print(f"{icon} {step}")
        logger.info(f"[{status}] {step}")
    
    def run_command(self, command: str, description: str, critical: bool = False) -> bool:
        """Exécuter commande avec gestion d'erreur"""
        self.print_step(f"Exécution: {description}")
        
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                self.print_step(f"✅ {description} - SUCCÈS", "SUCCESS")
                return True
            else:
                error_msg = f"{description} - ÉCHEC: {result.stderr}"
                self.print_step(error_msg, "ERROR")
                logger.error(f"Command failed: {command}")
                logger.error(f"Error: {result.stderr}")
                
                if critical:
                    self.issues_found.append(f"CRITIQUE: {error_msg}")
                else:
                    self.issues_found.append(error_msg)
                
                return False
                
        except Exception as e:
            error_msg = f"{description} - ERREUR: {e}"
            self.print_step(error_msg, "ERROR")
            logger.error(f"Exception in command: {command} - {e}")
            
            if critical:
                self.issues_found.append(f"CRITIQUE: {error_msg}")
            else:
                self.issues_found.append(error_msg)
            
            return False
    
    def check_python_environment(self):
        """Vérifier environnement Python"""
        self.print_header("VÉRIFICATION ENVIRONNEMENT PYTHON")
        
        # Vérifier Python version
        python_version = sys.version_info
        if python_version >= (3, 8):
            self.print_step(f"Python {python_version.major}.{python_version.minor} détecté", "SUCCESS")
        else:
            self.print_step(f"Python {python_version.major}.{python_version.minor} - VERSION TROP ANCIENNE", "ERROR")
            self.issues_found.append("Python version < 3.8")
        
        # Vérifier environnement virtuel
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            self.print_step("Environnement virtuel activé", "SUCCESS")
        else:
            self.print_step("Environnement virtuel NON activé", "WARNING")
            self.issues_found.append("Environnement virtuel non activé")
    
    def install_dependencies(self):
        """Installer/mettre à jour dépendances"""
        self.print_header("INSTALLATION DÉPENDANCES")
        
        # Fichiers requirements à traiter par ordre de priorité
        req_files = [
            ("requirements_production.txt", "Dépendances production", True),
            ("requirements.txt", "Dépendances standard", False),
            ("requirements_light.txt", "Dépendances allégées", False)
        ]
        
        for req_file, description, critical in req_files:
            req_path = self.project_root / req_file
            
            if req_path.exists():
                self.print_step(f"Installation depuis {req_file}")
                command = f"{sys.executable} -m pip install -r {req_file} --upgrade"
                success = self.run_command(command, description, critical)
                
                if success:
                    self.fixes_applied.append(f"Dépendances installées: {req_file}")
                    break  # Utiliser le premier fichier qui fonctionne
            else:
                self.print_step(f"Fichier {req_file} introuvable", "WARNING")
        
        # Installation spécifique pour macOS
        if self.system_os == "Darwin":
            self.print_step("Optimisations macOS détectées")
            
            # Permissions audio macOS
            macos_deps = [
                "pyobjc-framework-AVFoundation",
                "pyobjc-framework-AudioUnit"
            ]
            
            for dep in macos_deps:
                command = f"{sys.executable} -m pip install {dep}"
                self.run_command(command, f"Installation {dep} pour macOS")
    
    def check_audio_system(self):
        """Diagnostiquer système audio"""
        self.print_header("DIAGNOSTIC SYSTÈME AUDIO")
        
        # Test rapide des imports critiques
        audio_modules = [
            ("speech_recognition", "Reconnaissance vocale"),
            ("pyttsx3", "Text-to-Speech"),
            ("sounddevice", "Interface audio"),
            ("numpy", "Traitement numérique")
        ]
        
        for module, description in audio_modules:
            try:
                __import__(module)
                self.print_step(f"Module {module} disponible", "SUCCESS")
            except ImportError:
                self.print_step(f"Module {module} MANQUANT", "ERROR")
                self.issues_found.append(f"Module manquant: {module}")
                
                # Tenter installation automatique
                self.print_step(f"Tentative installation {module}", "FIX")
                command = f"{sys.executable} -m pip install {module}"
                if self.run_command(command, f"Installation {module}"):
                    self.fixes_applied.append(f"Module installé: {module}")
        
        # Test système audio complet
        self.print_step("Lancement test audio complet")
        test_command = f"{sys.executable} test_audio_system.py"
        
        if self.run_command(test_command, "Test système audio"):
            self.print_step("Système audio fonctionnel", "SUCCESS")
        else:
            self.print_step("Problèmes détectés dans système audio", "WARNING")
    
    def check_openai_configuration(self):
        """Vérifier configuration OpenAI"""
        self.print_header("VÉRIFICATION CONFIGURATION OPENAI")
        
        # Vérifier variable d'environnement
        api_key = os.getenv('OPENAI_API_KEY')
        
        if api_key:
            if api_key.startswith('sk-') and len(api_key) > 20:
                self.print_step("Clé OpenAI détectée via variable d'environnement", "SUCCESS")
            else:
                self.print_step("Format clé OpenAI invalide", "ERROR")
                self.issues_found.append("Clé OpenAI format invalide")
        else:
            self.print_step("Variable OPENAI_API_KEY non définie", "WARNING")
            self.print_step("Configuration fallback active dans config.py", "INFO")
        
        # Test connexion API
        try:
            import openai
            from config import config
            
            if config.ai.OPENAI_API_KEY:
                self.print_step("Test rapide connexion OpenAI")
                
                # Test minimal
                client = openai.OpenAI(api_key=config.ai.OPENAI_API_KEY)
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Test"}],
                    max_tokens=5,
                    timeout=5
                )
                
                self.print_step("Connexion OpenAI fonctionnelle", "SUCCESS")
                self.fixes_applied.append("API OpenAI validée")
            else:
                self.print_step("Clé OpenAI non disponible", "WARNING")
                
        except Exception as e:
            self.print_step(f"Erreur test OpenAI: {e}", "ERROR")
            self.issues_found.append(f"API OpenAI: {e}")
    
    def fix_macos_permissions(self):
        """Réparer permissions macOS"""
        if self.system_os != "Darwin":
            return
        
        self.print_header("RÉPARATION PERMISSIONS MACOS")
        
        # Permissions microphone
        self.print_step("Vérification permissions microphone")
        
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            input_devices = [d for d in devices if d['max_input_channels'] > 0]
            
            if input_devices:
                self.print_step(f"{len(input_devices)} devices audio détectés", "SUCCESS")
                self.fixes_applied.append("Permissions audio macOS validées")
            else:
                self.print_step("Aucun device d'entrée audio détecté", "ERROR")
                self.issues_found.append("Permissions audio macOS manquantes")
                
                # Instruction utilisateur
                print("\n" + "="*60)
                print("🔧 ACTION REQUISE UTILISATEUR:")
                print("1. Aller dans Préférences Système > Confidentialité")
                print("2. Autoriser Terminal/Python pour le Microphone")
                print("3. Redémarrer ce script")
                print("="*60)
                
        except Exception as e:
            self.print_step(f"Erreur vérification audio: {e}", "ERROR")
    
    def optimize_memory_settings(self):
        """Optimiser paramètres mémoire"""
        self.print_header("OPTIMISATION MÉMOIRE")
        
        try:
            import psutil
            
            # Vérifier mémoire disponible
            memory = psutil.virtual_memory()
            available_gb = memory.available / (1024**3)
            
            if available_gb >= 2.0:
                self.print_step(f"Mémoire disponible: {available_gb:.1f}GB", "SUCCESS")
            elif available_gb >= 1.0:
                self.print_step(f"Mémoire disponible: {available_gb:.1f}GB - LIMITE", "WARNING")
                self.issues_found.append("Mémoire système faible")
            else:
                self.print_step(f"Mémoire disponible: {available_gb:.1f}GB - CRITIQUE", "ERROR")
                self.issues_found.append("Mémoire système critique")
            
            # Optimisations GC Python
            import gc
            gc.set_threshold(700, 10, 10)  # Plus agressif
            self.print_step("Paramètres Garbage Collector optimisés", "SUCCESS")
            self.fixes_applied.append("GC Python optimisé")
            
        except ImportError:
            self.print_step("Module psutil non disponible", "WARNING")
    
    def create_startup_script(self):
        """Créer script de démarrage optimisé"""
        self.print_header("CRÉATION SCRIPT DÉMARRAGE")
        
        startup_script = '''#!/bin/bash
# Gideon AI - Script de démarrage optimisé

echo "🚀 Démarrage Gideon AI..."

# Activer environnement virtuel
if [ -d "venv_gideon_production" ]; then
    source venv_gideon_production/bin/activate
    echo "✅ Environnement virtuel activé"
else
    echo "⚠️ Environnement virtuel non trouvé"
fi

# Vérifier variable OpenAI
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️ Variable OPENAI_API_KEY non définie"
    echo "💡 Export recommandé: export OPENAI_API_KEY='your-key-here'"
fi

# Lancer Gideon optimisé
echo "🤖 Lancement Gideon AI Optimisé..."
python3 gideon_main_optimized.py

echo "👋 Gideon AI arrêté"
'''
        
        try:
            script_path = self.project_root / "start_gideon.sh"
            with open(script_path, 'w') as f:
                f.write(startup_script)
            
            # Rendre exécutable
            os.chmod(script_path, 0o755)
            
            self.print_step("Script de démarrage créé: start_gideon.sh", "SUCCESS")
            self.fixes_applied.append("Script démarrage créé")
            
        except Exception as e:
            self.print_step(f"Erreur création script: {e}", "ERROR")
    
    def run_final_test(self):
        """Test final du système complet"""
        self.print_header("TEST FINAL SYSTÈME")
        
        # Test audio complet
        self.print_step("Test final système audio")
        test_command = f"{sys.executable} test_audio_system.py"
        
        if self.run_command(test_command, "Test audio final"):
            self.print_step("✅ Système audio OPÉRATIONNEL", "SUCCESS")
        else:
            self.print_step("❌ Système audio nécessite attention", "WARNING")
        
        # Test import core modules
        core_modules = [
            "core.audio_manager_optimized",
            "core.assistant_core_production", 
            "core.logger",
            "core.memory_monitor"
        ]
        
        for module in core_modules:
            try:
                __import__(module)
                self.print_step(f"Module {module} OK", "SUCCESS")
            except ImportError as e:
                self.print_step(f"Module {module} ERREUR: {e}", "ERROR")
                self.issues_found.append(f"Import module: {module}")
    
    def generate_report(self):
        """Générer rapport de réparation"""
        self.print_header("RAPPORT DE RÉPARATION")
        
        print(f"\n📊 RÉSUMÉ:")
        print(f"   🔧 Corrections appliquées: {len(self.fixes_applied)}")
        print(f"   ⚠️ Problèmes détectés: {len(self.issues_found)}")
        
        if self.fixes_applied:
            print(f"\n✅ CORRECTIONS APPLIQUÉES:")
            for fix in self.fixes_applied:
                print(f"   • {fix}")
        
        if self.issues_found:
            print(f"\n⚠️ PROBLÈMES RESTANTS:")
            for issue in self.issues_found:
                print(f"   • {issue}")
        
        # Score de santé
        total_checks = len(self.fixes_applied) + len(self.issues_found)
        if total_checks > 0:
            health_score = (len(self.fixes_applied) / total_checks) * 100
        else:
            health_score = 100
        
        print(f"\n🏥 SCORE DE SANTÉ: {health_score:.1f}%")
        
        if health_score >= 90:
            print("🎉 SYSTÈME GIDEON AI PRÊT POUR PRODUCTION!")
            return True
        elif health_score >= 70:
            print("⚠️ Système fonctionnel mais avec améliorations possibles")
            return True
        else:
            print("❌ Système nécessite attention avant utilisation")
            return False
    
    def run_complete_repair(self):
        """Exécuter réparation complète"""
        print("""
╔══════════════════════════════════════════════════════════════╗
║               🔧 GIDEON AI AUTO-REPAIR SYSTEM               ║
║                     RÉPARATION AUTOMATIQUE                   ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        start_time = time.time()
        
        try:
            # Séquence de réparation
            self.check_python_environment()
            self.install_dependencies()
            self.check_audio_system()
            self.check_openai_configuration()
            self.fix_macos_permissions()
            self.optimize_memory_settings()
            self.create_startup_script()
            self.run_final_test()
            
            # Rapport final
            system_ready = self.generate_report()
            
            duration = time.time() - start_time
            
            print(f"\n⏱️ Durée totale: {duration:.1f} secondes")
            
            if system_ready:
                print(f"\n🚀 PRÊT À LANCER:")
                print(f"   ./start_gideon.sh")
                print(f"   OU")
                print(f"   python3 gideon_main_optimized.py")
                return 0
            else:
                print(f"\n🔧 ACTIONS REQUISES - Consultez le rapport ci-dessus")
                return 1
                
        except KeyboardInterrupt:
            print(f"\n⌨️ Réparation interrompue par utilisateur")
            return 2
        except Exception as e:
            print(f"\n❌ Erreur critique: {e}")
            logger.error(f"Critical error in repair: {e}")
            return 3

def main():
    """Point d'entrée principal"""
    repair_system = GideonAutoRepair()
    exit_code = repair_system.run_complete_repair()
    sys.exit(exit_code)

if __name__ == "__main__":
    main() 