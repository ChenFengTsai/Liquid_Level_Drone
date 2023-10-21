import configparser
from djitellopy import Tello

def execute_drone_command(tello, command, in_flight):
    if command == "takeoff":
        if not in_flight:
            tello.takeoff()
            in_flight = True
    elif command == "land":
        if in_flight:
            tello.land()
            in_flight = False
    elif in_flight:  # Only execute the following commands if the drone is in flight
        if command == "move_forward":
            tello.move_forward(20)
    elif command == "move_forward":
        tello.move_forward(20)  # Default to 20 cm. Adjust as needed.
    elif command == "move_back":
        tello.move_back(20)
    elif command == "move_left":
        tello.move_left(20)
    elif command == "move_right":
        tello.move_right(20)
    elif command == "move_up":
        tello.move_up(20)
    elif command == "move_down":
        tello.move_down(20)
    elif command == "rotate_clockwise":
        tello.rotate_clockwise(90)
    elif command == "rotate_counter_clockwise":
        tello.rotate_counter_clockwise(90)
    elif command == "flip":
        tello.flip("f")  # Default to forward flip. Adjust as needed.
    elif command == "flip_backward":
        tello.flip('b')
    elif command == "flip_right":
        tello.flip('r')
    elif command == "streamon":
        tello.streamon()
    elif command == "streamoff":
        tello.streamoff()
    elif command == "go_xyz_speed":
        x, y, z, speed = 20, 20, 20, 10
        tello.go_xyz_speed(x, y, z, speed)
    elif command == "status":
        stats = get_drone_status(tello)
        print(stats)
    else:
        print(f"Unknown command: {command}")

    return command, in_flight

def get_drone_status(tello):
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