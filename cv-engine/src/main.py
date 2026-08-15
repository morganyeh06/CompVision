import os
import requests
import base64
import cv2
import json
from ultralytics import YOLO
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from numericvision import detect_box_sequences
import easyocr
import threading
from dotenv import load_dotenv

# --------------------
# CLASSES
# --------------------

class AsyncOCR:
    def __init__(self, languages=["en"], use_gpu=False):
        self.reader = easyocr.Reader(languages, gpu=use_gpu)
        self.is_processing = False
        self.latest_result = None

    def process_roi_async(self, roi_image):
        """
        Starts OCR on background thread if worker not currently in use
        """
        # skip frame if OCR already running on previous frame
        if self.is_processing:
            return

        if roi_image is None or roi_image.size == 0:
            return 

        # mark as busy and start worker thread
        self.is_processing = True

        # pass copy of image to main thread
        thread = threading.Thread(
            target=self.read_judge_card,
            args=(roi_image.copy(),),
            daemon=True
        )
        thread.start()

    def read_judge_card(self, roi):
        """
        Worker method for reading card text
        """
        try:
            results = self.reader.readtext(roi, detail=0)
            if results:
                raw_text = "".join(results).upper()
                
                # Correct slight misreads
                if "OK" in raw_text or "0K" in raw_text:
                    self.latest_result = "OK"
                elif "+2" in raw_text or "+" in raw_text or "2" in raw_text:
                    self.latest_result = "+2"
                elif "DNF" in raw_text or "D" in raw_text or "N" in raw_text or "F" in raw_text:
                    self.latest_result = "DNF"
                else:
                    self.latest_result = None
            else:
                self.latest_result = None

        except Exception as e:
            print(f"OCR Exception: {e}")
            self.latest_result = None
        finally:
            # release lock for next ROI to be processed
            self.is_processing = False

    def get_latest_result(self):
        return self.latest_result

# --------------------
# GLOBAL VARIABLES
# --------------------

load_dotenv("../../.env")

TIMER_CLASS = "timer"
CARD_CLASS = "judge_card"

# OCR Config
ocr_reader = AsyncOCR(use_gpu=False)

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

ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY")
ROBOFLOW_URL = os.getenv("ROBOFLOW_URL")

# --------------------
# PENALTY DETECTION
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


def detect_penalty(frame, card_roi):
    """
    Determines penalty by checking judge card text or hand gesture, depending on what is shown
    """

    # read text on card if it exists
    if card_roi is not None:
        ocr_reader.process_roi_async(card_roi)
        return ocr_reader.get_latest_result()

    # look for hand gesture if card not found
    gesture = classify_hand_gesture(frame)
    if gesture is not None:
        return gesture

    # no card/gesture found
    return None

# --------------------
# READ TIMER
# --------------------

def img_to_base64(img, jpeg_quality=90):
    """
    Converts image to base64
    """
    success, buffer = cv2.imencode(
        ".jpg",
        img,
        [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality],
    )

    if not success:
        raise RuntimeError("Failed to encode video frame")

    return base64.b64encode(buffer).decode("utf-8")


def read_display_roboflow(img):
    """
    Reads timer using Roboflow model given an base64 image
    Returns JSON results
    """
    img_base64 = img_to_base64(img)

    response = requests.post(
        url=ROBOFLOW_URL,
        json={
            "api_key": ROBOFLOW_API_KEY,
            "inputs": {
                "image": {
                    "type": "base64",
                    "value": img_base64,
                }
            },
        },
        timeout=120,
    )

    response.raise_for_status()
    result = response.json()

    return result

def get_roboflow_digits(response):
    """
    Returns the digits from roboflow model response
    """
    # get digits as json
    digits_json = response["outputs"][0]["predictions"]["predictions"]
    
    # get list of (x-coordinate, digit) and sort by x-coordinate (left to right)
    pairs = []
    for item in digits_json:
        pairs.append((item["x"], item["class"]))
    pairs.sort()
    
    # get string of digits (note . may be read as well)
    digits = ""
    for pair in pairs:
        digits += pair[1]
    
    return digits


def clean_time_str(time):
    """
    Formats text as a M:SS.SSS
    """
    # Check if raw_text is M.SS.SSS or M.S.SSS
    if time.count('.') > 1:
        # replace first instance of . with :
        time = time.replace('.', ':', 1)

    # Check if time is M:S.SSS
    if ':' in time and len(time) == 7:
        # change text to M:0S.SSS
        time = time[:2] + "0" + time[2:]

    return time


def read_time(timer_roi):
    """
    Reads time displayed on timer and returns as a numerical value
    """
    # read text on card if it exists
    if timer_roi is not None and timer_roi.size > 0:
        # read display and get digits read
        response = read_display_roboflow(timer_roi)
        raw_text = get_roboflow_digits(response)

        # format the string as a proper time
        time = clean_time_str(raw_text)
        return time
        

    return None

# --------------------
# MAIN
# --------------------

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

        # read timer
        time = read_time(timer_roi)

        # display penalty and time on screen
        penalty_text = f"Penalty: {penalty}" if penalty else "Searching..."
        timer_text = f"Time: {time}"
        cv2.putText(frame, f"Status: {timer_text}", (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f"Status: {penalty_text}", (20, 80), 
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