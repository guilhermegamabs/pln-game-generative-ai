"""Cliente HTTP (requests) da API do jogo. O painel só fala com a API, nunca com o Ollama ou o Piper."""

import time

import requests


class ErroAPI(Exception):
    def __init__(self, mensagem, codigo=None):
        super().__init__(mensagem)
        self.codigo = codigo


class ClienteAPI:
    def __init__(self, url, api_key, timeout=200):
        self.url = url.rstrip("/")
        self.sessao = requests.Session()
        self.sessao.headers["X-API-Key"] = api_key
        self.timeout = timeout
        self.ultima = None  # Última chamada (rota, código, latência): o painel mostra como evidência.

    def _chamar(self, metodo, rota, **kwargs):
        inicio = time.perf_counter()
        try:
            resposta = self.sessao.request(metodo, f"{self.url}{rota}", timeout=self.timeout, **kwargs)
        except requests.RequestException as erro:
            self.ultima = {"metodo": metodo, "rota": rota, "codigo": None, "ms": None}
            raise ErroAPI(f"API fora do ar em {self.url} ({erro.__class__.__name__}).") from erro
        self.ultima = {
            "metodo": metodo,
            "rota": rota,
            "codigo": resposta.status_code,
            "ms": round((time.perf_counter() - inicio) * 1000),
        }
        if not resposta.ok:
            try:
                detalhe = resposta.json().get("detail", resposta.text)
            except ValueError:
                detalhe = resposta.text
            raise ErroAPI(f"HTTP {resposta.status_code}: {detalhe}", resposta.status_code)
        return resposta

    def health(self):
        return self._chamar("GET", "/health").json()

    def status(self):
        return self._chamar("GET", "/v1/ia-generativa/status").json()

    def texto(self, mensagens, schema=None, temperatura=None):
        corpo = {"mensagens": mensagens, "schema_resposta": schema}
        if temperatura is not None:
            corpo["temperatura"] = temperatura
        return self._chamar("POST", "/v1/ia-generativa/texto", json=corpo).json()

    def voz(self, texto, velocidade=1.0):
        return self._chamar("POST", "/v1/ia-generativa/voz", json={"texto": texto, "velocidade": velocidade}).content
