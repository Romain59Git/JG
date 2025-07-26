"""
Configuration settings for Gideon AI Assistant
"""

import os
from pathlib import Path

class Config:
    """Main configuration class"""
    
    def __init__(self):
        # Paths
        self.BASE_DIR = Path(__file__).parent
        self.LOGS_DIR = self.BASE_DIR / "logs"
        self.ASSETS_DIR = self.BASE_DIR / "assets"
        
        # Ensure directories exist
        self.LOGS_DIR.mkdir(exist_ok=True)
        self.ASSETS_DIR.mkdir(exist_ok=True)

class AIConfig:
    """AI-related configuration"""
    
    # OpenAI Configuration - VRAIE CLÉ API
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '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')
    
    # Model settings
    MODEL = "gpt-3.5-turbo"
    MAX_TOKENS = 150
    TEMPERATURE = 0.7
    
    # System prompt
    SYSTEM_PROMPT = "You are Gideon, a helpful AI assistant inspired by the Flash TV series. Be concise, friendly, and professional."

class AudioConfig:
    """Audio-related configuration"""
    
    # TTS Settings
    TTS_RATE = 200
    TTS_VOLUME = 0.9
    
    # Speech Recognition
    VOICE_RECOGNITION_LANGUAGE = "en-US"
    
    # Audio processing
    SAMPLE_RATE = 44100
    CHANNELS = 1
    CHUNK_SIZE = 1024

class UIConfig:
    """UI-related configuration"""
    
    # Window settings
    OVERLAY_OPACITY = 0.9
    WINDOW_WIDTH = 800
    WINDOW_HEIGHT = 600
    
    # Colors (Gideon theme)
    PRIMARY_COLOR = "#1a237e"
    SECONDARY_COLOR = "#0d47a1"
    ACCENT_COLOR = "#424242"
    TEXT_COLOR = "#ffffff"
    
    # Animation
    ANIMATION_DURATION = 300
    FPS_TARGET = 60

class FaceRecognitionConfig:
    """Face recognition configuration"""
    
    USER_PHOTO_PATH = "ton_visage.jpg"
    CONFIDENCE_THRESHOLD = 0.9
    
    # MTCNN settings
    MIN_FACE_SIZE = 20
    SCALE_FACTOR = 0.709
    STEPS_THRESHOLD = [0.6, 0.7, 0.7]

class SystemConfig:
    """System-related configuration"""
    
    DEBUG = True
    LOG_LEVEL = "INFO"
    LOG_FILE = "logs/gideon.log"
    
    # Memory management
    MEMORY_LIMIT_MB = 200
    MEMORY_CHECK_INTERVAL = 30  # seconds
    
    # Hotkeys
    TOGGLE_HOTKEY = "F12"

# Global config instances
config = Config()
config.ai = AIConfig()
config.audio = AudioConfig()
config.ui = UIConfig()
config.face_recognition = FaceRecognitionConfig()
config.system = SystemConfig() 