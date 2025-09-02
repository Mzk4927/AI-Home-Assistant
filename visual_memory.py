import sqlite3
import json
import datetime
from typing import List, Dict, Any
import os

class VisualMemory:
    """Manages visual memory for object detection and location tracking"""
    
    def __init__(self, db_path: str = "visual_memory.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for storing object detection history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create table for object detections
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS object_detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                object_name TEXT NOT NULL,
                confidence REAL NOT NULL,
                bbox_x REAL NOT NULL,
                bbox_y REAL NOT NULL,
                bbox_width REAL NOT NULL,
                bbox_height REAL NOT NULL,
                frame_width INTEGER NOT NULL,
                frame_height INTEGER NOT NULL,
                location_description TEXT,
                image_path TEXT
            )
        ''')
        
        # Create table for location descriptions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                x_min REAL,
                y_min REAL,
                x_max REAL,
                y_max REAL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_detection(self, object_name: str, confidence: float, bbox: tuple, 
                     frame_size: tuple, location_description: str = None, 
                     image_path: str = None):
        """Add a new object detection to memory"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.datetime.now().isoformat()
        x, y, w, h = bbox
        frame_width, frame_height = frame_size
        
        cursor.execute('''
            INSERT INTO object_detections 
            (timestamp, object_name, confidence, bbox_x, bbox_y, bbox_width, bbox_height,
             frame_width, frame_height, location_description, image_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (timestamp, object_name, confidence, x, y, w, h, 
              frame_width, frame_height, location_description, image_path))
        
        conn.commit()
        conn.close()
    
    def get_object_history(self, object_name: str, limit: int = 10) -> List[Dict]:
        """Get detection history for a specific object"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM object_detections 
            WHERE object_name = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (object_name, limit))
        
        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results
    
    def get_recent_detections(self, hours: int = 24, limit: int = 50) -> List[Dict]:
        """Get recent detections within specified hours"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_time = (datetime.datetime.now() - datetime.timedelta(hours=hours)).isoformat()
        
        cursor.execute('''
            SELECT * FROM object_detections 
            WHERE timestamp > ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (cutoff_time, limit))
        
        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results
    
    def search_objects_by_location(self, location_keyword: str) -> List[Dict]:
        """Search for objects detected in specific locations"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM object_detections 
            WHERE location_description LIKE ? 
            ORDER BY timestamp DESC
        ''', (f'%{location_keyword}%',))
        
        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results
    
    def get_all_objects(self) -> List[str]:
        """Get list of all unique objects detected"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT DISTINCT object_name FROM object_detections')
        results = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return results
    
    def add_location(self, name: str, description: str, bbox: tuple = None):
        """Add or update a location definition"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if bbox:
            x_min, y_min, x_max, y_max = bbox
            cursor.execute('''
                INSERT OR REPLACE INTO locations 
                (name, description, x_min, y_min, x_max, y_max)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, description, x_min, y_min, x_max, y_max))
        else:
            cursor.execute('''
                INSERT OR REPLACE INTO locations 
                (name, description)
                VALUES (?, ?)
            ''', (name, description))
        
        conn.commit()
        conn.close()
    
    def load_custom_zones(self, zones_file: str = "zones.json") -> List[Dict]:
        """Load custom zones from JSON file"""
        if os.path.exists(zones_file):
            try:
                with open(zones_file, 'r') as f:
                    zones = json.load(f)
                return zones
            except Exception as e:
                print(f"Warning: Could not load zones from {zones_file}: {e}")
        return []
    
    def get_location_for_bbox(self, bbox: tuple, frame_size: tuple, zones_file: str = "zones.json") -> str:
        """Determine location description based on bounding box position and custom zones"""
        x, y, w, h = bbox
        frame_width, frame_height = frame_size
        
        # Calculate object center
        center_x = x + w/2
        center_y = y + h/2
        
        # First, check if object is in any custom zone
        custom_zones = self.load_custom_zones(zones_file)
        
        for zone in custom_zones:
            zone_x, zone_y, zone_w, zone_h = zone["bbox"]
            zone_name = zone["name"]
            
            # Check if object center is within zone
            if (zone_x <= center_x <= zone_x + zone_w and 
                zone_y <= center_y <= zone_y + zone_h):
                return zone_name
        
        # If not in any custom zone, use generic location mapping
        rel_x = center_x / frame_width
        rel_y = center_y / frame_height
        
        # Simple location mapping based on relative position
        if rel_x < 0.33:
            x_region = "left"
        elif rel_x < 0.67:
            x_region = "center"
        else:
            x_region = "right"
        
        if rel_y < 0.33:
            y_region = "top"
        elif rel_y < 0.67:
            y_region = "middle"
        else:
            y_region = "bottom"
        
        return f"{y_region}-{x_region} area"
