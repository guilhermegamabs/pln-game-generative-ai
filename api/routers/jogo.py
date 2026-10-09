"""Rotas do jogo: a interface (jogo-web/) cria partidas e manda falas e ações; as regras rodam no servidor."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from schemas import PedidoComando, RespostaJogo
from seguranca import exigir_api_key
from servicos.partidas import GerenciadorPartidas, PartidaEncerrada, PartidaNaoEncontrada

router = APIRouter(prefix="/v1/jogo", tags=["Jogo"], dependencies=[Depends(exigir_api_key)])


def obter_partidas(request: Request) -> GerenciadorPartidas:
    return request.app.state.partidas


Partidas = Annotated[GerenciadorPartidas, Depends(obter_partidas)]
RESPOSTAS_ERRO = {
    401: {"description": "API Key ausente ou inválida"},
    404: {"description": "Partida não encontrada"},
}


@router.post("/partidas", response_model=RespostaJogo, status_code=status.HTTP_201_CREATED, summary="Nova partida")
def nova_partida(partidas: Partidas):
    return partidas.criar()


@router.get(
    "/partidas/{id_partida}", response_model=RespostaJogo, responses=RESPOSTAS_ERRO, summary="Estado da partida"
)
def estado_partida(id_partida: str, partidas: Partidas):
    """Usado pelo "Continuar" do menu: a partida volta do save mesmo depois de reiniciar a API."""
    try:
        return partidas.estado(id_partida)
    except PartidaNaoEncontrada as erro:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Partida não encontrada.") from erro


@router.post(
    "/partidas/{id_partida}/comandos",
    response_model=RespostaJogo,
    responses={**RESPOSTAS_ERRO, 409: {"description": "A partida já terminou"}},
    summary="Fala livre ou ação (/atacar, /roubar, /doar 10, /falar brenna, /veredito absolver...)",
)
def executar_comando(id_partida: str, pedido: PedidoComando, partidas: Partidas):
    """Fala livre vira um turno com a LLM (classificação + fala do NPC); comandos com "/" são regras do jogo.
    Se a IA cair, a partida segue no modo offline e a resposta vem com offline=true."""
    try:
        return partidas.executar(id_partida, pedido.entrada)
    except PartidaNaoEncontrada as erro:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Partida não encontrada.") from erro
    except PartidaEncerrada as erro:
        raise HTTPException(status.HTTP_409_CONFLICT, "Esta partida já terminou. Comece uma nova.") from erro
