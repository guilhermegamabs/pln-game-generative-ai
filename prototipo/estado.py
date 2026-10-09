"""Estado da partida (jogador e NPCs) e persistência em JSON."""

import json
from dataclasses import asdict, dataclass, field

from corrupcao import PECADOS


@dataclass
class Jogador:
    nome: str = "Inquisitor"
    pecados: dict = field(default_factory=lambda: {p: 0 for p in PECADOS})
    ouro: int = 30
    manifestacoes: list = field(default_factory=list)
    eventos: list = field(default_factory=list)
    final: str | None = None
    vida: int = 100
    vida_max: int = 100
    inventario: dict = field(default_factory=lambda: {"pocao": 2, "agua_benta": 1})
    # Combate em andamento: {"npc": id, "brecha": bool}. Fica no save para a partida voltar no meio da luta.
    combate: dict | None = None


@dataclass
class NPC:
    id: str
    nome: str
    descricao: str
    personalidade: str
    objetivo: str
    segredo: str
    reage_bem_a: list
    relacao: int = 0
    ouro: int = 0
    vivo: bool = True
    vida_max: int = 30
    dano: int = 5
    vida: int | None = None
    memorias: list = field(default_factory=list)
    historico: list = field(default_factory=list)

    def __post_init__(self):
        if self.vida is None:
            self.vida = self.vida_max

    def lembrar(self, memoria, limite):
        # O modelo costuma devolver a mesma memória em turnos seguidos; repetida só gasta contexto.
        if memoria in self.memorias:
            return
        self.memorias.append(memoria)
        # Memória curta de propósito: o prompt precisa caber no contexto de modelos pequenos locais.
        del self.memorias[:-limite]

    def registrar_fala(self, texto_jogador, fala_npc, limite):
        self.historico.append({"role": "user", "content": texto_jogador})
        self.historico.append({"role": "assistant", "content": fala_npc})
        del self.historico[:-limite]

    def ajustar_relacao(self, delta):
        self.relacao = max(-100, min(100, self.relacao + delta))


def rotulo_relacao(relacao):
    if relacao <= -50:
        return "odeia"
    if relacao < -10:
        return "desconfia"
    if relacao <= 10:
        return "neutro"
    if relacao < 40:
        return "simpatiza"
    return "confia"


def carregar_mundo(caminho):
    with open(caminho, encoding="utf-8") as arquivo:
        return json.load(arquivo)


def salvar_partida(caminho, jogador, npcs):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    dados = {"jogador": asdict(jogador), "npcs": [asdict(npc) for npc in npcs.values()]}
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=2)


def carregar_partida(caminho):
    with open(caminho, encoding="utf-8") as arquivo:
        dados = json.load(arquivo)
    jogador = Jogador(**dados["jogador"])
    npcs = {n["id"]: NPC(**n) for n in dados["npcs"]}
    return jogador, npcs
