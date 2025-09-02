import cv2
import numpy as np
from ultralytics import YOLO
import threading
import time
from typing import List, Tuple, Dict, Any
from visual_memory import VisualMemory
import json
import os

class ZoneFocusedDetector:
    """Object detector that only detects objects within defined zones"""
    
    def __init__(self, model_path: str = "yolo11n.pt", confidence_threshold: float = 0.15):
        self.model = YOLO(model_path)
        self.confidence_threshold = confidence_threshold
        self.visual_memory = VisualMemory()
        self.is_detecting = False
        self.detection_thread = None
        self.zones_file = "zones.json"
        self.zones = []
        
    def load_zones(self):
        """Load custom zones from JSON file"""
        if os.path.exists(self.zones_file):
            try:
                with open(self.zones_file, 'r') as f:
                    self.zones = json.load(f)
                print(f"📍 Loaded {len(self.zones)} zones for focused detection")
                return True
            except Exception as e:
                print(f"❌ Error loading zones: {e}")
                return False
        return False
    
    def is_point_in_zone(self, point: Tuple[float, float], zone: Dict) -> bool:
        """Check if a point is within a zone"""
        x, y = point
        zone_x, zone_y, zone_w, zone_h = zone["bbox"]
        
        return (zone_x <= x <= zone_x + zone_w and 
                zone_y <= y <= zone_y + zone_h)
    
    def get_zone_for_point(self, point: Tuple[float, float]) -> str:
        """Get zone name for a given point"""
        for zone in self.zones:
            if self.is_point_in_zone(point, zone):
                return zone["name"]
        return "outside_zones"
    
    def detect_objects_in_zones(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Detect objects only within defined zones"""
        if not self.zones:
            print("⚠️  No zones loaded, using full frame detection")
            return self.detect_objects_full_frame(frame)
        
        results = self.model(frame, conf=self.confidence_threshold)
        zone_detections = []
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    # Get bounding box coordinates
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = box.conf[0].cpu().numpy()
                    class_id = int(box.cls[0].cpu().numpy())
                    class_name = self.model.names[class_id]
                    
                    # Calculate object center point
                    center_x = (x1 + x2) / 2
                    center_y = (y1 + y2) / 2
                    
                    # Check if object center is in any zone
                    zone_name = self.get_zone_for_point((center_x, center_y))
                    
                    if zone_name != "outside_zones":
                        # Convert to (x, y, width, height) format
                        x, y, w, h = x1, y1, x2-x1, y2-y1
                        
                        detection = {
                            'class_name': class_name,
                            'confidence': float(confidence),
                            'bbox': (x, y, w, h),
                            'class_id': class_id,
                            'zone_name': zone_name
                        }
                        zone_detections.append(detection)
        
        return zone_detections
    
    def detect_objects_full_frame(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Fallback: detect objects in full frame if no zones"""
        results = self.model(frame, conf=self.confidence_threshold)
        detections = []
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = box.conf[0].cpu().numpy()
                    class_id = int(box.cls[0].cpu().numpy())
                    class_name = self.model.names[class_id]
                    
                    x, y, w, h = x1, y1, x2-x1, y2-y1
                    
                    detection = {
                        'class_name': class_name,
                        'confidence': float(confidence),
                        'bbox': (x, y, w, h),
                        'class_id': class_id,
                        'zone_name': 'full_frame'
                    }
                    detections.append(detection)
        
        return detections
    
    def draw_detections(self, frame: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """Draw bounding boxes and labels on frame"""
        frame_copy = frame.copy()
        
        # Draw zones first
        for zone in self.zones:
            x, y, w, h = zone["bbox"]
            name = zone["name"]
            
            # Draw zone rectangle (blue)
            cv2.rectangle(frame_copy, (int(x), int(y)), 
                         (int(x + w), int(y + h)), (255, 0, 0), 2)
            
            # Draw zone label
            cv2.putText(frame_copy, f"Zone: {name}", (int(x), int(y) - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        
        # Draw object detections
        for detection in detections:
            x, y, w, h = detection['bbox']
            class_name = detection['class_name']
            confidence = detection['confidence']
            zone_name = detection.get('zone_name', 'unknown')
            
            # Draw bounding box (green for zone objects)
            cv2.rectangle(frame_copy, (int(x), int(y)), 
                         (int(x + w), int(y + h)), (0, 255, 0), 2)
            
            # Draw label with zone info
            label = f"{class_name}: {confidence:.2f} ({zone_name})"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            cv2.rectangle(frame_copy, (int(x), int(y) - label_size[1] - 10),
                         (int(x) + label_size[0], int(y)), (0, 255, 0), -1)
            cv2.putText(frame_copy, label, (int(x), int(y) - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
        
        return frame_copy
    
    def start_continuous_detection(self, camera_index: int = 0, save_interval: int = 1):
        """Start continuous object detection from camera"""
        # Load zones first
        if not self.load_zones():
            print("⚠️  No zones found, will detect in full frame")
        
        self.is_detecting = True
        self.detection_thread = threading.Thread(
            target=self._detection_loop, 
            args=(camera_index, save_interval)
        )
        self.detection_thread.start()
    
    def stop_detection(self):
        """Stop continuous detection"""
        self.is_detecting = False
        if self.detection_thread:
            self.detection_thread.join()
    
    def _detection_loop(self, camera_index: int, save_interval: int):
        """Main detection loop running in separate thread"""
        cap = cv2.VideoCapture(camera_index)
        
        if not cap.isOpened():
            print(f"❌ Error: Could not open camera {camera_index}")
            return
        
        frame_count = 0
        
        try:
            while self.is_detecting:
                ret, frame = cap.read()
                if not ret:
                    print("❌ Error: Could not read frame from camera")
                    break
                
                # Detect objects in zones only
                detections = self.detect_objects_in_zones(frame)
                
                # Draw detections on frame
                frame_with_detections = self.draw_detections(frame, detections)
                
                # Add status info
                cv2.putText(frame_with_detections, f"Zone-Focused Detection: {len(detections)} objects", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                cv2.putText(frame_with_detections, f"Zones: {len(self.zones)}", 
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                # Display frame
                cv2.imshow('Zone-Focused AI Home Assistant', frame_with_detections)
                
                # Save detections to memory
                if frame_count % save_interval == 0 and detections:
                    self._save_detections_to_memory(detections, frame.shape[:2])
                    print(f"📝 Saved {len(detections)} zone detections to memory")
                
                frame_count += 1
                
                # Check for exit key
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
        finally:
            cap.release()
            cv2.destroyAllWindows()
    
    def _save_detections_to_memory(self, detections: List[Dict], frame_size: Tuple[int, int]):
        """Save detections to visual memory with zone information"""
        for detection in detections:
            bbox = detection['bbox']
            zone_name = detection.get('zone_name', 'unknown_zone')
            
            self.visual_memory.add_detection(
                object_name=detection['class_name'],
                confidence=detection['confidence'],
                bbox=bbox,
                frame_size=frame_size,
                location_description=zone_name
            )
    
    def get_detection_summary(self) -> Dict[str, Any]:
        """Get summary of recent detections"""
        recent_detections = self.visual_memory.get_recent_detections(hours=1)
        all_objects = self.visual_memory.get_all_objects()
        
        summary = {
            'total_objects_detected': len(all_objects),
            'recent_detections_count': len(recent_detections),
            'objects_list': all_objects,
            'recent_objects': list(set([d['object_name'] for d in recent_detections])),
            'zones_count': len(self.zones),
            'zone_names': [zone['name'] for zone in self.zones]
        }
        
        return summary
