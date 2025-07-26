#!/bin/bash

# Jarvis AI Assistant - Script de démarrage
# Version fonctionnelle corrigée

echo "🚀 Démarrage de Jarvis AI Assistant..."
echo "========================================"

# Couleurs pour l'affichage
GREEN='\033[0;32m'
YELLOW='\033[1;33m' 
RED='\033[0;31m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
log_info() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Vérification de l'environnement Python
check_python() {
    if command -v python3 &> /dev/null; then
        log_info "Python3 trouvé"
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        log_info "Python trouvé"
        PYTHON_CMD="python"
    else
        log_error "Python non trouvé. Veuillez installer Python 3.9+"
        exit 1
    fi
}

# Vérification de l'environnement virtuel
check_venv() {
    if [ -d "venv_gideon_production" ]; then
        log_info "Environnement virtuel trouvé: venv_gideon_production"
        VENV_PATH="venv_gideon_production"
    elif [ -d "venv_jarvis_local" ]; then
        log_info "Environnement virtuel trouvé: venv_jarvis_local"
        VENV_PATH="venv_jarvis_local"
    else
        log_warning "Aucun environnement virtuel trouvé"
        log_warning "Tentative d'exécution avec Python système..."
        VENV_PATH=""
    fi
}

# Activation de l'environnement virtuel
activate_venv() {
    if [ -n "$VENV_PATH" ]; then
        log_info "Activation de l'environnement virtuel..."
        source "$VENV_PATH/bin/activate"
        
        if [ $? -eq 0 ]; then
            log_info "Environnement virtuel activé"
        else
            log_error "Échec d'activation de l'environnement virtuel"
            exit 1
        fi
    fi
}

# Test de fonctionnement de Jarvis
test_jarvis() {
    log_info "Test de Jarvis..."
    
    if [ -f "test_main.py" ]; then
        $PYTHON_CMD test_main.py > /dev/null 2>&1
        
        if [ $? -eq 0 ]; then
            log_info "Jarvis testé avec succès"
            return 0
        else
            log_warning "Tests partiels - Jarvis fonctionne avec limitations"
            return 1
        fi
    else
        log_warning "Fichier de test non trouvé, démarrage direct"
        return 1
    fi
}

# Démarrage de Jarvis
start_jarvis() {
    echo ""
    echo "🤖 Quelle interface souhaitez-vous utiliser ?"
    echo "1. Interface graphique (GUI) - Recommandé"
    echo "2. Interface en ligne de commande (CLI)"
    echo "3. Test rapide uniquement"
    echo ""
    
    read -p "Votre choix (1/2/3): " choice
    
    case $choice in
        1)
            log_info "Démarrage en mode GUI..."
            $PYTHON_CMD main.py
            ;;
        2)
            log_info "Démarrage en mode CLI..."
            $PYTHON_CMD main.py --cli
            ;;
        3)
            log_info "Exécution du test rapide..."
            if [ -f "test_main.py" ]; then
                $PYTHON_CMD test_main.py
            else
                log_error "Fichier de test non trouvé"
            fi
            ;;
        *)
            log_warning "Choix invalide, démarrage en mode GUI par défaut..."
            $PYTHON_CMD main.py
            ;;
    esac
}

# Gestion des erreurs
handle_error() {
    echo ""
    log_error "Erreur lors du démarrage de Jarvis"
    echo ""
    echo "🔧 Solutions possibles :"
    echo "1. Vérifiez que vous êtes dans le bon répertoire"
    echo "2. Assurez-vous que Python 3.9+ est installé"
    echo "3. Vérifiez l'environnement virtuel"
    echo "4. Exécutez: pip install -r requirements.txt"
    echo ""
    echo "Pour plus d'aide, consultez README.md"
    exit 1
}

# Script principal
main() {
    # Vérifications préliminaires
    check_python
    check_venv
    
    # Activation de l'environnement
    activate_venv
    
    # Test optionnel
    if test_jarvis; then
        log_info "Système validé, démarrage de Jarvis..."
    else
        log_warning "Validation partielle, tentative de démarrage..."
    fi
    
    # Démarrage
    start_jarvis
}

# Gestion du signal d'interruption (Ctrl+C)
trap 'echo ""; log_warning "Arrêt demandé par l'utilisateur"; exit 0' INT

# Gestion des erreurs
trap 'handle_error' ERR

# Exécution du script principal
main "$@" 