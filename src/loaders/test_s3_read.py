from src.utils.logger import setup_logger
from src.utils.s3_io import list_objects, read_parquet_from_s3

logger = setup_logger("test_s3_read")


def main():
    try:
        bronze_objects = list_objects("bronze")
        silver_objects = list_objects("silver")
        gold_objects = list_objects("gold")

        logger.info(f"Bronze objects: {bronze_objects[:10]}")
        logger.info(f"Silver objects: {silver_objects[:10]}")
        logger.info(f"Gold objects: {gold_objects[:10]}")

        df = read_parquet_from_s3("silver", "ratings_joinable.parquet")
        logger.info(f"Loaded dataframe shape from S3: {df.shape}")
        logger.info(f"Columns: {list(df.columns)}")

    except Exception as e:
        logger.error(f"S3 read test failed: {e}", exc_info=True)


if __name__ == "__main__":
    main()