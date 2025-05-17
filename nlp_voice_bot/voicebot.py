import paho.mqtt.client as mqtt
import speech_recognition as sr
import os
import time
import json
import random
import subprocess
from gtts import gTTS
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
TOPIC_MOVEMENT = "movement"
TOPIC_ARRIVED = "arrived"

# Check if running in Docker container
IN_CONTAINER = os.environ.get('IN_DOCKER_CONTAINER', 'false').lower() == 'true'

mqtt_client = mqtt.Client(protocol=mqtt.MQTTv311)

EXHIBITS = [
    {"keyword": "da vinci", "location": "Mona Lisa"},
    {"keyword": "van gogh", "location": "Sunflowers (Van Gogh)"},
    {"keyword": "starry", "location": "Starry Night"},
    {"keyword": "liberty", "location": "Liberty Leading the People"},
    {"keyword": "egypt", "location": "Stylized Egyptian Sculpture"},
    {"keyword": "toy", "location": "Toy Dog"},
    # Keeping some of the original exhibit options as alternatives
]

current_location = None
upcoming_locations = []
arrived_flag = False

def speak(text):
    print("Bot:", text)
    if not IN_CONTAINER:
        # Use audio output only when not in container
        try:
            tts = gTTS(text=text, lang='en')
            tts.save("output.mp3")
            subprocess.run([
                "ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet",
                "-af", "atempo=1.3", "output.mp3"
            ], check=True)
        except Exception as e:
            print(f"Audio error (continuing with text only): {e}")

def on_arrived(client, userdata, message):
    global current_location, upcoming_locations, arrived_flag
    arrived_flag = True
    print(f"\nArrived at: {current_location}")
    if upcoming_locations:
        print(f"Next: {upcoming_locations[0]}")
    handle_conversation_after_arrival()

# Setup MQTT connection
def setup_mqtt():
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.subscribe(TOPIC_ARRIVED)
        mqtt_client.message_callback_add(TOPIC_ARRIVED, on_arrived)
        mqtt_client.loop_start()
        print("MQTT client connected to broker")
    except Exception as e:
        print(f"MQTT connection error: {e}")
        if IN_CONTAINER:
            print("If running in Docker, make sure MQTT broker is accessible")
            time.sleep(5)  # Give time for broker to potentially start
            try:
                mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
                mqtt_client.subscribe(TOPIC_ARRIVED)
                mqtt_client.message_callback_add(TOPIC_ARRIVED, on_arrived)
                mqtt_client.loop_start()
                print("MQTT client connected to broker on retry")
            except Exception as retry_e:
                print(f"MQTT connection retry failed: {retry_e}")

def listen_to_user():
    if IN_CONTAINER:
        # Use text input when in Docker container
        print("Enter your request (Docker mode):")
        return input("> ")
    else:
        # Use voice input normally
        recognizer = sr.Recognizer()
        print("Press [Enter] to start speaking")
        input()
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.4)
            print("Listening...")
            try:
                audio = recognizer.listen(source, timeout=6, phrase_time_limit=20)
                text = recognizer.recognize_google(audio)
                print("You said:", text)

                if text.strip().lower() == "testing cancel":
                    os._exit(0)

                return text
            except Exception as e:
                print("Error:", e)
                return None

def classify_user_preference(user_text):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": (
                "Classify the user's intent into one of these categories:\n"
                "- specific: they name an artist or exhibit\n"
                "- genre: they mention a theme like art, science, tech, history\n"
                "- unsure: they express indecision or ask to be surprised\n"
                "Reply ONLY with: specific, genre, or unsure"
            )},
            {"role": "user", "content": user_text}
        ]
    )
    return response.choices[0].message.content.strip().lower()

def choose_exhibit_locations(user_text):
    exhibit_list = ", ".join([f"{e['keyword']} ({e['location']})" for e in EXHIBITS])
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": (
                f"You are a helpful assistant. Based on the user's interests, pick up to 3 relevant exhibits from this list: {exhibit_list}.\n"
                "Return ONLY a comma-separated list of exhibit locations that best match the user's interests. If none match, return 'none'."
            )},
            {"role": "user", "content": user_text}
        ]
    )
    reply = response.choices[0].message.content.strip()
    if reply.lower() == "none":
        return []
    return [loc.strip() for loc in reply.split(",") if loc.strip()]

def send_movement_command(location):
    global arrived_flag
    print(f"Sending location to movement channel: {location}")
    mqtt_client.publish(TOPIC_MOVEMENT, location)
    # Reset the arrived flag when sending a new movement command
    arrived_flag = False

def handle_conversation_after_arrival():
    global current_location
    summary = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"You are a museum guide. Provide a warm, engaging 2-3 sentence summary about the exhibit called '{current_location}'."}
        ]
    ).choices[0].message.content.strip()
    speak(summary)
    speak(f"Would you like to hear more or ask a question about the {current_location}?")
    followup = listen_to_user()
    if followup:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"You are at the {current_location}. Describe it or answer questions about the exhibit."},
                {"role": "user", "content": followup}
            ]
        ).choices[0].message.content.strip()
        speak(response)

