# OS 7 PECADOS — IA Generativa e Game Design (CP4 e CP5)

RPG narrativo de fantasia sombria em que uma LLM local é o motor de interação: o jogador conversa em texto livre com os NPCs, eles lembram do que ele fez, e cada escolha alimenta um dos sete pecados capitais.

**Integrantes:** Guilherme Gama Bitencourt Souza (RM565293) · Igor Thiago Nakajima Vieira (RM563632)

📄 **Entrega:** [`OS_7_PECADOS_CP4.pdf`](OS_7_PECADOS_CP4.pdf) — relatório técnico + mockup.

## CP5: MVP jogável

| Pasta | Conteúdo |
|---|---|
| [`jogo-web/`](jogo-web/) | **O jogo**: React + TypeScript (Vite) com as telas do mockup (menu, gameplay, Espelho da Alma, final). [Como rodar e jogar](jogo-web/README.md) |
| [`api/`](api/) | **API FastAPI do grupo**: rotas de IA generativa (texto e voz) e do jogo, com API Key e Swagger em `/docs`. [Detalhes](api/README.md) |
| [`painel/`](painel/) | Painel Streamlit que consome a API via `requests` |
| [`prototipo/`](prototipo/) | Núcleo do jogo (regras, prompts, memória), o mesmo da CP4, agora usado pela API; também roda no terminal |

```
navegador (jogo-web) ──X-API-Key──► API FastAPI ──► Ollama (qwen2.5:7b, texto)
painel / terminal ─────X-API-Key──►     │       └─► Piper TTS (voz)
                                        └─► núcleo do jogo (prototipo/)
```

Para jogar: Ollama rodando, `api/` no ar (`uvicorn main:app --env-file .env`) e `jogo-web/` com `npm run dev`. Os passos completos estão nos READMEs de cada pasta.

Testes: `api/` (pytest), `painel/` (pytest), `prototipo/` (unittest) e `jogo-web/` (`npm run e2e`, Chrome headless jogando a partida inteira).

## CP4: onde está cada evidência

| Pasta / arquivo | Conteúdo |
|---|---|
| [`OS_7_PECADOS_CP4.pdf`](OS_7_PECADOS_CP4.pdf) | Relatório técnico completo e mockup (3 telas anotadas) |
| [`prototipo/`](prototipo/) | Protótipo jogável em Python com Ollama ([como rodar](prototipo/README.md)) |
| [`prototipo/logs/`](prototipo/logs/) | Prompt exato, resposta e latência de cada chamada à LLM (rodadas v1 a v6) |
| [`prototipo/experimentos/`](prototipo/experimentos/) | Benchmark do classificador de intenção (llama3.2:3b × qwen2.5:7b) |
| [`assets/imagens/`](assets/imagens/) | 7 imagens geradas com Stable Diffusion XL 1.0 |
| [`assets/audio/`](assets/audio/) | 4 vozes geradas com Piper TTS (+ [`variantes/`](assets/audio/variantes/)) |
| [`assets/manifesto_imagens.json`](assets/manifesto_imagens.json) · [`manifesto_audio.json`](assets/manifesto_audio.json) | Prompt, seed, parâmetros e tempo de cada asset |
| [`geracao/`](geracao/) | Scripts que geraram imagens e vozes |
| [`mockup/`](mockup/) | Fonte HTML do mockup e PNGs (limpos e anotados) |
| [`01_Conceito_do_Jogo.md`](01_Conceito_do_Jogo.md) · [`02_Testes_LLM.md`](02_Testes_LLM.md) · [`03_Geracao_Imagem_Voz.md`](03_Geracao_Imagem_Voz.md) | Documentação de trabalho de cada etapa |
| [`relatorio/`](relatorio/) | Fonte HTML do PDF e script de geração |
| [`Relatorio_OS_7_Pecados.pdf`](Relatorio_OS_7_Pecados.pdf) | Pitch inicial do grupo |

## IA generativa usada

| Modalidade | Ferramenta | Uso |
|---|---|---|
| Texto | Ollama + Qwen2.5 7B (local) | Classificação de intenção, falas dos NPCs, memória, Demônio Interior — em tempo real |
| Imagem | Stable Diffusion XL 1.0 (local) | Menu, cenário, retratos, manifestações — offline |
| Voz | Piper TTS pt_BR-faber-medium (local) | Narração e vozes dos personagens |

## Rodar o protótipo

```bash
ollama pull qwen2.5:7b
cd prototipo
python main.py --novo
```
