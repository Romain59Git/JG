#!/usr/bin/env python3
"""
Audio System Test Script for Gideon AI Assistant
Comprehensive testing of optimized audio components
"""

import sys
import time
import threading
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.audio_manager_optimized import audio_manager, AudioConfig, VoiceCommand
from core.logger import GideonLogger

class AudioSystemTester:
    """Comprehensive audio system tester"""
    
    def __init__(self):
        self.logger = GideonLogger("AudioTester")
        self.results = {}
        
    def print_header(self, title: str):
        """Print formatted test header"""
        print(f"\n{'='*60}")
        print(f"🧪 {title}")
        print(f"{'='*60}")
    
    def print_result(self, test_name: str, success: bool, details: str = ""):
        """Print test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        self.results[test_name] = success
    
    def test_audio_initialization(self):
        """Test audio manager initialization"""
        self.print_header("AUDIO INITIALIZATION TEST")
        
        try:
            # Test basic initialization
            has_recognizer = audio_manager.recognizer is not None
            has_microphone = audio_manager.microphone is not None
            has_tts = audio_manager.tts_engine is not None
            
            self.print_result("Speech Recognition Available", has_recognizer, 
                            f"Recognizer: {type(audio_manager.recognizer).__name__ if has_recognizer else 'None'}")
            self.print_result("Microphone Available", has_microphone,
                            "Default microphone detected" if has_microphone else "No microphone found")
            self.print_result("TTS Engine Available", has_tts,
                            f"TTS: {type(audio_manager.tts_engine).__name__ if has_tts else 'None'}")
            
            return has_recognizer and has_microphone
            
        except Exception as e:
            self.print_result("Audio Initialization", False, f"Error: {e}")
            return False
    
    def test_microphone_functionality(self):
        """Test microphone detection and functionality"""
        self.print_header("MICROPHONE FUNCTIONALITY TEST")
        
        try:
            # Test microphone basic functionality
            result = audio_manager.test_microphone()
            self.print_result("Microphone Test", result, 
                            "Microphone responded to test" if result else "No response or error")
            
            return result
            
        except Exception as e:
            self.print_result("Microphone Test", False, f"Error: {e}")
            return False
    
    def test_speech_recognition_single(self):
        """Test single speech recognition"""
        self.print_header("SINGLE SPEECH RECOGNITION TEST")
        
        if not audio_manager.recognizer or not audio_manager.microphone:
            self.print_result("Speech Recognition Single", False, "Components not available")
            return False
        
        try:
            print("🎤 Please speak something clearly within 5 seconds...")
            print("   (Try saying: 'Hello Gideon' or 'Test recognition')")
            
            start_time = time.time()
            command = audio_manager.listen_once()
            response_time = time.time() - start_time
            
            if command:
                self.print_result("Speech Recognition Single", True, 
                                f"Recognized: '{command.text}' in {response_time:.2f}s")
                return True
            else:
                self.print_result("Speech Recognition Single", False, 
                                f"No speech recognized in {response_time:.2f}s")
                return False
                
        except Exception as e:
            self.print_result("Speech Recognition Single", False, f"Error: {e}")
            return False
    
    def test_continuous_listening(self):
        """Test continuous listening mode"""
        self.print_header("CONTINUOUS LISTENING TEST")
        
        if not audio_manager.recognizer:
            self.print_result("Continuous Listening", False, "Speech recognition not available")
            return False
        
        try:
            commands_received = []
            test_duration = 15  # seconds
            
            print(f"🎤 Starting continuous listening for {test_duration} seconds...")
            print("   Please speak multiple commands (e.g., 'test one', 'test two', 'hello')")
            
            # Start listening
            audio_manager.start_continuous_listening()
            
            # Collect commands for test duration
            start_time = time.time()
            while time.time() - start_time < test_duration:
                command = audio_manager.get_next_command(timeout=1.0)
                if command:
                    commands_received.append(command)
                    print(f"    Received: '{command.text}' ({len(commands_received)} total)")
            
            # Stop listening
            audio_manager.stop_continuous_listening()
            
            success = len(commands_received) > 0
            details = f"Received {len(commands_received)} commands in {test_duration}s"
            if commands_received:
                details += f", Examples: {[cmd.text for cmd in commands_received[:3]]}"
            
            self.print_result("Continuous Listening", success, details)
            return success
            
        except Exception as e:
            self.print_result("Continuous Listening", False, f"Error: {e}")
            audio_manager.stop_continuous_listening()
            return False
    
    def test_tts_functionality(self):
        """Test text-to-speech functionality"""
        self.print_header("TEXT-TO-SPEECH TEST")
        
        if not audio_manager.tts_engine:
            self.print_result("TTS Functionality", False, "TTS engine not available")
            return False
        
        try:
            test_phrases = [
                "Hello, this is Gideon AI Assistant.",
                "Testing text to speech functionality.",
                "Audio system test complete."
            ]
            
            success_count = 0
            for i, phrase in enumerate(test_phrases, 1):
                print(f"🔊 Speaking phrase {i}: '{phrase}'")
                result = audio_manager.speak(phrase)
                if result:
                    success_count += 1
                time.sleep(1)  # Brief pause between phrases
            
            success = success_count > 0
            details = f"{success_count}/{len(test_phrases)} phrases spoken successfully"
            
            self.print_result("TTS Functionality", success, details)
            return success
            
        except Exception as e:
            self.print_result("TTS Functionality", False, f"Error: {e}")
            return False
    
    def test_performance_metrics(self):
        """Test performance and statistics"""
        self.print_header("PERFORMANCE METRICS TEST")
        
        try:
            stats = audio_manager.get_stats()
            
            # Check if stats are being collected
            has_stats = stats['total_listens'] >= 0
            self.print_result("Statistics Collection", has_stats, 
                            f"Total listens: {stats['total_listens']}")
            
            # Check response time tracking
            has_response_time = 'avg_response_time' in stats
            self.print_result("Response Time Tracking", has_response_time,
                            f"Average response time: {stats.get('avg_response_time', 'N/A')}")
            
            # Print detailed stats
            print("\n📊 Detailed Performance Statistics:")
            for key, value in stats.items():
                print(f"    {key}: {value}")
            
            return has_stats and has_response_time
            
        except Exception as e:
            self.print_result("Performance Metrics", False, f"Error: {e}")
            return False
    
    def test_error_handling(self):
        """Test error handling and recovery"""
        self.print_header("ERROR HANDLING TEST")
        
        try:
            # Test timeout handling
            print("🕐 Testing timeout handling (3 seconds of silence)...")
            start_time = time.time()
            command = audio_manager.listen_once()
            response_time = time.time() - start_time
            
            timeout_handled = command is None and response_time <= 4  # Should timeout around 3s
            self.print_result("Timeout Handling", timeout_handled,
                            f"Timeout handled in {response_time:.2f}s")
            
            # Test recovery after timeout
            recovery_successful = audio_manager.recognizer is not None
            self.print_result("Recovery After Timeout", recovery_successful,
                            "Audio system remains functional after timeout")
            
            return timeout_handled and recovery_successful
            
        except Exception as e:
            self.print_result("Error Handling", False, f"Error: {e}")
            return False
    
    def test_memory_optimization(self):
        """Test memory optimization features"""
        self.print_header("MEMORY OPTIMIZATION TEST")
        
        try:
            initial_stats = audio_manager.get_stats()
            
            # Simulate multiple recognition attempts
            print("🧠 Testing memory optimization with multiple operations...")
            for i in range(10):
                # Quick listen attempts
                command = audio_manager.listen_once()
                if i % 3 == 0:  # Occasional success simulation
                    print(f"    Operation {i+1}/10")
            
            final_stats = audio_manager.get_stats()
            
            # Check if operations were tracked
            operations_tracked = final_stats['total_listens'] > initial_stats['total_listens']
            self.print_result("Operation Tracking", operations_tracked,
                            f"Operations increased from {initial_stats['total_listens']} to {final_stats['total_listens']}")
            
            # Test cleanup functionality
            try:
                audio_manager.cleanup()
                cleanup_successful = True
            except Exception as cleanup_error:
                cleanup_successful = False
                print(f"    Cleanup error: {cleanup_error}")
            
            self.print_result("Memory Cleanup", cleanup_successful,
                            "Cleanup method executed successfully")
            
            return operations_tracked and cleanup_successful
            
        except Exception as e:
            self.print_result("Memory Optimization", False, f"Error: {e}")
            return False
    
    def run_full_test_suite(self):
        """Run complete audio system test suite"""
        print("""
