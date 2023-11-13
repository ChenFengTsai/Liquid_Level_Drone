# author: Chen Feng Tsai
import cv2
import torch
#import azure.cognitiveservices.speech as speechsdk
import multiprocessing
import time
import os
import configparser
import speech_recognition as sr

#########################
# SETUP
#########################

# Constants
config = configparser.ConfigParser()
config.read('config.ini')
# AZURE_SUBSCRIPTION_KEY = config.get('API key', 'AZURE_SUBSCRIPTION_KEY')
# AZURE_SERVICE_REGION = config.get('API key', 'AZURE_SERVICE_REGION')

# Paths (change these paths as per your system)
exp = "exp2-best"
root_path =  "/Users/richtsai1103/liquid_level_drone"
weights_path = os.path.join(root_path, f"yolov5/runs/train/{exp}/weights/best.pt")
model_path = os.path.join(root_path, "yolov5/")

# ACTIONS TO COMMANDS MAPPING
ACTIONS_TO_COMMANDS = {
    ("start", "fly", "take off", "lift off"): "takeoff",
    ("land", "stop", "settle", "touch down"): "land",
    ("front flip", "forward flip", "tumble forward"): "flip",
    ("forward", "move ahead", "go straight"): "move_forward",
    ("backward", "move back", "retreat"): "move_back",
    ("left", "move left", "go leftward"): "move_left",
    ("right", "move right", "go rightward"): "move_right",
    ("up", "ascend", "rise"): "move_up",
    ("down", "descend", "lower"): "move_down",
    ("spin right", "rotate clockwise", "turn right"): "rotate_clockwise",
    ("spin left", "rotate counter-clockwise", "turn left"): "rotate_counter_clockwise",
    ("back flip", "flip back"): "flip_backward",
    ("right flip"): "flip_right",
    ("video on", "start video", "begin stream"): "streamon",
    ("video off", "stop video", "end stream"): "streamoff",
    ("go xyz", "specific move"): "go_xyz_speed"
}

#########################
# FUNCTIONS
#########################

def interpret_command_to_drone_action(command):
    for action_phrases, action in ACTIONS_TO_COMMANDS.items():
        if command in action_phrases:
            return action
    return None

def mock_execute_drone_command(command):
    print(f"Mock executed command: {command}")

# def setup_speechrecog():
#     # Setup Azure Speech SDK
#     print("Setting up Azure Speech SDK...")
#     speech_config = speechsdk.SpeechConfig(subscription='55f2007ae13640a59b52e03dad3361ea', endpoint="https://northcentralus.api.cognitive.microsoft.com/sts/v1.0/issuetoken")
#     speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)
#     print("Azure Speech SDK setup complete.")
#     return speech_recognizer
    
def listen_to_commands():
    speech_recognizer = sr.Recognizer()
    # speech_recognizer = setup_speechrecog()
    print("Listening for commands. Speak into your microphone...")
    with sr.Microphone() as source:
        while True:
            print("Awaiting command...")
            audio = speech_recognizer.listen(source, timeout = 10, phrase_time_limit = 3)
            try:
                command_heard = speech_recognizer.recognize_google(audio).lower()
            
            # result = speech_recognizer.recognize_once()
            # if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            #     command_heard = result.text.lower().strip('.')
                print(f"Heard: {command_heard}")
            except sr.UnknownValueError:
                continue
            if command_heard:
                drone_command = interpret_command_to_drone_action(command_heard)
            else:
                print("Nothing is heard.")
            
            if drone_command:
                mock_execute_drone_command(drone_command)
            else:
                print(f"Not a valid action term: {command_heard}")
            time.sleep(5)
def start_video_feed(model):
    try:
        # Start the camera feed
        print("Attempting to start the camera feed...")
        
        # Try default camera first
        cap = cv2.VideoCapture(0)
        # print(cap)
        
        if not cap.isOpened():
            print("Default camera not accessible. Trying the next camera index...")
            cap = cv2.VideoCapture(0)
            
            if not cap.isOpened():
                print("Second camera not accessible. Exiting.")
                return
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame.")
                break
            
            # If YOLO processing is needed:
            # flip it
            frame = cv2.flip(frame, 1)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            #frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = model(frame)
            rendered_frame = results.render()[0]
            rendered_frame = cv2.cvtColor(rendered_frame, cv2.COLOR_BGR2RGB)
            cv2.imshow('YOLOv5', rendered_frame)
            
            if cv2.waitKey(1) == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()
        print("Camera feed ended.")

    except Exception as e:
        print(f"Error starting the video feed: {e}")

#########################
# MAIN - Execute the program
#########################

if __name__ == "__main__":
    # Check CUDA availability
    USE_CUDA = torch.cuda.is_available()
    DEVICE = 'cuda:0' if USE_CUDA else 'cpu'
    
    # Setup YOLOv5 with custom model weights
    model = torch.hub.load('yolov5/', 'custom', path=weights_path, source='local')
    if USE_CUDA:
        model = model.half()  # Half precision improves FPS
        print("YOLOv5 setup complete.")
        
    # multiprocessing
    listen_process = multiprocessing.Process(target=listen_to_commands)
    # Start the listen_process
    listen_process.start()

    time.sleep(5)  # Give a 5-second buffer before starting the video feed to avoid overloading

    # Start the video feed
    video_process = multiprocessing.Process(target=start_video_feed, args=(model,))
    video_process.start()

    # Wait for the all the processes to finish
    listen_process.join()
    video_process.join()
    
    # This is for multithreading but not using it
    # # Start listening for voice commands
    # listen_to_commands_thread = threading.Thread(target=listen_to_commands)

    # listen_to_commands_thread.start()
    # time.sleep(5)  # Give a 5-second buffer before starting the video feed

    # # Start the video feed sequentially to avoid overloading the system
    # start_video_feed()

    # # wait for the listening command to join the main thread (finish) to exit the program
    # # not pretty useful here since the listen command never end until you manual shutdown this thread
    # listen_to_commands_thread.join()
    
    