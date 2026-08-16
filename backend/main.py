import cv2 
import asyncio
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from cv_engine.src.detect_penalty import detect_penalty
from cv_engine.src.pipeline import State, process_state_machine
from ultralytics import YOLO

# --------------------
# GLOBAL VARIABLES
# --------------------

app = FastAPI()
camera = cv2.VideoCapture(0)

# YOLO classes
TIMER_CLASS = "timer"
CARD_CLASS = "judge_card"



# --------------------
# GENERATOR
# --------------------

async def generate_frames():
    """
    Continually reads from camera, encodes frame, and sends a HTTP response
    """
    # Variables for text display
    current_time_str = None
    current_penalty_str = None

    while True:
        success, frame = camera.read()
        if not success:
            break

        # load YOLO model
        model = YOLO('cv_engine/models/best.pt')

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


        # compress the OpenCV image into a JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue
            
        frame_bytes = buffer.tobytes()

        # yield the frame using the MJPEG boundary format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        # yield control back to the event loop so FastAPI doesn't lock up
        await asyncio.sleep(0.01)


@app.get("/video_feed")
async def video_feed():
    """
    Endpoint to get live footage from webcam
    """
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.on_event("shutdown")
def shutdown_event():
    camera.release()