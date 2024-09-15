import cv2
import boto3
import os
import time
import threading
from botocore.client import Config
from utils import LoggerConfig
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get credentials from .env file
minio_endpoint_url = os.getenv('MINIO_ENDPOINT_URL')
minio_access_key = os.getenv('MINIO_ACCESS_KEY')
minio_secret_key = os.getenv('MINIO_SECRET_KEY')
minio_region_name = os.getenv('MINIO_REGION_NAME')
rtsp_url = os.getenv('RTSP_URL')

data_dir = 'output'
os.makedirs(data_dir, exist_ok=True)

logger = LoggerConfig(name='main').get_logger()

# Global flag to stop threads gracefully
stop_event = threading.Event()

def images_to_video(image_folder='output', output_video_name='output_video.avi', fps=30):
    """Convert images to a video."""
    images = [img for img in os.listdir(image_folder) if img.endswith(".jpg") and img.startswith("frame")]
    images.sort(key=lambda x: int(x.replace('frame_', '').replace('.jpg', '')))  # Sort images by frame number

    if not images:
        logger.warning("No images found for video creation.")
        return None

    first_image_path = os.path.join(image_folder, images[0])
    frame = cv2.imread(first_image_path)
    height, width, layers = frame.shape

    # Define the codec and create a VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    video = cv2.VideoWriter(os.path.join(image_folder, output_video_name), fourcc, fps, (width, height))

    for image in images:
        img_path = os.path.join(image_folder, image)
        frame = cv2.imread(img_path)
        video.write(frame)

    video.release()
    logger.info(f"Video saved as {output_video_name}")
    return os.path.join(image_folder, output_video_name)

def capture_frames(frame_lock, frame_list):
    
    cap = connect_camera(rtsp_url)

    frame_count = 0
    retry = 0
    max_retry = 5
    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            logger.error("Failed to read frame from camera. Retrying in 5s...")
            retry += 1

            if retry == max_retry:
                logger.critical('Failed to read frame from camera, max retries reached.')
                logger.info('Sleeping for five minutes.')
                time.sleep(5*60)

            time.sleep(5)
            cap = connect_camera(rtsp_url)
            continue
            
        img_path = os.path.join(data_dir, f'frame_{frame_count}.jpg')
        cv2.imwrite(img_path, frame)

        with frame_lock:
            frame_list.append(img_path)

        frame_count += 1
        time.sleep(1)  # Adjust capture interval if needed
    
    cap.release()

def upload_frames(s3, bucket_name, frame_lock, frame_list, upload_interval=5*60):
    while not stop_event.is_set():
        time.sleep(upload_interval)

        with frame_lock:
            if frame_list:
                logger.info('Uploading frames...')
                frame_range = (frame_list[0].split('_')[1].replace('.jpg', ''), frame_list[-1].split('_')[1].replace('.jpg', ''))
                video_path = images_to_video(image_folder='output', output_video_name=f'{frame_range[0]}-{frame_range[1]}-video.avi')
                if video_path:
                    s3.upload_file(video_path, bucket_name, os.path.basename(video_path))
                    logger.info('Video uploaded to MinIO!')

                frame_list.clear()

def connect_camera(rtsp_url: str):

    # Setup the RTSP stream
    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        logger.error("Failed to open camera feed.")
        return
    
    return cap

def main():
    try:
        logger.info('Starting Camera-Connect')

        # MinIO client configuration (using S3 compatible API)
        s3 = boto3.client('s3',
            endpoint_url=minio_endpoint_url,
            aws_access_key_id=minio_access_key,
            aws_secret_access_key=minio_secret_key,
            config=Config(signature_version='s3v4'),
            region_name=minio_region_name
        )
        logger.info('MinIO client configured')

        bucket_name = 'rpi-camera'
        frame_list = []
        frame_lock = threading.Lock()  # Thread-safe access to frame_list

        # Start threads for capturing frames and uploading them
        capture_thread = threading.Thread(target=capture_frames, args=(frame_lock, frame_list))
        logger.info('Started Camera Thread...')
        upload_thread = threading.Thread(target=upload_frames, args=(s3, bucket_name, frame_lock, frame_list))
        logger.info('Started Upload Thread...')

        capture_thread.start()
        upload_thread.start()

        # Wait for keyboard interrupt to stop
        while True:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received, stopping...")
                stop_event.set()
                break

        # Join threads when done
        capture_thread.join()
        upload_thread.join()

    except Exception as e:
        logger.error(f"Error occurred: {e}")
    finally:
        logger.info("Capture released.")

if __name__ == "__main__":
    main()
