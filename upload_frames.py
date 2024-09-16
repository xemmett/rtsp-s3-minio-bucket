import os
import time
import boto3
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

to_upload_dir = os.path.join('data', 'to_upload')
logger = LoggerConfig(name='upload_frames').get_logger()

def upload_file(s3, bucket_name, file_path):
    """Upload a file to MinIO."""
    s3.upload_file(file_path, bucket_name, os.path.basename(file_path))
    logger.info(f"Uploaded {file_path} to MinIO!")

def upload_files(s3, bucket_name, upload_interval=5):
    """Upload video files to MinIO every interval."""
    while True:
        time.sleep(upload_interval)

        files_to_upload = [f for f in os.listdir(to_upload_dir) if f.endswith('.avi')]
        for file in files_to_upload:
            file_path = os.path.join(to_upload_dir, file)
            logger.info(f"Uploading {file_path} to MinIO.")
            upload_file(s3, bucket_name, file_path)
            os.remove(file_path)  # Remove the file after uploading

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
        upload_files(s3, bucket_name)

    except Exception as e:
        logger.error(f"Error occurred: {e}")
    finally:
        logger.info("Upload process stopped.")
