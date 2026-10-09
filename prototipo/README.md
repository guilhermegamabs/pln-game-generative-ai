# OS 7 PECADOS — Protótipo (POC)

Prova de conceito da mecânica central do jogo: **diálogo livre com NPCs movido por LLM local (Ollama)**, com **memória**, **relação** e **sistema de corrupção** pelos 7 pecados.

Cena: Praça do Pelourinho, em Cinzaforte (cidade da Ira). Tomás é acusado de roubar o amuleto do mercador Odran; a Capitã Brenna quer enforcá-lo.

## Requisitos

- Python 3.10+ (só biblioteca padrão, nada de `pip install`)
- [Ollama](https://ollama.com/download) instalado e rodando

## Como rodar

Desde a CP5 o jogo **não chama mais o Ollama direto**: ele chama a API do grupo (`../api/`), que chama o Ollama. Suba a API primeiro (ver `../api/README.md`):

```bash
ollama pull qwen2.5:7b
cd ../api && ../.venv/bin/uvicorn main:app --env-file .env
```

Em outro terminal, com a mesma chave do `api/.env`:

```bash
export OS7_API_KEY=sua-chave        # Windows (PowerShell): $env:OS7_API_KEY="sua-chave"
python main.py
```

Opções:

| Flag | Efeito |
|---|---|
| `--api URL` | Endereço da API (padrão `http://localhost:8000`, também via `OS7_API_URL`) |
| `--direto` | Modo da CP4: fala direto com o Ollama, sem a API |
| `--modelo llama3.2:3b` | Troca o modelo no modo `--direto` (com a API, o modelo é o `OLLAMA_MODEL` do `api/.env`) |
| `--novo` | Ignora o save e recomeça |
| `--offline` | Sem IA: respostas falsas por palavra-chave (para testar o loop) |

**Fallback:** se a API ou o Ollama cair no meio da partida (HTTP 503 ou conexão recusada), o jogo avisa e segue no modo offline em vez de travar.

**Modelo:** `qwen2.5:7b` é o padrão (4,7 GB de VRAM; cerca de 5,5 s por turno numa RTX 5060 Ti, somando classificação e fala): classifica e mantém personagem bem melhor. Em máquina sem GPU boa, use `--modelo llama3.2:3b`. A comparação entre os dois está em `../02_Testes_LLM.md`.

Ao abrir, o jogo pré-carrega o modelo na memória (20–70 s na primeira vez). Depois disso, cada turno leva poucos segundos.

## Comandos no jogo

Texto livre = fala com o NPC atual.

| Comando | O que faz |
|---|---|
| `/falar [nome]` | Troca de NPC (sem nome, lista presentes com relação) |
| `/atacar` | Mata o NPC atual (combate simplificado). Ira +20, testemunhas lembram |
| `/roubar` | Rouba até 25 moedas. Avareza +15 |
| `/doar <valor>` | Dá moedas. Reduz Avareza, melhora relação |
| `/status` | "Espelho da Alma": 7 medidores, aparência, manifestações, eventos |
| `/memorias` | O que o NPC atual lembra de você |
| `/sair` | Salva e sai |

## Como funciona

```
 jogador digita
      │
      ▼
 [1] CLASSIFICADOR  Ollama /api/chat, format = JSON Schema, temperatura 0, few-shot
      └─► {"intencao": "ameaca", "intensidade": 2}
      │
      ▼
 [2] NPC  ficha + relação + aparência do jogador + memórias + histórico + intenção lida
      └─► {"emocao": "medo", "fala": "...", "memoria": "O inquisitor me ameaçou na praça."}
      │
      ├──► fala na tela
      ├──► corrupcao.py (regras fixas): Ira +6, relação -16
      └──► NPC guarda memória
                │
                ▼
   pecado cruzou 40? ──► chamada extra: voz do Demônio Interior
   pecado chegou a 100? ──► FINAL: Consumido
```

**Decisões de design:**
- A LLM **só classifica** a intenção; os pontos de pecado vêm de tabela fixa em `corrupcao.py`. O balanceamento fica controlável e testável.
- A classificação é uma **chamada separada**: dentro do prompt longo de roleplay o modelo errava mais (ver `../02_Testes_LLM.md`).
- O **segredo** do NPC só entra no prompt quando a relação chega a 40. Pedir para o modelo "guardar segredo" não funcionou.

NPCs corrompidos aprovam o próprio pecado: Brenna (Ira) gosta de violência e ameaça; Odran (Avareza) gosta de suborno e ganância.

## Arquivos

| Arquivo | Papel |
|---|---|
| `main.py` | Entrada, argumentos, loop de input |
| `jogo.py` | Turno de diálogo, comandos, consequências, finais |
| `corrupcao.py` | Intenções, pesos dos pecados, limiares, aparência |
| `prompts.py` | Prompts de NPC e de manifestação |
| `llm.py` | Cliente da API (padrão), cliente Ollama direto, fallback, cliente falso, registro de chamadas |
| `estado.py` | Jogador, NPC, save/load JSON |
| `dados/mundo.json` | Cena, fichas dos NPCs, 7 manifestações |
| `logs/sessao_*.jsonl` | **Cada chamada: prompt completo, resposta, modelo, latência** (`v1_`…`v5_` = rodadas documentadas) |
| `experimentos/classificador_fewshot.py` | Benchmark de 12 frases com gabarito para comparar modelos na classificação |
| `saves/partida.json` | Save automático |

## Evidência para o relatório (Etapa 2)

Todo `logs/sessao_*.jsonl` contém o **prompt exato enviado** e o **resultado gerado**, com modelo e latência em ms. É a evidência de "prompt real + resultado" exigida pela rubrica, e a latência alimenta a seção de limitações técnicas.

## Testes

```bash
python -m unittest discover -s tests -t .
```

Os testes usam o cliente falso, então não precisam de Ollama.
