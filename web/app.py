"""
web_interface.py

This Flask web application provides a real-time video stream from a webcam, 
displays shared NLP/museum navigation data from a JSON file, and optionally supports
simple voting interactions. Designed as the browser interface for an interactive
museum tour system.

Key Features:
- Live webcam stream via OpenCV and MJPEG over HTTP.
- NLP data visualisation from a shared 'spoke.json' file.
- Dynamic HTML rendering through Flask templates.
- Capturable static frame as JPEG.
- Supports expansion for voting, user input, and more.

Author: GRINDRS
Date: 2025
"""

from flask import Flask, render_template, request, redirect, url_for, Response, make_response, send_file
import json, time, cv2, io, threading
from PIL import Image
from collections import Counter
import paho.mqtt.client as mqtt
import sys
import os

# Extend path to access shared modules if needed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
app = Flask(__name__)

# -------------------------------
# GLOBAL CONFIGURATION
# -------------------------------

# Initialise the camera (device 0)
cap = cv2.VideoCapture(0)

# Basic placeholder options for voting (not used actively here)
options = ["Mia", "May"]
answers = []  # Stored responses for vote simulation

# Path to shared JSON data (used by voicebot etc.)
spoke_path = "spoke.json"

# -------------------------------
# UTILITY FUNCTIONS
# -------------------------------

def load_json(name):
    """
    Load JSON data from a file.

    Args:
        name (str): File path.

    Returns:
        dict: Parsed JSON content.
    """
    with open(name) as f:
        return json.load(f)

def save_json(name, data):
    """
    Save dictionary data to a JSON file.

    Args:
        name (str): File path to save to.
        data (dict): Dictionary to write.
    """
    with open(name, 'w') as f:
        json.dump(data, f, indent=4)

def get_vote_cookie_key():
    """
    Generate a cookie key to check if the user has already voted.

    Returns:
        str: Unique cookie key.
    """
    return "has_voted_" + "_".join(option.lower() for option in options)

def generate_frames():
    """
    Yields frames from the webcam encoded as JPEG for MJPEG streaming.

    Yields:
        bytes: Multipart HTTP response chunk with JPEG frame.
    """
    prev = 0
    while True:
        time_elapsed = time.time() - prev
        if time_elapsed > 1 / 15:  # ~15 frames per second
            prev = time.time()
            success, frame = cap.read()
            if not success:
                break
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# -------------------------------
# ROUTES
# -------------------------------

@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Render the homepage which displays shared conversation and location data.

    Returns:
        HTML template rendered with spoke.json data.
    """
    spoke = load_json(spoke_path)
    return render_template('index.html', spoke=spoke)

@app.route('/video')
def video():
    """
    Streams the live webcam video to the web client using multipart encoding.

    Returns:
        Response: Streaming MJPEG video.
    """
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/frame.jpg')
def frame():
    """
    Captures a single frame from the camera and returns it as a JPEG image.

    Returns:
        FileResponse: JPEG image as a web response.
    """
    try:
        success, frame = cap.read()
        if not success:
            return "Failed to capture image", 500
        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        buf.seek(0)
        return send_file(buf, mimetype='image/jpeg')
    except Exception as e:
        print(f"Frame capture exception: {e}")
        return "Internal error", 500

# -------------------------------
# APP ENTRY POINT
# -------------------------------

if __name__ == '__main__':
    # Start the Flask development server with multithreading enabled
    app.run(host='0.0.0.0', port=5000, threaded=True)
