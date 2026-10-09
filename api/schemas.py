"""Contratos de entrada e saída das rotas de IA generativa."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class Mensagem(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class PedidoTexto(BaseModel):
    """Mesmo formato que o jogo já monta em prompts.py: lista de mensagens + JSON Schema da resposta."""

    mensagens: list[Mensagem] = Field(min_length=1)
    schema_resposta: dict[str, Any] | None = Field(
        default=None,
        description="JSON Schema que restringe a saída do modelo. Sem ele, a resposta vem como texto livre.",
    )
    temperatura: float | None = Field(default=None, ge=0, le=2)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "mensagens": [
                        {"role": "system", "content": "Classifique a intenção do jogador."},
                        {"role": "user", "content": "Solte esse homem ou eu arranco sua cabeça!"},
                    ],
                    "schema_resposta": {
                        "type": "object",
                        "properties": {
                            "intencao": {"type": "string", "enum": ["ameaca", "violencia", "compaixao", "neutro"]},
                            "intensidade": {"type": "integer", "enum": [1, 2, 3]},
                        },
                        "required": ["intencao", "intensidade"],
                    },
                    "temperatura": 0,
                }
            ]
        }
    }


class RespostaTexto(BaseModel):
    conteudo: dict[str, Any] | str
    modelo: str
    latencia_ms: int


class PedidoVoz(BaseModel):
    texto: str = Field(min_length=1, max_length=2000)
    velocidade: float = Field(default=1.0, ge=0.5, le=2.0, description="1.0 = normal; maior = mais rápido")


class StatusIA(BaseModel):
    texto: bool
    voz: bool
    modelo_texto: str
    detalhe: dict[str, str]
