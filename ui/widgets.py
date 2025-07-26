"""
Modular widgets for Gideon overlay interface
Reusable UI components with consistent styling
"""

import psutil
import time
from typing import Optional
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from config import config

class StatusWidget(QWidget):
    """Status indicator widget showing system state"""
    
    def __init__(self, gideon_core, parent=None):
        super().__init__(parent)
        self.gideon_core = gideon_core
        self._setup_ui()
        self._setup_timer()
        
    def _setup_ui(self):
        """Setup status indicators"""
        layout = QHBoxLayout(self)
        layout.setSpacing(10)
        
        # AI Status
        self.ai_indicator = self._create_indicator("AI", config.colors.SUCCESS)
        layout.addWidget(QLabel("AI:"))
        layout.addWidget(self.ai_indicator)
        
        # Voice Status  
        self.voice_indicator = self._create_indicator("Voice", config.colors.SECONDARY_DARK)
        layout.addWidget(QLabel("Voice:"))
        layout.addWidget(self.voice_indicator)
        
        # Auth Status
        self.auth_indicator = self._create_indicator("Auth", config.colors.SECONDARY_DARK)
        layout.addWidget(QLabel("Auth:"))
        layout.addWidget(self.auth_indicator)
        
    def _create_indicator(self, name: str, color: str) -> QWidget:
        """Create a status indicator circle"""
        indicator = QWidget()
        indicator.setFixedSize(20, 20)
        indicator.setStyleSheet(f"""
            QWidget {{
                background-color: {color};
                border-radius: 10px;
                border: 1px solid {config.colors.TEXT_SECONDARY};
            }}
        """)
        return indicator
        
    def _setup_timer(self):
        """Setup update timer"""
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_status)
        self.timer.start(1000)  # Update every second
        
    def _update_status(self):
        """Update status indicators"""
        # Voice status
        if self.gideon_core.is_listening:
            self._set_indicator_color(self.voice_indicator, config.colors.ACCENT_BLUE)
        elif self.gideon_core.is_speaking:
            self._set_indicator_color(self.voice_indicator, config.colors.ACCENT_GREEN)
        else:
            self._set_indicator_color(self.voice_indicator, config.colors.SECONDARY_DARK)
            
        # Auth status
        if self.gideon_core.is_authenticated:
            self._set_indicator_color(self.auth_indicator, config.colors.SUCCESS)
        else:
            self._set_indicator_color(self.auth_indicator, config.colors.ERROR)
            
    def _set_indicator_color(self, indicator: QWidget, color: str):
        """Update indicator color"""
        indicator.setStyleSheet(f"""
            QWidget {{
                background-color: {color};
                border-radius: 10px;
                border: 1px solid {config.colors.TEXT_SECONDARY};
            }}
        """)

