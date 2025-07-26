"""
Configuration settings for Jarvis/Gideon AI Assistant
MIGRATED TO 100% LOCAL SOLUTION
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
        self.DATA_DIR = self.BASE_DIR / "data"
        self.MODELS_DIR = self.DATA_DIR / "models"
        self.MEMORY_DB_DIR = self.DATA_DIR / "memory_db"
        self.CONVERSATIONS_DIR = self.DATA_DIR / "conversations"
        
        # Ensure directories exist
        for directory in [self.LOGS_DIR, self.ASSETS_DIR, self.DATA_DIR,
                          self.MODELS_DIR, self.MEMORY_DB_DIR,
                          self.CONVERSATIONS_DIR]:
            directory.mkdir(exist_ok=True)



class LocalAIConfig:
    """Local AI configuration - 100% OFFLINE"""
    
    # Ollama Configuration (LLM Local)
    OLLAMA_HOST = "http://localhost:11434"
    DEFAULT_MODEL = "mistral:7b"
    ALTERNATIVE_MODELS = ["llama3:8b", "phi3:mini", "codellama:7b"]
    
    # Model settings optimisés
    MAX_TOKENS = 2048
    TEMPERATURE = 0.7
    TIMEOUT = 10  # Timeout Ollama
    
    # System prompt Jarvis optimisé
    SYSTEM_PROMPT = """Tu es Jarvis, l'assistant IA personnel futuriste inspiré
    d'Iron Man et de Gideon de Flash. Tu es intelligent, efficace et toujours
    prêt à aider. Tu fonctionnes entièrement en local pour garantir la
    confidentialité. Réponds de manière concise mais complète. Tu peux
    contrôler des systèmes, répondre à des questions et avoir des 
    conversations naturelles."""
    
    # Context management local
    MAX_CONTEXT_LENGTH = 4000  # Tokens de contexte
    CONVERSATION_MEMORY_LIMIT = 50  # Nombre d'échanges gardés en mémoire


class AudioConfig:
    """Audio-related configuration - ENHANCED LOCAL"""
    
    # TTS Settings optimisés
    TTS_RATE = 200
    TTS_VOLUME = 0.8
    TTS_VOICE_ID = None  # Auto-detect best voice
    
    # Speech Recognition local optimisé
    VOICE_RECOGNITION_LANGUAGE = "en-US"
    ALTERNATIVE_LANGUAGES = ["fr-FR", "en-GB"]
    
    # Audio processing - OPTIMISÉ
    SAMPLE_RATE = 16000  # Optimal pour reconnaissance vocale
    CHANNELS = 1  # Mono pour performance
    CHUNK_SIZE = 1024
    
    # Wake word detection avancée
    ACTIVATION_KEYWORDS = ["jarvis", "gideon", "hey jarvis", "hey gideon",
                          "computer"]
    WAKE_WORD_THRESHOLD = 0.75
    WAKE_WORD_TIMEOUT = 5.0
    
    # Audio thresholds macOS optimisés
    ENERGY_THRESHOLD = 300
    DYNAMIC_ENERGY_THRESHOLD = True
    PAUSE_THRESHOLD = 0.8
    PHRASE_TIME_LIMIT = 10.0
    TIMEOUT = 5.0
    
    # Continuous listening
    LISTEN_TIMEOUT = 1.0
    PHRASE_TIMEOUT = 2.0
    MIC_TIMEOUT = 5.0


class VisionConfig:
    """Vision and face recognition configuration - LOCAL ONLY"""
    
    # Face recognition files
    USER_REFERENCE_IMAGE = "data/user_reference.jpg"
    FACE_CASCADE_PATH = "data/models/haarcascade_frontalface_default.xml"
    
    # Detection settings
    CONFIDENCE_THRESHOLD = 0.85
    FACE_RECOGNITION_THRESHOLD = 0.6
    
    # Performance settings
    FRAME_SKIP = 3  # Process every 3rd frame
    MAX_DETECTION_TIME = 2.0
    CAMERA_RESOLUTION = (640, 480)
    
    # Face detection optimization
    MIN_FACE_SIZE = (30, 30)
    SCALE_FACTOR = 1.1
    MIN_NEIGHBORS = 5

class MemoryConfig:
    """Local memory and knowledge base configuration"""
    
    # ChromaDB settings
    CHROMADB_PATH = "data/memory_db"
    COLLECTION_NAME = "jarvis_memory"
    
    # Embedding model (local)
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Sentence transformers local
    EMBEDDING_DIMENSION = 384
    
    # Memory management
    MAX_CONVERSATION_HISTORY = 1000
    MAX_MEMORY_ENTRIES = 10000
    SIMILARITY_THRESHOLD = 0.75
    
    # Context retrieval
    MAX_RELEVANT_MEMORIES = 5
    MEMORY_DECAY_FACTOR = 0.95  # Importance décroit avec le temps
    
    # Conversation persistence
    SAVE_CONVERSATIONS = True
    CONVERSATION_BATCH_SIZE = 10

class CommandsConfig:
    """Local system commands configuration - macOS"""
    
    # Available command categories
    ENABLED_COMMANDS = [
        "file_operations",
        "application_control", 
        "system_info",
        "media_control",
        "network_tools",
        "automation"
    ]
    
    # File operations
    SEARCH_LOCATIONS = [
        "~/Desktop",
        "~/Documents", 
        "~/Downloads",
        "~/Applications"
    ]
    
    # Application shortcuts
    COMMON_APPS = {
        "browser": ["Safari", "Chrome", "Firefox"],
        "editor": ["TextEdit", "VSCode", "Sublime"],
        "media": ["Music", "Photos", "QuickTime"],
        "system": ["Activity Monitor", "System Preferences"]
    }
    
    # System monitoring
    MONITOR_RESOURCES = True
    RESOURCE_CHECK_INTERVAL = 30  # seconds

class UIConfig:
    """UI configuration - ENHANCED"""
    
    # Window settings
    OVERLAY_OPACITY = 0.92
    WINDOW_WIDTH = 500
    WINDOW_HEIGHT = 400
    
    # Colors - Jarvis theme futuriste
    PRIMARY_COLOR = "#1a237e"    # Bleu profond
    SECONDARY_COLOR = "#0d47a1"  # Bleu électrique
    ACCENT_COLOR = "#00e676"     # Vert Matrix
    TEXT_COLOR = "#ffffff"
    SUCCESS_COLOR = "#4caf50"
    WARNING_COLOR = "#ff9800"
    ERROR_COLOR = "#f44336"
    
    # Animation et performance
    ANIMATION_DURATION = 250
    FPS_TARGET = 60
    VISUALIZATION_BARS = 32
    
    # Interface modes
    SHOW_DEBUG_PANEL = True
    SHOW_SYSTEM_TRAY = True
    MINIMIZE_TO_TRAY = True

class SystemConfig:
    """System configuration - PRODUCTION READY"""
    
    # Environment
    DEBUG = os.getenv('JARVIS_DEBUG', 'false').lower() == 'true'
    LOG_LEVEL = "INFO" if not DEBUG else "DEBUG"
    LOG_FILE = "logs/jarvis.log"
    LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # Memory management strict
    MEMORY_LIMIT_MB = 300  # Limite stricte
    MEMORY_CHECK_INTERVAL = 15  # Plus fréquent
    MEMORY_WARNING_THRESHOLD = 250
    MEMORY_CRITICAL_THRESHOLD = 280
    
    # Performance monitoring
    ENABLE_METRICS = True
    METRICS_INTERVAL = 30
    
    # Health monitoring
    HEALTH_CHECK_INTERVAL = 60
    AUTO_RECOVERY = True
    MAX_RESTART_ATTEMPTS = 3
    
    # Hotkeys et contrôles
    TOGGLE_HOTKEY = "F12"
    EMERGENCY_STOP = "F11"
    
    # Startup behavior
    AUTO_START_LISTENING = True
    AUTO_CALIBRATE_AUDIO = True
    LOAD_PREVIOUS_CONTEXT = True

# Global config instances avec nouvelle structure
config = Config()
config.ai = LocalAIConfig()
config.audio = AudioConfig()
config.vision = VisionConfig()
config.memory = MemoryConfig()
config.commands = CommandsConfig()
config.ui = UIConfig()
config.system = SystemConfig()

# Backward compatibility aliases
config.face_recognition = config.vision  # Alias pour l'ancien code 