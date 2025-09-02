import cv2
import threading
import time
import os
from typing import Dict, List, Any
from object_detector import ObjectDetector
from visual_memory import VisualMemory
from ollama_client import OllamaClient
from zone_definition_tool import ZoneDefinitionTool

class EnhancedAIHomeAssistant:
    """Enhanced AI Home Assistant with custom zone support"""
    
    def __init__(self, model_path: str = "yolo11n.pt"):
        self.object_detector = ObjectDetector(model_path)
        self.visual_memory = VisualMemory()
        self.ollama_client = OllamaClient()
        self.zone_tool = ZoneDefinitionTool()
        self.is_running = False
        self.camera_thread = None
        self.zones_file = "zones.json"
        
    def start(self, camera_index: int = 0):
        """Start the home assistant system"""
        print("🤖 Starting Enhanced AI Home Assistant...")
        
        # Check if zones exist, if not, offer to create them
        if not os.path.exists(self.zones_file):
            print("📍 No custom zones found. Would you like to define zones first?")
            response = input("Type 'y' to define zones, or 'n' to continue with generic areas: ").strip().lower()
            
            if response == 'y':
                print("🎯 Starting zone definition tool...")
                if self.zone_tool.run(camera_index):
                    print("✅ Zones defined successfully!")
                else:
                    print("⚠️  Zone definition cancelled, using generic areas")
        
        # Check if Ollama is available
        if not self.ollama_client.is_available():
            print("⚠️  Warning: Ollama service not available. Natural language features will be limited.")
            print("   Please make sure Ollama is running with: ollama serve")
        else:
            print("✅ Ollama service is available")
        
        # Load and display zones
        zones = self.visual_memory.load_custom_zones(self.zones_file)
        if zones:
            print(f"📍 Loaded {len(zones)} custom zones: {[zone['name'] for zone in zones]}")
        else:
            print("📍 Using generic location areas (top-left, center-right, etc.)")
        
        # Start object detection
        self.is_running = True
        self.object_detector.start_continuous_detection(camera_index)
        
        print("✅ Enhanced AI Home Assistant is now running!")
        print("📹 Camera feed is active - objects are being detected and remembered")
        print("💬 You can now ask questions about object locations")
        print("❌ Press 'q' in the camera window to stop detection")
        
    def stop(self):
        """Stop the home assistant system"""
        print("🛑 Stopping Enhanced AI Home Assistant...")
        self.is_running = False
        self.object_detector.stop_detection()
        print("✅ Enhanced AI Home Assistant stopped")
    
    def ask_question(self, question: str) -> str:
        """Ask a question about object locations"""
        if not self.is_running:
            return "Home assistant is not running. Please start it first."
        
        # Get recent detections for context
        recent_detections = self.visual_memory.get_recent_detections(hours=24, limit=20)
        
        if not recent_detections:
            return "I haven't detected any objects recently. Make sure the camera is working and objects are visible."
        
        # Use Ollama to answer the question
        if self.ollama_client.is_available():
            return self.ollama_client.answer_object_question(question, recent_detections)
        else:
            # Fallback to simple text-based answers
            return self._simple_answer(question, recent_detections)
    
    def _simple_answer(self, question: str, detections: List[Dict]) -> str:
        """Simple fallback answer when Ollama is not available"""
        question_lower = question.lower()
        
        # Extract object name from question
        detected_objects = self.visual_memory.get_all_objects()
        mentioned_object = None
        
        for obj in detected_objects:
            if obj.lower() in question_lower:
                mentioned_object = obj
                break
        
        if mentioned_object:
            # Get history for the mentioned object
            history = self.visual_memory.get_object_history(mentioned_object, limit=5)
            
            if history:
                latest = history[0]
                return f"I last saw {mentioned_object} at {latest['timestamp']} in the {latest.get('location_description', 'unknown location')} with {latest['confidence']:.1%} confidence."
            else:
                return f"I don't have recent information about {mentioned_object}."
        else:
            # General information
            recent_objects = list(set([d['object_name'] for d in detections]))
            return f"I've recently detected these objects: {', '.join(recent_objects[:5])}. Ask me about any specific object!"
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the home assistant"""
        detection_summary = self.object_detector.get_detection_summary()
        zones = self.visual_memory.load_custom_zones(self.zones_file)
        
        status = {
            'is_running': self.is_running,
            'ollama_available': self.ollama_client.is_available(),
            'total_objects_detected': detection_summary['total_objects_detected'],
            'recent_detections': detection_summary['recent_detections_count'],
            'available_objects': detection_summary['objects_list'],
            'custom_zones': len(zones),
            'zone_names': [zone['name'] for zone in zones]
        }
        
        return status
    
    def list_recent_objects(self, hours: int = 24) -> List[Dict]:
        """Get list of recently detected objects"""
        return self.visual_memory.get_recent_detections(hours=hours, limit=50)
    
    def search_objects_by_location(self, location: str) -> List[Dict]:
        """Search for objects in a specific location"""
        return self.visual_memory.search_objects_by_location(location)
    
    def get_object_history(self, object_name: str) -> List[Dict]:
        """Get detection history for a specific object"""
        return self.visual_memory.get_object_history(object_name)
    
    def redefine_zones(self, camera_index: int = 0):
        """Redefine custom zones"""
        print("🎯 Starting zone redefinition...")
        if self.zone_tool.run(camera_index):
            print("✅ Zones redefined successfully!")
            zones = self.visual_memory.load_custom_zones(self.zones_file)
            print(f"📍 Current zones: {[zone['name'] for zone in zones]}")
        else:
            print("⚠️  Zone redefinition cancelled")

def main():
    """Main function to run the enhanced home assistant"""
    assistant = EnhancedAIHomeAssistant()
    
    try:
        # Start the assistant
        assistant.start()
        
        # Interactive command loop
        print("\n" + "="*60)
        print("💬 ENHANCED INTERACTIVE MODE")
        print("="*60)
        print("Ask me questions about objects I've detected!")
        print("Examples:")
        print("  - 'Where did you see my phone?'")
        print("  - 'Have you seen any books recently?'")
        print("  - 'What objects are in the bed area?'")
        print("  - 'status' - Check system status")
        print("  - 'list' - List recent detections")
        print("  - 'zones' - Redefine custom zones")
        print("  - 'quit' - Exit the assistant")
        print("="*60)
        
        while assistant.is_running:
            try:
                user_input = input("\n🤖 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'stop']:
                    break
                elif user_input.lower() == 'status':
                    status = assistant.get_status()
                    print(f"📊 Status: Running={status['is_running']}, "
                          f"Ollama={status['ollama_available']}, "
                          f"Objects={status['total_objects_detected']}, "
                          f"Zones={status['custom_zones']}")
                    if status['zone_names']:
                        print(f"📍 Zones: {', '.join(status['zone_names'])}")
                elif user_input.lower() == 'list':
                    recent = assistant.list_recent_objects()
                    if recent:
                        print("📋 Recent detections:")
                        for det in recent[:10]:
                            print(f"  - {det['object_name']} at {det['timestamp']} "
                                  f"({det.get('location_description', 'unknown location')})")
                    else:
                        print("No recent detections found.")
                elif user_input.lower() == 'zones':
                    assistant.redefine_zones()
                elif user_input:
                    answer = assistant.ask_question(user_input)
                    print(f"🤖 Assistant: {answer}")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    finally:
        assistant.stop()

if __name__ == "__main__":
    main()
