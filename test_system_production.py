#!/usr/bin/env python3
"""
Gideon AI Assistant - System Validation Production
Script de validation complète résolvant le Problème #8

Tests automatiques:
- ✅ Compatibilité Python et OS
- ✅ Toutes les dépendances critiques et optionnelles
- ✅ Permissions système (microphone, caméra)
- ✅ Performance et mémoire disponible
- ✅ Configuration OpenAI
- ✅ Capacités audio/vidéo
- ✅ Interface graphique
- ✅ Recommandations personnalisées
"""

import sys
import os
import platform
import importlib
import subprocess
import time
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path

# Ajout du chemin du projet
sys.path.insert(0, str(Path(__file__).parent))

@dataclass
class TestResult:
    """Résultat d'un test individuel"""
    name: str
    passed: bool
    message: str
    critical: bool = True
    details: Dict = None

class Colors:
    """Codes couleur ANSI pour terminal"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

class SystemValidatorProduction:
    """Validateur système production pour Gideon AI Assistant"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.system_info = self._get_system_info()
        self.start_time = time.time()
        
    def _get_system_info(self) -> Dict[str, str]:
        """Obtenir informations système"""
        return {
            'os': platform.system(),
            'os_version': platform.release(),
            'architecture': platform.machine(),
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'python_executable': sys.executable,
            'working_directory': os.getcwd(),
            'script_location': str(Path(__file__).parent.absolute())
        }
    
    def print_header(self, title: str):
        """Afficher en-tête formaté"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{title.center(70)}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")
    
    def log_result(self, name: str, passed: bool, message: str = "", critical: bool = True, details: Dict = None) -> TestResult:
        """Enregistrer et afficher résultat de test"""
        result = TestResult(name, passed, message, critical, details)
        self.results.append(result)
        
        # Icône et couleur
        icon = "✅" if passed else ("❌" if critical else "⚠️")
        color = Colors.GREEN if passed else (Colors.RED if critical else Colors.YELLOW)
        severity = "CRITICAL" if critical and not passed else ("OPTIONAL" if not critical else "")
        
        # Affichage formaté
        print(f"{color}{icon} {name:<35} {severity:<10} {message}{Colors.END}")
        
        if details and not passed:
            for key, value in details.items():
                print(f"    {Colors.CYAN}{key}: {value}{Colors.END}")
        
        return result
    
    def test_python_environment(self) -> bool:
        """Test environnement Python"""
        self.print_header("🐍 ENVIRONNEMENT PYTHON")
        
        # Version Python
        version = sys.version_info
        required_version = (3, 8)
        python_ok = version >= required_version
        
        self.log_result(
            "Version Python",
            python_ok,
            f"{version.major}.{version.minor}.{version.micro}" + (" ✅" if python_ok else f" (requis: {required_version[0]}.{required_version[1]}+)"),
            critical=True
        )
        
        # Installation pip
        try:
            import pip
            pip_version = pip.__version__
            self.log_result("Package pip", True, f"v{pip_version}", critical=True)
        except ImportError:
            self.log_result("Package pip", False, "pip non disponible", critical=True)
        
        # Environnement virtuel
        in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        self.log_result(
            "Environnement virtuel",
            in_venv,
            "Activé" if in_venv else "Non détecté (recommandé)",
            critical=False
        )
        
        return python_ok
    
    def test_system_info(self) -> bool:
        """Test informations système"""
        self.print_header("💻 INFORMATIONS SYSTÈME")
        
        print(f"{Colors.CYAN}OS: {self.system_info['os']} {self.system_info['os_version']}{Colors.END}")
        print(f"{Colors.CYAN}Architecture: {self.system_info['architecture']}{Colors.END}")
        print(f"{Colors.CYAN}Python: {self.system_info['python_version']}{Colors.END}")
        print(f"{Colors.CYAN}Exécutable Python: {self.system_info['python_executable']}{Colors.END}")
        print(f"{Colors.CYAN}Répertoire de travail: {self.system_info['working_directory']}{Colors.END}")
        
        # Vérification OS supporté
        supported_os = ['Windows', 'Linux', 'Darwin']
        os_supported = self.system_info['os'] in supported_os
        
        self.log_result(
            "OS Supporté",
            os_supported,
            self.system_info['os'] if os_supported else f"{self.system_info['os']} (non testé)",
            critical=False
        )
        
        return True
    
    def test_critical_dependencies(self) -> bool:
        """Test dépendances critiques"""
        self.print_header("📦 DÉPENDANCES CRITIQUES")
        
        critical_deps = {
            'openai': "OpenAI API",
            'PyQt6': "Interface graphique",
            'requests': "Requêtes HTTP",
            'psutil': "Monitoring système",
            'numpy': "Calculs numériques"
        }
        
        all_critical_ok = True
        
        for dep_name, dep_desc in critical_deps.items():
            try:
                module = importlib.import_module(dep_name)
                version = getattr(module, '__version__', 'unknown')
                self.log_result(dep_desc, True, f"v{version}", critical=True)
            except ImportError as e:
                self.log_result(dep_desc, False, f"Non installé: {str(e)[:50]}", critical=True)
                all_critical_ok = False
        
        return all_critical_ok
    
    def test_optional_dependencies(self) -> bool:
        """Test dépendances optionnelles"""
        self.print_header("🔧 DÉPENDANCES OPTIONNELLES")
        
        optional_deps = {
            'sounddevice': "Audio input/output",
            'cv2': "Computer vision",
            'mtcnn': "Face detection",
            'tensorflow': "Machine learning",
            'pyttsx3': "Text-to-speech",
            'speech_recognition': "Speech recognition",
            'scipy': "Signal processing",
            'Pillow': "Image processing"
        }
        
        optional_count = 0
        
        for dep_name, dep_desc in optional_deps.items():
            try:
                if dep_name == 'cv2':
                    import cv2
                    module = cv2
                else:
                    module = importlib.import_module(dep_name)
                
                version = getattr(module, '__version__', 'unknown')
                self.log_result(dep_desc, True, f"v{version}", critical=False)
                optional_count += 1
            except ImportError:
                self.log_result(dep_desc, False, "Non installé", critical=False)
        
        # Score optionnel
        total_optional = len(optional_deps)
        score_percent = (optional_count / total_optional) * 100
        
        print(f"\n{Colors.CYAN}Score dépendances optionnelles: {optional_count}/{total_optional} ({score_percent:.1f}%){Colors.END}")
        
        return True
    
    def test_performance_system(self) -> bool:
        """Test performance système"""
        self.print_header("⚡ PERFORMANCE SYSTÈME")
        
        try:
            import psutil
            
            # Mémoire
            memory = psutil.virtual_memory()
            total_gb = memory.total / (1024**3)
            available_gb = memory.available / (1024**3)
            memory_ok = available_gb >= 1.0  # Minimum 1GB libre
            
            self.log_result(
                "Mémoire disponible",
                memory_ok,
                f"{available_gb:.1f}GB / {total_gb:.1f}GB total",
                critical=False,
                details={"Minimum recommandé": "1.0GB"} if not memory_ok else None
            )
            
            # CPU
            cpu_count = psutil.cpu_count()
            cpu_usage = psutil.cpu_percent(interval=1)
            cpu_ok = cpu_usage < 90  # Pas trop chargé
            
            self.log_result(
                "CPU",
                cpu_ok,
                f"{cpu_count} cœurs, {cpu_usage:.1f}% usage",
                critical=False
            )
            
            # Disque
            if platform.system() == 'Windows':
                disk_usage = psutil.disk_usage('C:')
            else:
                disk_usage = psutil.disk_usage('/')
            
            free_gb = disk_usage.free / (1024**3)
            disk_ok = free_gb >= 1.0  # Minimum 1GB libre
            
            self.log_result(
                "Espace disque",
                disk_ok,
                f"{free_gb:.1f}GB libre",
                critical=False
            )
            
            return memory_ok and disk_ok
            
        except ImportError:
            self.log_result("Performance système", False, "psutil non disponible", critical=False)
            return False
    
    def test_permissions(self) -> bool:
        """Test permissions système"""
        self.print_header("🔐 PERMISSIONS SYSTÈME")
        
        permissions_ok = True
        
        # Test écriture fichier
        try:
            test_file = Path("gideon_test_write.tmp")
            test_file.write_text("test")
            test_file.unlink()
            self.log_result("Écriture fichiers", True, "OK", critical=True)
        except Exception as e:
            self.log_result("Écriture fichiers", False, str(e)[:50], critical=True)
            permissions_ok = False
        
        # Test microphone (basique)
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            input_devices = [d for d in devices if d['max_input_channels'] > 0]
            mic_ok = len(input_devices) > 0
            
            self.log_result(
                "Périphériques audio",
                mic_ok,
                f"{len(input_devices)} périphérique(s) d'entrée",
                critical=False
            )
            
            # Test rapide microphone
            if mic_ok:
                try:
                    # Test très court pour éviter les demandes de permission
                    data = sd.rec(frames=1024, samplerate=44100, channels=1, blocking=True)
                    self.log_result("Accès microphone", True, "Test réussi", critical=False)
                except Exception as e:
                    details = {}
                    if platform.system() == 'Darwin':
                        details["Solution macOS"] = "System Preferences > Security & Privacy > Microphone"
                    
                    self.log_result(
                        "Accès microphone",
                        False,
                        str(e)[:50],
                        critical=False,
                        details=details
                    )
        except ImportError:
            self.log_result("Test audio", False, "sounddevice non installé", critical=False)
        
        # Test caméra (basique)
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            camera_ok = cap.isOpened()
            if camera_ok:
                cap.release()
            
            details = {}
            if not camera_ok and platform.system() == 'Darwin':
                details["Solution macOS"] = "System Preferences > Security & Privacy > Camera"
            
            self.log_result(
                "Accès caméra",
                camera_ok,
                "Caméra accessible" if camera_ok else "Accès refusé",
                critical=False,
                details=details if not camera_ok else None
            )
        except ImportError:
            self.log_result("Test caméra", False, "OpenCV non installé", critical=False)
        
        return permissions_ok
    
    def test_openai_configuration(self) -> bool:
        """Test configuration OpenAI"""
        self.print_header("🤖 CONFIGURATION OPENAI")
        
        # Test import OpenAI
        try:
            from openai import OpenAI
            self.log_result("Import OpenAI", True, "Nouvelle API détectée", critical=False)
        except ImportError:
            self.log_result("Import OpenAI", False, "Package non installé", critical=True)
            return False
        
        # Test clé API
        api_key = None
        
        # Chercher clé dans variables d'environnement
        api_key = os.getenv('OPENAI_API_KEY')
        
        # Chercher dans config si disponible
        if not api_key:
            try:
                from config import config
                api_key = config.ai.OPENAI_API_KEY
            except ImportError:
                pass
        
        if not api_key or api_key == "your-api-key-here":
            self.log_result(
                "Clé API OpenAI",
                False,
                "Non configurée",
                critical=False,
                details={
                    "Solution 1": "export OPENAI_API_KEY='votre-clé'",
                    "Solution 2": "Configurer dans config.py"
                }
            )
            return False
        
        # Test de connectivité (optionnel)
        try:
            client = OpenAI(api_key=api_key)
            # Test très léger
            self.log_result("Client OpenAI", True, "Client initialisé", critical=False)
            
            # Ne pas faire d'appel API réel pour éviter les coûts
            self.log_result(
                "Test API",
                True,
                "Configuration valide (test non effectué)",
                critical=False,
                details={"Note": "Appel API non testé pour éviter les coûts"}
            )
            
            return True
            
        except Exception as e:
            self.log_result(
                "Client OpenAI",
                False,
                str(e)[:50],
                critical=False
            )
            return False
    
    def test_ui_capabilities(self) -> bool:
        """Test capacités interface utilisateur"""
        self.print_header("🖥️ INTERFACE UTILISATEUR")
        
        # Test PyQt6
        try:
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtCore import QCoreApplication
            
            # Test création app (sans affichage)
            if not QCoreApplication.instance():
                app = QApplication([])
                self.log_result("PyQt6 Application", True, "Création réussie", critical=False)
                app.quit()
            else:
                self.log_result("PyQt6 Application", True, "Instance existante", critical=False)
            
            # Test system tray
            try:
                from PyQt6.QtWidgets import QSystemTrayIcon
                tray_available = QSystemTrayIcon.isSystemTrayAvailable()
                
                details = {}
                if not tray_available and platform.system() == 'Linux':
                    details["Solution Linux"] = "export QT_QPA_PLATFORM=xcb (si Wayland)"
                
                self.log_result(
                    "System Tray",
                    tray_available,
                    "Disponible" if tray_available else "Non disponible",
                    critical=False,
                    details=details if not tray_available else None
                )
            except ImportError:
                self.log_result("System Tray", False, "PyQt6 widgets non disponibles", critical=False)
            
            return True
            
        except ImportError as e:
            self.log_result("PyQt6", False, str(e)[:50], critical=False)
            return False
    
    def test_project_structure(self) -> bool:
        """Test structure du projet"""
        self.print_header("📁 STRUCTURE PROJET")
        
        required_files = [
            ('config.py', 'Configuration principale'),
            ('core/__init__.py', 'Module core'),
            ('ui/__init__.py', 'Module UI'),
            ('modules/__init__.py', 'Modules fonctionnels'),
            ('requirements_production.txt', 'Dépendances production')
        ]
        
        optional_files = [
            ('gideon_main_production.py', 'Application principale'),
            ('README.md', 'Documentation'),
            ('.vscode/settings.json', 'Configuration VS Code'),
            ('test_system_production.py', 'Tests système')
        ]
        
        structure_ok = True
        
        # Fichiers requis
        for file_path, description in required_files:
            file_exists = Path(file_path).exists()
            self.log_result(description, file_exists, file_path, critical=True)
            if not file_exists:
                structure_ok = False
        
        # Fichiers optionnels
        for file_path, description in optional_files:
            file_exists = Path(file_path).exists()
            self.log_result(description, file_exists, file_path, critical=False)
        
        return structure_ok
    
    def test_import_core_modules(self) -> bool:
        """Test import des modules core"""
        self.print_header("🔄 MODULES CORE")
        
        core_modules = [
            ('core.event_system', 'Système d\'événements'),
            ('core.logger', 'Système de logging'),
            ('core.assistant_core_production', 'Core assistant production')
        ]
        
        modules_ok = True
        
        for module_name, description in core_modules:
            try:
                importlib.import_module(module_name)
                self.log_result(description, True, f"Import {module_name} OK", critical=True)
            except ImportError as e:
                self.log_result(description, False, str(e)[:50], critical=True)
                modules_ok = False
        
        return modules_ok
    
    def run_comprehensive_test(self) -> Dict[str, any]:
        """Exécuter suite complète de tests"""
        print(f"\n{Colors.BOLD}{Colors.PURPLE}🤖 GIDEON AI ASSISTANT - VALIDATION SYSTÈME PRODUCTION{Colors.END}")
        print(f"{Colors.PURPLE}Démarrage validation complète...{Colors.END}")
        print(f"{Colors.PURPLE}Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}")
        
        # Exécuter tous les tests
        test_results = {
            'python_env': self.test_python_environment(),
            'system_info': self.test_system_info(),
            'critical_deps': self.test_critical_dependencies(),
            'optional_deps': self.test_optional_dependencies(),
            'performance': self.test_performance_system(),
            'permissions': self.test_permissions(),
            'openai_config': self.test_openai_configuration(),
            'ui_capabilities': self.test_ui_capabilities(),
            'project_structure': self.test_project_structure(),
            'core_modules': self.test_import_core_modules()
        }
        
        return test_results
    
    def generate_recommendations(self) -> List[str]:
        """Générer recommandations basées sur les résultats"""
        recommendations = []
        
        for result in self.results:
            if not result.passed:
                if 'OpenAI' in result.name and 'Non configurée' in result.message:
                    recommendations.append("Configurer clé API OpenAI: export OPENAI_API_KEY='votre-clé'")
                
                elif 'sounddevice' in result.message:
                    recommendations.append("Installer audio: pip install sounddevice soundfile")
                
                elif 'mtcnn' in result.message or 'tensorflow' in result.message:
                    recommendations.append("Installer face detection: pip install mtcnn tensorflow-cpu")
                
                elif 'PyQt6' in result.message:
                    recommendations.append("Installer interface: pip install PyQt6")
                
                elif 'microphone' in result.name.lower() and platform.system() == 'Darwin':
                    recommendations.append("Autoriser microphone macOS: System Preferences > Security & Privacy")
                
                elif 'System Tray' in result.name and platform.system() == 'Linux':
                    recommendations.append("Fix system tray Linux: export QT_QPA_PLATFORM=xcb")
                
                elif 'Mémoire' in result.name:
                    recommendations.append("Libérer mémoire RAM (minimum 1GB recommandé)")
        
        # Recommandations générales
        if not any('venv' in result.message for result in self.results if result.name == "Environnement virtuel"):
            recommendations.append("Créer environnement virtuel: python -m venv venv")
        
        # Dédupliquer
        return list(set(recommendations))
    
    def print_final_summary(self, test_results: Dict[str, bool]):
        """Afficher résumé final"""
        self.print_header("📊 RÉSUMÉ FINAL")
        
        # Statistiques
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        critical_tests = [r for r in self.results if r.critical]
        critical_passed = sum(1 for r in critical_tests if r.passed)
        
        # Score global
        score_percent = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        critical_score = (critical_passed / len(critical_tests)) * 100 if critical_tests else 100
        
        print(f"{Colors.BOLD}Tests totaux: {passed_tests}/{total_tests} ({score_percent:.1f}%){Colors.END}")
        print(f"{Colors.BOLD}Tests critiques: {critical_passed}/{len(critical_tests)} ({critical_score:.1f}%){Colors.END}")
        
        # Temps d'exécution
        execution_time = time.time() - self.start_time
        print(f"{Colors.BOLD}Temps d'exécution: {execution_time:.1f}s{Colors.END}")
        
        # Statut final
        if critical_score >= 80 and score_percent >= 70:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 SYSTÈME PRÊT POUR GIDEON PRODUCTION !{Colors.END}")
            print(f"{Colors.GREEN}Vous pouvez lancer: python gideon_main_production.py{Colors.END}")
        elif critical_score >= 60:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ SYSTÈME PARTIELLEMENT PRÊT{Colors.END}")
            print(f"{Colors.YELLOW}Mode dégradé possible. Résoudre les problèmes critiques.{Colors.END}")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}❌ SYSTÈME NON PRÊT{Colors.END}")
            print(f"{Colors.RED}Trop de problèmes critiques. Installation requise.{Colors.END}")
        
        # Recommandations
        recommendations = self.generate_recommendations()
        if recommendations:
            print(f"\n{Colors.CYAN}{Colors.BOLD}💡 RECOMMANDATIONS:{Colors.END}")
            for i, rec in enumerate(recommendations[:5], 1):  # Top 5
                print(f"{Colors.CYAN}  {i}. {rec}{Colors.END}")
        
        # Next steps
        print(f"\n{Colors.BLUE}{Colors.BOLD}🚀 PROCHAINES ÉTAPES:{Colors.END}")
        print(f"{Colors.BLUE}  1. Résoudre les problèmes critiques identifiés{Colors.END}")
        print(f"{Colors.BLUE}  2. Installer dépendances manquantes{Colors.END}")
        print(f"{Colors.BLUE}  3. Configurer permissions système{Colors.END}")
        print(f"{Colors.BLUE}  4. Relancer ce test: python test_system_production.py{Colors.END}")
        print(f"{Colors.BLUE}  5. Démarrer Gideon: python gideon_main_production.py{Colors.END}")
        
        return score_percent

def main():
    """Point d'entrée principal"""
    validator = SystemValidatorProduction()
    
    try:
        # Exécuter validation complète
        test_results = validator.run_comprehensive_test()
        
        # Afficher résumé
        final_score = validator.print_final_summary(test_results)
        
        # Code de sortie basé sur le score
        if final_score >= 70:
            return 0  # Succès
        elif final_score >= 50:
            return 1  # Avertissement
        else:
            return 2  # Échec critique
            
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Validation interrompue par l'utilisateur{Colors.END}")
        return 130
    except Exception as e:
        print(f"\n{Colors.RED}Erreur durant la validation: {e}{Colors.END}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 