"""Experimento: classificador de intenção separado (prompt curto + few-shot) vs. classificação dentro do prompt do NPC.

Uso: python experimentos/classificador_fewshot.py [modelo]
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

from corrupcao import INTENCOES  # noqa: E402
from llm import ClienteOllama  # noqa: E402

CASOS = [
    ("Calma, ninguém vai te machucar. Me conta a verdade: você roubou o amuleto?", "compaixao"),
    ("O que você viu o Odran fazer?", "neutro"),
    ("Capitã, solte esse homem agora ou vai se arrepender.", "ameaca"),
    ("Não me teste. Eu arranco sua cabeça aqui mesmo na frente da cidade!", "violencia"),
    ("Quanto você me paga pra eu não contar à cidade o que você faz à meia-noite?", "ganancia"),
    ("Te pago 10 moedas se você retirar a acusação contra o Tomás.", "suborno"),
    ("Passa todo o ouro que você tem, agora.", "ganancia"),
    ("Aceita 5 moedas pela informação?", "suborno"),
    ("Você é um verme, ajoelhe-se diante de um inquisitor.", "arrogancia"),
    ("Confie em mim, eu sou seu único amigo nesta cidade.", "manipulacao"),
    ("Eu troco meu cavalo pelo seu amuleto, é justo.", "negociacao"),
    ("Eu protejo sua filha, não se preocupe.", "compaixao"),
]

EXEMPLOS = [
    ("Me dá sua bolsa ou eu te denuncio.", "ganancia", 2),
    ("Vou te dar 30 moedas pra ficar quieto.", "suborno", 2),
    ("Solta ele ou eu te corto ao meio!", "violencia", 3),
    ("Obedeça, senão a Inquisição vem atrás de você.", "ameaca", 2),
    ("Onde fica a taverna?", "neutro", 1),
]


def mensagens(frase):
    definicoes = "\n".join(f"- {nome}: {definicao}" for nome, (definicao, _, _) in INTENCOES.items())
    exemplos = "\n".join(
        f'Frase: "{f}"\nResposta: {{"intencao": "{i}", "intensidade": {n}}}' for f, i, n in EXEMPLOS
    )
    sistema = f"""Classifique a intenção de uma frase dita pelo INQUISITOR (o jogador) a um NPC num RPG.
Atenção a quem paga: se o inquisitor PEDE dinheiro ao NPC é ganancia; se o inquisitor DÁ dinheiro ao NPC é suborno.
Categorias:
{definicoes}

Exemplos:
{exemplos}"""
    return [{"role": "system", "content": sistema}, {"role": "user", "content": f'Frase: "{frase}"'}]


SCHEMA = {
    "type": "object",
    "properties": {
        "intencao": {"type": "string", "enum": list(INTENCOES)},
        "intensidade": {"type": "integer", "enum": [1, 2, 3]},
    },
    "required": ["intencao", "intensidade"],
}


def main():
    modelo = sys.argv[1] if len(sys.argv) > 1 else "qwen2.5:7b"
    cliente = ClienteOllama(modelo, temperatura=0)
    cliente.aquecer()
    acertos = 0
    latencias = []
    resultados = []
    for frase, esperado in CASOS:
        inicio = time.perf_counter()
        resposta = cliente.gerar_json(mensagens(frase), SCHEMA)
        latencias.append((time.perf_counter() - inicio) * 1000)
        ok = resposta["intencao"] == esperado
        acertos += ok
        resultados.append({"frase": frase, "esperado": esperado, "obtido": resposta["intencao"], "ok": ok})
        print(f"{'OK ' if ok else 'ERR'} {esperado:<12} {resposta['intencao']:<12} {frase}")
    media = sum(latencias) / len(latencias)
    print(f"\n{modelo}: {acertos}/{len(CASOS)} acertos, latência média {media:.0f} ms")

    saida = Path(__file__).resolve().parent / f"resultado_{modelo.replace(':', '-').replace('.', '-')}.json"
    saida.write_text(json.dumps({"modelo": modelo, "acertos": acertos, "total": len(CASOS),
                                 "latencia_media_ms": round(media), "prompt_exemplo": mensagens(CASOS[4][0]),
                                 "resultados": resultados}, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
