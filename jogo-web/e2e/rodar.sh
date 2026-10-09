#!/bin/bash
# Sobe Ollama simulado (11998), API (8766) e Vite (5174) só para o teste, roda e derruba tudo.
set -u
RAIZ="$(cd "$(dirname "$0")/../.." && pwd)"
TMP="$(mktemp -d)"
cd "$RAIZ"
.venv/bin/python jogo-web/e2e/ollama_falso.py 11998 & P1=$!
(cd api && API_KEY=chave-e2e OLLAMA_URL=http://127.0.0.1:11998 PASTA_PARTIDAS="$TMP" CORS_ORIGENS=http://localhost:5174 \
  PIPER_VOZ="${PIPER_VOZ:-}" exec ../.venv/bin/uvicorn main:app --port 8766 --log-level warning) & P2=$!
(cd jogo-web && VITE_API_URL=http://localhost:8766 VITE_API_KEY=chave-e2e exec ./node_modules/.bin/vite --port 5174 --strictPort --logLevel warn) & P3=$!
trap 'kill $P1 $P2 $P3 2>/dev/null; rm -rf "$TMP"' EXIT
for i in $(seq 60); do curl -s localhost:8766/health >/dev/null && curl -s localhost:5174 >/dev/null && break; sleep 0.5; done
cd jogo-web && node e2e/jogar.mjs
