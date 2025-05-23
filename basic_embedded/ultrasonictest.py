"""
single_distance_read.py

This module provides a blocking function to retrieve a single distance measurement
from an HC-SR04 ultrasonic sensor using the Raspberry Pi's GPIO pins. It is suitable
for simple applications where periodic distance readings are sufficient and no
background threading is required.

The script can be executed directly to perform continuous measurements and print
them to the console. Appropriate for educational projects, small robotics,
and proximity detection tasks.

Author: GRINDRS
Platform: Raspberry Pi (BCM GPIO Mode)
Date: 2025
"""

import RPi.GPIO as GPIO
import time
import math.inf

# GPIO pin assignments for the ultrasonic sensor
TRIG = 5  # Trigger pin (GPIO 5)
ECHO = 6  # Echo pin (GPIO 6)

# Initialise GPIO using Broadcom SOC channel numbering
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

def get_distance(timeout=0.02):
    """
    Retrieves a single distance measurement using the ultrasonic sensor.

    Args:
        timeout (float): Maximum time in seconds to wait for echo response.

    Returns:
        float: Distance to the nearest object in centimetres.
               Returns math.inf if the echo never starts,
               or None if the echo takes too long to finish.
    """
    # Emit a 10-microsecond trigger pulse
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    start_time = time.time()

    # Wait for echo signal to go high (start of pulse)
    while GPIO.input(ECHO) == 0:
        if time.time() - start_time > timeout:
            return math.inf  # Timeout waiting for echo to start
    start = time.time()

    # Wait for echo signal to go low (end of pulse)
    while GPIO.input(ECHO) == 1:
        if time.time() - start > timeout:
            return None  # Timeout waiting for echo to end
    end = time.time()

    # Calculate distance using time difference and speed of sound
    duration = end - start
    distance = (duration * 34300) / 2  # Convert time to centimetres
    return round(distance, 2)

# When run as a script, take continuous readings
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
