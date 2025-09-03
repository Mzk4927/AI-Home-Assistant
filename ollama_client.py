import requests
import json
from typing import Dict, List, Any, Optional

class OllamaClient:
    """Client for interacting with Ollama 3.2 for natural language processing"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model_name = "llama3.2"  # Using Llama 3.2 as specified
        
    def is_available(self) -> bool:
        """Check if Ollama service is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def generate_response(self, prompt: str, context: str = "") -> str:
        """Generate response using Ollama"""
        if not self.is_available():
            return "Ollama service is not available. Please make sure Ollama is running."
        
        full_prompt = f"{context}\n\nUser: {prompt}\nAssistant:"
        
        # retry on timeout a couple of times with simple backoff
        timeouts = [120, 120]
        for attempt, timeout_s in enumerate(timeouts, start=1):
            try:
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model_name,
                        "prompt": full_prompt,
                        "stream": False
                    },
                    timeout=timeout_s
                )
                if response.status_code == 200:
                    result = response.json()
                    return result.get('response', 'No response generated')
                else:
                    return f"Error: {response.status_code} - {response.text}"
            except requests.exceptions.Timeout:
                if attempt == len(timeouts):
                    return "Request timed out. Please try again."
            except Exception as e:
                return f"Error communicating with Ollama: {str(e)}"
    
    def answer_object_question(self, question: str, detection_data: List[Dict]) -> str:
        """Answer questions about object detections using context from visual memory"""
        
        # Create context from detection data
        context = self._create_context_from_detections(detection_data)
        
        # Create system prompt for object location questions
        system_prompt = """You are an AI home assistant that helps users find objects in their home. 
        You have access to visual memory data about objects that have been detected by cameras.
        
        When answering questions about object locations:
        1. Be specific about when and where objects were seen
        2. Mention confidence levels if relevant
        3. Provide helpful suggestions if objects haven't been seen recently
        4. Be conversational and helpful
        5. If you don't have information about an object, say so clearly
        
        Context about recent object detections:
        """
        
        full_context = f"{system_prompt}\n{context}"
        
        return self.generate_response(question, full_context)
    
    def _create_context_from_detections(self, detections: List[Dict]) -> str:
        """Create context string from detection data"""
        if not detections:
            return "No recent object detections available."
        
        context_parts = []
        
        # Group detections by object name
        object_groups = {}
        for detection in detections:
            obj_name = detection['object_name']
            if obj_name not in object_groups:
                object_groups[obj_name] = []
            object_groups[obj_name].append(detection)
        
        # Create context for each object
        for obj_name, obj_detections in object_groups.items():
            latest = obj_detections[0]  # Most recent detection
            
            context_parts.append(
                f"Object: {obj_name}\n"
                f"Last seen: {latest['timestamp']}\n"
                f"Location: {latest.get('location_description', 'Unknown location')}\n"
                f"Confidence: {latest['confidence']:.2f}\n"
                f"Total detections: {len(obj_detections)}\n"
            )
        
        return "\n".join(context_parts)
    
    def get_object_search_suggestions(self, partial_name: str, available_objects: List[str]) -> List[str]:
        """Get suggestions for object names based on partial input"""
        if not partial_name:
            return available_objects[:5]  # Return first 5 objects
        
        # Simple fuzzy matching
        suggestions = []
        partial_lower = partial_name.lower()
        
        for obj in available_objects:
            if partial_lower in obj.lower():
                suggestions.append(obj)
        
        return suggestions[:5]
    
    def generate_location_description(self, bbox: tuple, frame_size: tuple) -> str:
        """Generate natural language description of object location"""
        x, y, w, h = bbox
        frame_width, frame_height = frame_size
        
        # Calculate relative position
        center_x = x + w/2
        center_y = y + h/2
        
        rel_x = center_x / frame_width
        rel_y = center_y / frame_height
        
        # Generate natural language description
        if rel_x < 0.25:
            x_desc = "far left"
        elif rel_x < 0.4:
            x_desc = "left side"
        elif rel_x < 0.6:
            x_desc = "center"
        elif rel_x < 0.75:
            x_desc = "right side"
        else:
            x_desc = "far right"
        
        if rel_y < 0.25:
            y_desc = "top"
        elif rel_y < 0.4:
            y_desc = "upper"
        elif rel_y < 0.6:
            y_desc = "middle"
        elif rel_y < 0.75:
            y_desc = "lower"
        else:
            y_desc = "bottom"
        
        return f"{y_desc} {x_desc} of the frame"
