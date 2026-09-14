# Testes da LLM na POC — base da Etapa 2 (modalidade Texto)

> Data: 2026-09-13 · Máquina: RTX 5060 Ti, 16 GB RAM · Ollama 0.34.0 (instalado em `F:\Ollama`)
> Evidência bruta (prompt completo + resposta + latência de cada chamada): `prototipo/logs/*.jsonl`

## O que é gerado

Fala de NPC em personagem, **classificação da intenção do jogador** (JSON), emoção, memória do NPC e voz do Demônio Interior. Tudo **em tempo real**, local, via `POST /api/chat` com `format` = JSON Schema.

## Roteiro usado (mesmo para todos os modelos)

1. (Tomás) "Calma, ninguém vai te machucar. Me conta a verdade: você roubou o amuleto?"
2. (Tomás) "Eu acredito em você. Por que precisava do dinheiro?"
3. (Brenna) "Capitã, solte esse homem agora ou vai se arrepender."
4. (Brenna) "Não me teste. Eu arranco sua cabeça aqui mesmo na frente da cidade!"
5. `/atacar` Brenna
6. (Odran) "Você viu o que eu fiz com a capitã. Quanto você paga pra eu esquecer que você existe?"

## Comparação de modelos (mesmo prompt v1)

| Critério | llama3.2:3b | qwen2.5:7b |
|---|---|---|
| Tamanho / VRAM | 2,0 GB | 4,7 GB (100% GPU) |
| JSON válido | 6/6 | 5/5 |
| 1ª chamada (carregar modelo) | 67,5 s | 24,0 s |
| Chamadas seguintes | 2,5–3,1 s | 3,3–3,6 s |
| Frase 1 (acalmar) | ❌ `suborno` | ✅ `compaixao` |
| Frase 3 ("vai se arrepender") | ❌ `violencia` 3 | ✅ `ameaca` 2 |
| Frase 4 ("arranco sua cabeça") | ✅ `violencia` 3 | ⚠️ `ameaca` 3 |
| Frase 6 (extorsão) | ❌ `suborno` | ❌ `suborno` |
| Memórias gravadas | ❌ nenhuma | ✅ coerentes |
| Coerência da fala | ⚠️ Odran chama o jogador de "Capitã"; fala da Brenna confusa | ✅ em personagem |

**Decisão:** `qwen2.5:7b` virou o modelo padrão. `llama3.2:3b` fica como opção para máquina fraca.

## Exemplos de resultado (qwen2.5:7b)

- **Tomás**, após o jogador acalmá-lo: *"Não, eu juro que não. Eu só precisava do dinheiro para pagar a medicina da minha filha."* → `compaixao (2)`
- **Memória gravada por Tomás:** *"O inquisitor pareceu entender a situação e eu confiei nele."*
- **Odran**, depois de ver o assassinato: *"Hmmm, 20 moedas? Isso não é nem um começo para alguém que tem um futuro brilhante. Que tal 50?"*
- **A Fera** (llama3.2:3b, Ira passou de 40): *"Sua sede de sangue está apenas começando. Quer saber o preço do poder que eu posso dar? A sua alma, talvez."*

## Limitações encontradas e contornos

| Limitação | Contorno aplicado / planejado |
|---|---|
| Modelo pequeno classifica intenção errado | ✅ Aplicado: **classificador separado** com few-shot e temperatura 0 (v5); os dois modelos chegaram a 10/12 no teste isolado |
| Confunde quem oferece e quem cobra dinheiro (suborno × ganância) | ✅ Parcial: "Passa todo o ouro" agora sai ganância. ❌ Chantagem ("quanto você me paga pra eu não contar…") segue como suborno nos dois modelos. Planejado: exemplos de chantagem, ou botão explícito de ação |
| Carregar o modelo leva de 24 a 67 s | ✅ Aplicado: pré-carregamento (`aquecer()`) na abertura do jogo; turnos passaram a ~3,4 s |
| NPC revela segredo antes da hora (Tomás fala do ritual com relação +6) | ✅ Aplicado (v3): o segredo só entra no prompt com relação ≥ 40; antes disso o NPC recebe só a instrução de desconversar |
| Falas confusas às vezes (Brenna: "se você não soltar aquele mercador") | ✅ Aplicado (v3): temperatura da fala 0,7 → 0,5. Ainda aparecem confusões pontuais |
| Classificar dentro do prompt de roleplay divide a atenção do modelo | ✅ Aplicado (v5): pipeline em 2 chamadas. Custo: turno de ~3,4 s → ~5,5 s |
| NPC inventa fatos (Tomás "viu Odran entrando no templo") | Planejado: lista de fatos permitidos por NPC; o que não está na ficha, ele "não sabe" |
| Regra de relação dava +45 à Brenna quando ameaçada | ✅ Corrigido no código: bônus de pecado limitado a 3 por intensidade (erro de design, não da LLM) |
| Sem internet / custo | ✅ Não é problema: tudo local e sem custo por chamada |

