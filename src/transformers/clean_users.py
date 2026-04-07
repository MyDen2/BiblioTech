from pathlib import Path
import pandas as pd

from src.utils.logger import setup_logger

logger = setup_logger("clean_users")

BRONZE_PATH = Path("data/bronze/BX-Users.csv")
SILVER_PATH = Path("data/silver/users_clean.parquet")


def load_users(csv_path: Path) -> pd.DataFrame:
    logger.info(f"Loading raw users from {csv_path}")

    df = pd.read_csv(
        csv_path,
        sep=";",
        encoding="latin-1",
        on_bad_lines="skip"
    )

    logger.info(f"Loaded dataframe shape: {df.shape}")
    return df


def extract_country(location: str) -> str | None:
    if pd.isna(location):
        return None

    parts = [part.strip() for part in str(location).split(",") if part.strip()]
    if not parts:
        return None

    return parts[-1]


def clean_users(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Starting users cleaning process")

    df = df.copy()

    # Normalisation des colonnes
    df.columns = [col.strip().lower().replace("-", "_") for col in df.columns]

    df = df.rename(columns={
        "user_id": "user_id",
        "location": "location",
        "age": "age"
    })

    expected_cols = ["user_id", "location", "age"]
    df = df[expected_cols]

    initial_count = len(df)

    # Nettoyage de base
    df["user_id"] = pd.to_numeric(df["user_id"], errors="coerce")
    df["location"] = df["location"].astype(str).str.strip()
    df["age"] = pd.to_numeric(df["age"], errors="coerce")

    df = df.replace({"nan": pd.NA, "": pd.NA})

    # Validation user_id
    df = df.dropna(subset=["user_id"])
    df = df[df["user_id"] > 0]
    df["user_id"] = df["user_id"].astype("int64")

    # Extraction pays
    df["country"] = df["location"].apply(extract_country)

    # Nettoyage âge : on garde une plage réaliste : 10 à 100
    df.loc[~df["age"].between(10, 100), "age"] = pd.NA

    # Déduplication
    df = df.drop_duplicates(subset=["user_id"])

    final_count = len(df)

    logger.info(f"Rows before cleaning: {initial_count}")
    logger.info(f"Rows after cleaning: {final_count}")
    logger.info(f"Removed {initial_count - final_count} rows")

    logger.info(f"Unique users: {df['user_id'].nunique()}")
    logger.info(f"Missing ages: {df['age'].isna().sum()}")
    logger.info(f"Missing countries: {df['country'].isna().sum()}")

    return df


def save_parquet(df: pd.DataFrame, output_path: Path) -> None:
    logger.info(f"Saving cleaned users to {output_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)

    logger.info("Save completed")


def main() -> None:
    try:
        df_raw = load_users(BRONZE_PATH)
        df_clean = clean_users(df_raw)
        save_parquet(df_clean, SILVER_PATH)

        logger.info("Users ETL process completed successfully")

    except Exception as e:
        logger.error(f"Error during users ETL: {e}", exc_info=True)


if __name__ == "__main__":
    main()