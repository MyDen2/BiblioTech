from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.api.database import (
    create_app_user,
    create_user_rating,
    search_books,
    get_app_user_ratings
)

from src.ml.recommender import (
    load_artifacts,
    recommend_books,
    recommend_for_app_user,
)


app = FastAPI(
    title="BiblioTech API",
    description="API de recommandation de livres",
    version="2.0.0"
)


# =========================
# Chargement des artefacts ML
# =========================

similarity, book_index_map, book_metadata = load_artifacts()

# =========================
# Modèles Pydantic
# =========================

class UserCreate(BaseModel):
    username: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    email: EmailStr

    age: int | None = Field(
        default=None,
        ge=10,
        le=100
    )

    country: str | None = None


class RatingCreate(BaseModel):
    app_user_id: int
    book_key: str
    rating: int = Field(
        ...,
        ge=1,
        le=10
    )


# =========================
# Accueil
# =========================

@app.get("/")
def root():
    return {
        "message": "Welcome to BiblioTech API",
        "endpoints": [
            "/books/search",
            "/recommend/book",
            "/recommend/user/{user_id}",
            "/users",
            "/ratings",
            "/docs"
        ]
    }


# =========================
# Recherche de livres
# =========================

@app.get("/books/search")
def search_books_route(
    q: str,
    limit: int = Query(
        default=20,
        ge=1,
        le=50
    )
):
    try:
        results = search_books(
            q,
            limit
        )

        return {
            "query": q,
            "count": len(results),
            "results": results
        }

    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Database error while searching books"
        )


# =========================
# Recommandation par œuvre
# =========================

@app.get("/recommend/book")
def recommend_by_book(
    book_key: str = Query(...),
    top_n: int = Query(
        default=5,
        ge=1,
        le=20
    )
):
    recommendations = recommend_books(
        book_key,
        similarity,
        book_index_map,
        book_metadata,
        top_n=top_n,
    )

    if not recommendations:
        raise HTTPException(
            status_code=404,
            detail="No recommendations found"
        )

    return {
        "mode": "book_to_books",
        "input_book_key": book_key,
        "recommendations": recommendations
    }


# =========================
# Recommandation utilisateur
# =========================

@app.get("/recommend/user/{app_user_id}")
def recommend_by_user(
    app_user_id: int,
    top_n: int = Query(
        default=5,
        ge=1,
        le=20
    )
):
    user_ratings = get_app_user_ratings(
        app_user_id
    )

    if not user_ratings:
        raise HTTPException(
            status_code=404,
            detail="No ratings found for this user"
        )

    recommendations = recommend_for_app_user(
        user_ratings,
        similarity,
        book_index_map,
        book_metadata,
        top_n=top_n
    )

    if not recommendations:
        raise HTTPException(
            status_code=404,
            detail=(
                "Not enough liked books to generate "
                "personalized recommendations"
            )
        )

    return {
        "mode": "user_to_books",
        "app_user_id": app_user_id,
        "recommendations": recommendations
    }


# =========================
# Création utilisateur
# =========================

@app.post("/users")
def create_user(
    user: UserCreate
):
    try:
        created_user = create_app_user(
            username=user.username,
            email=user.email,
            age=user.age,
            country=user.country
        )

        return {
            "message": "User created successfully",
            "user": created_user
        }

    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Email already exists"
        )

    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Database error while creating user"
        )


# =========================
# Notation d'une œuvre
# =========================

@app.post("/ratings")
def add_rating(
    rating: RatingCreate
):
    try:
        created_rating = create_user_rating(
            app_user_id=rating.app_user_id,
            book_key=rating.book_key,
            rating=rating.rating
        )

        return {
            "message": "Rating saved successfully",
            "rating": created_rating
        }

    except IntegrityError:
        raise HTTPException(
            status_code=400,
            detail="Invalid app_user_id or book_key"
        )

    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Database error while saving rating"
        )