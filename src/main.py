import argparse
import sys

from src.utils.logger import setup_logger

from src.transformers.clean_ratings import main as clean_ratings_main
from src.transformers.clean_books import main as clean_books_main
from src.transformers.clean_users import main as clean_users_main
from src.transformers.filter_joinable_ratings import main as filter_joinable_ratings_main
from src.transformers.build_book_popularity import main as build_book_popularity_main
from src.loaders.postgres_loader import main as postgres_loader_main

logger = setup_logger("main")


def run_step(step_name: str, step_function) -> None:
    logger.info(f"Starting step: {step_name}")
    step_function()
    logger.info(f"Finished step: {step_name}")


def run_full_pipeline() -> None:
    logger.info("Starting full BiblioTech pipeline")

    run_step("clean_ratings", clean_ratings_main)
    run_step("clean_books", clean_books_main)
    run_step("clean_users", clean_users_main)
    run_step("filter_joinable_ratings", filter_joinable_ratings_main)
    run_step("build_book_popularity", build_book_popularity_main)
    run_step("load_postgres", postgres_loader_main)

    logger.info("Full BiblioTech pipeline completed successfully")


def parse_args():
    parser = argparse.ArgumentParser(
        description="BiblioTech pipeline runner"
    )

    parser.add_argument(
        "command",
        choices=[
            "clean_ratings",
            "clean_books",
            "clean_users",
            "filter_joinable_ratings",
            "build_book_popularity",
            "load_postgres",
            "full_pipeline",
        ],
        help="Pipeline step to execute"
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    try:
        if args.command == "clean_ratings":
            run_step("clean_ratings", clean_ratings_main)

        elif args.command == "clean_books":
            run_step("clean_books", clean_books_main)

        elif args.command == "clean_users":
            run_step("clean_users", clean_users_main)

        elif args.command == "filter_joinable_ratings":
            run_step("filter_joinable_ratings", filter_joinable_ratings_main)

        elif args.command == "build_book_popularity":
            run_step("build_book_popularity", build_book_popularity_main)

        elif args.command == "load_postgres":
            run_step("load_postgres", postgres_loader_main)

        elif args.command == "full_pipeline":
            run_full_pipeline()

    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()