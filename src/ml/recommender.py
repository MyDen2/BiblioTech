from pathlib import Path

import joblib

from src.utils.logger import setup_logger


logger = setup_logger("recommender")

MODEL_DIR = Path("models/reco")


# =========================
# Chargement des artefacts
# =========================

def load_artifacts():
    """
    Charge les artefacts du modèle de recommandation.
    """
    logger.info("Loading recommendation artifacts")

    similarity = joblib.load(
        MODEL_DIR / "similarity.joblib"
    )

    book_index_map = joblib.load(
        MODEL_DIR / "book_index_map.joblib"
    )

    book_metadata = joblib.load(
        MODEL_DIR / "book_metadata.joblib"
    )

    return (
        similarity,
        book_index_map,
        book_metadata
    )


# =========================
# Recommandation par œuvre
# =========================

def recommend_books(
    book_key,
    similarity,
    book_index_map,
    book_metadata,
    top_n=5
):
    """
    Recommande des œuvres similaires
    à partir d'un book_key.
    """

    if book_key not in book_index_map:
        logger.warning(
            f"Book key not found in model: {book_key}"
        )
        return []

    idx = book_index_map[book_key]

    scores = list(
        enumerate(similarity[idx])
    )

    scores = sorted(
        scores,
        key=lambda x: x[1],
        reverse=True
    )

    # Exclure l'œuvre elle-même
    scores = scores[1:top_n + 1]

    reverse_map = {
        index: key
        for key, index
        in book_index_map.items()
    }

    recommendations = []

    for book_idx, score in scores:

        rec_book_key = reverse_map[book_idx]

        if rec_book_key not in book_metadata.index:
            continue

        metadata = book_metadata.loc[
            rec_book_key
        ]

        recommendations.append({
            "book_key": rec_book_key,
            "title": metadata["title"],
            "author": metadata["author"],
            "similarity_score": round(
                float(score),
                3
            ),
        })

    return recommendations


# =========================
# Recommandation utilisateur BiblioTech
# =========================

def recommend_for_app_user(
    user_ratings,
    similarity,
    book_index_map,
    book_metadata,
    top_n=5
):
    """
    Recommande des œuvres à un utilisateur BiblioTech
    à partir des notes enregistrées dans l'application.
    """

    if not user_ratings:
        logger.warning(
            "No ratings found for app user"
        )
        return []

    # Œuvres appréciées
    liked_books = [
        item["book_key"]
        for item in user_ratings
        if item["rating"] >= 7
    ]

    # Œuvres déjà notées
    already_seen = {
        item["book_key"]
        for item in user_ratings
    }

    if not liked_books:
        logger.warning(
            "No liked books found for app user"
        )
        return []

    reverse_map = {
        index: book_key
        for book_key, index
        in book_index_map.items()
    }

    candidate_scores = {}

    # =========================
    # Génération des candidats
    # =========================

    for book_key in liked_books:

        # Une œuvre peut exister dans PostgreSQL
        # sans faire partie des 5000 œuvres du modèle.
        if book_key not in book_index_map:
            continue

        idx = book_index_map[book_key]

        scores = list(
            enumerate(similarity[idx])
        )

        for book_idx, score in scores:

            candidate_book_key = reverse_map[
                book_idx
            ]

            if candidate_book_key in already_seen:
                continue

            candidate_scores[
                candidate_book_key
            ] = (
                candidate_scores.get(
                    candidate_book_key,
                    0
                )
                + float(score)
            )

    if not candidate_scores:
        logger.warning(
            "No recommendation candidates found for app user"
        )
        return []

    # =========================
    # Classement
    # =========================

    sorted_candidates = sorted(
        candidate_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )[:top_n]

    recommendations = []

    for book_key, score in sorted_candidates:

        if book_key not in book_metadata.index:
            continue

        metadata = book_metadata.loc[
            book_key
        ]

        recommendations.append({
            "book_key": book_key,
            "title": metadata["title"],
            "author": metadata["author"],
            "similarity_score": round(
                float(score),
                3
            )
        })

    return recommendations