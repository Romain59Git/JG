# 🔧 Installation Guide - Gideon AI Assistant

This comprehensive guide will help you install and configure Gideon AI Assistant on your system.

## 📋 System Requirements

### Minimum Requirements
- **Python 3.8+** (3.9+ recommended)
- **4GB RAM** (8GB recommended)
- **2GB free disk space**
- **Microphone** (built-in or external)
- **Webcam** (for face recognition)
- **Internet connection** (for OpenAI API)

### Operating System Support
- ✅ **Windows 10/11** (tested)
- ✅ **macOS 10.15+** (tested)
- ✅ **Linux Ubuntu 20.04+** (tested)
- ✅ **Linux Debian 11+** (tested)
- ⚠️ **Other Linux distributions** (should work with minor adjustments)

## 🐍 Python Installation

### Windows
1. Download Python from [python.org](https://python.org)
2. **Important**: Check "Add Python to PATH" during installation
3. Verify installation:
   ```cmd
   python --version
   pip --version
   ```

### macOS
```bash
# Using Homebrew (recommended)
brew install python@3.9

# Or download from python.org
```

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

## 📦 Dependency Installation

### 1. System Dependencies

#### Windows
```cmd
# Usually no additional system dependencies needed
# Windows users can skip to step 2
```

#### macOS
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required packages
brew install portaudio qt6 cmake
```

#### Linux (Ubuntu/Debian)
```bash
# Audio dependencies
sudo apt-get install libasound2-dev portaudio19-dev

# Qt6 dependencies
sudo apt-get install qt6-base-dev qt6-multimedia-dev

# OpenCV dependencies
sudo apt-get install libopencv-dev python3-opencv

# Face recognition dependencies
sudo apt-get install build-essential cmake libopenblas-dev liblapack-dev libx11-dev libgtk-3-dev

# Additional libraries
sudo apt-get install espeak espeak-data libespeak1 libespeak-dev
```

#### Linux (CentOS/RHEL/Fedora)
```bash
# For Fedora/CentOS/RHEL users
sudo dnf install alsa-lib-devel portaudio-devel qt6-qtbase-devel cmake gcc-c++ openblas-devel
```

### 2. Project Setup

#### Clone Repository
```bash
git clone https://github.com/yourusername/gideon-ai-assistant.git
cd gideon-ai-assistant
```

#### Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate

# Verify activation (should show (venv) in prompt)
which python  # Should point to venv/bin/python
```

#### Install Python Dependencies
```bash
# Upgrade pip first
pip install --upgrade pip

# Install core dependencies
pip install -r requirements.txt
```

### 3. Troubleshooting Dependency Issues

#### PyAudio Installation Issues

**Windows:**
```cmd
# If pip install fails, try pre-compiled wheel
pip install pipwin
pipwin install pyaudio
```

**macOS:**
```bash
# If homebrew installation of portaudio didn't work
brew reinstall portaudio
pip install pyaudio
```

**Linux:**
```bash
# If pyaudio compilation fails
sudo apt-get install python3-pyaudio
# or
pip install --global-option='build_ext' --global-option='-I/usr/local/include' --global-option='-L/usr/local/lib' pyaudio
```

#### Face Recognition Issues

**All Platforms:**
```bash
# If face_recognition fails to install
pip install cmake dlib
pip install face_recognition
```

**Linux specific:**
```bash
# If dlib compilation fails
sudo apt-get install build-essential cmake pkg-config
sudo apt-get install libx11-dev libatlas-base-dev
sudo apt-get install libgtk-3-dev libboost-python-dev
```

#### PyQt6 Issues

**Linux:**
```bash
# If PyQt6 installation fails
sudo apt-get install python3-pyqt6
# or try:
pip install PyQt6 --no-cache-dir
```

**macOS:**
```bash
# If Qt6 not found
brew install qt6
export PATH="/opt/homebrew/opt/qt@6/bin:$PATH"
pip install PyQt6
```

## 🔑 API Configuration

### OpenAI API Setup

1. **Create OpenAI Account**
   - Visit [platform.openai.com](https://platform.openai.com)
   - Sign up or log in
   - Navigate to API Keys section

2. **Generate API Key**
   - Click "Create new secret key"
   - Copy the key (starts with `sk-`)
   - **Important**: Store it securely

3. **Configure Gideon**
   
   **Method 1: Environment Variable (Recommended)**
   ```bash
   # Add to your shell profile (.bashrc, .zshrc, etc.)
   export OPENAI_API_KEY="sk-your-actual-api-key-here"
   
   # Or set for current session
   # Windows:
   set OPENAI_API_KEY=sk-your-actual-api-key-here
   
   # macOS/Linux:
   export OPENAI_API_KEY="sk-your-actual-api-key-here"
   ```
   
   **Method 2: Configuration File**
   ```python
   # Edit config.py
   # Find the line:
   OPENAI_API_KEY = "your-key-here"
   # Replace with your actual key
   ```

## 👤 Face Recognition Setup

### 1. Prepare Face Photo
- **Take a clear photo** of your face
- **Good lighting** is essential
- **Face should be centered** and clearly visible
- **Supported formats**: JPG, PNG
- **Recommended size**: 500x500 pixels or larger

### 2. Setup Face Photo
```bash
# Save your face photo as 'ton_visage.jpg' in project root
cp /path/to/your/face/photo.jpg ton_visage.jpg

# Verify the file exists
ls -la ton_visage.jpg
```

### 3. Test Face Recognition
```bash
python -c "
import face_recognition
import cv2

# Test if photo loads correctly
image = face_recognition.load_image_file('ton_visage.jpg')
encodings = face_recognition.face_encodings(image)

if encodings:
    print('✅ Face detected successfully!')
    print(f'Found {len(encodings)} face(s)')
else:
    print('❌ No face detected. Please use a clearer photo.')
"
```

## 🏠 Smart Home Configuration (Optional)

### Philips Hue Setup

1. **Ensure Hue Bridge is connected** to your network
2. **Find bridge IP address**
   ```bash
   # Method 1: Check router admin panel
   # Method 2: Use discovery
   curl https://discovery.meethue.com/
   ```

3. **Bridge Authentication**
   - Gideon will automatically discover and authenticate
   - When prompted, **press the button on your Hue bridge**
   - Authentication happens during first smart home discovery

## 🚀 First Launch

### 1. Test Installation
```bash
# Activate virtual environment if not already active
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Test core components
python -c "
import sys
print('✅ Python:', sys.version)

try:
    import PyQt6
    print('✅ PyQt6: Available')
except ImportError:
    print('❌ PyQt6: Missing')

try:
    import openai
    print('✅ OpenAI: Available')
except ImportError:
    print('❌ OpenAI: Missing')

try:
    import face_recognition
    print('✅ Face Recognition: Available')
except ImportError:
    print('❌ Face Recognition: Missing')

try:
    import cv2
    print('✅ OpenCV: Available')
except ImportError:
    print('❌ OpenCV: Missing')

try:
    import pyaudio
    print('✅ PyAudio: Available')
except ImportError:
    print('❌ PyAudio: Missing')
"
```

### 2. Launch Gideon
```bash
python gideon_main.py
```

### 3. First Launch Checklist
- [ ] **System tray icon** appears
- [ ] **Welcome message** is spoken
- [ ] **Tray notification** shows hotkey instructions
- [ ] **Press F12** to test overlay
- [ ] **Right-click tray icon** to access menu

## 🔧 Post-Installation Configuration

### 1. Audio Device Configuration
```bash
# List available audio devices
python -c "
import pyaudio
pa = pyaudio.PyAudio()
print('Available audio devices:')
for i in range(pa.get_device_count()):
    info = pa.get_device_info_by_index(i)
    print(f'{i}: {info[\"name\"]} - {info[\"maxInputChannels\"]} inputs')
pa.terminate()
"
```

### 2. Voice Recognition Test
1. Click **"Authenticate"** in system tray menu
2. Look at camera when prompted
3. If authenticated, try voice commands:
   - "Hello Gideon"
   - "What time is it?"
   - "Show overlay"

### 3. Smart Home Discovery
1. Right-click tray icon
2. Select **"Smart Home Discovery"**
3. Press Hue bridge button if prompted
4. Test with: "Turn on all lights"

## 🛠️ Development Setup (Optional)

### For Contributors and Developers

#### Additional Development Dependencies
```bash
# Install development tools
pip install black flake8 pytest mypy

# Install pre-commit hooks
pip install pre-commit
pre-commit install
```

#### IDE Configuration

**VS Code:**
```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black"
}
```

**PyCharm:**
- Set interpreter to `venv/bin/python`
- Configure code style to use Black formatter

## ❓ Common Installation Issues

### Issue: "No module named 'PyQt6'"
```bash
# Solution 1: Reinstall PyQt6
pip uninstall PyQt6
pip install PyQt6

# Solution 2: Install from different source
pip install PyQt6 --no-cache-dir

# Solution 3: Use system package (Linux)
sudo apt-get install python3-pyqt6
```

### Issue: "Microsoft Visual C++ 14.0 is required" (Windows)
```bash
# Install Microsoft C++ Build Tools
# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
# Or install Visual Studio Community Edition
```

### Issue: Face recognition crashes
```bash
# Ensure proper dependencies
pip install cmake
pip install dlib
pip install face_recognition

# Verify face photo is correct format
file ton_visage.jpg  # Should show: JPEG image data
```

### Issue: Audio device not found
```bash
# Windows: Check Windows audio settings
# macOS: Check System Preferences > Sound
# Linux: Check PulseAudio/ALSA configuration

# Test microphone access
python -c "
import pyaudio
import wave

pa = pyaudio.PyAudio()
stream = pa.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
print('Recording for 2 seconds...')
data = stream.read(44100 * 2)
print('✅ Audio recording successful')
stream.close()
pa.terminate()
"
```

## 🎯 Verification Checklist

After installation, verify these features work:

- [ ] **Application starts** without errors
- [ ] **System tray icon** is visible
- [ ] **F12 toggles overlay** interface
- [ ] **Face authentication** works
- [ ] **Voice recognition** detects speech
- [ ] **Text-to-speech** output is audible
- [ ] **Audio visualizer** shows activity
- [ ] **Smart home discovery** runs (if applicable)
- [ ] **System monitoring** displays CPU/memory
- [ ] **Application closes** gracefully

## 📞 Getting Help

If you encounter issues:

1. **Check logs**: Look for `gideon.log` in project directory
2. **Enable debug mode**: Set `DEBUG = True` in `config.py`
3. **Test individual components**: Use the test commands above
4. **Check GitHub Issues**: Search existing issues
5. **Create new issue**: Include logs and system information

**System Information Template:**
```
OS: [Windows 10/macOS Big Sur/Ubuntu 20.04]
Python Version: [3.9.x]
Hardware: [CPU, RAM, etc.]
Error Message: [Full error text]
Steps to Reproduce: [What you did when error occurred]
```

---

**Installation complete! 🎉 Welcome to the future with Gideon AI Assistant.** 