import time
from djitellopy import Tello

# Initialize the Tello drone connection
tello = Tello("192.168.87.41")
tello.connect()
tello.takeoff()

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

# Perform the movement
zigzag_movement()

# Land the drone after the process
tello.land()
