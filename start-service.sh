#!/bin/bash

# Change directory to the specified location
cd "~/camera-connect"

# Install requirements from requirements.txt using Python 3
python3 -m pip install -r requirements.txt

# Start two background processes using nohup to keep them running after the terminal is closed
nohup python3 capture_frames.py &
nohup python3 upload_frames.py &

# Wait for both processes to finish before exiting
wait