# Ce loader Python :

# lit les fichiers :
# - silver/books_clean.parquet
# - silver/users_clean.parquet
# - silver/ratings_joinable.parquet
# envoie les données vers Postgres,
# log le nombre de lignes chargées.

# MinIO silver/gold → pandas → PostgreSQL

import os
import pandas as pd
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from src.utils.logger import setup_logger
from src.utils.s3_io import read_parquet_from_s3


logger = setup_logger("postgres_loader")


# =========================
# Configuration
# =========================

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / "config" / ".env"

load_dotenv(dotenv_path=ENV_PATH)

DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_PUBLIC_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB")

SILVER_BUCKET = "silver"
GOLD_BUCKET = "gold"

BOOKS_KEY = "books_clean.parquet"
USERS_KEY = "users_clean.parquet"
RATINGS_KEY = "ratings_joinable.parquet"
POPULARITY_KEY = "book_popularity.parquet"


# =========================
# PostgreSQL
# =========================

def get_engine():
    """
    Crée et retourne la connexion SQLAlchemy vers PostgreSQL.
    """
    if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]):
        raise ValueError(
            "Missing PostgreSQL configuration in config/.env"
        )

    url = (
        f"postgresql+psycopg2://"
        f"{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    return create_engine(url)


# =========================
# Lecture MinIO
# =========================

def load_table_from_s3(bucket: str, key: str, name: str):
    """
    Charge un fichier Parquet depuis MinIO dans un DataFrame pandas.
    """
    logger.info(
        f"Loading {name} from s3://{bucket}/{key}"
    )

    df = read_parquet_from_s3(
        bucket,
        key
    )

    logger.info(
        f"{name} shape: {df.shape}"
    )

    return df


# =========================
# Conversion pandas → PostgreSQL
# =========================

def dataframe_to_records(df):
    """
    Convertit un DataFrame en liste de dictionnaires compatible PostgreSQL.

    Les valeurs manquantes pandas sont converties en None,
    afin d'être enregistrées comme NULL dans PostgreSQL.
    """
    clean_df = (
        df.astype(object)
        .where(pd.notna(df), None)
    )

    return clean_df.to_dict(
        orient="records"
    )


# =========================
# Préparation des œuvres
# =========================

def prepare_books(books_df: pd.DataFrame) -> pd.DataFrame:
    """
    Prépare une ligne représentative par œuvre.

    Les différentes éditions ISBN sont regroupées via book_key.
    """
    logger.info(
        "Preparing unique works from books dataset"
    )

    books_df = books_df.copy()

    books_df["year_of_publication"] = pd.to_numeric(
        books_df["year_of_publication"],
        errors="coerce"
    ).astype("Int64")

    columns = [
        "book_key",
        "title",
        "author",
        "year_of_publication",
        "publisher",
        "image_url_s",
        "image_url_m",
        "image_url_l"
    ]

    works_df = (
        books_df[columns]
        .drop_duplicates(
            subset=["book_key"]
        )
        .copy()
    )

    logger.info(
        f"Unique works prepared: {len(works_df)}"
    )

    return works_df


# =========================
# Nettoyage PostgreSQL
# =========================

def truncate_tables(engine):
    """
    Vide uniquement les tables dérivées du dataset.

    Les tables applicatives ne sont pas touchées.
    """
    logger.info(
        "Truncating dataset-derived PostgreSQL tables"
    )

    with engine.begin() as conn:
        conn.execute(
            text("""
                TRUNCATE TABLE
                    book_popularity,
                    ratings;
            """)
        )

    logger.info(
        "Dataset-derived tables truncated"
    )


# =========================
# UPSERT books
# =========================

def upsert_books(engine, books_df):
    """
    Insère les œuvres dans PostgreSQL.

    Si un book_key existe déjà, les métadonnées
    de l'œuvre sont mises à jour.
    """
    logger.info(
        "Upserting works into books"
    )

    query = text("""
        INSERT INTO books (
            book_key,
            title,
            author,
            year_of_publication,
            publisher,
            image_url_s,
            image_url_m,
            image_url_l
        )
        VALUES (
            :book_key,
            :title,
            :author,
            :year_of_publication,
            :publisher,
            :image_url_s,
            :image_url_m,
            :image_url_l
        )

        ON CONFLICT (book_key)
        DO UPDATE SET
            title = EXCLUDED.title,
            author = EXCLUDED.author,
            year_of_publication = EXCLUDED.year_of_publication,
            publisher = EXCLUDED.publisher,
            image_url_s = EXCLUDED.image_url_s,
            image_url_m = EXCLUDED.image_url_m,
            image_url_l = EXCLUDED.image_url_l;
    """)

    records = dataframe_to_records(
        books_df
    )

    batch_size = 5000

    with engine.begin() as conn:
        for start in range(
            0,
            len(records),
            batch_size
        ):
            batch = records[
                start:start + batch_size
            ]

            conn.execute(
                query,
                batch
            )

    logger.info(
        f"Upserted {len(books_df)} works into 'books'"
    )


# =========================
# UPSERT users
# =========================

def upsert_users(engine, users_df):
    """
    Insère les utilisateurs du dataset dans PostgreSQL.

    Si un user_id existe déjà, ses informations sont mises à jour.
    """
    logger.info(
        "Upserting dataset users"
    )

    query = text("""
        INSERT INTO users (
            user_id,
            location,
            country,
            age
        )
        VALUES (
            :user_id,
            :location,
            :country,
            :age
        )

        ON CONFLICT (user_id)
        DO UPDATE SET
            location = EXCLUDED.location,
            country = EXCLUDED.country,
            age = EXCLUDED.age;
    """)

    records = dataframe_to_records(
        users_df
    )

    batch_size = 5000

    with engine.begin() as conn:
        for start in range(
            0,
            len(records),
            batch_size
        ):
            batch = records[
                start:start + batch_size
            ]

            conn.execute(
                query,
                batch
            )

    logger.info(
        f"Upserted {len(users_df)} rows into 'users'"
    )


# =========================
# Chargement tables dérivées
# =========================

def load_table(
    df,
    table_name: str,
    engine
) -> None:
    """
    Charge un DataFrame dans une table PostgreSQL.
    """
    logger.info(
        f"Loading dataframe into table '{table_name}'"
    )

    df.to_sql(
        table_name,
        engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=5000
    )

    logger.info(
        f"Loaded {len(df)} rows into '{table_name}'"
    )


# =========================
# Pipeline PostgreSQL
# =========================

def main() -> None:
    try:
        engine = get_engine()

        # =========================
        # Lecture MinIO
        # =========================

        books_raw_df = load_table_from_s3(
            SILVER_BUCKET,
            BOOKS_KEY,
            "books"
        )

        users_df = load_table_from_s3(
            SILVER_BUCKET,
            USERS_KEY,
            "users"
        )

        ratings_df = load_table_from_s3(
            SILVER_BUCKET,
            RATINGS_KEY,
            "ratings_joinable"
        )

        popularity_df = load_table_from_s3(
            GOLD_BUCKET,
            POPULARITY_KEY,
            "book_popularity"
        )

        # =========================
        # Préparation
        # =========================

        books_df = prepare_books(
            books_raw_df
        )

        users_df["age"] = pd.to_numeric(
            users_df["age"],
            errors="coerce"
        ).astype("Int64")

        ratings_df["rating"] = pd.to_numeric(
            ratings_df["rating"],
            errors="coerce"
        )

        # =========================
        # PostgreSQL
        # =========================

        truncate_tables(
            engine
        )

        upsert_books(
            engine,
            books_df
        )

        upsert_users(
            engine,
            users_df
        )

        load_table(
            ratings_df,
            "ratings",
            engine
        )

        load_table(
            popularity_df,
            "book_popularity",
            engine
        )

        logger.info(
            "PostgreSQL loading completed successfully"
        )

    except Exception as e:
        logger.error(
            f"Error while loading PostgreSQL tables: {e}",
            exc_info=True
        )

        raise


if __name__ == "__main__":
    main()