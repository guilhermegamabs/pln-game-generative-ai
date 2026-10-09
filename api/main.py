"""API do OS 7 PECADOS: o jogo chama esta API, e só ela fala com os serviços de IA generativa.

Rodar (de dentro de api/):
    uvicorn main:app --reload --env-file .env
Swagger: http://localhost:8000/docs
"""

from config import carregar_config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from providers.ia_provider import ProviderIA
from routers import ia_generativa, jogo
from servicos.partidas import GerenciadorPartidas


def criar_app(config=None, provider=None):
    config = config or carregar_config()
    app = FastAPI(
        title="OS 7 PECADOS · API de IA generativa",
        version="1.0.0",
        description=(
            "Back-end da CP5. Encapsula a LLM local (Ollama) e o TTS (Piper) e roda as partidas do jogo web. "
            "Rotas em /v1/ia-generativa exigem o header **X-API-Key** (botão *Authorize*)."
        ),
    )
    app.state.config = config
    app.state.provider = provider or ProviderIA(config)
    app.state.partidas = GerenciadorPartidas(app.state.provider, config.pasta_partidas)

    # O front React roda em outra origem (Vite em :5173); sem CORS o navegador bloqueia as chamadas.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origens,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-API-Key"],
    )
    app.include_router(ia_generativa.router)
    app.include_router(jogo.router)

    @app.get("/health", tags=["infra"], summary="A API está no ar (sem autenticação)")
    def health():
        return {"status": "ok"}

    return app


app = criar_app()
