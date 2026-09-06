# CompVision
An automatic scoretaking system for speedcubing competitions utilizing live competition footage

### Built With
* Python
* FastAPI
* YOLO
* OpenCV
* React
* TypeScript
* Bootstrap
* Pandas

## Features
* **Live Video Streaming:** Streams real-time webcam frames from browser to backend via low-latency WebSockets using HTML5 Canvas capture
* **Automated Penalty Detection:** A computer vision engine combining YOLO, MediaPipe hand-tracking, and OCR to automatically detect physical judge cards and hand gestures (OK, +2, DNF)
* **WCA Score Calculation:** Automated processing of raw solve times into World Cube Association (WCA) formats, including Average of 5 (ao5) and Mean of 3 (mo3) calculations
* **Real-Time Leaderboard:** Dynamic Pandas-powered leaderboard that instantly re-calculates competitor rankings, single best times, and overall averages
* **Manual Result Editing:** Integrated controls for organizers to review recorded solves, edit times entered, and manually override penalties
* **CSV Data Export:** Generate and download formatted competition results, round breakdowns, and final standings in standard CSV format
