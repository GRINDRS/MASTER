# Museum Robot Guidance & Experience Platform

This repository contains an **end-to-end system** that turns a mobile robot into an engaging museum guide.  
It combines Natural-Language interaction, autonomous navigation, computer-vision utilities, and a real-time web dashboard—all connected through MQTT.

---

## 1. High-Level Architecture
```
┌──────────────────────────┐           MQTT            ┌───────────────────────────┐
│  nlp_voice_bot/voicebot  │──movement─▶│ navigation/navigation.py │
│    (speech ↔︎ GPT-4)      │◀─arrived───│   (PLC / SLAM layer)    │
└─────────────┬────────────┘            └─────────┬─────────────────┘
              │                                     │ (optionally)
              │  JSON file (spoke.json)             │
              ▼                                     ▼
┌──────────────────────────┐           HTTP           ┌───────────────────────────┐
│    web/app.py (Flask)    │◀───────browser──────────│     Video Stream + UI      │
└──────────────────────────┘                          └───────────────────────────┘
```
* **Voice Bot** – Handles speech recognition, exhibit selection logic, Q&A (powered by OpenAI), and publishes navigation commands.
* **Navigation Layer** – Subscribes to movement commands, drives the robot (or a simulation) and publishes an `arrived` message when it reaches its goal.
* **Web Dashboard** – Displays the current conversation, exhibit itinerary, live webcam feed, and provides at-a-glance status for operators or visitors.
* **Shared JSON (`web/spoke.json`)** – A simple hand-off mechanism between the voice bot and the web UI; keeps the dashboard in sync without a full database.

---

## 2. Directory Overview
```
.
├── basic_embedded/                # Micro-controller prototypes (C / Arduino)
├── computer_vision_gpt_approach/  # Exploratory CV+GPT scripts
├── navigation/
│   └── navigation.py              # MQTT-driven movement simulation / hardware bridge
├── nlp_voice_bot/
│   ├── voicebot.py                # Main conversational agent
│   ├── test_mqtt.py               # Simple publisher for manual tests
│   └── README.md                  # Notes specific to the bot
├── web/
│   ├── app.py                     # Flask server
│   ├── templates/index.html       # Dashboard HTML (Jinja2)
│   └── spoke.json                 # Shared state (auto-generated)
├── start_museum_system.sh         # Convenience script to launch components
├── docker-compose.yml             # Multi-container deployment (MQTT + services)
├── Dockerfile                     # Base image for Python services
├── requirements.txt               # All Python dependencies
└── README.md                      # ← you are here
```

---

## 3. Component Details

### 3.1 `nlp_voice_bot/voicebot.py`
* **Speech I/O** – Uses `speech_recognition` + Google STT for input, `gTTS` + `ffplay` for output.
* **State Machines** – Supports two visit modes:
  * **Guided Tour** – A fixed three-piece curriculum (Mona Lisa → Starry Night → The Scream).
  * **Free Roam** – The visitor picks any exhibit, can say *next* or *stop* at any time.
* **OpenAI Integrations**  
  * `exhibit_summary()` – Condenses background into 2-3 sentences.  
  * `answer_question()` – On-the-fly Q&A about the current piece.
* **Error Handling** –     
  * Time-outs for movement acknowledgement.  
  * "Sorry, I didn't catch that" reprompts on STT failures or unclear intent.
* **Shared Dashboard State** – Updates `web/spoke.json` whenever the user or bot speaks, and when the itinerary changes.

### 3.2 `navigation/navigation.py`
* **MQTT Topics** – Listens on `movement`; publishes on `arrived`.
* **Simulation vs Hardware** – Default behaviour sleeps ~5 s to mimic travel.  Swap the placeholder with actual motor/SLAM calls.

### 3.3 `web/app.py`
* **Flask Routes**  
  `/` – Renders the dashboard with current JSON.  
  `/video` – MPEG stream from an attached webcam.  
  `/frame.jpg` – Snapshot endpoint.
* **Front-End** – The template shows:
  * Latest user utterance
  * Bot response
  * Current exhibit
  * Visited & upcoming lists
  * Live video panel (uses HTML `<img>` stream)

### 3.4 Shell & Orchestration
* **`start_museum_system.sh`** – Convenience script that:
  1. Starts Mosquitto (if not already running)
  2. Launches navigation, voice bot and web server in dedicated terminals.
* **Docker Compose** – Spins up: Mosquitto, navigation, voice bot, and web dashboard in isolated containers.

---

## 4. Getting Started (Local Machine)
```bash
# 1.  Python env + system libs
brew install ffmpeg mosquitto
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2.  Secrets
cp .env.example .env         # then add your OPENAI_API_KEY

# 3.  Launch everything
./start_museum_system.sh     # or run each component manually

# 4.  Open the dashboard
open http://localhost:5000
```

---

## 5. Environment Variables
| Variable            | Purpose                       |
|---------------------|-------------------------------|
| `OPENAI_API_KEY`    | Access token for GPT requests |
| `MQTT_BROKER`       | Hostname (default `localhost`) |
| `MQTT_PORT`         | Port (default `1883`)         |

---

## 6. Extending Exhibits
Edit the list in **`voicebot.py → EXHIBITS`**:
```python
EXHIBITS = [
    {"keyword": "lilies",   "location": "Water Lilies by Claude Monet"},
    # add more …
]
```
Each entry needs:
* **`keyword`** – what the visitor might say.
* **`location`** – the friendly display & navigation target.

