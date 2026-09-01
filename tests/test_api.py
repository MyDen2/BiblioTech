import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

import src.api.app as api_module


client = TestClient(api_module.app)


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    """
    Nettoie les overrides FastAPI avant et après chaque test
    afin d'éviter qu'un utilisateur authentifié fictif ne
    contamine les autres tests.
    """
    api_module.app.dependency_overrides.clear()

    yield

    api_module.app.dependency_overrides.clear()


def authenticate_as_user(
    app_user_id=1,
    email="alice@example.com",
):
    """
    Simule un utilisateur authentifié pour les routes
    protégées sans avoir besoin de générer un vrai JWT.
    """

    api_module.app.dependency_overrides[
        api_module.get_current_user
    ] = lambda: {
        "app_user_id": app_user_id,
        "email": email,
    }


# ============================================================
# Root
# ============================================================

def test_root():
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Welcome to BiblioTech API"

    assert "/books/search" in data["endpoints"]
    assert "/recommend/book" in data["endpoints"]
    assert "/recommend/user" in data["endpoints"]
    assert "/users" in data["endpoints"]
    assert "/login" in data["endpoints"]
    assert "/ratings" in data["endpoints"]


# ============================================================
# Recherche
# ============================================================

def test_search_books_success(monkeypatch):
    fake_books = [
        {
            "book_key": "1984|george orwell",
            "title": "1984",
            "author": "George Orwell",
            "year_of_publication": 1949,
            "publisher": "Test Publisher",
            "image_url_m": None,
        }
    ]

    monkeypatch.setattr(
        api_module,
        "search_books",
        lambda query, limit: fake_books,
    )

    response = client.get(
        "/books/search?q=1984&limit=5"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["query"] == "1984"
    assert data["count"] == 1
    assert data["results"][0]["book_key"] == (
        "1984|george orwell"
    )


def test_search_books_invalid_limit():
    response = client.get(
        "/books/search?q=1984&limit=100"
    )

    assert response.status_code == 422


# ============================================================
# Recommandation livre -> livres
# ============================================================

def test_recommend_book_success(monkeypatch):
    fake_recommendations = [
        {
            "book_key": "animal farm|george orwell",
            "title": "Animal Farm",
            "author": "George Orwell",
            "similarity_score": 0.165,
        }
    ]

    monkeypatch.setattr(
        api_module,
        "recommend_books",
        lambda *args, **kwargs: fake_recommendations,
    )

    response = client.get(
        "/recommend/book",
        params={
            "book_key": "1984|george orwell",
            "top_n": 5,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["mode"] == "book_to_books"
    assert data["input_book_key"] == (
        "1984|george orwell"
    )

    assert len(data["recommendations"]) == 1


def test_recommend_book_not_found(monkeypatch):
    monkeypatch.setattr(
        api_module,
        "recommend_books",
        lambda *args, **kwargs: [],
    )

    response = client.get(
        "/recommend/book",
        params={
            "book_key": "unknown|author"
        },
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]
        == "No recommendations found"
    )


def test_recommend_book_invalid_top_n():
    response = client.get(
        "/recommend/book",
        params={
            "book_key": "1984|george orwell",
            "top_n": 50,
        },
    )

    assert response.status_code == 422


# ============================================================
# Création utilisateur
# ============================================================

def test_create_user_success(monkeypatch):
    monkeypatch.setattr(
        api_module,
        "hash_password",
        lambda password: "argon2_fake_hash",
    )

    captured = {}

    def fake_create_user(
        username,
        email,
        password_hash,
        age,
        country,
    ):
        captured["username"] = username
        captured["email"] = email
        captured["password_hash"] = password_hash
        captured["age"] = age
        captured["country"] = country

        return {
            "app_user_id": 1,
            "username": username,
            "email": email,
            "age": age,
            "country": country,
            "created_at": "2026-09-01T15:00:00",
        }

    monkeypatch.setattr(
        api_module,
        "create_app_user",
        fake_create_user,
    )

    response = client.post(
        "/users",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "MotDePasse123!",
            "age": 28,
            "country": "France",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["message"]
        == "User created successfully"
    )

    assert data["user"]["username"] == "alice"

    # Le hash doit être envoyé à la DB.
    assert (
        captured["password_hash"]
        == "argon2_fake_hash"
    )

    # Le mot de passe / hash ne doit jamais
    # apparaître dans la réponse API.
    assert "password" not in data["user"]
    assert "password_hash" not in data["user"]


def test_create_user_password_too_short():
    response = client.post(
        "/users",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "abc",
            "age": 28,
            "country": "France",
        },
    )

    assert response.status_code == 422


def test_create_user_duplicate_email(monkeypatch):
    def fake_create_user(*args, **kwargs):
        raise IntegrityError(
            "duplicate email",
            {},
            Exception("duplicate"),
        )

    monkeypatch.setattr(
        api_module,
        "hash_password",
        lambda password: "fake_hash",
    )

    monkeypatch.setattr(
        api_module,
        "create_app_user",
        fake_create_user,
    )

    response = client.post(
        "/users",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "MotDePasse123!",
            "age": 28,
            "country": "France",
        },
    )

    assert response.status_code == 409

    assert (
        response.json()["detail"]
        == "Email already exists"
    )


# ============================================================
# Login
# ============================================================

