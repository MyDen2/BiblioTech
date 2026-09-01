from src.utils.book_utils import normalize_text, build_book_key


def test_normalize_text_lowercase():
    assert normalize_text("George Orwell") == "george orwell"


def test_normalize_text_removes_accents():
    assert normalize_text("Émile Zola") == "emile zola"


def test_normalize_text_removes_parentheses():
    assert (
        normalize_text("The Sound and the Fury (Vintage International)")
        == "the sound and the fury"
    )


def test_normalize_text_removes_subtitle():
    assert normalize_text("Dune: A Novel") == "dune"


def test_normalize_text_removes_punctuation():
    assert normalize_text("Harry Potter's World!") == "harry potter s world"


def test_normalize_text_removes_extra_spaces():
    assert normalize_text("  George   Orwell  ") == "george orwell"


def test_normalize_text_empty_value():
    assert normalize_text("") == ""


def test_build_book_key():
    assert build_book_key("1984", "George Orwell") == "1984|george orwell"


def test_build_book_key_with_accents():
    assert (
        build_book_key("Au bonheur des dames", "Émile Zola")
        == "au bonheur des dames|emile zola"
    )


def test_build_book_key_normalizes_title_and_author():
    assert (
        build_book_key(
            "The Sound and the Fury (Vintage International)",
            "WILLIAM FAULKNER",
        )
        == "the sound and the fury|william faulkner"
    )