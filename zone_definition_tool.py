import cv2
import json
import os
import time
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
        self.filename = "zones.json"
        
    def mouse_callback(self, event, x, y, flags, param):
        """Handle mouse events for drawing zones"""
        if event == cv2.EVENT_LBUTTONDOWN:
            self.start_point = (x, y)
            self.end_point = (x, y)
            self.drawing = True

        elif event == cv2.EVENT_MOUSEMOVE:
            if self.drawing:
                self.end_point = (x, y)

        elif event == cv2.EVENT_LBUTTONUP:
            if self.drawing and self.start_point:
                self.end_point = (x, y)
                x0, y0 = self.start_point
                x1, y1 = self.end_point
                x_min, y_min = min(x0, x1), min(y0, y1)
                w, h = abs(x1 - x0), abs(y1 - y0)
                zone_name = input("Enter zone name: ").strip() or f"zone_{len(self.zones)+1}"
                zone = {"name": zone_name, "bbox": [int(x_min), int(y_min), int(w), int(h)], "created_at": time.time()}
                self.zones.append(zone)
                self.drawing = False
                self.start_point = None
                self.end_point = None
                self.save_zones(self.filename)
                print(f"[zone saved] {zone_name} -> {self.filename}")

    def draw_zones(self, frame):
        """Draw all defined zones on the frame"""
        frame_copy = frame.copy()
        
        # Draw completed zones
        for i, zone in enumerate(self.zones):
            x, y, w, h = zone["bbox"]
            cv2.rectangle(frame_copy, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame_copy, zone.get("name", f"zone{i}"), (x, y - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
        
        # Draw current zone being drawn
        if self.start_point and self.end_point and self.drawing:
            x0, y0 = self.start_point
            x1, y1 = self.end_point
            cv2.rectangle(frame_copy, (x0, y0), (x1, y1), (0, 165, 255), 2)
        
        return frame_copy
    
    def save_zones(self, filename: str = None):
        """Save zones to JSON file (atomic)"""
        if filename is None:
            filename = self.filename
        tmp = filename + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.zones, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, filename)
            # write a small mtime hint file so detectors can notice
            try:
                with open(filename + ".updated", "w", encoding="utf-8") as h:
                    h.write(str(time.time()))
            except Exception:
                pass
            return True
        except Exception as e:
            print("Error saving zones:", e)
            if os.path.exists(tmp):
                os.remove(tmp)
            return False
    
    def load_zones(self, filename: str = None):
        """Load zones from JSON file"""
        if filename is None:
            filename = self.filename
        if not os.path.exists(filename):
            return False
        try:
            with open(filename, "r", encoding="utf-8") as f:
                self.zones = json.load(f)
            return True
        except Exception as e:
            print("Error loading zones:", e)
            return False
    
    def run(self, camera_index: int = 0):
        """Main function to run the zone definition tool"""
        print("🎯 Zone Definition Tool")
        cap = cv2.VideoCapture(camera_index)
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(self.window_name, self.mouse_callback)
        if os.path.exists(self.filename):
            self.load_zones(self.filename)
            print(f"[loaded zones] {len(self.zones)} zones")
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                display = self.draw_zones(frame)
                cv2.imshow(self.window_name, display)
                key = cv2.waitKey(20) & 0xFF
                if key == ord('s'):
                    self.save_zones(self.filename)
                    print("[saved zones] saved and exiting")
                    break
                elif key == ord('q'):
                    print("[quit] exiting without further action")
                    break
                elif key == ord('l'):
                    self.load_zones(self.filename)
                    print(f"[loaded zones] {len(self.zones)} zones")
                elif key == ord('c'):
                    self.zones = []
                    print("[cleared] all zones removed")
        finally:
            cap.release()
            cv2.destroyAllWindows()
        return True

def main():
    tool = ZoneDefinitionTool()
    tool.run()

if __name__ == "__main__":
    main()
