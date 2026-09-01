import importlib

from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError


app_module = importlib.import_module("src.api.app")
client = TestClient(app_module.app)


# =========================
# Accueil
# =========================

def test_root():
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Welcome to BiblioTech API"
    assert "/books/search" in data["endpoints"]
    assert "/recommend/book" in data["endpoints"]


# =========================
# Recherche
# =========================

def test_search_books_success(monkeypatch):
    fake_results = [
        {
            "book_key": "1984|george orwell",
            "title": "1984",
            "author": "George Orwell",
            "year_of_publication": 1949,
            "publisher": "Test Publisher",
            "image_url_m": "https://example.com/1984.jpg",
        }
    ]

    monkeypatch.setattr(
        app_module,
        "search_books",
        lambda query, limit: fake_results,
    )

    response = client.get(
        "/books/search",
        params={
            "q": "1984",
            "limit": 20,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["query"] == "1984"
    assert data["count"] == 1
    assert data["results"][0]["book_key"] == "1984|george orwell"


def test_search_books_invalid_limit():
    response = client.get(
        "/books/search",
        params={
            "q": "1984",
            "limit": 100,
        },
    )

    assert response.status_code == 422


# =========================
# Recommandation par livre
# =========================

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
        app_module,
        "recommend_books",
        lambda book_key,
               similarity,
               book_index_map,
               book_metadata,
               top_n: fake_recommendations,
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
    assert data["input_book_key"] == "1984|george orwell"
    assert len(data["recommendations"]) == 1


def test_recommend_book_not_found(monkeypatch):
    monkeypatch.setattr(
        app_module,
        "recommend_books",
        lambda *args, **kwargs: [],
    )

    response = client.get(
        "/recommend/book",
        params={
            "book_key": "unknown|author",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "No recommendations found"


def test_recommend_book_invalid_top_n():
    response = client.get(
        "/recommend/book",
        params={
            "book_key": "1984|george orwell",
            "top_n": 50,
        },
    )

    assert response.status_code == 422


# =========================
# Recommandation utilisateur
# =========================

def test_recommend_user_success(monkeypatch):
    fake_ratings = [
        {
            "app_user_id": 1,
            "book_key": "1984|george orwell",
            "rating": 10,
        }
    ]

    fake_recommendations = [
        {
            "book_key": "lord of the flies|william gerald golding",
            "title": "Lord of the Flies",
            "author": "William Gerald Golding",
            "similarity_score": 0.255,
        }
    ]

    monkeypatch.setattr(
        app_module,
        "get_app_user_ratings",
        lambda app_user_id: fake_ratings,
    )

    monkeypatch.setattr(
        app_module,
        "recommend_for_app_user",
        lambda user_ratings,
               similarity,
               book_index_map,
               book_metadata,
               top_n: fake_recommendations,
    )

    response = client.get(
        "/recommend/user/1",
        params={"top_n": 5},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["mode"] == "user_to_books"
    assert data["app_user_id"] == 1
    assert len(data["recommendations"]) == 1


def test_recommend_user_without_ratings(monkeypatch):
    monkeypatch.setattr(
        app_module,
        "get_app_user_ratings",
        lambda app_user_id: [],
    )

    response = client.get("/recommend/user/999")

    assert response.status_code == 404
    assert (
        response.json()["detail"]
        == "No ratings found for this user"
    )


# =========================
# Création utilisateur
# =========================

def test_create_user_success(monkeypatch):
    fake_user = {
        "app_user_id": 1,
        "username": "test_bibliotech",
        "email": "test@example.com",
        "age": 25,
        "country": "France",
        "created_at": "2026-09-01T10:00:00",
    }

    monkeypatch.setattr(
        app_module,
        "create_app_user",
        lambda username, email, age, country: fake_user,
    )

    response = client.post(
        "/users",
        json={
            "username": "test_bibliotech",
            "email": "test@example.com",
            "age": 25,
            "country": "France",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "User created successfully"
    assert data["user"]["app_user_id"] == 1


def test_create_user_duplicate_email(monkeypatch):
    def fake_create_user(*args, **kwargs):
        raise IntegrityError(
            "INSERT",
            {},
            Exception("duplicate email"),
        )

    monkeypatch.setattr(
        app_module,
        "create_app_user",
        fake_create_user,
    )

    response = client.post(
        "/users",
        json={
            "username": "test_user",
            "email": "duplicate@example.com",
            "age": 25,
            "country": "France",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Email already exists"


# =========================
# Notes
# =========================

def test_create_rating_success(monkeypatch):
    fake_rating = {
        "rating_id": 1,
        "app_user_id": 1,
        "book_key": "1984|george orwell",
        "rating": 10,
        "created_at": "2026-09-01T10:00:00",
    }

    monkeypatch.setattr(
        app_module,
        "create_user_rating",
        lambda app_user_id, book_key, rating: fake_rating,
    )

    response = client.post(
        "/ratings",
        json={
            "app_user_id": 1,
            "book_key": "1984|george orwell",
            "rating": 10,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Rating saved successfully"
    assert data["rating"]["rating"] == 10


def test_rating_above_10_is_rejected():
    response = client.post(
        "/ratings",
        json={
            "app_user_id": 1,
            "book_key": "1984|george orwell",
            "rating": 11,
        },
    )

    assert response.status_code == 422


def test_rating_below_1_is_rejected():
    response = client.post(
        "/ratings",
        json={
            "app_user_id": 1,
            "book_key": "1984|george orwell",
            "rating": 0,
        },
    )

    assert response.status_code == 422