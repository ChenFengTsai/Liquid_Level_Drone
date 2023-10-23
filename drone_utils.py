import configparser
from djitellopy import Tello

class DroneUtils:
    def __init__(self, tello, in_flight):
        self.tello = tello
        self.in_flight = in_flight
        
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
            self.tello.rotate_clockwise(90)
        elif command == "rotate_counter_clockwise":
            self.tello.rotate_counter_clockwise(90)
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