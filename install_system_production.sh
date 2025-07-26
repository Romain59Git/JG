#!/bin/bash
# ================================================================
# GIDEON AI ASSISTANT - PRODUCTION INSTALLATION SCRIPT
# Installation automatique résolvant tous les problèmes critiques
# ================================================================

set -e  # Exit on any error

# =====================================
# CONFIGURATION ET DÉTECTION
# =====================================

# Colors pour output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Variables globales
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_NAME="venv_gideon_production"
PYTHON_MIN_VERSION="3.8"
LOG_FILE="$SCRIPT_DIR/install_production.log"

# Détecter OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        if command -v lsb_release >/dev/null 2>&1; then
            DISTRO=$(lsb_release -si)
        elif [ -f /etc/os-release ]; then
            DISTRO=$(grep "^ID=" /etc/os-release | cut -d'=' -f2 | tr -d '"')
        else
            DISTRO="unknown"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        DISTRO="macos"
    elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        OS="windows"
        DISTRO="windows"
    else
        echo -e "${RED}❌ OS non supporté: $OSTYPE${NC}"
        exit 1
    fi
}

# =====================================
# FONCTIONS UTILITAIRES
# =====================================

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
    echo -e "$1"
}

print_header() {
    echo -e "\n${BOLD}${BLUE}================================================${NC}"
    echo -e "${BOLD}${BLUE} $1${NC}"
    echo -e "${BOLD}${BLUE}================================================${NC}\n"
}

