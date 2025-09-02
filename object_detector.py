import cv2
import numpy as np
from ultralytics import YOLO
import threading
import time
from typing import List, Tuple, Dict, Any
from visual_memory import VisualMemory

class ObjectDetector:
    """Handles object detection using YOLO11n model"""
    
    def __init__(self, model_path: str = "yolo11n.pt", confidence_threshold: float = 0.3):
        self.model = YOLO(model_path)
        self.confidence_threshold = confidence_threshold
        self.visual_memory = VisualMemory()
        self.is_detecting = False
        self.detection_thread = None
        
    def detect_objects(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Detect objects in a single frame"""
        results = self.model(frame, conf=self.confidence_threshold)
        detections = []
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    # Get bounding box coordinates
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = box.conf[0].cpu().numpy()
                    class_id = int(box.cls[0].cpu().numpy())
                    class_name = self.model.names[class_id]
                    
                    # Convert to (x, y, width, height) format
                    x, y, w, h = x1, y1, x2-x1, y2-y1
                    
                    detection = {
                        'class_name': class_name,
                        'confidence': float(confidence),
                        'bbox': (x, y, w, h),
                        'class_id': class_id
                    }
                    detections.append(detection)
        
        return detections
    
    def draw_detections(self, frame: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """Draw bounding boxes and labels on frame"""
        frame_copy = frame.copy()
        
        for detection in detections:
            x, y, w, h = detection['bbox']
            class_name = detection['class_name']
            confidence = detection['confidence']
            
            # Draw bounding box
            cv2.rectangle(frame_copy, (int(x), int(y)), 
                         (int(x + w), int(y + h)), (0, 255, 0), 2)
            
            # Draw label
            label = f"{class_name}: {confidence:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            cv2.rectangle(frame_copy, (int(x), int(y) - label_size[1] - 10),
                         (int(x) + label_size[0], int(y)), (0, 255, 0), -1)
            cv2.putText(frame_copy, label, (int(x), int(y) - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
        
        return frame_copy
    
    def start_continuous_detection(self, camera_index: int = 0, save_interval: int = 1):
        """Start continuous object detection from camera"""
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
            print(f"Error: Could not open camera {camera_index}")
            return
        
        frame_count = 0
        
        try:
            while self.is_detecting:
                ret, frame = cap.read()
                if not ret:
                    print("Error: Could not read frame from camera")
                    break
                
                # Detect objects
                detections = self.detect_objects(frame)
                
                # Draw detections on frame
                frame_with_detections = self.draw_detections(frame, detections)
                
                # Display frame
                cv2.imshow('AI Home Assistant - Object Detection', frame_with_detections)
                
                # Save detections to memory more frequently
                if frame_count % save_interval == 0 and detections:
                    self._save_detections_to_memory(detections, frame.shape[:2])
                    print(f"📝 Saved {len(detections)} detections to memory")
                
                frame_count += 1
                
                # Check for exit key
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
        finally:
            cap.release()
            cv2.destroyAllWindows()
    
    def _save_detections_to_memory(self, detections: List[Dict], frame_size: Tuple[int, int]):
        """Save detections to visual memory"""
        for detection in detections:
            bbox = detection['bbox']
            location_description = self.visual_memory.get_location_for_bbox(bbox, frame_size, "zones.json")
            
            self.visual_memory.add_detection(
                object_name=detection['class_name'],
                confidence=detection['confidence'],
                bbox=bbox,
                frame_size=frame_size,
                location_description=location_description
            )
    
    def get_detection_summary(self) -> Dict[str, Any]:
        """Get summary of recent detections"""
        recent_detections = self.visual_memory.get_recent_detections(hours=1)
        all_objects = self.visual_memory.get_all_objects()
        
        summary = {
            'total_objects_detected': len(all_objects),
            'recent_detections_count': len(recent_detections),
            'objects_list': all_objects,
            'recent_objects': list(set([d['object_name'] for d in recent_detections]))
        }
        
        return summary
