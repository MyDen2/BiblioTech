from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.api.database import (
    create_app_user,
    create_user_rating,
    search_books,
    get_app_user_ratings,
    get_app_user_by_email
)

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Query,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from src.api.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
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

security = HTTPBearer()

# ==============================
# Récupérér l'utilisateur
# ==============================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
):
    try:
        payload = decode_access_token(
            credentials.credentials
        )

        app_user_id = int(
            payload["sub"]
        )

        return {
            "app_user_id": app_user_id,
            "email": payload.get("email"),
        }

    except (
        ValueError,
        KeyError,
        TypeError,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
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

    password: str = Field(
        ...,
        min_length=8,
        max_length=128
    )

    age: int | None = Field(
        default=None,
        ge=10,
        le=100
    )

    country: str | None = None


class RatingCreate(BaseModel):
    book_key: str
    rating: int = Field(
        ...,
        ge=1,
        le=10
    )

class LoginRequest(BaseModel):
    email: EmailStr

    password: str = Field(
        ...,
        min_length=8,
        max_length=128
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
            "/recommend/user",
            "/users",
            "/login",
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

@app.get("/recommend/user")
def recommend_by_user(
    top_n: int = Query(
        default=5,
        ge=1,
        le=20
    ),
    current_user: dict = Depends(
        get_current_user
    ),
):
    app_user_id = current_user[
        "app_user_id"
    ]

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
def create_user(user: UserCreate):
    try:
        password_hash = hash_password(
            user.password
        )

        created_user = create_app_user(
            username=user.username,
            email=user.email,
            password_hash=password_hash,
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
# Login
# =========================

@app.post("/login")
def login(credentials: LoginRequest):
    try:
        user = get_app_user_by_email(
            credentials.email
        )

        if user is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        password_hash = user.get(
            "password_hash"
        )

        if not password_hash:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        if not verify_password(
            credentials.password,
            password_hash
        ):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        access_token = create_access_token(
            app_user_id=user["app_user_id"],
            email=user["email"],
        )

        return {
            "message": "Login successful",
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "app_user_id": user[
                    "app_user_id"
                ],
                "username": user[
                    "username"
                ],
                "email": user[
                    "email"
                ],
            }
        }

    except HTTPException:
        raise

    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Database error while logging in"
        )
        
# =========================
# Notation d'une œuvre
# =========================

@app.post("/ratings")
def add_rating(
    rating: RatingCreate,
    current_user: dict = Depends(
        get_current_user
    ),
):
    try:
        created_rating = create_user_rating(
            app_user_id=current_user[
                "app_user_id"
            ],
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
            detail="Invalid book_key"
        )

    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Database error while saving rating"
        )