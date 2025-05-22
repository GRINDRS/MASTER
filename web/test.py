import cv2
import time
import datetime

# URL of the stream hosted by your Flask app
STREAM_URL = "http://10.89.115.76:5000/video"  # Replace <your-ip> with the actual IP

# Open the video stream
cap = cv2.VideoCapture(STREAM_URL)

if not cap.isOpened():
    print("Failed to connect to the video stream.")
    exit()

print("Connected to stream. Saving one frame every 10 seconds...")

# Timer
last_saved = time.time()

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read frame.")
            break

        now = time.time()
        if now - last_saved >= 10:  # 10 seconds interval
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"frame_{timestamp}.jpg"
            cv2.imwrite(filename, frame)
            print(f"Saved: {filename}")
            last_saved = now

        # Optional: display the stream in a window
        cv2.imshow("Stream", frame)
        if cv2.waitKey(1) == 27:  # ESC key to quit
            break

except KeyboardInterrupt:
    print("Interrupted by user.")

cap.release()
cv2.destroyAllWindows()
