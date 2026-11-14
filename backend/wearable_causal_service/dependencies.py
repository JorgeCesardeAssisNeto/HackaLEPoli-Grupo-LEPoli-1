"""Dependências compartilhadas de autenticação service-to-service."""

import hmac
from typing import Optional
from fastapi import Header, HTTPException, status

from config import settings, is_placeholder


async def verify_service_token(
    x_service_token: Optional[str] = Header(default=None, alias="X-Service-Token"),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> None:
    """
    Valida o token service-to-service quando `settings.SERVICE_API_KEY` está configurado:
      - Aceita `X-Service-Token: <token>` ou `Authorization: Bearer <token>`.
      - Se `SERVICE_API_KEY` estiver vazio (ou placeholder), permite a passagem (retrocompatível).
    """
    expected = (settings.SERVICE_API_KEY or "").strip()
    if not expected or is_placeholder(expected):
        return

    candidates = []
    if x_service_token:
        candidates.append(x_service_token.strip())
    if authorization:
        auth_val = authorization.strip()
        if auth_val.lower().startswith("bearer "):
            candidates.append(auth_val[7:].strip())
        else:
            candidates.append(auth_val)

    if not any(hmac.compare_digest(c, expected) for c in candidates if c):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing service token (provide X-Service-Token or Authorization: Bearer).",
        )

