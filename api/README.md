# API de IA generativa · OS 7 PECADOS (CP5)

Back-end FastAPI que encapsula a IA generativa do jogo. O jogo e o painel chamam **esta API**; só ela fala com o Ollama (texto) e com o Piper (voz).

```
 jogo / painel ──HTTP + X-API-Key──► routers/ia_generativa.py ──► providers/ia_provider.py ──► Ollama (texto)
                                     (validação, auth, códigos)     (única camada que conhece    Piper  (voz)
                                                                     os serviços de IA)
```

## Estrutura

| Arquivo | Papel |
|---|---|
| `main.py` | Cria o app, CORS, registra o router, `/health` |
| `routers/ia_generativa.py` | Rotas `/v1/ia-generativa/*`, protegidas por API Key |
| `providers/ia_provider.py` | Chamada ao Ollama (`/api/chat` com JSON Schema) e síntese com Piper |
| `seguranca.py` | Valida o header `X-API-Key` |
| `schemas.py` | Modelos Pydantic de entrada e saída |
| `config.py` | Configuração lida do ambiente (`.env`) |
| `tests/test_api.py` | 18 testes unitários (rotas com provider falso, provider com Ollama simulado) |
| `tests/test_integracao.py` | 20 testes pela rede de verdade: uvicorn + Ollama simulado + o jogo do protótipo jogando pela API; 5 deles usam o Piper real |

## Rotas

| Método | Rota | Auth | O que faz |
|---|---|---|---|
| `POST` | `/v1/ia-generativa/texto` | X-API-Key | Recebe `mensagens` + `schema_resposta` (opcional) + `temperatura`, devolve `conteudo`, `modelo`, `latencia_ms` |
| `POST` | `/v1/ia-generativa/voz` | X-API-Key | Recebe `texto` + `velocidade`, devolve `audio/wav`. Gestos entre `*asteriscos*` não são falados |
| `GET` | `/v1/ia-generativa/status` | X-API-Key | Diz se texto e voz estão disponíveis (o jogo usa para decidir o modo offline) |
| `GET` | `/health` | não | A API está no ar |
| `GET` | `/docs` | não | Swagger |

Códigos de erro: `401` chave ausente ou errada · `422` entrada inválida · `502` a IA respondeu com erro ou JSON inválido · `503` a IA está fora do ar (o jogo deve cair no fallback).

## Como rodar

Linux / macOS:

```bash
python -m venv .venv
.venv/bin/pip install -r api/requirements.txt
cp api/.env.example api/.env                       # e troque API_KEY
ollama pull qwen2.5:7b
cd api
../.venv/bin/uvicorn main:app --reload --env-file .env
```

Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\pip install -r api\requirements.txt
Copy-Item api\.env.example api\.env              # e troque API_KEY
ollama pull qwen2.5:7b
cd api
..\.venv\Scripts\uvicorn main:app --reload --env-file .env
```

O comando precisa rodar de dentro de `api/` (os imports são relativos a essa pasta).

Abra http://localhost:8000/docs, clique em **Authorize** e informe a chave do `.env`.

Para a voz, baixe `pt_BR-faber-medium.onnx` e `.onnx.json` de [rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices/tree/main/pt/pt_BR/faber/medium) e aponte `PIPER_VOZ` para o `.onnx`. Sem isso, `/voz` responde 503 e o resto funciona.

Exemplo:

```bash
curl -X POST http://localhost:8000/v1/ia-generativa/texto \
  -H "X-API-Key: SUA_CHAVE" -H "Content-Type: application/json" \
  -d '{"mensagens":[{"role":"user","content":"Solte esse homem!"}],"temperatura":0}'
```

## Testes

```bash
cd api
../.venv/bin/python -m pytest -q                                   # 33 passam, 5 de voz são pulados
PIPER_VOZ=/caminho/pt_BR-faber-medium.onnx ../.venv/bin/python -m pytest -q   # 38 com o Piper real
```

Nenhum teste precisa do Ollama: ele é simulado por um servidor HTTP local que também imita falhas (erro 500, resposta que não é JSON, lentidão além do timeout, queda no meio da partida).

O que é verificado, além do caminho feliz:

| Situação | Resultado esperado |
|---|---|
| Sem chave ou chave errada (texto, voz e status) | 401, e nada chega ao Ollama |
| Mensagem com mais de 20 mil caracteres ou mais de 40 mensagens | 422, e nada chega ao Ollama |
| Corpo que não é JSON | 422 |
| Ollama com erro 500 | 502 com o detalhe do erro |
| Ollama devolvendo HTML (proxy caído) | 502, não 500 |
| Ollama mais lento que `OLLAMA_TIMEOUT` | 503 sem esperar a resposta |
| Ollama cai no meio da partida | o jogo avisa e segue offline |
| 8 chamadas simultâneas | atendidas em paralelo, não em fila |
| Preflight CORS do front em `:5173` | liberado com o header `X-API-Key` |
| Swagger | toda rota `/v1` exige a chave; `/health` e `/docs` não |
| Acentos e emoji | chegam intactos ao Ollama |
| Voz (Piper real) | WAV mono 16 bits; gestos `*...*` não são falados; velocidade 2.0 encurta o áudio; 4 sínteses simultâneas |

## Painel de teste (Streamlit)

`painel/` é o front de consumo da API: tudo passa por `painel/cliente_api.py` (requests + `X-API-Key`). Ele reaproveita os prompts e schemas reais do jogo (`prototipo/prompts.py`, `prototipo/jogo.py`), então testa exatamente o que o jogo envia.

```bash
.venv/bin/pip install -r painel/requirements.txt
export OS7_API_KEY=sua-chave       # opcional: também dá para digitar na barra lateral
.venv/bin/streamlit run painel/app.py
```

Testes do painel (clicam nos botões com o `AppTest` do Streamlit): `cd painel && ../.venv/bin/python -m pytest -q` (7 testes).

Abas: **Fala de NPC** (classificação + fala + voz, um turno completo do jogo), **Classificar intenção**, **Voz** e **Texto livre**. Cada resultado mostra a rota chamada, o código HTTP e a latência.
