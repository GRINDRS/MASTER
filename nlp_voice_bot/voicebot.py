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
import json

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

print("==========================================")
print("Voice Bot Starting...")
print("==========================================")

# --------------------------------------------------
# MQTT CONFIG
# --------------------------------------------------
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
TOPIC_MOVEMENT = "movement"
TOPIC_ARRIVED  = "arrived"

# --------------------------------------------------
# GLOBAL STATE
# --------------------------------------------------
mqtt_connected    = False
mqtt_client: mqtt.Client | None = None
current_location  = None
waiting_for_arrival = False

# --------------------------------------------------
# EXHIBIT DEFINITIONS
# --------------------------------------------------
EXHIBITS = [
    {"keyword": "scream",       "location": "The Scream by Edvard Munch"},
    {"keyword": "starry night", "location": "Starry Night by Vincent van Gogh"},
    {"keyword": "sunflower",    "location": "Sunflowers by Vincent van Gogh"},
    {"keyword": "liberty",      "location": "Liberty Leading the People by Eugène Delacroix"},
    {"keyword": "mona lisa",    "location": "Mona Lisa by Leonardo da Vinci"},
    {"keyword": "egyptian",     "location": "Ancient Egyptian Statue"},
    {"keyword": "plushy dog",   "location": "Plushy Dog Sculpture"},
]

GUIDED_TOUR = [
    "Mona Lisa by Leonardo da Vinci",
    "Starry Night by Vincent van Gogh",
    "The Scream by Edvard Munch",
]

# --------------------------------------------------
# WEB/NLP SHARED DATA (spoke.json)
# --------------------------------------------------

SPOKE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "web", "spoke.json"))


def _load_spoke() -> dict:
    if os.path.exists(SPOKE_PATH):
        try:
            with open(SPOKE_PATH, "r") as f:
                return json.load(f)
        except Exception:
            pass  # fall through to empty
    return {}


def _save_spoke(data: dict):
    try:
        with open(SPOKE_PATH, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Could not write spoke.json → {e}")


# Keep track of visited & upcoming exhibits globally so they can be surfaced to the UI
visited_global: list[str] = []
upcoming_global: list[str] = []


def update_spoke(*, user: str | None = None, response: str | None = None):
    """Update the shared JSON file that the web layer reads."""

    data = _load_spoke()

    if user is not None:
        data["user"] = user
    if response is not None:
        data["response"] = response

    if current_location:
        data["current"] = current_location

    if visited_global:
        data["been_to"] = visited_global.copy()
    if upcoming_global:
        data["going_to"] = upcoming_global.copy()

    _save_spoke(data)

# --------------------------------------------------
# I/O HELPERS
# --------------------------------------------------

def speak(text: str):
    """TTS output + console log."""
    print("Bot:", text)
    # Update shared JSON with bot response
    update_spoke(response=text)
    try:
        tts = gTTS(text=text, lang="en")
        tts.save("output.mp3")
        subprocess.run([
            "ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet",
            "-af", "atempo=1.3", "output.mp3"
        ], check=True)
    except Exception as e:
        print(f"Audio error (continuing with text only): {e}")


def listen_to_user() -> str | None:
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.4)
        print("Listening …")
        try:
            audio = recognizer.listen(source, timeout=6, phrase_time_limit=20)
            text = recognizer.recognize_google(audio)
            print("You said:", text)
            update_spoke(user=text)
            return text
        except Exception as e:
            print("Error:", e)
            speak("Sorry, I didn't understand that.")
            return None

# --------------------------------------------------
# KEYWORD SETS & INTENT DETECTION
# --------------------------------------------------
YES_WORDS   = {"yes", "sure", "okay", "sounds good", "yep", "yeah", "alright", "why not", "continue", "next"}
NO_WORDS    = {"no", "nope", "another", "different", "change", "don't"}
MOVE_WORDS  = {"move on", "next", "continue", "let's go", "go on", "carry on"}
END_WORDS   = {"done", "stop", "that's all", "end", "quit", "exit", "finished"}
GUIDED_WORDS= {"guided", "guide", "tour"}
FREE_WORDS  = {"free", "roam", "myself", "alone"}


