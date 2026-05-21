from pathlib import Path

import joblib

from src.utils.logger import setup_logger
from src.utils.s3_io import read_parquet_from_s3

logger = setup_logger("recommender")

MODEL_DIR = Path("models/reco")


def load_artifacts():
    """Charge les artefacts du modèle de recommandation."""
    logger.info("Loading recommendation artifacts")

    similarity = joblib.load(MODEL_DIR / "similarity.joblib")
    book_index_map = joblib.load(MODEL_DIR / "book_index_map.joblib")
    book_metadata = joblib.load(MODEL_DIR / "book_metadata.joblib")

    return similarity, book_index_map, book_metadata


def load_user_ratings():
    """Charge les ratings préparés pour la recommandation utilisateur."""
    logger.info("Loading ratings_pre_ml from S3")
    return read_parquet_from_s3("gold", "ratings_pre_ml.parquet")


def recommend_books(isbn, similarity, book_index_map, book_metadata, top_n=5):
    """Recommande des livres similaires à un livre donné."""
    if isbn not in book_index_map:
        logger.warning(f"ISBN not found in model: {isbn}")
        return []

    idx = book_index_map[isbn]
    scores = list(enumerate(similarity[idx]))
    scores = sorted(scores, key=lambda x: x[1], reverse=True)
    scores = scores[1:top_n + 1]

    reverse_map = {v: k for k, v in book_index_map.items()}

    recommendations = []

    for i, score in scores:
        rec_isbn = reverse_map[i]

        if rec_isbn in book_metadata.index:
            recommendations.append({
                "isbn": rec_isbn,
                "title": book_metadata.loc[rec_isbn, "title"],
                "author": book_metadata.loc[rec_isbn, "author"],
                "similarity_score": round(float(score), 3),
            })

    return recommendations


def recommend_for_user(user_id, ratings, similarity, book_index_map, book_metadata, top_n=5):
    """Recommande des livres personnalisés à partir d'un user_id."""
    user_ratings = ratings[ratings["user_id"] == user_id]

    if user_ratings.empty:
        logger.warning(f"User not found: {user_id}")
        return []

    liked_books = user_ratings[user_ratings["rating"] >= 7]["isbn"].tolist()
    already_seen = set(user_ratings["isbn"].tolist())

    if not liked_books:
        logger.warning(f"No liked books found for user: {user_id}")
        return []

    reverse_map = {v: k for k, v in book_index_map.items()}
    candidate_scores = {}

    for isbn in liked_books:
        if isbn not in book_index_map:
            continue

        idx = book_index_map[isbn]
        scores = list(enumerate(similarity[idx]))

        for book_idx, score in scores:
            candidate_isbn = reverse_map[book_idx]

            if candidate_isbn in already_seen:
                continue

            candidate_scores[candidate_isbn] = (
                candidate_scores.get(candidate_isbn, 0) + float(score)
            )

    sorted_candidates = sorted(
        candidate_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )[:top_n]

    recommendations = []

    for isbn, score in sorted_candidates:
        if isbn in book_metadata.index:
            recommendations.append({
                "isbn": isbn,
                "title": book_metadata.loc[isbn, "title"],
                "author": book_metadata.loc[isbn, "author"],
                "similarity_score": round(float(score), 3),
            })

    return recommendations