#!/bin/bash

# Continuous loop
while true
do
    # Log start time
    echo "Checking frame capture and upload scripts at $(date)"

    # Check if frame capture script is still running
    if ps -p $frame_capture_pid > /dev/null 2>&1
    then
        echo "Frame capture script is still running"
    else
        echo "Frame capture script has finished or crashed, restarting..."
        python3 capture_frames.py &
        frame_capture_pid=$!
    fi

    # Check if upload script is still running
    if ps -p $upload_pid > /dev/null 2>&1
    then
        echo "Upload script is still running"
    else
        echo "Upload script has finished or crashed, restarting..."
        python3 upload_frames.py &
        upload_pid=$!
    fi

    # Wait 10 minutes before checking again
    sleep 600
done
