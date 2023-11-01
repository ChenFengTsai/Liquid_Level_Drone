import time
from djitellopy import Tello

# Initialize the Tello drone connection
tello = Tello()
tello.connect()
tello.takeoff()

def lawnmower_pattern(distance=100, height=20, wait_time=3, segments=4):
    segment_distance = distance // segments
    for _ in range(segments):
        tello.move_forward(segment_distance)
        time.sleep(wait_time)

def zigzag_movement(patterns=3, height=20):
    for i in range(patterns):
        if i % 2 == 0:  # Even pattern (0-indexed)
            lawnmower_pattern(height=height)
        else:  # Odd pattern
            lawnmower_pattern(height=height)
            tello.move_up(height)

# Perform the movement
zigzag_movement()

# Land the drone after the process
tello.land()
