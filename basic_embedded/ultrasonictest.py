import RPi.GPIO as GPIO
import time

# Use BCM pin numbering
TRIG = 5  # GPIO 5
ECHO = 6  # GPIO 6

# Set up the GPIO pins for the ultrasonic sensor.
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

def get_distance() -> int:
    """
    Gets the distance by the ultrasonic sensor.

    Returns:
        Distance of range ()
    """
    # Send 10us pulse to trigger
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    # Wait for echo start
    while GPIO.input(ECHO) == 0:
        start = time.time()

    # Wait for echo end
    while GPIO.input(ECHO) == 1:
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

