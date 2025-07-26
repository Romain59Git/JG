#!/bin/bash

# Jarvis/Gideon AI Assistant - Installation Script 100% LOCAL
# Optimized for macOS Apple M4 + Python 3.12
# This script sets up a completely local AI assistant

set -e  # Exit on any error

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              🤖 JARVIS LOCAL AI INSTALLATION                 ║"
echo "║                100% AUTONOMOUS ASSISTANT                     ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running on macOS
check_macos() {
    if [[ "$OSTYPE" != "darwin"* ]]; then
        log_error "This script is optimized for macOS. Exiting."
        exit 1
    fi
    log_success "macOS detected"
}

# Check if Homebrew is installed
check_homebrew() {
    log_info "Checking Homebrew installation..."
    
    if ! command -v brew &> /dev/null; then
        log_warning "Homebrew not found. Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # Add Homebrew to PATH for Apple Silicon
        if [[ $(uname -m) == "arm64" ]]; then
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zshrc
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi
    else
        log_success "Homebrew is installed"
    fi
}

# Install system dependencies
install_system_deps() {
    log_info "Installing system dependencies..."
    
    # Audio dependencies
    brew install portaudio
    
    # Computer vision dependencies
    brew install cmake
    
    # Python build dependencies
    brew install python@3.12
    
    log_success "System dependencies installed"
}

# Install Ollama for local LLM
install_ollama() {
    log_info "Installing Ollama for local LLM..."
    
    if ! command -v ollama &> /dev/null; then
        brew install ollama
        log_success "Ollama installed"
    else
        log_success "Ollama already installed"
    fi
    
    # Start Ollama service
    log_info "Starting Ollama service..."
    ollama serve &
    sleep 5
    
    # Download recommended models
    log_info "Downloading AI models (this may take a while)..."
    
    ollama pull mistral:7b || log_warning "Failed to download Mistral 7B"
    ollama pull llama3:8b || log_warning "Failed to download LLaMA3 8B"
    ollama pull phi3:mini || log_warning "Failed to download Phi3 Mini"
    
    log_success "Ollama setup completed"
}

# Create Python virtual environment
setup_python_env() {
    log_info "Setting up Python virtual environment..."
    
    # Create virtual environment
    python3.12 -m venv venv_jarvis_local
    
    # Activate virtual environment
    source venv_jarvis_local/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip setuptools wheel
    
    log_success "Python environment created"
}

# Install Python dependencies
install_python_deps() {
    log_info "Installing Python dependencies..."
    
    # Activate virtual environment
    source venv_jarvis_local/bin/activate
    
    # Install PyTorch first (Apple Silicon optimized)
    if [[ $(uname -m) == "arm64" ]]; then
        pip install torch torchvision torchaudio
    else
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
    fi
    
    # Install main requirements
    pip install -r requirements.txt
    
    # Handle potential dlib issues on Apple Silicon
    if [[ $(uname -m) == "arm64" ]]; then
        log_info "Installing dlib for Apple Silicon..."
        brew install dlib
        pip install dlib --no-cache-dir
    fi
    
    log_success "Python dependencies installed"
}

# Download required models and data
download_models() {
    log_info "Downloading required models..."
    
    # Create models directory
    mkdir -p data/models
    
    # Download OpenCV cascade files
    if [ ! -f "data/models/haarcascade_frontalface_default.xml" ]; then
        curl -o data/models/haarcascade_frontalface_default.xml \
             https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml
    fi
    
    log_success "Models downloaded"
}

# Create configuration files
setup_config() {
    log_info "Setting up configuration..."
    
    # Create data directories
    mkdir -p data/{memory_db,conversations,models}
    mkdir -p logs
    
    # Create environment file
    cat > .env << EOF
# Jarvis Local AI Assistant Environment
JARVIS_DEBUG=false
JARVIS_LOCAL_MODE=true
OLLAMA_HOST=http://localhost:11434
EOF
    
    log_success "Configuration completed"
}

