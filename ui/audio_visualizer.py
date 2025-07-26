"""
Real-time audio visualizer with circular spectrum display
Gideon-inspired futuristic audio visualization
"""

import math
import numpy as np
import pyaudio
import threading
import time
from typing import Optional, List
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QRadialGradient

from config import config

class AudioAnalyzer(QThread):
    """Audio analysis thread for real-time spectrum data"""
    
    spectrum_data = pyqtSignal(np.ndarray)
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.audio = None
        self.stream = None
        self.mode = 'idle'  # idle, listening, speaking, processing
        
    def start_analysis(self):
        """Start audio analysis"""
        try:
            self.audio = pyaudio.PyAudio()
            self.stream = self.audio.open(
                format=pyaudio.paFloat32,
                channels=config.audio.CHANNELS,
                rate=config.audio.SAMPLE_RATE,
                input=True,
                frames_per_buffer=config.audio.CHUNK_SIZE
            )
            self.running = True
            self.start()
        except Exception as e:
            print(f"Failed to start audio analysis: {e}")
    
    def stop_analysis(self):
        """Stop audio analysis"""
        self.running = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.audio:
            self.audio.terminate()
        self.wait()
    
    def set_mode(self, mode: str):
        """Set visualization mode"""
        self.mode = mode
    
    def run(self):
        """Main analysis loop"""
        while self.running:
            try:
                if self.stream and self.mode in ['listening', 'speaking']:
                    # Read audio data
                    data = self.stream.read(config.audio.CHUNK_SIZE, exception_on_overflow=False)
                    audio_data = np.frombuffer(data, dtype=np.float32)
                    
                    # Compute FFT
                    fft = np.fft.fft(audio_data)
                    magnitude = np.abs(fft[:config.ui.AUDIO_VISUALIZER_BARS])
                    
                    # Normalize
                    if magnitude.max() > 0:
                        magnitude = magnitude / magnitude.max()
                    
                    self.spectrum_data.emit(magnitude)
                else:
                    # Generate fake data for idle/processing modes
                    if self.mode == 'processing':
                        # Pulsing pattern
                        t = time.time()
                        fake_data = np.sin(np.arange(config.ui.AUDIO_VISUALIZER_BARS) * 0.5 + t * 5) * 0.3 + 0.3
                    else:
                        # Low activity for idle
                        fake_data = np.random.random(config.ui.AUDIO_VISUALIZER_BARS) * 0.1
                    
                    self.spectrum_data.emit(fake_data)
                
                time.sleep(1.0 / config.ui.FPS_TARGET)
                
            except Exception as e:
                print(f"Audio analysis error: {e}")
                time.sleep(0.1)

