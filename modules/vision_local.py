#!/usr/bin/env python3
"""
Local Vision Manager - Computer Vision Integration  
100% Local face recognition and camera management
"""

import cv2
import numpy as np
import logging
import time
import threading
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any, Callable
from dataclasses import dataclass

try:
    import face_recognition
    HAS_FACE_RECOGNITION = True
except ImportError:
    HAS_FACE_RECOGNITION = False

try:
    import mediapipe as mp
    HAS_MEDIAPIPE = True
except ImportError:
    HAS_MEDIAPIPE = False

from config import config


@dataclass
class FaceDetection:
    """Face detection result with metadata"""
    bounding_box: Tuple[int, int, int, int]  # (x, y, width, height)
    confidence: float
    is_known_user: bool = False
    recognition_confidence: float = 0.0
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


@dataclass
class CameraInfo:
    """Camera information and status"""
    index: int
    name: str
    resolution: Tuple[int, int]
    fps: float
    is_available: bool


class LocalFaceDetector:
    """Local face detection using OpenCV and optional MediaPipe"""
    
    def __init__(self):
        self.logger = logging.getLogger("FaceDetector")
        
        # OpenCV cascade classifier
        self.face_cascade = None
        self._load_opencv_cascade()
        
        # MediaPipe face detection (if available)
        self.mp_face_detection = None
        self.mp_drawing = None
        if HAS_MEDIAPIPE:
            self._init_mediapipe()
        
        # Detection settings
        self.min_face_size = config.vision.MIN_FACE_SIZE
        self.scale_factor = config.vision.SCALE_FACTOR
        self.min_neighbors = config.vision.MIN_NEIGHBORS
        
        self.logger.info("👁️ Face detector initialized")
    
    def _load_opencv_cascade(self):
        """Load OpenCV face cascade classifier"""
        try:
            # Try to load from config path first
            cascade_path = Path(config.vision.FACE_CASCADE_PATH)
            
            if not cascade_path.exists():
                # Try OpenCV's built-in cascade
                import cv2.data
                cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
            
            if cascade_path.exists():
                self.face_cascade = cv2.CascadeClassifier(str(cascade_path))
                self.logger.info(f"✅ OpenCV cascade loaded: {cascade_path}")
            else:
                self.logger.error("❌ OpenCV face cascade not found")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to load OpenCV cascade: {e}")
    
    def _init_mediapipe(self):
        """Initialize MediaPipe face detection"""
        try:
            self.mp_face_detection = mp.solutions.face_detection.FaceDetection(
                model_selection=0,  # 0 for short-range detection
                min_detection_confidence=0.5
            )
            self.mp_drawing = mp.solutions.drawing_utils
            self.logger.info("✅ MediaPipe face detection initialized")
            
        except Exception as e:
            self.logger.error(f"❌ MediaPipe initialization failed: {e}")
    
    def detect_faces_opencv(self, frame: np.ndarray) -> List[FaceDetection]:
        """Detect faces using OpenCV"""
        if self.face_cascade is None:
            return []
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=self.scale_factor,
                minNeighbors=self.min_neighbors,
                minSize=self.min_face_size
            )
            
            # Convert to FaceDetection objects
            detections = []
            for (x, y, w, h) in faces:
                detection = FaceDetection(
                    bounding_box=(x, y, w, h),
                    confidence=0.8  # OpenCV doesn't provide confidence
                )
                detections.append(detection)
            
            return detections
            
        except Exception as e:
            self.logger.error(f"❌ OpenCV face detection failed: {e}")
            return []
    
    def detect_faces_mediapipe(self, frame: np.ndarray) -> List[FaceDetection]:
        """Detect faces using MediaPipe"""
        if self.mp_face_detection is None:
            return []
        
        try:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process frame
            results = self.mp_face_detection.process(rgb_frame)
            
            detections = []
            if results.detections:
                h, w, _ = frame.shape
                
                for detection in results.detections:
                    bbox = detection.location_data.relative_bounding_box
                    
                    # Convert relative coordinates to absolute
                    x = int(bbox.xmin * w)
                    y = int(bbox.ymin * h)
                    width = int(bbox.width * w)
                    height = int(bbox.height * h)
                    
                    confidence = detection.score[0] if detection.score else 0.5
                    
                    face_detection = FaceDetection(
                        bounding_box=(x, y, width, height),
                        confidence=confidence
                    )
                    detections.append(face_detection)
            
            return detections
            
        except Exception as e:
            self.logger.error(f"❌ MediaPipe face detection failed: {e}")
            return []
    
    def detect_faces(self, frame: np.ndarray, prefer_mediapipe: bool = True) -> List[FaceDetection]:
        """Detect faces using best available method"""
        if prefer_mediapipe and self.mp_face_detection:
            return self.detect_faces_mediapipe(frame)
        elif self.face_cascade:
            return self.detect_faces_opencv(frame)
        else:
            return []
    
    def is_available(self) -> bool:
        """Check if face detection is available"""
        return self.face_cascade is not None or self.mp_face_detection is not None


