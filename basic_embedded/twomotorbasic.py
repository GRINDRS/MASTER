import RPi.GPIO as GPIO
import time

# Set GPIO mode
GPIO.setmode(GPIO.BCM)

# Define the GPIO pins for the motors
IN1 = 17
IN2 = 27
ENA = 22  # PWM for motor 1

IN3 = 23
IN4 = 24
ENB = 25  # PWM for motor 2

# Set up the GPIO pins
GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)
GPIO.setup(ENA, GPIO.OUT)  # Enable pin for motor 1

GPIO.setup(IN3, GPIO.OUT)
GPIO.setup(IN4, GPIO.OUT)
GPIO.setup(ENB, GPIO.OUT)  # Enable pin for motor 2

# Set the motor speeds (using PWM on ENA and ENB)
pwmA = GPIO.PWM(ENA, 1000)  # 1000 Hz frequency for motor 1
pwmB = GPIO.PWM(ENB, 1000)  # 1000 Hz frequency for motor 2
pwmA.start(50)  # Start with 0% duty cycle (off) for motor 1
pwmB.start(50)  # Start with 0% duty cycle (off) for motor 2

# Function to move motor 1 forward
def motor1_forward():
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    print("Motor 1 moving forward")

# Function to move motor 1 backward
def motor1_backward():
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    print("Motor 1 moving backward")

# Function to move motor 2 forward
def motor2_forward():
    GPIO.output(IN4, GPIO.HIGH)
    GPIO.output(IN3, GPIO.LOW)
    print("Motor 2 moving forward")

# Function to move motor 2 backward
def motor2_backward():
    GPIO.output(IN4, GPIO.LOW)
    GPIO.output(IN3, GPIO.HIGH)
    print("Motor 2 moving backward")

# Function to stop motor 1
def motor1_stop():
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    print("Motor 1 stopped")

# Function to stop motor 2
def motor2_stop():
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.LOW)
    print("Motor 2 stopped")

# Set motor speeds (optional, with PWM)
def set_speed(motor, speed):
    if motor == 1:
        pwmA.ChangeDutyCycle(speed)  # Change motor 1 speed (0-100%)
    elif motor == 2:
        pwmB.ChangeDutyCycle(speed)  # Change motor 2 speed (0-100%)

# Function to turn right (motor 1 moves forward, motor 2 moves backward)
def turn_right(timer):
    motor1_forward()
    motor2_backward()
    print("Turning right")
    time.sleep(timer)  # Turn for 0.2 seconds
    motor1_stop()
    motor2_stop()

# Function to turn left (motor 1 moves backward, motor 2 moves forward)
def turn_left(timer):
    motor1_backward()
    motor2_forward()
    print("Turning left")
    time.sleep(timer)  
    motor1_stop()
    motor2_stop()

# Function to move forward (both motors forward)
def move_forward():
    motor1_forward()
    motor2_forward()
    print("Moving forward")

# Function to move backward (both motors backward)
def move_backward():
    motor1_backward()
    motor2_backward()
    print("Moving backward")


# Main execution
if __name__ == "__main__":
    try:
        # Move forward at 50% speed
        move_forward()
        time.sleep(2)

        # Turn left for 0.2 seconds
        turn_left(1)

        # Stop for 1 second
        motor1_stop()
        motor2_stop()
        time.sleep(1)

        # Turn right for 0.2 seconds
        turn_right(1)

        # Stop motors
        motor1_stop()
        motor2_stop()

    finally:
        # Clean up the GPIO settings
        GPIO.cleanup()
        print("GPIO cleaned up")

