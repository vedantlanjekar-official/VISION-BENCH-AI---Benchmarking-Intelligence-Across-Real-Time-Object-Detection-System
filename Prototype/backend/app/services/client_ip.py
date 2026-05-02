from __future__ import annotations

import ipaddress
from typing import Optional

from fastapi import Request

from app.core.config import get_settings


def _is_trusted_proxy(remote_ip: str) -> bool:
    s = get_settings()
    try:
        rip = ipaddress.ip_address(remote_ip)
    except ValueError:
        return False
    for cidr in s.trusted_proxy_cidr_list:
        try:
            net = ipaddress.ip_network(cidr, strict=False)
        except ValueError:
            continue
        if rip in net:
            return True
    return False


def get_client_ip(request: Request) -> Optional[str]:
    """
    Proxy-aware client IP extraction.

    - If TRUST_PROXY_HEADERS is false: use direct peer IP.
    - If true: only honor X-Forwarded-For when the direct peer IP is in TRUSTED_PROXY_CIDRS.
      Uses the left-most (original) IP in XFF.
    """
    peer = request.client.host if request.client else None
    if not peer:
        return None

    s = get_settings()
    if not s.trust_proxy_headers:
        return peer

    if not _is_trusted_proxy(peer):
        return peer

    xff = request.headers.get("x-forwarded-for")
    if not xff:
        return peer

    first = xff.split(",")[0].strip()
    try:
        ipaddress.ip_address(first)
        return first
    except ValueError:
        return peer

