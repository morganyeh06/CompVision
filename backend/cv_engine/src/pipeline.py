import cv2
import time
from enum import Enum
from ultralytics import YOLO

from cv_engine.src.detect_penalty import detect_penalty
from cv_engine.src.read_timer import read_time

# --------------------
# CLASSES
# --------------------

class State(Enum): # Used for state machine
    SEARCHING = 1
    STABILIZING = 2
    CAPTURING = 3
    COOLDOWN = 4

# --------------------
# GLOBAL VARIABLES
# --------------------

# YOLO classes
TIMER_CLASS = "timer"
CARD_CLASS = "judge_card"

# State Machine variables
STABILIZATION_TIME = 1.0
COOLDOWN_TIME = 1.0
current_state = State.SEARCHING
detection_start_time = 0.0
cooldown_start_time = 0.0
current_penalty = None

# Variables for text display
current_time_str = None
current_penalty_str = None

# --------------------
# STATE MACHINE
# --------------------

def process_state_machine(detected_penalty, timer_roi):
    """
    Evaluates detected penalty and transitions state machine
    """
    global current_state, detection_start_time, cooldown_start_time, current_penalty
    timer_result = None

    # SEARCHING
    if current_state == State.SEARCHING:
        if detected_penalty is not None:
            # lock on to current frame, start timer
            current_penalty = detected_penalty
            detection_start_time = time.time()

            # transition to next state
            current_state = State.STABILIZING

    # STABILIZING
    elif current_state == State.STABILIZING:
        # ensure penalty did not change
        if detected_penalty != current_penalty:
            current_state = State.SEARCHING
            detected_penalty = None
        else:
            # transition to next state if enough time has passed
            elapsed_time = time.time() - detection_start_time
            if elapsed_time >= STABILIZATION_TIME:
                current_state = State.CAPTURING

    # CAPTURING
    elif current_state == State.CAPTURING:
        # get time from timer display
        timer_result = read_time(timer_roi)

        # Transition to Cooldown
        cooldown_start_time = time.time()
        current_state = State.COOLDOWN 

    # COOLDOWN
    elif current_state == State.COOLDOWN:
        # transition back to Searching if enough time has passed
        elapsed_time = time.time() - cooldown_start_time
        if elapsed_time >= COOLDOWN_TIME:
            current_state = State.SEARCHING
            current_penalty = None

    return current_state, timer_result

# --------------------
# MAIN
# --------------------

def main():
    global current_time_str, current_penalty_str

    # load YOLO model
    model = YOLO('../models/best.pt')

    # Open a connection to the webcam
    cap = cv2.VideoCapture(0)

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print("Failed to read frame from camera.")
            break

        # Run YOLO inference on the current frame
        results = model(frame, verbose=False)

        timer_roi = None
        card_roi = None

        # check if timer/card in captured in frame
        for box in results[0].boxes:
            class_id = int(box.cls[0])
            class_name = results[0].names[class_id]
                
            if class_name == TIMER_CLASS:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                timer_roi = frame[y1:y2, x1:x2]

            if class_name == CARD_CLASS:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                card_roi = frame[y1:y2, x1:x2]

        # determine penalty for solve
        penalty = detect_penalty(frame, card_roi)

        # transition the state machine; get current state and time
        current_state, time_str = process_state_machine(penalty, timer_roi)

        if time_str is not None:
            current_time_str = time_str
        if penalty is not None and current_state == State.COOLDOWN:
            current_penalty_str = penalty

        # display penalty, time, and state
        penalty_text = f"Penalty: {current_penalty_str}"
        timer_text = f"Time: {current_time_str}"
        state_text = f"State: {current_state}"
        cv2.putText(frame, f"{timer_text}", (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f"{penalty_text}", (20, 80), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f"{state_text}", (20, 200), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)


        # Show the live feed 
        cv2.imshow("CompVision", frame)

        # Press 'q' to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()