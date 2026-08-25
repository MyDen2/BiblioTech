from pathlib import Path

from sqlalchemy import text

from src.api.database import engine
from src.utils.logger import setup_logger

logger = setup_logger("init_database")

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SCHEMA_PATH = PROJECT_ROOT / "sql" / "schema.sql"
APP_SCHEMA_PATH = PROJECT_ROOT / "sql" / "app_schema.sql"


def execute_sql_file(path: Path) -> None:
    """
    Exécute un fichier SQL dans PostgreSQL.
    """
    logger.info(f"Executing SQL file: {path}")

    sql_content = path.read_text(encoding="utf-8")

    with engine.begin() as conn:
        conn.execute(text(sql_content))

    logger.info(f"SQL file executed successfully: {path.name}")


def main():
    logger.info("Initializing PostgreSQL database")

    execute_sql_file(SCHEMA_PATH)
    execute_sql_file(APP_SCHEMA_PATH)

    logger.info("PostgreSQL database initialized successfully")


if __name__ == "__main__":
    main()