class AudioVisualizer(QWidget):
    """
    Circular audio visualizer widget with Gideon-inspired design
    Real-time spectrum analysis with smooth animations
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Visualization state
        self.spectrum_data = np.zeros(config.ui.AUDIO_VISUALIZER_BARS)
        self.smoothed_data = np.zeros(config.ui.AUDIO_VISUALIZER_BARS)
        self.mode = 'idle'
        
        # Animation properties
        self.rotation_angle = 0.0
        self.pulse_phase = 0.0
        self.smoothing_factor = 0.7
        
        # Audio analyzer
        self.analyzer = AudioAnalyzer()
        self.analyzer.spectrum_data.connect(self.update_spectrum)
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.animate)
        self.update_timer.setInterval(config.system.UPDATE_INTERVAL_MS)
        
        # Styling
        self.setMinimumSize(300, 300)
        self.setStyleSheet("background-color: transparent;")
        
    def start(self):
        """Start audio visualization"""
        self.analyzer.start_analysis()
        self.update_timer.start()
        
    def stop(self):
        """Stop audio visualization"""
        self.update_timer.stop()
        self.analyzer.stop_analysis()
        
    def set_mode(self, mode: str):
        """Set visualization mode"""
        self.mode = mode
        self.analyzer.set_mode(mode)
        
    def update_spectrum(self, data: np.ndarray):
        """Update spectrum data from audio analyzer"""
        self.spectrum_data = data
        
    def animate(self):
        """Animation update loop"""
        # Smooth the spectrum data
        self.smoothed_data = (
            self.smoothing_factor * self.smoothed_data + 
            (1 - self.smoothing_factor) * self.spectrum_data
        )
        
        # Update animation parameters
        self.rotation_angle += 1.0
        self.pulse_phase += 0.1
        
        if self.rotation_angle >= 360:
            self.rotation_angle = 0
            
        self.update()
        
    def paintEvent(self, event):
        """Paint the audio visualizer"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get widget dimensions
        width = self.width()
        height = self.height()
        center_x = width // 2
        center_y = height // 2
        radius = min(width, height) // 2 - 20
        
        # Clear background
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
        
        # Draw based on mode
        if self.mode == 'idle':
            self._draw_idle_pattern(painter, center_x, center_y, radius)
        elif self.mode == 'listening':
            self._draw_listening_pattern(painter, center_x, center_y, radius)
        elif self.mode == 'speaking':
            self._draw_speaking_pattern(painter, center_x, center_y, radius)
        elif self.mode == 'processing':
            self._draw_processing_pattern(painter, center_x, center_y, radius)
            
        # Draw center circle
        self._draw_center_circle(painter, center_x, center_y)
        
    def _draw_idle_pattern(self, painter: QPainter, cx: int, cy: int, radius: int):
        """Draw idle mode pattern"""
        # Subtle pulsing ring
        pulse = math.sin(self.pulse_phase) * 0.3 + 0.7
        
        pen = QPen(QColor(config.colors.PRIMARY_DARK))
        pen.setWidth(2)
        painter.setPen(pen)
        
        ring_radius = int(radius * 0.8 * pulse)
        painter.drawEllipse(cx - ring_radius, cy - ring_radius, ring_radius * 2, ring_radius * 2)
        
    def _draw_listening_pattern(self, painter: QPainter, cx: int, cy: int, radius: int):
        """Draw listening mode pattern with spectrum bars"""
        num_bars = len(self.smoothed_data)
        angle_step = 360.0 / num_bars
        
        for i, magnitude in enumerate(self.smoothed_data):
            angle = math.radians(i * angle_step + self.rotation_angle)
            
            # Calculate bar properties
            inner_radius = radius * 0.6
            bar_height = magnitude * radius * 0.3
            outer_radius = inner_radius + bar_height
            
            # Calculate positions
            x1 = cx + inner_radius * math.cos(angle)
            y1 = cy + inner_radius * math.sin(angle)
            x2 = cx + outer_radius * math.cos(angle)
            y2 = cy + outer_radius * math.sin(angle)
            
            # Color based on magnitude
            alpha = int(255 * (0.3 + magnitude * 0.7))
            color = QColor(config.colors.ACCENT_BLUE)
            color.setAlpha(alpha)
            
            pen = QPen(color)
            pen.setWidth(3)
            painter.setPen(pen)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
            
    def _draw_speaking_pattern(self, painter: QPainter, cx: int, cy: int, radius: int):
        """Draw speaking mode pattern"""
        num_bars = len(self.smoothed_data)
        angle_step = 360.0 / num_bars
        
        for i, magnitude in enumerate(self.smoothed_data):
            angle = math.radians(i * angle_step - self.rotation_angle)  # Reverse direction
            
            # Create wave-like pattern
            wave_offset = math.sin(i * 0.5 + self.pulse_phase * 2) * 20
            inner_radius = radius * 0.5 + wave_offset
            bar_height = magnitude * radius * 0.4
            outer_radius = inner_radius + bar_height
            
            # Calculate positions
            x1 = cx + inner_radius * math.cos(angle)
            y1 = cy + inner_radius * math.sin(angle)
            x2 = cx + outer_radius * math.cos(angle)
            y2 = cy + outer_radius * math.sin(angle)
            
            # Green color for speaking
            alpha = int(255 * (0.4 + magnitude * 0.6))
            color = QColor(config.colors.ACCENT_GREEN)
            color.setAlpha(alpha)
            
            pen = QPen(color)
            pen.setWidth(4)
            painter.setPen(pen)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
            
    def _draw_processing_pattern(self, painter: QPainter, cx: int, cy: int, radius: int):
        """Draw processing mode pattern"""
        # Rotating spiral pattern
        num_points = 64
        angle_step = 720.0 / num_points  # Two full rotations
        
        for i in range(num_points):
            angle = math.radians(i * angle_step + self.rotation_angle * 3)
            spiral_radius = radius * 0.3 + (i / num_points) * radius * 0.4
            
            x = cx + spiral_radius * math.cos(angle)
            y = cy + spiral_radius * math.sin(angle)
            
            # Fade alpha based on position
            alpha = int(255 * (1 - i / num_points) * 0.8)
            color = QColor(config.colors.WARNING)
            color.setAlpha(alpha)
            
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(int(x - 2), int(y - 2), 4, 4)
            
    def _draw_center_circle(self, painter: QPainter, cx: int, cy: int):
        """Draw center indicator circle"""
        # Mode-specific center circle
        mode_colors = {
            'idle': config.colors.SECONDARY_DARK,
            'listening': config.colors.ACCENT_BLUE,
            'speaking': config.colors.ACCENT_GREEN,
            'processing': config.colors.WARNING
        }
        
        color = QColor(mode_colors.get(self.mode, config.colors.SECONDARY_DARK))
        
        # Pulsing effect
        pulse = math.sin(self.pulse_phase * 2) * 0.2 + 0.8
        radius = int(15 * pulse)
        
        # Gradient brush
        gradient = QRadialGradient(cx, cy, radius)
        gradient.setColorAt(0, color)
        color.setAlpha(0)
        gradient.setColorAt(1, color)
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(cx - radius, cy - radius, radius * 2, radius * 2)
        
    def closeEvent(self, event):
        """Handle widget close"""
        self.stop()
        super().closeEvent(event) 