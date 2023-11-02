import cv2
import torch
# import openai
from djitellopy import Tello
#import azure.cognitiveservices.speech as speechsdk
from pynput import keyboard
import threading
# import multiprocessing
import time
import datetime
from drone_utils import DroneUtils
import configparser
import os
import speech_recognition as sr

import sys
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget

#########################
# SETUP
#########################

# Constants
config = configparser.ConfigParser()
config.read('config.ini')
TELLO_IP = config.get('tello', 'ip')

# Paths
exp = "exp2-best"
root_path = "/Users/richtsai1103/liquid_level_drone"
weights_path = os.path.join(root_path, f"yolov5/runs/train/{exp}/weights/best.pt")

drone_control_kb = {
    'move': "",
    'takeoff': False,
    'land': False,
}

#########################
# FUNCTIONS
#########################

def control_drone(mock):
    # control with kb
    while True:
        if mock:
            print(f"Mock executed command: {drone_control_kb['move']}")
            time.sleep(1)
        else:
            if drone_control_kb['takeoff']:
                tello.takeoff()
                drone_control_kb['takeoff'] = False
            elif drone_control_kb['land']:
                tello.land()
                drone_control_kb['land'] = False
            else:
                time.sleep(1)
                # NOTE: You need to define drone_ops.execute_drone_command or replace with appropriate function
                # drone_ops.execute_drone_command(drone_control_kb['move'])
                drone_control_kb['move'] = ""


def lawnmower_pattern(distance=100, height=30, wait_time=3, segments=4, direction="left"):
    segment_distance = distance // segments
    for _ in range(segments):
        if direction == "left":
            tello.move_left(segment_distance)
        else:  # direction == "right"
            tello.move_right(segment_distance)
        time.sleep(wait_time)

def zigzag_movement(patterns=3, distance=100, height=30, segments=4):
    directions = ["left", "right", "left"]  # Starting from bottom right, as specified
    for i in range(patterns):
        lawnmower_pattern(distance=distance, height=height, segments=segments, direction=directions[i])
        if i != patterns - 1:  # Don't move up after the last pattern
            tello.move_up(height)

    
class CameraViewer(QMainWindow):
    def __init__(self, save_video=False, file_format='mp4'):
        super().__init__()

        self.setWindowTitle("Camera Viewer")

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)
        
        self.save_video = save_video
        self.file_format = file_format
        
        # Initialize video recording attributes
        self.fps = 30.0  # Frames per second
        self.video_width = 640  # Width of the output video frame
        self.video_height = 640  # Height of the output video frame
        self.output_directory = os.path.join('video_result', exp)  # Modify 'exp' to your desired experiment name
        os.makedirs(self.output_directory, exist_ok=True)
        self.timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.output_file = f'video_{self.timestamp}' + f'.{self.file_format}'
        self.output_path = os.path.join(self.output_directory, self.output_file)

        if self.file_format == 'mp4':
            self.fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        elif self.file_format == 'avi':
            self.fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Codec for AVI format

        self.out = cv2.VideoWriter(self.output_path, self.fourcc, self.fps, (self.video_width, self.video_height))
        
        self.label = QLabel(self)
        self.layout.addWidget(self.label)

        self.frame_read = tello.get_frame_read()  # Open the default camera (usually index 0)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(1)  # Update every 30 milliseconds (adjust as needed)

    def update_frame(self):
        frame_original = self.frame_read.frame

        # Convert the OpenCV frame to a QImage
        height, width, channel = frame_original.shape
        crop_x1 = width // 4  # Adjust the cropping region as needed
        crop_x2 = 3 * width // 4
        crop_y1 = height // 4
        crop_y2 = 3 * height // 4
        cropped_image = frame_original[crop_y1:crop_y2, crop_x1:crop_x2]

        # Resize for faster processing 
        # todo: (keep the same 640 since we trained on 640 or train model in 320)
        frame_resized = cv2.resize(cropped_image, (320, 320))

        # YOLO processing on low-res frame
        results = model(frame_resized)
        rendered_frame_small = results.render()[0]

        # Resize the rendered frame to a larger resolution for display
        rendered_frame_large = cv2.resize(rendered_frame_small, (640, 640)) 
        
        # Save the frame to the video file (if video recording is enabled)
        if self.save_video:
            self.out.write(rendered_frame_large)
            
        # render to QImage (since cv2 will block keyboard control)
        rendered_height, rendered_width, _ = rendered_frame_large.shape 
        bytes_per_line = 3 * rendered_width
        q_image = QImage(rendered_frame_large, rendered_width, rendered_height, bytes_per_line, QImage.Format_RGB888)

        # Display the QImage in the QLabel
        self.label.setPixmap(QPixmap.fromImage(q_image))
        
    def closeEvent(self, event):
        # Release the video writer when the application is closed
        if self.save_video:
            self.out.release()
        super().closeEvent(event)


# Class for keyboard control listener
class KeyboardListener(QThread):
    key_pressed = pyqtSignal(object)

    def run(self):
        def on_key_press(key):
            self.key_pressed.emit(key)

        with keyboard.Listener(on_press=on_key_press) as listener:
            listener.join()

# Function to handle key presses and update drone control commands
def handle_key_press(key, drone_control_kb):
    try:
        if key.char == 'w':
            drone_control_kb['move'] = 'move_forward'
        elif key.char == 's':
            drone_control_kb['move'] = 'move_back'
        elif key.char == 'a':
            drone_control_kb['move'] = 'move_left'
        elif key.char == 'd':
            drone_control_kb['move'] = 'move_right'
        elif key.char == 'e':
            drone_control_kb['move'] = 'move_up'
        elif key.char == 'q':
            drone_control_kb['move'] = 'move_down'
        elif key.char == 'z':
            zigzag_movement(tello)
    except AttributeError:
        if key == keyboard.Key.space:
            drone_control_kb['takeoff'] = True
        elif key == keyboard.Key.esc:
            drone_control_kb['land'] = True

    print(drone_control_kb)  # Print the updated drone control commands


#########################
# MAIN LOOP - Execute the script!
#########################

if __name__ == "__main__":

    # Initialize Tello drone
    tello = Tello(TELLO_IP)
    tello.connect()
    tello.streamoff()
    tello.streamon()

    #drone_ops = DroneUtils(tello, TELLO_IP)

    # Set up the PyQt application and camera viewer
    app = QApplication(sys.argv)
    viewer = CameraViewer()

    # Initialize and start the keyboard listener thread
    listener = KeyboardListener()
    listener.key_pressed.connect(lambda key: handle_key_press(key, drone_control_kb))
    listener.start()

    # Start the PyQt application
    sys.exit(app.exec_())

    # When the application closes, safely land the drone and disconnect
    tello.land()
    tello.end()

