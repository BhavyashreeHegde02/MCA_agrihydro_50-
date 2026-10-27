"""Registration, login and token refresh."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.core.config import settings
from app.core.security import (
    AuthError, create_access_token, create_refresh_token, decode_token,
    hash_password, verify_password,
)
from app.db.models import Farmer, User
from app.schemas.common import Message
from app.schemas.core import (
    LoginRequest, RefreshRequest, RegisterRequest, TokenPair, UserOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: DbSession) -> User:
    """Create an account and its farmer profile in one step.

    A user without a farmer profile cannot own a farm, so creating the two
    together removes a state the rest of the API would have to guard against.
    """
    existing = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "EMAIL_ALREADY_REGISTERED",
                    "message": "An account with this email address already exists.",
                    "details": {"field": "email"}},
        )

    try:
        password_hash = hash_password(payload.password)
    except AuthError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "INVALID_PASSWORD", "message": str(error)},
        ) from error

    user = User(
        email=payload.email.lower(),
        password_hash=password_hash,
        full_name=payload.full_name,
        phone=payload.phone,
        role="farmer",
    )
    db.add(user)
    db.flush()

    db.add(
        Farmer(
            user_id=user.id, full_name=payload.full_name, phone=payload.phone,
            state=payload.state, district=payload.district, taluk=payload.taluk,
        )
    )
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenPair)
def login(payload: LoginRequest, db: DbSession) -> TokenPair:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    # The same message for an unknown address and a wrong password, so the
    # endpoint cannot be used to enumerate registered accounts.
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "INVALID_CREDENTIALS",
                    "message": "Email address or password is incorrect."},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "ACCOUNT_DISABLED", "message": "This account is disabled."},
        )

    return TokenPair(
        access_token=create_access_token(user.id, {"role": user.role}),
        refresh_token=create_refresh_token(user.id),
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: DbSession) -> TokenPair:
    try:
        claims = decode_token(payload.refresh_token, expected_type="refresh")
    except AuthError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "INVALID_REFRESH_TOKEN", "message": str(error)},
        ) from error

    user = db.get(User, int(claims["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "USER_INACTIVE", "message": "This account is no longer active."},
        )

    return TokenPair(
        access_token=create_access_token(user.id, {"role": user.role}),
        refresh_token=create_refresh_token(user.id),
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser) -> User:
    return user


@router.post("/logout", response_model=Message)
def logout(user: CurrentUser) -> Message:
    """Client-side logout.

    Tokens are stateless and self-expiring, so there is nothing to revoke
    server-side without a denylist. Saying so is better than implying a
    server-side session that does not exist.
    """
    _ = user
    return Message(
        message="Discard the stored tokens on the client. Access tokens expire on "
                "their own; there is no server-side session to end."
    )
