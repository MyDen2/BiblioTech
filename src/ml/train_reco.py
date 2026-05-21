# Construction d'un modele capable :

## Input : livre
## Output : les livres les plus similaires

# basé sur : matrice sparse et cosine similarity

import pandas as pd
import sys
from pathlib import Path
from dotenv import load_dotenv
# Ajouter la racine du projet au PYTHONPATH
PROJECT_ROOT = Path().cwd()
sys.path.append(str(PROJECT_ROOT))

print("Project root added:", PROJECT_ROOT)

# Charger le .env
load_dotenv(PROJECT_ROOT / "config" / ".env")

print("ENV loaded from:", PROJECT_ROOT / "config" / ".env")
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity

from src.utils.s3_io import read_parquet_from_s3
from src.utils.logger import setup_logger

logger = setup_logger("train_reco")

def load_data():
    '''Chargement des données'''
    logger.info("Loading ratings_pre_ml from S3")

    ratings = read_parquet_from_s3("gold", "ratings_pre_ml.parquet")

    logger.info(f"Ratings shape BEFORE filtering: {ratings.shape}")

    # Limiter aux livres les plus populaires
    top_books = ratings["isbn"].value_counts().head(5000).index
    ratings = ratings[ratings["isbn"].isin(top_books)]

    logger.info(f"Ratings shape AFTER filtering: {ratings.shape}")

    return ratings

def build_sparse_matrix(ratings):
    '''Construction matrice sparse'''
    logger.info("Building sparse matrix")

    user_ids = ratings["user_id"].astype("category")
    book_ids = ratings["isbn"].astype("category")

    user_index = user_ids.cat.codes
    book_index = book_ids.cat.codes

    matrix = csr_matrix(
        (ratings["rating"], (user_index, book_index)),
        shape=(user_ids.cat.categories.size, book_ids.cat.categories.size)
    )

    logger.info(f"Matrix shape: {matrix.shape}")
    return matrix, book_ids.cat.categories

def compute_similarity(matrix):
    '''Similarité entre les livres : on transpose la matrice'''
    logger.info("Computing cosine similarity (item-based)")

    item_matrix = matrix.T  # livres x users

    similarity = cosine_similarity(item_matrix)

    logger.info("Similarity computation done")
    return similarity

def recommend_books(isbn, similarity, book_index_map, top_n=5):
    '''Fonction de recommandation'''
    logger.info(f"Generating recommendations for {isbn}")

    if isbn not in book_index_map:
        logger.warning("Book not found")
        return []

    idx = book_index_map[isbn]

    scores = list(enumerate(similarity[idx]))
    scores = sorted(scores, key=lambda x: x[1], reverse=True)

    # exclure lui-même
    scores = scores[1:top_n+1]

    reverse_map = {v: k for k, v in book_index_map.items()}

    recommendations = [reverse_map[i] for i, _ in scores]

    return recommendations

def main():
    ratings = load_data()

    matrix, book_categories = build_sparse_matrix(ratings)

    similarity = compute_similarity(matrix)

    # mapping isbn → index
    book_index_map = {isbn: i for i, isbn in enumerate(book_categories)}

    # test
    sample_isbn = ratings["isbn"].iloc[0]

    recos = recommend_books(sample_isbn, similarity, book_index_map)

    logger.info(f"Recommendations for {sample_isbn}: {recos}")


if __name__ == "__main__":
    main()



### Optimisation du calcul

# Le calcul de la similarité entre tous les livres étant très coûteux, une réduction du dataset a été appliquée.

# Seuls les 5000 livres les plus populaires ont été conservés.

# Cela permet de :

# - réduire la complexité du calcul
# - améliorer les performances
# - conserver les livres les plus pertinents