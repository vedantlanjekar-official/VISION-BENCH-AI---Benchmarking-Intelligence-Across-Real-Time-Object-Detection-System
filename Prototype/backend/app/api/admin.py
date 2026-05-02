from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select

from app.api.deps import require_admin
from app.db.models import AuditLog, User
from app.db.session import get_session
from app.services.audit import write_audit_log


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users")
def list_users(session: Session = Depends(get_session), _: User = Depends(require_admin)):
    users = session.exec(select(User).order_by(User.created_at.desc())).all()
    return {
        "users": [
            {"id": u.id, "email": u.email, "role": u.role, "created_at": u.created_at.isoformat()} for u in users
        ]
    }


@router.patch("/users/{user_id}/role")
def set_user_role(
    user_id: int,
    payload: dict,
    session: Session = Depends(get_session),
    admin: User = Depends(require_admin),
):
    role = payload.get("role")
    if role not in ("user", "admin"):
        raise HTTPException(status_code=400, detail="role must be 'user' or 'admin'")
    target = session.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="user not found")
    if target.id == admin.id and role != "admin":
        raise HTTPException(status_code=400, detail="cannot demote self")
    before = {"role": target.role}
    target.role = role
    session.add(target)
    session.commit()
    session.refresh(target)
    write_audit_log(
        session,
        actor_user_id=admin.id,
        action="user.role_change",
        target_type="user",
        target_id=target.id,
        before=before,
        after={"role": target.role},
    )
    return {"id": target.id, "email": target.email, "role": target.role}


@router.get("/audit")
def list_audit(
    page: int = 1,
    page_size: int = 50,
    session: Session = Depends(get_session),
    _: User = Depends(require_admin),
):
    page = max(1, page)
    page_size = min(max(1, page_size), 200)
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc())
    offset = (page - 1) * page_size
    rows = session.exec(stmt.offset(offset).limit(page_size + 1)).all()
    has_next = len(rows) > page_size
    rows = rows[:page_size]
    return {
        "page": page,
        "page_size": page_size,
        "has_next": has_next,
        "audit": [
            {
                "id": a.id,
                "actor_user_id": a.actor_user_id,
                "action": a.action,
                "target_type": a.target_type,
                "target_id": a.target_id,
                "ip": a.ip,
                "user_agent": a.user_agent,
                "fingerprint": a.fingerprint,
                "before": a.before,
                "after": a.after,
                "created_at": a.created_at.isoformat(),
            }
            for a in rows
        ],
    }


@router.get("/audit/export")
def export_audit(
    limit: int = 10000,
    session: Session = Depends(get_session),
    _: User = Depends(require_admin),
):
    """
    Export audit logs as JSONL (newline-delimited JSON), newest first.
    This endpoint is intentionally read-only to support immutable retention workflows.
    """
    limit = min(max(1, limit), 200000)
    rows = session.exec(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)).all()

    def gen():
        for a in rows:
            yield (
                json.dumps(
                    {
                        "id": a.id,
                        "actor_user_id": a.actor_user_id,
                        "action": a.action,
                        "target_type": a.target_type,
                        "target_id": a.target_id,
                        "ip": a.ip,
                        "user_agent": a.user_agent,
                        "fingerprint": a.fingerprint,
                        "before": a.before,
                        "after": a.after,
                        "created_at": a.created_at.isoformat(),
                    }
                )
                + "\n"
            )

    return StreamingResponse(
        gen(),
        media_type="application/x-ndjson",
        headers={"Content-Disposition": 'attachment; filename="audit.jsonl"'},
    )

