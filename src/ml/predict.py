import argparse

from src.utils.logger import setup_logger

from src.api.database import get_app_user_ratings

from src.ml.recommender import (
    load_artifacts,
    recommend_books,
    recommend_for_app_user,
)


logger = setup_logger("predict_reco")


# =========================
# Arguments CLI
# =========================

def parse_args():
    parser = argparse.ArgumentParser(
        description="BiblioTech recommendation CLI"
    )

    parser.add_argument(
        "--book_key",
        help="Identifiant logique de l'œuvre"
    )

    parser.add_argument(
        "--app_user_id",
        type=int,
        help="Identifiant d'un utilisateur BiblioTech"
    )

    parser.add_argument(
        "--top_n",
        type=int,
        default=5,
        help="Nombre de recommandations"
    )

    return parser.parse_args()


# =========================
# CLI
# =========================

def main():
    args = parse_args()

    # =========================
    # Validation
    # =========================

    if not args.book_key and not args.app_user_id:
        logger.error(
            "Vous devez fournir soit "
            "--book_key soit --app_user_id"
        )
        return

    if args.book_key and args.app_user_id:
        logger.error(
            "Fournissez uniquement --book_key "
            "ou --app_user_id, pas les deux"
        )
        return

    # =========================
    # Chargement modèle
    # =========================

    similarity, book_index_map, book_metadata = (
        load_artifacts()
    )

    # =========================
    # Recommandation par œuvre
    # =========================

    if args.book_key:

        recommendations = recommend_books(
            args.book_key,
            similarity,
            book_index_map,
            book_metadata,
            top_n=args.top_n,
        )

        logger.info(
            f"Recommendations for book_key: "
            f"{args.book_key}"
        )

    # =========================
    # Recommandation utilisateur
    # =========================

    else:

        user_ratings = get_app_user_ratings(
            args.app_user_id
        )

        if not user_ratings:
            logger.warning(
                f"No ratings found for app_user_id "
                f"{args.app_user_id}"
            )
            return

        recommendations = recommend_for_app_user(
            user_ratings,
            similarity,
            book_index_map,
            book_metadata,
            top_n=args.top_n,
        )

        logger.info(
            f"Recommendations for app_user_id "
            f"{args.app_user_id}"
        )

    # =========================
    # Résultats
    # =========================

    if not recommendations:
        logger.warning(
            "No recommendations found"
        )
        return

    for reco in recommendations:
        logger.info(
            f"{reco['title']} - "
            f"{reco['author']} "
            f"(book_key={reco['book_key']}, "
            f"score={reco['similarity_score']})"
        )


if __name__ == "__main__":
    main()