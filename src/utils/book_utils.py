import re
import unicodedata


def normalize_text(value: str) -> str:
    if not value:
        return ""

    value = str(value).lower().strip()

    value = unicodedata.normalize("NFKD", value)
    value = "".join(
        char for char in value
        if not unicodedata.combining(char)
    )

    value = re.sub(r"\([^)]*\)", "", value)
    value = value.split(":")[0]
    value = re.sub(r"[^\w\s]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()

    return value


def build_book_key(title: str, author: str) -> str:
    normalized_title = normalize_text(title)
    normalized_author = normalize_text(author)

    return f"{normalized_title}|{normalized_author}"