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
pwmA.start(100)  # Start with 0% duty cycle (off) for motor 1
pwmB.start(100)  # Start with 0% duty cycle (off) for motor 2

"""
Bare-metal motor functionality that interacts via GPIO pins.
"""
def motor1_forward() -> None:
    """
    Using GPIO Pins, drive motor1 forward.
    """
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    print("Motor 1 moving forward")

def motor1_backward() -> None:
    """
    Using GPIO Pins, drive motor1 backward.
    """
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    print("Motor 1 moving backward")

def motor2_forward() -> None:
    """
    Using GPIO Pins, drive motor2 forward.
    """
    GPIO.output(IN4, GPIO.HIGH)
    GPIO.output(IN3, GPIO.LOW)
    print("Motor 2 moving forward")

def motor2_backward() -> None:
    """
    Using GPIO Pins, drive motor2 backward.
    """
    GPIO.output(IN4, GPIO.LOW)
    GPIO.output(IN3, GPIO.HIGH)
    print("Motor 2 moving backward")

def motor1_stop() -> None:
    """
    Using GPIO Pins, stop motor1.
    """
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    print("Motor 1 stopped")

def motor2_stop() -> None:
    """
    Using GPIO Pins, stop motor2.
    """
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.LOW)
    print("Motor 2 stopped")

def set_speed(motor: int, speed: int) -> None:
    """
    Sets the speed of a requested motor using a given speed as a percentage.

    Parameters:
        motor: The motor number given (1, 2).
        speed: The speed integer (interpreted as a percentage).
    """
    if motor == 1:
        pwmA.ChangeDutyCycle(speed)  # Change motor 1 speed (0-100%)
    elif motor == 2:
        pwmB.ChangeDutyCycle(speed)  # Change motor 2 speed (0-100%)

"""
Abstraction layer functions that utilise the bare-metal ones.
"""
def turn_right(timer: float) -> None:
    """
    Turns the robot right on the spot, for a set time.

    Parameters:
        timer: The time to turn for.
    """
    motor1_forward()
    motor2_backward()
    print("Turning right")
    time.sleep(timer) 
    motor1_stop()
    motor2_stop()

def turn_left(timer: float) -> None:
    """
    Turns the robot left on the spot, for a set time.

    Parameters:
        timer: The time to turn for.
    """
    motor1_backward()
    motor2_forward()
    print("Turning left")
    time.sleep(timer)  
    motor1_stop()
    motor2_stop()

def move_forward() -> None:
    """
    Moves the robot forward using both motors for a small amount of time.
    """
    motor1_forward()
    motor2_forward()
    print("Moving forward")

def move_backward() -> None:
    """
    Moves the robot backwards using both motors for a small amount of time.
    """
    motor1_backward()
    motor2_backward()
    print("Moving backward")

def turn_90_left() -> None:
    """
    Rotates the bot on the spot 90 degrees to the left.
    """
    turn_left(1.45)

def turn_90_right() -> None:
    """
    Rotates the bot on the spot 90 degrees to the right.
    """
    turn_right(1.45)

def turn_behind_left() -> None:
    """
    Rotates the bot on the spot 180 degrees to the left.
    """
    turn_left(2.9)

def turn_behind_right() -> None:
    """
    Rotates the bot on the spot 180 degrees to the right.
    """
    turn_right(2.9)
