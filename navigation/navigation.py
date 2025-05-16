"""
SuperSimpleNAVigation 
    by Tristan Green

Proprietary software by GRINDRS - Ideas First; Innovation Later.
"""
import math
import time
from ..basic_embedded.twomotorbasic import move_forward, move_backward, \
                                           turn_right, motor1_stop, motor2_stop
from ..basic_embedded.ultrasonictest import get_distance
from capture_analyse import cap_anal

NINETY_DEG = 0.5
TIMEOUT_SECONDS = 90
PIVOT_DISTANCE: float = -math.inf
PAIRINGS: dict[str, str] = {
    "Mona Lisa": "Toy Dog",
    "Sunflowers (Van Gogh)": "Stylized Egyptian Sculpture",
    "Liberty Leading the People": "",
    "": "Starry Night"
}

# Error codes, think C language
SUCCESS = 0
FAILURE = 1


def wall_detection() -> bool:
    """
    Detects how close walls are using the subsonic sensor.

    Returns:
        True if the wall is close enough for a detection event,
        False otherwise.
    """
    current_subsonic = get_distance()
    if current_subsonic < PIVOT_DISTANCE:
        return True
    
    return False

def goal_artwork() -> str:
    """
    Returns the goal artwork that the robot aims to arrive at
    """
    goal_artwork = ""
    return goal_artwork

def detect_artwork() -> str:
    """
    Detects the artwork in front of the robot.

    Returns the detected artwork in front of the robot.
    """
    return cap_anal()

def is_correct_position(goal_art: str) -> bool:
    """
    Identifies if the robot is in the correct position to cease navigation.

    Returns:
        True if the robot is in the correct corner,
        False otherwise!
    """
    detected_art = detect_artwork()
    if (goal_art == detected_art or 
        goal_art == PAIRINGS[detected_art]):
        return True
    return False

def search_timeout(start_time: float) -> bool:
    """
    Checks if the search has timed out for the robot and the artwork cannot be
        found.

    Returns:
        True if the robot has timed out.
        False otherwise.
    """
    if time.time() - start_time > TIMEOUT_SECONDS:
        return True
    return False

def travel(goal_artwork: str) -> int:
    """
    Main navigation control flow.

    Returns:
        0 if the robot successfully navigated to its target artwork.
        1 if the robot's search timed out.
    """
    # Bookkeep time for a timeout check.
    start_time = time.time()
    while True:
        # Move forward before anything
        # TODO EMBEDDED MUST FIX THIS IMPLEMENTATION FUNCTIONALLY.
        move_forward()
        motor1_stop()
        motor2_stop()


        # If a wall has been detected in viewing distance for the bot
        if wall_detection():
            if is_correct_position(goal_artwork):
                return SUCCESS # We win
            else:
                # TODO EMBEDDED FIX
                turn_right(NINETY_DEG) # This param should be handled in embed??
        
        # If the navigation has taken more than 90 seconds (far too long).
        if search_timeout(start_time):
            return FAILURE