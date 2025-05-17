import paho.mqtt.client as mqtt
import speech_recognition as sr
import os
import time
import random
import subprocess
from gtts import gTTS
from openai import OpenAI
from dotenv import load_dotenv
import threading

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

print("==========================================")
print("Voice Bot Starting...")
print("==========================================")

# Configure MQTT connection
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
TOPIC_MOVEMENT = "movement"
TOPIC_ARRIVED = "arrived"

# Global state
mqtt_connected = False
mqtt_client = None
current_location = None
upcoming_locations = []
waiting_for_arrival = False

EXHIBITS = [
    {"keyword": "scream",       "location": "The Scream by Edvard Munch"},
    {"keyword": "starry night", "location": "Starry Night by Vincent van Gogh"},
    {"keyword": "sunflower",    "location": "Sunflowers by Vincent van Gogh"},
    {"keyword": "liberty",      "location": "Liberty Leading the People by Eugène Delacroix"},
    {"keyword": "mona lisa",    "location": "Mona Lisa by Leonardo da Vinci"},
    {"keyword": "egyptian",     "location": "Ancient Egyptian Statue"},
    {"keyword": "plushy dog",   "location": "Plushy Dog Sculpture"},
]

def speak(text):
    print("Bot:", text)
    try:
        tts = gTTS(text=text, lang='en')
        tts.save("output.mp3")
        subprocess.run([
            "ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet",
            "-af", "atempo=1.3", "output.mp3"
        ], check=True)
    except Exception as e:
        print(f"Audio error (continuing with text only): {e}")

def listen_to_user():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.4)
        print("Listening ...")
        try:
            audio = recognizer.listen(source, timeout=6, phrase_time_limit=20)
            text = recognizer.recognize_google(audio)
            print("You said:", text)
            return text
        except Exception as e:
            print("Error:", e)
            return None

YES_WORDS  = {"yes", "sure", "okay", "sounds good", "yep", "yeah", "alright", "why not"}
NO_WORDS   = {"no", "nope", "another", "different", "change", "don't"}
MOVE_WORDS = {
    "move on", "next", "continue", "let's go", "go on",
    "no questions", "no question"     
}
END_WORDS  = {"done", "stop", "that's all", "end", "quit", "exit"}  

def _contains(text: str, word_set: set[str]) -> bool:
    t = text.lower()
    return any(w in t for w in word_set)

def wants_yes(text: str | None) -> bool:
    return bool(text) and _contains(text, YES_WORDS)

def wants_no(text: str | None) -> bool:
    return bool(text) and _contains(text, NO_WORDS)

def wants_move_on(text: str | None) -> bool:
    return bool(text) and (_contains(text, MOVE_WORDS) or wants_yes(text))

def wants_to_end(text: str | None) -> bool:
    return bool(text) and _contains(text, END_WORDS)

# MQTT callback handlers
def on_connect(client, userdata, flags, rc):
    global mqtt_connected
    print(f"MQTT: Connected with result code {rc}")
    if rc == 0:
        mqtt_connected = True
        # Make sure we're subscribed to the arrived topic
        result = client.subscribe(TOPIC_ARRIVED)
        print(f"MQTT: Subscribed to {TOPIC_ARRIVED}, result: {result}")
        
        # Add a specific message callback for the arrived topic
        client.message_callback_add(TOPIC_ARRIVED, on_arrived_message)
        print("MQTT: Added specific callback for arrival messages")
    else:
        print(f"MQTT: Failed to connect, result code: {rc}")

def on_arrived_message(client, userdata, msg):
    """Specific callback for arrival messages"""
    global waiting_for_arrival
    try:
        print(f"MQTT: ARRIVAL MESSAGE RECEIVED!")
        message_content = msg.payload.decode() if msg.payload else ""
        print(f"MQTT: Arrival message: '{message_content}'")
        print(f"MQTT: Current location is: {current_location}")
        waiting_for_arrival = False
    except Exception as e:
        print(f"MQTT: Error in arrival callback: {e}")
        waiting_for_arrival = False

def on_message(client, userdata, msg):
    """General message handler for any other topics"""
    print(f"MQTT: General message received on topic: {msg.topic}")
    try:
        message_content = msg.payload.decode() if msg.payload else ""
        print(f"MQTT: Message content: '{message_content}'")
        
        # As a fallback, also check for arrival messages here
        if msg.topic == TOPIC_ARRIVED:
            print(f"MQTT: Arrival detected in general handler!")
            waiting_for_arrival = False
    except Exception as e:
        print(f"MQTT: Error in general message handler: {e}")

def simulate_arrival():
    """Simulate arrival after a delay (used if MQTT fails)"""
    global waiting_for_arrival
    time.sleep(5)  # Simulate travel time
    print("SIMULATED: Navigation completed")
    waiting_for_arrival = False

def setup_mqtt():
    """Set up MQTT with error handling"""
    global mqtt_client, mqtt_connected
    
    try:
        print("MQTT: Setting up client...")
        mqtt_client = mqtt.Client(protocol=mqtt.MQTTv311)
        mqtt_client.on_connect = on_connect
        mqtt_client.on_message = on_message
        
        print(f"MQTT: Connecting to broker at {MQTT_BROKER}:{MQTT_PORT}...")
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
        
        # Wait briefly to see if connection succeeds
        time.sleep(1)
        return mqtt_connected
    except Exception as e:
        print(f"MQTT: Setup failed with error: {e}")
        return False

