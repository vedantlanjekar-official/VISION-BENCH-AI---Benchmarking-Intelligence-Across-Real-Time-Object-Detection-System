from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.db.models import RefreshToken, User
from app.db.session import get_session
from app.schemas.auth import RefreshRequest, RegisterRequest, TokenResponse
from app.api.deps import get_current_user
from app.services.audit import write_audit_log
from app.services.rate_limit import hit
from app.services.client_ip import get_client_ip


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(request: Request, payload: RegisterRequest, session: Session = Depends(get_session)) -> TokenResponse:
    ip = get_client_ip(request)
    ua = request.headers.get("user-agent")
    existing = session.exec(select(User).where(User.email == payload.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    any_user = session.exec(select(User.id).limit(1)).first()
    user = User(email=payload.email, password_hash=hash_password(payload.password), role="admin" if not any_user else "user")
    session.add(user)
    session.commit()
    access = create_access_token(subject=user.email)
    refresh = generate_refresh_token()
    settings = get_settings()
    rt = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(refresh),
        expires_at=datetime.utcnow() + timedelta(days=int(settings.jwt_refresh_token_days)),
    )
    session.add(rt)
    session.commit()
    write_audit_log(
        session,
        actor_user_id=user.id,
        action="auth.register",
        target_type="user",
        target_id=user.id,
        ip=ip,
        user_agent=ua,
        before=None,
        after={"email": user.email, "role": user.role},
    )
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/login", response_model=TokenResponse)
def login(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
) -> TokenResponse:
    ip = get_client_ip(request)
    ua = request.headers.get("user-agent")
    email = (form.username or "").strip().lower()
    # layered limits: IP, email, and IP+email (slows credential stuffing)
    rl = hit(f"auth:login:ip:{ip}", limit=10, window_seconds=60)
    rl2 = hit(f"auth:login:email:{email}", limit=10, window_seconds=60) if email else None
    rl3 = hit(f"auth:login:ip_email:{ip}:{email}", limit=5, window_seconds=60) if ip and email else None
    if not rl.allowed:
        write_audit_log(
            session,
            actor_user_id=None,
            action="auth.rate_limited",
            target_type="auth.login",
            target_id=None,
            ip=ip,
            user_agent=ua,
            after={"remaining": rl.remaining, "reset_seconds": rl.reset_seconds},
        )
        raise HTTPException(
            status_code=429,
            detail="Too many login attempts",
            headers={"Retry-After": str(rl.reset_seconds)},
        )
    if rl2 is not None and not rl2.allowed:
        raise HTTPException(status_code=429, detail="Too many login attempts", headers={"Retry-After": str(rl2.reset_seconds)})
    if rl3 is not None and not rl3.allowed:
        raise HTTPException(status_code=429, detail="Too many login attempts", headers={"Retry-After": str(rl3.reset_seconds)})
    user = session.exec(select(User).where(User.email == email)).first()
    if not user or not verify_password(form.password, user.password_hash):
        write_audit_log(
            session,
            actor_user_id=None,
            action="auth.login_failed",
            target_type="user",
            target_id=None,
            ip=ip,
            user_agent=ua,
            before=None,
            after={"email": email},
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access = create_access_token(subject=user.email)
    refresh = generate_refresh_token()
    settings = get_settings()
    rt = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(refresh),
        expires_at=datetime.utcnow() + timedelta(days=int(settings.jwt_refresh_token_days)),
    )
    session.add(rt)
    session.commit()
    write_audit_log(
        session,
        actor_user_id=user.id,
        action="auth.login",
        target_type="user",
        target_id=user.id,
        ip=ip,
        user_agent=ua,
        before=None,
        after={"email": user.email},
    )
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse)
def refresh(request: Request, payload: RefreshRequest, session: Session = Depends(get_session)) -> TokenResponse:
    ip = get_client_ip(request)
    ua = request.headers.get("user-agent")
    # Per-IP refresh throttling + per-refresh-token hash (prevents hammering a stolen token)
    rl = hit(f"auth:refresh:ip:{ip}", limit=30, window_seconds=60)
    token_hash = hash_refresh_token(payload.refresh_token)
    rl2 = hit(f"auth:refresh:token:{token_hash}", limit=10, window_seconds=60)
    if not rl.allowed:
        write_audit_log(
            session,
            actor_user_id=None,
            action="auth.rate_limited",
            target_type="auth.refresh",
            target_id=None,
            ip=ip,
            user_agent=ua,
            after={"remaining": rl.remaining, "reset_seconds": rl.reset_seconds},
        )
        raise HTTPException(
            status_code=429,
            detail="Too many refresh attempts",
            headers={"Retry-After": str(rl.reset_seconds)},
        )
    if not rl2.allowed:
        raise HTTPException(status_code=429, detail="Too many refresh attempts", headers={"Retry-After": str(rl2.reset_seconds)})
    rt = session.exec(select(RefreshToken).where(RefreshToken.token_hash == token_hash)).first()
    if not rt or rt.revoked_at is not None or rt.expires_at < datetime.utcnow():
        write_audit_log(
            session,
            actor_user_id=None,
            action="auth.refresh_failed",
            target_type="refresh_token",
            target_id=None,
            ip=ip,
            user_agent=ua,
            before=None,
            after=None,
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = session.get(User, rt.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # Additional per-account throttling once user is known
    rl3 = hit(f"auth:refresh:user:{user.id}", limit=30, window_seconds=60)
    if not rl3.allowed:
        raise HTTPException(status_code=429, detail="Too many refresh attempts", headers={"Retry-After": str(rl3.reset_seconds)})

    # rotate refresh token
    rt.revoked_at = datetime.utcnow()
    session.add(rt)
    access = create_access_token(subject=user.email)
    new_refresh = generate_refresh_token()
    settings = get_settings()
    new_rt = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(new_refresh),
        expires_at=datetime.utcnow() + timedelta(days=int(settings.jwt_refresh_token_days)),
    )
    session.add(new_rt)
    session.commit()
    write_audit_log(
        session,
        actor_user_id=user.id,
        action="auth.refresh",
        target_type="user",
        target_id=user.id,
        ip=ip,
        user_agent=ua,
        before=None,
        after={"rotated": True},
    )
    return TokenResponse(access_token=access, refresh_token=new_refresh)


@router.post("/logout")
def logout(request: Request, payload: RefreshRequest, session: Session = Depends(get_session)) -> dict:
    ip = get_client_ip(request)
    ua = request.headers.get("user-agent")
    token_hash = hash_refresh_token(payload.refresh_token)
    rt = session.exec(select(RefreshToken).where(RefreshToken.token_hash == token_hash)).first()
    if rt and rt.revoked_at is None:
        rt.revoked_at = datetime.utcnow()
        session.add(rt)
        session.commit()
        write_audit_log(
            session,
            actor_user_id=rt.user_id,
            action="auth.logout",
            target_type="refresh_token",
            target_id=rt.id,
            ip=ip,
            user_agent=ua,
            before=None,
            after={"revoked": True},
        )
    return {"ok": True}


@router.get("/me")
def me(user: User = Depends(get_current_user)) -> dict:
    return {"id": user.id, "email": user.email, "role": user.role}

