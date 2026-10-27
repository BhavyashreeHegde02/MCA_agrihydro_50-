"""Shared FastAPI dependencies: the session, the current user, ownership checks."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import AuthError, decode_token
from app.db.models import Farm, Farmer, Field, FieldCrop, User
from app.db.session import get_db

bearer_scheme = HTTPBearer(auto_error=False)

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
) -> User:
    """Resolve the bearer token to an active user."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "NOT_AUTHENTICATED",
                    "message": "This endpoint requires an Authorization: Bearer <token> header."},
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_token(credentials.credentials, expected_type="access")
    except AuthError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "INVALID_TOKEN", "message": str(error)},
            headers={"WWW-Authenticate": "Bearer"},
        ) from error

    user = db.get(User, int(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "USER_INACTIVE",
                    "message": "This account no longer exists or has been deactivated."},
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_farmer(db: DbSession, user: CurrentUser) -> Farmer:
    farmer = db.scalar(select(Farmer).where(Farmer.user_id == user.id))
    if farmer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "FARMER_PROFILE_MISSING",
                    "message": "This account has no farmer profile."},
        )
    return farmer


CurrentFarmer = Annotated[Farmer, Depends(get_current_farmer)]


def require_researcher(user: CurrentUser) -> User:
    """Gate the research dashboard.

    A farmer must never see another farmer's records, and the admin endpoints
    aggregate across all of them.
    """
    if user.role not in {"researcher", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "FORBIDDEN",
                    "message": "This endpoint is restricted to research and admin accounts."},
        )
    return user


ResearchUser = Annotated[User, Depends(require_researcher)]


# --------------------------------------------------------------------------
# Ownership
# --------------------------------------------------------------------------
def _forbidden(kind: str, identifier: int) -> HTTPException:
    # Deliberately identical to the not-found response: telling an attacker that
    # a record exists but belongs to someone else is itself a disclosure.
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"error": "NOT_FOUND", "message": f"No {kind} with id {identifier} was found."},
    )


def owned_farm(db: Session, farmer: Farmer, farm_id: int) -> Farm:
    farm = db.get(Farm, farm_id)
    if farm is None or farm.farmer_id != farmer.id:
        raise _forbidden("farm", farm_id)
    return farm


def owned_field(db: Session, farmer: Farmer, field_id: int) -> Field:
    field = db.get(Field, field_id)
    if field is None:
        raise _forbidden("field", field_id)
    farm = db.get(Farm, field.farm_id)
    if farm is None or farm.farmer_id != farmer.id:
        raise _forbidden("field", field_id)
    return field


def owned_field_crop(db: Session, farmer: Farmer, field_crop_id: int) -> FieldCrop:
    planting = db.get(FieldCrop, field_crop_id)
    if planting is None:
        raise _forbidden("planting", field_crop_id)
    owned_field(db, farmer, planting.field_id)
    return planting
