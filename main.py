import time
from navigation.navigation import travel
from nlp_voice_bot.voicebot import mqtt_client
# TODO various other imports.

goal = None

def on_movement_message(client, userdata, msg):
    global goal
    goal = msg.payload.decode()
    print(f"MSG RECEIVED: {goal}")

def main():
    mqtt_client.subscribe("movement")
    mqtt_client.message_callback_add("movement", on_movement_message)

    while True:
        global goal
        
        if goal is None:
            time.sleep(0.5)
            continue
        
        did_timeout = travel(goal)
        if did_timeout:
            print("YOU LOSE!")

        goal = None

if __name__ == "__main__":
    main()