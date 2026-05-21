# from pathlib import Path

# import joblib
# from fastapi import FastAPI, HTTPException, Query

# from src.utils.s3_io import read_parquet_from_s3

# MODEL_DIR = Path("models/reco")

# app = FastAPI(
#     title="BiblioTech API",
#     description="API de recommandation de livres",
#     version="1.1.0"
# )


# # =========================
# # Chargement des artefacts
# # =========================

# similarity = joblib.load(MODEL_DIR / "similarity.joblib")
# book_index_map = joblib.load(MODEL_DIR / "book_index_map.joblib")
# book_metadata = joblib.load(MODEL_DIR / "book_metadata.joblib")

# # Nécessaire pour la recommandation personnalisée par utilisateur
# ratings = read_parquet_from_s3("gold", "ratings_pre_ml.parquet")


# # =========================
# # Fonctions de recommandation
# # =========================

# def recommend_books(isbn: str, top_n: int = 5):
#     if isbn not in book_index_map:
#         raise HTTPException(status_code=404, detail="ISBN not found in model")

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


# def recommend_for_user(user_id: int, top_n: int = 5):
#     user_ratings = ratings[ratings["user_id"] == user_id]

#     if user_ratings.empty:
#         raise HTTPException(status_code=404, detail="User not found")

#     liked_books = user_ratings[user_ratings["rating"] >= 7]["isbn"].tolist()
#     already_seen = set(user_ratings["isbn"].tolist())

#     if not liked_books:
#         raise HTTPException(
#             status_code=404,
#             detail="No liked books found for this user"
#         )

#     reverse_map = {v: k for k, v in book_index_map.items()}
#     candidate_scores = {}

#     for isbn in liked_books:
#         if isbn not in book_index_map:
#             continue

#         idx = book_index_map[isbn]
#         scores = list(enumerate(similarity[idx]))

#         for book_idx, score in scores:
#             candidate_isbn = reverse_map[book_idx]

#             if candidate_isbn in already_seen:
#                 continue

#             candidate_scores[candidate_isbn] = (
#                 candidate_scores.get(candidate_isbn, 0) + float(score)
#             )

#     sorted_candidates = sorted(
#         candidate_scores.items(),
#         key=lambda x: x[1],
#         reverse=True
#     )[:top_n]

#     recommendations = []

#     for isbn, score in sorted_candidates:
#         if isbn in book_metadata.index:
#             recommendations.append({
#                 "isbn": isbn,
#                 "title": book_metadata.loc[isbn, "title"],
#                 "author": book_metadata.loc[isbn, "author"],
#                 "similarity_score": round(float(score), 3)
#             })

#     return recommendations


# # =========================
# # Routes API
# # =========================

# @app.get("/")
# def root():
#     return {
#         "message": "Welcome to BiblioTech API",
#         "endpoints": [
#             "/recommend/{isbn}",
#             "/recommend/user/{user_id}",
#             "/docs"
#         ]
#     }


# @app.get("/recommend/{isbn}")
# def recommend_by_book(
#     isbn: str,
#     top_n: int = Query(default=5, ge=1, le=20)
# ):
#     return {
#         "mode": "book_to_books",
#         "input_isbn": isbn,
#         "recommendations": recommend_books(isbn, top_n)
#     }


# @app.get("/recommend/user/{user_id}")
# def recommend_by_user(
#     user_id: int,
#     top_n: int = Query(default=5, ge=1, le=20)
# ):
#     return {
#         "mode": "user_to_books",
#         "user_id": user_id,
#         "recommendations": recommend_for_user(user_id, top_n)
#     }

from fastapi import FastAPI, HTTPException, Query

from src.ml.recommender import (
    load_artifacts,
    load_user_ratings,
    recommend_books,
    recommend_for_user,
)

app = FastAPI(
    title="BiblioTech API",
    description="API de recommandation de livres",
    version="1.1.0"
)

similarity, book_index_map, book_metadata = load_artifacts()
ratings = load_user_ratings()


@app.get("/")
def root():
    return {
        "message": "Welcome to BiblioTech API",
        "endpoints": [
            "/recommend/book/{isbn}",
            "/recommend/user/{user_id}",
            "/docs"
        ]
    }


@app.get("/recommend/book/{isbn}")
def recommend_by_book(
    isbn: str,
    top_n: int = Query(default=5, ge=1, le=20)
):
    recommendations = recommend_books(
        isbn,
        similarity,
        book_index_map,
        book_metadata,
        top_n=top_n,
    )

    if not recommendations:
        raise HTTPException(status_code=404, detail="No recommendations found")

    return {
        "mode": "book_to_books",
        "input_isbn": isbn,
        "recommendations": recommendations
    }


@app.get("/recommend/user/{user_id}")
def recommend_by_user(
    user_id: int,
    top_n: int = Query(default=5, ge=1, le=20)
):
    recommendations = recommend_for_user(
        user_id,
        ratings,
        similarity,
        book_index_map,
        book_metadata,
        top_n=top_n,
    )

    if not recommendations:
        raise HTTPException(status_code=404, detail="No recommendations found")

    return {
        "mode": "user_to_books",
        "user_id": user_id,
        "recommendations": recommendations
    }