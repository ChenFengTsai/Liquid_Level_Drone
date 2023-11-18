import configparser
from djitellopy import Tello
import time
from collections import Counter
import json

class DroneUtils:
    def __init__(self, tello, in_flight):
        self.tello = tello
        self.in_flight = in_flight
        self.make_center = False
        self.center_times = 0
        self.p_current = []
        self.pred_ls = []
        self.pred_res = {}
        self.all_res = {}
        
    def execute_drone_command(self, command):
        dist = 20
        if command == "takeoff":
            if not self.in_flight:
                self.tello.takeoff()
                self.in_flight = True
            else:
                self.tello.send_control_command("command")
        elif command == "land":
            if self.in_flight:
                self.tello.land()
                self.in_flight = False
        elif command == "move_forward":
            self.tello.move_forward(dist)  # Default to 20 cm. Adjust as needed.
        elif command == "move_back":
            self.tello.move_back(dist)
        elif command == "move_left":
            self.tello.move_left(dist)
        elif command == "move_right":
            self.tello.move_right(dist)
        elif command == "move_up":
            self.tello.move_up(dist)
        elif command == "move_down":
            self.tello.move_down(dist)
        elif command == "rotate_clockwise":
            self.tello.rotate_clockwise(30)
        elif command == "rotate_counter_clockwise":
            self.tello.rotate_counter_clockwise(30)
        elif command == "flip":
            self.tello.flip("f")  # Default to forward flip. Adjust as needed.
        elif command == "flip_backward":
            self.tello.flip('b')
        elif command == "flip_right":
            self.tello.flip('r')
        elif command == "streamon":
            self.tello.streamon()
        elif command == "streamoff":
            self.tello.streamoff()
        elif command == "go_xyz_speed":
            x, y, z, speed = dist, dist, dist, 10
            self.tello.go_xyz_speed(x, y, z, speed)
        elif command == 'navigation':
            self.zigzag_movement()
            
            # final result reporting
            print("\nDetect objects: ", len(self.pred_ls))
            for i in range(len(self.pred_ls)):
                labels = [label for label, conf, e_time in self.pred_ls[i]]
                cts = Counter(labels)
                print(f'Predictions for item {i}: ', cts)
                if not cts:
                    most_common = 'Nothing'
                else:
                    most_common = cts.most_common(1)[0][0]
                    
                self.pred_res[i] = most_common
                self.all_res[i] = self.pred_ls[i]
            print('\nFinal Report: ', self.pred_res)

            
        elif command == "status":
            stats = self.get_drone_status(self.tello)
            print(stats)
        elif command == "disconnect":
            self.tello.disconnect()
        else:
            # keep sending signal to prevent auto shutdown
            self.tello.send_control_command('command')
            print(f"Unknown command: {command}")

        return command

    def lawnmower_pattern(self, distance=100, wait_time=10, segments=1, direction="left"):
        segment_distance = distance // segments
        for _ in range(segments):
            print(f'\nMoving {direction} with {segment_distance}cm for next object')
            if direction == "left":
                self.tello.move_left(segment_distance)
            else: 
                self.tello.move_right(segment_distance)
                
            self.moving_start = time.time()
            self.center_times = 0
            self.make_center = True
            # 10 seconds for centering and detecting, change it if needed
            time.sleep(wait_time)
            
            self.pred_ls.append(self.p_current)
            self.p_current = []
            
            # end centering and start moving
            self.make_center = False
            

    def zigzag_movement(self, patterns=4, distance=40, height=45, segments=1, wait_time=10):
        directions = ["left", "right", "left", "right"]  # Starting from bottom right, as specified
        for i in range(patterns):
            self.lawnmower_pattern(distance=distance, segments=segments, direction=directions[i])
            
            if i < patterns - 1:  # Don't move up after the last pattern
                self.tello.move_up(height)
                
                self.moving_start = time.time()
                self.center_times = 0
                self.make_center = True
                # 10 seconds for centering and detecting, change it if needed
                time.sleep(wait_time)
                
                self.pred_ls.append(self.p_current)
                self.p_current = []  
                self.make_center = False 
                
                
    def center(self, bbox, img_size):
        center_x = (bbox[0] + bbox[2]) / 2
        center_y = (bbox[1] + bbox[3]) / 2

        # Calculate the desired center within your frame
        desired_center_x = img_size / 2  # Half of the frame width
        desired_center_y = img_size / 2  # Half of the frame height

        # Calculate the direction and distance to move the drone
        delta_x = center_x - desired_center_x
        print(f'Object away from center: {delta_x}_x')
        delta_y = center_y - desired_center_y
        print(f'Object away from center: {delta_y}_y')
        distance = ((bbox[0]-bbox[2])**2 + (bbox[1]-bbox[3])**2)**0.5
        print(f'Box size: {distance}')

        
        # adjust the threshold for drone movement
        ### Remember it is 320 now
        threshold = img_size//4
        distance_threshold = (img_size/2.65, img_size/0.75)

        # Send control commands to the drone based on the delta values
        if abs(delta_x) > threshold:
            # Adjust the drone's horizontal position
            if delta_x > 0:
                # Move right
                self.execute_drone_command('move_right')
                print('Centering: Move Right')
            else:
                # Move left
                self.execute_drone_command('move_left')
                print('Centering: Move Left')

        if abs(delta_y) > threshold:
            # Adjust the drone's vertical position
            if delta_y > 0:
                # Move down
                self.execute_drone_command('move_down')
                print('Centering: Move Down')
            else:
                # Move up
                self.execute_drone_command('move_up')
                print('Centering: Move Up')
                
        # move forward and backward when the bbox is not at the corner (means mistake)
        # todo: tune the threshold
        
        if not (bbox[0]<20) or (bbox[1]<20) or bbox[2]>300 or bbox[3]>300:
            if distance < distance_threshold[0]:
                # Move forward
                self.execute_drone_command('move_forward')
                print('Centering: Move Forward')
                
            elif distance > distance_threshold[1]:
                # Move back
                self.execute_drone_command('move_back')
                print('Centering: Move Back')
                
        if abs(delta_x) <= threshold \
            and abs(delta_y) <= threshold \
                and distance_threshold[0] <= distance <= distance_threshold[1]:
            # make as finished centering
            self.make_center = False
                
            
    def get_drone_status(self):
        # Basic status
        battery_level = self.tello.get_battery()
        drone_speed_x = self.tello.get_speed_x()
        drone_speed_y = self.tello.get_speed_y()
        drone_speed_z = self.tello.get_speed_z()
        flight_time = self.tello.get_flight_time()
        
        # Additional status
        min_temp = self.tello.get_lowest_temperature()  # Returns the lowest temperature
        max_temp = self.tello.get_highest_temperature()  # Returns the highest temperature
        pitch = self.tello.get_pitch()  # Returns the drone's pitch
        roll = self.tello.get_roll()  # Returns the drone's roll
        barometer = self.tello.get_barometer()  # Gets the barometer value in cm
        flight_distance = self.tello.get_distance_tof()  # Gets the Time of Flight distance in cm
        
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

def drone_private_conn():
    """
    Allow you to connect your drone to private net and control it through the private net
    """
    # get info from config file
    config = configparser.ConfigParser()
    config.read('config.ini')
    wifi_name = config.get('wifi', 'wifi_name')
    wifi_password = config.get('wifi', 'wifi_password')
        
    # Connect to the drone
    drone = Tello()
    drone.connect(False)

    # Connect to your home WiFi
    drone.connect_to_wifi(wifi_name, wifi_password)
    
    # reboot the drone
    
if __name__ == "__main__":
    drone_private_conn()