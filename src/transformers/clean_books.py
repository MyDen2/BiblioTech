from pathlib import Path
from datetime import datetime
import pandas as pd

from src.utils.logger import setup_logger

logger = setup_logger("clean_books")

BRONZE_PATH = Path("data/bronze/BX_Books.csv")
SILVER_PATH = Path("data/silver/books_clean.parquet")


def load_books(csv_path: Path) -> pd.DataFrame:
    logger.info(f"Loading raw books from {csv_path}")

    df = pd.read_csv(
        csv_path,
        sep=";",
        encoding="latin-1",
        on_bad_lines="skip"
    )

    logger.info(f"Loaded dataframe shape: {df.shape}")
    return df


def clean_books(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Starting books cleaning process")

    df = df.copy()

    # Normalisation des colonnes
    df.columns = [col.strip().lower().replace("-", "_") for col in df.columns]

    # Renommage explicite
    df = df.rename(columns={
        "isbn": "isbn",
        "book_title": "title",
        "book_author": "author",
        "year_of_publication": "year_of_publication",
        "publisher": "publisher",
        "image_url_s": "image_url_s",
        "image_url_m": "image_url_m",
        "image_url_l": "image_url_l"
    })

    expected_cols = [
        "isbn",
        "title",
        "author",
        "year_of_publication",
        "publisher",
        "image_url_s",
        "image_url_m",
        "image_url_l"
    ]
    df = df[expected_cols]

    initial_count = len(df)

    # Nettoyage texte
    text_cols = [
        "isbn", "title", "author", "publisher",
        "image_url_s", "image_url_m", "image_url_l"
    ]
    for col in text_cols:
        df[col] = df[col].astype(str).str.strip()

    df["isbn"] = df["isbn"].str.upper()

    # Remplacer les "nan" texte créés par astype(str)
    df = df.replace({"nan": pd.NA, "": pd.NA})

    # Conversion année
    df["year_of_publication"] = pd.to_numeric(df["year_of_publication"], errors="coerce")

    current_year = datetime.now().year
    df.loc[
        ~df["year_of_publication"].between(1900, current_year),
        "year_of_publication"
    ] = pd.NA

    # Supprimer lignes invalides minimales
    df = df.dropna(subset=["isbn", "title", "author"])
    df = df[df["isbn"] != ""]

    # Déduplication par ISBN
    df = df.drop_duplicates(subset=["isbn"])

    final_count = len(df)

    logger.info(f"Rows before cleaning: {initial_count}")
    logger.info(f"Rows after cleaning: {final_count}")
    logger.info(f"Removed {initial_count - final_count} rows")

    logger.info(f"Unique ISBN: {df['isbn'].nunique()}")
    logger.info(f"Unique authors: {df['author'].nunique()}")
    logger.info(f"Missing publication years: {df['year_of_publication'].isna().sum()}")

    return df


def save_parquet(df: pd.DataFrame, output_path: Path) -> None:
    logger.info(f"Saving cleaned books to {output_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)

    logger.info("Save completed")


def main() -> None:
    try:
        df_raw = load_books(BRONZE_PATH)
        df_clean = clean_books(df_raw)
        save_parquet(df_clean, SILVER_PATH)

        logger.info("Books ETL process completed successfully")

    except Exception as e:
        logger.error(f"Error during books ETL: {e}", exc_info=True)


if __name__ == "__main__":
    main()