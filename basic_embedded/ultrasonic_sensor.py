import RPi.GPIO as GPIO
import time
import threading
import math

TRIG = 5  # GPIO 5
ECHO = 6  # GPIO 6

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

_latest_distance = 999 
_lock = threading.Lock()
_thread = None
_running = False

def _read_distance(timeout=0.02):
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    start_time = time.time()
    while GPIO.input(ECHO) == 0:
        if time.time() - start_time > timeout:
            return 999
    start = time.time()

    while GPIO.input(ECHO) == 1:
        if time.time() - start > timeout:
            return 999
    end = time.time()

    duration = end - start
    distance = (duration * 34300) / 2
    return round(distance, 2)

def _update_distance():
    global _latest_distance, _running
    while _running:
        dist = _read_distance()
        with _lock:
            _latest_distance = dist
        time.sleep(0.2)

def init_sensor():
    global _thread, _running
    if not _running:
        _running = True
        _thread = threading.Thread(target=_update_distance, daemon=True)
        _thread.start()

def stop_sensor():
    global _running
    _running = False
    if _thread:
        _thread.join()

def get_distance():
    with _lock:
        return _latest_distance

def cleanup():
    GPIO.cleanup()
