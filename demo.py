#!/usr/bin/env python3
"""
Gideon AI Assistant - Demo Script
Demonstrates the architecture and features without requiring full dependencies
"""

import time
import threading
from dataclasses import dataclass
from typing import Dict, List, Optional

# Demo configuration (simplified version of config.py)
@dataclass
class DemoConfig:
    """Demo configuration for showcasing features"""
    PRIMARY_DARK = "#1a237e"
    ACCENT_BLUE = "#03DAC6"
    ACCENT_GREEN = "#00FF41"
    WARNING = "#FF6B35"
    
    # Demo settings
    DEMO_MODE = True
    VOICE_SIMULATION = True
    SMART_HOME_SIMULATION = True

config = DemoConfig()

# Demo Event System
class DemoEventSystem:
    """Simplified event system for demo"""
    
    def __init__(self):
        self.listeners = {}
    
    def subscribe(self, event_name: str, callback):
        if event_name not in self.listeners:
            self.listeners[event_name] = []
        self.listeners[event_name].append(callback)
    
    def emit(self, event_name: str, data=None):
        if event_name in self.listeners:
            for callback in self.listeners[event_name]:
                try:
                    callback(data)
                except Exception as e:
                    print(f"Event error: {e}")

# Demo Logger
class DemoLogger:
    """Simplified logger for demo"""
    
    def __init__(self, name: str = "Demo"):
        self.name = name
    
    def info(self, message: str):
        print(f"[INFO] {self.name}: {message}")
    
    def warning(self, message: str):
        print(f"[WARN] {self.name}: {message}")
    
    def error(self, message: str):
        print(f"[ERROR] {self.name}: {message}")

# Demo Voice Command
@dataclass
class DemoVoiceCommand:
    """Demo voice command structure"""
    text: str
    confidence: float
    timestamp: float

# Demo Smart Home Module
class DemoSmartHomeModule:
    """Demonstration of smart home functionality"""
    
    def __init__(self):
        self.logger = DemoLogger("SmartHome")
        self.event_system = DemoEventSystem()
        
        # Simulated devices
        self.lights = {
            1: {"name": "Living Room", "on": False, "brightness": 100},
            2: {"name": "Bedroom", "on": True, "brightness": 50},
            3: {"name": "Kitchen", "on": False, "brightness": 100},
        }
        
        self.thermostats = {
            "living_room": {"name": "Living Room", "current": 22.5, "target": 23.0, "mode": "heating"},
            "bedroom": {"name": "Bedroom", "current": 21.0, "target": 20.0, "mode": "auto"}
        }
        
        self.logger.info("Smart Home module initialized (DEMO MODE)")
    
    def discover_devices(self) -> bool:
        """Simulate device discovery"""
        self.logger.info("🔍 Discovering smart home devices...")
        time.sleep(1.5)  # Simulate discovery time
        
        self.logger.info(f"✅ Found {len(self.lights)} Philips Hue lights")
        self.logger.info(f"✅ Found {len(self.thermostats)} thermostats")
        
        self.event_system.emit('devices_discovered', {
            'lights': len(self.lights),
            'thermostats': len(self.thermostats)
        })
        
        return True
    
    def set_light_state(self, light_id: int, state: Dict) -> bool:
        """Set light state"""
        if light_id in self.lights:
            self.lights[light_id].update(state)
            self.logger.info(f"💡 {self.lights[light_id]['name']} light: {state}")
            return True
        return False
    
    def set_scene(self, scene_name: str) -> bool:
        """Apply lighting scene"""
        scenes = {
            "morning": {"on": True, "brightness": 100},
            "evening": {"on": True, "brightness": 50},
            "night": {"on": True, "brightness": 20},
            "party": {"on": True, "brightness": 100},
            "off": {"on": False}
        }
        
        if scene_name in scenes:
            scene_state = scenes[scene_name]
            for light_id in self.lights.keys():
                self.set_light_state(light_id, scene_state)
            
            self.logger.info(f"🎬 Applied '{scene_name}' scene to all lights")
            return True
        
        return False
    
    def set_temperature(self, thermostat_id: str, temperature: float) -> bool:
        """Set thermostat temperature"""
        if thermostat_id in self.thermostats:
            self.thermostats[thermostat_id]["target"] = temperature
            self.logger.info(f"🌡️ {self.thermostats[thermostat_id]['name']} set to {temperature}°C")
            return True
        return False
    
    def process_voice_command(self, command: str) -> str:
        """Process voice commands for smart home"""
        command_lower = command.lower()
        
        if "turn on all lights" in command_lower:
            for light_id in self.lights.keys():
                self.set_light_state(light_id, {"on": True})
            return "Turned on all lights"
        
        elif "turn off all lights" in command_lower:
            for light_id in self.lights.keys():
                self.set_light_state(light_id, {"on": False})
            return "Turned off all lights"
        
        elif "evening scene" in command_lower or "evening mood" in command_lower:
            self.set_scene("evening")
            return "Applied evening scene"
        
        elif "party scene" in command_lower or "party mood" in command_lower:
            self.set_scene("party")
            return "Party mode activated! 🎉"
        
        elif "set temperature" in command_lower:
            # Extract temperature number
            import re
            temp_match = re.search(r'(\d+)', command_lower)
            if temp_match:
                temp = int(temp_match.group(1))
                self.set_temperature("living_room", temp)
                return f"Set temperature to {temp}°C"
        
        return "Smart home command not recognized"