def test_login_success(monkeypatch):
    fake_user = {
        "app_user_id": 1,
        "username": "alice",
        "email": "alice@example.com",
        "password_hash": "$argon2id$fake",
        "age": 28,
        "country": "France",
        "created_at": "2026-09-01T15:00:00",
    }

    monkeypatch.setattr(
        api_module,
        "get_app_user_by_email",
        lambda email: fake_user,
    )

    monkeypatch.setattr(
        api_module,
        "verify_password",
        lambda plain, hashed: True,
    )

    monkeypatch.setattr(
        api_module,
        "create_access_token",
        lambda app_user_id, email: (
            "fake.jwt.token"
        ),
    )

    response = client.post(
        "/login",
        json={
            "email": "alice@example.com",
            "password": "MotDePasse123!",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Login successful"
    assert data["access_token"] == "fake.jwt.token"
    assert data["token_type"] == "bearer"

    assert data["user"]["app_user_id"] == 1
    assert data["user"]["username"] == "alice"

    assert "password_hash" not in data["user"]


def test_login_unknown_email(monkeypatch):
    monkeypatch.setattr(
        api_module,
        "get_app_user_by_email",
        lambda email: None,
    )

    response = client.post(
        "/login",
        json={
            "email": "unknown@example.com",
            "password": "MotDePasse123!",
        },
    )

    assert response.status_code == 401

    assert (
        response.json()["detail"]
        == "Invalid email or password"
    )


def test_login_wrong_password(monkeypatch):
    fake_user = {
        "app_user_id": 1,
        "username": "alice",
        "email": "alice@example.com",
        "password_hash": "$argon2id$fake",
    }

    monkeypatch.setattr(
        api_module,
        "get_app_user_by_email",
        lambda email: fake_user,
    )

    monkeypatch.setattr(
        api_module,
        "verify_password",
        lambda plain, hashed: False,
    )

    response = client.post(
        "/login",
        json={
            "email": "alice@example.com",
            "password": "MauvaisMotDePasse",
        },
    )

    assert response.status_code == 401

    assert (
        response.json()["detail"]
        == "Invalid email or password"
    )


# ============================================================
# Ratings protégés par JWT
# ============================================================

def test_rating_requires_authentication():
    response = client.post(
        "/ratings",
        json={
            "book_key": "1984|george orwell",
            "rating": 10,
        },
    )

    assert response.status_code == 401


def test_rating_success_authenticated(
    monkeypatch,
):
    authenticate_as_user(
        app_user_id=1
    )

    def fake_create_rating(
        app_user_id,
        book_key,
        rating,
    ):
        return {
            "rating_id": 1,
            "app_user_id": app_user_id,
            "book_key": book_key,
            "rating": rating,
            "created_at": (
                "2026-09-01T15:25:17"
            ),
        }

    monkeypatch.setattr(
        api_module,
        "create_user_rating",
        fake_create_rating,
    )

    response = client.post(
        "/ratings",
        json={
            "book_key": "1984|george orwell",
            "rating": 10,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["message"]
        == "Rating saved successfully"
    )

    # L'app_user_id vient du JWT/dependency,
    # pas du JSON envoyé par le client.
    assert data["rating"]["app_user_id"] == 1

    assert (
        data["rating"]["book_key"]
        == "1984|george orwell"
    )

    assert data["rating"]["rating"] == 10


def test_rating_above_10_rejected():
    authenticate_as_user()

    response = client.post(
        "/ratings",
        json={
            "book_key": "1984|george orwell",
            "rating": 11,
        },
    )

    assert response.status_code == 422


def test_rating_below_1_rejected():
    authenticate_as_user()

    response = client.post(
        "/ratings",
        json={
            "book_key": "1984|george orwell",
            "rating": 0,
        },
    )

    assert response.status_code == 422


# ============================================================
# Recommandation utilisateur protégée
# ============================================================

def test_recommend_user_requires_authentication():
    response = client.get(
        "/recommend/user"
    )

    assert response.status_code == 401


def test_recommend_user_success(monkeypatch):
    authenticate_as_user(
        app_user_id=1
    )

    fake_ratings = [
        {
            "app_user_id": 1,
            "book_key": "1984|george orwell",
            "rating": 10,
        }
    ]

    fake_recommendations = [
        {
            "book_key": (
                "animal farm|george orwell"
            ),
            "title": "Animal Farm",
            "author": "George Orwell",
            "similarity_score": 0.165,
        }
    ]

    monkeypatch.setattr(
        api_module,
        "get_app_user_ratings",
        lambda app_user_id: fake_ratings,
    )

    monkeypatch.setattr(
        api_module,
        "recommend_for_app_user",
        lambda *args, **kwargs: (
            fake_recommendations
        ),
    )

    response = client.get(
        "/recommend/user?top_n=5"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["mode"] == "user_to_books"

    # L'identité vient de l'utilisateur
    # authentifié.
    assert data["app_user_id"] == 1

    assert (
        data["recommendations"][0][
            "book_key"
        ]
        == "animal farm|george orwell"
    )


def test_recommend_user_without_ratings(
    monkeypatch,
):
    authenticate_as_user(
        app_user_id=1
    )

    monkeypatch.setattr(
        api_module,
        "get_app_user_ratings",
        lambda app_user_id: [],
    )

    response = client.get(
        "/recommend/user"
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]
        == "No ratings found for this user"
    )


def test_recommend_user_not_enough_liked_books(
    monkeypatch,
):
    authenticate_as_user(
        app_user_id=1
    )

    fake_ratings = [
        {
            "app_user_id": 1,
            "book_key": "some book|author",
            "rating": 4,
        }
    ]

    monkeypatch.setattr(
        api_module,
        "get_app_user_ratings",
        lambda app_user_id: fake_ratings,
    )

    monkeypatch.setattr(
        api_module,
        "recommend_for_app_user",
        lambda *args, **kwargs: [],
    )

    response = client.get(
        "/recommend/user"
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]
        == (
            "Not enough liked books to generate "
            "personalized recommendations"
        )
    )


def test_recommend_user_invalid_top_n():
    authenticate_as_user()

    response = client.get(
        "/recommend/user?top_n=50"
    )

    assert response.status_code == 422