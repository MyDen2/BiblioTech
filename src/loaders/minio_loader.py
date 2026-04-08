from pathlib import Path
import boto3
import os 
from dotenv import load_dotenv
from src.utils.logger import setup_logger

logger = setup_logger("minio_loader")

# Config MinIO
load_dotenv("config/.env")
MINIO_ENDPOINT = "http://localhost:9000"
ACCESS_KEY = os.getenv("MINIO_ROOT_USER")
SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD")
logger.info(f"MINIO_ROOT_USER={ACCESS_KEY}")
logger.info(f"MINIO_ROOT_PASSWORD={'SET' if SECRET_KEY else 'MISSING'}")
# Buckets
BUCKETS = ["bronze", "silver", "gold"]

# Paths locaux
DATA_PATH = Path("data")


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY
    )


def create_bucket_if_not_exists(s3, bucket_name):
    existing_buckets = [b["Name"] for b in s3.list_buckets()["Buckets"]]

    if bucket_name not in existing_buckets:
        logger.info(f"Creating bucket: {bucket_name}")
        s3.create_bucket(Bucket=bucket_name)
    else:
        logger.info(f"Bucket already exists: {bucket_name}")


def upload_file(s3, file_path: Path, bucket: str, object_name: str):
    logger.info(f"Uploading {file_path} to {bucket}/{object_name}")
    s3.upload_file(str(file_path), bucket, object_name)


def upload_folder(s3, folder_path: Path, bucket: str):
    logger.info(f"Uploading folder {folder_path} to bucket {bucket}")

    for file_path in folder_path.rglob("*"):
        if file_path.is_file():
            relative_path = file_path.relative_to(folder_path)
            upload_file(s3, file_path, bucket, str(relative_path))


def main():
    try:
        s3 = get_s3_client()

        # Créer les buckets
        for bucket in BUCKETS:
            create_bucket_if_not_exists(s3, bucket)

        # Upload bronze / silver / gold
        for layer in BUCKETS:
            folder_path = DATA_PATH / layer

            if folder_path.exists():
                upload_folder(s3, folder_path, layer)
            else:
                logger.warning(f"Folder not found: {folder_path}")

        logger.info("MinIO upload completed successfully")

    except Exception as e:
        logger.error(f"Error during MinIO upload: {e}", exc_info=True)


if __name__ == "__main__":
    main()