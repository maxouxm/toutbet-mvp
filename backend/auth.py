from __future__ import annotations

import datetime as dt
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

import crud
import models
import schemas
from database import get_db
from deps import get_refresh_cookie
from security import create_access_token, create_refresh_token, safe_decode_token
from settings import settings


router = APIRouter(prefix="/auth", tags=["auth"])

def _enforce_origin(request: Request) -> None:
    """
    Pragmatic CSRF mitigation for cookie-based endpoints.
    If Origin is present (browsers), it must match allowed frontend origins.
    """
    origin = request.headers.get("origin")
    if origin and origin not in settings.parsed_origins():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid origin")


def _set_refresh_cookie(resp: Response, refresh_token: str) -> None:
    resp.set_cookie(
        key="tb_refresh",
        value=refresh_token,
        httponly=True,
        secure=bool(settings.cookie_secure),
        samesite=settings.cookie_samesite,
        max_age=int(dt.timedelta(days=settings.refresh_token_expire_days).total_seconds()),
        path="/",
    )


def _clear_refresh_cookie(resp: Response) -> None:
    resp.delete_cookie(key="tb_refresh", path="/")


@router.post("/register", response_model=schemas.UserOut, status_code=201)
def register(payload: schemas.RegisterIn, request: Request, db: Session = Depends(get_db)):
    if not payload.accept_terms:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Terms must be accepted")
    u = crud.create_user(db, email=str(payload.email).lower(), password=payload.password)
    u.terms_accepted_at = dt.datetime.now(dt.timezone.utc)
    u.terms_version = "v1"
    db.commit()
    return schemas.UserOut(id=u.id, email=u.email, role=u.role.value, balance_tokens=u.balance_tokens)


@router.post("/login", response_model=schemas.TokenPair)
def login(payload: schemas.LoginIn, request: Request, resp: Response, db: Session = Depends(get_db)):
    u = crud.authenticate(db, email=str(payload.email).lower(), password=payload.password)
    access = create_access_token(sub=str(u.id), role=u.role.value)
    refresh, jti = create_refresh_token(sub=str(u.id), role=u.role.value)
    crud.create_refresh_session(db, user_id=u.id, jti=jti)
    _set_refresh_cookie(resp, refresh)
    crud.create_audit(db, user_id=u.id, action="auth.login", entity_type="user", entity_id=u.id, message="User logged in")
    db.commit()
    return schemas.TokenPair(access_token=access)


@router.post("/refresh", response_model=schemas.TokenPair)
def refresh(request: Request, resp: Response, refresh_cookie: str = Depends(get_refresh_cookie), db: Session = Depends(get_db)):
    _enforce_origin(request)
    payload = safe_decode_token(refresh_cookie)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    sub = payload.get("sub")
    role = payload.get("role")
    jti = payload.get("jti")
    if not sub or not role or not str(sub).isdigit():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    if not jti or not isinstance(jti, str):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    u = db.get(models.User, int(sub))
    if not u:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    session = crud.get_refresh_session(db, jti=jti)
    if not session or session.revoked or session.user_id != u.id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh session revoked")
    exp = session.expires_at
    # SQLite may round-trip tz-naive datetimes; treat naive as UTC.
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=dt.timezone.utc)
    else:
        exp = exp.astimezone(dt.timezone.utc)
    if exp <= dt.datetime.now(dt.timezone.utc):
        session.revoked = True
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh session expired")

    # Rotate refresh token on refresh (mitigates replay)
    session.revoked = True
    new_refresh, new_jti = create_refresh_token(sub=str(u.id), role=u.role.value)
    crud.create_refresh_session(db, user_id=u.id, jti=new_jti)
    _set_refresh_cookie(resp, new_refresh)
    access = create_access_token(sub=str(u.id), role=u.role.value)
    crud.create_audit(db, user_id=u.id, action="auth.refresh", entity_type="user", entity_id=u.id, message="Token refreshed")
    db.commit()
    return schemas.TokenPair(access_token=access)


@router.post("/logout", response_model=schemas.Msg)
def logout(request: Request, resp: Response, refresh_cookie: Optional[str] = Depends(get_refresh_cookie), db: Session = Depends(get_db)):
    _enforce_origin(request)
    # Best-effort audit (refresh may be invalid)
    payload = safe_decode_token(refresh_cookie) if refresh_cookie else None
    user_id = int(payload["sub"]) if payload and str(payload.get("sub", "")).isdigit() else None
    jti = payload.get("jti") if payload else None
    if isinstance(jti, str):
        crud.revoke_refresh_session(db, jti=jti)
    if user_id:
        crud.create_audit(db, user_id=user_id, action="auth.logout", entity_type="user", entity_id=user_id, message="User logged out")
        db.commit()
    _clear_refresh_cookie(resp)
    return schemas.Msg(message="Logged out")