---

## 7. FAQ / Troubleshooting
* **The bot hangs on navigation** – Check that `navigation/navigation.py` publishes `arrived` or increase the time-out in `wait_for_arrival()`.
* **Speech recognition errors** – Ensure your microphone is correctly configured; the bot already reprompts on failure.
* **OpenAI 400 error** – Make sure text sent to GPT is non-empty (fixed in latest patch).

---

## 8. Licence
No licensing required except for the openAI key.

---

## 9. Development Workflow

Below is the **recommended process** for contributing new features or debugging existing ones.

1. **Fork & Clone** the repository, then create a feature branch.
2. **Spin-up required services locally** using `docker-compose up mqtt` to ensure a broker is running.
3. **Run unit tests** (where available) via `pytest -q`—see section 13 for how tests are structured.
4. **Start the live system** in *watch mode*:
   ```bash
   ./start_museum_system.sh dev   # spawns each component with live-reload
   ```
5. **Tail the logs** for each service (navigation, voicebot, web) in their respective terminals.
6. **Edit code**; changes to `voicebot.py`, templates, or `navigation.py` will automatically reload thanks to the built-in watchers.
7. **Commit & push** once the feature is verified; open a PR and link to any relevant issues.

---

## 10. Directory Deep Dive

| Path | Purpose |
|------|---------|
| `basic_embedded/` | Experiments for driving stepper motors with Arduino/C++; may inform future hardware integration. |
| `computer_vision_gpt_approach/` | Proof-of-concept scripts that describe a camera frame to GPT for object recognition; not used in production yet but demonstrates multi-modal potential. |
| `capture_analyse.py` | Quick utility to snap webcam frames and analyse facial sentiment—another CV exploration. |
| `navigation/` | All motion-related logic; right now a pure-Python simulator but intended to be swapped with ROS2 or PLC code. |
| `nlp_voice_bot/` | Speech, NLP, GPT calls, itinerary logic, and JSON syncing. |
| `web/` | Lightweight dashboard (Flask + Jinja2) that surfaces system state and video feed. |
| `docker-compose.yml` | Defines 4 services: `mqtt`, `voicebot`, `navigation`, and `dashboard`. |
| `start_museum_system.sh` | Bash script to orchestrate local development (with automatic process restarts). |

---

## 11. MQTT Topic Specification

| Topic | Direction | Payload | Description |
|-------|-----------|---------|-------------|
| `movement` | VoiceBot → Navigation | *string* (exhibit name) | Tells the robot to navigate to a particular exhibit or waypoint such as `"Mona Lisa by Leonardo da Vinci"`. |
| `arrived` | Navigation → VoiceBot | *string* (echo of location) | Signals that navigation is complete—VoiceBot unblocks its flow once this is received. |

QoS 0 is sufficient for a small venue; consider QoS 1 if the network is spotty.

---

## 12. Speech & LLM Configuration

| Component | Lib | Notes |
|-----------|-----|-------|
| **STT** | `speech_recognition` (Google Web Speech) | You can swap in Offline Vosk by setting `STT_ENGINE=vosk` in `.env`. |
| **TTS** | `gTTS` + `ffplay` | Uses FFmpeg's playback to allow variable speed via `-af atempo=1.3`. |
| **LLM** | OpenAI Chat Completions | Model selectable via `OPENAI_MODEL` (defaults to `gpt-3.5-turbo`). |

If you need full offline mode, replace TTS with `espeak` and LLM calls with a local model such as `llama.cpp`—the interfaces are isolated in helper functions to ease substitution.

---

## 13. Testing Strategy

* **Unit Tests (`tests/`)** – Cover helper functions like `choose_locs`, intent detection, and navigation fallbacks.
* **Integration Scenario** – A scripted conversation fed through a mocked STT layer ensures the full stack responds as intended; see `tests/test_convo.py`.
* **Hardware-in-the-loop** – When a real robot is available, the navigation simulator is disabled via `NAV_SIM=false` and tests verify physical arrival sensors.

To run all tests:
```bash
pytest -q
```

---

## 14. Deployment Targets

| Platform | Tested | Notes |
|----------|--------|-------|
| **Docker on x86-64** | ✅ | Fastest way to replicate full environment. |
| **Raspberry Pi 4** | ✅ | Requires `sudo apt install ffmpeg mosquitto` and enabling pi camera. |
| **Jetson Nano** | ⚠️ | Builds fine but GPU CV demo scripts require patched OpenCV. |
| **ROS 2 Foxy** | 🚧 | Planned: wrap navigation publisher/subscriber as ROS nodes. |

---

## 15. Contribution Guidelines

* Follow **PEP-8** and document public functions with *Google-style* docstrings.
* Run `ruff --fix .` before committing to auto-format and lint.
* Each new exhibit or feature should be accompanied by at least one test.
* File an issue first before embarking on large architectural changes.

---

## 16. Roadmap / Future Work

1. **Dynamic map** – Integrate SLAM feedback into the dashboard to show real-time robot position.
2. **Multi-language support** – Parameterise TTS/STT to switch languages on the fly.
3. **Crowd analytics** – Use the computer-vision module to estimate foot-traffic and adjust tour suggestions.
4. **Ticketing system integration** – Personalise tours based on visitor profile read from QR code.
5. **Accessibility mode** – Provide on-screen captions and sign-language avatar.

---
