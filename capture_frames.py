import cv2
import os
import shutil
import time
import datetime
from dotenv import load_dotenv
from utils import LoggerConfig

# Set up logging
logger = LoggerConfig(name='Capture Frames').get_logger()

# Load environment variables from .env file
load_dotenv()

# Get the RTSP URL from environment variables
RTSP_URL = os.getenv('RTSP_URL')

# Directory paths
ACTIVE_DIR = os.path.join('data', 'active')
UPLOAD_DIR = os.path.join('data', 'to_upload')


# Ensure directories exist
os.makedirs(ACTIVE_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_current_time():
    return datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

def start_stream():
    cap = cv2.VideoCapture(RTSP_URL)
    if not cap.isOpened():
        logger.critical("Failed to open RTSP stream.")
        raise Exception("Failed to open RTSP stream.")
    logger.info("RTSP stream opened successfully.")
    return cap

def process_stream(cap):
    current_file = os.path.join(ACTIVE_DIR, f"video_{get_current_time()}.avi")
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(current_file, fourcc, 20.0, (int(cap.get(3)), int(cap.get(4))))

    logger.info(f"Started recording to file: {current_file}")
    return cap, out, current_file

def main():
    stream_cap = None
    video_writer = None
    active_file = None
    last_transfer_time = time.time()

    while True:
        if stream_cap is None or not stream_cap.isOpened():
            logger.info("Starting a new stream...")
            try:
                stream_cap = start_stream()
                stream_cap, video_writer, active_file = process_stream(stream_cap)
            except Exception as e:
                logger.error(f"Error starting stream: {e}")
                time.sleep(5)  # Wait before retrying
                continue

        ret, frame = stream_cap.read()
        if not ret:
            logger.warning("Stream read failed, restarting...")
            stream_cap.release()
            video_writer.release()
            time.sleep(5)  # Wait before retrying
            continue

        video_writer.write(frame)

        # Check if it's time to switch files
        current_time = time.time()
        if current_time - last_transfer_time >= 300:
            video_writer.release()
            shutil.move(active_file, UPLOAD_DIR)
            logger.info(f"Moved file to upload directory: {active_file}")

            # Restart video writer
            active_file = os.path.join(ACTIVE_DIR, f"video_{get_current_time()}.avi")
            video_writer = cv2.VideoWriter(active_file, cv2.VideoWriter_fourcc(*'XVID'), 20.0, (int(stream_cap.get(3)), int(stream_cap.get(4))))
            last_transfer_time = current_time

if __name__ == "__main__":
    main()