def _contains(text: str, words: set[str]) -> bool:
    t = text.lower() if text else ""
    return any(w in t for w in words)

def wants_yes(text: str | None) -> bool:      return _contains(text, YES_WORDS)

def wants_no(text: str | None) -> bool:       return _contains(text, NO_WORDS)

def wants_move_on(text: str | None) -> bool:  return _contains(text, MOVE_WORDS) or wants_yes(text)

def wants_to_end(text: str | None) -> bool:   return _contains(text, END_WORDS)

def wants_guided(text: str | None) -> bool:   return _contains(text, GUIDED_WORDS)

def wants_free(text: str | None) -> bool:     return _contains(text, FREE_WORDS)

# --------------------------------------------------
# MQTT CALLBACKS
# --------------------------------------------------

def on_connect(client, userdata, flags, rc):
    global mqtt_connected
    print(f"MQTT: Connected with result code {rc}")
    if rc == 0:
        mqtt_connected = True
        client.subscribe(TOPIC_ARRIVED)
        client.message_callback_add(TOPIC_ARRIVED, on_arrived_message)
    else:
        print("MQTT: Connection failed")


def on_arrived_message(client, userdata, msg):
    global waiting_for_arrival
    print("MQTT: ARRIVAL MESSAGE RECEIVED → Arrived!")
    waiting_for_arrival = False


def on_message(client, userdata, msg):
    # Fallback handler
    if msg.topic == TOPIC_ARRIVED:
        on_arrived_message(client, userdata, msg)


def simulate_arrival():
    global waiting_for_arrival
    time.sleep(5)
    print("SIMULATED: Navigation completed")
    waiting_for_arrival = False


def setup_mqtt() -> bool:
    global mqtt_client, mqtt_connected
    try:
        mqtt_client = mqtt.Client(protocol=mqtt.MQTTv311)
        mqtt_client.on_connect = on_connect
        mqtt_client.on_message = on_message
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
        time.sleep(1)
        return mqtt_connected
    except Exception as e:
        print(f"MQTT: Setup failed → {e}")
        return False

# --------------------------------------------------
# NAVIGATION HELPERS
# --------------------------------------------------

def to_location(name: str) -> str:
    return next((e["location"] for e in EXHIBITS if e["keyword"] == name.lower()), name)


def send_movement_command(location: str):
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


def wait_for_arrival():
    speak("We're on our way to the exhibit. Please wait while we navigate there.")
    while waiting_for_arrival:
        time.sleep(0.5)

# --------------------------------------------------
# OPENAI / LLM HELPERS
# --------------------------------------------------

def exhibit_summary(name: str) -> str:
    long_name = to_location(name)
    return client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": f"You are a museum guide. Provide a warm, engaging 2–3 sentence summary about the exhibit '{long_name}'."}]
    ).choices[0].message.content.strip()


def answer_question(exhibit: str, question: str) -> str:
    long_exhibit = to_location(exhibit)
    return client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"You are a museum guide at '{long_exhibit}'. Answer visitor questions clearly but concisely."},
            {"role": "user", "content": question}
        ]
    ).choices[0].message.content.strip()


def choose_locs(text: str) -> list[str]:
    if not text:
        return []

    lower = text.lower()
    matches = [e["location"] for e in EXHIBITS if e["keyword"] in lower]
    if matches:
        return matches[:3]
    exhibit_list = ", ".join(f"{e['keyword']} ({e['location']})" for e in EXHIBITS)
    reply = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"Choose up to 3 exhibit LOCATIONS matching the user's request from: {exhibit_list}. Return a comma‑separated list or 'none'."},
            {"role": "user", "content": text}
        ]
    ).choices[0].message.content.strip()
    if reply.lower() == "none":
        return []
    raw = [r.strip() for r in reply.split(",")]
    return [to_location(r) for r in raw]

# --------------------------------------------------
# FLOW HELPERS
# --------------------------------------------------

