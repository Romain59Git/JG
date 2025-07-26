#!/bin/bash

# Script d'installation des dépendances Jarvis AI Assistant
# Version simplifiée et fonctionnelle

echo "📦 Installation des dépendances Jarvis AI Assistant"
echo "=================================================="

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Vérification de l'environnement virtuel
check_and_activate_venv() {
    if [ -d "venv_gideon_production" ]; then
        log_info "Activation de l'environnement virtuel..."
        source venv_gideon_production/bin/activate
        VENV_ACTIVE=true
    elif [ -d "venv_jarvis_local" ]; then
        log_info "Activation de l'environnement virtuel..."
        source venv_jarvis_local/bin/activate
        VENV_ACTIVE=true
    else
        log_warning "Aucun environnement virtuel trouvé"
        log_info "Création d'un nouvel environnement virtuel..."
        python3 -m venv venv_jarvis_fixed
        source venv_jarvis_fixed/bin/activate
        VENV_ACTIVE=true
    fi
}

# Installation des dépendances core
install_core_dependencies() {
    log_info "Installation des dépendances principales..."
    
    # Mise à jour pip
    pip install --upgrade pip
    
    # Dépendances essentielles pour faire fonctionner Jarvis
    pip install psutil>=5.9.0
    pip install requests>=2.31.0
    pip install PyQt6>=6.5.0
    pip install pyttsx3>=2.90
    pip install SpeechRecognition>=3.10.0
    
    log_info "Dépendances principales installées"
}

# Installation des dépendances optionnelles
install_optional_dependencies() {
    log_info "Installation des dépendances optionnelles..."
    
    # Audio avancé
    pip install pyaudio>=0.2.11 || log_warning "PyAudio non installé (nécessite portaudio)"
    pip install sounddevice>=0.4.6 || log_warning "SoundDevice non installé"
    
    # Vision locale (optionnelle)
    pip install opencv-python>=4.8.0 || log_warning "OpenCV non installé"
    pip install Pillow>=10.0.0 || log_warning "Pillow non installé"
    
    # Mémoire vectorielle (optionnelle)
    pip install chromadb>=0.4.0 || log_warning "ChromaDB non installé"
    pip install sentence-transformers>=2.2.0 || log_warning "Sentence-transformers non installé"
    
    # Interface riche
    pip install rich>=13.0.0 || log_warning "Rich non installé"
    
    log_info "Dépendances optionnelles traitées"
}

# Test de l'installation
test_installation() {
    log_info "Test de l'installation..."
    
    python3 -c "import psutil; print('✅ psutil OK')" 2>/dev/null || log_error "psutil manquant"
    python3 -c "import requests; print('✅ requests OK')" 2>/dev/null || log_error "requests manquant"
    python3 -c "import pyttsx3; print('✅ pyttsx3 OK')" 2>/dev/null || log_warning "pyttsx3 manquant"
    python3 -c "import speech_recognition; print('✅ SpeechRecognition OK')" 2>/dev/null || log_warning "SpeechRecognition manquant"
    
    # Test des modules optionnels
    python3 -c "from PyQt6.QtWidgets import QApplication; print('✅ PyQt6 OK')" 2>/dev/null || log_warning "PyQt6 manquant"
    python3 -c "import cv2; print('✅ OpenCV OK')" 2>/dev/null || log_warning "OpenCV manquant (optionnel)"
    python3 -c "import chromadb; print('✅ ChromaDB OK')" 2>/dev/null || log_warning "ChromaDB manquant (optionnel)"
    
    log_info "Test d'installation terminé"
}

# Fonction principale
main() {
    # Vérification Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 non trouvé. Veuillez installer Python 3.9+"
        exit 1
    fi
    
    # Activation environnement virtuel
    check_and_activate_venv
    
    # Installation des dépendances
    install_core_dependencies
    install_optional_dependencies
    
    # Test de l'installation
    test_installation
    
    echo ""
    log_info "Installation terminée!"
    echo ""
    echo "🚀 Pour démarrer Jarvis, exécutez:"
    echo "   ./start_jarvis.sh"
    echo ""
    echo "🧪 Pour tester le système:"
    echo "   python3 test_main.py"
    echo ""
}

# Gestion des erreurs
trap 'log_error "Erreur lors de l'"'"'installation"; exit 1' ERR

# Exécution
main "$@" 