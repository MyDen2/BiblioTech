# - lit depuis silver sur MinIO
# - agrège :
    # count(rating)
    # mean(rating)
# - joint avec les métadonnées livres
# - écrit dans gold sur MinIO

import pandas as pd

from src.utils.logger import setup_logger
from src.utils.s3_io import read_parquet_from_s3, write_parquet_to_s3

logger = setup_logger("build_book_popularity")

SILVER_BUCKET = "silver"
GOLD_BUCKET = "gold"

BOOKS_KEY = "books_clean.parquet"
RATINGS_KEY = "ratings_joinable.parquet"
OUTPUT_KEY = "book_popularity.parquet"


def load_parquet(bucket: str, key: str, name: str) -> pd.DataFrame:
    logger.info(f"Loading {name} from s3://{bucket}/{key}")
    df = read_parquet_from_s3(bucket, key)
    logger.info(f"{name} shape: {df.shape}")
    return df


def build_book_popularity(books_df: pd.DataFrame, ratings_df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Building book popularity gold table")

    ratings_agg = (
        ratings_df
        .groupby("isbn", as_index=False)
        .agg(
            ratings_count=("rating", "count"),
            average_rating=("rating", "mean")
        )
    )

    logger.info(f"Aggregated ratings shape: {ratings_agg.shape}")

    gold_df = books_df.merge(ratings_agg, on="isbn", how="inner")
    logger.info(f"Gold table shape after join: {gold_df.shape}")

    gold_df["average_rating"] = gold_df["average_rating"].round(2)

    global_mean = gold_df["average_rating"].mean()
    min_votes = 10

    gold_df["weighted_score"] = (
        (gold_df["ratings_count"] / (gold_df["ratings_count"] + min_votes)) * gold_df["average_rating"]
        + (min_votes / (gold_df["ratings_count"] + min_votes)) * global_mean
    ).round(2)

    gold_df = gold_df.sort_values(
        by=["weighted_score", "ratings_count"],
        ascending=[False, False]
    ).reset_index(drop=True)

    logger.info(f"Final gold table shape: {gold_df.shape}")
    logger.info(f"Books with ratings: {gold_df['isbn'].nunique()}")

    return gold_df


def save_parquet(df: pd.DataFrame) -> None:
    logger.info(f"Saving gold table to s3://{GOLD_BUCKET}/{OUTPUT_KEY}")
    write_parquet_to_s3(df, GOLD_BUCKET, OUTPUT_KEY)
    logger.info("Save completed")


def main() -> None:
    try:
        books_df = load_parquet(SILVER_BUCKET, BOOKS_KEY, "books")
        ratings_df = load_parquet(SILVER_BUCKET, RATINGS_KEY, "ratings_joinable")

        gold_df = build_book_popularity(books_df, ratings_df)
        save_parquet(gold_df)

        logger.info("Book popularity gold table built successfully")

    except Exception as e:
        logger.error(f"Error while building gold table: {e}", exc_info=True)


if __name__ == "__main__":
    main()