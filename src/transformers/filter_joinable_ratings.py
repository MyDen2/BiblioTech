# Ce fihier a pour but de :
# - lire books_clean.parquet, users_clean.parquet, ratings_clean.parquet depuis silver
# - filtrer les ratings joignables
# - rattacher chaque rating à une œuvre via book_key
# - agréger les ratings au niveau user_id + book_key
# - écrire ratings_joinable.parquet dans silver

import pandas as pd

from src.utils.logger import setup_logger
from src.utils.s3_io import read_parquet_from_s3, write_parquet_to_s3

logger = setup_logger("filter_joinable_ratings")

SILVER_BUCKET = "silver"

BOOKS_KEY = "books_clean.parquet"
USERS_KEY = "users_clean.parquet"
RATINGS_KEY = "ratings_clean.parquet"
OUTPUT_KEY = "ratings_joinable.parquet"


def load_parquet(key: str, name: str) -> pd.DataFrame:
    logger.info(f"Loading {name} from s3://{SILVER_BUCKET}/{key}")

    df = read_parquet_from_s3(
        SILVER_BUCKET,
        key
    )

    logger.info(f"{name} shape: {df.shape}")

    return df


def filter_joinable_ratings(
    ratings_df: pd.DataFrame,
    books_df: pd.DataFrame,
    users_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Conserve uniquement les ratings associés à un utilisateur
    et à un livre existants.

    Ajoute également book_key afin de rattacher chaque rating
    à l'œuvre correspondante et non uniquement à son édition ISBN.
    """
    logger.info("Filtering joinable ratings")

    initial_count = len(ratings_df)

    # =========================
    # Filtrage utilisateurs
    # =========================

    valid_users_mask = ratings_df["user_id"].isin(
        users_df["user_id"]
    )

    ratings_df = ratings_df[
        valid_users_mask
    ].copy()

    # =========================
    # Jointure avec les livres
    # =========================

    books_mapping = books_df[
        [
            "isbn",
            "book_key"
        ]
    ].drop_duplicates(
        subset=["isbn"]
    )

    filtered_df = ratings_df.merge(
        books_mapping,
        on="isbn",
        how="inner"
    )

    # =========================
    # Agrégation au niveau œuvre
    # =========================

    filtered_df = (
        filtered_df
        .groupby(
            ["user_id", "book_key"],
            as_index=False
        )
        .agg(
            rating=("rating", "mean")
        )
    )

    filtered_df["rating"] = (
        filtered_df["rating"]
        .round(2)
    )

    final_count = len(filtered_df)

    # =========================
    # Logs
    # =========================

    logger.info(
        f"Rows before filtering: {initial_count}"
    )

    logger.info(
        f"Rows after filtering: {final_count}"
    )

    logger.info(
        f"Removed {initial_count - final_count} orphan ratings"
    )

    logger.info(
        f"Unique users kept: "
        f"{filtered_df['user_id'].nunique()}"
    )

    logger.info(
        f"Unique works kept: "
        f"{filtered_df['book_key'].nunique()}"
    )

    return filtered_df


def save_parquet(df: pd.DataFrame) -> None:
    logger.info(
        f"Saving joinable ratings to "
        f"s3://{SILVER_BUCKET}/{OUTPUT_KEY}"
    )

    write_parquet_to_s3(
        df,
        SILVER_BUCKET,
        OUTPUT_KEY
    )

    logger.info("Save completed")


def main() -> None:
    try:
        books_df = load_parquet(
            BOOKS_KEY,
            "books"
        )

        users_df = load_parquet(
            USERS_KEY,
            "users"
        )

        ratings_df = load_parquet(
            RATINGS_KEY,
            "ratings"
        )

        joinable_df = filter_joinable_ratings(
            ratings_df,
            books_df,
            users_df
        )

        save_parquet(joinable_df)

        logger.info(
            "Joinable ratings filtering completed successfully"
        )

    except Exception as e:
        logger.error(
            f"Error during joinable ratings filtering: {e}",
            exc_info=True
        )
        raise


if __name__ == "__main__":
    main()