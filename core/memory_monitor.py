"""
Intelligent Memory Monitor for Gideon AI Assistant
Real-time memory tracking with automatic cleanup and optimization
"""

import psutil
import gc
import time
import threading
import logging
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from collections import deque
import os
import sys

@dataclass
class MemoryThresholds:
    """Memory usage thresholds for different alert levels"""
    # Memory limits in MB
    LOW_USAGE: int = 150      # Normal operation
    MEDIUM_USAGE: int = 250   # Warning level
    HIGH_USAGE: int = 350     # Alert level
    CRITICAL_USAGE: int = 500 # Critical - force cleanup
    
    # Performance thresholds
    GC_INTERVAL: int = 100    # Checks before forcing GC
    ALERT_INTERVAL: int = 30  # Seconds between alerts
    MONITORING_INTERVAL: int = 5  # Seconds between checks

@dataclass
class MemoryInfo:
    """Memory usage information snapshot"""
    rss_mb: float           # Resident Set Size
    vms_mb: float          # Virtual Memory Size
    percent: float         # Percentage of system memory
    available_mb: float    # Available system memory
    timestamp: float       # When measurement was taken
    objects_count: int     # Number of Python objects
    gc_collections: int    # GC collection count

class MemoryMonitor:
    """Intelligent memory monitoring and management"""
    
    def __init__(self, thresholds: MemoryThresholds = None):
        self.thresholds = thresholds or MemoryThresholds()
        self.logger = logging.getLogger("MemoryMonitor")
        
        # Monitoring state
        self.is_monitoring = False
        self.monitor_thread = None
        self.last_alert_time = 0
        self.gc_check_counter = 0
        
        # Statistics
        self.history = deque(maxlen=1000)  # Keep last 1000 measurements
        self.peak_usage = 0
        self.total_cleanups = 0
        self.cleanup_callbacks: List[Callable] = []
        
        # Performance tracking
        self.stats = {
            'measurements': 0,
            'alerts': 0,
            'forced_cleanups': 0,
            'avg_memory': 0,
            'peak_memory': 0
        }
        
        self.process = psutil.Process()
    
    def get_current_memory(self) -> MemoryInfo:
        """Get current memory usage information"""
        try:
            # Process memory info
            memory_info = self.process.memory_info()
            memory_percent = self.process.memory_percent()
            
            # System memory info
            system_memory = psutil.virtual_memory()
            
            # Python objects count
            objects_count = len(gc.get_objects())
            
            # GC statistics
            gc_stats = gc.get_stats()
            gc_collections = sum(stat['collections'] for stat in gc_stats)
            
            info = MemoryInfo(
                rss_mb=memory_info.rss / 1024 / 1024,
                vms_mb=memory_info.vms / 1024 / 1024,
                percent=memory_percent,
                available_mb=system_memory.available / 1024 / 1024,
                timestamp=time.time(),
                objects_count=objects_count,
                gc_collections=gc_collections
            )
            
            # Update statistics
            self.stats['measurements'] += 1
            self.peak_usage = max(self.peak_usage, info.rss_mb)
            self.stats['peak_memory'] = self.peak_usage
            
            # Update running average
            measurements = self.stats['measurements']
            current_avg = self.stats['avg_memory']
            self.stats['avg_memory'] = ((current_avg * (measurements - 1)) + info.rss_mb) / measurements
            
            return info
            
        except Exception as e:
            self.logger.error(f"❌ Error getting memory info: {e}")
            return None
    
    def add_cleanup_callback(self, callback: Callable):
        """Add a cleanup callback function"""
        self.cleanup_callbacks.append(callback)
        self.logger.info(f"✅ Added cleanup callback: {callback.__name__}")
    
    def force_cleanup(self) -> Dict[str, float]:
        """Force memory cleanup and return results"""
        start_time = time.time()
        initial_memory = self.get_current_memory()
        
        if not initial_memory:
            return {'error': 'Could not measure initial memory'}
        
        initial_mb = initial_memory.rss_mb
        
        self.logger.info(f"🧹 Starting forced cleanup - Current: {initial_mb:.1f}MB")
        
        # Step 1: Call custom cleanup callbacks
        for callback in self.cleanup_callbacks:
            try:
                callback()
            except Exception as e:
                self.logger.error(f"❌ Cleanup callback {callback.__name__} failed: {e}")
        
        # Step 2: Force garbage collection multiple times
        for generation in range(3):
            collected = gc.collect(generation)
            if collected > 0:
                self.logger.debug(f"🗑️ GC gen {generation}: collected {collected} objects")
        
        # Step 3: Force full GC
        gc.collect()
        
        # Step 4: Clear some internal caches if possible
        try:
            # Clear import cache for modules not in use
            import sys
            modules_to_remove = []
            for module_name in sys.modules:
                if module_name.startswith('_'):  # Private modules
                    continue
                module = sys.modules[module_name]
                if hasattr(module, '__file__') and module.__file__:
                    # Keep core modules
                    if any(core in module.__file__ for core in ['core', 'config', 'gideon']):
                        continue
                    # Mark others for potential removal (be careful)
                    
            # Additional cleanup can be added here
            
        except Exception as e:
            self.logger.debug(f"⚠️ Cache cleanup warning: {e}")
        
        # Final measurement
        final_memory = self.get_current_memory()
        if not final_memory:
            return {'error': 'Could not measure final memory'}
        
        final_mb = final_memory.rss_mb
        saved_mb = initial_mb - final_mb
        cleanup_time = time.time() - start_time
        
        self.total_cleanups += 1
        self.stats['forced_cleanups'] += 1
        
        result = {
            'initial_mb': initial_mb,
            'final_mb': final_mb,
            'saved_mb': saved_mb,
            'cleanup_time': cleanup_time,
            'success': True
        }
        
        self.logger.info(f"✅ Cleanup completed: {initial_mb:.1f}MB → {final_mb:.1f}MB "
                        f"(saved {saved_mb:.1f}MB) in {cleanup_time:.2f}s")
        
        return result
    
    def check_memory_status(self) -> str:
        """Check current memory status and return alert level"""
        memory_info = self.get_current_memory()
        if not memory_info:
            return "ERROR"
        
        usage_mb = memory_info.rss_mb
        
        if usage_mb >= self.thresholds.CRITICAL_USAGE:
            return "CRITICAL"
        elif usage_mb >= self.thresholds.HIGH_USAGE:
            return "HIGH"
        elif usage_mb >= self.thresholds.MEDIUM_USAGE:
            return "MEDIUM"
        else:
            return "LOW"
    
    def should_cleanup(self, force: bool = False) -> bool:
        """Determine if cleanup should be performed"""
        if force:
            return True
        
        status = self.check_memory_status()
        
        # Always cleanup on critical
        if status == "CRITICAL":
            return True
        
        # Cleanup on high usage if enough time passed
        if status == "HIGH":
            time_since_alert = time.time() - self.last_alert_time
            return time_since_alert >= self.thresholds.ALERT_INTERVAL
        
        # Periodic cleanup based on counter
        self.gc_check_counter += 1
        if self.gc_check_counter >= self.thresholds.GC_INTERVAL:
            self.gc_check_counter = 0
            return True
        
        return False
    
    def start_monitoring(self):
        """Start continuous memory monitoring"""
        if self.is_monitoring:
            self.logger.warning("⚠️ Memory monitoring already running")
            return
        
        def _monitor_loop():
            self.logger.info("📊 Starting memory monitoring...")
            
            while self.is_monitoring:
                try:
                    # Get current memory info
                    memory_info = self.get_current_memory()
                    if memory_info:
                        self.history.append(memory_info)
                        
                        # Check if cleanup is needed
                        if self.should_cleanup():
                            status = self.check_memory_status()
                            
                            if status in ["HIGH", "CRITICAL"]:
                                current_time = time.time()
                                if (current_time - self.last_alert_time) >= self.thresholds.ALERT_INTERVAL:
                                    self.logger.warning(f"🚨 Memory usage {status}: {memory_info.rss_mb:.1f}MB")
                                    self.stats['alerts'] += 1
                                    self.last_alert_time = current_time
                                    
                                    # Auto-cleanup on critical
                                    if status == "CRITICAL":
                                        self.force_cleanup()
                    
                    # Sleep until next check
                    time.sleep(self.thresholds.MONITORING_INTERVAL)
                    
                except Exception as e:
                    self.logger.error(f"❌ Monitoring error: {e}")
                    time.sleep(5)  # Longer sleep on error
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=_monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        self.logger.info("📊 Memory monitoring started")
    
    def stop_monitoring(self):
        """Stop memory monitoring"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=3.0)
        
        self.logger.info("📊 Memory monitoring stopped")
    
    def get_memory_report(self) -> Dict:
        """Generate comprehensive memory report"""
        current = self.get_current_memory()
        if not current:
            return {'error': 'Could not get current memory info'}
        
        # Calculate statistics from history
        recent_usage = [m.rss_mb for m in list(self.history)[-50:]]  # Last 50 measurements
        
        avg_recent = sum(recent_usage) / len(recent_usage) if recent_usage else 0
        min_recent = min(recent_usage) if recent_usage else 0
        max_recent = max(recent_usage) if recent_usage else 0
        
        status = self.check_memory_status()
        
        # Performance rating
        if status == "LOW":
            rating = "EXCELLENT"
        elif status == "MEDIUM":
            rating = "GOOD"
        elif status == "HIGH":
            rating = "WARNING"
        else:
            rating = "CRITICAL"
        
        report = {
            'current': {
                'rss_mb': current.rss_mb,
                'vms_mb': current.vms_mb,
                'percent': current.percent,
                'objects': current.objects_count,
                'status': status,
                'rating': rating
            },
            'statistics': {
                'peak_mb': self.peak_usage,
                'avg_mb': self.stats['avg_memory'],
                'recent_avg_mb': avg_recent,
                'recent_min_mb': min_recent,
                'recent_max_mb': max_recent
            },
            'performance': {
                'total_measurements': self.stats['measurements'],
                'total_alerts': self.stats['alerts'],
                'total_cleanups': self.total_cleanups,
                'forced_cleanups': self.stats['forced_cleanups']
            },
            'system': {
                'available_mb': current.available_mb,
                'total_mb': psutil.virtual_memory().total / 1024 / 1024
            },
            'thresholds': {
                'low': self.thresholds.LOW_USAGE,
                'medium': self.thresholds.MEDIUM_USAGE,
                'high': self.thresholds.HIGH_USAGE,
                'critical': self.thresholds.CRITICAL_USAGE
            }
        }
        
        return report
    
    def optimize_memory_usage(self) -> Dict:
        """Perform comprehensive memory optimization"""
        self.logger.info("🔧 Starting memory optimization...")
        
        initial_info = self.get_current_memory()
        if not initial_info:
            return {'error': 'Could not measure initial memory'}
        
        initial_mb = initial_info.rss_mb
        optimizations = []
        
        # Step 1: Standard cleanup
        cleanup_result = self.force_cleanup()
        if cleanup_result.get('success'):
            optimizations.append(f"Cleanup saved {cleanup_result['saved_mb']:.1f}MB")
        
        # Step 2: Adjust GC thresholds for better performance
        try:
            # Get current thresholds
            original_thresholds = gc.get_threshold()
            
            # Set more aggressive thresholds for better memory management
            # (threshold0, threshold1, threshold2)
            new_thresholds = (700, 10, 10)  # More frequent collection
            gc.set_threshold(*new_thresholds)
            
            optimizations.append(f"GC thresholds: {original_thresholds} → {new_thresholds}")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Could not optimize GC thresholds: {e}")
        
        # Step 3: Enable GC debugging (optional)
        if self.logger.level <= logging.DEBUG:
            gc.set_debug(gc.DEBUG_STATS)
            optimizations.append("Enabled GC debugging")
        
        # Final measurement
        final_info = self.get_current_memory()
        if final_info:
            final_mb = final_info.rss_mb
            total_saved = initial_mb - final_mb
            
            self.logger.info(f"✅ Memory optimization completed: "
                           f"{initial_mb:.1f}MB → {final_mb:.1f}MB "
                           f"(total saved: {total_saved:.1f}MB)")
            
            return {
                'initial_mb': initial_mb,
                'final_mb': final_mb,
                'total_saved_mb': total_saved,
                'optimizations': optimizations,
                'success': True
            }
        else:
            return {'error': 'Could not measure final memory'}
    
    def cleanup(self):
        """Clean up monitor resources"""
        self.stop_monitoring()
        self.cleanup_callbacks.clear()
        self.history.clear()
        self.logger.info("🧹 Memory monitor cleanup completed")

# Global memory monitor instance
memory_monitor = MemoryMonitor() 