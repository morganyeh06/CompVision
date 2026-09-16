# CompVision
CompVision is an automated data entry and score-taking system for speedcubing competitions. By analyzing live webcam feeds, the application automatically reads solve times from displays and detects solve penalties (+2s, DNF) via hand gestures or physical judge cards.

**Link:** https://comp-vision-one.vercel.app/

## Architecture & Tech Stack

### **Frontend**
* **Framework:** React + TypeScript (Vite)
* **Styling:** Bootstrap CSS
* **Deployment:** Vercel

### **Backend & Computer Vision Engine**
* **API / WebSocket:** FastAPI + Uvicorn
* **Hand Gesture Detection:** MediaPipe Task Vision API
* **Object Detection & Model Execution:** YOLO / ONNX Runtime
* **Text Recognition (OCR):** EasyOCR
* **Data Processing:** Pandas
* **Containerization & Hosting:** Docker on Google Cloud Run

## Features
* **Live Video Streaming:** Streams real-time webcam frames from browser to backend via low-latency WebSockets using HTML5 Canvas capture
* **Automated Penalty Detection:** A computer vision engine combining YOLO, MediaPipe hand-tracking, and OCR to automatically detect physical judge cards and hand gestures (OK, +2, DNF)
* **WCA Score Calculation:** Automated processing of raw solve times into World Cube Association (WCA) formats, including Average of 5 (ao5) and Mean of 3 (mo3) calculations
* **Real-Time Leaderboard:** Dynamic Pandas-powered leaderboard that instantly re-calculates competitor rankings, single best times, and overall averages
* **Manual Result Editing:** Integrated controls for organizers to review recorded solves, edit times entered, and manually override penalties
* **CSV Data Export:** Generate and download formatted competition results, round breakdowns, and final standings in standard CSV format
