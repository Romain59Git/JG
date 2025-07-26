#!/bin/bash
# ===============================================
# GIDEON AI ASSISTANT - SYSTEM DEPENDENCIES
# Automatic installation script for all OS
# ===============================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]]; then
    OS="windows"
else
    echo -e "${RED}❌ Unsupported OS: $OSTYPE${NC}"
    exit 1
fi

echo -e "${GREEN}🤖 GIDEON AI ASSISTANT - SYSTEM SETUP${NC}"
echo -e "${YELLOW}Detected OS: $OS${NC}"

# Linux Installation
install_linux() {
    echo -e "${YELLOW}📦 Installing Linux dependencies...${NC}"
    
    # Update package list
    sudo apt update
    
    # Essential build tools
    sudo apt install -y \
        python3-dev \
        python3-pip \
        python3-venv \
        build-essential \
        cmake \
        pkg-config \
        git
    
    # Audio dependencies (CRITICAL)
    echo -e "${YELLOW}🎵 Installing audio dependencies...${NC}"
    sudo apt install -y \
        libasound2-dev \
        portaudio19-dev \
        pulseaudio \
        alsa-utils \
        libportaudio2
    
    # Try Qt6 (may fail on older systems)
    echo -e "${YELLOW}🖥️ Installing Qt6 (may require manual intervention)...${NC}"
    sudo apt install -y qt6-base-dev qt6-multimedia-dev || {
        echo -e "${YELLOW}⚠️ Qt6 system package failed, will use pip version${NC}"
    }
    
    # OpenCV dependencies
    echo -e "${YELLOW}👁️ Installing OpenCV dependencies...${NC}"
    sudo apt install -y \
        libopencv-dev \
        python3-opencv
    
    # Text-to-speech
    sudo apt install -y \
        espeak \
        espeak-data \
        libespeak1 \
        libespeak-dev
    
    # Add user to audio group
    sudo usermod -a -G audio $USER
    
    echo -e "${GREEN}✅ Linux dependencies installed${NC}"
    echo -e "${YELLOW}⚠️ Please REBOOT to apply audio group changes${NC}"
}

# macOS Installation  
install_macos() {
    echo -e "${YELLOW}📦 Installing macOS dependencies...${NC}"
    
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo -e "${YELLOW}🍺 Installing Homebrew...${NC}"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    # Update Homebrew
    brew update
    
    # Install dependencies
    echo -e "${YELLOW}🔧 Installing core dependencies...${NC}"
    brew install \
        python@3.9 \
        cmake \
        portaudio \
        qt6 \
        pkg-config \
        opencv
    
    # Add Qt6 to PATH
    echo 'export PATH="/opt/homebrew/opt/qt@6/bin:$PATH"' >> ~/.zshrc
    export PATH="/opt/homebrew/opt/qt@6/bin:$PATH"
    
    echo -e "${GREEN}✅ macOS dependencies installed${NC}"
    echo -e "${YELLOW}⚠️ Please grant microphone/camera permissions in System Preferences${NC}"
}

# Windows Installation (via package managers)
install_windows() {
    echo -e "${YELLOW}📦 Windows dependency check...${NC}"
    
    # Check for winget
    if command -v winget &> /dev/null; then
        echo -e "${YELLOW}📦 Installing via winget...${NC}"
        winget install Git.Git
        winget install Python.Python.3
    elif command -v choco &> /dev/null; then
        echo -e "${YELLOW}🍫 Installing via Chocolatey...${NC}"
        choco install git python
    else
        echo -e "${RED}❌ No package manager found${NC}"
        echo -e "${YELLOW}Please install manually:${NC}"
        echo "1. Git: https://git-scm.com/download/win"
        echo "2. Python 3.8+: https://python.org"
        echo "3. Visual Studio Build Tools: https://visualstudio.microsoft.com/visual-cpp-build-tools/"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Windows setup complete${NC}"
    echo -e "${YELLOW}⚠️ May need Visual Studio Build Tools for compilation${NC}"
}

# Main installation
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

echo -e "${GREEN}🎉 System dependencies installation complete!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Clone the Gideon repository"
echo "2. Create Python virtual environment"
echo "3. Install Python dependencies"
echo "4. Configure OpenAI API key"
echo "5. Run: python gideon_main.py" 