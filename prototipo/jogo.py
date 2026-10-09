"""Loop do protótipo: comandos, turno de diálogo com NPC e consequências no estado."""

import unicodedata

import corrupcao
import prompts
from corrupcao import NOMES, PECADOS
from estado import NPC, Jogador, carregar_partida, rotulo_relacao, salvar_partida
from llm import ErroLLM

SCHEMA_CLASSIFICACAO = {
    "type": "object",
    "properties": {
        "intencao": {"type": "string", "enum": list(corrupcao.INTENCOES)},
        "intensidade": {"type": "integer", "enum": [1, 2, 3]},
    },
    "required": ["intencao", "intensidade"],
}

SCHEMA_TURNO = {
    "type": "object",
    "properties": {
        "emocao": {"type": "string"},
        "fala": {"type": "string"},
        "memoria": {"type": "string"},
    },
    "required": ["emocao", "fala", "memoria"],
}

SCHEMA_FALA = {
    "type": "object",
    "properties": {"fala": {"type": "string"}},
    "required": ["fala"],
}

MAX_HISTORICO = 8
MAX_MEMORIAS = 12
VALOR_ROUBO = 25


def _limpar(texto):
    # Com JSON Schema no Ollama, o qwen2.5:7b às vezes devolve espaços duplos entre todas as palavras
    # (visto na fala da Fera em teste real). Junta qualquer sequência de espaços/quebras em um espaço só.
    return " ".join(str(texto or "").split())

AJUDA = """Digite livremente o que quer dizer ao NPC atual. Comandos:
  /falar [nome] [fala]   escolhe com quem falar e, opcionalmente, já diz algo
                         (sem nome, lista os presentes; ex.: /falar brenna Solte esse homem)
  /atacar         ataca o NPC atual (combate simplificado)
  /roubar         rouba moedas do NPC atual
  /doar <valor>   dá moedas ao NPC atual
  /status         medidores de pecado, aparência, manifestações
  /memorias       o que o NPC atual lembra de você
  /ajuda          esta ajuda
  /sair           salva e sai"""


