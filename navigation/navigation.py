
"""
SuperSimpleNAVigation 


Proprietary software by GRINDRS - Ideas First; Innovation Later.
"""
import math
import time
import paho.mqtt.client as mqtt
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from basic_embedded.twomotorbasic import move_forward, move_backward, \
                                       turn_right, motor1_stop, motor2_stop,\
                                       turn_90_left, turn_90_right
from basic_embedded.ultrasonic_sensor import init_sensor, stop_sensor, get_distance
from capture_analyse import cap_anal

NINETY_DEG = 0.5
TIMEOUT_SECONDS = 90
PIVOT_DISTANCE = 30.00
OBSTACLE_THRESHOLD = 30.00

PAIRINGS: dict[str, str] = {
    "Mona Lisa": "Toy Dog",
    "Sunflowers (Van Gogh)": "Stylized Egyptian Sculpture",
    "Liberty Leading the People": "",
    "": "Starry Night"
}

SUCCESS = 0
FAILURE = 1

def wall_detection() -> bool:
    current_subsonic = get_distance()
    if current_subsonic is not None and current_subsonic < PIVOT_DISTANCE:
        return True
    return False

def goal_artwork() -> str:
    return ""

def detect_artwork() -> str:
    return cap_anal()

def is_correct_position(goal_art: str) -> bool:
    detected_art = detect_artwork()
    print(f"Detected artwork: {detected_art}, Goal: {goal_art}")
    if (goal_art == detected_art or 
        goal_art == PAIRINGS.get(detected_art, "") or
        detected_art == PAIRINGS.get(goal_art, "")):
        return True
    return False

def search_timeout(start_time: float) -> bool:
    return (time.time() - start_time) > TIMEOUT_SECONDS

def travel(goal: str) -> int:
    print("Starting travel logic...")
    init_sensor()
    start_time = time.time()

    try:
        while not is_correct_position(goal):
            if search_timeout(start_time):
                print("Search timed out.")
                return FAILURE

            distance = get_distance()
            if distance != 999 and distance < OBSTACLE_THRESHOLD:
                print(f"Obstacle too close ({distance} cm). Checking visual...")

                motor1_stop()
                motor2_stop()

                visual_output = cap_anal()
                print(f"Visual detection result: {visual_output}")

                if visual_output.strip().lower() == "wall":
                    print("Wall detected. Turning right.")
                    turn_90_right()
                else:
                    print("Not a wall. Waiting...")
                    while get_distance() != 999 and get_distance() <= OBSTACLE_THRESHOLD:
                        time.sleep(0.2)

                print("Resuming movement.")
            else:
                move_forward()
                time.sleep(3)

            motor1_stop()
            motor2_stop()

        print("Goal position reached.")
        return SUCCESS

    finally:
        stop_sensor()

# MQTT setup
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
TOPIC_MOVEMENT = "movement"
TOPIC_ARRIVED = "arrived"

mqtt_client = mqtt.Client(protocol=mqtt.MQTTv311)
goal = None
navigation_active = False

def on_movement_message(client, userdata, msg):
    global goal, navigation_active
    goal = msg.payload.decode()
    navigation_active = True
    print(f"Movement request received: {goal}")

def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT broker with result code {rc}")
    mqtt_client.subscribe(TOPIC_MOVEMENT)
    mqtt_client.message_callback_add(TOPIC_MOVEMENT, on_movement_message)

def start_navigation_loop():
    global goal, navigation_active
    mqtt_client.on_connect = on_connect
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()

    print("Navigation system initialized. Waiting for commands...")
    while True:
        if not navigation_active:
            time.sleep(0.5)
            continue

        print(f"Starting navigation to: {goal}")
        result = travel(goal)

        arrival_message = f"arrived at {goal}"
        print(f"Publishing to {TOPIC_ARRIVED}: '{arrival_message}'")
        mqtt_client.publish(TOPIC_ARRIVED, arrival_message)

        navigation_active = False
        goal = None

# Automatically start navigation loop if this script is run
if __name__ == "__main__":
    start_navigation_loop()
