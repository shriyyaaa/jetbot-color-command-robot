# jetbot-color-command-robot
Real-time computer vision system for controlling a JetBot using colored visual commands, OpenCV, and a Jetson Nano CSI camera.

# JetBot Color Command Robot

A real-time computer vision project that controls a JetBot using colored visual commands. The system uses a Jetson Nano CSI camera and OpenCV to detect colored objects and translate them into robot movement commands.

## Color Commands

The robot responds to four detected colors:

| Color | Robot Action |
|---|---|
| Red | Stop |
| Blue | Turn Anticlockwise |
| Green | Turn Clockwise |
| Yellow | Move Forward |

The system remembers the last detected command, so the robot continues executing the previous command even when the colored object temporarily leaves the camera frame.

## Features

* Real-time color detection using OpenCV
* HSV-based color segmentation
* Contour detection to identify the largest colored region
* Four visual commands for robot control
* Last-command memory for continuous operation
* Jetson Nano CSI camera support
* JetBot motor control
* Live MJPEG video streaming over HTTP
* Multithreaded camera streaming and robot control

## System Architecture

```text
Jetson Nano CSI Camera
          ↓
      OpenCV Frame
          ↓
     HSV Conversion
          ↓
     Gaussian Blur
          ↓
    Color Segmentation
          ↓
   Contour Detection
          ↓
     Command Mapping
          ↓
      JetBot Robot
```

At the same time, the processed camera frames are served through an MJPEG HTTP stream.

## Color Detection

The camera frame is converted from BGR to HSV because HSV makes it easier to define ranges for different colors.

The system detects:

* Red
* Blue
* Green
* Yellow

A contour must exceed a minimum area threshold before it is considered a valid command. This helps reduce false detections caused by small regions or image noise.

## Command Memory

The robot stores the most recently detected color in:

```python
last_command_color
```

If the camera temporarily fails to detect a color, the robot continues using the previous command rather than immediately stopping.

For example:

```text
Yellow detected → Robot moves forward
Yellow disappears → Robot continues forward
Red detected → Robot stops
```

## Technologies Used

* Python
* OpenCV
* NumPy
* JetBot
* NVIDIA Jetson Nano
* CSI Camera
* Multithreading
* HTTP/MJPEG Streaming

## Hardware

* NVIDIA Jetson Nano
* JetBot robot platform
* Jetson Nano CSI camera
* Robot motors

## Running the Project

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/jetbot-color-command-robot.git
cd jetbot-color-command-robot
```

Run the program on the JetBot:

```bash
python3 src/color_command_robot.py
```

The MJPEG camera stream is available at:

```text
http://<JETBOT_IP>:8080/
```

Replace `<JETBOT_IP>` with the IP address of the JetBot.

## Important Notes

This project is designed for a JetBot running on an NVIDIA Jetson Nano. The GStreamer pipeline in the source code is specifically configured for the Jetson Nano CSI camera.

The HSV thresholds may need to be adjusted depending on:

* Lighting conditions
* Camera exposure
* Camera white balance
* Color of the command objects
* Distance from the camera

## Future Improvements

* Add object tracking instead of only color detection
* Add confidence scoring for commands
* Add temporal filtering to reduce false detections
* Add obstacle detection
* Add emergency timeout/safety stop
* Add a web interface for robot control
* Replace rule-based color detection with a trained object-detection model
* Add automated testing for the vision-processing pipeline

## Author

**Shriya Tiwari**

Computer Science Engineering
Thapar Institute of Engineering and Technology
