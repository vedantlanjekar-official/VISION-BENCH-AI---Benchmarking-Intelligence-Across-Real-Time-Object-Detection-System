from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from app.core.security import decode_token
from app.db.models import User
from app.db.session import get_session


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def _get_or_create_guest(session: Session) -> User:
    guest_email = "guest@visionbench.local"
    user = session.exec(select(User).where(User.email == guest_email)).first()
    if user:
        return user
    user = User(email=guest_email, hashed_password="!", role="user")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def get_current_user(session: Session = Depends(get_session), token: str | None = Depends(oauth2_scheme)) -> User:
    # Auth is optional for this project: if no token is provided, a persistent Guest user is used.
    if not token:
        return _get_or_create_guest(session)
    sub = decode_token(token)
    if not sub:
        return _get_or_create_guest(session)
    user = session.exec(select(User).where(User.email == sub)).first()
    if not user:
        return _get_or_create_guest(session)
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin required")
    return user