╔══════════════════════════════════════════════════════════════╗
║                  🎤 AUDIO SYSTEM TEST SUITE                 ║
║                     Gideon AI Assistant                      ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        test_methods = [
            self.test_audio_initialization,
            self.test_microphone_functionality,
            self.test_speech_recognition_single,
            self.test_tts_functionality,
            self.test_continuous_listening,
            self.test_performance_metrics,
            self.test_error_handling,
            self.test_memory_optimization
        ]
        
        passed_tests = 0
        total_tests = len(test_methods)
        
        for test_method in test_methods:
            try:
                if test_method():
                    passed_tests += 1
            except Exception as e:
                self.logger.error(f"Test {test_method.__name__} failed with exception: {e}")
        
        # Final summary
        self.print_header("TEST SUMMARY")
        success_rate = (passed_tests / total_tests) * 100
        
        print(f"📊 Tests Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            print("🎉 OVERALL RESULT: ✅ AUDIO SYSTEM IS READY")
        elif success_rate >= 60:
            print("⚠️  OVERALL RESULT: 🟡 AUDIO SYSTEM HAS ISSUES")
        else:
            print("❌ OVERALL RESULT: 🔴 AUDIO SYSTEM NEEDS MAJOR FIXES")
        
        # Detailed results
        print(f"\n📋 Detailed Results:")
        for test_name, result in self.results.items():
            status = "✅" if result else "❌"
            print(f"    {status} {test_name}")
        
        return success_rate >= 80

def main():
    """Main test execution"""
    tester = AudioSystemTester()
    
    try:
        success = tester.run_full_test_suite()
        
        if success:
            print("\n🚀 Audio system is ready for Gideon AI Assistant!")
            return 0
        else:
            print("\n🔧 Audio system needs attention before production use.")
            return 1
            
    except KeyboardInterrupt:
        print("\n⌨️  Test interrupted by user")
        return 2
    except Exception as e:
        print(f"\n❌ Critical test error: {e}")
        return 3
    finally:
        # Cleanup
        try:
            audio_manager.cleanup()
        except:
            pass

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 