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

logger = LoggerConfig(name='main').get_logger()

try:
    logger.info('Starting Camera-Capture')

    # Setup the RTSP stream
    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        logger.error("Failed to open camera feed")

    # MinIO client configuration (using S3 compatible API)
    s3 = boto3.client('s3',
        endpoint_url=minio_endpoint_url,  # MinIO server URL
        aws_access_key_id=minio_access_key,  # Your MinIO access key
        aws_secret_access_key=minio_secret_key,  # Your MinIO secret key
        config=Config(signature_version='s3v4'),
        region_name=minio_region_name
    )
    logger.info('MinIO client configured')

    bucket_name = 'rpi-camera'
    frame_count = 0
    frame_list = []
    frame_lock = threading.Lock()  # Lock for thread-safe access to frame_list
    upload_interval = 5 * 60  # 5 minutes in seconds

    def upload_frames():
        """Function to upload frames every 5 minutes."""
        global frame_list
        while True:
            time.sleep(upload_interval)

            # Upload frames every 5 minutes in a separate thread
            with frame_lock:
                if frame_list:
                    logger.info('Uploading frames...')
                    images_to_video(image_folder='output', output_video_name='output_video.avi')
                    video_path = os.path.join('output', 'output_video.avi')
                    s3.upload_file(video_path, bucket_name, 'output/output_video.avi')
                    logger.info('Video uploaded to MinIO!')

            # Clear the frame list
            with frame_lock:
                frame_list.clear()

    def images_to_video(image_folder='rpi-camera', output_video_name='output_video.avi', fps=30):
        # Get a list of all the files in the folder
        images = [img for img in os.listdir(image_folder) if img.endswith(".jpg") and img.startswith("output")]
        
        # Sort images by their frame number
        images.sort(key=lambda x: int(x.replace('output_', '').replace('.jpg', '')))  # Assuming filenames are like 'frame{i}.jpg'
        
        # Read the first image to get the frame size
        frame = cv2.imread(os.path.join(image_folder, images[0]))
        height, width, layers = frame.shape
        
        # Define the codec and create a VideoWriter object
        fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Codec for AVI format
        video = cv2.VideoWriter(os.path.join(image_folder, output_video_name), fourcc, fps, (width, height))
        
        # Write each image to the video
        for image in images:
            img_path = os.path.join(image_folder, image)
            frame = cv2.imread(img_path)
            video.write(frame)
        
        # Release the VideoWriter object
        video.release()
        
        # Print the output video name
        print(f"Video saved as: {output_video_name}")

    def capture_frames():
        while True:
            try:
                # Take a picture
                ret, frame = cap.read()

                # Save the image to the 'output' folder
                img_path = os.path.join('output', f'frame{frame_count}.jpg')
                cv2.imwrite(img_path, frame)

                # Add frame to the list safely
                with frame_lock:
                    logger.info('Adding frame to list...')
                    frame_list.append((img_path, f'frame{frame_count}.jpg'))
                
                # Increment frame count
                frame_count += 1

            except Exception as e:
                logger.error(f"Error occurred: {e}")
            finally:
                cap.release()

    capture_frames_thread = threading.Thread(target=capture_frames)
    upload_frames_thread = threading.Thread(target=upload_frames)

    capture_frames_thread.start()
    upload_frames_thread.start()

except Exception as e:
    logger.error(f"Error occurred: {e}")
finally:
    # Stop both threads when exiting the program
    if 'capture_frames_thread' in locals():
        capture_frames_thread.join()
    if 'upload_frames_thread' in locals():
        upload_frames_thread.join()