from pathlib import Path
import pandas as pd

from src.utils.logger import setup_logger

logger = setup_logger("quality_checks")

BOOKS_PATH = Path("data/silver/books_clean.parquet")
USERS_PATH = Path("data/silver/users_clean.parquet")
RATINGS_PATH = Path("data/silver/ratings_clean.parquet")


def load_parquet(path: Path, name: str) -> pd.DataFrame:
    logger.info(f"Loading {name} from {path}")
    df = pd.read_parquet(path)
    logger.info(f"{name} shape: {df.shape}")
    return df


def check_referential_integrity(
    ratings_df: pd.DataFrame,
    books_df: pd.DataFrame,
    users_df: pd.DataFrame
) -> None:
    logger.info("Starting referential integrity checks")

    total_ratings = len(ratings_df)

    valid_books = ratings_df["isbn"].isin(books_df["isbn"])
    valid_users = ratings_df["user_id"].isin(users_df["user_id"])

    ratings_with_valid_books = valid_books.sum()
    ratings_with_valid_users = valid_users.sum()

    orphan_book_ratings = (~valid_books).sum()
    orphan_user_ratings = (~valid_users).sum()

    valid_both = (valid_books & valid_users).sum()
    orphan_either = (~(valid_books & valid_users)).sum()

    logger.info(f"Total ratings: {total_ratings}")

    logger.info(
        f"Ratings linked to existing books: {ratings_with_valid_books} "
        f"({ratings_with_valid_books / total_ratings:.2%})"
    )
    logger.info(
        f"Ratings linked to existing users: {ratings_with_valid_users} "
        f"({ratings_with_valid_users / total_ratings:.2%})"
    )

    logger.info(
        f"Ratings with missing book reference: {orphan_book_ratings} "
        f"({orphan_book_ratings / total_ratings:.2%})"
    )
    logger.info(
        f"Ratings with missing user reference: {orphan_user_ratings} "
        f"({orphan_user_ratings / total_ratings:.2%})"
    )

    logger.info(
        f"Ratings valid on both sides: {valid_both} "
        f"({valid_both / total_ratings:.2%})"
    )
    logger.info(
        f"Ratings orphan on at least one side: {orphan_either} "
        f"({orphan_either / total_ratings:.2%})"
    )

    # couverture des clés
    logger.info(f"Unique ISBN in ratings: {ratings_df['isbn'].nunique()}")
    logger.info(f"Unique ISBN in books: {books_df['isbn'].nunique()}")
    logger.info(f"Unique user_id in ratings: {ratings_df['user_id'].nunique()}")
    logger.info(f"Unique user_id in users: {users_df['user_id'].nunique()}")


def main() -> None:
    try:
        books_df = load_parquet(BOOKS_PATH, "books")
        users_df = load_parquet(USERS_PATH, "users")
        ratings_df = load_parquet(RATINGS_PATH, "ratings")

        check_referential_integrity(ratings_df, books_df, users_df)

        logger.info("Quality checks completed successfully")

    except Exception as e:
        logger.error(f"Error during quality checks: {e}", exc_info=True)


if __name__ == "__main__":
    main()