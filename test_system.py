#!/usr/bin/env python3
"""
Gideon AI Assistant - System Validation Test
Comprehensive testing of all dependencies and functionality
"""

import sys
import os
import importlib
import platform
from typing import Dict, List, Tuple
import subprocess

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(title: str):
    """Print formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def print_result(test_name: str, status: bool, message: str = "", critical: bool = True):
    """Print test result with color coding"""
    icon = "✅" if status else ("❌" if critical else "⚠️")
    color = Colors.GREEN if status else (Colors.RED if critical else Colors.YELLOW)
    severity = "CRITICAL" if critical and not status else ("OPTIONAL" if not critical else "")
    
    print(f"{color}{icon} {test_name:<30} {severity:<10} {message}{Colors.END}")
    return status

def test_python_version() -> bool:
    """Test Python version compatibility"""
    version = sys.version_info
    required_version = (3, 8)
    
    if version >= required_version:
        print_result("Python Version", True, f"✅ {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_result("Python Version", False, f"❌ {version.major}.{version.minor}.{version.micro} (need 3.8+)")
        return False

def test_dependency(name: str, critical: bool = True, import_test: str = None) -> bool:
    """Test if a Python package is available"""
    try:
        if import_test:
            exec(f"import {import_test}")
        else:
            importlib.import_module(name)
        
        # Get version if possible
        try:
            module = importlib.import_module(name)
            version = getattr(module, '__version__', 'unknown')
            print_result(name, True, f"v{version}", critical)
        except:
            print_result(name, True, "installed", critical)
        
        return True
    except ImportError as e:
        print_result(name, False, str(e)[:50], critical)
        return False

def test_system_audio() -> bool:
    """Test system audio capabilities"""
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        input_devices = [d for d in devices if d['max_input_channels'] > 0]
        
        if input_devices:
            print_result("Audio Input Devices", True, f"{len(input_devices)} found")
            return True
        else:
            print_result("Audio Input Devices", False, "No input devices found")
            return False
    except Exception as e:
        print_result("Audio System", False, str(e)[:50], False)
        return False

def test_openai_api() -> bool:
    """Test OpenAI API configuration"""
    try:
        from openai import OpenAI
        
        # Check if API key is configured
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            # Try from config file
            try:
                from config import config
                api_key = config.ai.OPENAI_API_KEY
            except:
                pass
        
        if api_key and api_key != "your-api-key-here":
            print_result("OpenAI API Key", True, "configured")
            
            # Test API call (optional)
            try:
                client = OpenAI(api_key=api_key)
                # Just test client creation, not actual API call
                print_result("OpenAI Client", True, "initialized")
                return True
            except Exception as e:
                print_result("OpenAI Client", False, str(e)[:50], False)
                return False
        else:
            print_result("OpenAI API Key", False, "not configured", False)
            return False
    except ImportError:
        print_result("OpenAI Package", False, "not installed")
        return False

def test_ui_capabilities() -> bool:
    """Test UI and graphics capabilities"""
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QCoreApplication
        
        # Test if we can create QApplication (headless test)
        if not QCoreApplication.instance():
            app = QApplication([])
            print_result("PyQt6 Application", True, "can create GUI")
            app.quit()
        else:
            print_result("PyQt6 Application", True, "already running")
        
        return True
    except Exception as e:
        print_result("PyQt6 GUI Test", False, str(e)[:50])
        return False

def test_computer_vision() -> bool:
    """Test computer vision capabilities"""
    try:
        import cv2
        print_result("OpenCV", True, f"v{cv2.__version__}")
        
        # Test camera access (without actually opening camera)
        cameras = []
        for i in range(3):  # Check first 3 camera indices
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                cameras.append(i)
                cap.release()
        
        if cameras:
            print_result("Camera Access", True, f"found cameras: {cameras}")
        else:
            print_result("Camera Access", False, "no cameras detected", False)
        
        return True
    except Exception as e:
        print_result("Computer Vision", False, str(e)[:50], False)
        return False

def test_face_detection() -> bool:
    """Test face detection capabilities"""
    try:
        import mtcnn
        detector = mtcnn.MTCNN()
        print_result("Face Detection (MTCNN)", True, "lightweight detector")
        return True
    except ImportError:
        try:
            import face_recognition
            print_result("Face Detection (dlib)", True, "full featured")
            return True
        except ImportError:
            print_result("Face Detection", False, "no face detection available", False)
            return False
    except Exception as e:
        print_result("Face Detection Test", False, str(e)[:50], False)
        return False

def test_smart_home() -> bool:
    """Test smart home connectivity"""
    try:
        import requests
        
        # Test internet connectivity
        response = requests.get("https://httpbin.org/status/200", timeout=5)
        if response.status_code == 200:
            print_result("Internet Connectivity", True, "online")
            
            # Test Philips Hue discovery service
            try:
                hue_response = requests.get("https://discovery.meethue.com/", timeout=5)
                if hue_response.status_code == 200:
                    print_result("Hue Discovery Service", True, "accessible")
                else:
                    print_result("Hue Discovery Service", False, f"HTTP {hue_response.status_code}", False)
            except:
                print_result("Hue Discovery Service", False, "unreachable", False)
            
            return True
        else:
            print_result("Internet Connectivity", False, f"HTTP {response.status_code}")
            return False
    except Exception as e:
        print_result("Network Test", False, str(e)[:50])
        return False

def test_permissions() -> bool:
    """Test system permissions"""
    system = platform.system()
    
    if system == "Darwin":  # macOS
        # Check if running in restricted environment
        try:
            os.access("/dev/null", os.R_OK | os.W_OK)
            print_result("macOS Basic Permissions", True, "file system access OK")
            
            # Note: Can't easily test microphone/camera permissions without triggering prompts
            print_result("macOS Media Permissions", True, "check System Preferences manually", False)
            return True
        except:
            print_result("macOS Permissions", False, "restricted environment")
            return False
    
    elif system == "Linux":
        # Check audio group membership
        try:
            import grp
            audio_group = grp.getgrnam('audio')
            user_groups = os.getgroups()
            
            if audio_group.gr_gid in user_groups:
                print_result("Linux Audio Group", True, "user in audio group")
            else:
                print_result("Linux Audio Group", False, "user not in audio group", False)
            
            return True
        except Exception as e:
            print_result("Linux Permissions", False, str(e)[:50], False)
            return False
    
    elif system == "Windows":
        # Basic Windows permissions test
        try:
            temp_file = os.path.join(os.environ.get('TEMP', '.'), 'gideon_test.tmp')
            with open(temp_file, 'w') as f:
                f.write('test')
            os.remove(temp_file)
            print_result("Windows File Permissions", True, "write access OK")
            return True
        except Exception as e:
            print_result("Windows Permissions", False, str(e)[:50])
            return False
    
    return True

def run_comprehensive_test() -> Dict[str, bool]:
    """Run all tests and return results"""
    
    print_header("🤖 GIDEON AI ASSISTANT - SYSTEM VALIDATION")
    
    print(f"{Colors.CYAN}System Information:{Colors.END}")
    print(f"  OS: {platform.system()} {platform.release()}")
    print(f"  Architecture: {platform.machine()}")
    print(f"  Python: {sys.version}")
    print(f"  Working Directory: {os.getcwd()}")
    
    results = {}
    
    # Core Python test
    print_header("🐍 PYTHON ENVIRONMENT")
    results['python_version'] = test_python_version()
    
    # Critical dependencies
    print_header("📦 CRITICAL DEPENDENCIES")
    results['pyqt6'] = test_dependency('PyQt6')
    results['openai'] = test_dependency('openai')
    results['requests'] = test_dependency('requests')
    results['psutil'] = test_dependency('psutil')
    results['numpy'] = test_dependency('numpy')
    
    # Optional dependencies
    print_header("🔧 OPTIONAL DEPENDENCIES")
    results['opencv'] = test_dependency('cv2', False, 'cv2')
    results['speech_recognition'] = test_dependency('speech_recognition', False)
    results['pyttsx3'] = test_dependency('pyttsx3', False)
    results['sounddevice'] = test_dependency('sounddevice', False)
    
    # System capabilities
    print_header("🖥️ SYSTEM CAPABILITIES")
    results['ui_test'] = test_ui_capabilities()
    results['audio_test'] = test_system_audio()
    results['cv_test'] = test_computer_vision()
    results['face_detection'] = test_face_detection()
    results['smart_home'] = test_smart_home()
    results['permissions'] = test_permissions()
    
    # Configuration tests
    print_header("⚙️ CONFIGURATION")
    results['openai_api'] = test_openai_api()
    
    return results

def print_summary(results: Dict[str, bool]):
    """Print test summary"""
    print_header("📊 TEST SUMMARY")
    
    critical_tests = ['python_version', 'pyqt6', 'openai', 'requests', 'psutil', 'numpy']
    critical_passed = sum(1 for test in critical_tests if results.get(test, False))
    
    optional_tests = [k for k in results.keys() if k not in critical_tests]
    optional_passed = sum(1 for test in optional_tests if results.get(test, False))
    
    total_tests = len(results)
    total_passed = sum(results.values())
    
    print(f"{Colors.BOLD}Critical Tests: {critical_passed}/{len(critical_tests)} passed{Colors.END}")
    print(f"{Colors.BOLD}Optional Tests: {optional_passed}/{len(optional_tests)} passed{Colors.END}")
    print(f"{Colors.BOLD}Total Score: {total_passed}/{total_tests} ({total_passed/total_tests*100:.1f}%){Colors.END}")
    
    if critical_passed == len(critical_tests):
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 SYSTEM READY FOR GIDEON DEPLOYMENT!{Colors.END}")
        print(f"{Colors.GREEN}You can run: python gideon_main.py{Colors.END}")
    elif critical_passed >= len(critical_tests) - 1:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ SYSTEM MOSTLY READY - MINOR ISSUES{Colors.END}")
        print(f"{Colors.YELLOW}Try: python demo.py for basic functionality{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ CRITICAL DEPENDENCIES MISSING{Colors.END}")
        print(f"{Colors.RED}Please install missing packages and try again{Colors.END}")
    
    # Specific recommendations
    print(f"\n{Colors.CYAN}{Colors.BOLD}RECOMMENDATIONS:{Colors.END}")
    
    if not results.get('openai_api', False):
        print(f"{Colors.YELLOW}• Configure OpenAI API key for AI responses{Colors.END}")
    
    if not results.get('sounddevice', False):
        print(f"{Colors.YELLOW}• Install sounddevice for audio input: pip install sounddevice{Colors.END}")
    
    if not results.get('face_detection', False):
        print(f"{Colors.YELLOW}• Install face detection: pip install mtcnn{Colors.END}")
    
    if not results.get('audio_test', False):
        print(f"{Colors.YELLOW}• Check microphone permissions and drivers{Colors.END}")

def main():
    """Main test function"""
    try:
        results = run_comprehensive_test()
        print_summary(results)
        
        # Exit code based on critical tests
        critical_tests = ['python_version', 'pyqt6', 'openai', 'requests', 'psutil']
        critical_passed = all(results.get(test, False) for test in critical_tests)
        
        sys.exit(0 if critical_passed else 1)
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test interrupted by user{Colors.END}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}Test failed with error: {e}{Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    main() 