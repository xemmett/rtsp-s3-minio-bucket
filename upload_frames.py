import os
import time
import boto3
from botocore.client import Config
from utils import LoggerConfig
from dotenv import load_dotenv
import cv2

# Load environment variables from .env file
load_dotenv()

# Get credentials from .env file
minio_endpoint_url = os.getenv('MINIO_ENDPOINT_URL')
minio_access_key = os.getenv('MINIO_ACCESS_KEY')
minio_secret_key = os.getenv('MINIO_SECRET_KEY')
minio_region_name = os.getenv('MINIO_REGION_NAME')

data_dir = 'output'
logger = LoggerConfig(name='upload_frames').get_logger()

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

def upload_frames(s3, bucket_name, upload_interval=5*60):
    """Upload frames as a video to MinIO."""
    while True:
        time.sleep(upload_interval)

        frame_list = [img for img in os.listdir(data_dir) if img.endswith(".jpg") and img.startswith("frame")]
        if frame_list:
            logger.info('Uploading frames...')
            frame_range = (frame_list[0].split('_')[1].replace('.jpg', ''), frame_list[-1].split('_')[1].replace('.jpg', ''))
            video_path = images_to_video(image_folder='output', output_video_name=f'{frame_range[0]}-{frame_range[1]}-video.avi')
            if video_path:
                s3.upload_file(video_path, bucket_name, os.path.basename(video_path))
                logger.info('Video uploaded to MinIO!')

            # Clear frames after video creation
            for frame in frame_list:
                os.remove(os.path.join(data_dir, frame))

if __name__ == "__main__":
    try:
        logger.info('Starting Upload Process')

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

        # Start the upload process
        upload_frames(s3, bucket_name)

    except Exception as e:
        logger.error(f"Error occurred: {e}")
    finally:
        logger.info("Upload process stopped.")