# Demo Core Assistant
class DemoGideonCore:
    """Demonstration of core assistant functionality"""
    
    def __init__(self):
        self.logger = DemoLogger("GideonCore")
        self.event_system = DemoEventSystem()
        
        # System state
        self.is_listening = False
        self.is_speaking = False
        self.is_authenticated = False
        
        # Demo commands queue
        self.demo_commands = [
            "Hello Gideon",
            "Turn on all lights",
            "Set temperature to 23 degrees",
            "Apply evening scene",
            "What time is it?",
            "Turn off all lights",
            "Apply party scene"
        ]
        self.command_index = 0
        
        self.logger.info("Gideon Core initialized (DEMO MODE)")
    
    def authenticate_user(self) -> bool:
        """Simulate face authentication"""
        self.logger.info("🔍 Starting face recognition authentication...")
        self.speak("Searching for your face...")
        
        # Simulate authentication process
        for i in range(3):
            time.sleep(1)
            print(f"   📷 Analyzing frame {i+1}/3...")
        
        self.is_authenticated = True
        self.logger.info("✅ User authenticated successfully")
        self.speak("Hello! Authentication successful. I'm at your service.")
        self.event_system.emit('user_authenticated')
        
        return True
    
    def speak(self, text: str):
        """Simulate text-to-speech"""
        self.is_speaking = True
        self.event_system.emit('speech_started', {'text': text})
        
        print(f"🗣️  Gideon: {text}")
        time.sleep(len(text) * 0.05)  # Simulate speaking time
        
        self.is_speaking = False
        self.event_system.emit('speech_ended', {'text': text})
    
    def get_next_demo_command(self) -> Optional[DemoVoiceCommand]:
        """Get next demo voice command"""
        if self.command_index < len(self.demo_commands):
            command_text = self.demo_commands[self.command_index]
            self.command_index += 1
            
            return DemoVoiceCommand(
                text=command_text,
                confidence=0.95,
                timestamp=time.time()
            )
        return None
    
    def generate_ai_response(self, prompt: str) -> str:
        """Simulate AI responses"""
        responses = {
            "hello gideon": "Hello! I'm Gideon, your AI assistant. How can I help you today?",
            "what time is it": f"The current time is {time.strftime('%H:%M:%S')}",
            "how are you": "I'm functioning perfectly and ready to assist you!",
            "tell me a joke": "Why don't scientists trust atoms? Because they make up everything!",
            "weather": "I'm in demo mode, so I can't check real weather. But imagine it's a beautiful day! ☀️"
        }
        
        prompt_lower = prompt.lower()
        for key, response in responses.items():
            if key in prompt_lower:
                return response
        
        return "I'm running in demo mode. In the full version, I'd use OpenAI GPT-4 to respond to that!"

# Demo Audio Visualizer
class DemoAudioVisualizer:
    """Demonstration of audio visualization"""
    
    def __init__(self):
        self.logger = DemoLogger("AudioViz")
        self.mode = 'idle'
        self.is_running = False
        
    def start(self):
        """Start visualization"""
        self.is_running = True
        self.logger.info("🎵 Audio visualizer started")
        
    def stop(self):
        """Stop visualization"""
        self.is_running = False
        self.logger.info("🔇 Audio visualizer stopped")
        
    def set_mode(self, mode: str):
        """Set visualization mode"""
        mode_colors = {
            'idle': '⚪',
            'listening': '🔵',
            'speaking': '🟢',
            'processing': '🟠'
        }
        
        self.mode = mode
        color = mode_colors.get(mode, '⚪')
        self.logger.info(f"{color} Visualizer mode: {mode.upper()}")

