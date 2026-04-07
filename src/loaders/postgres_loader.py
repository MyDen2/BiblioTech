# Ce loader Python :

# lit les fichiers parquet,
# envoie les données vers Postgres,
# log le nombre de lignes chargées.

from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text

from src.utils.logger import setup_logger

logger = setup_logger("postgres_loader")

BOOKS_PATH = Path("data/silver/books_clean.parquet")
USERS_PATH = Path("data/silver/users_clean.parquet")
RATINGS_PATH = Path("data/silver/ratings_joinable.parquet")
POPULARITY_PATH = Path("data/gold/book_popularity.parquet")


DB_USER = "bibliotech"
DB_PASSWORD = "bibliotech"
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "bibliotech_db"


def get_engine():
    url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(url)


def load_parquet(path: Path, name: str) -> pd.DataFrame:
    logger.info(f"Loading {name} from {path}")
    df = pd.read_parquet(path)
    logger.info(f"{name} shape: {df.shape}")
    return df


def truncate_tables(engine) -> None:
    logger.info("Truncating PostgreSQL tables")
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE book_popularity, ratings, users, books CASCADE;"))
    logger.info("Truncate completed")


def load_table(df: pd.DataFrame, table_name: str, engine) -> None:
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

        books_df = load_parquet(BOOKS_PATH, "books")
        users_df = load_parquet(USERS_PATH, "users")
        ratings_df = load_parquet(RATINGS_PATH, "ratings_joinable")
        popularity_df = load_parquet(POPULARITY_PATH, "book_popularity")

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