"""
Event System for Gideon AI Assistant
Handles communication between modules
"""

import threading
from typing import Dict, List, Callable, Any
from collections import defaultdict

class EventSystem:
    """Event system for inter-module communication"""
    
    def __init__(self):
        self._listeners = defaultdict(list)
        self._lock = threading.Lock()
    
    def subscribe(self, event_type: str, callback: Callable[[Any], None]):
        """Subscribe to an event type"""
        with self._lock:
            self._listeners[event_type].append(callback)
    
    def unsubscribe(self, event_type: str, callback: Callable[[Any], None]):
        """Unsubscribe from an event type"""
        with self._lock:
            if event_type in self._listeners:
                try:
                    self._listeners[event_type].remove(callback)
                except ValueError:
                    pass  # Callback not found
    
    def emit(self, event_type: str, data: Any = None):
        """Emit an event to all subscribers"""
        with self._lock:
            listeners = self._listeners[event_type].copy()
        
        for callback in listeners:
            try:
                callback(data)
            except Exception as e:
                print(f"Error in event callback: {e}")
    
    def get_listener_count(self, event_type: str) -> int:
        """Get number of listeners for an event type"""
        with self._lock:
            return len(self._listeners[event_type])
    
    def clear_all(self):
        """Clear all event listeners"""
        with self._lock:
            self._listeners.clear() 