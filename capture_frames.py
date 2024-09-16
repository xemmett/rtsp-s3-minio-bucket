import os
import cv2
import numpy as np
import imutils
from datetime import datetime
from dotenv import load_dotenv
from utils import LoggerConfig
import shutil
import time

# =============================================================================
# USER-SET PARAMETERS
# =============================================================================

FRAMES_TO_PERSIST = 10
MIN_SIZE_FOR_MOVEMENT = 2000
MOVEMENT_DETECTED_PERSISTENCE = 100
VIDEO_OUTPUT_DIR = 'data/active'
UPLOAD_DIR = 'data/to_upload'
TEMP_DIR = 'data/temp'

# =============================================================================
# CORE PROGRAM
# =============================================================================

# Set up logging
logger = LoggerConfig(name='Capture Frames').get_logger()

# Load environment variables
load_dotenv()
RTSP_URL = os.getenv('RTSP_URL')

# Create capture object
cap = cv2.VideoCapture(RTSP_URL)
if not cap.isOpened():
    logger.error("Unable to open video stream")
    exit()

first_frame = None
next_frame = None
font = cv2.FONT_HERSHEY_SIMPLEX
delay_counter = 0
movement_persistent_counter = 0
recording = False
video_writer = None
output_filename = None

# Ensure output directories exist
os.makedirs(VIDEO_OUTPUT_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

while True:
    transient_movement_flag = False
    ret, frame = cap.read()

    if not ret:
        logger.error("Error capturing frame")
        continue

    frame = imutils.resize(frame, width=750)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    if first_frame is None:
        first_frame = gray

    delay_counter += 1
    if delay_counter > FRAMES_TO_PERSIST:
        delay_counter = 0
        first_frame = next_frame

    next_frame = gray
    frame_delta = cv2.absdiff(first_frame, next_frame)
    thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)
    cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for c in cnts:
        (x, y, w, h) = cv2.boundingRect(c)
        if cv2.contourArea(c) > MIN_SIZE_FOR_MOVEMENT:
            transient_movement_flag = True
            # cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2) # draw rectange

    if transient_movement_flag:
        movement_persistent_flag = True
        movement_persistent_counter = MOVEMENT_DETECTED_PERSISTENCE
        if not recording:
            # Start recording with proper error handling
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = os.path.join(TEMP_DIR, f"{timestamp}.avi")
            
            # Try different codecs
            fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Use MJPG or H264
            video_writer = cv2.VideoWriter(output_filename, fourcc, 20.0, (frame.shape[1], frame.shape[0]))
            
            # Ensure the VideoWriter is opened properly
            if not video_writer.isOpened():
                logger.error(f"Failed to open VideoWriter for {output_filename}")
                recording = False
            else:
                recording = True
                logger.info(f"Started recording: {output_filename}")
    
    if recording:
        video_writer.write(frame)

    if movement_persistent_counter > 0:
        text = f"Movement Detected {movement_persistent_counter}"
        movement_persistent_counter -= 1
    else:
        text = "No Movement Detected"
        if recording:
            video_writer.release()
            # Finalize the video file before moving it
            time.sleep(1)
            shutil.move(output_filename, os.path.join(UPLOAD_DIR, os.path.basename(output_filename)))
            logger.info(f"Recording stopped and file moved: {output_filename}")
            recording = False

    cv2.putText(frame, text, (10, 35), font, 0.75, (255, 255, 255), 2, cv2.LINE_AA)
    frame_delta = cv2.cvtColor(frame_delta, cv2.COLOR_GRAY2BGR)
    # cv2.imshow("frame", np.hstack((frame_delta, frame))) # add to view what motion viewer sees.

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Final cleanup
if recording and video_writer:
    video_writer.release()
    time.sleep(1)
    shutil.move(output_filename, os.path.join(UPLOAD_DIR, os.path.basename(output_filename)))

cap.release()
cv2.destroyAllWindows()
