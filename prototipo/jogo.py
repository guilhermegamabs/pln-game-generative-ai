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

# Combate por turnos (M5 da CP4): valores fixos, como a corrupção, para o balanceamento ser previsível e testável.
DANO_GOLPE = 25
DANO_PODER = 45
FRACAO_DEFESA = 0.25  # defendendo, o jogador recebe só 1/4 do dano e abre uma brecha (próximo dano em dobro)
CURA_POCAO = 35
PURIFICACAO_AGUA = 10
ITENS = {
    "pocao": ("Poção de cura", f"recupera {CURA_POCAO} de vida"),
    "agua_benta": ("Água benta", f"purifica {PURIFICACAO_AGUA} pontos do pecado mais alto"),
}
EM_COMBATE = {"atacar", "defender", "poder", "item", "fugir", "status", "memorias", "ajuda", "sair"}


def _limpar(texto):
    # Com JSON Schema no Ollama, o qwen2.5:7b às vezes devolve espaços duplos entre todas as palavras
    # (visto na fala da Fera em teste real). Junta qualquer sequência de espaços/quebras em um espaço só.
    return " ".join(str(texto or "").split())

AJUDA = """Digite livremente o que quer dizer ao NPC atual. Comandos:
  /falar [nome] [fala]   escolhe com quem falar e, opcionalmente, já diz algo
                         (sem nome, lista os presentes; ex.: /falar brenna Solte esse homem)
  /atacar         ataca o NPC atual e começa um combate por turnos (ou golpeia, se já estiver em combate)
  /defender       em combate: recebe 1/4 do dano e o próximo golpe sai em dobro
  /poder          em combate: usa o poder de uma manifestação desperta (mais dano, mais pecado)
  /fugir          em combate: abandona a luta (o NPC não esquece)
  /item [nome]    usa um item (pocao, agua_benta); sem nome, lista o inventário
  /roubar         rouba moedas do NPC atual
  /doar <valor>   dá moedas ao NPC atual
  /status         medidores de pecado, aparência, manifestações
  /memorias       o que o NPC atual lembra de você
  /veredito absolver|condenar   julga Tomás e encerra a partida (o final depende dos seus pecados)
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
        # Resultado estruturado do último comando (fala, intenção lida, memória, manifestação, final).
        # O terminal usa só as linhas de texto; a interface web (CP5) monta os painéis a partir disto.
        self.ultimo = {}

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
        self.ultimo = {}
        comando, _, argumento = entrada[1:].partition(" ") if entrada.startswith("/") else ("", "", "")
        if self.jogador.combate and comando.lower() not in EM_COMBATE:
            npc = self.npcs[self.jogador.combate["npc"]]
            self.saida(f"Você está em combate com {npc.nome}. Use /atacar, /defender, /poder, /item ou /fugir.")
            return True
        if entrada.startswith("/"):
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
        emocao = _limpar(resposta.get("emocao"))

        npc.registrar_fala(texto, fala, MAX_HISTORICO)
        self.saida(f"\n{npc.nome}: {fala}")

        delta_rel = corrupcao.delta_relacao(intencao, intensidade, npc.reage_bem_a)
        npc.ajustar_relacao(delta_rel)
        if memoria:
            npc.lembrar(memoria, MAX_MEMORIAS)
            self.ultimo["memoria"] = {"npc": npc.id, "texto": memoria}
        self.ultimo["fala"] = {"npc": npc.id, "texto": fala, "emocao": emocao}
        self.ultimo["leitura"] = {
            "npc": npc.id,
            "intencao": intencao,
            "intensidade": intensidade,
            "delta_relacao": delta_rel,
        }

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
        if self.jogador.combate:
            npc = self.npcs[self.jogador.combate["npc"]]
            self.saida(f"\nVocê golpeia {npc.nome}.")
            self._turno_combate(npc, DANO_GOLPE, "golpe")
            return
        npc = self._npc_atual_vivo()
        if npc is None:
            return
        self.jogador.combate = {"npc": npc.id, "brecha": False}
        npc.ajustar_relacao(-30)
        npc.lembrar("O inquisitor me atacou no meio da praça.", MAX_MEMORIAS)
        self.saida(f"\nVocê avança sobre {npc.nome}. O combate começa.")
        self._consequencias(corrupcao.ACOES["atacar"], gatilho=f"atacar {npc.nome}", detalhe="ação: atacar")
        if not self.encerrado:
            self._turno_combate(npc, DANO_GOLPE, "golpe")

    def cmd_defender(self, _):
        npc = self._npc_em_combate()
        if npc is None:
            return
        self.saida(f"\nVocê ergue a guarda e espera a brecha de {npc.nome}.")
        self._turno_combate(npc, 0, "defender")

    def cmd_poder(self, _):
        npc = self._npc_em_combate()
        if npc is None:
            return
        if not self.jogador.manifestacoes:
            self.saida("Nenhum pecado despertou dentro de você ainda. Não há poder a pedir.")
            return
        pecado = max(self.jogador.manifestacoes, key=lambda p: self.jogador.pecados[p])
        manifestacao = self.manifestacoes[pecado]
        self.saida(f"\nVocê aceita o poder de {manifestacao['nome']}: {manifestacao['poder']}.")
        self._consequencias(
            {pecado: corrupcao.CUSTO_PODER}, gatilho=f"usar o poder de {manifestacao['nome']}", detalhe="ação: poder demoníaco"
        )
        if not self.encerrado:
            self._turno_combate(npc, DANO_PODER, "poder")
            self.ultimo["combate"]["poder"] = pecado

    def cmd_fugir(self, _):
        npc = self._npc_em_combate()
        if npc is None:
            return
        self.jogador.combate = None
        npc.lembrar("O inquisitor me atacou e fugiu da luta.", MAX_MEMORIAS)
        self.jogador.eventos.append(f"Fugiu do combate com {npc.nome}.")
        self.saida(f"\nVocê recua e some na multidão. {npc.nome} fica de pé, ofegante, e não vai esquecer.")
        self._registrar_combate(npc, "fugir", "fugiu")
        self._salvar()

    def cmd_item(self, nome):
        inventario = self.jogador.inventario
        if not nome:
            itens = [f"{ITENS[i][0]} x{q} ({ITENS[i][1]})" for i, q in inventario.items() if q > 0 and i in ITENS]
            self.saida("Inventário: " + ("; ".join(itens) if itens else "vazio"))
            return
        chave = _sem_acento(nome).replace(" ", "_")
        item = next((i for i in ITENS if i.startswith(chave) or _sem_acento(ITENS[i][0]).startswith(_sem_acento(nome))), None)
        if item is None or inventario.get(item, 0) <= 0:
            self.saida(f"Você não tem '{nome}'. Use /item para ver o inventário.")
            return
        if item == "pocao":
            if self.jogador.vida >= self.jogador.vida_max:
                self.saida("Sua vida já está cheia.")
                return
            antes = self.jogador.vida
            self.jogador.vida = min(self.jogador.vida_max, antes + CURA_POCAO)
            efeito = f"vida +{self.jogador.vida - antes}"
            self.saida(f"\nVocê bebe a poção de cura ({efeito}). Vida: {self.jogador.vida}/{self.jogador.vida_max}.")
        else:
            pecado, valor = max(self.jogador.pecados.items(), key=lambda item: item[1])
            if valor == 0:
                self.saida("Não há pecado em você para a água benta purificar.")
                return
            efeito = f"{NOMES[pecado]} -{min(valor, PURIFICACAO_AGUA)}"
            self.saida(f"\nVocê derrama a água benta sobre as mãos. A {NOMES[pecado]} recua por um instante.")
        inventario[item] -= 1
        self.ultimo["item"] = {"id": item, "nome": ITENS[item][0], "efeito": efeito}
        if item == "agua_benta":
            self._consequencias({pecado: -PURIFICACAO_AGUA}, gatilho="usar água benta", detalhe="item: água benta")
        if self.jogador.combate and not self.encerrado:
            # Usar um item gasta o turno: o oponente ataca.
            self._turno_combate(self.npcs[self.jogador.combate["npc"]], 0, "item")
        self._salvar()

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

    def cmd_veredito(self, decisao):
        decisao = _sem_acento(decisao.strip())
        acusado = self.npcs[self.cena.get("acusado", "tomas")]
        if acusado.vivo and decisao not in ("absolver", "condenar"):
            self.saida(f"Uso: /veredito absolver  ou  /veredito condenar  (julga {acusado.nome} e encerra a partida)")
            return
        pecado, valor = max(self.jogador.pecados.items(), key=lambda item: item[1])
        if not acusado.vivo:
            julgamento = f"Com {acusado.nome} morto, não resta ninguém a julgar. A praça só espera para ver quem você se tornou."
        elif decisao == "absolver":
            julgamento = f"Você ergue a mão e declara {acusado.nome} livre. A multidão hesita, mas abre caminho."
        else:
            julgamento = f"Você declara {acusado.nome} culpado. A multidão urra, e a corda é preparada no pelourinho."
        if valor < corrupcao.LIMIAR_MANIFESTACAO:
            titulo = "Redenção"
            desfecho = (
                "Nenhum pecado tomou forma dentro de você. Pela primeira vez em anos, Cinzaforte vê um julgamento "
                "sem ódio nem ouro por trás, e a manifestação da Ira perde força sobre a cidade."
            )
        else:
            nome = self.manifestacoes[pecado]["nome"]
            titulo = f"Marcado pela {NOMES[pecado]}"
            desfecho = (
                f"O veredito sai da sua boca, mas a voz não é só sua: {nome} fala junto. Cinzaforte ganha um juiz, "
                f"e a {NOMES[pecado]} ganha um servo. O caso está encerrado; você, não."
            )
        self.jogador.eventos.append(f"Veredito: {decisao or 'sem julgamento'} ({acusado.nome}).")
        self._encerrar(titulo, f"{julgamento} {desfecho}")

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

    def _npc_em_combate(self):
        if not self.jogador.combate:
            self.saida("Você não está em combate. Use /atacar para começar um.")
            return None
        return self.npcs[self.jogador.combate["npc"]]

    def _turno_combate(self, npc, dano, acao):
        """Um turno: o golpe do jogador (se houver) e, se o oponente seguir de pé, o revide dele."""
        combate = self.jogador.combate
        causado = 0
        if dano:
            if combate["brecha"]:
                dano *= 2
                self.saida("Você aproveita a brecha: o golpe sai em dobro.")
            combate["brecha"] = False
            causado = min(dano, npc.vida)
            npc.vida -= causado
            self.saida(f"  {npc.nome} sofre {causado} de dano (vida {npc.vida}/{npc.vida_max}).")
            if npc.vida == 0:
                self._registrar_combate(npc, acao, "venceu", causado=causado)
                self._derrubar(npc)
                return
        recebido = round(npc.dano * FRACAO_DEFESA) if acao == "defender" else npc.dano
        if acao == "defender":
            combate["brecha"] = True
        if npc.dano == 0:
            self.saida(f"  {npc.nome} não tem como revidar.")
        else:
            self.jogador.vida = max(0, self.jogador.vida - recebido)
            self.saida(f"  {npc.nome} revida: {recebido} de dano (sua vida {self.jogador.vida}/{self.jogador.vida_max}).")
        morreu = self.jogador.vida == 0
        self._registrar_combate(npc, acao, "derrota" if morreu else "continua", causado=causado, recebido=recebido)
        if morreu:
            self.jogador.combate = None
            self.jogador.eventos.append(f"Morreu lutando contra {npc.nome}.")
            self._encerrar(
                "Morto em Cinzaforte",
                f"O golpe de {npc.nome} te derruba sobre as pedras da praça. A multidão fecha o círculo, e o "
                f"inquisitor que veio julgar a cidade termina julgado por ela.",
            )
        else:
            self._salvar()

    def _derrubar(self, npc):
        npc.vivo = False
        self.jogador.combate = None
        self.saida(f"\n{npc.nome} cai sem vida sobre as pedras da praça.")
        for testemunha in self.npcs.values():
            if testemunha.vivo:
                delta = corrupcao.delta_relacao("violencia", 3, testemunha.reage_bem_a)
                testemunha.ajustar_relacao(delta)
                testemunha.lembrar(f"Viu o inquisitor matar {npc.nome} na praça.", MAX_MEMORIAS)
                self.saida(f"  {testemunha.nome} viu tudo (relação {delta:+d}).")
        self.jogador.eventos.append(f"Matou {npc.nome}.")
        self._consequencias(corrupcao.ACOES["matar"], gatilho=f"matar {npc.nome}", detalhe="ação: matar")

    def _registrar_combate(self, npc, acao, resultado, causado=0, recebido=0):
        self.ultimo["combate"] = {
            "npc": npc.id,
            "acao": acao,
            "dano_causado": causado,
            "dano_recebido": recebido,
            "vida_npc": npc.vida,
            "vida_npc_max": npc.vida_max,
            "vida_jogador": self.jogador.vida,
            "resultado": resultado,
        }

    def _consequencias(self, deltas, gatilho, detalhe):
        aplicados, novas = corrupcao.aplicar(self.jogador.pecados, deltas, self.jogador.manifestacoes)
        # Um comando pode aplicar pecado mais de uma vez (atacar e matar no mesmo golpe): soma tudo.
        acumulado = self.ultimo.setdefault("pecados", {})
        for pecado, valor in aplicados.items():
            if valor:
                acumulado[pecado] = acumulado.get(pecado, 0) + valor
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
        self.ultimo["manifestacao"] = {"pecado": pecado, "nome": manifestacao["nome"], "fala": fala}
        self.saida(f"\n*** {manifestacao['nome']} desperta dentro de você ***\n{manifestacao['nome']}: {fala}")

    def _final_consumido(self, pecado):
        nome = self.manifestacoes[pecado]["nome"]
        self._encerrar(
            f"Consumido pela {NOMES[pecado]}",
            f"{nome} toma o controle. O inquisitor que chegou a Cinzaforte não existe mais — "
            f"agora a cidade tem uma nova manifestação.",
        )

    def _encerrar(self, titulo, texto):
        self.jogador.final = titulo
        self.ultimo["final"] = {"titulo": titulo, "texto": texto}
        self.saida(f"\n=== FINAL: {titulo.upper()} ===\n{texto}")
        self.encerrado = True
        self._salvar()

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

    def estado(self):
        """Fotografia do jogo para a interface web: jogador, NPCs, cena e limiares."""
        return {
            "cena": self.cena,
            "atual": self.atual,
            "encerrado": self.encerrado,
            "jogador": {
                "nome": self.jogador.nome,
                "ouro": self.jogador.ouro,
                "pecados": dict(self.jogador.pecados),
                "manifestacoes": list(self.jogador.manifestacoes),
                "eventos": list(self.jogador.eventos),
                "final": self.jogador.final,
                "aparencia": corrupcao.aparencia(self.jogador.pecados),
                "vida": self.jogador.vida,
                "vida_max": self.jogador.vida_max,
                "inventario": [
                    {"id": i, "nome": ITENS[i][0], "efeito": ITENS[i][1], "quantidade": q}
                    for i, q in self.jogador.inventario.items()
                    if i in ITENS
                ],
                "combate": self.jogador.combate,
            },
            "npcs": [
                {
                    "id": npc.id,
                    "nome": npc.nome,
                    "descricao": npc.descricao,
                    "relacao": npc.relacao,
                    "rotulo_relacao": rotulo_relacao(npc.relacao),
                    "vivo": npc.vivo,
                    "ouro": npc.ouro,
                    "vida": npc.vida,
                    "vida_max": npc.vida_max,
                    "memorias": list(npc.memorias),
                }
                for npc in self.npcs.values()
            ],
            "manifestacoes": {
                pecado: {"nome": m["nome"], "poder": m["poder"]} for pecado, m in self.manifestacoes.items()
            },
            "limiares": {
                "manifestacao": corrupcao.LIMIAR_MANIFESTACAO,
                "consumido": corrupcao.LIMITE_CONSUMIDO,
            },
        }

    def hud(self):
        visiveis = [p for p in PECADOS if p in ("ira", "avareza") or self.jogador.pecados[p] > 0]
        medidores = " | ".join(f"{NOMES[p]} {_barra(self.jogador.pecados[p])} {self.jogador.pecados[p]}" for p in visiveis)
        return f"  Vida {self.jogador.vida}/{self.jogador.vida_max} | {medidores} | Ouro {self.jogador.ouro}"


def _sem_acento(texto):
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)).lower()


def _barra(valor):
    cheios = valor // 10
    return "█" * cheios + "░" * (10 - cheios)
