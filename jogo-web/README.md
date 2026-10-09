# OS 7 PECADOS · Jogo (MVP da CP5)

Interface do jogo em **React + TypeScript (Vite)**, com as telas do mockup da CP4: **Menu**, **Gameplay** (HUD, medidores, intenção lida, memória, sussurro do demônio, diálogo) e **Espelho da Alma** (`Tab`), mais a tela de **Final**.

O navegador só fala com a API do grupo (`../api`). As regras do jogo rodam no servidor (`../prototipo`), e a IA é chamada pelo provider da API:

```
navegador ──X-API-Key──► /v1/jogo/partidas/...      (falas e ações; regras no servidor)
          └────────────► /v1/ia-generativa/voz       (voz da fala do NPC e do demônio)
                                │
                                ▼
                       Ollama (texto, qwen2.5:7b)  ·  Piper (voz)
```

Imagens (SDXL) e narração de abertura (Piper) são os assets gerados na CP4, servidos direto de `../assets`.

## Como rodar

1. Suba a API (ver `../api/README.md`) com o Ollama rodando.
2. Configure e rode o front:

```bash
cp .env.example .env.local     # coloque em VITE_API_KEY a mesma chave do API_KEY de api/.env
npm install
npm run dev                    # http://localhost:5173
```

## Como jogar

- Digite livremente o que quer dizer ao NPC e aperte **Enter**. A LLM classifica a intenção, o código aplica os pecados e o NPC responde (com voz).
- **Na praça**: clique em outro personagem para falar com ele.
- **Atacar** (pede confirmação), **Roubar**, **Doar 10**, **Itens**: ações com consequência fixa.
- **Combate por turnos**: Atacar abre a luta. A vida do inquisitor fica no HUD e a do oponente aparece ao lado do nome dele. Em combate, o diálogo trava e as ações passam a ser:
  - **Golpear**: 25 de dano;
  - **Defender**: recebe 1/4 do dano e o próximo golpe sai em dobro;
  - **Poder**: o da manifestação desperta, 45 de dano, mas o pecado sobe 8;
  - **Poção** e **Água benta**;
  - **Fugir**.

  Cada ação gasta o turno e o oponente revida. Tomás, amarrado, não revida. Vida zerada é derrota: final **Morto em Cinzaforte**.
- **Memórias**: o que o NPC lembra de você. **Espelho da Alma** (`Tab`): os 7 pecados, aparência, manifestações e finais.
- **Veredito**: absolver ou condenar Tomás encerra a partida. O final depende dos pecados naquele momento:
  - **Redenção**: todos abaixo de 40;
  - **Marcado pela (pecado)**: o pecado dominante passou de 40;
  - **Consumido pela (pecado)**: algum pecado chegou a 100 (acontece a qualquer momento).
- A partida fica salva no servidor: **Continuar** no menu retoma de onde parou.

Sem GPU, cada fala leva de 1 a 2 minutos com o qwen2.5:7b; o indicador "pensando" mostra os segundos. Se a IA cair, o jogo avisa e segue com falas simples (modo offline).

## Teste de ponta a ponta

```bash
npm run e2e
```

Sobe um Ollama simulado, a API (porta 8766) e o Vite (porta 5174), e um Chrome headless joga a partida inteira: menu, fala livre, troca de NPC, ataque, manifestação da Fera, Espelho, memórias, veredito, final e "Continuar". Confere que nenhuma chamada sai do navegador para fora da API e salva um print de cada tela em `e2e/prints/`. Para testar com voz, defina `PIPER_VOZ` com o caminho do `.onnx`.
