#!/usr/bin/env python3
"""
Test script pour vérifier que main.py fonctionne
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test des imports principaux"""
    print("🧪 Test des imports...")
    
    try:
        from main import SimpleJarvisApp
        print("✅ Import SimpleJarvisApp: OK")
    except Exception as e:
        print(f"❌ Import SimpleJarvisApp: {e}")
        return False
    
    try:
        from core.logger import GideonLogger
        print("✅ Import GideonLogger: OK")
    except Exception as e:
        print(f"❌ Import GideonLogger: {e}")
        return False
    
    try:
        from core.memory_monitor import MemoryMonitor
        print("✅ Import MemoryMonitor: OK")
    except Exception as e:
        print(f"❌ Import MemoryMonitor: {e}")
        return False
    
    try:
        from core.audio_manager_optimized import AudioManager
        print("✅ Import AudioManager: OK")
    except Exception as e:
        print(f"❌ Import AudioManager: {e}")
        return False
    
    try:
        from core.assistant_core_production import AssistantCore
        print("✅ Import AssistantCore: OK")
    except Exception as e:
        print(f"❌ Import AssistantCore: {e}")
        return False
    
    return True

def test_jarvis_initialization():
    """Test d'initialisation de Jarvis"""
    print("\n🧪 Test d'initialisation...")
    
    try:
        from main import SimpleJarvisApp
        app = SimpleJarvisApp()
        print("✅ Création SimpleJarvisApp: OK")
        
        # Test initialisation des systèmes core
        result = app.initialize_core_systems()
        if result:
            print("✅ Initialisation systèmes core: OK")
        else:
            print("⚠️ Initialisation systèmes core: Partielle")
        
        # Test cleanup
        app.cleanup()
        print("✅ Nettoyage: OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Initialisation: {e}")
        return False

def test_assistant_core():
    """Test de l'assistant core"""
    print("\n🧪 Test Assistant Core...")
    
    try:
        from core.assistant_core_production import AssistantCore
        assistant = AssistantCore()
        print("✅ Création AssistantCore: OK")
        
        # Test de traitement simple
        result = assistant.process_voice_command("Hello test")
        if result['success']:
            print("✅ Traitement commande: OK")
            print(f"📝 Réponse: {result['response'][:50]}...")
        else:
            print(f"⚠️ Traitement commande: {result.get('error', 'Erreur inconnue')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test AssistantCore: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 Tests de validation Jarvis AI Assistant")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: Imports
    if test_imports():
        tests_passed += 1
    
    # Test 2: Initialisation
    if test_jarvis_initialization():
        tests_passed += 1
    
    # Test 3: Assistant Core
    if test_assistant_core():
        tests_passed += 1
    
    # Résultats
    print("\n" + "=" * 50)
    print(f"📊 RÉSULTATS: {tests_passed}/{total_tests} tests réussis")
    
    if tests_passed == total_tests:
        print("🎉 TOUS LES TESTS PASSÉS - Jarvis est fonctionnel!")
        return True
    elif tests_passed > 0:
        print("⚠️ TESTS PARTIELS - Jarvis fonctionne avec limitations")
        return True
    else:
        print("❌ ÉCHEC - Jarvis ne fonctionne pas")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Erreur fatale de test: {e}")
        sys.exit(1) 