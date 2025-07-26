#!/usr/bin/env python3
"""
Local Commands Manager - macOS System Integration
100% Local system commands and automation
"""

import subprocess
import os
import platform
import psutil
import logging
import time
import webbrowser
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass

from config import config


@dataclass
class CommandResult:
    """Result of a system command execution"""
    success: bool
    output: str
    error: Optional[str] = None
    execution_time: float = 0
    command: str = ""


class SystemInfoManager:
    """System information and monitoring for macOS"""
    
    def __init__(self):
        self.logger = logging.getLogger("SystemInfo")
        self.system_type = platform.system()
        self.logger.info(f"💻 System info manager initialized: {self.system_type}")
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        try:
            info = {
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'hostname': platform.node(),
                'python_version': platform.python_version(),
                'cpu_count': psutil.cpu_count(),
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory': self._get_memory_info(),
                'disk': self._get_disk_info(),
                'network': self._get_network_info(),
                'uptime': self._get_uptime()
            }
            
            # macOS specific info
            if self.system_type == "Darwin":
                info.update(self._get_macos_info())
            
            return info
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get system info: {e}")
            return {'error': str(e)}
    
    def _get_memory_info(self) -> Dict[str, Any]:
        """Get memory information"""
        try:
            memory = psutil.virtual_memory()
            return {
                'total_gb': round(memory.total / (1024**3), 2),
                'available_gb': round(memory.available / (1024**3), 2),
                'used_gb': round(memory.used / (1024**3), 2),
                'percent': memory.percent
            }
        except:
            return {}
    
    def _get_disk_info(self) -> Dict[str, Any]:
        """Get disk usage information"""
        try:
            disk = psutil.disk_usage('/')
            return {
                'total_gb': round(disk.total / (1024**3), 2),
                'used_gb': round(disk.used / (1024**3), 2),
                'free_gb': round(disk.free / (1024**3), 2),
                'percent': round((disk.used / disk.total) * 100, 1)
            }
        except:
            return {}
    
    def _get_network_info(self) -> Dict[str, Any]:
        """Get network interface information"""
        try:
            interfaces = psutil.net_if_addrs()
            active_interfaces = []
            
            for interface, addresses in interfaces.items():
                for addr in addresses:
                    if addr.family == 2:  # AF_INET (IPv4)
                        active_interfaces.append({
                            'interface': interface,
                            'ip': addr.address
                        })
            
            return {'interfaces': active_interfaces}
        except:
            return {}
    
    def _get_uptime(self) -> str:
        """Get system uptime"""
        try:
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            hours = int(uptime_seconds // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
        except:
            return "Unknown"
    
    def _get_macos_info(self) -> Dict[str, Any]:
        """Get macOS specific information"""
        try:
            macos_info = {}
            
            # macOS version
            try:
                result = subprocess.run(['sw_vers', '-productVersion'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    macos_info['macos_version'] = result.stdout.strip()
            except:
                pass
            
            # Hardware info
            try:
                result = subprocess.run(['system_profiler', 'SPHardwareDataType'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    output = result.stdout
                    if 'Model Name:' in output:
                        model_line = [line for line in output.split('\n') if 'Model Name:' in line]
                        if model_line:
                            macos_info['model'] = model_line[0].split(':')[1].strip()
            except:
                pass
            
            return macos_info
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get macOS info: {e}")
            return {}


class ApplicationManager:
    """Application management for macOS"""
    
    def __init__(self):
        self.logger = logging.getLogger("ApplicationManager")
        self.common_apps = config.commands.COMMON_APPS
        self.logger.info("📱 Application manager initialized")
    
    def open_application(self, app_name: str) -> CommandResult:
        """Open an application by name"""
        start_time = time.time()
        
        try:
            # Normalize app name
            app_name = app_name.lower().strip()
            
            # Check if it's a common app alias
            actual_app_name = self._resolve_app_name(app_name)
            
            # Try to open using 'open' command
            cmd = ['open', '-a', actual_app_name]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            execution_time = time.time() - start_time
            
            if result.returncode == 0:
                self.logger.info(f"✅ Opened application: {actual_app_name}")
                return CommandResult(
                    success=True,
                    output=f"Successfully opened {actual_app_name}",
                    execution_time=execution_time,
                    command=' '.join(cmd)
                )
            else:
                error = result.stderr or f"Failed to open {actual_app_name}"
                self.logger.warning(f"⚠️ Failed to open {actual_app_name}: {error}")
                return CommandResult(
                    success=False,
                    output="",
                    error=error,
                    execution_time=execution_time,
                    command=' '.join(cmd)
                )
                
        except subprocess.TimeoutExpired:
            return CommandResult(
                success=False,
                output="",
                error="Application launch timed out",
                execution_time=10,
                command=f"open -a {app_name}"
            )
        except Exception as e:
            return CommandResult(
                success=False,
                output="",
                error=str(e),
                execution_time=time.time() - start_time,
                command=f"open -a {app_name}"
            )
    
    def _resolve_app_name(self, app_name: str) -> str:
        """Resolve app name from aliases"""
        app_name_lower = app_name.lower()
        
        # Check category mappings
        for category, apps in self.common_apps.items():
            if app_name_lower == category:
                return apps[0]  # Return first app in category
            
            for app in apps:
                if app_name_lower in app.lower() or app.lower() in app_name_lower:
                    return app
        
        # Return original name if no match found
        return app_name
    
    def list_running_applications(self) -> List[Dict[str, Any]]:
        """List currently running applications"""
        try:
            cmd = ['ps', 'aux']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                return []
            
            # Parse process list
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            apps = []
            
            for line in lines:
                parts = line.split()
                if len(parts) >= 11:
                    # Look for GUI applications (those in /Applications/)
                    command = ' '.join(parts[10:])
                    if '/Applications/' in command and '.app' in command:
                        app_name = command.split('/Applications/')[1].split('.app')[0]
                        if app_name and app_name not in [app['name'] for app in apps]:
                            apps.append({
                                'name': app_name,
                                'pid': parts[1],
                                'cpu_percent': parts[2],
                                'memory_percent': parts[3]
                            })
            
            return apps[:20]  # Limit to 20 apps
            
        except Exception as e:
            self.logger.error(f"❌ Failed to list applications: {e}")
            return []
    
    def quit_application(self, app_name: str) -> CommandResult:
        """Quit an application"""
        start_time = time.time()
        
        try:
            cmd = ['osascript', '-e', f'quit app "{app_name}"']
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            execution_time = time.time() - start_time
            
            if result.returncode == 0:
                return CommandResult(
                    success=True,
                    output=f"Successfully quit {app_name}",
                    execution_time=execution_time,
                    command=' '.join(cmd)
                )
            else:
                return CommandResult(
                    success=False,
                    output="",
                    error=result.stderr or f"Failed to quit {app_name}",
                    execution_time=execution_time,
                    command=' '.join(cmd)
                )
                
        except Exception as e:
            return CommandResult(
                success=False,
                output="",
                error=str(e),
                execution_time=time.time() - start_time,
                command=f"quit app {app_name}"
            )


class FileManager:
    """File system operations manager"""
    
    def __init__(self):
        self.logger = logging.getLogger("FileManager")
        self.search_locations = [Path(loc).expanduser() for loc in config.commands.SEARCH_LOCATIONS]
        self.logger.info("📁 File manager initialized")
    
    def search_files(self, query: str, location: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for files by name"""
        try:
            results = []
            search_paths = [Path(location).expanduser()] if location else self.search_locations
            
            for search_path in search_paths:
                if not search_path.exists():
                    continue
                
                try:
                    # Use case-insensitive glob search
                    pattern = f"*{query.lower()}*"
                    
                    for file_path in search_path.rglob(pattern):
                        if len(results) >= limit:
                            break
                        
                        try:
                            stat = file_path.stat()
                            results.append({
                                'name': file_path.name,
                                'path': str(file_path),
                                'size_bytes': stat.st_size,
                                'size_human': self._format_size(stat.st_size),
                                'modified': time.strftime('%Y-%m-%d %H:%M:%S', 
                                                        time.localtime(stat.st_mtime)),
                                'is_directory': file_path.is_dir()
                            })
                        except OSError:
                            continue
                
                except Exception as e:
                    self.logger.debug(f"Search error in {search_path}: {e}")
                    continue
            
            self.logger.info(f"🔍 Found {len(results)} files for query: {query}")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ File search failed: {e}")
            return []
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    def open_file(self, file_path: str) -> CommandResult:
        """Open a file with default application"""
        start_time = time.time()
        
        try:
            path = Path(file_path).expanduser()
            
            if not path.exists():
                return CommandResult(
                    success=False,
                    output="",
                    error=f"File not found: {file_path}",
                    execution_time=time.time() - start_time,
                    command=f"open {file_path}"
                )
            
            cmd = ['open', str(path)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            execution_time = time.time() - start_time
            
            if result.returncode == 0:
                return CommandResult(
                    success=True,
                    output=f"Successfully opened {path.name}",
                    execution_time=execution_time,
                    command=' '.join(cmd)
                )
            else:
                return CommandResult(
                    success=False,
                    output="",
                    error=result.stderr or f"Failed to open {path.name}",
                    execution_time=execution_time,
                    command=' '.join(cmd)
                )
                
        except Exception as e:
            return CommandResult(
                success=False,
                output="",
                error=str(e),
                execution_time=time.time() - start_time,
                command=f"open {file_path}"
            )
    
    def show_in_finder(self, file_path: str) -> CommandResult:
        """Show file in Finder"""
        start_time = time.time()
        
        try:
            path = Path(file_path).expanduser()
            
            if not path.exists():
                return CommandResult(
                    success=False,
                    output="",
                    error=f"Path not found: {file_path}",
                    execution_time=time.time() - start_time,
                    command=f"open -R {file_path}"
                )
            
            cmd = ['open', '-R', str(path)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            execution_time = time.time() - start_time
            
            if result.returncode == 0:
                return CommandResult(
                    success=True,
                    output=f"Showed {path.name} in Finder",
                    execution_time=execution_time,
                    command=' '.join(cmd)
                )
            else:
                return CommandResult(
                    success=False,
                    output="",
                    error=result.stderr or f"Failed to show {path.name} in Finder",
                    execution_time=execution_time,
                    command=' '.join(cmd)
                )
                
        except Exception as e:
            return CommandResult(
                success=False,
                output="",
                error=str(e),
                execution_time=time.time() - start_time,
                command=f"open -R {file_path}"
            )


class MediaController:
    """Media control for macOS"""
    
    def __init__(self):
        self.logger = logging.getLogger("MediaController")
        self.logger.info("🎵 Media controller initialized")
    
    def control_volume(self, action: str, value: Optional[int] = None) -> CommandResult:
        """Control system volume"""
        start_time = time.time()
        
        try:
            if action == "get":
                cmd = ['osascript', '-e', 'output volume of (get volume settings)']
            elif action == "set" and value is not None:
                # Clamp value between 0 and 100
                value = max(0, min(100, value))
                cmd = ['osascript', '-e', f'set volume output volume {value}']
            elif action == "mute":
                cmd = ['osascript', '-e', 'set volume with output muted']
            elif action == "unmute":
                cmd = ['osascript', '-e', 'set volume without output muted']
            else:
                return CommandResult(
                    success=False,
                    output="",
                    error="Invalid volume action. Use: get, set, mute, unmute",
                    execution_time=0,
                    command=""
                )
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            execution_time = time.time() - start_time
            
            if result.returncode == 0:
                output = f"Volume {action}"
                if action == "get":
                    output = f"Current volume: {result.stdout.strip()}"
                elif action == "set":
                    output = f"Volume set to {value}"
                
                return CommandResult(
                    success=True,
                    output=output,
                    execution_time=execution_time,
                    command=' '.join(cmd)
                )
            else:
                return CommandResult(
                    success=False,
                    output="",
                    error=result.stderr or f"Failed to {action} volume",
                    execution_time=execution_time,
                    command=' '.join(cmd)
                )
                
        except Exception as e:
            return CommandResult(
                success=False,
                output="",
                error=str(e),
                execution_time=time.time() - start_time,
                command=f"volume {action}"
            )
    
    def take_screenshot(self, file_path: Optional[str] = None) -> CommandResult:
        """Take a screenshot"""
        start_time = time.time()
        
        try:
            if file_path is None:
                # Default to Desktop with timestamp
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                file_path = f"~/Desktop/screenshot_{timestamp}.png"
            
            path = Path(file_path).expanduser()
            cmd = ['screencapture', str(path)]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            execution_time = time.time() - start_time
            
            if result.returncode == 0 and path.exists():
                return CommandResult(
                    success=True,
                    output=f"Screenshot saved to {path}",
                    execution_time=execution_time,
                    command=' '.join(cmd)
                )
            else:
                return CommandResult(
                    success=False,
                    output="",
                    error=result.stderr or "Failed to take screenshot",
                    execution_time=execution_time,
                    command=' '.join(cmd)
                )
                
        except Exception as e:
            return CommandResult(
                success=False,
                output="",
                error=str(e),
                execution_time=time.time() - start_time,
                command=f"screenshot {file_path or 'default'}"
            )


class CommandManager:
    """Main command manager orchestrating all system operations"""
    
    def __init__(self):
        self.logger = logging.getLogger("CommandManager")
        
        # Initialize component managers
        self.system_info = SystemInfoManager()
        self.app_manager = ApplicationManager()
        self.file_manager = FileManager()
        self.media_controller = MediaController()
        
        # Command statistics
        self.stats = {
            'total_commands': 0,
            'successful_commands': 0,
            'failed_commands': 0,
            'avg_execution_time': 0
        }
        
        # Available commands mapping
        self.command_handlers = {
            # System information
            'system_info': self.system_info.get_system_info,
            
            # Application management
            'open_app': self.app_manager.open_application,
            'quit_app': self.app_manager.quit_application,
            'list_apps': self.app_manager.list_running_applications,
            
            # File operations
            'search_files': self.file_manager.search_files,
            'open_file': self.file_manager.open_file,
            'show_in_finder': self.file_manager.show_in_finder,
            
            # Media control
            'volume': self.media_controller.control_volume,
            'screenshot': self.media_controller.take_screenshot,
            
            # Web operations
            'open_url': self._open_url
        }
        
        self.logger.info(f"⚙️ Command manager initialized with {len(self.command_handlers)} commands")
    
    def execute_command(self, command: str, **kwargs) -> CommandResult:
        """Execute a system command"""
        start_time = time.time()
        self.stats['total_commands'] += 1
        
        try:
            if command not in self.command_handlers:
                return CommandResult(
                    success=False,
                    output="",
                    error=f"Unknown command: {command}",
                    execution_time=time.time() - start_time,
                    command=command
                )
            
            handler = self.command_handlers[command]
            
            # Execute command with parameters
            if command in ['system_info', 'list_apps']:
                # Commands with no parameters
                result = handler()
                if isinstance(result, dict):
                    # Convert dict results to CommandResult
                    result = CommandResult(
                        success=True,
                        output=str(result),
                        execution_time=time.time() - start_time,
                        command=command
                    )
            else:
                # Commands with parameters
                result = handler(**kwargs)
            
            # Update statistics
            if result.success:
                self.stats['successful_commands'] += 1
            else:
                self.stats['failed_commands'] += 1
            
            # Update average execution time
            total_commands = self.stats['total_commands']
            current_avg = self.stats['avg_execution_time']
            self.stats['avg_execution_time'] = (
                (current_avg * (total_commands - 1) + result.execution_time) / total_commands
            )
            
            self.logger.info(f"⚙️ Command '{command}' executed: {'✅' if result.success else '❌'}")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Command execution failed: {e}")
            self.stats['failed_commands'] += 1
            
            return CommandResult(
                success=False,
                output="",
                error=str(e),
                execution_time=time.time() - start_time,
                command=command
            )
    
    def _open_url(self, url: str) -> CommandResult:
        """Open URL in default browser"""
        start_time = time.time()
        
        try:
            webbrowser.open(url)
            
            return CommandResult(
                success=True,
                output=f"Opened URL: {url}",
                execution_time=time.time() - start_time,
                command=f"open {url}"
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                output="",
                error=str(e),
                execution_time=time.time() - start_time,
                command=f"open {url}"
            )
    
    def get_available_commands(self) -> List[str]:
        """Get list of available commands"""
        return list(self.command_handlers.keys())
    
    def get_command_help(self, command: str) -> Dict[str, Any]:
        """Get help information for a command"""
        help_info = {
            'system_info': {
                'description': 'Get comprehensive system information',
                'parameters': None,
                'example': 'system_info'
            },
            'open_app': {
                'description': 'Open an application',
                'parameters': {'app_name': 'Name of the application to open'},
                'example': 'open_app(app_name="Safari")'
            },
            'quit_app': {
                'description': 'Quit an application',
                'parameters': {'app_name': 'Name of the application to quit'},
                'example': 'quit_app(app_name="Safari")'
            },
            'search_files': {
                'description': 'Search for files by name',
                'parameters': {
                    'query': 'Search query',
                    'location': 'Optional search location',
                    'limit': 'Maximum number of results'
                },
                'example': 'search_files(query="document", limit=10)'
            },
            'volume': {
                'description': 'Control system volume',
                'parameters': {
                    'action': 'Action: get, set, mute, unmute',
                    'value': 'Volume level (0-100) for set action'
                },
                'example': 'volume(action="set", value=50)'
            },
            'screenshot': {
                'description': 'Take a screenshot',
                'parameters': {'file_path': 'Optional path to save screenshot'},
                'example': 'screenshot(file_path="~/Desktop/my_screenshot.png")'
            }
        }
        
        return help_info.get(command, {'description': 'No help available', 'parameters': None})
    
    def get_stats(self) -> Dict[str, Any]:
        """Get command execution statistics"""
        stats = dict(self.stats)
        
        if self.stats['total_commands'] > 0:
            success_rate = (self.stats['successful_commands'] / self.stats['total_commands']) * 100
            stats['success_rate'] = f"{success_rate:.1f}%"
        else:
            stats['success_rate'] = "0%"
        
        stats['available_commands'] = len(self.command_handlers)
        
        return stats
    
    def get_health_status(self) -> Dict[str, str]:
        """Get health status of command system"""
        return {
            'system_info': 'healthy',
            'app_manager': 'healthy',
            'file_manager': 'healthy',
            'media_controller': 'healthy',
            'overall': 'healthy'
        }


# Global instance
command_manager = CommandManager() 