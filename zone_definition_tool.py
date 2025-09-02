import cv2
import json
import os
from typing import List, Dict, Tuple

class ZoneDefinitionTool:
    """Tool for defining custom zones in camera feed by mouse interaction"""
    
    def __init__(self):
        self.zones = []  # List of zones: [{"name": str, "bbox": (x, y, w, h)}]
        self.current_zone = None  # Current zone being drawn
        self.drawing = False
        self.start_point = None
        self.end_point = None
        self.frame = None
        self.window_name = "Zone Definition Tool - Draw zones and press S to save, Q to quit"
        
    def mouse_callback(self, event, x, y, flags, param):
        """Handle mouse events for drawing zones"""
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.start_point = (x, y)
            self.current_zone = {"start": (x, y), "end": (x, y)}
            
        elif event == cv2.EVENT_MOUSEMOVE:
            if self.drawing:
                self.current_zone["end"] = (x, y)
                
        elif event == cv2.EVENT_LBUTTONUP:
            if self.drawing:
                self.drawing = False
                self.end_point = (x, y)
                
                # Calculate rectangle coordinates
                x1, y1 = self.start_point
                x2, y2 = self.end_point
                
                # Ensure proper rectangle (top-left to bottom-right)
                x_min, x_max = min(x1, x2), max(x1, x2)
                y_min, y_max = min(y1, y2), max(y1, y2)
                
                # Only add zone if it has some area
                if x_max - x_min > 10 and y_max - y_min > 10:
                    # Ask for zone name
                    zone_name = input("Enter zone name (e.g., 'bed', 'table', 'cupboard'): ").strip()
                    
                    if zone_name:
                        zone = {
                            "name": zone_name,
                            "bbox": (x_min, y_min, x_max - x_min, y_max - y_min)
                        }
                        self.zones.append(zone)
                        print(f"✅ Zone '{zone_name}' added: {zone['bbox']}")
                    else:
                        print("❌ Zone name cannot be empty, zone not added")
                
                self.current_zone = None
                self.start_point = None
                self.end_point = None
    
    def draw_zones(self, frame):
        """Draw all defined zones on the frame"""
        frame_copy = frame.copy()
        
        # Draw completed zones
        for i, zone in enumerate(self.zones):
            x, y, w, h = zone["bbox"]
            name = zone["name"]
            
            # Draw rectangle
            cv2.rectangle(frame_copy, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Draw label background
            label_size = cv2.getTextSize(name, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            cv2.rectangle(frame_copy, (x, y - label_size[1] - 10), 
                         (x + label_size[0], y), (0, 255, 0), -1)
            
            # Draw label text
            cv2.putText(frame_copy, name, (x, y - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        
        # Draw current zone being drawn
        if self.current_zone and self.drawing:
            x1, y1 = self.current_zone["start"]
            x2, y2 = self.current_zone["end"]
            cv2.rectangle(frame_copy, (x1, y1), (x2, y2), (0, 0, 255), 2)
        
        return frame_copy
    
    def save_zones(self, filename: str = "zones.json"):
        """Save zones to JSON file"""
        try:
            with open(filename, 'w') as f:
                json.dump(self.zones, f, indent=2)
            print(f"✅ Zones saved to {filename}")
            return True
        except Exception as e:
            print(f"❌ Error saving zones: {e}")
            return False
    
    def load_zones(self, filename: str = "zones.json"):
        """Load zones from JSON file"""
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    self.zones = json.load(f)
                print(f"✅ Loaded {len(self.zones)} zones from {filename}")
                return True
            except Exception as e:
                print(f"❌ Error loading zones: {e}")
                return False
        return False
    
    def run(self, camera_index: int = 0):
        """Main function to run the zone definition tool"""
        print("🎯 Zone Definition Tool")
        print("=" * 50)
        print("Instructions:")
        print("• Click and drag to draw a rectangle")
        print("• Enter zone name when prompted")
        print("• Press 'S' to save zones and exit")
        print("• Press 'Q' to quit without saving")
        print("• Press 'L' to load existing zones")
        print("• Press 'C' to clear all zones")
        print("=" * 50)
        
        # Try to load existing zones
        if self.load_zones():
            print(f"📋 Current zones: {[zone['name'] for zone in self.zones]}")
        
        # Initialize camera
        cap = cv2.VideoCapture(camera_index)
        
        if not cap.isOpened():
            print(f"❌ Error: Could not open camera {camera_index}")
            return False
        
        # Set window properties
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(self.window_name, self.mouse_callback)
        
        print("📹 Camera started. Start drawing zones!")
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("❌ Error: Could not read frame from camera")
                    break
                
                # Draw zones on frame
                frame_with_zones = self.draw_zones(frame)
                
                # Add instructions on frame
                cv2.putText(frame_with_zones, "Draw zones with mouse, S=Save, Q=Quit, L=Load, C=Clear", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                cv2.putText(frame_with_zones, f"Zones defined: {len(self.zones)}", 
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                # Display frame
                cv2.imshow(self.window_name, frame_with_zones)
                
                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q') or key == ord('Q'):
                    print("❌ Exiting without saving...")
                    break
                    
                elif key == ord('s') or key == ord('S'):
                    if self.zones:
                        if self.save_zones():
                            print("✅ Zones saved successfully!")
                            break
                    else:
                        print("⚠️  No zones to save!")
                        
                elif key == ord('l') or key == ord('L'):
                    self.load_zones()
                    print(f"📋 Current zones: {[zone['name'] for zone in self.zones]}")
                    
                elif key == ord('c') or key == ord('C'):
                    self.zones = []
                    print("🗑️  All zones cleared!")
        
        finally:
            cap.release()
            cv2.destroyAllWindows()
        
        return len(self.zones) > 0

def main():
    """Main function to run the zone definition tool"""
    tool = ZoneDefinitionTool()
    success = tool.run()
    
    if success:
        print("\n🎉 Zone definition completed!")
        print(f"📋 Defined zones: {[zone['name'] for zone in tool.zones]}")
    else:
        print("\n👋 Zone definition cancelled or failed")

if __name__ == "__main__":
    main()
