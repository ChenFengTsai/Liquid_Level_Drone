import cv2
import torch
# import openai
from djitellopy import Tello
import azure.cognitiveservices.speech as speechsdk
#import threading
import multiprocessing
import time
import drone_utils

#########################
# SETUP
#########################

# Constants
AZURE_SUBSCRIPTION_KEY = '55f2007ae13640a59b52e03dad3361ea'
AZURE_SERVICE_REGION = 'https://northcentralus.api.cognitive.microsoft.com/sts/v1.0/issuetoken'
#OPENAI_API_KEY = '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'
TELLO_IP = '192.168.86.42'

# Paths (change these paths as per your system)
weights_path = "yolov5/runs/train/exp2-best/weights/best.pt"

# Assuming you initialize drone_state as 'landed' or 'flying' elsewhere in your script
in_flight = False

# Setup OpenAI API
# print("Setting up OpenAI...")
# openai.api_key = OPENAI_API_KEY
# print("OpenAI setup complete.")

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
    ("go xyz", "specific move", "exact move", "precise direction", "navigate xyz"): "go_xyz_speed"
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

# def get_interpretation_from_openai(command):
#     response = openai.Completion.create(
#         model="text-davinci-002",
#         prompt=f"What drone action corresponds to the command: '{command}'?",
#         max_tokens=50
#     )
#     interpreted_action = response.choices[0].text.strip().lower()
#     return interpret_command_to_drone_action(interpreted_action)

# def execute_drone_command(command):
#     global in_flight

#     if command == "takeoff":
#         if not in_flight:
#             tello.takeoff()
#             in_flight = True
#     elif command == "land":
#         if in_flight:
#             tello.land()
#             in_flight = False
#     elif in_flight:  # Only execute the following commands if the drone is in flight
#         if command == "move_forward":
#             tello.move_forward(20)
#     elif command == "move_forward":
#         tello.move_forward(20)  # Default to 20 cm. Adjust as needed.
#     elif command == "move_back":
#         tello.move_back(20)
#     elif command == "move_left":
#         tello.move_left(20)
#     elif command == "move_right":
#         tello.move_right(20)
#     elif command == "move_up":
#         tello.move_up(20)
#     elif command == "move_down":
#         tello.move_down(20)
#     elif command == "rotate_clockwise":
#         tello.rotate_clockwise(90)
#     elif command == "rotate_counter_clockwise":
#         tello.rotate_counter_clockwise(90)
#     elif command == "flip":
#         tello.flip("f")  # Default to forward flip. Adjust as needed.
#     elif command == "flip_backward":
#         tello.flip('b')
#     elif command == "flip_right":
#         tello.flip('r')
#     elif command == "streamon":
#         tello.streamon()
#     elif command == "streamoff":
#         tello.streamoff()
#     elif command == "go_xyz_speed":
#         x, y, z, speed = 20, 20, 20, 10
#         tello.go_xyz_speed(x, y, z, speed)
#     else:
#         print(f"Unknown command: {command}")

#     return command

def get_drone_status():
    # Basic status
    battery_level = tello.get_battery()
    drone_speed_x = tello.get_speed_x()
    drone_speed_y = tello.get_speed_y()
    drone_speed_z = tello.get_speed_z()
    flight_time = tello.get_flight_time()
    
    # Additional status
    min_temp = tello.get_lowest_temperature()  # Returns the lowest temperature
    max_temp = tello.get_highest_temperature()  # Returns the highest temperature
    pitch = tello.get_pitch()  # Returns the drone's pitch
    roll = tello.get_roll()  # Returns the drone's roll
    barometer = tello.get_barometer()  # Gets the barometer value in cm
    flight_distance = tello.get_distance_tof()  # Gets the Time of Flight distance in cm
    
    status_message = (f"Drone Status:\n"
                      f"Battery Level: {battery_level}%\n"
                      f"Speed X: {drone_speed_x}cm/s\n"
                      f"Speed Y: {drone_speed_y}cm/s\n"
                      f"Speed Z: {drone_speed_z}cm/s\n"
                      f"Flight Time: {flight_time} seconds\n"
                      f"Min Temp: {min_temp}°C\n"
                      f"Max Temp: {max_temp}°C\n"
                      f"Pitch: {pitch}°\n"
                      f"Roll: {roll}°\n"
                      f"Barometer: {barometer}cm\n"
                      f"Flight Distance (ToF): {flight_distance}cm")
    
    return status_message

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
                
                if "give me stats" in command_heard:
                    stats = get_drone_status()
                    print(stats)
                    # speak_feedback(stats)
                    continue

                drone_command = interpret_command_to_drone_action(command_heard)
                
                # if not drone_command:
                #     # Get interpretation from OpenAI
                #     interpreted = get_interpretation_from_openai(command_heard)
                #     # Safeguard to ensure interpreted action is in our predefined list
                #     if interpreted in ACTIONS_TO_COMMANDS.values():
                #         drone_command = interpreted
                
                if drone_command:
                    print(f"\nExecuting command: {drone_command}")
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

def start_video_feed():
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
            frame_gray = cv2.cvtColor(frame_original, cv2.COLOR_BGR2GRAY)
            # frame_rgb = cv2.cvtColor(frame_original, cv2.COLOR_BGR2RGB)

            # Resize for faster processing
            frame_resized = cv2.resize(frame_gray, (640, 480))

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
    tello.connect()
    tello.streamoff()
    tello.streamon()
    
    # multiprocessing
    listen_process = multiprocessing.Process(target=listen_to_commands)
    # Start the listen_process
    listen_process.start()

    time.sleep(5)  # Give a 5-second buffer before starting the video feed

    # Start the video feed sequentially to avoid overloading the system
    start_video_feed()
    time.sleep(5)
    
    stats = get_drone_status()
    print(stats)

    # Wait for the listen_process to finish, (not useful here since listen command never end untial you manual shut it)
    listen_process.join()

    # # Start listening for voice commands
    # listen_to_commands_thread = threading.Thread(target=listen_to_commands)

    # listen_to_commands_thread.start()
    # time.sleep(5)  # Give a 5-second buffer before starting the video feed
    
                  
    # # Start the video feed sequentially to avoid overloading the system
    # start_video_feed()
    # time.sleep(5)
    
    # # Get the drone's status
    # stats = get_drone_status()
    # print(stats)

    # listen_to_commands_thread.join()