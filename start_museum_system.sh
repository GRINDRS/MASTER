#!/bin/bash
#
# start_museum_system.sh
#
# This script initialises and supervises the full museum navigation system.
# It checks for the Mosquitto MQTT broker, installs it if missing (for macOS or Linux),
# starts the broker, and then launches three components in the background:
# - The main navigation backend
# - The voicebot assistant
# - The web interface
#
# If any process crashes, the script will restart it automatically.
# Use Ctrl+C to stop the system gracefully.
#
# Author: GRINDRS
# Date: 2025

# --------------------------------------------------
# Ensure Mosquitto MQTT Broker is Installed
# --------------------------------------------------

if ! command -v mosquitto &> /dev/null; then
    echo "Mosquitto MQTT broker not found. Installing..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # For macOS using Homebrew
        brew install mosquitto
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # For Debian/Ubuntu-based Linux systems
        sudo apt-get update
        sudo apt-get install -y mosquitto mosquitto-clients
    else
        echo "Unsupported OS. Please install Mosquitto manually."
        exit 1
    fi
fi

# --------------------------------------------------
# Start Mosquitto Broker
# --------------------------------------------------

echo "Starting Mosquitto MQTT broker..."
mosquitto -d

# Allow broker time to initialise
sleep 2

# --------------------------------------------------
# Launch Core Components in Background
# --------------------------------------------------

echo "Starting main navigation system..."
python3 navigation/navigation.py &
MAIN_PID=$!

echo "Starting voice bot system..."
python3 nlp_voice_bot/voicebot.py &
VOICE_PID=$!

echo "Starting web page..."
python3 web/app.py &
WEB_PID=$!

echo "Museum system started successfully!"
echo "Press Ctrl+C to stop the script"

# --------------------------------------------------
# Process Supervision Loop
# --------------------------------------------------

# Graceful shutdown handling
trap "echo 'Shutting down...'; kill $MAIN_PID; kill $VOICE_PID; kill $WEB_PID; pkill -f mosquitto; exit 0" SIGINT

# Monitor and restart any crashed processes
while true; do
    if ! ps -p $MAIN_PID > /dev/null; then
        echo "Main navigation system has stopped. Restarting..."
        python3 navigation/navigation.py &
        MAIN_PID=$!
    fi

    if ! ps -p $VOICE_PID > /dev/null; then
        echo "Voice bot system has stopped. Restarting..."
        python3 nlp_voice_bot/voicebot.py &
        VOICE_PID=$!
    fi

    if ! ps -p $WEB_PID > /dev/null; then
        echo "Web page has stopped. Restarting..."
        python3 web/app.py &
        WEB_PID=$!
    fi

    sleep 2
done
