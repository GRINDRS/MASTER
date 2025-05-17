#!/bin/bash

# Check if Mosquitto MQTT broker is installed
if ! command -v mosquitto &> /dev/null; then
    echo "Mosquitto MQTT broker not found. Installing..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew install mosquitto
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        sudo apt-get update
        sudo apt-get install -y mosquitto mosquitto-clients
    else
        echo "Unsupported OS. Please install Mosquitto manually."
        exit 1
    fi
fi

# Start Mosquitto MQTT broker in the background
echo "Starting Mosquitto MQTT broker..."
mosquitto -d

# Sleep for a moment to ensure broker is running
sleep 2

# Start the main system in the background
echo "Starting main navigation system..."
python3 main.py &
MAIN_PID=$!

# Start the voicebot in the background
echo "Starting voice bot system..."
python3 nlp_voice_bot/voicebot.py &
VOICE_PID=$!

echo "Museum system started successfully!"
echo "Press Ctrl+C to stop the script"

# Keep script running to allow orderly shutdown
trap "echo 'Shutting down...'; kill $MAIN_PID; kill $VOICE_PID; pkill -f mosquitto; exit 0" SIGINT
while true; do
    # Check if either process has died
    if ! ps -p $MAIN_PID > /dev/null; then
        echo "Main navigation system has stopped. Restarting..."
        python3 main.py &
        MAIN_PID=$!
    fi
    
    if ! ps -p $VOICE_PID > /dev/null; then
        echo "Voice bot system has stopped. Restarting..."
        python3 nlp_voice_bot/voicebot.py &
        VOICE_PID=$!
    fi
    
    sleep 2
done 
