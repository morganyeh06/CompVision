FROM python:3.11-slim

WORKDIR /app

# Install Linux system dependencies required by MediaPipe and OpenCV
RUN apt-get update && apt-get install -y \
    libgl1 \
    libgles2 \
    libegl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY . .

# Run Uvicorn from the backend root
CMD uvicorn main:app --host 0.0.0.0 --port $PORT