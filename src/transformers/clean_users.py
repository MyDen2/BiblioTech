import pandas as pd

from src.utils.logger import setup_logger
from src.utils.s3_io import read_csv_from_s3, write_parquet_to_s3

logger = setup_logger("clean_users")

BRONZE_BUCKET = "bronze"
BRONZE_KEY = "BX-Users.csv"

SILVER_BUCKET = "silver"
SILVER_KEY = "users_clean.parquet"


def load_users() -> pd.DataFrame:
    logger.info(f"Loading raw users from s3://{BRONZE_BUCKET}/{BRONZE_KEY}")

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


def extract_country(location: str) -> str | None:
    if pd.isna(location):
        return None

    parts = [part.strip() for part in str(location).split(",") if part.strip()]
    if not parts:
        return None

    return parts[-1]


def clean_users(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Starting users cleaning process")

    df = df.copy()
    df.columns = [col.strip().lower().replace("-", "_") for col in df.columns]
    df = df[["user_id", "location", "age"]]

    initial_count = len(df)

    df["user_id"] = pd.to_numeric(df["user_id"], errors="coerce")
    df["location"] = df["location"].astype(str).str.strip()
    df["age"] = pd.to_numeric(df["age"], errors="coerce")

    df = df.replace({"nan": pd.NA, "": pd.NA})

    df = df.dropna(subset=["user_id"])
    df = df[df["user_id"] > 0]
    df["user_id"] = df["user_id"].astype("int64")

    df["country"] = df["location"].apply(extract_country)

    df.loc[~df["age"].between(10, 100), "age"] = pd.NA

    df = df.drop_duplicates(subset=["user_id"])

    final_count = len(df)

    logger.info(f"Rows before cleaning: {initial_count}")
    logger.info(f"Rows after cleaning: {final_count}")
    logger.info(f"Removed {initial_count - final_count} rows")
    logger.info(f"Unique users: {df['user_id'].nunique()}")
    logger.info(f"Missing ages: {df['age'].isna().sum()}")
    logger.info(f"Missing countries: {df['country'].isna().sum()}")

    return df


def save_users(df: pd.DataFrame) -> None:
    logger.info(f"Saving cleaned users to s3://{SILVER_BUCKET}/{SILVER_KEY}")
    write_parquet_to_s3(df, bucket=SILVER_BUCKET, key=SILVER_KEY)
    logger.info("Save completed")


def main() -> None:
    try:
        raw_df = load_users()
        clean_df = clean_users(raw_df)
        save_users(clean_df)

        logger.info("Users ETL process completed successfully")

    except Exception as e:
        logger.error(f"Error during users ETL: {e}", exc_info=True)


if __name__ == "__main__":
    main()