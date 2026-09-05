import cv2 
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
from cv_engine.src.detect_penalty import detect_penalty
from cv_engine.src.pipeline import State, process_state_machine

from pydantic import BaseModel
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import math

import csv
import io

from fastapi import WebSocket, WebSocketDisconnect
import base64
import numpy as np

# --------------------------
# GLOBAL VARIABLES & CONFIG
# --------------------------

'''camera = cv2.VideoCapture(0)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)'''

# YOLO Classes
TIMER_CLASS = "timer"
CARD_CLASS = "judge_card"
YOLO_FREQ = 15 # how often to run YOLO on a frame
yolo_model = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting server")
    yield
    
    print("Shutting down")
    #camera.release()

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

class editResultRequest(BaseModel):
    competitor_name: str
    solve_index: int
    new_time: str


# --------------------
# HELPER FUNCTIONS
# --------------------

def get_yolo_model():
    """Lazy loader for YOLO model to save boot-time memory"""
    global yolo_model
    if yolo_model is None:
        from ultralytics import YOLO  # Lazy import
        yolo_model = YOLO('cv_engine/models/best.pt')
    return yolo_model


def parse_wca_time(time_str: str):
    """
    Converts WCA time string to seconds
    """
    if not time_str:
        return None
    if time_str.upper() == "DNF":
        return float('inf')
    
    parts = time_str.split(':')
    total_seconds = 0
    if len(parts) == 2:
        total_seconds = int(parts[0]) * 60 + float(parts[1])
    else:
        total_seconds = float(parts[0])

    # truncate time to 2 decimal places
    total_seconds = math.trunc(total_seconds * 100) / 100
    return total_seconds


