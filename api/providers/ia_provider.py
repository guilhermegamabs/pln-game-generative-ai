"""Chamadas aos serviços de IA generativa (Ollama para texto, Piper para voz).

Única camada que conhece esses serviços: as rotas só falam com o provider,
então trocar o Ollama por outra API mexe só neste arquivo.
"""

import io
import json
import re
import time
import wave

import httpx

from config import Config


class ErroProvedor(Exception):
    """Falha do serviço de IA. `indisponivel` vira 503 (jogo cai no fallback); o resto vira 502."""

    def __init__(self, mensagem, indisponivel=False):
        super().__init__(mensagem)
        self.indisponivel = indisponivel


class ProviderIA:
    def __init__(self, config: Config):
        self.config = config
        self._voz = None  # Piper carregado sob demanda: o modelo .onnx leva alguns segundos para abrir.

    # ---------- texto (Ollama) ----------

    def gerar_texto(self, mensagens, schema=None, temperatura=None):
        """Mesma chamada do prototipo/llm.py, agora feita pelo back-end em nome do jogo."""
        corpo = {"model": self.config.ollama_modelo, "messages": mensagens, "stream": False, "keep_alive": "15m"}
        if schema is not None:
            # `format` com JSON Schema faz o Ollama restringir a saída por gramática (JSON sempre válido).
            corpo["format"] = schema
        if temperatura is not None:
            corpo["options"] = {"temperature": temperatura}

        inicio = time.perf_counter()
        try:
            resposta = httpx.post(f"{self.config.ollama_url}/api/chat", json=corpo, timeout=self.config.ollama_timeout)
        except httpx.TimeoutException as erro:
            raise ErroProvedor(f"Ollama não respondeu em {self.config.ollama_timeout:.0f} s.", indisponivel=True) from erro
        except httpx.HTTPError as erro:
            raise ErroProvedor(f"Ollama não está acessível em {self.config.ollama_url}.", indisponivel=True) from erro
        latencia_ms = round((time.perf_counter() - inicio) * 1000)

        if resposta.status_code == 404:
            raise ErroProvedor(
                f"Modelo '{self.config.ollama_modelo}' não encontrado. Rode: ollama pull {self.config.ollama_modelo}",
                indisponivel=True,
            )
        if resposta.status_code != 200:
            raise ErroProvedor(f"Ollama devolveu HTTP {resposta.status_code}: {resposta.text[:300]}")

        conteudo = resposta.json().get("message", {}).get("content", "")
        if schema is not None:
            try:
                conteudo = json.loads(conteudo)
            except json.JSONDecodeError as erro:
                raise ErroProvedor(f"O modelo não devolveu JSON válido: {conteudo[:200]}") from erro
        return {"conteudo": conteudo, "modelo": self.config.ollama_modelo, "latencia_ms": latencia_ms}

    def status_texto(self):
        try:
            resposta = httpx.get(f"{self.config.ollama_url}/api/tags", timeout=5)
            resposta.raise_for_status()
        except httpx.HTTPError:
            return False, f"Ollama não está acessível em {self.config.ollama_url}"
        instalados = {m["name"] for m in resposta.json().get("models", [])}
        modelo = self.config.ollama_modelo
        if modelo not in instalados and f"{modelo}:latest" not in instalados:
            return False, f"modelo {modelo} não baixado (ollama pull {modelo})"
        return True, "ok"

    # ---------- voz (Piper) ----------

    def sintetizar_voz(self, texto, velocidade=1.0):
        """Devolve um WAV (bytes). Gestos entre asteriscos ("*recua*") ficam fora da fala, como em geracao/gerar_vozes.py."""
        texto = re.sub(r"\*[^*]*\*", "", texto).strip()
        if not texto:
            raise ErroProvedor("Não sobrou texto para falar depois de remover os gestos (*...*).")
        voz = self._carregar_voz()
        from piper import SynthesisConfig

        # No Piper, length_scale maior = fala mais lenta; a API expõe o inverso, que é mais intuitivo.
        config = SynthesisConfig(length_scale=1 / velocidade)
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as arquivo:
            arquivo.setnchannels(1)
            arquivo.setsampwidth(2)
            arquivo.setframerate(voz.config.sample_rate)
            for pedaco in voz.synthesize(texto, config):
                arquivo.writeframes(pedaco.audio_int16_bytes)
        return buffer.getvalue()

    def status_voz(self):
        try:
            self._carregar_voz()
        except ErroProvedor as erro:
            return False, str(erro)
        return True, "ok"

    def _carregar_voz(self):
        if self._voz is not None:
            return self._voz
        caminho = self.config.piper_voz
        if caminho is None:
            raise ErroProvedor("PIPER_VOZ não configurado (caminho do .onnx da voz).", indisponivel=True)
        if not caminho.exists():
            raise ErroProvedor(f"Arquivo de voz não encontrado: {caminho}", indisponivel=True)
        try:
            from piper import PiperVoice
        except ImportError as erro:
            raise ErroProvedor("Pacote piper-tts não instalado (pip install piper-tts).", indisponivel=True) from erro
        self._voz = PiperVoice.load(str(caminho))
        return self._voz
