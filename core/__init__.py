"""
Core module for Gideon AI Assistant
Contains base classes and core functionality
"""

from .assistant_core_production import GideonCoreProduction
from .event_system import EventSystem
from .logger import GideonLogger

__all__ = ['GideonCoreProduction', 'EventSystem', 'GideonLogger'] 