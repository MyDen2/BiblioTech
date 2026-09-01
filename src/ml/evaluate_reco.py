from src.ml.recommender import (
    load_artifacts,
    recommend_for_app_user,
)
from src.utils.logger import setup_logger
from src.utils.s3_io import read_parquet_from_s3


logger = setup_logger("evaluate_reco")

SILVER_BUCKET = "silver"
RATINGS_KEY = "ratings_joinable.parquet"

K = 5
MIN_LIKED_BOOKS = 2
MAX_USERS = 1000


# =========================
# Métriques
# =========================

def precision_at_k(recommended, relevant, k):
    recommended_k = recommended[:k]

    if not recommended_k:
        return 0.0

    hits = len(
        set(recommended_k)
        & set(relevant)
    )

    return hits / k


def recall_at_k(recommended, relevant, k):
    if not relevant:
        return 0.0

    recommended_k = recommended[:k]

    hits = len(
        set(recommended_k)
        & set(relevant)
    )

    return hits / len(relevant)


def hit_rate_at_k(recommended, relevant, k):
    recommended_k = recommended[:k]

    return float(
        bool(
            set(recommended_k)
            & set(relevant)
        )
    )


# =========================
# Évaluation
# =========================

def evaluate():
    logger.info(
        "Loading ratings_joinable"
    )

    ratings = read_parquet_from_s3(
        SILVER_BUCKET,
        RATINGS_KEY
    )

    logger.info(
        f"Ratings loaded: {ratings.shape}"
    )

    (
        similarity,
        book_index_map,
        book_metadata
    ) = load_artifacts()

    # =========================
    # Limitation au périmètre
    # du modèle Top 5000
    # =========================

    ratings = ratings[
        ratings["book_key"].isin(
            book_index_map
        )
    ].copy()

    logger.info(
        f"Ratings inside model scope: "
        f"{ratings.shape}"
    )

    # =========================
    # Œuvres appréciées
    # =========================

    liked = ratings[
        ratings["rating"] >= 7
    ].copy()

    # =========================
    # Baseline de popularité
    # =========================

    popular_books = (
        liked.groupby("book_key")
        .size()
        .sort_values(
            ascending=False
        )
        .index
        .tolist()
    )

    logger.info(
        "Popularity baseline catalog: "
        f"{len(popular_books)} books"
    )

    # =========================
    # Utilisateurs éligibles
    # =========================

    liked_by_user = (
        liked.groupby("user_id")["book_key"]
        .apply(list)
    )

    eligible_users = liked_by_user[
        liked_by_user.apply(len)
        >= MIN_LIKED_BOOKS
    ]

    logger.info(
        f"Eligible users: "
        f"{len(eligible_users)}"
    )

    if MAX_USERS:
        eligible_users = (
            eligible_users.iloc[
                :MAX_USERS
            ]
        )

    # =========================
    # Scores du modèle
    # collaboratif
    # =========================

    precision_scores = []
    recall_scores = []
    hit_scores = []

    recommended_catalog = set()

    # =========================
    # Scores baseline
    # popularité
    # =========================

    baseline_precision_scores = []
    baseline_recall_scores = []
    baseline_hit_scores = []

    evaluated_users = 0

    # =========================
    # Boucle d'évaluation
    # =========================

    for (
        user_id,
        liked_books
    ) in eligible_users.items():

        # Split leave-one-out :
        # dernière œuvre appréciée
        # utilisée comme vérité terrain
        test_book = liked_books[-1]

        # Les autres œuvres appréciées
        # constituent le profil connu
        train_books = liked_books[:-1]

        user_ratings = [
            {
                "book_key": book_key,
                "rating": 10
            }
            for book_key in train_books
        ]

        # =========================
        # Modèle collaboratif
        # =========================

        recommendations = (
            recommend_for_app_user(
                user_ratings=user_ratings,
                similarity=similarity,
                book_index_map=(
                    book_index_map
                ),
                book_metadata=(
                    book_metadata
                ),
                top_n=K
            )
        )

        recommended_keys = [
            item["book_key"]
            for item
            in recommendations
        ]

        relevant = [
            test_book
        ]

        precision_scores.append(
            precision_at_k(
                recommended_keys,
                relevant,
                K
            )
        )

        recall_scores.append(
            recall_at_k(
                recommended_keys,
                relevant,
                K
            )
        )

        hit_scores.append(
            hit_rate_at_k(
                recommended_keys,
                relevant,
                K
            )
        )

        recommended_catalog.update(
            recommended_keys
        )

        # =========================
        # Baseline popularité
        # =========================

        baseline_recommended = [
            book_key
            for book_key
            in popular_books
            if book_key
            not in train_books
        ][:K]

        baseline_precision_scores.append(
            precision_at_k(
                baseline_recommended,
                relevant,
                K
            )
        )

        baseline_recall_scores.append(
            recall_at_k(
                baseline_recommended,
                relevant,
                K
            )
        )

        baseline_hit_scores.append(
            hit_rate_at_k(
                baseline_recommended,
                relevant,
                K
            )
        )

        evaluated_users += 1

    # =========================
    # Vérification
    # =========================

    if evaluated_users == 0:
        logger.warning(
            "No users could be evaluated"
        )
        return

    # =========================
    # Moyennes du modèle
    # collaboratif
    # =========================

    mean_precision = (
        sum(precision_scores)
        / len(precision_scores)
    )

    mean_recall = (
        sum(recall_scores)
        / len(recall_scores)
    )

    mean_hit_rate = (
        sum(hit_scores)
        / len(hit_scores)
    )

    # =========================
    # Moyennes baseline
    # =========================

    baseline_precision = (
        sum(
            baseline_precision_scores
        )
        / len(
            baseline_precision_scores
        )
    )

    baseline_recall = (
        sum(
            baseline_recall_scores
        )
        / len(
            baseline_recall_scores
        )
    )

    baseline_hit_rate = (
        sum(
            baseline_hit_scores
        )
        / len(
            baseline_hit_scores
        )
    )

    # =========================
    # Coverage
    # =========================

    catalog_size = len(
        book_index_map
    )

    coverage = (
        len(
            recommended_catalog
        )
        / catalog_size
        if catalog_size
        else 0
    )

    # =========================
    # Comparaison
    # =========================

    difference = (
        mean_hit_rate
        - baseline_hit_rate
    )

    relative_difference = None

    if baseline_hit_rate > 0:
        relative_difference = (
            difference
            / baseline_hit_rate
        ) * 100

    # =========================
    # Affichage
    # =========================

    print()
    print(
        "BiblioTech - Offline evaluation"
    )
    print("=" * 40)

    print(
        f"Users evaluated : "
        f"{evaluated_users}"
    )

    print(
        f"K               : "
        f"{K}"
    )

    print()
    print(
        "Collaborative filtering"
    )
    print("=" * 40)

    print(
        f"Precision@{K}     : "
        f"{mean_precision:.4f}"
    )

    print(
        f"Recall@{K}        : "
        f"{mean_recall:.4f}"
    )

    print(
        f"HitRate@{K}       : "
        f"{mean_hit_rate:.4f}"
    )

    print(
        f"Coverage         : "
        f"{coverage:.4f}"
    )

    print(
        f"Catalog size     : "
        f"{catalog_size}"
    )

    print(
        f"Books recommended: "
        f"{len(recommended_catalog)}"
    )

    print()
    print(
        "Popularity baseline"
    )
    print("=" * 40)

    print(
        f"Precision@{K}     : "
        f"{baseline_precision:.4f}"
    )

    print(
        f"Recall@{K}        : "
        f"{baseline_recall:.4f}"
    )

    print(
        f"HitRate@{K}       : "
        f"{baseline_hit_rate:.4f}"
    )

    print()
    print(
        "Comparison"
    )
    print("=" * 40)

    print(
        f"Collaborative HitRate@{K}: "
        f"{mean_hit_rate:.4f}"
    )

    print(
        f"Popularity HitRate@{K}   : "
        f"{baseline_hit_rate:.4f}"
    )

    print(
        "Absolute difference      : "
        f"{difference:+.4f}"
    )

    if relative_difference is not None:
        print(
            "Relative difference      : "
            f"{relative_difference:+.1f}%"
        )
    else:
        print(
            "Relative difference      : "
            "N/A"
        )


if __name__ == "__main__":
    evaluate()