"""Clientes de LLM: Ollama local, cliente falso (offline/testes) e registro das chamadas."""

import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime

URL_PADRAO = os.environ.get("OLLAMA_URL", "http://localhost:11434")
# qwen2.5:7b venceu o llama3.2:3b no teste da cena (classificação, memória, português) com latência parecida.
MODELO_PADRAO = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")


class ErroLLM(Exception):
    pass


class ClienteOllama:
    # 0.7 gerava falas confusas no 7B (Brenna mandando "soltar o mercador"); 0.5 segura o personagem.
    def __init__(self, modelo=MODELO_PADRAO, url=URL_PADRAO, timeout=180, temperatura=0.5):
        self.modelo = modelo
        self.url = url.rstrip("/")
        self.timeout = timeout
        self.temperatura = temperatura

    def verificar(self):
        try:
            with urllib.request.urlopen(f"{self.url}/api/tags", timeout=5) as resposta:
                dados = json.loads(resposta.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError) as erro:
            raise ErroLLM(
                f"Ollama não está rodando em {self.url}. Abra o app do Ollama ou rode `ollama serve`."
            ) from erro
        instalados = {m["name"] for m in dados.get("models", [])}
        if self.modelo not in instalados and f"{self.modelo}:latest" not in instalados:
            raise ErroLLM(f"Modelo '{self.modelo}' não está baixado. Rode: ollama pull {self.modelo}")

    def aquecer(self):
        # Carregar o modelo na VRAM leva 20-70 s; sem isso, esse tempo cai no primeiro turno de diálogo.
        requisicao = urllib.request.Request(
            f"{self.url}/api/generate",
            data=json.dumps({"model": self.modelo, "keep_alive": "15m"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(requisicao, timeout=self.timeout):
                pass
        except (urllib.error.URLError, TimeoutError) as erro:
            raise ErroLLM(f"Falha ao carregar o modelo '{self.modelo}': {erro}") from erro

    def gerar_json(self, mensagens, schema, temperatura=None):
        # `format` com JSON Schema faz o Ollama restringir a saída por gramática:
        # mesmo modelos de 3B devolvem JSON válido com os campos e enums pedidos.
        corpo = {
            "model": self.modelo,
            "messages": mensagens,
            "format": schema,
            "stream": False,
            "options": {"temperature": self.temperatura if temperatura is None else temperatura},
        }
        requisicao = urllib.request.Request(
            f"{self.url}/api/chat",
            data=json.dumps(corpo).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(requisicao, timeout=self.timeout) as resposta:
                dados = json.loads(resposta.read().decode("utf-8"))
        except urllib.error.HTTPError as erro:
            detalhe = erro.read().decode("utf-8", "replace")
            if erro.code == 404:
                raise ErroLLM(f"Modelo '{self.modelo}' não encontrado. Rode: ollama pull {self.modelo}") from erro
            raise ErroLLM(f"Ollama devolveu HTTP {erro.code}: {detalhe}") from erro
        except (urllib.error.URLError, TimeoutError) as erro:
            raise ErroLLM(f"Falha ao falar com o Ollama em {self.url}: {erro}") from erro

        conteudo = dados.get("message", {}).get("content", "")
        try:
            return json.loads(conteudo)
        except json.JSONDecodeError as erro:
            raise ErroLLM(f"O modelo não devolveu JSON válido: {conteudo[:200]}") from erro


class ClienteFalso:
    """Responde por palavras-chave. Serve para testar o loop sem Ollama e para os testes automáticos."""

    modelo = "falso"

    PALAVRAS = [
        ("violencia", ("mato", "matar", "morrer", "quebro", "soco", "espada", "sangue", "arranco")),
        ("ameaca", ("senão", "se não", "cuidado", "vai se arrepender", "ou eu")),
        ("suborno", ("pago", "pagar", "propina", "moedas", "suborno")),
        ("ganancia", ("me dá", "me dê", "cobrar", "tudo que você tem", "quero seu")),
        ("arrogancia", ("verme", "inferior", "ajoelhe", "sou superior")),
        ("manipulacao", ("confie em mim", "prometo", "segredo nosso")),
        ("compaixao", ("ajudar", "ajudo", "calma", "entendo", "perdão", "proteger")),
        ("negociacao", ("acordo", "troca", "negociar", "proposta")),
    ]

    FALAS = {
        "violencia": "*recua, trêmulo* Por favor... não precisa disso!",
        "ameaca": "*engole em seco* Está bem, está bem. O que você quer?",
        "arrogancia": "*baixa os olhos* Como quiser, senhor inquisitor.",
        "suborno": "*olha para as moedas* Isso... pode mudar as coisas.",
        "ganancia": "Eu não tenho nada! Juro que não tenho nada!",
        "manipulacao": "*hesita* Por que eu deveria acreditar em você?",
        "compaixao": "*respira aliviado* Ninguém nesta cidade fala assim comigo.",
        "negociacao": "Uma troca justa? Aqui? Vamos ver.",
        "neutro": "*observa você em silêncio por um momento* O que deseja?",
    }

    def gerar_json(self, mensagens, schema, temperatura=None):
        if list(schema["properties"]) == ["fala"]:
            return {"fala": "Sinto seu poder crescer... deixe-me sair. (resposta offline)"}
        texto = mensagens[-1]["content"].lower()
        intencao = next((i for i, palavras in self.PALAVRAS if any(p in texto for p in palavras)), "neutro")
        # Mesmo dicionário serve para a classificação e para a fala: o jogo lê só as chaves de cada etapa.
        return {
            "intencao": intencao,
            "intensidade": 1 if intencao == "neutro" else 2,
            "emocao": "tenso",
            "fala": self.FALAS[intencao],
            "memoria": "" if intencao == "neutro" else f"O inquisitor disse: \"{mensagens[-1]['content'][:80]}\"",
        }


class ClienteRegistrado:
    """Grava cada chamada em JSONL: prompt real + resultado + latência, evidência para a Etapa 2 do relatório."""

    def __init__(self, cliente, caminho):
        self.cliente = cliente
        self.caminho = caminho

    @property
    def modelo(self):
        return self.cliente.modelo

    def gerar_json(self, mensagens, schema, temperatura=None):
        inicio = time.perf_counter()
        resposta = None
        erro = None
        try:
            resposta = self.cliente.gerar_json(mensagens, schema, temperatura)
            return resposta
        except ErroLLM as falha:
            erro = str(falha)
            raise
        finally:
            registro = {
                "quando": datetime.now().isoformat(timespec="seconds"),
                "modelo": self.cliente.modelo,
                "latencia_ms": round((time.perf_counter() - inicio) * 1000),
                "mensagens": mensagens,
                "resposta": resposta,
                "erro": erro,
            }
            self.caminho.parent.mkdir(parents=True, exist_ok=True)
            with open(self.caminho, "a", encoding="utf-8") as arquivo:
                arquivo.write(json.dumps(registro, ensure_ascii=False) + "\n")
