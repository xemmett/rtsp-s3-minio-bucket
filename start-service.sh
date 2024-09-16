#!/bin/bash

# Change directory to the current location
cd "$(pwd)"

# Install requirements from requirements.txt using Python 3 in an unmanaged virtual environment
# python3 -m venv env
# source env/bin/activate
# pip install -r requirements.txt

# Start two background processes using nohup to keep them running after the terminal is closed
python3 capture_frames.py &
python3 upload_frames.py &

# Wait for both processes to finish before exiting
wait