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
| `tests/test_api.py` | 18 testes, sem precisar de Ollama nem Piper |

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

```bash
python -m venv .venv
.venv/bin/pip install -r api/requirements.txt      # Windows: .venv\Scripts\pip
cp api/.env.example api/.env                       # e troque API_KEY
ollama pull qwen2.5:7b
cd api
../.venv/bin/uvicorn main:app --reload --env-file .env
```

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
../.venv/bin/python -m pytest -q
```

## Painel de teste (Streamlit)

`painel/` é o front de consumo da API: tudo passa por `painel/cliente_api.py` (requests + `X-API-Key`). Ele reaproveita os prompts e schemas reais do jogo (`prototipo/prompts.py`, `prototipo/jogo.py`), então testa exatamente o que o jogo envia.

```bash
.venv/bin/pip install -r painel/requirements.txt
export OS7_API_KEY=sua-chave       # opcional: também dá para digitar na barra lateral
.venv/bin/streamlit run painel/app.py
```

Abas: **Fala de NPC** (classificação + fala + voz, um turno completo do jogo), **Classificar intenção**, **Voz** e **Texto livre**. Cada resultado mostra a rota chamada, o código HTTP e a latência.
