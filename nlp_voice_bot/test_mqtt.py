"""
test_mqtt.py

This script tests MQTT connectivity by subscribing to a topic and publishing
a test message to that same topic. It confirms that the client can both send
and receive messages via the broker.

Useful for verifying MQTT broker setup and basic communication with a local or remote broker.

Author: GRINDRS
Date: 2025
"""

import paho.mqtt.client as mqtt
import time

# MQTT broker configuration
BROKER_ADDRESS = "localhost"  # Change to your broker's IP if needed
PORT = 1883
TOPIC = "test/topic"
TEST_MESSAGE = "Hello from test_mqtt.py!"

# Flag to confirm message receipt
message_received = False

def on_connect(client, userdata, flags, rc):
    """
    Callback executed upon successful MQTT connection.

    Args:
        client: The client instance.
        userdata: Private user data (not used).
        flags: Response flags sent by the broker.
        rc: Connection result code.
    """
    if rc == 0:
        print("Connected to MQTT broker.")
        client.subscribe(TOPIC)
    else:
        print("Failed to connect. Return code:", rc)

def on_message(client, userdata, msg):
    """
    Callback executed when a message is received from the broker.

    Args:
        client: The client instance.
        userdata: Private user data (not used).
        msg: The received MQTT message.
    """
    global message_received
    print(f"Received message on topic '{msg.topic}': {msg.payload.decode()}")
    message_received = True

# Create MQTT client instance
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# Connect to the broker
client.connect(BROKER_ADDRESS, PORT, 60)

# Start the loop in a non-blocking thread
client.loop_start()

# Give the connection time to establish
time.sleep(2)

# Publish a test message
print(f"Publishing to {TOPIC}: {TEST_MESSAGE}")
client.publish(TOPIC, TEST_MESSAGE)

# Wait for a message or timeout
timeout = time.time() + 10  # 10-second timeout
while not message_received and time.time() < timeout:
    time.sleep(0.1)

client.loop_stop()
client.disconnect()

if message_received:
    print("MQTT test successful.")
else:
    print("MQTT test failed. No message received.")
