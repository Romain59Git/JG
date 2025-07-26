"""
Modules for Gideon AI Assistant
Advanced functionality modules for smart home, calendar, analytics, etc.
"""

from .smart_home import SmartHomeModule
from .calendar_module import CalendarModule  
from .analytics import AnalyticsModule
from .communications import CommunicationsModule
from .multimedia import MultimediaModule

__all__ = [
    'SmartHomeModule',
    'CalendarModule', 
    'AnalyticsModule',
    'CommunicationsModule',
    'MultimediaModule'
] 