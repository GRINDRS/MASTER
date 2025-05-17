FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    mosquitto \
    mosquitto-clients \
    ffmpeg \
    libportaudio2 \
    libsndfile1 \
    pulseaudio \
    alsa-utils \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose MQTT port
EXPOSE 1883

# Create an entrypoint script
RUN echo '#!/bin/bash\n\
# Start Mosquitto MQTT broker in the background\n\
mosquitto -d\n\
\n\
# Sleep to ensure broker is running\n\
sleep 2\n\
\n\
# Export environment variable to indicate container environment\n\
export IN_DOCKER_CONTAINER=true\n\
\n\
# Start the main navigation system and the voicebot in parallel\n\
python main.py & python nlp_voice_bot/voicebot.py\n\
\n\
# Keep the container running\n\
wait\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"] 