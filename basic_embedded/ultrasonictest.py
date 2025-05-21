import RPi.GPIO as GPIO
import time
import math.inf

# Use BCM pin numbering
TRIG = 5  # GPIO 5
ECHO = 6  # GPIO 6

# Set up the GPIO pins for the ultrasonic sensor.
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

def get_distance(timeout=0.02) :
    """
    Gets the distance by the ultrasonic sensor.

    Returns:
        Distance of range ()
    """
    # Send 10us pulse to trigger
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)
    start_time = time.time()

    # Wait for echo to go high (start)
    while GPIO.input(ECHO) == 0:
        if time.time() - start_time > timeout:
            return math.inf # Timeout waiting for echo to start
    start = time.time()

    # Wait for echo to go low (end)
    while GPIO.input(ECHO) == 1:
        if time.time() - start > timeout:
            return None  # Timeout waiting for echo to end
    end = time.time()

    # Time difference
    duration = end - start
    distance = (duration * 34300) / 2  # cm
    return round(distance, 2)


if __name__ == "__main__":
    try:
        while True:
            dist = get_distance()
            print(f"Distance: {dist} cm")
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping program.")

    finally:
        GPIO.cleanup()

