"""Autenticação por API Key no header X-API-Key."""

import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader

# APIKeyHeader faz o Swagger (/docs) mostrar o botão "Authorize" com o campo X-API-Key.
esquema_api_key = APIKeyHeader(name="X-API-Key", auto_error=False, description="Chave definida em API_KEY no .env")


def exigir_api_key(request: Request, chave: Annotated[str | None, Depends(esquema_api_key)]):
    esperada = request.app.state.config.api_key
    if not esperada:
        # Sem chave configurada a API ficaria aberta: melhor recusar tudo e avisar.
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "API_KEY não configurada no servidor.")
    # compare_digest evita vazar a chave pelo tempo de resposta da comparação.
    if not chave or not secrets.compare_digest(chave.encode(), esperada.encode()):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "API Key ausente ou inválida.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
