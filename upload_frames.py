import os
import time
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
from dotenv import load_dotenv
from utils import LoggerConfig

# Set up logging
logger = LoggerConfig(name='S3 Uploader').get_logger()

# Load environment variables from .env file
load_dotenv()

# AWS S3 configuration
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
S3_REGION = os.getenv('S3_REGION', 'us-west-1')  # Default to 'us-west-1' if not specified
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
S3_ENDPOINT_URL = os.getenv('S3_ENDPOINT_URL')  # Optional: specify if using a custom S3-compatible service

# Directory paths
UPLOAD_DIR = os.path.join('data', 'to_upload')

# Initialize S3 client
s3_client_args = {
    'region_name': S3_REGION,
    'aws_access_key_id': AWS_ACCESS_KEY_ID,
    'aws_secret_access_key': AWS_SECRET_ACCESS_KEY
}

if S3_ENDPOINT_URL:
    s3_client_args['endpoint_url'] = S3_ENDPOINT_URL


def upload_files(files):
    s3_client = boto3.client('s3', **s3_client_args)

    for file_path in files:
        file_name = os.path.basename(file_path)
        try:
            logger.info(f"Uploading {file_name} to S3 bucket.")
            s3_client.upload_file(file_path, S3_BUCKET_NAME, file_name)
            logger.info(f"Successfully uploaded {file_name} to S3 bucket.")
            os.remove(file_path)
        except FileNotFoundError:
            logger.error(f"File {file_name} not found.")
        except NoCredentialsError:
            logger.critical("AWS credentials not found.")
        except PartialCredentialsError:
            logger.critical("Incomplete AWS credentials.")
        except ClientError as e:
            logger.error(f"Client error occurred: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")

    s3_client.close()

def main():
    time.sleep(15)
    while True:
        files = [os.path.join(UPLOAD_DIR, f) for f in os.listdir(UPLOAD_DIR) if os.path.isfile(os.path.join(UPLOAD_DIR, f))]
        if not files:
            logger.info("No files to upload. Sleeping for 5 minutes...")
            time.sleep(1*60)  # Sleep for 5 minutes if no files are present
            continue

        upload_files(files)

        logger.info("All files uploaded. Sleeping for 5 minutes...")
        time.sleep(300)  # Sleep for 5 minutes after uploading all files

if __name__ == "__main__":
    main()
