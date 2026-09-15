FROM python:3.11-slim

WORKDIR /app

# install Linux system dependencies required by MediaPipe and OpenCV
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libgles2 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy backend application code
COPY . .

# run uvicorn from the backend root
CMD uvicorn main:app --host 0.0.0.0 --port $PORT