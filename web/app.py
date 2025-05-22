from flask import Flask, render_template, request, redirect, url_for, Response, make_response, send_file
import json, time, cv2, io, threading
from PIL import Image
from collections import Counter
import paho.mqtt.client as mqtt
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
app = Flask(__name__)

# Initialize the webcam
cap = cv2.VideoCapture(0)

# Voting options
options = ["Mia", "May"]
# Store user answers (in memory)
answers = []

# Path to JSON file used for shared data
spoke_path = "web/spoke.json"

def load_json(name):
    """
    Load JSON data from a file.

    Args:
        name (str): File path.

    Returns:
        dict: Parsed JSON data.
    """
    with open(name) as f:
        return json.load(f)

def save_json(name, data):
    """
    Save JSON data to a file.

    Args:
        name (str): File path.
        data (dict): Data to save.
    """
    with open(name, 'w') as f:
        json.dump(data, f, indent=4)

def get_vote_cookie_key():
    """
    Generate a unique cookie key to track if the user has voted.

    Returns:
        str: Unique cookie key.
    """
    return "has_voted_" + "_".join(option.lower() for option in options)

def generate_frames():
    """
    Generator function that captures frames from the camera and yields them as JPEG byte streams
    for real-time video streaming over HTTP.
    """
    prev = 0
    while True:
        time_elapsed = time.time() - prev
        if time_elapsed > 1 / 15:  # Limit to ~15 FPS
            prev = time.time()
            success, frame = cap.read()
            if not success:
                break
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Render the main page and handle conversation and 
    places from the NLP.
    """
    spoke = load_json(spoke_path)
    return render_template('index.html', spoke=spoke)

@app.route('/video')
def video():
    """
    Stream live video from the camera to the browser using multipart/x-mixed-replace.
    """
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/frame.jpg')
def frame():
    """
    Capture a single frame from the camera and return it as a JPEG image.
    """
    try:
        frame = cap.get(cv2.cv.CV_CAP_PROP_POS_FRAMES)
        # Convert OpenCV image (BGR) to PIL Image (RGB)
        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        buf.seek(0)
        return send_file(buf, mimetype='image/jpeg')
    except Exception as e:
        print(f"Frame capture exception: {e}")
        return "Internal error", 500

if __name__ == '__main__':
    # Start the Flask app
    app.run(host='0.0.0.0', port=5000, threaded=True)
