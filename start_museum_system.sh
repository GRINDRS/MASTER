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

# Start the main system in a new terminal
echo "Starting main navigation system..."
osascript -e 'tell app "Terminal" to do script "cd '$(pwd)' && python main.py"'

# Start the voicebot in a new terminal
echo "Starting voice bot system..."
osascript -e 'tell app "Terminal" to do script "cd '$(pwd)' && python nlp_voice_bot/voicebot.py"'

echo "Museum system started successfully!"
echo "Press Ctrl+C to stop the script"

# Keep script running to allow orderly shutdown
trap "echo 'Shutting down...'; pkill -f mosquitto; exit 0" SIGINT
while true; do
    sleep 1
done 