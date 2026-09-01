import pandas as pd

from src.ml.recommender import (
    recommend_books,
    recommend_for_app_user,
)


def build_test_data():
    similarity = [
        [1.0, 0.9, 0.8, 0.1],
        [0.9, 1.0, 0.4, 0.2],
        [0.8, 0.4, 1.0, 0.7],
        [0.1, 0.2, 0.7, 1.0],
    ]

    book_index_map = {
        "book a|author a": 0,
        "book b|author b": 1,
        "book c|author c": 2,
        "book d|author d": 3,
    }

    book_metadata = pd.DataFrame(
        [
            {
                "book_key": "book a|author a",
                "title": "Book A",
                "author": "Author A",
            },
            {
                "book_key": "book b|author b",
                "title": "Book B",
                "author": "Author B",
            },
            {
                "book_key": "book c|author c",
                "title": "Book C",
                "author": "Author C",
            },
            {
                "book_key": "book d|author d",
                "title": "Book D",
                "author": "Author D",
            },
        ]
    ).set_index("book_key")

    return similarity, book_index_map, book_metadata


def test_recommend_books_returns_top_results():
    similarity, book_index_map, book_metadata = build_test_data()

    results = recommend_books(
        "book a|author a",
        similarity,
        book_index_map,
        book_metadata,
        top_n=2,
    )

    assert len(results) == 2

    assert results[0]["book_key"] == "book b|author b"
    assert results[0]["similarity_score"] == 0.9

    assert results[1]["book_key"] == "book c|author c"
    assert results[1]["similarity_score"] == 0.8


def test_recommend_books_excludes_input_book():
    similarity, book_index_map, book_metadata = build_test_data()

    results = recommend_books(
        "book a|author a",
        similarity,
        book_index_map,
        book_metadata,
        top_n=3,
    )

    returned_keys = {
        item["book_key"]
        for item in results
    }

    assert "book a|author a" not in returned_keys


def test_recommend_books_unknown_book_returns_empty_list():
    similarity, book_index_map, book_metadata = build_test_data()

    results = recommend_books(
        "unknown|author",
        similarity,
        book_index_map,
        book_metadata,
    )

    assert results == []


def test_recommend_for_app_user_returns_recommendations():
    similarity, book_index_map, book_metadata = build_test_data()

    user_ratings = [
        {
            "book_key": "book a|author a",
            "rating": 10,
        }
    ]

    results = recommend_for_app_user(
        user_ratings,
        similarity,
        book_index_map,
        book_metadata,
        top_n=2,
    )

    assert len(results) == 2

    assert results[0]["book_key"] == "book b|author b"
    assert results[1]["book_key"] == "book c|author c"


def test_recommend_for_app_user_excludes_seen_books():
    similarity, book_index_map, book_metadata = build_test_data()

    user_ratings = [
        {
            "book_key": "book a|author a",
            "rating": 10,
        },
        {
            "book_key": "book b|author b",
            "rating": 8,
        },
    ]

    results = recommend_for_app_user(
        user_ratings,
        similarity,
        book_index_map,
        book_metadata,
        top_n=5,
    )

    returned_keys = {
        item["book_key"]
        for item in results
    }

    assert "book a|author a" not in returned_keys
    assert "book b|author b" not in returned_keys


def test_recommend_for_app_user_no_ratings_returns_empty_list():
    similarity, book_index_map, book_metadata = build_test_data()

    results = recommend_for_app_user(
        [],
        similarity,
        book_index_map,
        book_metadata,
    )

    assert results == []


def test_recommend_for_app_user_no_liked_books_returns_empty_list():
    similarity, book_index_map, book_metadata = build_test_data()

    user_ratings = [
        {
            "book_key": "book a|author a",
            "rating": 4,
        },
        {
            "book_key": "book b|author b",
            "rating": 6,
        },
    ]

    results = recommend_for_app_user(
        user_ratings,
        similarity,
        book_index_map,
        book_metadata,
    )

    assert results == []


def test_recommend_for_app_user_ignores_books_outside_model():
    similarity, book_index_map, book_metadata = build_test_data()

    user_ratings = [
        {
            "book_key": "outside model|author",
            "rating": 10,
        }
    ]

    results = recommend_for_app_user(
        user_ratings,
        similarity,
        book_index_map,
        book_metadata,
    )

    assert results == []