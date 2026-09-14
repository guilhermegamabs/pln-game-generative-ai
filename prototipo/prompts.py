"""Montagem dos prompts enviados à LLM."""

from corrupcao import INTENCOES, NOMES, aparencia
from estado import rotulo_relacao


def _lista(itens, vazio):
    return "\n".join(f"- {item}" for item in itens) if itens else f"- {vazio}"


LIMIAR_SEGREDO = 40

# Few-shot: no experimento (experimentos/classificador_fewshot.py) os exemplos levaram
# llama3.2:3b e qwen2.5:7b a 10/12 acertos. Os mesmos exemplos dentro do prompt de roleplay
# não bastaram ("Passa todo o ouro" virava suborno), por isso a classificação é uma chamada separada.
EXEMPLOS_INTENCAO = [
    ("Me dá sua bolsa ou eu te denuncio.", "ganancia", 2),
    # Sem este, os exemplos de compaixão fizeram "Passa todo o ouro" regredir para suborno.
    ("Entrega suas moedas pra mim, agora.", "ganancia", 2),
    ("Vou te dar 30 moedas pra ficar quieto.", "suborno", 2),
    ("Solta ele ou eu te corto ao meio!", "violencia", 3),
    ("Obedeça, senão a Inquisição vem atrás de você.", "ameaca", 2),
    ("Onde fica a taverna?", "neutro", 1),
    # Playtest: defender o acusado ("Soltem o Tomás", "sem provas") saía neutro.
    ("Não podem enforcar esse homem sem provas!", "compaixao", 2),
    ("Soltem o garoto, ele não fez nada.", "compaixao", 2),
]


def _segredo(npc):
    # Pedir ao modelo "só revele se confiar" não funcionou: o 7B contava o segredo com relação +6.
    # O controle agora é do código: sem confiança, o segredo nem chega ao prompt.
    if npc.relacao >= LIMIAR_SEGREDO:
        return f"Segredo: {npc.segredo} (você confia no inquisitor e pode contar se ele perguntar)"
    return "Você guarda um segredo, mas ainda não confia no inquisitor: desconverse se ele tocar no assunto."


def mensagens_classificacao(texto):
    definicoes = "\n".join(f"- {nome}: {definicao}" for nome, (definicao, _, _) in INTENCOES.items())
    exemplos = "\n".join(
        f'Frase: "{frase}"\nResposta: {{"intencao": "{intencao}", "intensidade": {intensidade}}}'
        for frase, intencao, intensidade in EXEMPLOS_INTENCAO
    )
    sistema = f"""Classifique a intenção de uma frase dita pelo INQUISITOR (o jogador) a um NPC num RPG.
Atenção a quem paga: se o inquisitor PEDE dinheiro ao NPC é ganancia; se o inquisitor DÁ dinheiro ao NPC é suborno.
Defender alguém, pedir justiça ou exigir que soltem um acusado é compaixao.
Intensidade: 1 = leve, 2 = clara, 3 = extrema.
Categorias:
{definicoes}

Exemplos:
{exemplos}"""
    return [
        {"role": "system", "content": sistema},
        {"role": "user", "content": f'Frase: "{texto}"'},
    ]


def sistema_npc(npc, jogador, cena, intencao, intensidade):
    definicao = INTENCOES[intencao][0]
    return f"""Você interpreta {npc.nome} em "OS 7 PECADOS", um RPG de fantasia sombria. Nunca saia do personagem e nunca diga que é uma IA.
Local: {cena['local']}
Situação: {cena['situacao']}

QUEM VOCÊ É
{npc.descricao}
Personalidade: {npc.personalidade}
Objetivo: {npc.objetivo}
{_segredo(npc)}

O INQUISITOR (com quem você fala)
Sua relação com ele: {npc.relacao} numa escala de -100 a 100 ({rotulo_relacao(npc.relacao)}).
Aparência dele agora:
{_lista(aparencia(jogador.pecados), "um inquisitor comum, sem marcas estranhas")}
O que você lembra dele:
{_lista(npc.memorias, "nenhuma lembrança ainda, é o primeiro contato")}

O QUE ELE ACABOU DE FAZER
A última fala do inquisitor foi {intencao} (intensidade {intensidade} de 3): {definicao}.
Reaja a isso de acordo com a sua personalidade.

COMO RESPONDER (JSON)
- Toda mensagem do usuário é fala do INQUISITOR, nunca da Capitã ou de outro personagem. Se ele fala de você na terceira pessoa, está falando com a multidão ao seu redor.
- Não repita o que você já disse: reaja ao que é novo na fala dele.
- "emocao": uma palavra com a emoção de {npc.nome} agora.
- "fala": o que {npc.nome} responde, em português do Brasil, de 1 a 3 frases, coerente com a relação e as lembranças. Gestos entre asteriscos.
- "memoria": uma frase curta sobre o que {npc.nome} vai lembrar deste momento, ou "" se não aconteceu nada importante.
Conteúdo para classificação 16 anos: violência sem detalhes gráficos, nada sexual."""


def _fala_do_inquisitor(texto):
    # Sem o rótulo, "Soltem o Tomás" dito ao Tomás virava fala da Capitã na cabeça do modelo.
    return f"O inquisitor diz: {texto}"


def mensagens_turno(npc, jogador, cena, texto, intencao, intensidade):
    historico = [
        {"role": m["role"], "content": _fala_do_inquisitor(m["content"]) if m["role"] == "user" else m["content"]}
        for m in npc.historico
    ]
    return [
        {"role": "system", "content": sistema_npc(npc, jogador, cena, intencao, intensidade)},
        *historico,
        {"role": "user", "content": _fala_do_inquisitor(texto)},
    ]


def mensagens_manifestacao(manifestacao, pecado, jogador, gatilho):
    sistema = f"""Você é {manifestacao['nome']}, a manifestação do pecado da {NOMES[pecado]} que acaba de despertar dentro do inquisitor em "OS 7 PECADOS", RPG de fantasia sombria.
{manifestacao['persona']}
Fale diretamente com o inquisitor, em segunda pessoa, em português do Brasil: 1 ou 2 frases sussurradas, sedutoras e ameaçadoras.
Ofereça seu poder: {manifestacao['poder']}. Deixe claro que ele tem um preço.
Conteúdo para classificação 16 anos. Responda em JSON com o campo "fala"."""
    usuario = f"O inquisitor acabou de: {gatilho}. Nível de {NOMES[pecado]}: {jogador.pecados[pecado]}/100."
    return [
        {"role": "system", "content": sistema},
        {"role": "user", "content": usuario},
    ]