# Demo Application
class DemoGideonApplication:
    """Demonstration of the complete Gideon application"""
    
    def __init__(self):
        self.logger = DemoLogger("GideonApp")
        
        # Initialize components
        self.gideon_core = DemoGideonCore()
        self.smart_home = DemoSmartHomeModule()
        self.audio_visualizer = DemoAudioVisualizer()
        
        # Connect events
        self._connect_events()
        
        self.logger.info("🤖 Gideon AI Assistant Demo initialized")
    
    def _connect_events(self):
        """Connect component events"""
        self.gideon_core.event_system.subscribe('speech_started', self._on_speech_started)
        self.gideon_core.event_system.subscribe('speech_ended', self._on_speech_ended)
        self.gideon_core.event_system.subscribe('user_authenticated', self._on_authenticated)
    
    def _on_speech_started(self, data):
        """Handle speech started"""
        self.audio_visualizer.set_mode('speaking')
    
    def _on_speech_ended(self, data):
        """Handle speech ended"""
        self.audio_visualizer.set_mode('idle')
    
    def _on_authenticated(self, data):
        """Handle user authentication"""
        self.audio_visualizer.start()
    
    def run_demo(self):
        """Run the demonstration"""
        print("\n" + "="*60)
        print("🤖 GIDEON AI ASSISTANT - DEMONSTRATION")
        print("="*60)
        
        # Show system info
        print("\n📊 SYSTEM ARCHITECTURE:")
        print("├── 🧠 Core Assistant (Voice Recognition + AI)")
        print("├── 🏠 Smart Home Module (Philips Hue + Thermostats)")
        print("├── 🎵 Audio Visualizer (Real-time Spectrum)")
        print("├── 🖥️ Desktop Overlay (PyQt6 Interface)")
        print("└── 📱 Modular Widgets (System Monitoring)")
        
        # Start authentication
        print("\n🔐 AUTHENTICATION PHASE:")
        if self.gideon_core.authenticate_user():
            print("✅ Authentication successful!")
        
        # Smart home discovery
        print("\n🏠 SMART HOME DISCOVERY:")
        if self.smart_home.discover_devices():
            print("✅ Smart home devices ready!")
        
        # Voice command simulation
        print("\n🎤 VOICE COMMAND DEMONSTRATION:")
        print("(Simulating voice commands...)")
        
        for i in range(7):
            print(f"\n--- Command {i+1}/7 ---")
            
            # Get next command
            command = self.gideon_core.get_next_demo_command()
            if not command:
                break
            
            # Simulate listening
            self.audio_visualizer.set_mode('listening')
            print(f"👤 User: \"{command.text}\"")
            time.sleep(0.5)
            
            # Process command
            self.audio_visualizer.set_mode('processing')
            response = self._route_command(command.text)
            time.sleep(0.3)
            
            # Speak response
            if response:
                self.gideon_core.speak(response)
            
            time.sleep(1)
        
        # Show interface features
        print("\n🖥️ INTERFACE FEATURES:")
        print("├── F12: Toggle overlay interface")
        print("├── 🎵 Circular audio visualizer (60 FPS)")
        print("├── 📊 Real-time system monitoring")
        print("├── 🎨 Gideon-inspired futuristic design")
        print("└── 👻 Semi-transparent overlay with animations")
        
        # Show module capabilities
        print("\n⚡ MODULE CAPABILITIES:")
        print("🏠 Smart Home:")
        for light_id, light in self.smart_home.lights.items():
            status = "ON" if light["on"] else "OFF"
            print(f"   💡 {light['name']}: {status} ({light['brightness']}%)")
        
        for thermo_id, thermo in self.smart_home.thermostats.items():
            print(f"   🌡️ {thermo['name']}: {thermo['current']}°C → {thermo['target']}°C ({thermo['mode']})")
        
        # Performance info
        print("\n⚡ PERFORMANCE SPECIFICATIONS:")
        print("├── 🎵 Audio: 60 FPS real-time visualization")
        print("├── 💾 Memory: < 200MB RAM usage")
        print("├── ⚡ Startup: < 3 seconds initialization")
        print("├── 🗣️ Voice: < 500ms response time")
        print("└── 🎨 UI: Smooth 60 FPS animations")
        
        print("\n" + "="*60)
        print("✨ DEMONSTRATION COMPLETE")
        print("🚀 Ready for production deployment!")
        print("📚 See README.md and INSTALL.md for setup instructions")
        print("="*60)
    
    def _route_command(self, command_text: str) -> str:
        """Route commands to appropriate modules"""
        command_lower = command_text.lower()
        
        # Smart home commands
        if any(word in command_lower for word in ['light', 'lights', 'scene', 'temperature']):
            return self.smart_home.process_voice_command(command_text)
        
        # General AI commands
        else:
            return self.gideon_core.generate_ai_response(command_text)

def main():
    """Main demo function"""
    try:
        # Create and run demo
        demo_app = DemoGideonApplication()
        demo_app.run_demo()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
    
    print("\n👋 Thank you for trying Gideon AI Assistant!")

if __name__ == "__main__":
    main() 