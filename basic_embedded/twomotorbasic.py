"""
twomotorbasic.py

This module provides low-level GPIO-based motor control functions and high-level
movement behaviours for a two-motor robotic platform, using the Raspberry Pi's
GPIO interface.

The script is configured for two DC motors connected via an H-bridge motor driver.
It supports forward/reverse motion, turning, stopping, and speed control through
PWM (Pulse Width Modulation). Designed to be used in indoor or controlled
environments, typical applications include robotics demonstrations, autonomous
navigation experiments, or educational projects.

Author: GRINDRS
Platform: Raspberry Pi (BCM GPIO Mode)
Date: 2025
"""

import RPi.GPIO as GPIO
import time

# ----------------------------------------------------------------------
# GPIO SETUP
# ----------------------------------------------------------------------

# Use Broadcom SOC channel numbering
GPIO.setmode(GPIO.BCM)

# Assign GPIO pins for motor 1
IN1 = 17
IN2 = 27
ENA = 22  # PWM-enabled pin for controlling motor 1 speed

# Assign GPIO pins for motor 2
IN3 = 23
IN4 = 24
ENB = 25  # PWM-enabled pin for controlling motor 2 speed

# Set all motor control pins as outputs
GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)
GPIO.setup(ENA, GPIO.OUT)

GPIO.setup(IN3, GPIO.OUT)
GPIO.setup(IN4, GPIO.OUT)
GPIO.setup(ENB, GPIO.OUT)

# Set up PWM channels at 1 kHz for each motor
pwmA = GPIO.PWM(ENA, 1000)
pwmB = GPIO.PWM(ENB, 1000)

# Start motors with 100% duty cycle
pwmA.start(100)
pwmB.start(100)

# ----------------------------------------------------------------------
# LOW-LEVEL MOTOR FUNCTIONS
# ----------------------------------------------------------------------

def motor1_forward() -> None:
    """
    Drives motor 1 forward by setting the appropriate GPIO outputs.
    """
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    print("Motor 1 moving forward")

def motor1_backward() -> None:
    """
    Drives motor 1 in reverse by toggling its GPIO outputs.
    """
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    print("Motor 1 moving backward")

def motor2_forward() -> None:
    """
    Drives motor 2 forward by setting the relevant GPIO signals.
    """
    GPIO.output(IN4, GPIO.HIGH)
    GPIO.output(IN3, GPIO.LOW)
    print("Motor 2 moving forward")

def motor2_backward() -> None:
    """
    Drives motor 2 in reverse direction by toggling its GPIO pins.
    """
    GPIO.output(IN4, GPIO.LOW)
    GPIO.output(IN3, GPIO.HIGH)
    print("Motor 2 moving backward")

def motor1_stop() -> None:
    """
    Stops motor 1 by disabling both input pins.
    """
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    print("Motor 1 stopped")

def motor2_stop() -> None:
    """
    Stops motor 2 by setting both input pins to LOW.
    """
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.LOW)
    print("Motor 2 stopped")

def set_speed(motor: int, speed: int) -> None:
    """
    Adjusts the speed of the specified motor using PWM duty cycle.

    Parameters:
        motor (int): Either 1 or 2 to represent motor 1 or motor 2.
        speed (int): Desired speed as a percentage (0–100).
    """
    if motor == 1:
        pwmA.ChangeDutyCycle(speed)
    elif motor == 2:
        pwmB.ChangeDutyCycle(speed)

# ----------------------------------------------------------------------
# HIGH-LEVEL ROBOT CONTROL FUNCTIONS
# ----------------------------------------------------------------------

def turn_right(timer: float) -> None:
    """
    Rotates the robot to the right on the spot for a defined time.

    Parameters:
        timer (float): Duration of the turn in seconds.
    """
    motor1_forward()
    motor2_backward()
    print("Turning right")
    time.sleep(timer)
    motor1_stop()
    motor2_stop()

def turn_left(timer: float) -> None:
    """
    Rotates the robot to the left on the spot for a defined time.

    Parameters:
        timer (float): Duration of the turn in seconds.
    """
    motor1_backward()
    motor2_forward()
    print("Turning left")
    time.sleep(timer)
    motor1_stop()
    motor2_stop()

def move_forward() -> None:
    """
    Moves the robot forward by engaging both motors in forward motion.
    """
    motor1_forward()
    motor2_forward()
    print("Moving forward")

def move_backward() -> None:
    """
    Moves the robot backward by reversing both motors.
    """
    motor1_backward()
    motor2_backward()
    print("Moving backward")

def turn_90_left() -> None:
    """
    Rotates the robot roughly 90 degrees to the left.
    The duration may need calibration depending on surface and battery.
    """
    turn_left(1.45)

def turn_90_right() -> None:
    """
    Rotates the robot roughly 90 degrees to the right.
    The duration may need calibration depending on surface and battery.
    """
    turn_right(1.45)

def turn_behind_left() -> None:
    """
    Performs a full 180-degree turn to the left.
    """
    turn_left(2.9)

def turn_behind_right() -> None:
    """
    Performs a full 180-degree turn to the right.
    """
    turn_right(2.9)
