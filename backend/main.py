import cv2 
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
from cv_engine.src.detect_penalty import detect_penalty
from cv_engine.src.pipeline import State, process_state_machine
from ultralytics import YOLO

# --------------------
# GLOBAL VARIABLES
# --------------------

camera = cv2.VideoCapture(0)

# YOLO classes
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

# --------------------
# GENERATOR
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


@app.get("/video_feed")
def video_feed():
    """
    Endpoint to get live footage from webcam
    """
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )