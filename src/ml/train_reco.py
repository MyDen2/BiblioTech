# # Construction d'un modele capable :

# ## Input : livre
# ## Output : les livres les plus similaires

# # basé sur : matrice sparse et cosine similarity

# import pandas as pd

# from scipy.sparse import csr_matrix
# from sklearn.metrics.pairwise import cosine_similarity

# from src.utils.s3_io import read_parquet_from_s3
# from src.utils.logger import setup_logger

# logger = setup_logger("train_reco")

# def load_data():
#     '''Chargement des données'''
#     logger.info("Loading ratings_pre_ml from S3")
#     books = read_parquet_from_s3("silver", "books_clean.parquet")

#     ratings = read_parquet_from_s3("gold", "ratings_pre_ml.parquet")

#     logger.info(f"Ratings shape BEFORE filtering: {ratings.shape}")

#     # Limiter aux livres les plus populaires
#     top_books = ratings["isbn"].value_counts().head(5000).index
#     ratings = ratings[ratings["isbn"].isin(top_books)]

#     logger.info(f"Ratings shape AFTER filtering: {ratings.shape}")

#     return ratings

# def build_sparse_matrix(ratings):
#     '''Construction matrice sparse'''
#     logger.info("Building sparse matrix")

#     user_ids = ratings["user_id"].astype("category")
#     book_ids = ratings["isbn"].astype("category")

#     user_index = user_ids.cat.codes
#     book_index = book_ids.cat.codes

#     matrix = csr_matrix(
#         (ratings["rating"], (user_index, book_index)),
#         shape=(user_ids.cat.categories.size, book_ids.cat.categories.size)
#     )

#     logger.info(f"Matrix shape: {matrix.shape}")
#     return matrix, book_ids.cat.categories

# def compute_similarity(matrix):
#     '''Similarité entre les livres : on transpose la matrice'''
#     logger.info("Computing cosine similarity (item-based)")

#     item_matrix = matrix.T  # livres x users

#     similarity = cosine_similarity(item_matrix)

#     logger.info("Similarity computation done")
#     return similarity

# def build_book_metadata(books):
#     """Mapping ISBN -> titre + auteur"""
#     return books.set_index("isbn")[["title", "author"]]

# def recommend_books(isbn, similarity, book_index_map, book_metadata, top_n=5):
#     logger.info(f"Generating recommendations for {isbn}")

#     if isbn not in book_index_map:
#         logger.warning("Book not found")
#         return []

#     idx = book_index_map[isbn]

#     scores = list(enumerate(similarity[idx]))
#     scores = sorted(scores, key=lambda x: x[1], reverse=True)

#     # exclure lui-même
#     scores = scores[1:top_n+1]

#     reverse_map = {v: k for k, v in book_index_map.items()}

#     recommendations = []

#     for i, score in scores:
#         rec_isbn = reverse_map[i]

#         if rec_isbn in book_metadata.index:
#             title = book_metadata.loc[rec_isbn, "title"]
#             author = book_metadata.loc[rec_isbn, "author"]

#             recommendations.append({
#                 "isbn": rec_isbn,
#                 "title": title,
#                 "author": author,
#                 "score": round(float(score), 3)
#             })

#     return recommendations

# def main():
#     ratings = load_data()
#     books = read_parquet_from_s3("silver", "books_clean.parquet")

#     matrix, book_categories = build_sparse_matrix(ratings)

#     similarity = compute_similarity(matrix)

#     book_index_map = {isbn: i for i, isbn in enumerate(book_categories)}

#     book_metadata = build_book_metadata(books)

#     sample_isbn = ratings["isbn"].iloc[0]

#     recos = recommend_books(
#         sample_isbn,
#         similarity,
#         book_index_map,
#         book_metadata
#     )

#     logger.info(f"Recommendations for {sample_isbn}:")

#     for r in recos:
#         logger.info(f"{r['title']} - {r['author']} (score={r['score']})")


# if __name__ == "__main__":
#     main()



# ### Optimisation du calcul

# # Le calcul de la similarité entre tous les livres étant très coûteux, une réduction du dataset a été appliquée.

# # Seuls les 5000 livres les plus populaires ont été conservés.

# # Cela permet de :

# # - réduire la complexité du calcul
# # - améliorer les performances
# # - conserver les livres les plus pertinents

# import pandas as pd
# from scipy.sparse import csr_matrix
# from sklearn.metrics.pairwise import cosine_similarity

# from src.utils.s3_io import read_parquet_from_s3
# from src.utils.logger import setup_logger

# logger = setup_logger("train_reco")

# TOP_N_BOOKS = 5000


# def load_data():
#     """Charge les données préparées pour la recommandation."""
#     logger.info("Loading ratings_pre_ml from S3")

#     ratings = read_parquet_from_s3("gold", "ratings_pre_ml.parquet")
#     books = read_parquet_from_s3("silver", "books_clean.parquet")

#     logger.info(f"Ratings shape BEFORE filtering: {ratings.shape}")

#     top_books = ratings["isbn"].value_counts().head(TOP_N_BOOKS).index
#     ratings = ratings[ratings["isbn"].isin(top_books)].copy()

#     logger.info(f"Ratings shape AFTER filtering: {ratings.shape}")

#     return ratings, books


