import time
import paho.mqtt.client as mqtt
from navigation.navigation import travel


# MQTT configuration
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

def main():
    global goal, navigation_active
    
    # Connect to MQTT broker
    mqtt_client.on_connect = on_connect
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()
    
    print("Main system initialized. Waiting for navigation commands...")

    while True:
        if not navigation_active:
            time.sleep(0.5)
            continue
        
        print(f"Starting navigation to: {goal}")
        result = travel(goal)
        
        # Send arrival notification
        print(f"Navigation completed with result: {'SUCCESS' if result == 0 else 'FAILURE'}")
        
        # More verbose arrival publishing
        arrival_message = f"arrived at {goal}"
        print(f"Publishing to {TOPIC_ARRIVED}: '{arrival_message}'")
        publish_result = mqtt_client.publish(TOPIC_ARRIVED, arrival_message)
        print(f"Publish result: {publish_result.rc} (0 means success)")
        
        # Reset navigation state
        navigation_active = False
        goal = None

if __name__ == "__main__":
    main()