def format_wca_time(time_float: float):
    """
    Converts numerical time to WCA string format
    """
    if time_float is None:
        return ""
    elif time_float == float('inf'):
        return "DNF"
    elif time_float >= 60:
        mins = int(time_float // 60)
        secs = time_float % 60
        return f"{mins}:{secs:05.2f}"
    else:
        return f"{time_float:.2f}"


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

    # truncate time to 2 decimal places
    total_seconds = math.trunc(total_seconds * 100) / 100

    # apply +2 penalty if applicable
    if penalty == "+2": 
        total_seconds += 2.00

    return format_wca_time(total_seconds)
    

# --------------------
# ENDPOINTS
# --------------------

@app.get("/backend_status")
def get_backend_status():
    """
    Checks if backend is ready
    """
    return { "status": "success" }


@app.websocket("/ws/video_feed")
async def websocket_video_feed(websocket: WebSocket):
    await websocket.accept()
    model = get_yolo_model()
    frame_count = 0

    try:
        while True:
            # get base64 frame from React
            data = await websocket.receive_text()

            # convert base64 back to OpenCV frame
            encoded_data = data.split(",")[1]
            nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # process frame via YOLO
            if frame_count % YOLO_FREQ == 0:
                results = model(frame, verbose=False)
                timer_roi, card_roi = None, None

                for box in results[0].boxes:
                    class_id = int(box.cls[0])
                    class_name = results[0].names[class_id]
                    if class_name == TIMER_CLASS:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        timer_roi = frame[y1:y2, x1:x2]
                    if class_name == CARD_CLASS:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        card_roi = frame[y1:y2, x1:x2]

                penalty = detect_penalty(frame, card_roi)
                current_state, time_str = process_state_machine(penalty, timer_roi)

                # update global state
                if time_str: cv_state["time"] = time_str
                if penalty and current_state == State.COOLDOWN: cv_state["penalty"] = penalty
                cv_state["state"] = str(current_state)

            frame_count = (frame_count + 1) % 1000

    except WebSocketDisconnect:
        print("Client disconnected from video feed.")


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

    if leaderboard_df.empty:
        # initialize new leaderboard
        leaderboard_df = pd.DataFrame(index=settings.competitors, columns=columns)
    else:
        # update leaderboard rows: add/remove competitors as needed
        leaderboard_df = leaderboard_df.reindex(
            index=settings.competitors,
            columns=columns
        ).fillna("")

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

@app.post("/reset")
def reset():
    """
    Resets the backend state
    """
    global cv_state, leaderboard_df, app_settings

    cv_state = {"time": None, "penalty": None, "state": None}
    app_settings = {}
    leaderboard_df = pd.DataFrame()

    return { 
        "status": "success",
        "message": "backend reset"
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


@app.post("/reset_cv")
def reset_cv(): 
    """
    Resets the current CV engine values
    """
    global cv_state

    cv_state["time"] = None
    cv_state["penalty"] = None
    cv_state["state"] = "State.SEARCHING"

    return { "status": "cv reset" }


@app.post("/save_result")
def save_result(req: SaveResultRequest):
    """
    Saves competitor's result to the leaderboard
    """
    global leaderboard_df

    # add competitor to leaderboard if not already there
    if req.competitor_name not in leaderboard_df.index:
        leaderboard_df.loc[req.competitor_name] = ""

    # add result to leaderboard
    col_name = f"Solve {req.solve_index}"
    leaderboard_df.at[req.competitor_name, col_name] = req.final_result

    return {
        "status": "success",
        "leaderboard": leaderboard_df.fillna("").to_dict(orient="index")
    }


@app.get("/leaderboard")
def get_leaderboard():
    """
    Returns live leaderboard with calculated averages and ranks
    """
    global leaderboard_df, app_settings

    if leaderboard_df.empty:
        return { "leaderboard": [] }


    fmt = app_settings.get("avg_format", "ao5").lower()
    event = app_settings.get("event", "3x3")
    num_solves = 3 if fmt == "mo3" else 5

    results = []

    # process each competitor's results
    for name, row in leaderboard_df.iterrows():
        # check for NaN values
        raw_solves = [row.get(f"Solve {i+1}", "") for i in range(num_solves)]
        raw_solves = [s if pd.notna(s) else "" for s in raw_solves]

        # parse and validate solves
        parsed_solves = [parse_wca_time(s) for s in raw_solves]
        valid_solves = [s for s in parsed_solves if s is not None]

        is_finished = len(valid_solves) == num_solves

        # get fastest single and calculate average if competitor is finished
        best = min(valid_solves) if valid_solves else None
        avg = None
        if is_finished:
            if fmt == "ao5":
                dnf_count = parsed_solves.count(float('inf'))
                # average is DNF if there is > 1 DNF
                if dnf_count > 1:
                    avg = float('inf')
                else:
                    # drop fastest and slowest solves, then calculate mean of middle three
                    sorted_solves = sorted(parsed_solves)
                    avg = sum(sorted_solves[1:4]) / 3

            elif fmt == "mo3":
                # mean is DNF if one resultis DNF
                if float('inf') in parsed_solves:
                    avg = float('inf')
                else:
                    avg = sum(parsed_solves) / 3

        if avg and avg != float('inf'):
            avg = math.trunc(avg * 100) / 100

        # record results
        results.append({
            "name": name,
            "solves": raw_solves,
            "best_raw": best,
            "avg_raw": avg,
            "best": format_wca_time(best),
            "average": format_wca_time(avg),
            "is_finished": is_finished
        })

    # sort leaderboard
    def sort_key(r):
        # competitors not finished yet go to bottom of leaderboard
        if not r["is_finished"]:
            return (1, 0, 0)

        # rank by single for 3BLD, rank by average for all other events
        primary = r["best_raw"] if event == "3BLD" else r["avg_raw"]
        secondary = r["avg_raw"] if event == "3BLD" else r["best_raw"] # tiebreaker

        return (0, primary, secondary)

    results.sort(key=sort_key)

    final_leaderboard = []
    curr_rank = 1
    for entry in results:
        # assign rank
        if entry["is_finished"]:
            entry["rank"] = curr_rank
            curr_rank += 1
        else:
            entry["rank"] = ""

        # clean data
        final_leaderboard.append({
            "rank": entry["rank"],
            "name": entry["name"],
            "solves": entry["solves"],
            "best": entry["best"],
            "average": entry["average"],
            "is_finished": entry["is_finished"]
        })

    return { "leaderboard": final_leaderboard }


@app.post("/edit_result")
def edit_result(req: editResultRequest):
    """
    Saves edited result to the leaderboard
    """
    global leaderboard_df

    # ensure competitor is on leaderboard
    if req.competitor_name not in leaderboard_df.index:
        return {
            "status": "error",
            "message": "Competitor not found"
        }

    # update time
    new_time_str = ""
    if req.new_time.strip():
        new_time_float = parse_wca_time(req.new_time)
        new_time_str = format_wca_time(new_time_float)

    col_name = f"Solve {req.solve_index}"
    leaderboard_df.at[req.competitor_name, col_name] = new_time_str

    return {
        "status": "success",
        "message": "Result updated"
    }


@app.get("/export_csv")
def export_csv():
    """
    Downloads the competition results as a csv file
    """
    global app_settings

    comp_name = app_settings.get("competition_name", "Competition")
    event = app_settings.get("event", "3x3")
    round_num = app_settings.get("round", "1")
    fmt = app_settings.get("avg_format", "ao5").lower()

    # use competition name as filename
    filename = f"{comp_name.replace(' ', "_")}.csv"

    output = io.StringIO()
    writer = csv.writer(output)
    
    # create rows for title and subtitle
    writer.writerow([comp_name])
    writer.writerow([f"{event} - Round {round_num}"])
    writer.writerow([])
    
    # leaderboard headers
    num_solves = 3 if fmt == "mo3" else 5
    avg_col_name = "Mean" if fmt == "mo3" else "Average"
    headers = ["#", "Name"] + [f"Solve {i+1}" for i in range(num_solves)] + [avg_col_name, "Best"]
    writer.writerow(headers)
    
    # get formatted leaderboard
    board_data = get_leaderboard()["leaderboard"]
    for row in board_data:
        data_row = [
            row["rank"],
            row["name"]
        ] + row["solves"] + [row["average"], row["best"]]
        writer.writerow(data_row)
        
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )