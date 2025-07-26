#!/usr/bin/env python3
"""
Gideon AI Assistant - Main Application
Futuristic AI assistant with desktop overlay interface
"""

import sys
import signal
import threading
import time
from typing import Optional

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QIcon, QPixmap, QAction

from config import config
from core import GideonCore, GideonLogger
from ui import GideonOverlay
from modules import SmartHomeModule

class GideonApplication:
    """
    Main Gideon AI Assistant application
    Manages the core system, UI overlay, and modules
    """
    
    def __init__(self):
        self.logger = GideonLogger("GideonApp")
        self.logger.log_system_info()
        
        # Initialize Qt Application
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Gideon AI Assistant")
        self.app.setApplicationVersion("1.0.0")
        self.app.setQuitOnLastWindowClosed(False)
        
        # Core components
        self.gideon_core: Optional[GideonCore] = None
        self.overlay: Optional[GideonOverlay] = None
        self.tray_icon: Optional[QSystemTrayIcon] = None
        
        # Modules
        self.smart_home: Optional[SmartHomeModule] = None
        
        # Background tasks
        self.voice_processing_timer: Optional[QTimer] = None
        
        # System state
        self.is_running = False
        self.is_shutting_down = False
        
        self.logger.info("Gideon application initialized")
    
    def initialize(self) -> bool:
        """
        Initialize all components
        
        Returns:
            True if initialization successful
        """
        try:
            # Initialize core
            self.logger.info("Initializing Gideon Core...")
            self.gideon_core = GideonCore()
            
            # Initialize modules
            self.logger.info("Initializing modules...")
            self.smart_home = SmartHomeModule()
            
            # Connect module events
            self._connect_module_events()
            
            # Initialize UI overlay
            self.logger.info("Initializing UI overlay...")
            self.overlay = GideonOverlay(self.gideon_core)
            
            # Setup system tray
            self._setup_system_tray()
            
            # Setup background tasks
            self._setup_background_tasks()
            
            # Setup signal handlers
            self._setup_signal_handlers()
            
            self.logger.info("Gideon initialization complete")
            return True
            
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            return False
    
    def _connect_module_events(self):
        """Connect module events to core system"""
        if self.smart_home:
            # Connect smart home events
            self.gideon_core.event_system.subscribe(
                'system_command', 
                self._handle_system_command
            )
            
            self.gideon_core.event_system.subscribe(
                'voice_command',
                self._handle_voice_command
            )
    
    def _setup_system_tray(self):
        """Setup system tray icon and menu"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.logger.warning("System tray not available")
            return
        
        # Create tray icon
        self.tray_icon = QSystemTrayIcon(self.app)
        
        # Create icon (use text-based icon for now)
        pixmap = QPixmap(32, 32)
        pixmap.fill()
        self.tray_icon.setIcon(QIcon(pixmap))
        
        # Create tray menu
        tray_menu = QMenu()
        
        # Show/Hide overlay action
        toggle_action = QAction("Toggle Overlay", self.app)
        toggle_action.triggered.connect(self._toggle_overlay)
        tray_menu.addAction(toggle_action)
        
        # Authentication action
        auth_action = QAction("Authenticate", self.app)
        auth_action.triggered.connect(self._authenticate_user)
        tray_menu.addAction(auth_action)
        
        tray_menu.addSeparator()
        
        # Module actions
        smart_home_action = QAction("Smart Home Discovery", self.app)
        smart_home_action.triggered.connect(self._discover_smart_home)
        tray_menu.addAction(smart_home_action)
        
        tray_menu.addSeparator()
        
        # Quit action
        quit_action = QAction("Quit Gideon", self.app)
        quit_action.triggered.connect(self.shutdown)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.setToolTip("Gideon AI Assistant")
        
        # Connect tray icon signals
        self.tray_icon.activated.connect(self._tray_icon_activated)
        
        # Show tray icon
        self.tray_icon.show()
        
        self.logger.info("System tray setup complete")
    
    def _setup_background_tasks(self):
        """Setup background processing tasks"""
        # Voice command processing timer
        self.voice_processing_timer = QTimer()
        self.voice_processing_timer.timeout.connect(self._process_voice_commands)
        self.voice_processing_timer.start(100)  # Check every 100ms
        
        self.logger.info("Background tasks setup complete")
    
    def _setup_signal_handlers(self):
        """Setup system signal handlers for graceful shutdown"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Handle Qt application quit
        self.app.aboutToQuit.connect(self.shutdown)
    
    def _signal_handler(self, signum, frame):
        """Handle system signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()
    
    def run(self) -> int:
        """
        Run the main application loop
        
        Returns:
            Application exit code
        """
        if not self.initialize():
            self.logger.error("Failed to initialize application")
            return 1
        
        self.is_running = True
        self.logger.info("Starting Gideon AI Assistant...")
        
        # Show welcome message
        self._show_welcome_message()
        
        # Start voice recognition if user is authenticated
        if config.system.AUTO_START:
            self._auto_start_sequence()
        
        # Run Qt application
        try:
            exit_code = self.app.exec()
            self.logger.info(f"Application exited with code {exit_code}")
            return exit_code
            
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
            return 0
        except Exception as e:
            self.logger.error(f"Application error: {e}")
            return 1
        finally:
            self.shutdown()
    
    def _show_welcome_message(self):
        """Show welcome message and instructions"""
        if self.tray_icon:
            self.tray_icon.showMessage(
                "Gideon AI Assistant",
                f"Press {config.system.HOTKEY_TOGGLE} to toggle overlay\nRight-click tray icon for options",
                QSystemTrayIcon.MessageIcon.Information,
                3000
            )
        
        # Speak welcome if TTS is available
        if self.gideon_core:
            self.gideon_core.speak(
                "Gideon AI Assistant is now running. Press F12 to toggle the overlay interface."
            )
    
    def _auto_start_sequence(self):
        """Auto-start sequence if enabled"""
        def auto_start():
            time.sleep(2)  # Wait for everything to initialize
            
            # Attempt authentication
            if self.gideon_core.authenticate_user():
                # Start continuous listening
                self.gideon_core.start_continuous_listening()
                
                # Discover smart home devices
                if self.smart_home:
                    self.smart_home.discover_devices()
        
        threading.Thread(target=auto_start, daemon=True).start()
    
    def _process_voice_commands(self):
        """Process voice commands from queue"""
        if not self.gideon_core or not self.is_running:
            return
        
        # Get voice command from queue
        command = self.gideon_core.get_next_voice_command(timeout=0.1)
        if command:
            self.logger.info(f"Processing voice command: {command.text}")
            
            # Process with appropriate module
            response = self._route_voice_command(command.text)
            
            # Speak response
            if response:
                self.gideon_core.speak(response)
    
    def _route_voice_command(self, command_text: str) -> str:
        """
        Route voice command to appropriate module
        
        Args:
            command_text: Voice command text
            
        Returns:
            Response text
        """
        command_lower = command_text.lower()
        
        # Smart home commands
        if any(word in command_lower for word in [
            "light", "lights", "lamp", "scene", "temperature", "thermostat", "heating"
        ]):
            if self.smart_home:
                return self.smart_home.process_voice_command(command_text)
            else:
                return "Smart home module not available"
        
        # System commands
        elif any(phrase in command_lower for phrase in [
            "show overlay", "hide overlay", "toggle overlay"
        ]):
            if "show" in command_lower:
                self._show_overlay()
                return "Showing overlay"
            elif "hide" in command_lower:
                self._hide_overlay()
                return "Hiding overlay"
            else:
                self._toggle_overlay()
                return "Toggling overlay"
        
        elif "authenticate" in command_lower or "login" in command_lower:
            self._authenticate_user_async()
            return "Starting authentication"
        
        elif "discover devices" in command_lower or "find devices" in command_lower:
            self._discover_smart_home_async()
            return "Starting device discovery"
        
        # Default to AI response
        else:
            return self.gideon_core.generate_ai_response(command_text)
    
    # UI Control Methods
    def _toggle_overlay(self):
        """Toggle overlay visibility"""
        if self.overlay:
            self.overlay.toggle_overlay()
    
    def _show_overlay(self):
        """Show overlay"""
        if self.overlay:
            self.overlay.show_overlay()
    
    def _hide_overlay(self):
        """Hide overlay"""
        if self.overlay:
            self.overlay.hide_overlay()
    
    def _authenticate_user(self):
        """Authenticate user (synchronous)"""
        if self.gideon_core:
            self.gideon_core.authenticate_user()
    
    def _authenticate_user_async(self):
        """Authenticate user (asynchronous)"""
        def auth_thread():
            self._authenticate_user()
        
        threading.Thread(target=auth_thread, daemon=True).start()
    
    def _discover_smart_home(self):
        """Discover smart home devices"""
        if self.smart_home:
            success = self.smart_home.discover_devices()
            if success:
                self.gideon_core.speak("Smart home devices discovered successfully")
            else:
                self.gideon_core.speak("No smart home devices found")
    
    def _discover_smart_home_async(self):
        """Discover smart home devices (asynchronous)"""
        def discovery_thread():
            self._discover_smart_home()
        
        threading.Thread(target=discovery_thread, daemon=True).start()
    
    # Event Handlers
    def _handle_system_command(self, data):
        """Handle system command events"""
        action = data.get('action')
        
        if action == 'open_vscode':
            import subprocess
            try:
                subprocess.Popen(["code"])
                self.logger.info("Opened Visual Studio Code")
            except Exception as e:
                self.logger.error(f"Failed to open VS Code: {e}")
    
    def _handle_voice_command(self, data):
        """Handle voice command events"""
        command = data.get('command')
        if command:
            # Route to appropriate module
            response = self._route_voice_command(command.text)
            if response and response != command.text:  # Avoid echoing
                self.gideon_core.speak(response)
    
    def _tray_icon_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._toggle_overlay()
    
    def shutdown(self):
        """Graceful shutdown of all components"""
        if self.is_shutting_down:
            return
        
        self.is_shutting_down = True
        self.is_running = False
        
        self.logger.info("Starting graceful shutdown...")
        
        # Stop background tasks
        if self.voice_processing_timer:
            self.voice_processing_timer.stop()
        
        # Hide overlay
        if self.overlay:
            self.overlay.hide_overlay()
        
        # Shutdown core
        if self.gideon_core:
            self.gideon_core.shutdown()
        
        # Hide tray icon
        if self.tray_icon:
            self.tray_icon.hide()
        
        # Quit application
        if self.app:
            self.app.quit()
        
        self.logger.info("Gideon shutdown complete")

def main():
    """Main entry point"""
    try:
        # Create and run application
        gideon_app = GideonApplication()
        return gideon_app.run()
        
    except Exception as e:
        print(f"Fatal error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 