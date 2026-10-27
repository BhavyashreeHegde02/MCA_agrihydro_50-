"""Password hashing and JSON Web Tokens.

Passwords are hashed with bcrypt, which is deliberately slow and salts every
hash. Tokens are signed with the application secret and carry a type claim, so a
refresh token cannot be replayed as an access token.
"""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any, Literal

import bcrypt
import jwt

from app.core.config import settings

TokenType = Literal["access", "refresh"]

#: bcrypt truncates at 72 bytes. Rejecting longer input is safer than silently
#: ignoring the tail, which would make two different passwords equivalent.
MAX_PASSWORD_BYTES = 72


class AuthError(Exception):
    """Raised when a credential or token cannot be accepted."""


def hash_password(password: str) -> str:
    encoded = password.encode("utf-8")
    if len(encoded) > MAX_PASSWORD_BYTES:
        raise AuthError(
            f"password must be at most {MAX_PASSWORD_BYTES} bytes; bcrypt would "
            "otherwise silently ignore everything beyond that"
        )
    return bcrypt.hashpw(encoded, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        # A malformed stored hash must fail closed, not raise into the handler.
        return False


def _create_token(subject: str, token_type: TokenType, expires: dt.timedelta,
                  extra: dict[str, Any] | None = None) -> str:
    now = dt.datetime.now(dt.timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires).timestamp()),
        "jti": uuid.uuid4().hex,
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(subject: str | int, extra: dict[str, Any] | None = None) -> str:
    return _create_token(
        str(subject), "access",
        dt.timedelta(minutes=settings.access_token_expire_minutes), extra,
    )


def create_refresh_token(subject: str | int) -> str:
    return _create_token(
        str(subject), "refresh", dt.timedelta(minutes=settings.refresh_token_expire_minutes)
    )


def decode_token(token: str, expected_type: TokenType | None = None) -> dict[str, Any]:
    """Decode and validate a token, or explain why it is unacceptable."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError as exc:
        raise AuthError("token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthError("token is invalid") from exc

    if expected_type and payload.get("type") != expected_type:
        raise AuthError(
            f"expected a {expected_type} token but received a "
            f"{payload.get('type', 'untyped')} one"
        )
    return payload
