import cv2
import os
import time
import shutil
from datetime import datetime
from utils import LoggerConfig
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get credentials from .env file
rtsp_url = os.getenv('RTSP_URL')

active_dir = 'data\\active'
to_upload_dir = 'data\\to_upload'
os.makedirs(active_dir, exist_ok=True)
os.makedirs(to_upload_dir, exist_ok=True)

logger = LoggerConfig(name='frame_capture').get_logger()

def connect_camera(rtsp_url: str):
    """Connect to the RTSP camera feed."""
    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        logger.error("Failed to open camera feed.")
        return None
    return cap

def format_timestamp(timestamp):
    """Format timestamp for filename."""
    return timestamp.strftime('%Y%m%d%H%M%S')

def stream_to_file(output_video_name='{}_{}.avi', fps=30, segment_duration=30):
    """Stream the camera feed into segmented video files."""
    cap = connect_camera(rtsp_url)
    if not cap:
        return

    # Get the width and height from the first frame
    ret, frame = cap.read()
    if not ret:
        logger.error("Failed to read frame from camera.")
        cap.release()
        return

    height, width, _ = frame.shape

    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    segment_start_time = time.time()
    segment_index = 0

    def get_segment_filename(start_time, end_time):
        return os.path.join(active_dir, output_video_name.format(format_timestamp(start_time), format_timestamp(end_time), segment_index))

    def update_segment_filename():
        nonlocal segment_index
        nonlocal segment_start_time
        segment_end_time = datetime.fromtimestamp(time.time())
        video.release()
        segment_index += 1
        segment_start_time = time.time()
        segment_end_time = datetime.fromtimestamp(segment_start_time)
        return get_segment_filename(segment_end_time, datetime.fromtimestamp(segment_start_time))

    segment_start_dt = datetime.fromtimestamp(segment_start_time)
    video = cv2.VideoWriter(get_segment_filename(segment_start_dt, segment_start_dt), fourcc, fps, (width, height))
    logger.info(f"Streaming to file...")

    while True:
        ret, frame = cap.read()
        if not ret:
            logger.error("Failed to read frame from camera. Exiting...")
            break

        video.write(frame)

        current_time = time.time()
        if current_time - segment_start_time >= segment_duration:
            new_filename = update_segment_filename()
            

            # Move files from active to to_upload
            for filename in os.listdir(active_dir):
                file_path = os.path.join(active_dir, filename)
                if os.path.isfile(file_path):
                    segment_end_dt = datetime.fromtimestamp(current_time)
                    
                    shutil.move(file_path, os.path.join(to_upload_dir, output_video_name.format(format_timestamp(segment_start_dt), format_timestamp(segment_end_dt), segment_index)))
                    logger.info(f"Moved {filename} to {to_upload_dir}")
                    
            video = cv2.VideoWriter(new_filename, fourcc, fps, (width, height))
            logger.info(f"Started new segment: {new_filename}")

    cap.release()
    video.release()
    logger.info("Video streaming finished.")

if __name__ == "__main__":
    try:
        logger.info('Starting Camera Stream')
        stream_to_file()
    except Exception as e:
        logger.error(f"Error occurred: {e}")
    finally:
        logger.info("Streaming stopped.")
