# - lit depuis silver sur MinIO
# - agrège les ratings par œuvre (book_key)
# - sélectionne une édition représentative
# - calcule un score pondéré
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


def load_parquet(
    bucket: str,
    key: str,
    name: str
) -> pd.DataFrame:
    """
    Charge un fichier Parquet depuis MinIO.
    """
    logger.info(
        f"Loading {name} from s3://{bucket}/{key}"
    )

    df = read_parquet_from_s3(bucket, key)

    logger.info(
        f"{name} shape: {df.shape}"
    )

    return df

def build_book_popularity(
    books_df: pd.DataFrame,
    ratings_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Construit la table Gold de popularité au niveau œuvre.

    Les différentes éditions partageant un même book_key
    sont regroupées.
    """
    logger.info(
        "Building book popularity gold table by book_key"
    )

    # =========================
    # Agrégation par œuvre
    # =========================

    ratings_agg = (
        ratings_df
        .groupby("book_key", as_index=False)
        .agg(
            ratings_count=("rating", "count"),
            average_rating=("rating", "mean")
        )
    )

    logger.info(
        f"Aggregated works shape: {ratings_agg.shape}"
    )

    # =========================
    # Métadonnées représentatives par œuvre
    # =========================

    metadata_columns = [
        "book_key",
        "title",
        "author",
        "year_of_publication",
        "publisher",
        "image_url_s",
        "image_url_m",
        "image_url_l"
    ]

    representative_books = (
        books_df[metadata_columns]
        .drop_duplicates(subset=["book_key"])
        .copy()
    )

    logger.info(
        f"Representative works count: "
        f"{len(representative_books)}"
    )

    # =========================
    # Jointure avec la popularité
    # =========================

    gold_df = representative_books.merge(
        ratings_agg,
        on="book_key",
        how="inner"
    )

    logger.info(
        f"Gold table shape after join: {gold_df.shape}"
    )

    # =========================
    # Score pondéré
    # =========================

    gold_df["average_rating"] = (
        gold_df["average_rating"]
        .round(2)
    )

    global_mean = gold_df["average_rating"].mean()
    min_votes = 10

    gold_df["weighted_score"] = (
        (
            gold_df["ratings_count"]
            / (gold_df["ratings_count"] + min_votes)
        )
        * gold_df["average_rating"]
        +
        (
            min_votes
            / (gold_df["ratings_count"] + min_votes)
        )
        * global_mean
    ).round(2)

    # =========================
    # Tri final
    # =========================

    gold_df = gold_df.sort_values(
        by=[
            "weighted_score",
            "ratings_count"
        ],
        ascending=[
            False,
            False
        ]
    ).reset_index(drop=True)

    logger.info(
        f"Final gold table shape: {gold_df.shape}"
    )

    logger.info(
        f"Unique works with ratings: "
        f"{gold_df['book_key'].nunique()}"
    )

    return gold_df

def save_parquet(
    df: pd.DataFrame
) -> None:
    """
    Sauvegarde la table Gold dans MinIO.
    """
    logger.info(
        f"Saving gold table to "
        f"s3://{GOLD_BUCKET}/{OUTPUT_KEY}"
    )

    write_parquet_to_s3(
        df,
        GOLD_BUCKET,
        OUTPUT_KEY
    )

    logger.info("Save completed")


def main() -> None:
    try:
        books_df = load_parquet(
            SILVER_BUCKET,
            BOOKS_KEY,
            "books"
        )

        ratings_df = load_parquet(
            SILVER_BUCKET,
            RATINGS_KEY,
            "ratings_joinable"
        )

        gold_df = build_book_popularity(
            books_df,
            ratings_df
        )

        save_parquet(gold_df)

        logger.info(
            "Book popularity gold table "
            "built successfully"
        )

    except Exception as e:
        logger.error(
            f"Error while building gold table: {e}",
            exc_info=True
        )
        raise


if __name__ == "__main__":
    main()