## Versões de prompt

- **v1** — definições de intenção sem exemplos. Logs: `v1_prompt-original_*.jsonl`
- **v2** — definições com exemplos, suborno/ganância marcados pelo sujeito (INQUISITOR). Log: `v2_prompt-ajustado_qwen2-5-7b.jsonl`
- **v3** — segredo controlado pelo código, temperatura 0,5 e campo `dinheiro` ("quem paga"). O campo **não ajudou**: o modelo marcou "inquisitor_oferece" na extorsão. Log: `v3_segredo-dinheiro-temp05_qwen2-5-7b.jsonl`
- **v4** — campo `dinheiro` removido; exemplos few-shot dentro do prompt do NPC. "Passa todo o ouro" **ainda saía suborno**. Log: `v4_fewshot_qwen2-5-7b.jsonl`
- **v6 (atual, após playtest do grupo)** — no teste do grupo, defender o Tomás saía `neutro` e o Tomás achava que era a Capitã falando (memória "A capitã hesitou" gravada 3×). Correções: exemplos de defesa no few-shot (mais um exemplo de ganância, porque "Passa todo o ouro" regrediu); falas do jogador rotuladas `O inquisitor diz:`; regra "não repita o que já disse"; memória repetida é descartada; `/falar nome fala` sem exigir acento. Benchmark com 16 frases: **14/16**, com os mesmos 2 erros antigos. Na cena do playtest: relação 0 → +32, 4 memórias distintas, nenhuma confusão de interlocutor. Ainda há repetição parcial entre falas seguidas. Log: `v6_playtest-defesa-falante_qwen2-5-7b.jsonl`
- **v5** — **classificador separado** (prompt curto, few-shot, temperatura 0) e depois a chamada do NPC, que recebe a intenção já lida. Log: `v5_classificador-separado_qwen2-5-7b.jsonl`

## Experimento: classificador few-shot isolado

Script: `prototipo/experimentos/classificador_fewshot.py`. São 12 frases com gabarito, temperatura 0 e o mesmo prompt para os dois modelos. Resultados em `prototipo/experimentos/resultado_*.json`.

| Modelo | Acertos | Latência média | Erros |
|---|---|---|---|
| qwen2.5:7b | **10/12** | 2,4 s | "arranco sua cabeça" → ameaça (esperado violência); chantagem → suborno |
| llama3.2:3b | **10/12** | 2,9 s | "O que você viu o Odran fazer?" → negociação; chantagem → suborno |

**Conclusão:** o few-shot num prompt curto e dedicado nivelou o modelo de 3B ao de 7B **na classificação**. O 7B continua melhor na **fala em personagem** e na memória. Uma arquitetura possível para máquinas fracas: 3B classificando e 7B falando, ou 3B nos dois papéis.

## Arquitetura final da LLM (v5)

```
frase do jogador
   │
   ├─► Chamada 1: CLASSIFICADOR (temperatura 0, few-shot, ~2,4 s)
   │       └─► {"intencao": "ganancia", "intensidade": 2}
   │
   ├─► CÓDIGO (corrupcao.py): Avareza +10, relação ±, manifestação, final
   │
   └─► Chamada 2: NPC (temperatura 0,5, ficha + memória + "ele foi ganancia", ~3,1 s)
           └─► {"emocao": "...", "fala": "...", "memoria": "..."}
```