# def build_sparse_matrix(ratings):
#     """Construit une matrice sparse utilisateur-livre."""
#     logger.info("Building sparse matrix")

#     user_ids = ratings["user_id"].astype("category")
#     book_ids = ratings["isbn"].astype("category")

#     user_index = user_ids.cat.codes
#     book_index = book_ids.cat.codes

#     matrix = csr_matrix(
#         (ratings["rating"], (user_index, book_index)),
#         shape=(user_ids.cat.categories.size, book_ids.cat.categories.size)
#     )

#     logger.info(f"Matrix shape: {matrix.shape}")

#     return matrix, book_ids.cat.categories


# def compute_similarity(matrix):
#     """Calcule la similarité cosinus entre livres."""
#     logger.info("Computing cosine similarity item-based")

#     item_matrix = matrix.T
#     similarity = cosine_similarity(item_matrix)

#     logger.info("Similarity computation done")

#     return similarity


# def build_book_metadata(books):
#     """Crée un mapping ISBN vers titre et auteur."""
#     return books.set_index("isbn")[["title", "author"]]


# def recommend_books(isbn, similarity, book_index_map, book_metadata, top_n=5):
#     """Recommande les livres les plus similaires à un ISBN donné."""
#     logger.info(f"Generating recommendations for {isbn}")

#     if isbn not in book_index_map:
#         logger.warning("Book not found in recommendation model")
#         return []

#     idx = book_index_map[isbn]

#     scores = list(enumerate(similarity[idx]))
#     scores = sorted(scores, key=lambda x: x[1], reverse=True)

#     scores = scores[1:top_n + 1]

#     reverse_map = {v: k for k, v in book_index_map.items()}

#     recommendations = []

#     for i, score in scores:
#         rec_isbn = reverse_map[i]

#         if rec_isbn in book_metadata.index:
#             recommendations.append({
#                 "isbn": rec_isbn,
#                 "title": book_metadata.loc[rec_isbn, "title"],
#                 "author": book_metadata.loc[rec_isbn, "author"],
#                 "similarity_score": round(float(score), 3)
#             })

#     return recommendations


# def main():
#     ratings, books = load_data()

#     matrix, book_categories = build_sparse_matrix(ratings)
#     similarity = compute_similarity(matrix)

#     book_index_map = {
#         isbn: index
#         for index, isbn in enumerate(book_categories)
#     }

#     book_metadata = build_book_metadata(books)

#     # Choisir automatiquement le livre le plus noté
#     sample_isbn = ratings["isbn"].value_counts().idxmax()
#     logger.info(f"Most rated ISBN selected: {sample_isbn}")

#     recommendations = recommend_books(
#         sample_isbn,
#         similarity,
#         book_index_map,
#         book_metadata,
#         top_n=5
#     )

#     logger.info(f"Recommendations for ISBN {sample_isbn}")

#     for reco in recommendations:
#         logger.info(
#             f"{reco['title']} - {reco['author']} "
#             f"(ISBN={reco['isbn']}, score={reco['similarity_score']})"
#         )


# if __name__ == "__main__":
#     main()

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
    logger.info("Loading ratings_pre_ml and books from S3")

    ratings = read_parquet_from_s3("gold", "ratings_pre_ml.parquet")
    books = read_parquet_from_s3("silver", "books_clean.parquet")

    logger.info(f"Ratings shape BEFORE filtering: {ratings.shape}")

    top_books = ratings["isbn"].value_counts().head(TOP_N_BOOKS).index
    ratings = ratings[ratings["isbn"].isin(top_books)].copy()

    logger.info(f"Ratings shape AFTER filtering: {ratings.shape}")

    return ratings, books


def build_sparse_matrix(ratings):
    logger.info("Building sparse matrix")

    user_ids = ratings["user_id"].astype("category")
    book_ids = ratings["isbn"].astype("category")

    user_index = user_ids.cat.codes
    book_index = book_ids.cat.codes

    matrix = csr_matrix(
        (ratings["rating"], (user_index, book_index)),
        shape=(user_ids.cat.categories.size, book_ids.cat.categories.size),
    )

    logger.info(f"Matrix shape: {matrix.shape}")

    return matrix, book_ids.cat.categories


def compute_similarity(matrix):
    logger.info("Computing item-based cosine similarity")

    item_matrix = matrix.T
    similarity = cosine_similarity(item_matrix)

    logger.info("Similarity computation done")

    return similarity


def build_book_metadata(books):
    return books.set_index("isbn")[["title", "author"]]


def save_artifacts(similarity, book_index_map, book_metadata):
    logger.info("Saving recommendation artifacts")

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(similarity, MODEL_DIR / "similarity.joblib")
    joblib.dump(book_index_map, MODEL_DIR / "book_index_map.joblib")
    joblib.dump(book_metadata, MODEL_DIR / "book_metadata.joblib")

    logger.info(f"Artifacts saved in {MODEL_DIR}")


def main():
    ratings, books = load_data()

    matrix, book_categories = build_sparse_matrix(ratings)
    similarity = compute_similarity(matrix)

    book_index_map = {
        isbn: index
        for index, isbn in enumerate(book_categories)
    }

    book_metadata = build_book_metadata(books)

    save_artifacts(similarity, book_index_map, book_metadata)

    logger.info("Recommendation model training completed successfully")


if __name__ == "__main__":
    main()