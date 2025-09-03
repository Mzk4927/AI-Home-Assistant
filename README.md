<<<<<<< HEAD
# AI-Home-Assistant
Intelligent home assistant with YOLO11n object detection, custom zones, and natural language Q&amp;A
=======
# 🤖 AI Home Assistant with Custom Zones

An intelligent home assistant that uses YOLO11n.pt for object detection, creates visual memory of object locations using custom zones, and uses Ollama 3.2 for natural language processing.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.8+-green.svg)](https://opencv.org)
[![YOLO](https://img.shields.io/badge/YOLO-11n-orange.svg)](https://ultralytics.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ Features

- **Real-time Object Detection**: Uses YOLO11n.pt to detect objects in camera feed
- **Custom Zone Definition**: Draw custom zones (bed, table, cupboard, etc.) by clicking and dragging
- **Visual Memory**: Remembers where and when objects were seen
- **Natural Language Q&A**: Ask questions like "Where did you see my phone?" using Ollama 3.2
- **Persistent Storage**: SQLite database stores all detection history
- **Interactive Interface**: Command-line interface for asking questions

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install Ollama and Llama 3.2
```bash
# Install Ollama from https://ollama.ai/
ollama pull llama3.2
ollama serve
```

### 3. Define Custom Zones (Optional but Recommended)
```bash
python zone_definition_tool.py
```
- Click and drag to draw rectangles
- Enter zone names (e.g., "bed", "table", "cupboard")
- Press 'S' to save zones to `zones.json`
- Press 'Q' to quit

### 4. Start the Home Assistant
```bash
python enhanced_home_assistant.py
```

## 🎯 Zone Definition Tool

The zone definition tool lets you create custom areas in your camera view:

### Controls:
- **Mouse**: Click and drag to draw rectangles
- **S Key**: Save zones and exit
- **Q Key**: Quit without saving
- **L Key**: Load existing zones
- **C Key**: Clear all zones

### Example Usage:
1. Run `python zone_definition_tool.py`
2. Draw a rectangle around your bed area
3. Enter "bed" when prompted
4. Draw a rectangle around your table
5. Enter "table" when prompted
6. Press 'S' to save

## 💬 Using the Assistant

Once running, you can ask questions like:
- "Where did you see my phone?"
- "Have you seen any books recently?"
- "What objects are in the bed area?"
- "Show me recent detections"

### Commands:
- `status` - Check system status
- `list` - List recent detections
- `zones` - Redefine custom zones
- `quit` - Exit the assistant

## 📁 File Structure

```
AI-Home-Assistant/
├── yolo11n.pt                    # YOLO model file
├── zone_focused_assistant.py     # Main application (RUN THIS)
├── zone_definition_tool.py       # Zone definition tool
├── zone_focused_detector.py      # Zone-focused detection logic
├── visual_memory.py              # Memory management with zones
├── ollama_client.py              # Ollama integration
├── requirements.txt              # Python dependencies
├── README.md                     # This file
├── zones.json                    # Custom zones (created by tool)
└── visual_memory.db              # Detection database (auto-created)
```

## 🔧 Customization

### Adjust Detection Sensitivity
Edit `zone_focused_detector.py`:
```python
self.confidence_threshold = 0.1  # Lower = more detections
```

### Change Camera
Edit the camera index in the main file:
```python
assistant.start(camera_index=1)  # Use second camera
```

### Modify Zone Detection
Edit `visual_memory.py` in the `get_location_for_bbox()` method to customize how zones are detected.

## 🧪 Testing

Run the main application to test everything:
```bash
python zone_focused_assistant.py
```

This will test:
- Zone-focused object detection
- Real-time Q&A system
- Custom zone integration

## 🐛 Troubleshooting

### Camera Issues
- **No camera feed**: Check if camera is being used by another application
- **Permission denied**: Grant camera permissions to Python/terminal
- **Wrong camera**: Change camera_index in the code (default: 0)

### Ollama Issues
- **Service not available**: Run `ollama serve` in a separate terminal
- **Model not found**: Run `ollama pull llama3.2`
- **Connection timeout**: Check if Ollama is running on port 11434

### Zone Issues
- **Zones not working**: Make sure `zones.json` exists and has valid format
- **Wrong zone detection**: Redraw zones with `python zone_definition_tool.py`

## 📊 Example zones.json Format

```json
[
  {
    "name": "bed",
    "bbox": [100, 100, 200, 150]
  },
  {
    "name": "table", 
    "bbox": [300, 200, 150, 100]
  },
  {
    "name": "cupboard",
    "bbox": [50, 300, 100, 200]
  }
]
```

Where `bbox` is `[x, y, width, height]` in pixels.

## 🎉 Example Usage Flow

1. **Setup**: Install dependencies and Ollama
2. **Define Zones**: Run zone tool to draw bed, table, cupboard areas
3. **Start Assistant**: Run enhanced home assistant
4. **Ask Questions**: "Where did you see my laptop?" → "I last saw your laptop in the bed area at 2:30 PM"

## 🔮 Future Enhancements

- Voice commands using speech recognition
- Web interface for mobile access
- Multiple camera support
- Object tracking across frames
- Time-based location history
- Integration with smart home devices

## 📝 Notes

- The system works without custom zones (uses generic areas like "top-left", "center-right")
- Ollama is optional but recommended for better natural language responses
- All detection data is stored in SQLite database for persistence
- Zones are saved in JSON format for easy editing

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section
2. Verify all prerequisites are installed
3. Check console output for error messages
4. Ensure camera and Ollama services are running
5. Test with the provided test script
>>>>>>> 47f9110 (Initial commit: AI Home Assistant with zone-focused detection)

## License
Add a LICENSE file (e.g., MIT) if you plan to publish.
