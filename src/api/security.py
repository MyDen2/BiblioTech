import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
from dotenv import load_dotenv
from jwt import InvalidTokenError
from pwdlib import PasswordHash


BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / "config" / ".env"
load_dotenv(dotenv_path=ENV_PATH)

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(
    os.getenv("JWT_EXPIRE_MINUTES", "60")
)

if not JWT_SECRET_KEY:
    raise ValueError(
        "Missing JWT_SECRET_KEY in config/.env"
    )


password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    return password_hash.verify(
        plain_password,
        hashed_password,
    )


def create_access_token(
    app_user_id: int,
    email: str,
) -> str:
    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=JWT_EXPIRE_MINUTES
        )
    )

    payload = {
        "sub": str(app_user_id),
        "email": email,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )

    except InvalidTokenError as exc:
        raise ValueError(
            "Invalid or expired token"
        ) from exc