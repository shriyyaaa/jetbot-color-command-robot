import cv2
import numpy as np
from jetbot import Robot
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# Initialize Jetbot
robot = Robot()

# GStreamer pipeline for Jetson Nano CSI camera
pipeline = (
    "nvarguscamerasrc ! "
    "video/x-raw(memory:NVMM), width=320, height=240, framerate=30/1 ! "
    "nvvidconv ! video/x-raw, format=BGRx ! videoconvert ! appsink drop=true sync=false"
)
cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)

# Global variables for MJPEG server and threading
current_frame = None
lock = threading.Lock()

class MJPEGHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=--jpgboundary')
            self.end_headers()
            while True:
                with lock:
                    if current_frame is None:
                        time.sleep(0.01)
                        continue
                    ret, jpeg = cv2.imencode('.jpg', current_frame)
                    if not ret:
                        continue
                    frame_bytes = jpeg.tobytes()
                
                try:
                    self.wfile.write(b"--jpgboundary\r\n")
                    self.send_header('Content-type', 'image/jpeg')
                    self.send_header('Content-length', str(len(frame_bytes)))
                    self.end_headers()
                    self.wfile.write(frame_bytes)
                    self.wfile.write(b'\r\n')
                except Exception:
                    break
                time.sleep(0.05)

def start_mjpeg_server():
    server = HTTPServer(('0.0.0.0', 8080), MJPEGHandler)
    server.serve_forever()

def detect_command_color(hsv_frame):
    # --- Define HSV Color Ranges ---
    mask_red1 = cv2.inRange(hsv_frame, np.array([0, 120, 100]), np.array([10, 255, 255]))
    mask_red2 = cv2.inRange(hsv_frame, np.array([170, 120, 100]), np.array([180, 255, 255]))
    mask_red = cv2.add(mask_red1, mask_red2)
    
    mask_blue = cv2.inRange(hsv_frame, np.array([100, 150, 100]), np.array([140, 255, 255]))
    mask_green = cv2.inRange(hsv_frame, np.array([40, 100, 100]), np.array([80, 255, 255]))
    mask_yellow = cv2.inRange(hsv_frame, np.array([20, 100, 100]), np.array([35, 255, 255]))

    colors = {
        "RED": mask_red,
        "BLUE": mask_blue,
        "GREEN": mask_green,
        "YELLOW": mask_yellow
    }

    largest_area = 0
    detected_color = None
    best_contour = None

    # Check which color has the biggest presence on screen
    for color_name, mask in colors.items():
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest_c = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_c)
            if area > 800 and area > largest_area:
                largest_area = area
                detected_color = color_name
                best_contour = largest_c

    return detected_color, best_contour

def main():
    global current_frame
    
    # Start MJPEG HTTP server in a background thread
    server_thread = threading.Thread(target=start_mjpeg_server, daemon=True)
    server_thread.start()
    print("MJPEG Server started. View stream at http://<jetbot_ip>:8080/")

    # Control Settings
    speed = 0.25 
    
    # --- NEW: State Memory Variable ---
    last_command_color = None

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Convert frame to HSV and blur
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            blurred_hsv = cv2.GaussianBlur(hsv, (11, 11), 0)
            
            # Scan for the dominant command color
            command_color, contour = detect_command_color(blurred_hsv)
            
            # If a color is currently visible, update the memory and draw the box
            if command_color is not None:
                last_command_color = command_color
                
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 255, 255), 2)
                status_text = "ACTIVE"
            else:
                status_text = "RETAINED"

            # --- EXECUTE MOTORS BASED ON MEMORY (last_command_color) ---
            if last_command_color == "RED":
                robot.stop()
                cv2.putText(frame, f"CMD: STOP (RED) [{status_text}]", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            elif last_command_color == "BLUE":
                robot.left(speed)
                cv2.putText(frame, f"CMD: ANTICLOCK (BLUE) [{status_text}]", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            
            elif last_command_color == "GREEN":
                robot.right(speed)
                cv2.putText(frame, f"CMD: CLOCKWISE (GREEN) [{status_text}]", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            elif last_command_color == "YELLOW":
                robot.forward(speed)
                cv2.putText(frame, f"CMD: FORWARD (YELLOW) [{status_text}]", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                
            else:
                # This only runs right after boot up, before any color has been shown
                robot.stop()
                cv2.putText(frame, "WAITING FOR INITIAL COLOR...", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (165, 165, 165), 2)
            
            # Update the global frame for the MJPEG stream
            with lock:
                current_frame = frame.copy()
                
    except KeyboardInterrupt:
        print("Interrupted by user, shutting down...")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        robot.stop()
        cap.release()
        print("Camera and motors released.")

if __name__ == '__main__':
    main()
