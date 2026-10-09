"""Rotas de IA generativa consumidas pelo jogo e pelo painel. Toda a lógica de chamada fica no provider."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from providers.ia_provider import ErroProvedor, ProviderIA
from schemas import PedidoTexto, PedidoVoz, RespostaTexto, StatusIA
from seguranca import exigir_api_key

router = APIRouter(prefix="/v1/ia-generativa", tags=["IA generativa"], dependencies=[Depends(exigir_api_key)])

RESPOSTAS_ERRO = {
    401: {"description": "API Key ausente ou inválida"},
    502: {"description": "O serviço de IA respondeu, mas com erro ou resposta inválida"},
    503: {"description": "Serviço de IA indisponível (o jogo deve usar o fallback)"},
}


def obter_provider(request: Request) -> ProviderIA:
    return request.app.state.provider


def _http(erro: ErroProvedor):
    codigo = status.HTTP_503_SERVICE_UNAVAILABLE if erro.indisponivel else status.HTTP_502_BAD_GATEWAY
    return HTTPException(codigo, str(erro))


# Rotas síncronas (def, não async def): o FastAPI roda cada uma numa thread,
# então uma geração lenta do Ollama não trava as outras requisições.


@router.post("/texto", response_model=RespostaTexto, responses=RESPOSTAS_ERRO, summary="Gera texto com a LLM (Ollama)")
def gerar_texto(pedido: PedidoTexto, provider: ProviderIA = Depends(obter_provider)):
    """Usado pelo jogo para classificar a intenção do jogador, gerar a fala do NPC e a voz do Demônio Interior."""
    try:
        return provider.gerar_texto(
            [m.model_dump() for m in pedido.mensagens], pedido.schema_resposta, pedido.temperatura
        )
    except ErroProvedor as erro:
        raise _http(erro) from erro


@router.post(
    "/voz",
    response_class=Response,
    responses={**RESPOSTAS_ERRO, 200: {"content": {"audio/wav": {}}, "description": "Áudio WAV mono 16 bits"}},
    summary="Sintetiza voz com Piper TTS",
)
def sintetizar_voz(pedido: PedidoVoz, provider: ProviderIA = Depends(obter_provider)):
    try:
        audio = provider.sintetizar_voz(pedido.texto, pedido.velocidade)
    except ErroProvedor as erro:
        raise _http(erro) from erro
    return Response(audio, media_type="audio/wav")


@router.get("/status", response_model=StatusIA, responses={401: RESPOSTAS_ERRO[401]}, summary="Disponibilidade de texto e voz")
def status_ia(provider: ProviderIA = Depends(obter_provider)):
    """O jogo chama ao abrir: se texto=false, entra direto no modo offline em vez de falhar no primeiro turno."""
    texto_ok, texto_detalhe = provider.status_texto()
    voz_ok, voz_detalhe = provider.status_voz()
    return StatusIA(
        texto=texto_ok,
        voz=voz_ok,
        modelo_texto=provider.config.ollama_modelo,
        detalhe={"texto": texto_detalhe, "voz": voz_detalhe},
    )
