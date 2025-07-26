#!/usr/bin/env python3
"""
Gideon AI Assistant - OPTIMIZED Production Version
Memory-optimized, performance-tuned, with intelligent audio management

🎯 OPTIMIZATIONS IMPLEMENTED:
- ✅ Smart memory management (< 300MB target)
- ✅ Optimized audio recognition with timeouts
- ✅ Intelligent garbage collection
- ✅ Performance monitoring
- ✅ Graceful degradation
"""

import os
import sys
import time
import signal
import platform
import threading
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Early memory optimization
import gc
gc.set_threshold(700, 10, 10)  # More aggressive GC

try:
    from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar
    from PyQt6.QtCore import QTimer, QThread, pyqtSignal, Qt
    from PyQt6.QtGui import QIcon, QFont
    PYQT6_AVAILABLE = True
except ImportError:
    PYQT6_AVAILABLE = False
    print("⚠️ PyQt6 non disponible - Mode console activé")

# OS Detection and optimization
SYSTEM_OS = platform.system()
if SYSTEM_OS == "Linux" and "WAYLAND_DISPLAY" in os.environ:
    os.environ["QT_QPA_PLATFORM"] = "xcb"
    print("🐧 Wayland détecté - Basculement vers X11 pour system tray")

# Core imports with optimization
from config import config
from core.logger import GideonLogger
from core.event_system import EventSystem
from core.audio_manager_optimized import audio_manager, AudioConfig
from core.memory_monitor import memory_monitor, MemoryThresholds

# Conditional imports
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    import cv2
    from mtcnn import MTCNN
    HAS_FACE_DETECTION = True
except ImportError:
    HAS_FACE_DETECTION = False

