"""
Smart Home module for Gideon AI Assistant
Controls Philips Hue lights, thermostats, and other connected devices
"""

import json
import requests
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from core.event_system import EventSystem
from core.logger import GideonLogger

@dataclass
class HueLight:
    """Philips Hue light data structure"""
    id: int
    name: str
    state: Dict[str, Any]
    reachable: bool

@dataclass
class Thermostat:
    """Smart thermostat data structure"""
    id: str
    name: str
    current_temp: float
    target_temp: float
    mode: str  # heating, cooling, auto, off

class SmartHomeModule:
    """
    Smart Home control module
    Manages Philips Hue lights, thermostats, and other IoT devices
    """
    
    def __init__(self):
        self.logger = GideonLogger("SmartHome")
        self.event_system = EventSystem()
        
        # Philips Hue configuration
        self.hue_bridge_ip = None
        self.hue_username = None
        self.hue_lights: Dict[int, HueLight] = {}
        
        # Thermostat configuration
        self.thermostats: Dict[str, Thermostat] = {}
        
        # Device discovery status
        self.devices_discovered = False
        
        self.logger.info("Smart Home module initialized")
    
    def discover_devices(self) -> bool:
        """
        Discover and connect to smart home devices
        
        Returns:
            True if devices were found, False otherwise
        """
        self.logger.info("Starting device discovery...")
        
        # Discover Philips Hue bridge
        hue_found = self._discover_hue_bridge()
        
        # Discover thermostats (simulate for demo)
        thermostat_found = self._discover_thermostats()
        
        self.devices_discovered = hue_found or thermostat_found
        
        if self.devices_discovered:
            self.logger.info("Device discovery completed successfully")
            self.event_system.emit('smart_home_devices_discovered', {
                'hue_lights': len(self.hue_lights),
                'thermostats': len(self.thermostats)
            })
        else:
            self.logger.warning("No smart home devices found")
        
        return self.devices_discovered
    
    def _discover_hue_bridge(self) -> bool:
        """Discover Philips Hue bridge on network"""
        try:
            # Try to find Hue bridge via discovery
            response = requests.get("https://discovery.meethue.com/", timeout=5)
            if response.status_code == 200:
                bridges = response.json()
                if bridges:
                    self.hue_bridge_ip = bridges[0]["internalipaddress"]
                    self.logger.info(f"Found Hue bridge at {self.hue_bridge_ip}")
                    
                    # Try to authenticate (requires user to press bridge button)
                    return self._authenticate_hue()
            
        except Exception as e:
            self.logger.debug(f"Hue bridge discovery failed: {e}")
        
        # Fallback: try common IP addresses
        common_ips = ["192.168.1.2", "192.168.0.2", "10.0.0.2"]
        for ip in common_ips:
            if self._test_hue_connection(ip):
                self.hue_bridge_ip = ip
                return self._authenticate_hue()
        
        return False
    
    def _test_hue_connection(self, ip: str) -> bool:
        """Test connection to Hue bridge"""
        try:
            response = requests.get(f"http://{ip}/api/", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def _authenticate_hue(self) -> bool:
        """Authenticate with Hue bridge"""
        if not self.hue_bridge_ip:
            return False
        
        try:
            # Try existing credentials first
            if self.hue_username:
                return self._load_hue_lights()
            
            # Create new user (requires bridge button press)
            auth_data = {"devicetype": "gideon_ai_assistant"}
            response = requests.post(
                f"http://{self.hue_bridge_ip}/api/",
                json=auth_data,
                timeout=5
            )
            
            result = response.json()
            if result and isinstance(result, list) and "success" in result[0]:
                self.hue_username = result[0]["success"]["username"]
                self.logger.info("Hue authentication successful")
                return self._load_hue_lights()
            else:
                # Button not pressed
                self.logger.info("Press the button on your Hue bridge to authenticate")
                return False
                
        except Exception as e:
            self.logger.error(f"Hue authentication failed: {e}")
            return False
    
    def _load_hue_lights(self) -> bool:
        """Load Hue lights information"""
        try:
            response = requests.get(
                f"http://{self.hue_bridge_ip}/api/{self.hue_username}/lights",
                timeout=5
            )
            
            if response.status_code == 200:
                lights_data = response.json()
                self.hue_lights.clear()
                
                for light_id, light_info in lights_data.items():
                    light = HueLight(
                        id=int(light_id),
                        name=light_info["name"],
                        state=light_info["state"],
                        reachable=light_info["state"]["reachable"]
                    )
                    self.hue_lights[int(light_id)] = light
                
                self.logger.info(f"Loaded {len(self.hue_lights)} Hue lights")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to load Hue lights: {e}")
        
        return False
    
    def _discover_thermostats(self) -> bool:
        """Discover smart thermostats (simulated for demo)"""
        # Simulate thermostat discovery
        demo_thermostats = [
            Thermostat(
                id="demo_living_room",
                name="Living Room",
                current_temp=22.5,
                target_temp=23.0,
                mode="heating"
            ),
            Thermostat(
                id="demo_bedroom",
                name="Bedroom", 
                current_temp=21.0,
                target_temp=20.0,
                mode="auto"
            )
        ]
        
        for thermostat in demo_thermostats:
            self.thermostats[thermostat.id] = thermostat
        
        self.logger.info(f"Discovered {len(self.thermostats)} thermostats")
        return len(self.thermostats) > 0
    
    # Light control methods
    def set_light_state(self, light_id: int, state: Dict[str, Any]) -> bool:
        """
        Set Hue light state
        
        Args:
            light_id: Light ID
            state: New light state (on, bri, hue, sat, etc.)
            
        Returns:
            True if successful
        """
        if not self.hue_bridge_ip or not self.hue_username:
            self.logger.error("Hue bridge not configured")
            return False
        
        if light_id not in self.hue_lights:
            self.logger.error(f"Light {light_id} not found")
            return False
        
        try:
            response = requests.put(
                f"http://{self.hue_bridge_ip}/api/{self.hue_username}/lights/{light_id}/state",
                json=state,
                timeout=5
            )
            
            if response.status_code == 200:
                # Update local state
                self.hue_lights[light_id].state.update(state)
                self.logger.info(f"Light {light_id} state updated: {state}")
                
                self.event_system.emit('light_state_changed', {
                    'light_id': light_id,
                    'state': state
                })
                
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to set light state: {e}")
        
        return False
    
    def toggle_light(self, light_id: int) -> bool:
        """Toggle light on/off"""
        if light_id not in self.hue_lights:
            return False
        
        current_state = self.hue_lights[light_id].state.get("on", False)
        return self.set_light_state(light_id, {"on": not current_state})
    
    def set_light_brightness(self, light_id: int, brightness: int) -> bool:
        """Set light brightness (0-254)"""
        brightness = max(0, min(254, brightness))
        return self.set_light_state(light_id, {"bri": brightness, "on": brightness > 0})
    
    def set_light_color(self, light_id: int, hue: int, saturation: int) -> bool:
        """Set light color using HSV"""
        hue = max(0, min(65535, hue))
        saturation = max(0, min(254, saturation))
        return self.set_light_state(light_id, {"hue": hue, "sat": saturation})
    
    def set_scene(self, scene_name: str) -> bool:
        """
        Set a predefined lighting scene
        
        Args:
            scene_name: Scene name (evening, morning, night, party, etc.)
            
        Returns:
            True if successful
        """
        scenes = {
            "morning": {"on": True, "bri": 200, "ct": 250},  # Bright, cool white
            "evening": {"on": True, "bri": 100, "ct": 400},  # Dim, warm white
            "night": {"on": True, "bri": 20, "ct": 500},     # Very dim, very warm
            "party": {"on": True, "bri": 254, "hue": 46920, "sat": 254},  # Bright colors
            "relax": {"on": True, "bri": 80, "ct": 450},     # Soft warm light
            "off": {"on": False}
        }
        
        if scene_name not in scenes:
            self.logger.error(f"Unknown scene: {scene_name}")
            return False
        
        scene_state = scenes[scene_name]
        success_count = 0
        
        for light_id in self.hue_lights.keys():
            if self.set_light_state(light_id, scene_state):
                success_count += 1
        
        self.logger.info(f"Applied scene '{scene_name}' to {success_count} lights")
        return success_count > 0
    
    # Thermostat control methods
    def set_thermostat_temperature(self, thermostat_id: str, temperature: float) -> bool:
        """Set thermostat target temperature"""
        if thermostat_id not in self.thermostats:
            self.logger.error(f"Thermostat {thermostat_id} not found")
            return False
        
        # Simulate temperature change
        self.thermostats[thermostat_id].target_temp = temperature
        
        self.logger.info(f"Set {thermostat_id} temperature to {temperature}°C")
        self.event_system.emit('thermostat_changed', {
            'thermostat_id': thermostat_id,
            'target_temp': temperature
        })
        
        return True
    
    def set_thermostat_mode(self, thermostat_id: str, mode: str) -> bool:
        """Set thermostat mode (heating, cooling, auto, off)"""
        if thermostat_id not in self.thermostats:
            return False
        
        valid_modes = ["heating", "cooling", "auto", "off"]
        if mode not in valid_modes:
            self.logger.error(f"Invalid thermostat mode: {mode}")
            return False
        
        self.thermostats[thermostat_id].mode = mode
        
        self.logger.info(f"Set {thermostat_id} mode to {mode}")
        self.event_system.emit('thermostat_mode_changed', {
            'thermostat_id': thermostat_id,
            'mode': mode
        })
        
        return True
    
    # Voice command processing
    def process_voice_command(self, command: str) -> str:
        """
        Process smart home voice commands
        
        Args:
            command: Voice command text
            
        Returns:
            Response text
        """
        command_lower = command.lower()
        
        # Light commands
        if any(word in command_lower for word in ["light", "lights", "lamp"]):
            if "turn on" in command_lower or "allume" in command_lower:
                if "all" in command_lower or "toute" in command_lower:
                    return self._turn_on_all_lights()
                else:
                    return self._parse_light_command(command_lower, "on")
            
            elif "turn off" in command_lower or "éteint" in command_lower:
                if "all" in command_lower or "toute" in command_lower:
                    return self._turn_off_all_lights()
                else:
                    return self._parse_light_command(command_lower, "off")
            
            elif "dim" in command_lower or "diminue" in command_lower:
                return self._parse_brightness_command(command_lower, "dim")
            
            elif "bright" in command_lower or "augmente" in command_lower:
                return self._parse_brightness_command(command_lower, "bright")
        
        # Scene commands
        elif any(word in command_lower for word in ["scene", "ambiance", "mood"]):
            return self._parse_scene_command(command_lower)
        
        # Temperature commands
        elif any(word in command_lower for word in ["temperature", "thermostat", "heating", "cooling"]):
            return self._parse_temperature_command(command_lower)
        
        return "I didn't understand that smart home command."
    
    def _turn_on_all_lights(self) -> str:
        """Turn on all lights"""
        success_count = 0
        for light_id in self.hue_lights.keys():
            if self.toggle_light(light_id) if not self.hue_lights[light_id].state.get("on") else True:
                success_count += 1
        
        return f"Turned on {success_count} lights"
    
    def _turn_off_all_lights(self) -> str:
        """Turn off all lights"""
        success_count = 0
        for light_id in self.hue_lights.keys():
            if self.set_light_state(light_id, {"on": False}):
                success_count += 1
        
        return f"Turned off {success_count} lights"
    
    def _parse_light_command(self, command: str, action: str) -> str:
        """Parse specific light commands"""
        # Simple parsing - could be enhanced with NLP
        light_names = [light.name.lower() for light in self.hue_lights.values()]
        
        for light in self.hue_lights.values():
            if light.name.lower() in command:
                if action == "on":
                    self.set_light_state(light.id, {"on": True})
                    return f"Turned on {light.name}"
                elif action == "off":
                    self.set_light_state(light.id, {"on": False})
                    return f"Turned off {light.name}"
        
        return "Could not find that light"
    
    def _parse_scene_command(self, command: str) -> str:
        """Parse scene commands"""
        scene_keywords = {
            "morning": ["morning", "matin", "wake up"],
            "evening": ["evening", "soir", "relax"],
            "night": ["night", "nuit", "sleep", "bed"],
            "party": ["party", "fête", "celebration"],
            "off": ["off", "éteint", "dark"]
        }
        
        for scene, keywords in scene_keywords.items():
            if any(keyword in command for keyword in keywords):
                if self.set_scene(scene):
                    return f"Applied {scene} scene"
        
        return "Unknown lighting scene"
    
    def _parse_temperature_command(self, command: str) -> str:
        """Parse temperature commands"""
        # Extract temperature number
        import re
        temp_match = re.search(r'(\d+(?:\.\d+)?)', command)
        
        if temp_match:
            temperature = float(temp_match.group(1))
            
            # Find thermostat by room name
            for thermostat in self.thermostats.values():
                if thermostat.name.lower() in command:
                    self.set_thermostat_temperature(thermostat.id, temperature)
                    return f"Set {thermostat.name} temperature to {temperature}°C"
            
            # Default to first thermostat
            if self.thermostats:
                first_thermostat = list(self.thermostats.values())[0]
                self.set_thermostat_temperature(first_thermostat.id, temperature)
                return f"Set temperature to {temperature}°C"
        
        return "Could not understand temperature command"
    
    def get_device_status(self) -> Dict[str, Any]:
        """Get status of all smart home devices"""
        return {
            "lights": {
                light_id: {
                    "name": light.name,
                    "on": light.state.get("on", False),
                    "brightness": light.state.get("bri", 0),
                    "reachable": light.reachable
                }
                for light_id, light in self.hue_lights.items()
            },
            "thermostats": {
                t_id: {
                    "name": thermostat.name,
                    "current_temp": thermostat.current_temp,
                    "target_temp": thermostat.target_temp,
                    "mode": thermostat.mode
                }
                for t_id, thermostat in self.thermostats.items()
            }
        } 