def send_movement_command(location: str) -> None:
    global waiting_for_arrival, mqtt_client, mqtt_connected
    
    # Simplify location string for navigation - use only the first part before "by" if it exists
    nav_location = location.split(" by ")[0].lower()
    print(f"Navigation: Requesting movement to '{nav_location}'")
    waiting_for_arrival = True
    
    if mqtt_connected and mqtt_client:
        try:
            print(f"MQTT: Publishing to {TOPIC_MOVEMENT}: {nav_location}")
            mqtt_client.publish(TOPIC_MOVEMENT, nav_location)
            print("MQTT: Message sent, waiting for arrival...")
            # No simulation fallback - wait for real navigation
        except Exception as e:
            print(f"MQTT: Publish failed: {e}")
            print("MQTT: Falling back to simulation ONLY because publishing failed...")
            threading.Thread(target=simulate_arrival).start()
    else:
        print("Navigation: MQTT not connected, using simulation")
        threading.Thread(target=simulate_arrival).start()

def wait_for_arrival():
    global waiting_for_arrival
    
    print("Navigation: Waiting for arrival...")
    speak("We're on our way to the exhibit. Please wait while we navigate there.")
    
    # Print initial waiting status
    print(f"Navigation: waiting_for_arrival state: {waiting_for_arrival}")
    
    # Wait indefinitely for arrival notification
    while waiting_for_arrival:
        time.sleep(0.5)
    
    print(f"Navigation: Arrived at {current_location}")

def exhibit_summary(name: str) -> str:
    return client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system",
                   "content": f"You are a museum guide. Provide a warm, engaging 2-3 sentence summary about the exhibit '{name}'."}]
    ).choices[0].message.content.strip()

def answer_question(exhibit: str, question: str) -> str:
    return client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"You are a museum guide at '{exhibit}'. Answer visitor questions clearly but concisely."},
            {"role": "user", "content": question}
        ]
    ).choices[0].message.content.strip()

def propose_exhibit(unvisited: list[str]) -> str | None:
    if not unvisited:
        return None
    while unvisited:
        choice = random.choice(unvisited)
        speak(f"How about we head to the {choice}? How does that sound?")
        reply = listen_to_user()

        if wants_to_end(reply):
            return None
        if wants_yes(reply):
            return choice        
        unvisited.remove(choice)
        if unvisited:
            speak("No problem, let me suggest another option.")
    return None

def end_tour() -> None:
    speak("Thanks for visiting! I hope you enjoy the rest of your day at the museum.")
    send_movement_command("initial")
    if mqtt_connected and mqtt_client:
        mqtt_client.disconnect()
    raise SystemExit

def choose_locs(text: str) -> list[str]:
    exhibit_list = ", ".join(f"{e['keyword']} ({e['location']})" for e in EXHIBITS)
    reply = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system",
             "content": f"Choose up to 3 exhibit LOCATIONS matching the user's interest from: {exhibit_list}. Return a comma-separated list or 'none'."},
            {"role": "user", "content": text}
        ]
    ).choices[0].message.content.strip()
    return [] if reply.lower() == "none" else [loc.strip() for loc in reply.split(",")]

# MAIN PROGRAM STARTS HERE
def main():
    global current_location, mqtt_connected
    
    # Try to set up MQTT, but continue even if it fails
    mqtt_connected = setup_mqtt()
    print(f"MQTT connected: {mqtt_connected}")
    
    # Start interaction
    visited = set()
    speak("Hi! Welcome to the museum. What kind of exhibits are you interested in seeing today?")
    first = listen_to_user()

    if not first or _contains(first, {"don't know", "not sure", "idk"}):
        while True:
            unvisited = [e["location"] for e in EXHIBITS if e["location"] not in visited]
            target = propose_exhibit(unvisited)
            if target is None:
                end_tour()

            current_location = target
            visited.add(current_location)
            send_movement_command(current_location)
            wait_for_arrival()
            speak(exhibit_summary(current_location))

            while True:
                speak("Do you have any questions about this exhibit, or would you like to move on?")
                resp = listen_to_user()

                if wants_to_end(resp):
                    end_tour()
                if wants_move_on(resp):
                    break
                if not resp:
                    speak("I didn't catch that, so let's move on.")
                    break
                speak(answer_question(current_location, resp))
    else:
        upcoming = choose_locs(first)
        if not upcoming:
            upcoming = [random.choice([e["location"] for e in EXHIBITS])]

        while True:
            current_location = upcoming.pop(0)
            visited.add(current_location)
            send_movement_command(current_location)
            wait_for_arrival()
            speak(exhibit_summary(current_location))

            while True:
                speak("Do you have any questions about this exhibit, or would you like to move on?")
                r = listen_to_user()

                if wants_to_end(r):
                    end_tour()
                if wants_move_on(r):
                    break
                if not r:
                    speak("I didn't catch that, so let's move on.")
                    break
                speak(answer_question(current_location, r))

            if not upcoming:
                speak("Would you like to visit another exhibit?")
                nxt = listen_to_user()

                if wants_to_end(nxt) or wants_no(nxt):  
                    end_tour()

                if not nxt or _contains(nxt, {"don't know", "not sure", "idk"}):
                    pick = propose_exhibit([e["location"] for e in EXHIBITS if e["location"] not in visited])
                    if pick is None:
                        end_tour()
                    upcoming.append(pick)
                else:
                    cand = [loc for loc in choose_locs(nxt) if loc not in visited]
                    upcoming.extend(cand or
                                   [random.choice([e["location"] for e in EXHIBITS if e["location"] not in visited])])

# Start the main program
if __name__ == "__main__":
    print("Starting voice bot system...")
    main()