class Jogo:
    def __init__(self, cliente, mundo, caminho_save=None, carregar=True, saida=print):
        self.cliente = cliente
        self.cena = mundo["cena"]
        self.manifestacoes = mundo["manifestacoes"]
        self.caminho_save = caminho_save
        self.saida = saida
        self.encerrado = False
        self.carregado = bool(carregar and caminho_save and caminho_save.exists())
        if self.carregado:
            self.jogador, self.npcs = carregar_partida(caminho_save)
        else:
            self.jogador = Jogador()
            self.npcs = {ficha["id"]: NPC(**ficha) for ficha in mundo["npcs"]}
        self.atual = self.cena["npc_inicial"]

    # ---------- entrada ----------

    def introducao(self):
        if self.jogador.final:
            self.saida(f"Esta partida já terminou (final: {self.jogador.final}). Rode com --novo para recomeçar.")
            self.encerrado = True
            return
        if self.carregado:
            self.saida("[partida carregada]")
        self.saida(f"\n=== {self.cena['local']} ===\n{self.cena['situacao']}\n")
        npc = self.npcs[self.atual]
        self.saida(f"Você está diante de {npc.nome}. {npc.descricao}")
        self.saida("Digite /ajuda para ver os comandos.")
        self.saida(self.hud())

    def processar(self, entrada):
        """Processa uma linha do jogador. Retorna False quando o jogo deve encerrar."""
        entrada = entrada.strip()
        if not entrada or self.encerrado:
            return not self.encerrado
        if entrada.startswith("/"):
            comando, _, argumento = entrada[1:].partition(" ")
            metodo = getattr(self, f"cmd_{comando.lower()}", None)
            if metodo is None:
                self.saida("Comando desconhecido. Digite /ajuda.")
            else:
                metodo(argumento.strip())
        else:
            self.falar(entrada)
        return not self.encerrado

    # ---------- diálogo ----------

    def falar(self, texto):
        npc = self._npc_atual_vivo()
        if npc is None:
            return
        # Etapa 1: classificador curto e determinístico (temperatura 0). Etapa 2: NPC reage à intenção já lida.
        classificacao = self._gerar(prompts.mensagens_classificacao(texto), SCHEMA_CLASSIFICACAO, temperatura=0)
        if classificacao is None:
            return
        intencao = classificacao.get("intencao")
        if intencao not in corrupcao.INTENCOES:
            intencao = "neutro"
        try:
            intensidade = min(3, max(1, int(classificacao.get("intensidade", 1))))
        except (TypeError, ValueError):
            intensidade = 1

        resposta = self._gerar(
            prompts.mensagens_turno(npc, self.jogador, self.cena, texto, intencao, intensidade), SCHEMA_TURNO
        )
        if resposta is None:
            return
        fala = _limpar(resposta.get("fala")) or "*fica em silêncio*"
        memoria = _limpar(resposta.get("memoria"))

        npc.registrar_fala(texto, fala, MAX_HISTORICO)
        self.saida(f"\n{npc.nome}: {fala}")

        delta_rel = corrupcao.delta_relacao(intencao, intensidade, npc.reage_bem_a)
        npc.ajustar_relacao(delta_rel)
        if memoria:
            npc.lembrar(memoria, MAX_MEMORIAS)

        self._consequencias(
            corrupcao.deltas_intencao(intencao, intensidade),
            gatilho=f'dizer a {npc.nome}: "{texto}"',
            detalhe=f"intenção: {intencao} ({intensidade}) · relação com {npc.nome} {delta_rel:+d}",
        )

    # ---------- comandos ----------

    def cmd_ajuda(self, _):
        self.saida(AJUDA)

    def cmd_falar(self, nome):
        if not nome:
            for npc in self.npcs.values():
                estado = "morto" if not npc.vivo else f"relação {npc.relacao:+d} ({rotulo_relacao(npc.relacao)})"
                marcador = ">" if npc.id == self.atual else " "
                self.saida(f" {marcador} {npc.id:<8} {npc.nome} — {estado}")
            return
        npc, fala = self._achar_npc(nome)
        if npc is None:
            self.saida(f"Ninguém chamado '{nome.split()[0]}' por aqui. Use /falar para listar.")
            return
        self.atual = npc.id
        self.saida(f"Você se volta para {npc.nome}. {npc.descricao}")
        if fala:
            self.falar(fala)

    def _achar_npc(self, texto):
        """Casa o começo do texto com id, primeiro nome ou nome completo (sem acento). Retorna (npc, resto)."""
        normalizado = _sem_acento(texto)
        candidatos = []
        for npc in self.npcs.values():
            for chave in {npc.id, _sem_acento(npc.nome.split(",")[0]), _sem_acento(npc.nome.split()[0])}:
                candidatos.append((chave, npc))
        # Chave mais longa primeiro: "capita brenna" deve ganhar de "capita".
        for chave, npc in sorted(candidatos, key=lambda c: -len(c[0])):
            if normalizado == chave or normalizado.startswith(chave + " "):
                # NFKD + remoção de acento preserva a contagem de letras latinas, então o corte vale no texto original.
                return npc, texto[len(chave):].strip()
        return None, ""

    def cmd_atacar(self, _):
        npc = self._npc_atual_vivo()
        if npc is None:
            return
        npc.vivo = False
        self.saida(f"\nVocê avança sobre {npc.nome}. O combate é breve. {npc.nome} cai sem vida sobre as pedras da praça.")
        for testemunha in self.npcs.values():
            if testemunha.vivo:
                delta = corrupcao.delta_relacao("violencia", 3, testemunha.reage_bem_a)
                testemunha.ajustar_relacao(delta)
                testemunha.lembrar(f"Viu o inquisitor matar {npc.nome} na praça.", MAX_MEMORIAS)
                self.saida(f"  {testemunha.nome} viu tudo (relação {delta:+d}).")
        self.jogador.eventos.append(f"Matou {npc.nome}.")
        self._consequencias(corrupcao.ACOES["atacar"], gatilho=f"matar {npc.nome}", detalhe="ação: atacar")

    def cmd_roubar(self, _):
        npc = self._npc_atual_vivo()
        if npc is None:
            return
        quantia = min(npc.ouro, VALOR_ROUBO)
        if quantia == 0:
            self.saida(f"{npc.nome} não tem nada que valha a pena roubar.")
            return
        npc.ouro -= quantia
        self.jogador.ouro += quantia
        delta = corrupcao.delta_relacao("ganancia", 3, npc.reage_bem_a)
        npc.ajustar_relacao(delta)
        npc.lembrar(f"Percebeu que o inquisitor roubou {quantia} moedas dele.", MAX_MEMORIAS)
        self.saida(f"\nVocê tira {quantia} moedas de {npc.nome}. Ele percebe (relação {delta:+d}).")
        self.jogador.eventos.append(f"Roubou {quantia} moedas de {npc.nome}.")
        self._consequencias(corrupcao.ACOES["roubar"], gatilho=f"roubar {npc.nome}", detalhe="ação: roubar")

    def cmd_doar(self, valor):
        npc = self._npc_atual_vivo()
        if npc is None:
            return
        try:
            quantia = int(valor)
        except ValueError:
            self.saida("Uso: /doar <valor>")
            return
        if quantia <= 0 or quantia > self.jogador.ouro:
            self.saida(f"Você tem {self.jogador.ouro} moedas.")
            return
        self.jogador.ouro -= quantia
        npc.ouro += quantia
        npc.ajustar_relacao(10)
        npc.lembrar(f"Recebeu {quantia} moedas do inquisitor sem pedir nada.", MAX_MEMORIAS)
        self.saida(f"\nVocê entrega {quantia} moedas a {npc.nome} (relação +10).")
        self.jogador.eventos.append(f"Doou {quantia} moedas a {npc.nome}.")
        self._consequencias(
            {"avareza": -max(1, quantia // 5)}, gatilho=f"doar moedas a {npc.nome}", detalhe="ação: doar"
        )

    def cmd_status(self, _):
        self.saida("\n--- Espelho da Alma ---")
        for pecado in PECADOS:
            valor = self.jogador.pecados[pecado]
            manifestado = f"  <- {self.manifestacoes[pecado]['nome']}" if pecado in self.jogador.manifestacoes else ""
            self.saida(f"  {NOMES[pecado]:<9} {_barra(valor)} {valor:3d}{manifestado}")
        marcas = corrupcao.aparencia(self.jogador.pecados)
        self.saida(f"  Aparência: {', '.join(marcas) if marcas else 'sem marcas'}")
        self.saida(f"  Ouro: {self.jogador.ouro}")
        if self.jogador.eventos:
            self.saida("  Eventos: " + " | ".join(self.jogador.eventos[-5:]))

    def cmd_memorias(self, _):
        npc = self.npcs[self.atual]
        self.saida(f"\n{npc.nome} — relação {npc.relacao:+d} ({rotulo_relacao(npc.relacao)})")
        for memoria in npc.memorias or ["(nenhuma lembrança)"]:
            self.saida(f"  - {memoria}")

    def cmd_sair(self, _):
        self._salvar()
        self.saida("Partida salva. Até a próxima, inquisitor.")
        self.encerrado = True

    # ---------- internos ----------

    def _npc_atual_vivo(self):
        npc = self.npcs[self.atual]
        if not npc.vivo:
            self.saida(f"{npc.nome} está morto. Use /falar para escolher outra pessoa.")
            return None
        return npc

    def _consequencias(self, deltas, gatilho, detalhe):
        aplicados, novas = corrupcao.aplicar(self.jogador.pecados, deltas, self.jogador.manifestacoes)
        partes = [detalhe] + [f"{NOMES[p]} {v:+d}" for p, v in aplicados.items() if v]
        self.saida(f"  [{' · '.join(partes)}]")

        for pecado in novas:
            self.jogador.manifestacoes.append(pecado)
            self._manifestar(pecado, gatilho)

        consumidor = corrupcao.pecado_consumidor(self.jogador.pecados)
        if consumidor:
            self._final_consumido(consumidor)
        else:
            self.saida(self.hud())
        self._salvar()

    def _manifestar(self, pecado, gatilho):
        manifestacao = self.manifestacoes[pecado]
        resposta = self._gerar(
            prompts.mensagens_manifestacao(manifestacao, pecado, self.jogador, gatilho), SCHEMA_FALA
        )
        fala = _limpar((resposta or {}).get("fala")) or manifestacao["fala_reserva"]
        self.saida(f"\n*** {manifestacao['nome']} desperta dentro de você ***\n{manifestacao['nome']}: {fala}")

    def _final_consumido(self, pecado):
        nome = self.manifestacoes[pecado]["nome"]
        self.jogador.final = f"Consumido pela {NOMES[pecado]}"
        self.saida(
            f"\n=== FINAL: CONSUMIDO PELA {NOMES[pecado].upper()} ===\n"
            f"{nome} toma o controle. O inquisitor que chegou a Cinzaforte não existe mais — "
            f"agora a cidade tem uma nova manifestação."
        )
        self.encerrado = True

    def _gerar(self, mensagens, schema, temperatura=None):
        erro = None
        for _ in range(2):
            try:
                return self.cliente.gerar_json(mensagens, schema, temperatura)
            except ErroLLM as falha:
                erro = falha
        self.saida(f"[erro da IA] {erro}")
        return None

    def _salvar(self):
        if self.caminho_save:
            salvar_partida(self.caminho_save, self.jogador, self.npcs)

    def hud(self):
        visiveis = [p for p in PECADOS if p in ("ira", "avareza") or self.jogador.pecados[p] > 0]
        medidores = " | ".join(f"{NOMES[p]} {_barra(self.jogador.pecados[p])} {self.jogador.pecados[p]}" for p in visiveis)
        return f"  {medidores} | Ouro {self.jogador.ouro}"


def _sem_acento(texto):
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)).lower()


def _barra(valor):
    cheios = valor // 10
    return "█" * cheios + "░" * (10 - cheios)