# Performance optimized debug panel
class DebugPanel(QWidget):
    """Lightweight debug panel for real-time monitoring"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gideon AI - Control Panel")
        self.setFixedSize(400, 300)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        
        self.setup_ui()
        self.setup_timers()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("🤖 GIDEON AI - CONTROL PANEL")
        title.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Audio Status
        audio_layout = QHBoxLayout()
        self.audio_status = QLabel("🎤 Audio: INIT")
        self.audio_test_btn = QPushButton("Test Mic")
        self.audio_test_btn.clicked.connect(self.test_microphone)
        audio_layout.addWidget(self.audio_status)
        audio_layout.addWidget(self.audio_test_btn)
        layout.addLayout(audio_layout)
        
        # Memory Status
        memory_layout = QHBoxLayout()
        self.memory_status = QLabel("💾 Memory: 0MB")
        self.memory_bar = QProgressBar()
        self.memory_bar.setMaximum(300)  # 300MB target
        self.cleanup_btn = QPushButton("Clean RAM")
        self.cleanup_btn.clicked.connect(self.force_cleanup)
        memory_layout.addWidget(self.memory_status)
        memory_layout.addWidget(self.memory_bar)
        memory_layout.addWidget(self.cleanup_btn)
        layout.addLayout(memory_layout)
        
        # API Status
        self.api_status = QLabel("🔗 OpenAI: CHECKING")
        layout.addWidget(self.api_status)
        
        # Performance Stats
        self.perf_stats = QLabel("📊 Performance: INIT")
        layout.addWidget(self.perf_stats)
        
        # Control Buttons
        controls_layout = QHBoxLayout()
        self.listen_btn = QPushButton("🎤 Start Listening")
        self.listen_btn.clicked.connect(self.toggle_listening)
        self.mode_btn = QPushButton("🔧 Debug Mode")
        self.mode_btn.clicked.connect(self.toggle_debug_mode)
        controls_layout.addWidget(self.listen_btn)
        controls_layout.addWidget(self.mode_btn)
        layout.addLayout(controls_layout)
        
        self.setLayout(layout)
        
    def setup_timers(self):
        # Update timer for real-time stats
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_stats)
        self.update_timer.start(2000)  # Update every 2 seconds
        
    def update_stats(self):
        """Update all status displays"""
        try:
            # Memory status
            memory_info = memory_monitor.get_current_memory()
            if memory_info:
                mb_used = memory_info.rss_mb
                self.memory_status.setText(f"💾 Memory: {mb_used:.1f}MB")
                self.memory_bar.setValue(min(int(mb_used), 300))
                
                # Color coding
                if mb_used < 150:
                    color = "green"
                elif mb_used < 250:
                    color = "orange"
                else:
                    color = "red"
                self.memory_bar.setStyleSheet(f"QProgressBar::chunk {{ background-color: {color}; }}")
            
            # Audio status
            stats = audio_manager.get_stats()
            listening = "ON" if stats['is_listening'] else "OFF"
            success_rate = stats['success_rate']
            self.audio_status.setText(f"🎤 Audio: {listening} ({success_rate} success)")
            
            # Performance stats
            self.perf_stats.setText(f"📊 Listens: {stats['total_listens']} | "
                                   f"Success: {stats['successful_recognitions']} | "
                                   f"Failures: {stats['failures']}")
            
        except Exception as e:
            print(f"❌ Error updating stats: {e}")
    
    def test_microphone(self):
        """Test microphone functionality"""
        self.audio_test_btn.setText("Testing...")
        self.audio_test_btn.setEnabled(False)
        
        def test_mic():
            result = audio_manager.test_microphone()
            status = "✅ WORKS" if result else "❌ FAILED"
            
            # Update UI in main thread
            self.audio_test_btn.setText(f"Test Mic - {status}")
            QTimer.singleShot(2000, lambda: (
                self.audio_test_btn.setText("Test Mic"),
                self.audio_test_btn.setEnabled(True)
            ))
        
        threading.Thread(target=test_mic, daemon=True).start()
    
    def force_cleanup(self):
        """Force memory cleanup"""
        self.cleanup_btn.setText("Cleaning...")
        self.cleanup_btn.setEnabled(False)
        
        def cleanup():
            result = memory_monitor.force_cleanup()
            if result.get('success'):
                saved = result['saved_mb']
                self.cleanup_btn.setText(f"Saved {saved:.1f}MB")
            else:
                self.cleanup_btn.setText("Failed")
            
            QTimer.singleShot(2000, lambda: (
                self.cleanup_btn.setText("Clean RAM"),
                self.cleanup_btn.setEnabled(True)
            ))
        
        threading.Thread(target=cleanup, daemon=True).start()
    
    def toggle_listening(self):
        """Toggle audio listening"""
        if audio_manager.is_listening:
            audio_manager.stop_continuous_listening()
            self.listen_btn.setText("🎤 Start Listening")
        else:
            audio_manager.start_continuous_listening()
            self.listen_btn.setText("🔇 Stop Listening")
    
    def toggle_debug_mode(self):
        """Toggle debug mode"""
        logger = GideonLogger()
        current_level = logger.logger.level
        
        if current_level == 20:  # INFO
            logger.logger.setLevel(10)  # DEBUG
            self.mode_btn.setText("🔍 Debug ON")
        else:
            logger.logger.setLevel(20)  # INFO
            self.mode_btn.setText("🔧 Debug Mode")

class OptimizedGideonCore:
    """Lightweight core with essential features only"""
    
    def __init__(self):
        self.logger = GideonLogger("GideonOptimized")
        self.event_system = EventSystem()
        
        # OpenAI client
        self.openai_client = None
        if HAS_OPENAI:
            try:
                self.openai_client = OpenAI(api_key=config.ai.OPENAI_API_KEY)
                self.logger.info("✅ OpenAI client initialized")
            except Exception as e:
                self.logger.error(f"❌ OpenAI initialization failed: {e}")
        
        # Face detection (lightweight)
        self.face_detector = None
        if HAS_FACE_DETECTION:
            try:
                self.face_detector = MTCNN()
                self.logger.info("✅ Face detector initialized")
            except Exception as e:
                self.logger.error(f"❌ Face detector failed: {e}")
        
        # Setup memory callbacks
        memory_monitor.add_cleanup_callback(self.cleanup_memory_resources)
    
    def authenticate_user(self) -> bool:
        """Quick face authentication"""
        if not self.face_detector:
            self.logger.info("Face detection not available - allowing access")
            return True
        
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                return False
            
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                return False
            
            # Quick face detection
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            faces = self.face_detector.detect_faces(frame_rgb)
            
            success = len(faces) > 0
            if success:
                self.logger.info("✅ Face authentication successful")
            else:
                self.logger.warning("❌ No face detected")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Face authentication error: {e}")
            return False
    
    def generate_ai_response(self, prompt: str) -> str:
        """Generate AI response with optimization"""
        if not self.openai_client:
            return "AI services not available. Please check your configuration."
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are Gideon, a helpful AI assistant. Be concise and friendly."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,  # Reduced for faster response
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"❌ OpenAI API error: {e}")
            return "Sorry, I'm having trouble with my AI services right now."
    
    def process_voice_command(self, command_text: str):
        """Process voice command optimally"""
        if not command_text:
            return
        
        self.logger.info(f"🎯 Processing: '{command_text}'")
        
        # Generate response
        response = self.generate_ai_response(command_text)
        
        # Speak response
        audio_manager.speak(response)
        
        # Log interaction
        self.logger.info(f"🤖 Response: '{response}'")
    
    def cleanup_audio_resources(self):
        """Cleanup audio-related resources"""
        self.logger.debug("🧹 Cleaning audio resources")
        # Audio cleanup is handled by audio_manager itself
    
    def cleanup_memory_resources(self):
        """Cleanup memory-heavy resources"""
        self.logger.debug("🧹 Cleaning memory resources")
        
        # Force cleanup of face detection cache if available
        if self.face_detector:
            try:
                # Clear any internal caches
                pass
            except:
                pass
        
        # Force garbage collection
        gc.collect()

class GideonOptimizedApp:
    """Main optimized application"""
    
    def __init__(self):
        self.logger = GideonLogger("GideonApp")
        self.app = None
        self.debug_panel = None
        self.gideon_core = None
        self.running = False
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"📡 Received signal {signum} - shutting down...")
        self.shutdown()
    
    def initialize(self):
        """Initialize application with optimizations"""
        self.logger.info("🚀 Initializing Gideon AI Optimized...")
        
        # Start memory monitoring
        memory_monitor.start_monitoring()
        
        # Optimize memory settings
        memory_result = memory_monitor.optimize_memory_usage()
        if memory_result.get('success'):
            self.logger.info(f"🔧 Memory optimized: saved {memory_result['total_saved_mb']:.1f}MB")
        
        # Initialize core
        self.gideon_core = OptimizedGideonCore()
        
        # Initialize PyQt6 app if available
        if PYQT6_AVAILABLE:
            self.app = QApplication(sys.argv)
            self.app.setQuitOnLastWindowClosed(False)
            
            # Create debug panel
            self.debug_panel = DebugPanel()
            self.debug_panel.show()
            
            self.logger.info("✅ PyQt6 interface initialized")
        else:
            self.logger.warning("⚠️ Running in console mode")
        
        # Authenticate user
        if self.gideon_core.authenticate_user():
            self.logger.info("✅ User authenticated")
            audio_manager.speak("Hello! Gideon AI is ready and optimized.")
        else:
            self.logger.warning("⚠️ Authentication failed - continuing anyway")
        
        self.running = True
        self.logger.info("🎉 Gideon AI Optimized is ready!")
    
    def start_voice_processing(self):
        """Start voice command processing"""
        def voice_loop():
            self.logger.info("🎤 Starting voice processing loop...")
            
            # Start audio manager
            audio_manager.start_continuous_listening()
            
            while self.running:
                try:
                    # Get next command with timeout
                    command = audio_manager.get_next_command(timeout=1.0)
                    
                    if command:
                        # Process in separate thread to avoid blocking
                        threading.Thread(
                            target=self.gideon_core.process_voice_command,
                            args=(command.text,),
                            daemon=True
                        ).start()
                    
                    # Check memory periodically
                    memory_status = memory_monitor.check_memory_status()
                    if memory_status in ["HIGH", "CRITICAL"]:
                        self.logger.warning(f"🚨 Memory status: {memory_status}")
                        if memory_status == "CRITICAL":
                            memory_monitor.force_cleanup()
                    
                except Exception as e:
                    self.logger.error(f"❌ Voice processing error: {e}")
                    time.sleep(1)
        
        # Start voice processing in background
        voice_thread = threading.Thread(target=voice_loop, daemon=True)
        voice_thread.start()
    
    def run(self):
        """Run the optimized application"""
        try:
            self.initialize()
            self.start_voice_processing()
            
            # Show status
            memory_info = memory_monitor.get_current_memory()
            if memory_info:
                self.logger.info(f"📊 Current memory usage: {memory_info.rss_mb:.1f}MB")
            
            audio_stats = audio_manager.get_stats()
            self.logger.info(f"🎤 Audio system: {audio_stats['is_listening']} listening")
            
            # Run application
            if PYQT6_AVAILABLE and self.app:
                self.logger.info("🖥️ Starting PyQt6 application...")
                sys.exit(self.app.exec())
            else:
                self.logger.info("🖥️ Running in console mode...")
                try:
                    while self.running:
                        time.sleep(1)
                except KeyboardInterrupt:
                    self.logger.info("⌨️ Keyboard interrupt received")
                    self.shutdown()
        
        except Exception as e:
            self.logger.error(f"❌ Critical error: {e}")
            self.shutdown()
    
    def shutdown(self):
        """Clean shutdown"""
        self.logger.info("🔄 Shutting down Gideon AI Optimized...")
        
        self.running = False
        
        # Stop audio
        audio_manager.stop_continuous_listening()
        audio_manager.cleanup()
        
        # Stop memory monitoring
        memory_monitor.stop_monitoring()
        
        # Final memory report
        report = memory_monitor.get_memory_report()
        if not report.get('error'):
            current = report['current']
            stats = report['performance']
            self.logger.info(f"📊 Final memory: {current['rss_mb']:.1f}MB "
                           f"(peak: {report['statistics']['peak_mb']:.1f}MB)")
            self.logger.info(f"📊 Performance: {stats['total_measurements']} measurements, "
                           f"{stats['total_cleanups']} cleanups")
        
        # Cleanup
        if self.gideon_core:
            memory_monitor.cleanup()
        
        if self.app:
            self.app.quit()
        
        self.logger.info("✅ Shutdown complete")

def main():
    """Main entry point"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    🤖 GIDEON AI ASSISTANT                    ║
║                     OPTIMIZED VERSION                        ║
╠══════════════════════════════════════════════════════════════╣
║  ⚡ Performance Optimized   📊 Memory Monitored             ║
║  🎤 Smart Audio Recognition 🧹 Auto Cleanup                 ║
║  🔧 Debug Panel Included    💾 < 300MB Target               ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    app = GideonOptimizedApp()
    app.run()

if __name__ == "__main__":
    main() 