# Test installation
test_installation() {
    log_info "Testing installation..."
    
    # Activate environment
    source venv_jarvis_local/bin/activate
    
    # Test Python imports
    python3 -c "
import sys
print('Testing Python imports...')

try:
    import torch
    print('✅ PyTorch: OK')
except ImportError as e:
    print(f'❌ PyTorch: {e}')

try:
    import cv2
    print('✅ OpenCV: OK')
except ImportError as e:
    print(f'❌ OpenCV: {e}')

try:
    import requests
    print('✅ Requests: OK')
except ImportError as e:
    print(f'❌ Requests: {e}')

try:
    import chromadb
    print('✅ ChromaDB: OK')
except ImportError as e:
    print(f'❌ ChromaDB: {e}')

try:
    import sentence_transformers
    print('✅ Sentence Transformers: OK')
except ImportError as e:
    print(f'❌ Sentence Transformers: {e}')

print('Python testing completed.')
"
    
    # Test Ollama connection
    if curl -s http://localhost:11434/api/tags > /dev/null; then
        log_success "Ollama connection: OK"
    else
        log_warning "Ollama connection: Failed (make sure ollama serve is running)"
    fi
    
    log_success "Installation test completed"
}

# Create startup scripts
create_startup_scripts() {
    log_info "Creating startup scripts..."
    
    # Create main startup script
    cat > start_jarvis_local.sh << 'EOF'
#!/bin/bash

# Jarvis Local AI Assistant Startup Script

echo "🚀 Starting Jarvis Local AI Assistant..."

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "📡 Starting Ollama service..."
    ollama serve &
    sleep 5
fi

# Activate Python environment
source venv_jarvis_local/bin/activate

# Start Jarvis
echo "🤖 Launching Jarvis..."
python main.py
EOF
    
    chmod +x start_jarvis_local.sh
    
    # Create CLI startup script
    cat > start_jarvis_cli.sh << 'EOF'
#!/bin/bash

# Jarvis CLI Mode Startup Script

echo "🖥️ Starting Jarvis in CLI mode..."

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "📡 Starting Ollama service..."
    ollama serve &
    sleep 5
fi

# Activate Python environment
source venv_jarvis_local/bin/activate

# Start Jarvis in CLI mode
python main.py --cli
EOF
    
    chmod +x start_jarvis_cli.sh
    
    log_success "Startup scripts created"
}

# Show final instructions
show_final_instructions() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                   🎉 INSTALLATION COMPLETE!                 ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    log_success "Jarvis Local AI Assistant is ready!"
    echo ""
    echo "📋 NEXT STEPS:"
    echo ""
    echo "1. 🚀 Start Jarvis GUI mode:"
    echo "   ./start_jarvis_local.sh"
    echo ""
    echo "2. 🖥️ Start Jarvis CLI mode:"
    echo "   ./start_jarvis_cli.sh"
    echo ""
    echo "3. 🎤 For voice recognition, make sure your microphone is working"
    echo ""
    echo "4. 👁️ For face recognition, run this to capture your reference image:"
    echo "   source venv_jarvis_local/bin/activate"
    echo "   python -c \"from modules.vision_local import vision_manager; vision_manager.capture_reference_image()\""
    echo ""
    echo "📚 FEATURES AVAILABLE:"
    echo "• 🧠 Local LLM with Ollama (Mistral, LLaMA3)"
    echo "• 🎤 Speech recognition & synthesis"
    echo "• 👁️ Computer vision & face recognition"
    echo "• 🗃️ Vector memory with ChromaDB"
    echo "• ⚙️ System commands for macOS"
    echo "• 💻 Modern PyQt6 interface"
    echo ""
    echo "🆘 TROUBLESHOOTING:"
    echo "• If Ollama fails: brew services restart ollama"
    echo "• If audio fails: Check microphone permissions in System Preferences"
    echo "• If PyQt6 fails: pip install PyQt6 --no-cache-dir"
    echo ""
    echo "✨ Enjoy your fully local AI assistant!"
}

# Main installation flow
main() {
    log_info "Starting Jarvis Local AI installation..."
    
    check_macos
    check_homebrew
    install_system_deps
    install_ollama
    setup_python_env
    install_python_deps
    download_models
    setup_config
    test_installation
    create_startup_scripts
    show_final_instructions
    
    log_success "Installation completed successfully!"
}

# Run main function
main "$@" 