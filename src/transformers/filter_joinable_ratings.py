from pathlib import Path
import pandas as pd

from src.utils.logger import setup_logger

logger = setup_logger("filter_joinable_ratings")

BOOKS_PATH = Path("data/silver/books_clean.parquet")
USERS_PATH = Path("data/silver/users_clean.parquet")
RATINGS_PATH = Path("data/silver/ratings_clean.parquet")
OUTPUT_PATH = Path("data/silver/ratings_joinable.parquet")


def load_parquet(path: Path, name: str) -> pd.DataFrame:
    logger.info(f"Loading {name} from {path}")
    df = pd.read_parquet(path)
    logger.info(f"{name} shape: {df.shape}")
    return df


def filter_joinable_ratings(
    ratings_df: pd.DataFrame,
    books_df: pd.DataFrame,
    users_df: pd.DataFrame
) -> pd.DataFrame:
    logger.info("Filtering joinable ratings")

    initial_count = len(ratings_df)

    valid_books_mask = ratings_df["isbn"].isin(books_df["isbn"])
    valid_users_mask = ratings_df["user_id"].isin(users_df["user_id"])

    filtered_df = ratings_df[valid_books_mask & valid_users_mask].copy()

    final_count = len(filtered_df)

    logger.info(f"Rows before filtering: {initial_count}")
    logger.info(f"Rows after filtering: {final_count}")
    logger.info(f"Removed {initial_count - final_count} orphan ratings")

    logger.info(f"Unique users kept: {filtered_df['user_id'].nunique()}")
    logger.info(f"Unique books kept: {filtered_df['isbn'].nunique()}")

    return filtered_df


def save_parquet(df: pd.DataFrame, output_path: Path) -> None:
    logger.info(f"Saving joinable ratings to {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    logger.info("Save completed")


def main() -> None:
    try:
        books_df = load_parquet(BOOKS_PATH, "books")
        users_df = load_parquet(USERS_PATH, "users")
        ratings_df = load_parquet(RATINGS_PATH, "ratings")

        joinable_df = filter_joinable_ratings(ratings_df, books_df, users_df)
        save_parquet(joinable_df, OUTPUT_PATH)

        logger.info("Joinable ratings filtering completed successfully")

    except Exception as e:
        logger.error(f"Error during joinable ratings filtering: {e}", exc_info=True)


if __name__ == "__main__":
    main()