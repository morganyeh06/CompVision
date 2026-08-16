import cv2
import os
import base64
import requests
from dotenv import load_dotenv

# --------------------
# GLOBAL VARIABLES
# --------------------

load_dotenv("../../../.env")

# Roboflow Config
ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY")
ROBOFLOW_URL = os.getenv("ROBOFLOW_URL")

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


def clean_time_str(time_str):
    """
    Formats text as a M:SS.SSS
    """
    # remove 'screen' from string
    if 'screen' in time_str:
        time_str = time_str.replace('screen', '')

    # Check if . is missing from time (eg. SSSS)
    if time_str.count('.') == 0:
        # insert . in the 4th position from the end
        i = len(time_str) - 3
        time_str = time_str[:i] + "." + time_str[i:]

    # Check if raw_text is M.SS.SSS or M.S.SSS
    if time_str.count('.') > 1:
        # replace first instance of . with :
        time_str = time_str.replace('.', ':', 1)

    # Check if time is M:S.SSS
    if ':' in time_str and len(time_str) == 7:
        # change text to M:0S.SSS
        time_str = time_str[:2] + "0" + time_str[2:]

    return time_str


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