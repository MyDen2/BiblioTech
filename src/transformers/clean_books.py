import pandas as pd

from src.utils.logger import setup_logger
from src.utils.s3_io import read_csv_from_s3, write_parquet_to_s3

logger = setup_logger("clean_books")

BRONZE_BUCKET = "bronze"
BRONZE_KEY = "BX_Books.csv"

SILVER_BUCKET = "silver"
SILVER_KEY = "books_clean.parquet"


def load_books():
    logger.info(f"Loading raw books from s3://{BRONZE_BUCKET}/{BRONZE_KEY}")

    df = read_csv_from_s3(
        bucket=BRONZE_BUCKET,
        key=BRONZE_KEY,
        sep=";",
        encoding="latin-1",
        on_bad_lines="skip",
        engine="python"
    )

    logger.info(f"Loaded dataframe shape: {df.shape}")
    return df


def clean_books(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Starting books cleaning process")

    df = df.copy()

    df.columns = [col.strip().lower().replace("-", "_") for col in df.columns]

    df = df.rename(columns={
        "book_title": "title",
        "book_author": "author",
        "year_of_publication": "year_of_publication"
    })

    df = df[[
        "isbn",
        "title",
        "author",
        "year_of_publication",
        "publisher",
        "image_url_s",
        "image_url_m",
        "image_url_l"
    ]]

    initial_count = len(df)

    df["isbn"] = df["isbn"].astype(str).str.strip().str.upper()
    df["title"] = df["title"].astype(str).str.strip()
    df["author"] = df["author"].astype(str).str.strip()
    df["publisher"] = df["publisher"].astype(str).str.strip()

    df["year_of_publication"] = pd.to_numeric(df["year_of_publication"], errors="coerce")

    df.loc[~df["year_of_publication"].between(1900, 2025), "year_of_publication"] = pd.NA

    df = df.dropna(subset=["isbn", "title", "author"])
    df = df[df["isbn"] != ""]

    df = df.drop_duplicates(subset=["isbn"])

    final_count = len(df)

    logger.info(f"Rows before cleaning: {initial_count}")
    logger.info(f"Rows after cleaning: {final_count}")
    logger.info(f"Removed {initial_count - final_count} rows")

    logger.info(f"Unique ISBN: {df['isbn'].nunique()}")
    logger.info(f"Unique authors: {df['author'].nunique()}")

    return df


def save_books(df: pd.DataFrame):
    logger.info(f"Saving cleaned books to s3://{SILVER_BUCKET}/{SILVER_KEY}")
    write_parquet_to_s3(df, bucket=SILVER_BUCKET, key=SILVER_KEY)
    logger.info("Save completed")


def main():
    try:
        raw_df = load_books()
        clean_df = clean_books(raw_df)
        save_books(clean_df)

        logger.info("Books ETL process completed successfully")

    except Exception as e:
        logger.error(f"Error during books ETL: {e}", exc_info=True)


if __name__ == "__main__":
    main()