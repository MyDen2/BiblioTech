# Ce loader Python :

# lit les fichiers :
# - silver/books_clean.parquet
# - silver/users_clean.parquet
# - silver/ratings_joinable.parquet
# envoie les données vers Postgres,
# log le nombre de lignes chargées.

# MinIO silver/gold → pandas → PostgreSQL

import os
from sqlalchemy import create_engine, text

from src.utils.logger import setup_logger
from src.utils.s3_io import read_parquet_from_s3
from dotenv import load_dotenv
from pathlib import Path

logger = setup_logger("postgres_loader")

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / "config" / ".env"
load_dotenv(dotenv_path=ENV_PATH)

DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_PUBLIC_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB")

SILVER_BUCKET = "silver"
GOLD_BUCKET = "gold"

BOOKS_KEY = "books_clean.parquet"
USERS_KEY = "users_clean.parquet"
RATINGS_KEY = "ratings_joinable.parquet"
POPULARITY_KEY = "book_popularity.parquet"


def get_engine():
    if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]):
        raise ValueError("Missing PostgreSQL configuration in config/.env")

    url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(url)


def load_table_from_s3(bucket: str, key: str, name: str):
    logger.info(f"Loading {name} from s3://{bucket}/{key}")
    df = read_parquet_from_s3(bucket, key)
    logger.info(f"{name} shape: {df.shape}")
    return df


def truncate_tables(engine) -> None:
    logger.info("Truncating PostgreSQL tables")
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE book_popularity, ratings, users, books CASCADE;"))
    logger.info("Truncate completed")


def load_table(df, table_name: str, engine) -> None:
    logger.info(f"Loading dataframe into table '{table_name}'")
    df.to_sql(
        table_name,
        engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=5000
    )
    logger.info(f"Loaded {len(df)} rows into '{table_name}'")


def main() -> None:
    try:
        engine = get_engine()

        books_df = load_table_from_s3(SILVER_BUCKET, BOOKS_KEY, "books")
        users_df = load_table_from_s3(SILVER_BUCKET, USERS_KEY, "users")
        ratings_df = load_table_from_s3(SILVER_BUCKET, RATINGS_KEY, "ratings_joinable")
        popularity_df = load_table_from_s3(GOLD_BUCKET, POPULARITY_KEY, "book_popularity")

        truncate_tables(engine)

        load_table(books_df, "books", engine)
        load_table(users_df, "users", engine)
        load_table(ratings_df, "ratings", engine)
        load_table(popularity_df, "book_popularity", engine)

        logger.info("PostgreSQL loading completed successfully")

    except Exception as e:
        logger.error(f"Error while loading PostgreSQL tables: {e}", exc_info=True)


if __name__ == "__main__":
    main()