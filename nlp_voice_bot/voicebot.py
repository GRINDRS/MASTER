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

mqtt_client = mqtt.Client(protocol=mqtt.MQTTv311)

EXHIBITS = [
    {"keyword": "da vinci", "location": "Renaissance Art Hall"},
    {"keyword": "van gogh", "location": "Impressionist Gallery"},
    {"keyword": "dinosaur", "location": "Natural History Wing"},
    {"keyword": "space", "location": "Cosmos Exploration Room"},
    {"keyword": "egypt", "location": "Ancient Egypt Exhibit"},
    {"keyword": "robot", "location": "Technology and Innovation Lab"},
    {"keyword": "marine", "location": "Ocean Wonders Zone"},
    {"keyword": "volcano", "location": "Earth Science Theatre"},
    {"keyword": "medieval", "location": "Medieval Europe Hall"},
    {"keyword": "fashion", "location": "Historic Fashion Gallery"},
    {"keyword": "ai", "location": "Artificial Intelligence Hub"},
    {"keyword": "greek", "location": "Ancient Greece Exhibit"},
    {"keyword": "china", "location": "Dynasties of China Pavilion"},
    {"keyword": "australia", "location": "First Nations Cultural Space"},
    {"keyword": "insect", "location": "Entomology Showcase"},
    {"keyword": "music", "location": "Sounds Through the Ages Room"},
    {"keyword": "photography", "location": "Digital Media and Photography Wing"},
    {"keyword": "cars", "location": "Automotive Innovations Hall"},
    {"keyword": "planes", "location": "Aviation Heritage Gallery"},
    {"keyword": "medicine", "location": "History of Medicine Chamber"},
]

current_location = None
upcoming_locations = []

def speak(text):
    print("Bot:", text)
    tts = gTTS(text=text, lang='en')
    tts.save("output.mp3")
    subprocess.run([
        "ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet",
        "-af", "atempo=1.3", "output.mp3"
    ], check=True)

def on_arrived(client, userdata, message):
    global current_location, upcoming_locations
    print(f"\nArrived at: {current_location}")
    if upcoming_locations:
        print(f"Next: {upcoming_locations[0]}")
    handle_conversation_after_arrival()

mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.subscribe(TOPIC_ARRIVED)
mqtt_client.on_message = on_arrived
mqtt_client.loop_start()

def listen_to_user():
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
    print(f"Sending location to movement channel: {location}")
    mqtt_client.publish(TOPIC_MOVEMENT, location)

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

def simulate_arrival():
    time.sleep(2)
    on_arrived(None, None, type("MQTTMessage", (object,), {"topic": TOPIC_ARRIVED, "payload": b""}))

def tour_loop():
    global current_location, upcoming_locations
    while True:
        simulate_arrival()
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
            send_movement_command(current_location)
        else:
            speak("Ending the tour. Hope you enjoyed it!")
            break

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
            exit()
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
    locations += random.sample(extras, 3 - len(locations))

if len(locations) >= 3:
    speak(f"Great! Here's the plan for today: we'll start at the {locations[0]}, then head to the {locations[1]}, and finish at the {locations[2]}.")
    speak("Are you happy with this plan or would you like to visit different exhibits? Here are a few options: " + ", ".join(random.sample([e['location'] for e in EXHIBITS if e['location'] not in locations], 3)) + ".")
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