def wait_for_arrival():
    global arrived_flag
    print("Waiting for arrival confirmation...")
    timeout = 30  # 30 seconds timeout
    start_time = time.time()
    
    while not arrived_flag:
        time.sleep(0.5)
        if time.time() - start_time > timeout:
            print("Timeout waiting for arrival confirmation")
            return False
    
    return True

def tour_loop():
    global current_location, upcoming_locations, arrived_flag
    while True:
        # Wait for arrival confirmation from the navigation system
        if not wait_for_arrival():
            speak("I'm having trouble confirming our arrival at the exhibit. Let me try again.")
            send_movement_command(current_location)
            if not wait_for_arrival():
                speak("I'm sorry, but there seems to be a problem with the navigation system.")
                break
        
        if not upcoming_locations:
            speak("We've now visited all the planned exhibits. Are there any more exhibits you'd like to visit, or should we conclude the tour for today?")
            final_reply = listen_to_user()
            if final_reply:
                confirm_end = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Decide if the user is saying they want to end the tour. Reply ONLY with 'yes' to end, or 'no' to continue."},
                        {"role": "user", "content": final_reply}
                    ]
                ).choices[0].message.content.strip().lower()
                if confirm_end == "yes":
                    speak("Thanks for visiting! I hope you enjoy the rest of your day at the museum.")
                    break
                else:
                    speak("No problem! What kind of exhibit would you like to visit next?")
                    next_request = listen_to_user()
                    new_locations = choose_exhibit_locations(next_request)
                    if not new_locations:
                        new_locations = random.sample([e["location"] for e in EXHIBITS], 1)
                        speak("I couldn't find a perfect match, but let's check this one out!")
                    current_location = new_locations[0]
                    send_movement_command(current_location)
                    continue
            else:
                speak("Thanks for visiting! I hope you enjoy the rest of your day at the museum.")
                break

        speak("Would you like to continue to the next exhibit?")
        reply = listen_to_user()
        if not reply:
            speak("I didn't catch that. Would you like to continue to the next exhibit?")
            reply = listen_to_user()
            if not reply:
                speak("Still didn't catch a response, so I'll end the tour here. Hope you enjoyed it!")
                break
        if reply:
            confirm = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Decide if the user is saying yes to continue. Reply ONLY with 'yes' or 'no'."},
                    {"role": "user", "content": reply}
                ]
            ).choices[0].message.content.strip().lower()
            if confirm == "yes":
                if upcoming_locations:
                    current_location = upcoming_locations.pop(0)
                    speak(f"Alright, now heading to the {current_location}.")
                    send_movement_command(current_location)
                else:
                    speak("Looks like we've reached the end of our planned exhibits. Hope you enjoyed the tour!")
                    break
            else:
                speak("Ending the tour. Hope you enjoyed it!")
                break
        else:
            speak("Ending the tour. Hope you enjoyed it!")
            break

def main():
    # Setup MQTT connection
    setup_mqtt()
    
    global current_location, upcoming_locations
    
    speak("Hi! Welcome to the museum. What kind of exhibits are you interested in seeing today?")
    user_input = listen_to_user()
    preference = classify_user_preference(user_input or "unsure")

    if preference == "specific":
        locations = choose_exhibit_locations(user_input)
        if not locations:
            speak("Sorry, we don't have any exhibits that match your interests.")
            locations = random.sample([e["location"] for e in EXHIBITS], 3)
            speak("Would you like to visit some random exhibits instead?")
            confirm = listen_to_user()
            if confirm and "yes" in confirm.lower():
                speak(f"Great! Today we'll visit {', '.join(locations)}.")
            else:
                speak("No worries, feel free to ask me again anytime!")
                return
    elif preference == "genre":
        locations = choose_exhibit_locations(user_input)
        if not locations:
            locations = random.sample([e["location"] for e in EXHIBITS], 3)
            speak(f"Couldn't find a perfect match. How about these: {', '.join(locations)}?")
    else:
        locations = random.sample([e["location"] for e in EXHIBITS], 3)
        speak(f"I'll surprise you! Let's visit {', '.join(locations)}.")

    if len(locations) < 3:
        extras = [e["location"] for e in EXHIBITS if e["location"] not in locations]
        if extras:
            locations += random.sample(extras, min(3 - len(locations), len(extras)))

    if len(locations) >= 3:
        speak(f"Great! Here's the plan for today: we'll start at the {locations[0]}, then head to the {locations[1]}, and finish at the {locations[2]}.")
        speak("Are you happy with this plan or would you like to visit different exhibits?")
        alt_reply = listen_to_user()
        if alt_reply and any(word in alt_reply.lower() for word in ["change", "different", "another", "other"]):
            locations = choose_exhibit_locations(alt_reply)
            if not locations:
                locations = random.sample([e["location"] for e in EXHIBITS], 3)
            speak(f"Thanks! Here's your new plan: {', '.join(locations)}.")
    elif len(locations) == 2:
        speak(f"Great! Here's the plan for today: we'll visit the {locations[0]} and then the {locations[1]}. Let's get started!")
    elif len(locations) == 1:
        speak(f"Great! We'll start with the {locations[0]}. Let's begin!")

    upcoming_locations = locations.copy()
    current_location = upcoming_locations.pop(0)
    send_movement_command(current_location)
    tour_loop()

if __name__ == "__main__":
    main()
