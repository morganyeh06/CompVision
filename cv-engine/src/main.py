import cv2
from ultralytics import YOLO
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import easyocr

# --------------------
# GLOBAL VARIABLES
# --------------------
TIMER_CLASS = "timer"
CARD_CLASS = "judge_card"

# OCR Config
ocr_reader = easyocr.Reader(["en"], gpu=False)

# MediaPipe config
base_options = python.BaseOptions(model_asset_path="../models/hand_landmarker.task")
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=1,
    min_hand_detection_confidence=0.6,
    min_hand_presence_confidence=0.6,
    min_tracking_confidence=0.6,
    running_mode=vision.RunningMode.IMAGE 
)
detector = vision.HandLandmarker.create_from_options(options)

# --------------------
# HELPER FUNCTIONS
# --------------------

def read_card_text(card_roi):
    """
    Runs OCR on judge card region
    """
    if card_roi is None or card_roi.size == 0:
        return None

    # run OCR
    results = ocr_reader.readtext(card_roi, detail=0)
    if not results:
        return None
    raw_text = "".join(results).upper()

    # Correct slight misreads
    if "OK" in raw_text or "0K" in raw_text:
        return "OK"
    elif "+2" in raw_text or "+" in raw_text or "2" in raw_text:
        return "+2"
    elif "DNF" in raw_text or "D" in raw_text or "N" in raw_text or "F" in raw_text:
        return "DNF"
    else:
        return None


def classify_hand_gesture(frame):
    """
    Analyzes frame and determine whether hand gesture corresponds to OK, +2, DNF, or none
    """
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
    results = detector.detect(mp_image)

    if not results.hand_landmarks:
        return None

    # get hand landmarks for first detected hand
    lm = results.hand_landmarks[0]
    

    # finger positions, indices below
    # 0: wrist, 4: thumb tip, 2: thumb MCP
    # 8: index tip, 6: index PIP
    # 12: middle tip, 10: middle PIP
    # 16: ring tip, 14: ring PIP
    # 20: pinky tip, 18: pinky PIP
    index_folded = lm[8].y > lm[6].y
    middle_folded = lm[12].y > lm[10].y
    ring_folded = lm[16].y > lm[14].y
    pinky_folded = lm[20].y > lm[18].y
    thumb_up = lm[4].y < lm[3].y and lm[3].y < lm[2].y and lm[2].y < lm[1].y


    # helper functions for determining hand gestures
    def is_ok_gesture():
        """
        Returns true if hand landmarks create OK gesture (thumbs up), false otherwise
        """
        return lm[4].y < lm[2].y and index_folded and middle_folded and thumb_up

    def is_plus2_gesture():
        """
        Returns true if hand landmarks create +2 gesture (two fingers up), false otherwise
        """
        return not index_folded and not middle_folded and ring_folded and pinky_folded

    def is_dnf_gesture():
        """
        Returns true if hand landmarks create DNF gesture (thumbs down), false otherwise
        """
        return lm[4].y > lm[2].y and index_folded and middle_folded

    # determine hand gesture shown
    if is_ok_gesture():
        return "OK"
    elif is_plus2_gesture():
        return "+2"
    elif is_dnf_gesture():
        return "DNF"
    else:
        return None


def detect_penalty(frame, yolo_results):
    """
    Determines penalty by checking judge card text or hand gesture, depending on what is shown
    """
    card_roi = None

    # check if judge card in captured in frame
    for box in yolo_results[0].boxes:
        class_id = int(box.cls[0])
        class_name = yolo_results[0].names[class_id]

        if class_name == CARD_CLASS:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            card_roi = frame[y1:y2, x1:x2]
            break

    # read text on card if it exists
    if card_roi is not None:
        card_text = read_card_text(card_roi)
        if card_text is not None:
            return card_text

    # look for hand gesture if card not found
    gesture = classify_hand_gesture(frame)
    if gesture is not None:
        return gesture

    # no card/gesture found
    return None


def main():
    # Load custom YOLO modelq
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

        # determine penalty for solve
        penalty = detect_penalty(frame, results)

        # display penalty on screen
        status_text = f"Penalty: {penalty}" if penalty else "Searching..."
        cv2.putText(frame, f"Status: {status_text}", (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        '''timer_roi = None
        card_roi = None

        # Parse the YOLO results
        for box in results[0].boxes:
            # Get bounding box coordinates and class ID
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            class_id = int(box.cls[0])
            class_name = model.names[class_id]

            if class_name == TIMER_CLASS:
                # Crop the frame using the bounding box to isolate the timer
                timer_roi = frame[y1:y2, x1:x2]
                
                # Draw a green box for visual debugging
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, "Timer", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
            elif class_name == CARD_CLASS:
                # Crop the frame to isolate the judge's card
                card_roi = frame[y1:y2, x1:x2]
                
                # Draw a blue box for visual debugging
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                cv2.putText(frame, "Card", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)'''

        # Show the live feed 
        cv2.imshow("WCA Vision Assistant", frame)

        # Press 'q' to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()