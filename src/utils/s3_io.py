from io import BytesIO
from pathlib import Path
import os
from io import BytesIO

import boto3
import pandas as pd
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / "config" / ".env"
load_dotenv(dotenv_path=ENV_PATH)

MINIO_ENDPOINT = os.getenv("MINIO_PUBLIC_ENDPOINT", "http://localhost:9000")
MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER")
MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD")


def get_s3_client():
    if not MINIO_ROOT_USER or not MINIO_ROOT_PASSWORD:
        raise ValueError("Missing MinIO credentials in config/.env")

    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ROOT_USER,
        aws_secret_access_key=MINIO_ROOT_PASSWORD,
    )


def list_objects(bucket: str, prefix: str = "") -> list[str]:
    s3 = get_s3_client()
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)

    if "Contents" not in response:
        return []

    return [obj["Key"] for obj in response["Contents"]]


def read_csv_from_s3(bucket: str, key: str, **kwargs) -> pd.DataFrame:
    s3 = get_s3_client()
    obj = s3.get_object(Bucket=bucket, Key=key)
    data = obj["Body"].read()
    buffer = BytesIO(data)
    return pd.read_csv(buffer, **kwargs)


def read_parquet_from_s3(bucket: str, key: str) -> pd.DataFrame:
    s3 = get_s3_client()
    obj = s3.get_object(Bucket=bucket, Key=key)
    buffer = BytesIO(obj["Body"].read())
    return pd.read_parquet(buffer)


def write_parquet_to_s3(df: pd.DataFrame, bucket: str, key: str) -> None:
    s3 = get_s3_client()
    buffer = BytesIO()
    df.to_parquet(buffer, index=False)
    buffer.seek(0)

    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=buffer.getvalue(),
        ContentType="application/octet-stream"
    )