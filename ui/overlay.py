"""
Main overlay interface for Gideon AI Assistant
Futuristic desktop overlay with transparency and animations
"""

import sys
import math
import time
from typing import Dict, List, Optional
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from config import config
from core import GideonCore, EventSystem
from .widgets import StatusWidget, QuickActionsWidget, SystemInfoWidget
from .audio_visualizer import AudioVisualizer

class GideonOverlay(QMainWindow):
    """
    Main overlay window with Gideon-inspired design
    Semi-transparent overlay that can be toggled with F12
    """
    
    def __init__(self, gideon_core: GideonCore):
        super().__init__()
        self.gideon_core = gideon_core
        self.event_system = gideon_core.event_system
        
        # Window state
        self.is_visible = False
        self.is_animated = False
        self.widgets: Dict[str, QWidget] = {}
        
        # Animation properties
        self.opacity_effect = QGraphicsOpacityEffect()
        self.scale_animation = QPropertyAnimation(self, b"geometry")
        self.opacity_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        
        self._setup_window()
        self._setup_ui()
        self._setup_animations()
        self._setup_shortcuts()
        self._connect_events()
        
        # Start hidden
        self.hide()
        
    def _setup_window(self):
        """Configure window properties for overlay"""
        # Window flags for overlay behavior
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.X11BypassWindowManagerHint
        )
        
        # Make window transparent
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGraphicsEffect(self.opacity_effect)
        
        # Set window properties
        self.setFixedSize(config.ui.WINDOW_WIDTH, config.ui.WINDOW_HEIGHT)
        self._center_window()
        
        # Apply Gideon theme
        self.setStyleSheet(config.get_style_sheet())
        
    def _center_window(self):
        """Center window on screen"""
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
    
    def _setup_ui(self):
        """Setup the main UI layout and widgets"""
        central_widget = QWidget()
        central_widget.setObjectName("gideon-main")
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QGridLayout(central_widget)
        main_layout.setSpacing(config.ui.WIDGET_PADDING)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Create and add widgets
        self._create_header()
        self._create_central_area()
        self._create_side_panels()
        
        # Add widgets to layout
        main_layout.addWidget(self.widgets['header'], 0, 0, 1, 3)
        main_layout.addWidget(self.widgets['left_panel'], 1, 0, 2, 1)
        main_layout.addWidget(self.widgets['central_area'], 1, 1, 1, 1)
        main_layout.addWidget(self.widgets['right_panel'], 1, 2, 2, 1)
        main_layout.addWidget(self.widgets['bottom_panel'], 2, 1, 1, 1)
        
        # Set stretch factors
        main_layout.setRowStretch(1, 1)
        main_layout.setColumnStretch(1, 2)
    
    def _create_header(self):
        """Create header with Gideon branding and status"""
        header = QWidget()
        header.setObjectName("gideon-panel")
        header.setFixedHeight(80)
        
        layout = QHBoxLayout(header)
        
        # Gideon logo/title
        title_label = QLabel("GIDEON AI ASSISTANT")
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 24px;
                font-weight: bold;
                color: {config.colors.ACCENT_BLUE};
                text-align: center;
                padding: 10px;
            }}
        """)
        
        # Status indicator
        status_widget = StatusWidget(self.gideon_core)
        
        # Quick actions
        quick_actions = QuickActionsWidget(self.gideon_core)
        
        layout.addWidget(title_label)
        layout.addStretch()
        layout.addWidget(status_widget)
        layout.addWidget(quick_actions)
        
        self.widgets['header'] = header
    
    def _create_central_area(self):
        """Create central area with audio visualizer"""
        central = QWidget()
        central.setObjectName("gideon-panel")
        
        layout = QVBoxLayout(central)
        
        # Audio visualizer
        self.audio_visualizer = AudioVisualizer()
        self.audio_visualizer.setMinimumSize(400, 400)
        
        # Voice status
        voice_status = QLabel("Voice Assistant Ready")
        voice_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        voice_status.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                color: {config.colors.TEXT_SECONDARY};
                padding: 10px;
            }}
        """)
        
        layout.addWidget(self.audio_visualizer)
        layout.addWidget(voice_status)
        
        self.widgets['central_area'] = central
        self.widgets['voice_status'] = voice_status
    
    def _create_side_panels(self):
        """Create left and right side panels"""
        # Left panel - System info
        left_panel = SystemInfoWidget()
        left_panel.setFixedWidth(250)
        self.widgets['left_panel'] = left_panel
        
        # Right panel - Quick controls
        right_panel = QWidget()
        right_panel.setObjectName("gideon-panel")
        right_panel.setFixedWidth(250)
        
        right_layout = QVBoxLayout(right_panel)
        
        # Module buttons
        modules = [
            ("Smart Home", "🏠"),
            ("Calendar", "📅"), 
            ("Analytics", "📊"),
            ("Media", "🎵"),
            ("Communications", "📧")
        ]
        
        for module_name, icon in modules:
            btn = self._create_module_button(module_name, icon)
            right_layout.addWidget(btn)
        
        right_layout.addStretch()
        self.widgets['right_panel'] = right_panel
        
        # Bottom panel - Command input
        bottom_panel = QWidget()
        bottom_panel.setObjectName("gideon-panel")
        bottom_panel.setFixedHeight(100)
        
        bottom_layout = QHBoxLayout(bottom_panel)
        
        # Command input
        command_input = QLineEdit()
        command_input.setPlaceholderText("Type a command or speak...")
        command_input.setObjectName("gideon-text")
        command_input.returnPressed.connect(self._process_text_command)
        
        # Voice toggle button
        voice_btn = QPushButton("🎤")
        voice_btn.setObjectName("gideon-button")
        voice_btn.setFixedSize(60, 40)
        voice_btn.clicked.connect(self._toggle_voice_listening)
        
        bottom_layout.addWidget(command_input)
        bottom_layout.addWidget(voice_btn)
        
        self.widgets['bottom_panel'] = bottom_panel
        self.widgets['command_input'] = command_input
        self.widgets['voice_btn'] = voice_btn
    
    def _create_module_button(self, name: str, icon: str) -> QPushButton:
        """Create a module activation button"""
        btn = QPushButton(f"{icon} {name}")
        btn.setObjectName("gideon-button")
        btn.setFixedHeight(50)
        btn.clicked.connect(lambda: self._activate_module(name))
        
        # Add hover effects
        btn.enterEvent = lambda e: self._button_hover_enter(btn)
        btn.leaveEvent = lambda e: self._button_hover_leave(btn)
        
        return btn
    
    def _setup_animations(self):
        """Setup animations for smooth transitions"""
        # Scale animation
        self.scale_animation.setDuration(config.ui.ANIMATION_DURATION)
        self.scale_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Opacity animation
        self.opacity_animation.setDuration(config.ui.ANIMATION_DURATION)
        self.opacity_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Animation group
        self.animation_group = QParallelAnimationGroup()
        self.animation_group.addAnimation(self.scale_animation)
        self.animation_group.addAnimation(self.opacity_animation)
    
    def _setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # F12 to toggle overlay
        toggle_shortcut = QShortcut(QKeySequence(config.system.HOTKEY_TOGGLE), self)
        toggle_shortcut.activated.connect(self.toggle_overlay)
        
        # Escape to hide
        hide_shortcut = QShortcut(QKeySequence("Escape"), self)
        hide_shortcut.activated.connect(self.hide_overlay)
    
    def _connect_events(self):
        """Connect to Gideon Core events"""
        self.event_system.subscribe('speech_started', self._on_speech_started)
        self.event_system.subscribe('speech_ended', self._on_speech_ended)
        self.event_system.subscribe('listening_started', self._on_listening_started)
        self.event_system.subscribe('listening_ended', self._on_listening_ended)
        self.event_system.subscribe('voice_command', self._on_voice_command)
    
    def toggle_overlay(self):
        """Toggle overlay visibility with animation"""
        if self.is_animated:
            return
            
        if self.is_visible:
            self.hide_overlay()
        else:
            self.show_overlay()
    
    def show_overlay(self):
        """Show overlay with animation"""
        if self.is_visible or self.is_animated:
            return
            
        self.is_animated = True
        self.show()
        
        # Setup animations
        start_rect = self.geometry()
        end_rect = start_rect
        
        # Scale from center
        center = start_rect.center()
        start_rect.setSize(start_rect.size() * 0.8)
        start_rect.moveCenter(center)
        
        self.scale_animation.setStartValue(start_rect)
        self.scale_animation.setEndValue(end_rect)
        
        self.opacity_animation.setStartValue(0.0)
        self.opacity_animation.setEndValue(config.ui.OVERLAY_OPACITY)
        
        # Connect completion
        self.animation_group.finished.connect(self._on_show_complete)
        
        # Start animations
        self.setGeometry(start_rect)
        self.opacity_effect.setOpacity(0.0)
        self.animation_group.start()
    
    def hide_overlay(self):
        """Hide overlay with animation"""
        if not self.is_visible or self.is_animated:
            return
            
        self.is_animated = True
        
        # Setup animations
        start_rect = self.geometry()
        end_rect = start_rect
        
        # Scale to center
        center = start_rect.center()
        end_rect.setSize(end_rect.size() * 0.8)
        end_rect.moveCenter(center)
        
        self.scale_animation.setStartValue(start_rect)
        self.scale_animation.setEndValue(end_rect)
        
        self.opacity_animation.setStartValue(config.ui.OVERLAY_OPACITY)
        self.opacity_animation.setEndValue(0.0)
        
        # Connect completion
        self.animation_group.finished.connect(self._on_hide_complete)
        
        # Start animations
        self.animation_group.start()
    
    def _on_show_complete(self):
        """Called when show animation completes"""
        self.is_animated = False
        self.is_visible = True
        self.animation_group.finished.disconnect()
        
        # Start audio visualizer
        self.audio_visualizer.start()
    
    def _on_hide_complete(self):
        """Called when hide animation completes"""
        self.is_animated = False
        self.is_visible = False
        self.animation_group.finished.disconnect()
        self.hide()
        
        # Stop audio visualizer
        self.audio_visualizer.stop()
    
    def _button_hover_enter(self, button: QPushButton):
        """Handle button hover enter"""
        button.setStyleSheet(button.styleSheet() + f"""
            QPushButton {{
                border-color: {config.colors.ACCENT_BLUE};
                box-shadow: 0 0 {config.ui.GLOW_INTENSITY}px {config.colors.ACCENT_BLUE};
            }}
        """)
    
    def _button_hover_leave(self, button: QPushButton):
        """Handle button hover leave"""
        button.setStyleSheet("")  # Reset to default
    
    def _process_text_command(self):
        """Process text command from input field"""
        text = self.widgets['command_input'].text().strip()
        if not text:
            return
            
        self.widgets['command_input'].clear()
        
        # Create voice command from text
        from core.assistant_core import VoiceCommand
        command = VoiceCommand(text=text, confidence=1.0, timestamp=time.time())
        
        # Process command
        response = self.gideon_core.process_voice_command(command)
        self.gideon_core.speak(response)
    
    def _toggle_voice_listening(self):
        """Toggle voice listening mode"""
        if self.gideon_core.is_listening:
            self.gideon_core.stop_continuous_listening()
            self.widgets['voice_btn'].setText("🎤")
        else:
            self.gideon_core.start_continuous_listening()
            self.widgets['voice_btn'].setText("🔴")
    
    def _activate_module(self, module_name: str):
        """Activate a module"""
        # TODO: Implement module activation
        self.gideon_core.speak(f"Activating {module_name} module")
    
    # Event handlers
    def _on_speech_started(self, data):
        """Handle speech started event"""
        self.widgets['voice_status'].setText("Speaking...")
        self.widgets['voice_status'].setStyleSheet(f"""
            QLabel {{
                color: {config.colors.ACCENT_GREEN};
                font-weight: bold;
            }}
        """)
        self.audio_visualizer.set_mode('speaking')
    
    def _on_speech_ended(self, data):
        """Handle speech ended event"""
        self.widgets['voice_status'].setText("Voice Assistant Ready")
        self.widgets['voice_status'].setStyleSheet("")
        self.audio_visualizer.set_mode('idle')
    
    def _on_listening_started(self, data):
        """Handle listening started event"""
        self.widgets['voice_status'].setText("Listening...")
        self.widgets['voice_status'].setStyleSheet(f"""
            QLabel {{
                color: {config.colors.ACCENT_BLUE};
                font-weight: bold;
            }}
        """)
        self.audio_visualizer.set_mode('listening')
    
    def _on_listening_ended(self, data):
        """Handle listening ended event"""
        self.widgets['voice_status'].setText("Processing...")
        self.audio_visualizer.set_mode('processing')
    
    def _on_voice_command(self, data):
        """Handle voice command event"""
        command = data['command']
        self.widgets['command_input'].setText(command.text)
        
        # Process command
        response = self.gideon_core.process_voice_command(command)
        self.gideon_core.speak(response)
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Just hide instead of closing
        event.ignore()
        self.hide_overlay() 