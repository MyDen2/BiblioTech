# from pathlib import Path
# import pandas as pd

# from src.utils.logger import setup_logger

# # Logger
# logger = setup_logger("clean_ratings")

# BRONZE_PATH = Path("data/bronze/BX-Book-Ratings.csv")
# SILVER_PATH = Path("data/silver/ratings_clean.parquet")


# def load_ratings(csv_path: Path) -> pd.DataFrame:
#     logger.info(f"Loading raw ratings from {csv_path}")

#     df = pd.read_csv(
#         csv_path,
#         sep=";",
#         encoding="latin-1",  ## question : pourquoi ? 
#         on_bad_lines="skip"
#     )

#     logger.info(f"Loaded dataframe shape: {df.shape}")
#     return df


# def clean_ratings(df: pd.DataFrame) -> pd.DataFrame:
#     logger.info("Starting cleaning process")

#     df = df.copy()

#     df.columns = [col.strip().lower().replace("-", "_") for col in df.columns]

#     df = df.rename(columns={
#         "user_id": "user_id",
#         "isbn": "isbn",
#         "book_rating": "rating"
#     })

#     df = df[["user_id", "isbn", "rating"]]

#     initial_count = len(df)

#     df["user_id"] = pd.to_numeric(df["user_id"], errors="coerce")
#     df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
#     df["isbn"] = df["isbn"].astype(str).str.strip().str.upper()

#     df = df.dropna(subset=["user_id", "isbn", "rating"])
#     df = df[df["isbn"] != ""]
#     df = df[df["user_id"] > 0]

#     # filtrage explicite
#     df = df[df["rating"] > 0]
#     df = df[df["rating"].between(1, 10)]

#     df["user_id"] = df["user_id"].astype("int64")
#     df["rating"] = df["rating"].astype("int64")

#     df = df.drop_duplicates(subset=["user_id", "isbn"])

#     final_count = len(df)

#     logger.info(f"Rows before cleaning: {initial_count}")
#     logger.info(f"Rows after cleaning: {final_count}")
#     logger.info(f"Removed {initial_count - final_count} rows")

#     logger.info(f"Unique users: {df['user_id'].nunique()}")
#     logger.info(f"Unique books: {df['isbn'].nunique()}")

#     return df


# def save_parquet(df: pd.DataFrame, output_path: Path) -> None:
#     logger.info(f"Saving cleaned data to {output_path}")

#     output_path.parent.mkdir(parents=True, exist_ok=True)
#     df.to_parquet(output_path, index=False)

#     logger.info("Save completed")


# def main():
#     try:
#         df_raw = load_ratings(BRONZE_PATH)
#         df_clean = clean_ratings(df_raw)
#         save_parquet(df_clean, SILVER_PATH)

#         logger.info("ETL process completed successfully")

#     except Exception as e:
#         logger.error(f"Error during ETL: {e}", exc_info=True)


# if __name__ == "__main__":
#     main()

import pandas as pd

from src.utils.logger import setup_logger
from src.utils.s3_io import read_csv_from_s3, write_parquet_to_s3

logger = setup_logger("clean_ratings")

BRONZE_BUCKET = "bronze"
BRONZE_KEY = "BX-Book-Ratings.csv"

SILVER_BUCKET = "silver"
SILVER_KEY = "ratings_clean.parquet"


def load_ratings() -> pd.DataFrame:
    logger.info(f"Loading raw ratings from s3://{BRONZE_BUCKET}/{BRONZE_KEY}")

    df = read_csv_from_s3(
        bucket=BRONZE_BUCKET,
        key=BRONZE_KEY,
        sep=";",
        encoding="latin-1",
        on_bad_lines="skip"
    )

    logger.info(f"Loaded dataframe shape: {df.shape}")
    return df


def clean_ratings(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Starting cleaning process")

    df = df.copy()

    df.columns = [col.strip().lower().replace("-", "_") for col in df.columns]
    df = df.rename(columns={"book_rating": "rating"})
    df = df[["user_id", "isbn", "rating"]]

    initial_count = len(df)

    df["user_id"] = pd.to_numeric(df["user_id"], errors="coerce")
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df["isbn"] = df["isbn"].astype(str).str.strip().str.upper()

    df = df.dropna(subset=["user_id", "isbn", "rating"])
    df = df[df["isbn"] != ""]
    df = df[df["user_id"] > 0]

    # On garde seulement les ratings explicites
    df = df[df["rating"] > 0]
    df = df[df["rating"].between(1, 10)]

    df["user_id"] = df["user_id"].astype("int64")
    df["rating"] = df["rating"].astype("int64")

    df = df.drop_duplicates(subset=["user_id", "isbn"])

    final_count = len(df)

    logger.info(f"Rows before cleaning: {initial_count}")
    logger.info(f"Rows after cleaning: {final_count}")
    logger.info(f"Removed {initial_count - final_count} rows")
    logger.info(f"Unique users: {df['user_id'].nunique()}")
    logger.info(f"Unique books: {df['isbn'].nunique()}")

    return df


def save_ratings(df: pd.DataFrame) -> None:
    logger.info(f"Saving cleaned ratings to s3://{SILVER_BUCKET}/{SILVER_KEY}")
    write_parquet_to_s3(df, bucket=SILVER_BUCKET, key=SILVER_KEY)
    logger.info("Save completed")


def main() -> None:
    try:
        raw_df = load_ratings()
        clean_df = clean_ratings(raw_df)
        save_ratings(clean_df)

        logger.info("ETL process completed successfully")

    except Exception as e:
        logger.error(f"Error during ETL: {e}", exc_info=True)


if __name__ == "__main__":
    main()