"""Ollama simulado para o teste de ponta a ponta: responde rápido, pelo tipo de pedido do jogo."""

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

VIOLENCIA = ("mato", "matar", "cabeça", "sangue")


class Ollama(BaseHTTPRequestHandler):
    def _enviar(self, corpo):
        dados = json.dumps(corpo).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(dados)

    def do_GET(self):
        self._enviar({"models": [{"name": "qwen2.5:7b"}]})

    def do_POST(self):
        corpo = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        campos = set(corpo.get("format", {}).get("properties", {}))
        ultima = corpo["messages"][-1]["content"].lower()
        if campos == {"intencao", "intensidade"}:
            violento = any(p in ultima for p in VIOLENCIA)
            conteudo = {"intencao": "violencia" if violento else "compaixao", "intensidade": 3 if violento else 2}
        elif campos == {"fala"}:
            conteudo = {"fala": "Isso. Deixe o sangue ferver, inquisitor. Minha força é sua, mas eu cobro caro."}
        elif campos:
            conteudo = {"emocao": "medo", "fala": "Por favor, senhor, eu só queria salvar minha filha!", "memoria": "O inquisitor me pressionou na praça."}
        else:
            conteudo = {}
        self._enviar({"message": {"content": json.dumps(conteudo, ensure_ascii=False)}})

    def log_message(self, *args):
        pass


ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1])), Ollama).serve_forever()
