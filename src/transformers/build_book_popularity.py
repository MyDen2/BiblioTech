# - charge books_clean.parquet
# - charge ratings_joinable.parquet
# - agrège :
    # count(rating)
    # mean(rating)
# - joint avec les métadonnées livres
# - exporte en data/gold/book_popularity.parquet

from pathlib import Path
import pandas as pd

from src.utils.logger import setup_logger

logger = setup_logger("build_book_popularity")

BOOKS_PATH = Path("data/silver/books_clean.parquet")
RATINGS_PATH = Path("data/silver/ratings_joinable.parquet")
OUTPUT_PATH = Path("data/gold/book_popularity.parquet")


def load_parquet(path: Path, name: str) -> pd.DataFrame:
    logger.info(f"Loading {name} from {path}")
    df = pd.read_parquet(path)
    logger.info(f"{name} shape: {df.shape}")
    return df


def build_book_popularity(books_df: pd.DataFrame, ratings_df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Building book popularity gold table")

    # Agrégation ratings par livre
    ratings_agg = (
        ratings_df
        .groupby("isbn", as_index=False)
        .agg(
            ratings_count=("rating", "count"),
            average_rating=("rating", "mean")
        )
    )

    logger.info(f"Aggregated ratings shape: {ratings_agg.shape}")

    # Jointure avec métadonnées livres
    gold_df = books_df.merge(ratings_agg, on="isbn", how="inner")

    logger.info(f"Gold table shape after join: {gold_df.shape}")

    # Arrondir note moyenne
    gold_df["average_rating"] = gold_df["average_rating"].round(2)

    # Score pondéré simple
    global_mean = gold_df["average_rating"].mean()
    min_votes = 10

    gold_df["weighted_score"] = (
        (gold_df["ratings_count"] / (gold_df["ratings_count"] + min_votes)) * gold_df["average_rating"]
        + (min_votes / (gold_df["ratings_count"] + min_votes)) * global_mean
    ).round(2)

    # Tri utile
    gold_df = gold_df.sort_values(
        by=["weighted_score", "ratings_count"],
        ascending=[False, False]
    ).reset_index(drop=True)

    logger.info(f"Final gold table shape: {gold_df.shape}")
    logger.info(f"Books with ratings: {gold_df['isbn'].nunique()}")

    return gold_df


def save_parquet(df: pd.DataFrame, output_path: Path) -> None:
    logger.info(f"Saving gold table to {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    logger.info("Save completed")


def main() -> None:
    try:
        books_df = load_parquet(BOOKS_PATH, "books")
        ratings_df = load_parquet(RATINGS_PATH, "ratings_joinable")

        gold_df = build_book_popularity(books_df, ratings_df)
        save_parquet(gold_df, OUTPUT_PATH)

        logger.info("Book popularity gold table built successfully")

    except Exception as e:
        logger.error(f"Error while building gold table: {e}", exc_info=True)


if __name__ == "__main__":
    main()