import cv2 
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
from cv_engine.src.detect_penalty import detect_penalty
from cv_engine.src.pipeline import State, process_state_machine
from ultralytics import YOLO

from pydantic import BaseModel
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import math

# --------------------------
# GLOBAL VARIABLES & CONFIG
# --------------------------

camera = cv2.VideoCapture(0)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# YOLO Classes
TIMER_CLASS = "timer"
CARD_CLASS = "judge_card"
YOLO_FREQ = 15 # how often to run YOLO on a frame

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting server")
    yield
    
    print("Shutting down")
    camera.release()

app = FastAPI(lifespan=lifespan)

# allow frontend server to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global State
cv_state = {"time": None, "penalty": None, "state": None}
app_settings = {}
leaderboard_df = pd.DataFrame()


# --------------------
# CLASSES
# --------------------

class CompetitionSettings(BaseModel):
    competition_name: str
    event: str
    round_number: str
    avg_format: str
    competitors: List[str]

class SaveResultRequest(BaseModel):
    competitor_name: str
    solve_index: int
    final_result: str


# --------------------
# HELPER FUNCTIONS
# --------------------

def generate_frames():
    """
    Continually reads from camera, encodes frame, and sends a HTTP response
    """
    # Variables for text display
    current_time_str = None
    current_penalty_str = None

    # load YOLO model
    model = YOLO('cv_engine/models/best.pt')

    frame_count = 0

    while True:
        success, frame = camera.read()
        if not success:
            break

        # run YOLO every 15 frames
        if frame_count % YOLO_FREQ == 0:
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

            # update cv state
            if time_str is not None:
                cv_state["time"] = time_str
            if penalty is not None and current_state == State.COOLDOWN:
                cv_state["penalty"] = penalty

            cv_state["state"] = str(current_state)
            

        # increase frame_count, reset if large
        frame_count += 1
        if frame_count >= 1000:
            frame_count = 0

        # compress the OpenCV image into a JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue
            
        frame_bytes = buffer.tobytes()

        # yield the frame using the MJPEG boundary format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')


def calculate_wca_result(raw_time_str: str, penalty: str) -> str:
    """
    Processes raw time string, applies penalty, then formats as WCA time
    """
    if not raw_time_str or penalty == "DNF":
        return "DNF"

    # calculate total number of seconds in the time
    time_parts = raw_time_str.split(":")
    total_seconds = 0
    if len(time_parts) == 2:
        total_seconds = int(time_parts[0]) * 60 + float(time_parts[1])
    else:
        total_seconds = float(time_parts[0])

    # apply +2 penalty if applicable
    if penalty == "+2": 
        total_seconds += 2.0

    # truncate time to 2 decimal places
    total_seconds = math.trunc(total_seconds * 100) / 100

    # format time as M:SS.SS
    if total_seconds >= 60:
        mins = int(total_seconds // 60)
        secs = total_seconds % 60
        return f"{mins}:{secs:05.2f}"
    else:
        return f"{total_seconds:.2f}"
    

# --------------------
# ENDPOINTS
# --------------------

@app.get("/video_feed")
def video_feed():
    """
    Endpoint to get live footage from webcam
    """
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@app.post("/settings")
def save_settings(settings: CompetitionSettings):
    """
    Saves competition settings to global state
    """
    global app_settings, leaderboard_df
    app_settings = settings.model_dump()

    # generate dataframe columns based on avg format
    num_solves = 5 if settings.avg_format.lower() == "ao5" else 3
    columns = [f"Solve {i+1}" for i in range(num_solves)]

    # create dataframe indexed by competitor names
    leaderboard_df = pd.DataFrame(index=settings.competitors, columns=columns)

    return {
        "status": "success",
        "message": "Settings applied and leaderboard created."
    }

@app.get("/settings")
def get_current_settings():
    """Returns the currently active competition settings"""
    global app_settings
    
    if not app_settings:
        return {"status": "empty", "message": "No settings configured yet."}
        
    return {
        "status": "success", 
        "data": app_settings
    }  


@app.get("/latest_result")
def get_latest_result():
    """
    Gets latest solve result from cv_state
    """
    raw_time = cv_state["time"]
    penalty = cv_state["penalty"]

    # calculate final result
    final_result = calculate_wca_result(raw_time, penalty) if raw_time else None

    return {
        "raw_time": raw_time,
        "penalty": penalty,
        "final_result": final_result,
        "cv_status": cv_state["state"] # also return state machine status
    }


@app.post("/save_result")
def save_result(req: SaveResultRequest):
    """
    Saves competitor's result to the leaderboard
    """
    global leaderboard_df

    # add competitor to leaderboard if not already there
    if req.competitor_name not in leaderboard_df.index:
        leaderboard_df.loc[req.competitor_name] = ""

    # add resilt to leaderboard
    col_name = f"Solve {req.solve_index}"
    leaderboard_df.at[req.competitor_name, col_name] = req.final_time

    return {
        "status": "success",
        "leaderboard": leaderboard_df.to_dict(orient="index")
    }