class LocalFaceRecognizer:
    """Local face recognition using face_recognition library"""
    
    def __init__(self):
        self.logger = logging.getLogger("FaceRecognizer")
        
        # Known face encodings
        self.known_face_encodings = []
        self.known_face_names = []
        
        # Recognition settings
        self.recognition_threshold = config.vision.FACE_RECOGNITION_THRESHOLD
        
        # Load reference face if available
        self._load_reference_face()
        
        self.logger.info("🔍 Face recognizer initialized")
    
    def _load_reference_face(self):
        """Load reference face from image"""
        if not HAS_FACE_RECOGNITION:
            self.logger.warning("⚠️ face_recognition library not available")
            return
        
        try:
            ref_image_path = Path(config.vision.USER_REFERENCE_IMAGE)
            
            if ref_image_path.exists():
                # Load and encode reference image
                reference_image = face_recognition.load_image_file(str(ref_image_path))
                reference_encodings = face_recognition.face_encodings(reference_image)
                
                if reference_encodings:
                    self.known_face_encodings.append(reference_encodings[0])
                    self.known_face_names.append("User")
                    self.logger.info(f"✅ Reference face loaded: {ref_image_path}")
                else:
                    self.logger.warning("⚠️ No face found in reference image")
            else:
                self.logger.info("ℹ️ No reference face image found")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to load reference face: {e}")
    
    def recognize_faces(self, frame: np.ndarray, face_locations: List[Tuple[int, int, int, int]]) -> List[str]:
        """Recognize faces in frame"""
        if not HAS_FACE_RECOGNITION or not self.known_face_encodings:
            return ["Unknown"] * len(face_locations)
        
        try:
            # Convert OpenCV format (x,y,w,h) to face_recognition format (top,right,bottom,left)
            face_recognition_locations = []
            for (x, y, w, h) in face_locations:
                top, right, bottom, left = y, x + w, y + h, x
                face_recognition_locations.append((top, right, bottom, left))
            
            # Encode faces in current frame
            face_encodings = face_recognition.face_encodings(frame, face_recognition_locations)
            
            # Recognize each face
            names = []
            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(
                    self.known_face_encodings, 
                    face_encoding,
                    tolerance=self.recognition_threshold
                )
                
                name = "Unknown"
                
                # Use the known face with the smallest distance
                face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                
                if matches[best_match_index] and face_distances[best_match_index] < self.recognition_threshold:
                    name = self.known_face_names[best_match_index]
                
                names.append(name)
            
            return names
            
        except Exception as e:
            self.logger.error(f"❌ Face recognition failed: {e}")
            return ["Unknown"] * len(face_locations)
    
    def capture_reference_face(self, frame: np.ndarray, face_location: Tuple[int, int, int, int]) -> bool:
        """Capture and save new reference face"""
        try:
            x, y, w, h = face_location
            
            # Extract face region
            face_region = frame[y:y+h, x:x+w]
            
            # Save reference image
            ref_image_path = Path(config.vision.USER_REFERENCE_IMAGE)
            ref_image_path.parent.mkdir(parents=True, exist_ok=True)
            
            cv2.imwrite(str(ref_image_path), face_region)
            
            # Reload reference face
            self._load_reference_face()
            
            self.logger.info(f"✅ Reference face captured: {ref_image_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to capture reference face: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if face recognition is available"""
        return HAS_FACE_RECOGNITION and len(self.known_face_encodings) > 0


class CameraManager:
    """Local camera management and streaming"""
    
    def __init__(self):
        self.logger = logging.getLogger("CameraManager")
        
        # Camera state
        self.camera = None
        self.is_active = False
        self.current_camera_index = 0
        
        # Camera settings
        self.resolution = config.vision.CAMERA_RESOLUTION
        self.frame_skip = config.vision.FRAME_SKIP
        self.frame_count = 0
        
        # Available cameras
        self.available_cameras = self._detect_cameras()
        
        self.logger.info(f"📹 Camera manager initialized: {len(self.available_cameras)} cameras found")
    
    def _detect_cameras(self) -> List[CameraInfo]:
        """Detect available cameras"""
        cameras = []
        
        # Test camera indices 0-5
        for index in range(6):
            try:
                cap = cv2.VideoCapture(index)
                
                if cap.isOpened():
                    # Get camera properties
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    
                    camera_info = CameraInfo(
                        index=index,
                        name=f"Camera {index}",
                        resolution=(width, height),
                        fps=fps,
                        is_available=True
                    )
                    cameras.append(camera_info)
                
                cap.release()
                
            except Exception as e:
                self.logger.debug(f"Camera {index} not available: {e}")
                continue
        
        return cameras
    
    def start_camera(self, camera_index: int = 0) -> bool:
        """Start camera capture"""
        try:
            if self.is_active:
                self.stop_camera()
            
            self.camera = cv2.VideoCapture(camera_index)
            
            if not self.camera.isOpened():
                self.logger.error(f"❌ Failed to open camera {camera_index}")
                return False
            
            # Set camera properties
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            
            self.current_camera_index = camera_index
            self.is_active = True
            self.frame_count = 0
            
            self.logger.info(f"✅ Camera {camera_index} started: {self.resolution}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start camera: {e}")
            return False
    
    def stop_camera(self):
        """Stop camera capture"""
        try:
            if self.camera:
                self.camera.release()
                self.camera = None
            
            self.is_active = False
            self.logger.info("📹 Camera stopped")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to stop camera: {e}")
    
    def capture_frame(self) -> Optional[np.ndarray]:
        """Capture single frame from camera"""
        if not self.is_active or not self.camera:
            return None
        
        try:
            ret, frame = self.camera.read()
            
            if ret:
                self.frame_count += 1
                return frame
            else:
                self.logger.warning("⚠️ Failed to capture frame")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Frame capture failed: {e}")
            return None
    
    def should_process_frame(self) -> bool:
        """Determine if current frame should be processed (for performance)"""
        return self.frame_count % self.frame_skip == 0
    
    def get_camera_info(self) -> Optional[CameraInfo]:
        """Get current camera information"""
        if not self.is_active:
            return None
        
        for cam_info in self.available_cameras:
            if cam_info.index == self.current_camera_index:
                return cam_info
        
        return None
    
    def is_available(self) -> bool:
        """Check if camera is available"""
        return len(self.available_cameras) > 0


class VisionManager:
    """Main vision manager orchestrating all computer vision components"""
    
    def __init__(self):
        self.logger = logging.getLogger("VisionManager")
        
        # Initialize components
        self.face_detector = LocalFaceDetector()
        self.face_recognizer = LocalFaceRecognizer()
        self.camera_manager = CameraManager()
        
        # Monitoring state
        self.is_monitoring = False
        self.monitoring_thread = None
        self.user_detection_callbacks = []
        
        # Statistics
        self.stats = {
            'frames_processed': 0,
            'faces_detected': 0,
            'user_recognitions': 0,
            'false_detections': 0,
            'avg_processing_time': 0
        }
        
        self.logger.info("👁️ Vision Manager initialized")
    
    def add_user_detection_callback(self, callback: Callable[[bool], None]):
        """Add callback for user presence detection"""
        self.user_detection_callbacks.append(callback)
    
    def _notify_user_presence(self, user_present: bool):
        """Notify callbacks about user presence"""
        for callback in self.user_detection_callbacks:
            try:
                callback(user_present)
            except Exception as e:
                self.logger.error(f"❌ Callback error: {e}")
    
    def detect_and_recognize_faces(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Detect and recognize faces in frame"""
        start_time = time.time()
        
        try:
            # Detect faces
            face_detections = self.face_detector.detect_faces(frame)
            
            if not face_detections:
                return []
            
            # Extract face locations for recognition
            face_locations = [detection.bounding_box for detection in face_detections]
            
            # Recognize faces
            face_names = self.face_recognizer.recognize_faces(frame, face_locations)
            
            # Combine detection and recognition results
            results = []
            for detection, name in zip(face_detections, face_names):
                detection.is_known_user = (name == "User")
                
                result = {
                    'bounding_box': detection.bounding_box,
                    'confidence': detection.confidence,
                    'name': name,
                    'is_known_user': detection.is_known_user,
                    'timestamp': detection.timestamp
                }
                results.append(result)
            
            # Update statistics
            processing_time = time.time() - start_time
            self.stats['frames_processed'] += 1
            self.stats['faces_detected'] += len(results)
            
            known_users = sum(1 for r in results if r['is_known_user'])
            self.stats['user_recognitions'] += known_users
            
            # Update average processing time
            frames_processed = self.stats['frames_processed']
            current_avg = self.stats['avg_processing_time']
            self.stats['avg_processing_time'] = (
                (current_avg * (frames_processed - 1) + processing_time) / frames_processed
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Face detection/recognition failed: {e}")
            return []
    
    def start_monitoring(self, camera_index: int = 0) -> bool:
        """Start continuous face monitoring"""
        if self.is_monitoring:
            self.logger.warning("⚠️ Monitoring already active")
            return True
        
        # Start camera
        if not self.camera_manager.start_camera(camera_index):
            return False
        
        # Start monitoring thread
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        self.logger.info("👁️ Face monitoring started")
        return True
    
    def stop_monitoring(self):
        """Stop face monitoring"""
        self.is_monitoring = False
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2)
        
        self.camera_manager.stop_camera()
        self.logger.info("👁️ Face monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop running in separate thread"""
        last_user_seen = time.time()
        user_currently_present = False
        
        while self.is_monitoring:
            try:
                # Capture frame
                frame = self.camera_manager.capture_frame()
                
                if frame is None:
                    time.sleep(0.1)
                    continue
                
                # Skip frames for performance
                if not self.camera_manager.should_process_frame():
                    continue
                
                # Detect and recognize faces
                face_results = self.detect_and_recognize_faces(frame)
                
                # Check for known user
                user_detected = any(result['is_known_user'] for result in face_results)
                
                if user_detected:
                    last_user_seen = time.time()
                    
                    if not user_currently_present:
                        user_currently_present = True
                        self._notify_user_presence(True)
                        self.logger.info("👤 User detected")
                
                # Check if user left (no detection for 5 seconds)
                elif user_currently_present and time.time() - last_user_seen > 5:
                    user_currently_present = False
                    self._notify_user_presence(False)
                    self.logger.info("👤 User left")
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"❌ Monitoring loop error: {e}")
                time.sleep(1)
    
    def capture_reference_image(self) -> bool:
        """Capture new reference image for face recognition"""
        if not self.camera_manager.is_active:
            if not self.camera_manager.start_camera():
                return False
        
        try:
            # Capture frame
            frame = self.camera_manager.capture_frame()
            if frame is None:
                return False
            
            # Detect faces
            face_detections = self.face_detector.detect_faces(frame)
            
            if not face_detections:
                self.logger.warning("⚠️ No face detected for reference")
                return False
            
            # Use largest face
            largest_face = max(face_detections, key=lambda d: d.bounding_box[2] * d.bounding_box[3])
            
            # Capture reference face
            success = self.face_recognizer.capture_reference_face(frame, largest_face.bounding_box)
            
            if success:
                self.logger.info("✅ Reference face captured successfully")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Failed to capture reference: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive vision statistics"""
        stats = dict(self.stats)
        
        # Add component availability
        stats['face_detector_available'] = self.face_detector.is_available()
        stats['face_recognizer_available'] = self.face_recognizer.is_available()
        stats['camera_available'] = self.camera_manager.is_available()
        stats['monitoring_active'] = self.is_monitoring
        
        # Add camera info
        camera_info = self.camera_manager.get_camera_info()
        if camera_info:
            stats['camera_resolution'] = camera_info.resolution
            stats['camera_fps'] = camera_info.fps
        
        return stats
    
    def get_health_status(self) -> Dict[str, str]:
        """Get health status of all vision components"""
        return {
            'face_detector': 'healthy' if self.face_detector.is_available() else 'unavailable',
            'face_recognizer': 'healthy' if self.face_recognizer.is_available() else 'unavailable',  
            'camera_manager': 'healthy' if self.camera_manager.is_available() else 'unavailable',
            'overall': 'healthy' if all([
                self.face_detector.is_available(),
                self.camera_manager.is_available()
            ]) else 'degraded'
        }
    
    def cleanup(self):
        """Cleanup vision resources"""
        self.stop_monitoring()
        self.logger.info("🧹 Vision Manager cleanup completed")


# Global instance
vision_manager = VisionManager() 