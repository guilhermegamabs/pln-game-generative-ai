"""Configuração lida do ambiente (ou do api/.env via `uvicorn --env-file`)."""

import os
from dataclasses import dataclass, field
from pathlib import Path


def _lista(valor):
    return [item.strip() for item in valor.split(",") if item.strip()]


@dataclass(frozen=True)
class Config:
    api_key: str = field(default_factory=lambda: os.environ.get("API_KEY", ""))
    ollama_url: str = field(default_factory=lambda: os.environ.get("OLLAMA_URL", "http://localhost:11434"))
    # Mesmo modelo padrão do protótipo: qwen2.5:7b venceu o llama3.2:3b nos testes da CP4.
    ollama_modelo: str = field(default_factory=lambda: os.environ.get("OLLAMA_MODEL", "qwen2.5:7b"))
    ollama_timeout: float = field(default_factory=lambda: float(os.environ.get("OLLAMA_TIMEOUT", "180")))
    piper_voz: Path | None = field(
        default_factory=lambda: Path(os.environ["PIPER_VOZ"]) if os.environ.get("PIPER_VOZ") else None
    )
    # Saves e logs das partidas do jogo web (um .json e um .jsonl por partida).
    pasta_partidas: Path = field(
        default_factory=lambda: Path(os.environ.get("PASTA_PARTIDAS", Path(__file__).resolve().parent / "partidas"))
    )
    # Origem do front React em dev (Vite) por padrão; em produção, listar o domínio do jogo.
    cors_origens: list[str] = field(
        default_factory=lambda: _lista(os.environ.get("CORS_ORIGENS", "http://localhost:5173,http://127.0.0.1:5173"))
    )


def carregar_config():
    return Config()