def end_tour():
    speak("Thanks for visiting! I hope you enjoy the rest of your day at the museum.")
    send_movement_command("initial")
    if mqtt_connected and mqtt_client:
        mqtt_client.disconnect()
    raise SystemExit


def navigate_to(location: str):
    global current_location
    current_location = location
    send_movement_command(location)
    wait_for_arrival()
    speak(exhibit_summary(location))


def q_and_a_loop(location: str):
    """Handle repeated Q&A for an exhibit until the visitor says to move on or end."""
    while True:
        speak("Do you have any questions about this exhibit? Say 'next' when you're ready to continue, or 'stop' to end the tour.")
        resp = listen_to_user()
        if wants_to_end(resp):
            end_tour()
        if wants_move_on(resp):
            return  # move on
        if not resp:
            speak("I didn't catch that, so let's continue.")
            return
        answer = answer_question(location, resp)
        speak(answer)

# --------------------------------------------------
# GUIDED VS FREE‑ROAM FLOWS
# --------------------------------------------------

def guided_tour_flow():
    global visited_global, upcoming_global
    visited_global = []
    upcoming_global = GUIDED_TOUR.copy()
    for idx, loc in enumerate(GUIDED_TOUR):
        current_remaining = GUIDED_TOUR[idx + 1:]
        upcoming_global = current_remaining.copy()
        update_spoke()

        navigate_to(loc)
        visited_global.append(loc)
        update_spoke()

        q_and_a_loop(loc)
    # finished tour
    end_tour()


def free_roam_flow():
    global visited_global, upcoming_global
    visited: set[str] = set()

    # Ask for first destination
    speak("Which exhibit would you like to visit first?")
    first = listen_to_user()
    if wants_to_end(first):
        end_tour()

    if not first or _contains(first, {"don't know", "not sure", "idk"}):
        # Visitor is unsure – default to the Mona Lisa and let them know
        speak("No worries – let's start with the Mona Lisa and see how we go from there.")
        dests = [GUIDED_TOUR[0]]  # default Mona Lisa
    else:
        dests = choose_locs(first) or [GUIDED_TOUR[0]]

    # Keep the upcoming list in sync
    upcoming_global = dests.copy()

    while True:
        # If there is no planned destination, prompt the visitor until we get one.
        if not dests:
            speak("Where would you like to go next? You can also say 'stop' to finish your tour.")
            nxt = listen_to_user()
            if wants_to_end(nxt):
                end_tour()
            if not nxt:
                speak("Sorry, I didn't quite catch that.")
                continue  # ask again

            dests.extend(choose_locs(nxt) or [random.choice([e['location'] for e in EXHIBITS if e['location'] not in visited])])
            upcoming_global = dests.copy()
            update_spoke()
            continue  # Loop will now navigate to the new destination

        location = dests.pop(0)
        if location in visited:
            if not dests:
                speak("You've already seen that one. Where would you like to go instead?")
                nxt = listen_to_user()
                if wants_to_end(nxt):
                    end_tour()
                dests.extend(choose_locs(nxt) or [random.choice([e['location'] for e in EXHIBITS if e['location'] not in visited])])
            continue

        navigate_to(location)
        visited.add(location)

        # Update global tracking lists and JSON after visiting
        visited_global = list(visited)
        upcoming_global = dests.copy()
        update_spoke()

        # In free-roam mode we skip the detailed Q&A prompt and ask directly for the next destination.
        nxt = listen_to_user()
        if wants_to_end(nxt):
            end_tour()

        if not nxt:
            speak("Sorry, I didn't quite catch that.")
            # The loop will re-prompt at the top if dests is empty.
            continue

        dests.extend(choose_locs(nxt) or [random.choice([e['location'] for e in EXHIBITS if e['location'] not in visited])])

        upcoming_global = dests.copy()
        update_spoke()

# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():
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
        # couldn't determine – default to asking again / guided as fallback
        speak("I didn't quite catch that. Let's do the guided tour to get started – you can always switch to free roam later.")
        guided_tour_flow()


if __name__ == "__main__":
    main()
