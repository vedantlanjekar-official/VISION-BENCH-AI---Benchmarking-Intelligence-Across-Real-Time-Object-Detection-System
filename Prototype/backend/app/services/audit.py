from __future__ import annotations

import json
import hashlib
from typing import Any, Optional

from sqlmodel import Session

from app.db.models import AuditLog


def _fingerprint(ip: Optional[str], user_agent: Optional[str]) -> Optional[str]:
    if not ip and not user_agent:
        return None
    raw = f"{ip or ''}|{user_agent or ''}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def write_audit_log(
    session: Session,
    *,
    actor_user_id: Optional[int],
    action: str,
    target_type: str,
    target_id: Optional[int],
    ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    before: Any = None,
    after: Any = None,
) -> AuditLog:
    row = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        ip=ip,
        user_agent=user_agent,
        fingerprint=_fingerprint(ip, user_agent),
        before=json.dumps(before) if before is not None else None,
        after=json.dumps(after) if after is not None else None,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row