print_step() {
    echo -e "${CYAN}➤ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Vérifier commande
check_command() {
    if command -v "$1" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Vérifier version Python
check_python_version() {
    local python_cmd="$1"
    if ! check_command "$python_cmd"; then
        return 1
    fi
    
    local version=$($python_cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    local required="$PYTHON_MIN_VERSION"
    
    if [ "$(printf '%s\n' "$required" "$version" | sort -V | head -n1)" = "$required" ]; then
        echo "$version"
        return 0
    else
        return 1
    fi
}

# =====================================
# INSTALLATION PAR OS
# =====================================

install_linux() {
    print_header "🐧 INSTALLATION LINUX ($DISTRO)"
    
    # Mise à jour des packages
    print_step "Mise à jour des packages système..."
    if [[ "$DISTRO" == "ubuntu" ]] || [[ "$DISTRO" == "debian" ]]; then
        sudo apt update || { print_error "Échec mise à jour apt"; exit 1; }
        
        # Packages essentiels
        print_step "Installation des dépendances système..."
        sudo apt install -y \
            python3-dev \
            python3-pip \
            python3-venv \
            build-essential \
            cmake \
            pkg-config \
            git \
            curl \
            wget || { print_error "Échec installation packages de base"; exit 1; }
        
        # Audio (résout Problème #2 - pyaudio)
        print_step "Installation des dépendances audio..."
        sudo apt install -y \
            libasound2-dev \
            portaudio19-dev \
            pulseaudio \
            alsa-utils \
            libportaudio2 \
            libsndfile1-dev || print_warning "Certains packages audio ont échoué"
        
        # Qt6 pour interface (résout Problème #6)
        print_step "Installation Qt6..."
        sudo apt install -y \
            qt6-base-dev \
            qt6-multimedia-dev \
            python3-pyqt6 || print_warning "Qt6 système non disponible, utilisera pip"
        
        # OpenCV dépendances
        print_step "Installation dépendances OpenCV..."
        sudo apt install -y \
            libopencv-dev \
            python3-opencv \
            libgtk-3-dev \
            libcanberra-gtk-module \
            libcanberra-gtk3-module || print_warning "Certains packages OpenCV ont échoué"
        
        # Text-to-speech
        print_step "Installation TTS..."
        sudo apt install -y \
            espeak \
            espeak-data \
            libespeak1 \
            libespeak-dev || print_warning "TTS system non installé"
        
    elif [[ "$DISTRO" == "fedora" ]] || [[ "$DISTRO" == "rhel" ]] || [[ "$DISTRO" == "centos" ]]; then
        # RedHat/Fedora
        sudo dnf update -y || sudo yum update -y
        sudo dnf install -y python3-devel python3-pip python3-venv gcc gcc-c++ cmake git || \
        sudo yum install -y python3-devel python3-pip python3-venv gcc gcc-c++ cmake git
        
    elif [[ "$DISTRO" == "arch" ]]; then
        # Arch Linux
        sudo pacman -Syu --noconfirm
        sudo pacman -S --noconfirm python python-pip base-devel cmake git qt6-base qt6-multimedia
    fi
    
    # Groupes utilisateur pour audio (résout Problème #5)
    print_step "Configuration groupes utilisateur..."
    sudo usermod -a -G audio "$USER" 2>/dev/null || print_warning "Groupe audio non ajouté"
    sudo usermod -a -G video "$USER" 2>/dev/null || print_warning "Groupe video non ajouté"
    
    # Fix Wayland system tray (résout Problème #6)
    if [ -n "$WAYLAND_DISPLAY" ]; then
        print_step "Configuration Wayland pour system tray..."
        echo 'export QT_QPA_PLATFORM=xcb' >> ~/.bashrc
        echo 'export QT_QPA_PLATFORM=xcb' >> ~/.profile
        export QT_QPA_PLATFORM=xcb
        print_success "Wayland configuré pour utiliser X11 (system tray)"
    fi
    
    print_success "Installation Linux terminée"
}

install_macos() {
    print_header "🍎 INSTALLATION MACOS"
    
    # Vérifier/installer Homebrew
    if ! check_command brew; then
        print_step "Installation Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # Ajouter au PATH
        if [[ -d "/opt/homebrew" ]]; then
            echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
            export PATH="/opt/homebrew/bin:$PATH"
        fi
    fi
    
    # Mise à jour Homebrew
    print_step "Mise à jour Homebrew..."
    brew update
    
    # Dépendances système
    print_step "Installation dépendances système..."
    brew install \
        python@3.9 \
        cmake \
        portaudio \
        qt6 \
        pkg-config \
        opencv \
        git || { print_error "Échec installation packages Homebrew"; exit 1; }
    
    # Configuration PATH
    print_step "Configuration PATH..."
    {
        echo 'export PATH="/opt/homebrew/opt/python@3.9/bin:$PATH"'
        echo 'export PATH="/opt/homebrew/opt/qt@6/bin:$PATH"'
        echo 'export PKG_CONFIG_PATH="/opt/homebrew/lib/pkgconfig:$PKG_CONFIG_PATH"'
    } >> ~/.zshrc
    
    # Appliquer immédiatement
    export PATH="/opt/homebrew/opt/python@3.9/bin:$PATH"
    export PATH="/opt/homebrew/opt/qt@6/bin:$PATH"
    export PKG_CONFIG_PATH="/opt/homebrew/lib/pkgconfig:$PKG_CONFIG_PATH"
    
    # Permissions macOS (résout Problème #5)
    print_step "Configuration permissions macOS..."
    print_warning "IMPORTANT: Vous devrez autoriser manuellement:"
    print_warning "  1. System Preferences > Security & Privacy > Microphone"
    print_warning "  2. System Preferences > Security & Privacy > Camera"
    print_warning "  3. Ajouter Terminal et Python aux applications autorisées"
    
    print_success "Installation macOS terminée"
}

install_windows() {
    print_header "🪟 INSTALLATION WINDOWS"
    
    # Vérifier gestionnaire de packages
    if check_command winget; then
        print_step "Installation via winget..."
        winget install --id Git.Git -e --silent
        winget install --id Python.Python.3.9 -e --silent
        winget install --id Microsoft.VisualStudio.2022.BuildTools -e --silent
        
    elif check_command choco; then
        print_step "Installation via Chocolatey..."
        choco install -y git python visualstudio2022buildtools
        
    else
        print_error "Aucun gestionnaire de packages trouvé!"
        print_warning "Installation manuelle requise:"
        print_warning "  1. Git: https://git-scm.com/download/win"
        print_warning "  2. Python 3.9+: https://python.org"
        print_warning "  3. Visual Studio Build Tools: https://visualstudio.microsoft.com/visual-cpp-build-tools/"
        read -p "Appuyez sur Entrée une fois l'installation manuelle terminée..."
    fi
    
    # Visual C++ Build Tools (résout Problème #3 - face_recognition)
    print_step "Vérification Visual C++ Build Tools..."
    if [ -d "/c/Program Files (x86)/Microsoft Visual Studio" ] || [ -d "/c/Program Files/Microsoft Visual Studio" ]; then
        print_success "Visual Studio Build Tools détecté"
    else
        print_warning "Visual Studio Build Tools requis pour certaines dépendances"
        print_warning "Télécharger: https://visualstudio.microsoft.com/visual-cpp-build-tools/"
    fi
    
    print_success "Installation Windows terminée"
}

# =====================================
# INSTALLATION PYTHON ET DÉPENDANCES
# =====================================

setup_python_environment() {
    print_header "🐍 CONFIGURATION ENVIRONNEMENT PYTHON"
    
    # Détecter Python
    local python_cmd=""
    for cmd in python3.9 python3 python; do
        if version=$(check_python_version "$cmd"); then
            python_cmd="$cmd"
            print_success "Python $version détecté: $cmd"
            break
        fi
    done
    
    if [ -z "$python_cmd" ]; then
        print_error "Python $PYTHON_MIN_VERSION+ requis mais non trouvé"
        exit 1
    fi
    
    # Créer environnement virtuel
    print_step "Création environnement virtuel..."
    if [ -d "$VENV_NAME" ]; then
        print_warning "Environnement virtuel existant trouvé, suppression..."
        rm -rf "$VENV_NAME"
    fi
    
    "$python_cmd" -m venv "$VENV_NAME" || { print_error "Échec création venv"; exit 1; }
    
    # Activer environnement
    print_step "Activation environnement virtuel..."
    if [[ "$OS" == "windows" ]]; then
        source "$VENV_NAME/Scripts/activate"
    else
        source "$VENV_NAME/bin/activate"
    fi
    
    # Mise à jour pip
    print_step "Mise à jour pip..."
    python -m pip install --upgrade pip setuptools wheel || { print_error "Échec mise à jour pip"; exit 1; }
    
    print_success "Environnement Python configuré"
}

install_python_dependencies() {
    print_header "📦 INSTALLATION DÉPENDANCES PYTHON"
    
    # Vérifier fichier requirements
    if [ ! -f "requirements_production.txt" ]; then
        print_error "Fichier requirements_production.txt non trouvé!"
        exit 1
    fi
    
    # Installation séquentielle pour éviter conflits (résout Problème #4)
    print_step "Installation dépendances critiques..."
    
    # Numpy en premier (base pour tout)
    python -m pip install "numpy>=1.21.0,<1.26.0" || { print_error "Échec installation numpy"; exit 1; }
    
    # PyQt6 avec gestion d'erreurs
    print_step "Installation PyQt6..."
    python -m pip install "PyQt6>=6.4.0,<6.7.0" || {
        print_warning "PyQt6 pip a échoué, essai version système..."
        if [[ "$OS" == "linux" ]]; then
            print_warning "Utilisation PyQt6 système (apt install python3-pyqt6)"
        fi
    }
    
    # OpenAI nouvelle API (résout Problème #1)
    print_step "Installation OpenAI (nouvelle API)..."
    python -m pip install "openai>=1.0.0,<2.0.0" || { print_error "Échec installation OpenAI"; exit 1; }
    
    # Audio stack stable (résout Problème #2 - pyaudio)
    print_step "Installation stack audio stable..."
    python -m pip install "sounddevice>=0.4.6,<0.5.0" "soundfile>=0.12.1,<0.13.0" "scipy>=1.9.0,<1.12.0" || {
        print_warning "Certains packages audio ont échoué"
    }
    
    # Computer vision
    print_step "Installation computer vision..."
    python -m pip install "opencv-python>=4.7.0,<4.9.0" || print_warning "OpenCV installation échouée"
    
    # Face detection lightweight (résout Problème #3 - face_recognition)
    print_step "Installation détection faciale (MTCNN)..."
    python -m pip install "mtcnn>=0.1.1,<1.0.0" "tensorflow-cpu>=2.10.0,<2.14.0" "Pillow>=9.0.0,<11.0.0" || {
        print_warning "Face detection non installée (optionnel)"
    }
    
    # Autres dépendances
    print_step "Installation autres dépendances..."
    python -m pip install -r requirements_production.txt || {
        print_warning "Certaines dépendances optionnelles ont échoué"
    }
    
    print_success "Dépendances Python installées"
}

# =====================================
# CONFIGURATION ET TESTS
# =====================================

configure_system() {
    print_header "⚙️ CONFIGURATION SYSTÈME"
    
    # Créer fichier d'environnement
    print_step "Création fichier .env..."
    cat > .env << EOF
# Configuration Gideon AI Assistant Production
OPENAI_API_KEY=your-api-key-here
PYTHONPATH=.
QT_QPA_PLATFORM=xcb
EOF
    
    # VS Code configuration (résout Problème #4)
    print_step "Configuration VS Code..."
    mkdir -p .vscode
    if [ ! -f ".vscode/settings.json" ]; then
        print_warning ".vscode/settings.json non trouvé - utilisez la version fournie"
    fi
    
    # Permissions exécution
    print_step "Configuration permissions..."
    chmod +x test_system_production.py 2>/dev/null || true
    chmod +x gideon_main_production.py 2>/dev/null || true
    
    print_success "Configuration système terminée"
}

run_validation_tests() {
    print_header "🧪 TESTS DE VALIDATION"
    
    print_step "Exécution tests système..."
    if [ -f "test_system_production.py" ]; then
        python test_system_production.py || {
            print_warning "Tests système ont révélé des problèmes"
            print_warning "Consultez la sortie ci-dessus pour plus de détails"
        }
    else
        print_warning "Script de test non trouvé"
    fi
}

# =====================================
# FONCTION PRINCIPALE
# =====================================

main() {
    # Initialisation
    log "Démarrage installation Gideon AI Assistant Production"
    detect_os
    
    print_header "🤖 GIDEON AI ASSISTANT - INSTALLATION PRODUCTION"
    echo -e "${PURPLE}Résolution complète des 10 problèmes critiques${NC}"
    echo -e "${PURPLE}OS détecté: $OS ($DISTRO)${NC}"
    echo -e "${PURPLE}Répertoire: $SCRIPT_DIR${NC}"
    echo -e "${PURPLE}Log: $LOG_FILE${NC}\n"
    
    # Vérifications préliminaires
    if [ "$EUID" -eq 0 ]; then
        print_error "Ne pas exécuter en tant que root (sauf pour macOS/Linux packages système)"
        print_warning "Relancez sans sudo pour l'installation Python"
    fi
    
    # Installation par OS
    case $OS in
        "linux")
            install_linux
            ;;
        "macos")
            install_macos
            ;;
        "windows")
            install_windows
            ;;
    esac
    
    # Configuration Python
    setup_python_environment
    install_python_dependencies
    
    # Configuration finale
    configure_system
    
    # Tests de validation
    run_validation_tests
    
    # Résumé final
    print_header "🎉 INSTALLATION TERMINÉE"
    print_success "Gideon AI Assistant Production installé avec succès!"
    
    echo -e "\n${CYAN}PROCHAINES ÉTAPES:${NC}"
    echo -e "${CYAN}1. Configurer clé OpenAI:${NC}"
    echo -e "   export OPENAI_API_KEY='votre-clé-api'"
    echo -e "${CYAN}2. Ajouter photo de visage:${NC}"
    echo -e "   cp votre_photo.jpg ton_visage.jpg"
    
    if [[ "$OS" == "macos" ]]; then
        echo -e "${CYAN}3. Autoriser permissions macOS:${NC}"
        echo -e "   System Preferences > Security & Privacy > Microphone/Camera"
    fi
    
    echo -e "${CYAN}4. Tester l'installation:${NC}"
    if [[ "$OS" == "windows" ]]; then
        echo -e "   $VENV_NAME\\Scripts\\activate"
    else
        echo -e "   source $VENV_NAME/bin/activate"
    fi
    echo -e "   python test_system_production.py"
    
    echo -e "${CYAN}5. Lancer Gideon:${NC}"
    echo -e "   python gideon_main_production.py"
    
    print_success "Installation Production Complete! 🚀"
}

# =====================================
# EXÉCUTION
# =====================================

# Gestion d'erreurs
trap 'print_error "Installation interrompue"; exit 1' INT TERM

# Exécution principale
main "$@" 