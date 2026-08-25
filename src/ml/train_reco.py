# from pathlib import Path

# import joblib
# from scipy.sparse import csr_matrix
# from sklearn.metrics.pairwise import cosine_similarity

# from src.utils.s3_io import read_parquet_from_s3
# from src.utils.logger import setup_logger

# logger = setup_logger("train_reco")

# TOP_N_BOOKS = 5000
# MODEL_DIR = Path("models/reco")


# def load_data():
#     logger.info("Loading ratings_pre_ml and books from S3")

#     ratings = read_parquet_from_s3("gold", "ratings_pre_ml.parquet")
#     books = read_parquet_from_s3("silver", "books_clean.parquet")

#     logger.info(f"Ratings shape BEFORE filtering: {ratings.shape}")

#     top_books = ratings["isbn"].value_counts().head(TOP_N_BOOKS).index
#     ratings = ratings[ratings["isbn"].isin(top_books)].copy()

#     logger.info(f"Ratings shape AFTER filtering: {ratings.shape}")

#     return ratings, books


# def build_sparse_matrix(ratings):
#     logger.info("Building sparse matrix")

#     user_ids = ratings["user_id"].astype("category")
#     book_ids = ratings["isbn"].astype("category")

#     user_index = user_ids.cat.codes
#     book_index = book_ids.cat.codes

#     matrix = csr_matrix(
#         (ratings["rating"], (user_index, book_index)),
#         shape=(user_ids.cat.categories.size, book_ids.cat.categories.size),
#     )

#     logger.info(f"Matrix shape: {matrix.shape}")

#     return matrix, book_ids.cat.categories


# def compute_similarity(matrix):
#     logger.info("Computing item-based cosine similarity")

#     item_matrix = matrix.T
#     similarity = cosine_similarity(item_matrix)

#     logger.info("Similarity computation done")

#     return similarity


# def build_book_metadata(books):
#     return books.set_index("isbn")[["title", "author"]]


# def save_artifacts(similarity, book_index_map, book_metadata):
#     logger.info("Saving recommendation artifacts")

#     MODEL_DIR.mkdir(parents=True, exist_ok=True)

#     joblib.dump(similarity, MODEL_DIR / "similarity.joblib")
#     joblib.dump(book_index_map, MODEL_DIR / "book_index_map.joblib")
#     joblib.dump(book_metadata, MODEL_DIR / "book_metadata.joblib")

#     logger.info(f"Artifacts saved in {MODEL_DIR}")


# def main():
#     ratings, books = load_data()

#     matrix, book_categories = build_sparse_matrix(ratings)
#     similarity = compute_similarity(matrix)

#     book_index_map = {
#         isbn: index
#         for index, isbn in enumerate(book_categories)
#     }

#     book_metadata = build_book_metadata(books)

#     save_artifacts(similarity, book_index_map, book_metadata)

#     logger.info("Recommendation model training completed successfully")


# if __name__ == "__main__":
#     main()


from pathlib import Path

import joblib
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity

from src.utils.s3_io import read_parquet_from_s3
from src.utils.logger import setup_logger


logger = setup_logger("train_reco")

TOP_N_BOOKS = 5000
MODEL_DIR = Path("models/reco")


def load_data():
    """
    Charge les ratings au niveau œuvre et les métadonnées livres.
    """
    logger.info("Loading ratings_joinable and books from S3")

    ratings = read_parquet_from_s3(
        "silver",
        "ratings_joinable.parquet"
    )

    books = read_parquet_from_s3(
        "silver",
        "books_clean.parquet"
    )

    logger.info(
        f"Ratings shape BEFORE filtering: {ratings.shape}"
    )

    # Garder les 5000 œuvres les plus notées
    top_books = (
        ratings["book_key"]
        .value_counts()
        .head(TOP_N_BOOKS)
        .index
    )

    ratings = ratings[
        ratings["book_key"].isin(top_books)
    ].copy()

    logger.info(
        f"Ratings shape AFTER filtering: {ratings.shape}"
    )

    return ratings, books


def build_sparse_matrix(ratings):
    """
    Construit la matrice sparse utilisateur × œuvre.
    """
    logger.info("Building sparse matrix")

    user_ids = ratings["user_id"].astype("category")
    book_ids = ratings["book_key"].astype("category")

    user_index = user_ids.cat.codes
    book_index = book_ids.cat.codes

    matrix = csr_matrix(
        (
            ratings["rating"],
            (
                user_index,
                book_index
            )
        ),
        shape=(
            user_ids.cat.categories.size,
            book_ids.cat.categories.size
        ),
    )

    logger.info(
        f"Matrix shape: {matrix.shape}"
    )

    return matrix, book_ids.cat.categories


def compute_similarity(matrix):
    """
    Calcule la similarité cosinus entre les œuvres.
    """
    logger.info(
        "Computing item-based cosine similarity"
    )

    item_matrix = matrix.T

    similarity = cosine_similarity(
        item_matrix
    )

    logger.info(
        "Similarity computation done"
    )

    return similarity


def build_book_metadata(books):
    """
    Construit les métadonnées d'une œuvre
    à partir de book_key.
    """

    metadata = (
        books[
            [
                "book_key",
                "title",
                "author"
            ]
        ]
        .drop_duplicates(
            subset=["book_key"]
        )
        .set_index("book_key")
    )

    return metadata


def save_artifacts(
    similarity,
    book_index_map,
    book_metadata
):
    """
    Sauvegarde les artefacts du modèle.
    """
    logger.info(
        "Saving recommendation artifacts"
    )

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    joblib.dump(
        similarity,
        MODEL_DIR / "similarity.joblib"
    )

    joblib.dump(
        book_index_map,
        MODEL_DIR / "book_index_map.joblib"
    )

    joblib.dump(
        book_metadata,
        MODEL_DIR / "book_metadata.joblib"
    )

    logger.info(
        f"Artifacts saved in {MODEL_DIR}"
    )


def main():
    ratings, books = load_data()

    matrix, book_categories = (
        build_sparse_matrix(ratings)
    )

    similarity = compute_similarity(
        matrix
    )

    book_index_map = {
        book_key: index
        for index, book_key
        in enumerate(book_categories)
    }

    book_metadata = build_book_metadata(
        books
    )

    save_artifacts(
        similarity,
        book_index_map,
        book_metadata
    )

    logger.info(
        "Recommendation model training completed successfully"
    )


if __name__ == "__main__":
    main()