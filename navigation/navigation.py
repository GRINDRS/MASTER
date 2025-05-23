"""
Integrated Grid-Based Navigation with Optimized Turning and Image Verification
"""

import math
import time
import paho.mqtt.client as mqtt
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from basic_embedded.twomotorbasic import (
    move_forward, move_backward,
    turn_90_left, turn_90_right,
    turn_behind_left, turn_behind_right,
    motor1_stop, motor2_stop
)
from basic_embedded.ultrasonic_sensor import init_sensor, stop_sensor, get_distance
from capture_analyse import cap_anal

# Constants
PIVOT_DISTANCE = 30.0
OBSTACLE_THRESHOLD = 30.0

# Updated Location_matrix (using long exhibit names) for compatibility with voicebot (which now sends the long exhibit name) and capture_analyse (which uses the long exhibit name for image verification)
Location_matrix = [
    ["The Scream by Edvard Munch", "Mona Lisa by Leonardo da Vinci", "Sunflowers by Vincent van Gogh"],
    ["Plushy Dog Sculpture", 0, "Ancient Egyptian Statue"],
    ["Liberty Leading the People by Eugène Delacroix", "initial", "Starry Night by Vincent van Gogh"]
]

directions = ["UP", "RIGHT", "DOWN", "LEFT"]
currently_facing = "UP"
# MQTT client placeholder – will be initialised in start_navigation()
mqtt_client: mqtt.Client | None = None

currentPosition = [2, 1]  # Start at "Initial"

def wall_detection() -> bool:
    current = get_distance()
    return current is not None and current < PIVOT_DISTANCE

def update_orientation(turn: str):
    global currently_facing
    idx = directions.index(currently_facing)
    if turn == "RIGHT":
        currently_facing = directions[(idx + 1) % 4]
    elif turn == "LEFT":
        currently_facing = directions[(idx - 1) % 4]

def rotate_to_direction(direction_vector):
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
    rotate_to_direction(direction_vector)
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

    # Arrival logic
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

        # Verification with retries
        print("Running image verification...")
        verification_success = False
        for attempt in range(3):
            detected = cap_anal()
            if detected == location:
                print("Image verification successful.")
                verification_success = True
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

        if verification_success and mqtt_client:
            try:
                mqtt_client.publish("arrived", location)
                print("MQTT: Published 'arrived' for", location)
            except Exception as e:
                print("MQTT publish error:", e)
        elif not verification_success:
            print(f"WARNING: Expected '{location}' but image not confirmed after retries. Not publishing arrival.")

def next_position(name):
    for i, row in enumerate(Location_matrix):
        for j, val in enumerate(row):
            if val == name:
                return [i, j]
    return None

def get_to_location(location):
    global currentPosition
    target = next_position(location)
    if not target:
        print("Target location not found:", location)
        return

    while currentPosition != target:
        direction_vector = [target[0] - currentPosition[0], target[1] - currentPosition[1]]

        # Candidate moves (row-first and column-first)
        row_step = [int(direction_vector[0] / abs(direction_vector[0])) if direction_vector[0] != 0 else 0, 0]
        col_step = [0, int(direction_vector[1] / abs(direction_vector[1])) if direction_vector[1] != 0 else 0]

        def is_walkable(step_vec):
            nxt = [currentPosition[0] + step_vec[0], currentPosition[1] + step_vec[1]]
            if not (0 <= nxt[0] < len(Location_matrix) and 0 <= nxt[1] < len(Location_matrix[0])):
                return False
            return Location_matrix[nxt[0]][nxt[1]] != 0

        # Decide which axis to move along this step
        if row_step != [0, 0] and is_walkable(row_step):
            step = row_step
        elif col_step != [0, 0] and is_walkable(col_step):
            step = col_step
        else:
            # If preferred axes blocked, try the other non-zero axis anyway (may be forced to obstacle cell)
            step = col_step if row_step == [0, 0] else row_step

        next_step = [currentPosition[0] + step[0], currentPosition[1] + step[1]]
        calculate_movement(next_step, step, location)

# MQTT Setup
def on_connect(client, userdata, flags, rc):
    print("Connected with result code", rc)
    client.subscribe("movement")

def on_message(client, userdata, msg):
    global currently_facing
    location = msg.payload.decode()
    print("Received target location:", location)
    currently_facing = "UP"
    init_sensor()
    try:
        get_to_location(location)
    finally:
        stop_sensor()

def start_navigation():
    global mqtt_client
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.connect("localhost", 1883, 60)
    mqtt_client.loop_forever()

if __name__ == "__main__":
    start_navigation()
