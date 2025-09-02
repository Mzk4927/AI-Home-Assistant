# AI Home Assistant — Zone-Focused Detection

A lightweight project for drawing custom zones on camera feeds and performing zone-based object detection and assistant actions.

## Overview
- Interactive tool to draw, name, save, and load rectangular zones on a camera feed.
- Zone-focused detectors that filter detections by user-defined zones.
- Example modules included: object detector, zone-focused detector, real-time assistant.

## Prerequisites
- Windows, Python 3.8+
- Git, VS Code (recommended)
- A virtual environment is recommended

## Installation
Open PowerShell in the project folder (D:\new_AI home assis):

```powershell
# create and activate virtual environment (if not already active)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# upgrade pip and install dependencies
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Run the Zone Definition Tool
This tool lets you draw rectangles on the camera feed and save them to `zones.json`.

```powershell
python .\zone_definition_tool.py
```

## Controls
- Click and drag to draw a rectangle
- After releasing the mouse you'll be prompted to enter a zone name
- S: Save zones and exit
- Q: Quit without saving
- L: Load existing zones
- C: Clear all zones

## Files of interest
- zone_definition_tool.py — interactive zone drawing, save/load
- object_detector.py — detection logic (model integration)
- zone_focused_detector.py — applies detections to defined zones
- zone_focused_assistant.py / real_time_assistant.py — assistant behaviors and integrations
- requirements.txt — Python dependencies
- zones.json — saved zones (created when you save)

## Saving & Loading
- Zones are saved to `zones.json` in the project root by default.
- Use the tool's "L" command or call `load_zones()` to load previously saved zones.

## Development Notes
- Use normal Git workflows to integrate remote changes (pull/rebase/merge).
- If you rebase local commits, push with `--force-with-lease` to update remote safely.

## License
Add a LICENSE file (e.g., MIT) if you plan to publish.