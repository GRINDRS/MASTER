
import paho.mqtt.client as mqtt

def on_message(client, userdata, message):
    print(f" Received on {message.topic}: {message.payload.decode()}")

client = mqtt.Client()
client.connect("localhost", 1883)
client.subscribe("movement")  
client.on_message = on_message
client.loop_forever()