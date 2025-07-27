"""
Core module for Gideon AI Assistant
Updated imports for production version with French audio
"""

from .logger import GideonLogger
from .event_system import EventSystem
from .memory_monitor import MemoryMonitor
from .assistant_core_production import AssistantCore
from .audio_manager_optimized import EnhancedAudioManager as AudioManager

__all__ = [
    'GideonLogger',
    'EventSystem', 
    'MemoryMonitor',
    'AssistantCore',
    'AudioManager'
] 