"""
grid_navigator.py

Integrated Grid-Based Navigation with Optimised Turning and Image Verification

This module controls a museum navigation robot that moves through a 3x3 grid of
exhibits using directional logic, obstacle detection, and image verification.
It subscribes to a target location via MQTT, aligns directionally using an
orientation model, and validates arrival using camera-based image recognition.

Key Features:
- Grid-based movement with directional memory
- Obstacle avoidance using ultrasonic sensors
- Image confirmation via OpenAI Vision pipeline
- MQTT message-driven navigation control

Author: GRINDRS
Date: 2025
"""

import math
import time
import paho.mqtt.client as mqtt
import sys
import os

# Import local modules for motor and sensor control
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from basic_embedded.twomotorbasic import (
    move_forward, move_backward,
    turn_90_left, turn_90_right,
    turn_behind_left, turn_behind_right,
    motor1_stop, motor2_stop
)
from basic_embedded.ultrasonic_sensor import init_sensor, stop_sensor, get_distance
from capture_analyse import cap_anal

# -----------------------------
# Constants and Initial States
# -----------------------------

PIVOT_DISTANCE = 30.0  # Distance in cm to consider obstacle too close
OBSTACLE_THRESHOLD = 30.0  # Redundant but defined for future use

# Location matrix representing 3x3 grid of exhibits
Location_matrix = [
    ["The Scream by Edvard Munch", "Mona Lisa by Leonardo da Vinci", "Sunflowers by Vincent van Gogh"],
    ["Plushy Dog Sculpture", 0, "Ancient Egyptian Statue"],
    ["Liberty Leading the People by Eugène Delacroix", "initial", "Starry Night by Vincent van Gogh"]
]

# Directional states and starting position
directions = ["UP", "RIGHT", "DOWN", "LEFT"]
currently_facing = "UP"
currentPosition = [2, 1]  # Start at the "initial" location

# -----------------------------
# Navigation and Detection
# -----------------------------

def wall_detection() -> bool:
    """
    Returns True if an obstacle is detected within the pivot distance threshold.
    """
    current = get_distance()
    return current is not None and current < PIVOT_DISTANCE

def update_orientation(turn: str):
    """
    Updates the robot’s orientation based on the last turn direction.

    Args:
        turn (str): Either "LEFT" or "RIGHT".
    """
    global currently_facing
    idx = directions.index(currently_facing)
    if turn == "RIGHT":
        currently_facing = directions[(idx + 1) % 4]
    elif turn == "LEFT":
        currently_facing = directions[(idx - 1) % 4]

def rotate_to_direction(direction_vector):
    """
    Rotates the robot to face a new direction based on the direction vector.

    Args:
        direction_vector (list[int]): A vector like [-1, 0] representing direction.
    """
    global currently_facing
    direction_map = {
        (-1, 0): "UP",
        (1, 0): "DOWN",
        (0, -1): "LEFT",
        (0, 1): "RIGHT"
    }
    desired = direction_map.get(tuple(direction_vector))
    if desired is None:
        return

    current_index = directions.index(currently_facing)
    desired_index = directions.index(desired)
    delta = (desired_index - current_index) % 4

    # Determine the shortest rotation (left/right/180)
    if delta == 0:
        return
    elif delta == 1:
        turn_90_right()
        update_orientation("RIGHT")
    elif delta == 2:
        turn_behind_left()
        update_orientation("RIGHT")
        update_orientation("RIGHT")
    elif delta == 3:
        turn_90_left()
        update_orientation("LEFT")

def calculate_movement(next_loc, direction_vector, location):
    """
    Rotates, checks for obstacles, moves forward, and performs image verification.

    Args:
        next_loc (list[int]): Coordinates of the next position.
        direction_vector (list[int]): Direction to face.
        location (str): Target location name for image verification.
    """
    rotate_to_direction(direction_vector)

    # Wait for obstacle to clear
    if wall_detection():
        print("Obstacle detected. Waiting...")
        while wall_detection():
            time.sleep(1)

    print("Moving forward to:", next_loc)
    move_forward()
    time.sleep(4.75)
    motor1_stop()
    motor2_stop()

    global currentPosition
    currentPosition = next_loc

    # If reached destination, verify exhibit visually
    if currentPosition == next_position(location):
        wall_direction = None
        if currentPosition == [3, 1] or currentPosition == [0, 1]:
            wall_direction = "UP"
        elif currentPosition[1] == 0:
            wall_direction = "LEFT"
        elif currentPosition[1] == 2:
            wall_direction = "RIGHT"

        if wall_direction:
            print("Adjusting to face wall:", wall_direction)
            target_vector = {
                "UP": (-1, 0), "RIGHT": (0, 1),
                "DOWN": (1, 0), "LEFT": (0, -1)
            }[wall_direction]
            rotate_to_direction(target_vector)

        # Retry image verification if initial attempt fails
        print("Running image verification...")
        for attempt in range(3):
            detected = cap_anal()
            if detected == location:
                print("Image verification successful.")
                break
            print(f"Attempt {attempt + 1}: Image not matched. Adjusting position.")

            if attempt == 0:
                move_backward()
                time.sleep(0.3)
            elif attempt == 1:
                move_forward()
                time.sleep(0.6)

            motor1_stop()
            motor2_stop()
        else:
            print(f"WARNING: Expected '{location}' but image not confirmed after retries.")

def next_position(name):
    """
    Looks up the coordinates of a given exhibit name.

    Args:
        name (str): Exhibit name.

    Returns:
        list[int] | None: Grid coordinates if found, else None.
    """
    for i, row in enumerate(Location_matrix):
        for j, val in enumerate(row):
            if val == name:
                return [i, j]
    return None

def get_to_location(location):
    """
    Navigates the robot to the specified exhibit location.

    Args:
        location (str): Target exhibit name.
    """
    global currentPosition
    target = next_position(location)
    if not target:
        print("Target location not found:", location)
        return

    # Move in a stepwise fashion until the robot reaches the target
    while currentPosition != target:
        direction_vector = [target[0] - currentPosition[0], target[1] - currentPosition[1]]
        step = [0, 0]
        if direction_vector[0] != 0:
            step[0] = int(direction_vector[0] / abs(direction_vector[0]))
        elif direction_vector[1] != 0:
            step[1] = int(direction_vector[1] / abs(direction_vector[1]))
        next_step = [currentPosition[0] + step[0], currentPosition[1] + step[1]]
        calculate_movement(next_step, step, location)

# -----------------------------
# MQTT Communication
# -----------------------------

def on_connect(client, userdata, flags, rc):
    """
    Callback triggered on successful MQTT connection.

    Args:
        client: MQTT client.
        userdata: User data (unused).
        flags: Response flags.
        rc: Connection result code.
    """
    print("Connected with result code", rc)
    client.subscribe("movement")

def on_message(client, userdata, msg):
    """
    Handles incoming MQTT messages to trigger navigation.

    Args:
        client: MQTT client.
        userdata: User data (unused).
        msg: MQTT message.
    """
    global currentPosition, currently_facing
    location = msg.payload.decode()
    print("Received target location:", location)
    currentPosition = [3, 1]  # Reset position
    currently_facing = "UP"
    init_sensor()
    try:
        get_to_location(location)
    finally:
        stop_sensor()

def start_navigation():
    """
    Initialises the MQTT client and starts listening for movement commands.
    """
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("localhost", 1883, 60)
    client.loop_forever()

if __name__ == "__main__":
    start_navigation()
