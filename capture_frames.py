import cv2
import os
import time
from utils import LoggerConfig
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get credentials from .env file
rtsp_url = os.getenv('RTSP_URL')

data_dir = 'output'
os.makedirs(data_dir, exist_ok=True)

logger = LoggerConfig(name='frame_capture').get_logger()

def connect_camera(rtsp_url: str):
    """Connect to the RTSP camera feed."""
    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        logger.error("Failed to open camera feed.")
        return None
    return cap

def capture_frames():
    """Capture frames from the RTSP stream."""
    cap = connect_camera(rtsp_url)

    if not cap:
        return

    frame_count = 0
    retry = 0
    max_retry = 5
    while True:
        ret, frame = cap.read()
        if not ret:
            logger.error("Failed to read frame from camera. Retrying in 5s...")
            retry += 1

            if retry == max_retry:
                logger.critical('Failed to read frame from camera, max retries reached.')
                logger.info('Sleeping for five minutes.')
                time.sleep(5*60)
                retry = 0

            time.sleep(5)
            cap = connect_camera(rtsp_url)
            continue

        img_path = os.path.join(data_dir, f'frame_{frame_count}.jpg')
        cv2.imwrite(img_path, frame)

        frame_count += 1
        time.sleep(1)  # Adjust capture interval if needed

    cap.release()

if __name__ == "__main__":
    try:
        logger.info('Starting Camera-Connect')
        capture_frames()
    except Exception as e:
        logger.error(f"Error occurred: {e}")
    finally:
        logger.info("Capture stopped.")
