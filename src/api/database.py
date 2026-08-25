import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from src.utils.logger import setup_logger

logger = setup_logger("api_database")

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / "config" / ".env"

load_dotenv(dotenv_path=ENV_PATH)

DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_PUBLIC_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB")


def get_engine():
    if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]):
        raise ValueError("Missing PostgreSQL configuration in config/.env")

    url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(url)


engine = get_engine()


def create_app_user(username: str, email: str, age: int | None, country: str | None):
    query = text("""
        INSERT INTO app_users (username, email, age, country)
        VALUES (:username, :email, :age, :country)
        RETURNING app_user_id, username, email, age, country, created_at;
    """)

    try:
        with engine.begin() as conn:
            result = conn.execute(query, {
                "username": username,
                "email": email,
                "age": age,
                "country": country
            })
            return dict(result.mappings().first())

    except SQLAlchemyError as e:
        logger.error(f"Error creating app user: {e}", exc_info=True)
        raise

def create_user_rating(
    app_user_id: int,
    book_key: str,
    rating: int
):
    """
    Crée ou met à jour la note donnée par un utilisateur
    à une œuvre identifiée par son book_key.
    """
    query = text("""
        INSERT INTO user_book_ratings (
            app_user_id,
            book_key,
            rating
        )
        VALUES (
            :app_user_id,
            :book_key,
            :rating
        )

        ON CONFLICT (app_user_id, book_key)
        DO UPDATE SET
            rating = EXCLUDED.rating,
            created_at = CURRENT_TIMESTAMP

        RETURNING
            rating_id,
            app_user_id,
            book_key,
            rating,
            created_at;
    """)

    try:
        with engine.begin() as conn:
            result = conn.execute(
                query,
                {
                    "app_user_id": app_user_id,
                    "book_key": book_key,
                    "rating": rating
                }
            )

            return dict(
                result.mappings().first()
            )

    except SQLAlchemyError as e:
        logger.error(
            f"Error creating user rating: {e}",
            exc_info=True
        )
        raise

def search_books(
    query: str,
    limit: int = 20
):
    """
    Recherche des œuvres à partir d'un mot-clé présent
    dans le titre ou le nom de l'auteur.

    Parameters
    ----------
    query : str
        Mot-clé saisi par l'utilisateur.

    limit : int, optional
        Nombre maximum de résultats retournés.

    Returns
    -------
    list[dict]
        Liste des œuvres correspondantes contenant :
        book_key, titre, auteur, année de publication
        et éditeur.
    """

    sql = text("""
        SELECT
            book_key,
            title,
            author,
            year_of_publication,
            publisher,
            image_url_m
        FROM books
        WHERE LOWER(title) LIKE LOWER(:pattern)
           OR LOWER(author) LIKE LOWER(:pattern)
        ORDER BY title, author
        LIMIT :limit;
    """)

    pattern = f"%{query}%"

    try:
        with engine.begin() as conn:
            result = conn.execute(
                sql,
                {
                    "pattern": pattern,
                    "limit": limit
                }
            )

            return [
                dict(row)
                for row in result.mappings()
            ]

    except SQLAlchemyError as e:
        logger.error(
            f"Error searching books: {e}",
            exc_info=True
        )
        raise

def get_app_user_ratings(app_user_id: int):
    """
    Récupère les notes données par un utilisateur BiblioTech.
    """

    query = text("""
        SELECT
            app_user_id,
            book_key,
            rating
        FROM user_book_ratings
        WHERE app_user_id = :app_user_id;
    """)

    try:
        with engine.begin() as conn:
            result = conn.execute(
                query,
                {
                    "app_user_id": app_user_id
                }
            )

            return [
                dict(row)
                for row in result.mappings()
            ]

    except SQLAlchemyError as e:
        logger.error(
            f"Error loading app user ratings: {e}",
            exc_info=True
        )
        raise