import cv2
from ultralytics import YOLO

TIMER_CLASS = "timer"
CARD_CLASS = "judge_card"

def main():
    # Load custom YOLO model
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
                cv2.putText(frame, "Card", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        # Show the live feed 
        cv2.imshow("WCA Vision Assistant", frame)
        
        # Show the cropped timer ROI in a separate window to verify the crop
        #if timer_roi is not None and timer_roi.size > 0:
             #cv2.imshow("Timer ROI", timer_roi)

        # Press 'q' to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()