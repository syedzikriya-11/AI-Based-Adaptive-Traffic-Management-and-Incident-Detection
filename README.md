# AI-Based Adaptive Traffic Management System and Incident Detection

## 📌 Project Overview

The **AI-Based Adaptive Traffic Management System and Incident Detection** is designed to improve traffic flow and road safety using computer vision and intelligent traffic monitoring.

The system uses a camera to capture real-time traffic footage and applies AI-based object detection to identify vehicles and potential traffic incidents. Based on the detected traffic conditions, the system aims to support adaptive traffic signal management and incident alerts.

## 🎯 Objectives

- Monitor road traffic using a camera.
- Detect and identify vehicles using YOLO-based object detection.
- Analyze traffic conditions to support adaptive traffic signal control.
- Detect potential road incidents and generate alerts.
- Integrate software-based computer vision with Arduino-based hardware control.

## 🛠️ Technologies Used

- **Programming Languages:** Python, Arduino C/C++
- **AI and Computer Vision:** YOLOv8, OpenCV
- **Hardware:** Arduino board, USB camera
- **Development Tools:** Python IDE, Arduino IDE, Git, GitHub

## ⚙️ System Workflow

1. The USB camera captures live traffic footage.
2. Python and OpenCV read the camera frames.
3. The YOLO model processes the frames to detect vehicles and relevant objects.
4. The system analyzes the detections to estimate traffic conditions and identify potential incidents.
5. Traffic-control decisions are communicated to the Arduino hardware, where implemented.
6. Incident notifications are generated through the configured alert mechanism.

## 📷 USB Camera Configuration

The project supports USB cameras connected to a laptop or computer. The camera index must be configured according to the device on which the program runs.

```python
import cv2

CAMERA_INDEX = 0  # Change this according to your system
cap = cv2.VideoCapture(CAMERA_INDEX)

if not cap.isOpened():
    print("Error: Unable to access the camera.")
    exit()

while True:
    ret, frame = cap.read()

    if not ret:
        print("Error: Unable to capture frame.")
        break

    cv2.imshow("Traffic Monitoring", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
```

### Camera Index Guide

| Camera index | Typical device |
|---|---|
| `0` | Default or first detected camera |
| `1` | Second detected camera |
| `2` | Third detected camera |

**Note:** These are typical examples, not guaranteed mappings. The correct index depends on the operating system, connected cameras, and OpenCV backend. If the camera fails to open, try another index or check which device is detected by your system.

If multiple USB cameras are connected, configure the appropriate camera index for each camera.

## 🚀 Getting Started

### Prerequisites

- Python 3.x
- OpenCV
- Ultralytics YOLO
- Arduino IDE (for hardware integration)
- A compatible camera connected to the computer

### Installation

1. Clone the repository:

   ```bash
   git clone <YOUR_GITHUB_REPOSITORY_URL>
   ```

2. Navigate to the project directory:

   ```bash
   cd <YOUR_PROJECT_DIRECTORY>
   ```

3. Install the required Python packages:

   ```bash
   pip install opencv-python ultralytics
   ```

4. Connect the USB camera and configure its index in the Python script.

5. Ensure the YOLO model weights and any required configuration files are available.

6. Connect and configure the Arduino hardware according to the project's circuit and communication setup.

### Run the Project

```bash
python main.py
```

Replace `main.py` with the actual Python entry-point filename if it differs.

## 🔔 Incident Detection and Alerts

The system is designed to detect relevant traffic incidents using visual information and generate notifications through the configured alert mechanism.

## 🔮 Future Improvements

- Support for more multiple camera feeds.
- More robust incident classification.
- Optimized real-time inference.
- Integration with intelligent transportation infrastructure.
- GPS-Based Ambulance Detection and Priority Control

## 👨‍💻 Project Information

Project Title: AI-Based Adaptive Traffic Management System and Incident Detection
Project Type: Final-Year Engineering Team Project
My Role: Team Lead, Original Idea Originator & Sole Technical Developer

## 💡 Idea and Technical Ownership

The original concept for this project was proposed by me. As the team leader, I independently handled the complete technical development, from initial system design and implementation to hardware integration, AI-based vehicle detection, adaptive traffic management, incident detection, testing, and documentation.

## 🏆 Achievements

First Prize – Robotics and Automation, National-Level Project Expo, organized by CMR Institute of Technology (CMRIT), Bengaluru.
Conceived the original project idea and independently developed the complete technical solution while leading the project team.
