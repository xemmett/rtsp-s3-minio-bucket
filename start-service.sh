#!/bin/bash

# Activate the virtual environment (if needed)
# source venv/bin/activate

# Log start time
echo "Starting frame capture and upload scripts at $(date)"

# Start frame capture
echo "Starting frame capture script..."
python3 capture_frames.py &

# Start upload script
echo "Starting upload frames script..."
python3 upload_frames.py &

# Wait for both processes to end
wait

# Log end time
echo "Both scripts finished running at $(date)"
