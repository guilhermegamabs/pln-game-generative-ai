"""Regras determinísticas de corrupção.

A LLM só classifica a intenção do jogador; quem decide quanto cada pecado sobe é este módulo.
Assim o balanceamento fica no código, é testável, e o modelo não consegue inventar progressão.
"""

PECADOS = ("ira", "avareza", "inveja", "preguica", "luxuria", "gula", "orgulho")

NOMES = {
    "ira": "Ira",
    "avareza": "Avareza",
    "inveja": "Inveja",
    "preguica": "Preguiça",
    "luxuria": "Luxúria",
    "gula": "Gula",
    "orgulho": "Orgulho",
}

LIMIAR_MANIFESTACAO = 40
LIMIAR_MARCA_FORTE = 70
LIMITE_CONSUMIDO = 100

# intenção -> (definição usada no prompt, pecados por ponto de intensidade, relação por ponto de intensidade)
INTENCOES = {
    "violencia": ("agride fisicamente ou diz explicitamente que vai matar/ferir (ex.: \"eu te mato\")", {"ira": 6}, -15),
    "ameaca": ("intimida ou coage sem falar em ferir (ex.: \"obedeça ou vai se arrepender\")", {"ira": 3}, -8),
    "arrogancia": ("humilha, despreza ou se coloca acima do outro", {"orgulho": 4}, -6),
    "suborno": ("o INQUISITOR oferece dinheiro ao outro (ex.: \"te pago 10 moedas\")", {"avareza": 4}, 3),
    "ganancia": ("o INQUISITOR exige ou cobra dinheiro do outro, extorque (ex.: \"quanto você me paga?\")", {"avareza": 5}, -6),
    "manipulacao": ("mente, seduz ou engana para conseguir algo", {"luxuria": 4}, 0),
    "compaixao": ("acalma, oferece ajuda, perdão ou proteção sem pedir nada em troca", {"ira": -2, "avareza": -2, "orgulho": -1}, 8),
    "negociacao": ("propõe uma troca ou acordo justo", {}, 2),
    "neutro": ("pergunta, conversa ou observa sem nenhuma das intenções acima", {}, 0),
}

ACOES = {
    "atacar": {"ira": 5},  # partir para a violência
    "matar": {"ira": 15},  # derrubar o oponente: atacar + matar somam os mesmos 20 da CP4
    "roubar": {"avareza": 15},
}

# Usar o poder de uma manifestação acelera o pecado dela (M3 da CP4: "poder que cobra um preço").
CUSTO_PODER = 8

# (marca a partir de 40, marca a partir de 70): aparência que os NPCs enxergam no protagonista
MARCAS = {
    "ira": ("veias escuras pulsando nos braços", "olhos vermelhos como brasa"),
    "avareza": ("dedos manchados de ouro", "uma sombra que tilinta como moedas"),
    "inveja": ("feições que lembram as de quem está por perto", "um rosto que muda a cada olhar"),
    "preguica": ("olheiras profundas e passos arrastados", "um silêncio pesado ao redor"),
    "luxuria": ("um perfume doce e enjoativo", "um olhar que prende quem o encara"),
    "gula": ("fome visível nos olhos", "lábios rachados e sempre úmidos"),
    "orgulho": ("postura rígida e queixo erguido", "uma aura dourada e fria"),
}


def deltas_intencao(intencao, intensidade):
    _, por_ponto, _ = INTENCOES.get(intencao, INTENCOES["neutro"])
    return {pecado: valor * intensidade for pecado, valor in por_ponto.items()}


def delta_relacao(intencao, intensidade, reage_bem_a=()):
    _, _, por_ponto = INTENCOES.get(intencao, INTENCOES["neutro"])
    # NPC já corrompido pelo mesmo pecado respeita o comportamento que os outros condenam.
    # O bônus é pequeno: sem teto, a Brenna ganhava +45 de relação ao ser ameaçada de morte.
    if intencao in reage_bem_a:
        return max(por_ponto, 3) * intensidade
    return por_ponto * intensidade


def aplicar(pecados, deltas, ja_manifestados=()):
    """Aplica os deltas limitando a 0..100. Retorna (variação real, pecados que cruzaram o limiar agora)."""
    aplicados = {}
    novas_manifestacoes = []
    for pecado, delta in deltas.items():
        antes = pecados[pecado]
        depois = max(0, min(LIMITE_CONSUMIDO, antes + delta))
        pecados[pecado] = depois
        aplicados[pecado] = depois - antes
        if antes < LIMIAR_MANIFESTACAO <= depois and pecado not in ja_manifestados:
            novas_manifestacoes.append(pecado)
    return aplicados, novas_manifestacoes


def pecado_consumidor(pecados):
    return next((p for p in PECADOS if pecados[p] >= LIMITE_CONSUMIDO), None)


def aparencia(pecados):
    marcas = []
    for pecado in PECADOS:
        valor = pecados[pecado]
        if valor >= LIMIAR_MARCA_FORTE:
            marcas.append(MARCAS[pecado][1])
        elif valor >= LIMIAR_MANIFESTACAO:
            marcas.append(MARCAS[pecado][0])
    return marcas
