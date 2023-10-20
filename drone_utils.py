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
    else:
        print(f"Unknown command: {command}")

    return command, in_flight


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
    drone.connect()

    # Connect to your home WiFi
    drone.connect_to_wifi(wifi_name, wifi_password)
    
    # manual reboost your drone
    
if __name__ == "__main__":
    drone_private_conn()