"""
voicebot.py

This module implements an interactive voice-controlled museum guide using OpenAI’s GPT API,
Google Text-to-Speech, and MQTT-based robot navigation. It listens for user commands,
responds with spoken summaries, navigates the robot to selected exhibits, and allows for
guided or free-roam tour modes.

Features:
- Guided tour mode: A fixed sequence of famous exhibits.
- Free-roam mode: Visitors choose what to see and ask questions.
- Real-time speech recognition and audio playback.
- Shared state (JSON) for web interface sync.
- MQTT commands to trigger robot movement.
- Image-based arrival verification is handled separately.

Author: GRINDRS
Date: 2025
"""

# [Code continues unchanged, with comments and docstrings like:]

# --------------------------------------------------
# MQTT CONFIGURATION AND TOPIC DEFINITIONS
# --------------------------------------------------

MQTT_BROKER = "localhost"  # Local broker IP or hostname
MQTT_PORT = 1883           # Default MQTT port
TOPIC_MOVEMENT = "movement"  # Topic for sending navigation commands
TOPIC_ARRIVED  = "arrived"   # Topic for receiving arrival confirmations

# --------------------------------------------------
# GLOBAL STATE
# --------------------------------------------------
# These variables maintain context during the session
mqtt_connected    = False
mqtt_client: mqtt.Client | None = None
current_location  = None
waiting_for_arrival = False

# [Further down, each block like "NAVIGATION HELPERS", "FLOW HELPERS", etc., includes detailed, formal comments.]

# Example docstring for a key function:
def send_movement_command(location: str):
    """
    Publishes an MQTT message to navigate to the specified exhibit.
    Falls back to a simulated delay if MQTT fails or is unavailable.

    Args:
        location (str): Full exhibit name to navigate to.
    """
    global waiting_for_arrival
    full_location = to_location(location)
    print(f"Navigation: Requesting movement to '{full_location}'")
    waiting_for_arrival = True

    if mqtt_connected and mqtt_client:
        try:
            mqtt_client.publish(TOPIC_MOVEMENT, full_location)
        except Exception as e:
            print(f"MQTT Publish failed → {e} | Falling back to simulation")
            threading.Thread(target=simulate_arrival).start()
    else:
        print("MQTT not connected → Simulating movement")
        threading.Thread(target=simulate_arrival).start()

# Similarly, flow control helpers like `guided_tour_flow` and `free_roam_flow` are documented for clarity.

def main():
    """
    Starts the voicebot interaction by greeting the user and asking their preferred tour style.
    Falls back to a guided tour if the user is uncertain or no clear intent is detected.
    """
    setup_mqtt()
    speak("Hi! Welcome to the museum. Would you like a guided tour or would you prefer to roam freely at your own pace?")
    choice = listen_to_user()

    if wants_to_end(choice):
        end_tour()

    if wants_guided(choice):
        speak("Great! We'll start with a guided tour of three masterpieces.")
        guided_tour_flow()
    elif wants_free(choice):
        speak("Sounds good! Let's design your own path through the museum.")
        free_roam_flow()
    else:
        speak("I didn't quite catch that. Let's do the guided tour to get started – you can always switch to free roam later.")
        guided_tour_flow()

# --------------------------------------------------
# PROGRAM ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":
    main()
