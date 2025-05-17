# Museum Navigation System

This project integrates a voice bot with a navigation system for a museum robot tour guide using MQTT for communication.

## Components

- **Voice Bot**: Natural language interface that allows users to select exhibits to visit
- **Navigation System**: Handles the robot's movement to selected exhibits
- **Main System**: Coordinates between the voice bot and navigation components

## Docker Setup

The simplest way to run this system is using Docker:

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- OpenAI API key for the voice bot

### Setup

1. Clone this repository
2. Create a `.env` file in the project root with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

3. Build and start the Docker container:
   ```bash
   docker-compose up --build
   ```

### Running in Development Mode

For development, you might want to run components separately:

1. Start the MQTT broker:
   ```bash
   mosquitto -d
   ```

2. Run the main system:
   ```bash
   python main.py
   ```

3. Run the voice bot:
   ```bash
   python nlp_voice_bot/voicebot.py
   ```

## Manual Setup (without Docker)

If you prefer not to use Docker:

1. Install dependencies:
   - Python 3.9+
   - Mosquitto MQTT broker
   - FFmpeg
   - Required Python packages: `pip install -r requirements.txt`

2. Create a `.env` file with your OpenAI API key

3. Make the startup script executable:
   ```bash
   chmod +x start_museum_system.sh
   ```

4. Run the system:
   ```bash
   ./start_museum_system.sh
   ```

## MQTT Communication

- Voice bot sends exhibit selections to the "movement" topic
- Main system receives these selections and passes them to the navigation system
- When navigation is complete, main system sends a confirmation on the "arrived" topic
- Voice bot receives the confirmation and continues the tour 