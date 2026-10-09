"""Partidas em andamento. O núcleo do jogo (prototipo/) roda aqui no servidor e pede texto à IA pelo provider."""

import re
import sys
import threading
import uuid
from pathlib import Path

from providers.ia_provider import ErroProvedor, ProviderIA

PROTOTIPO = Path(__file__).resolve().parents[2] / "prototipo"
sys.path.insert(0, str(PROTOTIPO))
from estado import carregar_mundo  # noqa: E402
from jogo import Jogo  # noqa: E402
from llm import ClienteComFallback, ClienteFalso, ClienteRegistrado, ErroLLM  # noqa: E402

MUNDO = PROTOTIPO / "dados" / "mundo.json"
# O id vira nome de arquivo do save: só aceita o formato que nós mesmos geramos (evita "../" no caminho).
FORMATO_ID = re.compile(r"^[0-9a-f]{32}$")


class PartidaNaoEncontrada(Exception):
    pass


class PartidaEncerrada(Exception):
    pass


class ClienteProvider:
    """Adapta o ProviderIA à interface que o jogo já usa (gerar_json), sem passar por HTTP de novo."""

    def __init__(self, provider: ProviderIA):
        self.provider = provider

    @property
    def modelo(self):
        return self.provider.config.ollama_modelo

    def gerar_json(self, mensagens, schema, temperatura=None):
        try:
            return self.provider.gerar_texto(mensagens, schema, temperatura)["conteudo"]
        except ErroProvedor as erro:
            raise ErroLLM(str(erro), indisponivel=erro.indisponivel) from erro


class Partida:
    def __init__(self, id_partida, provider, pasta, carregar):
        self.id = id_partida
        self.linhas = []
        self.trava = threading.Lock()  # um comando por vez: cada turno leva segundos e mexe no mesmo estado
        self.fallback = ClienteComFallback(ClienteProvider(provider), ClienteFalso(), avisar=self.linhas.append)
        # Mesmo formato de log do terminal: prompt, resposta, modelo e latência de cada chamada (evidência).
        cliente = ClienteRegistrado(self.fallback, pasta / f"{id_partida}.jsonl")
        self.jogo = Jogo(
            cliente, carregar_mundo(MUNDO), pasta / f"{id_partida}.json", carregar=carregar, saida=self.linhas.append
        )
        if self.jogo.jogador.final:
            self.jogo.encerrado = True

    def resposta(self, linhas):
        return {
            "id": self.id,
            "linhas": linhas,
            "ultimo": self.jogo.ultimo,
            "estado": self.jogo.estado(),
            "offline": self.fallback.em_fallback,
        }


class GerenciadorPartidas:
    def __init__(self, provider: ProviderIA, pasta: Path):
        self.provider = provider
        self.pasta = pasta
        self.partidas = {}
        self.trava = threading.Lock()

    def criar(self):
        self.pasta.mkdir(parents=True, exist_ok=True)
        partida = Partida(uuid.uuid4().hex, self.provider, self.pasta, carregar=False)
        with self.trava:
            self.partidas[partida.id] = partida
        with partida.trava:
            partida.jogo.introducao()
            partida.jogo._salvar()
            linhas, partida.linhas[:] = list(partida.linhas), []
            return partida.resposta(linhas)

    def obter(self, id_partida):
        if not FORMATO_ID.match(id_partida):
            raise PartidaNaoEncontrada(id_partida)
        with self.trava:
            if id_partida not in self.partidas:
                # Depois de reiniciar a API, a partida volta do save em disco ("Continuar" do menu).
                if not (self.pasta / f"{id_partida}.json").exists():
                    raise PartidaNaoEncontrada(id_partida)
                self.partidas[id_partida] = Partida(id_partida, self.provider, self.pasta, carregar=True)
            return self.partidas[id_partida]

    def estado(self, id_partida):
        partida = self.obter(id_partida)
        with partida.trava:
            partida.jogo.ultimo = {}
            return partida.resposta([])

    def executar(self, id_partida, entrada):
        partida = self.obter(id_partida)
        with partida.trava:
            if partida.jogo.encerrado:
                raise PartidaEncerrada(id_partida)
            partida.linhas.clear()
            partida.jogo.processar(entrada)
            linhas = list(partida.linhas)
            partida.linhas.clear()
            return partida.resposta(linhas)
