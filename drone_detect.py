import cv2
import torch
# import openai
from djitellopy import Tello
import azure.cognitiveservices.speech as speechsdk
import threading
import multiprocessing
import time
import drone_utils
import configparser
import os

#########################
# SETUP
#########################

# Constants
config = configparser.ConfigParser()
config.read('config.ini')
AZURE_SUBSCRIPTION_KEY = config.get('API key', 'AZURE_SUBSCRIPTION_KEY')
AZURE_SERVICE_REGION = config.get('API key', 'AZURE_SERVICE_REGION')

TELLO_IP = config.get('tello', 'ip')

# Paths (change these paths as per your system)
exp = "exp2-best"
root_path =  "/Users/richtsai1103/liquid_level_drone"
weights_path = os.path.join(root_path, f"yolov5/runs/train/{exp}/weights/best.pt")
model_path = os.path.join(root_path, "yolov5/")

# Assuming you initialize drone_state as 'landed' or 'flying' elsewhere in your script
in_flight = False

# ACTIONS TO COMMANDS MAPPING
ACTIONS_TO_COMMANDS = {
    ("start", "fly", "take off", "lift off", "launch", "begin flight", "skyward"): "takeoff",
    ("land", "settle", "touch down", "finish", "end flight", "ground"): "land",
    ("front flip", "forward flip"): "flip",
    ("forward", "move ahead", "go straight", "advance", "head forward", "proceed front", "go on", "move on"): "move_forward",
    ("backward", "move back", "retreat", "go backward", "back up", "reverse", "recede"): "move_back",
    ("left", "move left", "go leftward", "turn leftward", "shift left", "sidestep left"): "move_left",
    ("right", "move right", "go rightward", "turn rightward", "shift right", "sidestep right"): "move_right",
    ("move up", "up", "ascend", "rise", "climb", "skyrocket", "soar upwards", "elevate"): "move_up",
    ("move down", "down", "descend", "lower", "sink", "drop", "fall", "decline"): "move_down",
    ("spin right", "rotate clockwise", "turn right", "twirl right", "circle right", "whirl right", "swirl right"): "rotate_clockwise",
    ("spin left", "rotate counter-clockwise", "turn left", "twirl left", "circle left", "whirl left", "swirl left"): "rotate_counter_clockwise",
    ("back flip", "flip back"): "flip_backward",
    ("flip", "forward flip", "flip forward"): "flip_forward",
    ("right flip", "flip to the right", "sideways flip right"): "flip_right",
    ("video on", "start video", "begin stream", "camera on"): "streamon",
    ("video off", "stop video", "end stream", "camera off"): "streamoff",
    ("go xyz", "specific move", "exact move", "precise direction", "navigate xyz"): "go_xyz_speed",
    ("give me stats", "status"): "status"
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


def setup_speechrecog():
    # Setup Azure Speech SDK
    print("Setting up Azure Speech SDK...")
    speech_config = speechsdk.SpeechConfig(subscription='55f2007ae13640a59b52e03dad3361ea', endpoint="https://northcentralus.api.cognitive.microsoft.com/sts/v1.0/issuetoken")
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)
    print("Azure Speech SDK setup complete.")
    return speech_recognizer

def listen_to_commands():
    try:
        speech_recognizer = setup_speechrecog()
        print("Listening for commands. Speak into your microphone...")
        
        while True:
            command_heard = ""  # Initialize it at the start of the loop
            print("\nAwaiting command...")
            
            result = speech_recognizer.recognize_once()
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                try:
                    command_heard = result.text.lower().strip('.')
                    print(f"\nHeard: {command_heard}")
                except Exception as e:  # Using a more generic exception to catch any unexpected errors
                    print(f"Error processing heard command: {e}")
                    command_heard = ""
            
                drone_command = interpret_command_to_drone_action(command_heard)              
                if drone_command:
                    print(f"\nExecuting command: {drone_command}")
                    ## mocking ##
                    mock = True
                    if mock:
                        mock_execute_drone_command(drone_command)
                        
                    else:
                        try:
                            command, in_flight = drone_utils.execute_drone_command(tello, drone_command, in_flight)
                            print(f"Executed command: {command}")
                        except Exception as e:
                            print(f"Error executing the command: {e}")
                else:
                    print(f"\nCould not interpret the command: {command_heard}")
                    
            elif result.reason == speechsdk.ResultReason.NoMatch:
                print("\nNo speech could be recognized.")
                
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation = result.cancellation_details
                print(f"\nSpeech Recognition canceled: {cancellation.reason}")
                if cancellation.reason == speechsdk.CancellationReason.Error:
                    print(f"Error details: {cancellation.error_details}")

            # Check for a command to end the program gracefully
            if "terminate program" in command_heard:
                print("Terminating program...")
                break

    except Exception as e:
        print(f"Error in recognizing speech: {e}")