class QuickActionsWidget(QWidget):
    """Quick action buttons widget"""
    
    def __init__(self, gideon_core, parent=None):
        super().__init__(parent)
        self.gideon_core = gideon_core
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup quick action buttons"""
        layout = QHBoxLayout(self)
        layout.setSpacing(5)
        
        # Auth button
        self.auth_btn = QPushButton("🔒")
        self.auth_btn.setObjectName("gideon-button")
        self.auth_btn.setFixedSize(40, 40)
        self.auth_btn.setToolTip("Authenticate")
        self.auth_btn.clicked.connect(self._authenticate)
        
        # Settings button
        self.settings_btn = QPushButton("⚙️")
        self.settings_btn.setObjectName("gideon-button")
        self.settings_btn.setFixedSize(40, 40)
        self.settings_btn.setToolTip("Settings")
        self.settings_btn.clicked.connect(self._open_settings)
        
        # Minimize button
        self.minimize_btn = QPushButton("➖")
        self.minimize_btn.setObjectName("gideon-button")
        self.minimize_btn.setFixedSize(40, 40)
        self.minimize_btn.setToolTip("Hide Overlay")
        self.minimize_btn.clicked.connect(self._minimize)
        
        layout.addWidget(self.auth_btn)
        layout.addWidget(self.settings_btn)
        layout.addWidget(self.minimize_btn)
        
    def _authenticate(self):
        """Trigger authentication"""
        def auth_thread():
            self.gideon_core.authenticate_user()
            
        import threading
        threading.Thread(target=auth_thread, daemon=True).start()
        
    def _open_settings(self):
        """Open settings dialog"""
        # TODO: Implement settings dialog
        self.gideon_core.speak("Settings interface not yet implemented")
        
    def _minimize(self):
        """Minimize overlay"""
        parent = self.parent()
        while parent and not hasattr(parent, 'hide_overlay'):
            parent = parent.parent()
        if parent:
            parent.hide_overlay()

class SystemInfoWidget(QWidget):
    """System information display widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._setup_timer()
        
    def _setup_ui(self):
        """Setup system info display"""
        self.setObjectName("gideon-panel")
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("SYSTEM STATUS")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"""
            QLabel {{
                font-weight: bold;
                color: {config.colors.ACCENT_BLUE};
                padding: 5px;
                font-size: 14px;
            }}
        """)
        layout.addWidget(title)
        
        # CPU Usage
        self.cpu_label = QLabel("CPU: 0%")
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setStyleSheet(self._get_progress_style())
        layout.addWidget(self.cpu_label)
        layout.addWidget(self.cpu_bar)
        
        # Memory Usage
        self.memory_label = QLabel("Memory: 0%")
        self.memory_bar = QProgressBar()
        self.memory_bar.setStyleSheet(self._get_progress_style())
        layout.addWidget(self.memory_label)
        layout.addWidget(self.memory_bar)
        
        # Network indicator
        self.network_label = QLabel("Network: Checking...")
        layout.addWidget(self.network_label)
        
        # Time display
        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet(f"""
            QLabel {{
                color: {config.colors.TEXT_PRIMARY};
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
            }}
        """)
        layout.addWidget(self.time_label)
        
        layout.addStretch()
        
    def _get_progress_style(self) -> str:
        """Get progress bar stylesheet"""
        return f"""
            QProgressBar {{
                border: 1px solid {config.colors.SECONDARY_DARK};
                border-radius: 4px;
                text-align: center;
                color: {config.colors.TEXT_PRIMARY};
                background-color: {config.colors.BACKGROUND_LIGHT};
            }}
            QProgressBar::chunk {{
                background-color: {config.colors.PRIMARY_DARK};
                border-radius: 3px;
            }}
        """
        
    def _setup_timer(self):
        """Setup update timer"""
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_info)
        self.timer.start(2000)  # Update every 2 seconds
        self._update_info()  # Initial update
        
    def _update_info(self):
        """Update system information"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=None)
            self.cpu_label.setText(f"CPU: {cpu_percent:.1f}%")
            self.cpu_bar.setValue(int(cpu_percent))
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            self.memory_label.setText(f"Memory: {memory_percent:.1f}%")
            self.memory_bar.setValue(int(memory_percent))
            
            # Network (simplified check)
            try:
                network_stats = psutil.net_io_counters()
                self.network_label.setText("Network: Connected")
                self.network_label.setStyleSheet(f"color: {config.colors.SUCCESS};")
            except:
                self.network_label.setText("Network: Disconnected")
                self.network_label.setStyleSheet(f"color: {config.colors.ERROR};")
            
            # Current time
            current_time = time.strftime("%H:%M:%S")
            current_date = time.strftime("%Y-%m-%d")
            self.time_label.setText(f"{current_time}\n{current_date}")
            
        except Exception as e:
            print(f"System info update error: {e}")

class ModuleWidget(QWidget):
    """Base class for module-specific widgets"""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self._setup_base_ui()
        
    def _setup_base_ui(self):
        """Setup base widget structure"""
        self.setObjectName("gideon-panel")
        
        self.main_layout = QVBoxLayout(self)
        
        # Title bar
        title_bar = QWidget()
        title_layout = QHBoxLayout(title_bar)
        
        title_label = QLabel(self.title)
        title_label.setStyleSheet(f"""
            QLabel {{
                font-weight: bold;
                color: {config.colors.ACCENT_BLUE};
                font-size: 14px;
            }}
        """)
        
        close_btn = QPushButton("✕")
        close_btn.setObjectName("gideon-button")
        close_btn.setFixedSize(25, 25)
        close_btn.clicked.connect(self.close)
        
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(close_btn)
        
        self.main_layout.addWidget(title_bar)
        
        # Content area
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.main_layout.addWidget(self.content_widget)
        
    def add_content(self, widget: QWidget):
        """Add content to the module widget"""
        self.content_layout.addWidget(widget) 