def start_video_feed(model, tello):
    try:
        print("Attempting to start the Tello camera feed...")
        frame_read = tello.get_frame_read()

        if not frame_read:
            print("Failed to get Tello frame read. Exiting.")
            return

        last_report_time = time.time()
        report_interval = 10  # seconds

        while True:
            # Original high-resolution frame
            frame_original = frame_read.frame

            # Convert to grayscale for faster processing
            # frame_gray = cv2.cvtColor(frame_original, cv2.COLOR_BGR2GRAY)
            frame_rgb = cv2.cvtColor(frame_original, cv2.COLOR_BGR2RGB)
            

            # Resize for faster processing
            frame_resized = cv2.resize(frame_rgb, (640, 480))

            # YOLO processing on low-res frame
            results = model(frame_resized)
            rendered_frame_small = results.render()[0]

            # Resize the rendered frame to a larger resolution for display
            rendered_frame_large = cv2.resize(rendered_frame_small, (1280, 960))  # Double the display size, adjust as needed

            # If it's time to report detections
            if time.time() - last_report_time > report_interval:
                for detection in results.pred[0]:
                    x1, y1, x2, y2, conf, class_id = map(float, detection)
                    label = results.names[int(class_id)]
                    print(f"Detected: {label}, Confidence: {conf:.2f}")
                # Reset the report timer after reporting
                last_report_time = time.time()
                print("-------")

            # Display the high-resolution frame with detections overlaid
            cv2.imshow('YOLOv5 Tello Feed', rendered_frame_large)

            if cv2.waitKey(1) == ord('q'):
                break

        cv2.destroyAllWindows()
        print("Tello camera feed ended.")

    except Exception as e:
        print(f"Error starting the video feed: {e}")
        

#########################
# MAIN LOOP - Execute the script!
#########################

if __name__ == "__main__":

    # Check CUDA availability
    USE_CUDA = torch.cuda.is_available()
    DEVICE = 'cuda:0' if USE_CUDA else 'cpu'
    
    # Setup YOLOv5 with custom model weights
    model = torch.hub.load('yolov5/', 'custom', path=weights_path, source='local').to(DEVICE)
    if USE_CUDA:
        model = model.half()  # Half precision improves FPS
        print("YOLOv5 setup complete.")
    
    # --- TELLO DRONE SETUP ---
    print("Start Drone")
    tello = Tello(TELLO_IP)
    tello.connect(False)

    # start video streaming 
    tello.streamon()
    
    # get better real-time performance
    tello.set_video_fps(tello.FPS_30)
    tello.set_video_resolution(tello.RESOLUTION_480P)
    tello.set_video_bitrate(tello.BITRATE_2MBPS)
    
    # multiprocessing
    listen_process = multiprocessing.Process(target=listen_to_commands)
    listen_process.start()

    time.sleep(5)  # Give a 5-second buffer before starting the video feed to prevent overload

    # Start the video feed in another processes
    video_process = multiprocessing.Process(target=start_video_feed, args=(model, tello))
    video_process.start()
    time.sleep(5)
    
    # todo: fix state udp
    # stats = drone_utils.get_drone_status(tello)
    # print(stats)

    # Wait for the listen_process to finish, (not useful here since listen command never end untial you manual shut it)
    listen_process.join()
    video_process.join()

    # todo: multithreading
    # # Start listening for voice commands
    # listen_to_commands_thread = threading.Thread(target=listen_to_commands)

    # listen_to_commands_thread.start()
    # time.sleep(5)  # Give a 5-second buffer before starting the video feed to avoid overloading the system
    
    # start_video_feed(model)
    # time.sleep(5)
    
    # # Get the drone's status
    # stats = drone_utils.get_drone_status(model)
    # print(stats)

    # listen_to_commands_thread.join()