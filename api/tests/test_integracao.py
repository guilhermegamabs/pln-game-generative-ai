"""Integração pela rede de verdade: uvicorn numa porta + Ollama simulado (HTTP) + o jogo do protótipo.

Os testes de voz usam o Piper real e só rodam com PIPER_VOZ apontando para o .onnx da voz.
"""

import io
import json
import os
import socket
import sys
import tempfile
import threading
import time
import unittest
import wave
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import httpx
import uvicorn
from config import Config
from main import criar_app
from providers.ia_provider import ProviderIA

PROTOTIPO = Path(__file__).resolve().parents[2] / "prototipo"
sys.path.insert(0, str(PROTOTIPO))
from estado import carregar_mundo  # noqa: E402
from jogo import Jogo  # noqa: E402
from llm import ClienteAPI, ClienteComFallback, ClienteFalso, ErroLLM  # noqa: E402

CHAVE = "chave-integracao"
CABECALHO = {"X-API-Key": CHAVE}
PEDIDO = {"mensagens": [{"role": "user", "content": "Solte esse homem!"}], "schema_resposta": {"type": "object"}}
RESPOSTA_NPC = {
    "intencao": "ameaca",
    "intensidade": 2,
    "emocao": "medo",
    "fala": "Por favor, senhor!",
    "memoria": "Fui ameaçado.",
}


def porta_livre():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class OllamaSimulado(BaseHTTPRequestHandler):
    """modo: ok | lento | erro500 | nao_json. Guarda o corpo de cada /api/chat recebido."""

    modo = "ok"
    atraso = 0.0
    recebidos = []

    def _enviar(self, codigo, corpo, tipo="application/json"):
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.end_headers()
        self.wfile.write(corpo.encode("utf-8"))

    def do_GET(self):
        self._enviar(200, json.dumps({"models": [{"name": "qwen2.5:7b"}]}))

    def do_POST(self):
        corpo = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        OllamaSimulado.recebidos.append(corpo)
        if OllamaSimulado.atraso:
            time.sleep(OllamaSimulado.atraso)
        if OllamaSimulado.modo == "erro500":
            return self._enviar(500, json.dumps({"error": "CUDA out of memory"}))
        if OllamaSimulado.modo == "nao_json":
            return self._enviar(200, "<html>proxy caiu</html>", "text/html")
        self._enviar(200, json.dumps({"message": {"content": json.dumps(RESPOSTA_NPC)}}))

    def log_message(self, *args):
        pass


class ServidorOllama(ThreadingHTTPServer):
    # O padrão do Python é 5 conexões na fila: no teste de 8 chamadas simultâneas, às vezes uma era recusada
    # e a API respondia 503 (certo para "Ollama fora", mas o Ollama real aceita bem mais que 5).
    request_queue_size = 64


class Servidores:
    """Sobe um Ollama simulado e a API real (uvicorn) em portas livres."""

    def __init__(self, ollama_timeout=5.0, piper_voz=None):
        self.ollama = ServidorOllama(("127.0.0.1", 0), OllamaSimulado)
        threading.Thread(target=self.ollama.serve_forever, daemon=True).start()
        config = Config(
            api_key=CHAVE,
            ollama_url=f"http://127.0.0.1:{self.ollama.server_port}",
            ollama_timeout=ollama_timeout,
            piper_voz=piper_voz,
            cors_origens=["http://localhost:5173"],
        )
        porta = porta_livre()
        self.url = f"http://127.0.0.1:{porta}"
        self.api = uvicorn.Server(
            uvicorn.Config(criar_app(config, ProviderIA(config)), port=porta, log_level="warning")
        )
        threading.Thread(target=self.api.run, daemon=True).start()
        for _ in range(200):
            if self.api.started:
                break
            time.sleep(0.05)
        else:
            raise RuntimeError("uvicorn não subiu em 10 s")

    def derrubar_ollama(self):
        self.ollama.shutdown()
        self.ollama.server_close()

    def encerrar(self):
        self.api.should_exit = True
        self.derrubar_ollama()


class TestIntegracaoHTTP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = Servidores(ollama_timeout=1.0)
        cls.http = httpx.Client(base_url=cls.srv.url, timeout=10)

    @classmethod
    def tearDownClass(cls):
        cls.http.close()
        cls.srv.encerrar()

    def setUp(self):
        OllamaSimulado.modo = "ok"
        OllamaSimulado.atraso = 0.0
        OllamaSimulado.recebidos = []

    def test_texto_ponta_a_ponta(self):
        resposta = self.http.post("/v1/ia-generativa/texto", json=PEDIDO, headers=CABECALHO)
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()["conteudo"]["fala"], "Por favor, senhor!")
        self.assertEqual(OllamaSimulado.recebidos[0]["format"], {"type": "object"})
        self.assertFalse(OllamaSimulado.recebidos[0]["stream"])

    def test_sem_chave_nao_chega_no_ollama(self):
        self.assertEqual(self.http.post("/v1/ia-generativa/texto", json=PEDIDO).status_code, 401)
        self.assertEqual(self.http.get("/v1/ia-generativa/status").status_code, 401)
        self.assertEqual(self.http.post("/v1/ia-generativa/voz", json={"texto": "oi"}).status_code, 401)
        self.assertEqual(OllamaSimulado.recebidos, [])

    def test_acentos_e_emoji_preservados(self):
        texto = "Ação, coração, pão e 🔥 na praça"
        self.http.post(
            "/v1/ia-generativa/texto", json={"mensagens": [{"role": "user", "content": texto}]}, headers=CABECALHO
        )
        self.assertEqual(OllamaSimulado.recebidos[0]["messages"][0]["content"], texto)

    def test_payload_gigante_recusado_antes_do_ollama(self):
        enorme = {"mensagens": [{"role": "user", "content": "a" * 20_001}]}
        self.assertEqual(self.http.post("/v1/ia-generativa/texto", json=enorme, headers=CABECALHO).status_code, 422)
        muitas = {"mensagens": [{"role": "user", "content": "oi"}] * 41}
        self.assertEqual(self.http.post("/v1/ia-generativa/texto", json=muitas, headers=CABECALHO).status_code, 422)
        self.assertEqual(OllamaSimulado.recebidos, [])

    def test_json_malformado_no_corpo_e_422(self):
        resposta = self.http.post(
            "/v1/ia-generativa/texto", content=b"{nao e json", headers={**CABECALHO, "Content-Type": "application/json"}
        )
        self.assertEqual(resposta.status_code, 422)

    def test_ollama_com_erro_500_vira_502(self):
        OllamaSimulado.modo = "erro500"
        resposta = self.http.post("/v1/ia-generativa/texto", json=PEDIDO, headers=CABECALHO)
        self.assertEqual(resposta.status_code, 502)
        self.assertIn("CUDA out of memory", resposta.json()["detail"])

    def test_ollama_devolvendo_html_vira_502_e_nao_500(self):
        OllamaSimulado.modo = "nao_json"
        resposta = self.http.post("/v1/ia-generativa/texto", json=PEDIDO, headers=CABECALHO)
        self.assertEqual(resposta.status_code, 502)
        self.assertIn("não é JSON", resposta.json()["detail"])

    def test_ollama_lento_alem_do_timeout_vira_503(self):
        OllamaSimulado.atraso = 3.0  # timeout da API neste teste: 1 s
        inicio = time.perf_counter()
        resposta = self.http.post("/v1/ia-generativa/texto", json=PEDIDO, headers=CABECALHO)
        self.assertEqual(resposta.status_code, 503)
        self.assertLess(time.perf_counter() - inicio, 2.5)  # desistiu antes de o Ollama responder

    def test_chamadas_simultaneas_nao_esperam_umas_pelas_outras(self):
        OllamaSimulado.atraso = 0.4
        inicio = time.perf_counter()
        with ThreadPoolExecutor(8) as pool:
            codigos = list(
                pool.map(
                    lambda _: self.http.post("/v1/ia-generativa/texto", json=PEDIDO, headers=CABECALHO).status_code,
                    range(8),
                )
            )
        self.assertEqual(codigos, [200] * 8)
        self.assertLess(time.perf_counter() - inicio, 8 * 0.4 * 0.75)  # em fila levaria 3,2 s

    def test_cors_pelo_servidor_real(self):
        preflight = self.http.options(
            "/v1/ia-generativa/texto",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type,x-api-key",
            },
        )
        self.assertEqual(preflight.status_code, 200)
        self.assertIn("x-api-key", preflight.headers["access-control-allow-headers"].lower())
        resposta = self.http.post(
            "/v1/ia-generativa/texto", json=PEDIDO, headers={**CABECALHO, "Origin": "http://localhost:5173"}
        )
        self.assertEqual(resposta.headers["access-control-allow-origin"], "http://localhost:5173")

    def test_swagger_exige_chave_em_todas_as_rotas_v1(self):
        esquema = self.http.get("/openapi.json").json()
        for rota, operacoes in esquema["paths"].items():
            for metodo, operacao in operacoes.items():
                protegida = any("APIKeyHeader" in requisito for requisito in operacao.get("security", []))
                self.assertEqual(protegida, rota.startswith("/v1/"), f"{metodo.upper()} {rota}")
        self.assertEqual(self.http.get("/docs").status_code, 200)

    def test_status_reflete_ollama_e_voz(self):
        corpo = self.http.get("/v1/ia-generativa/status", headers=CABECALHO).json()
        self.assertTrue(corpo["texto"])
        self.assertFalse(corpo["voz"])
        self.assertIn("PIPER_VOZ", corpo["detalhe"]["voz"])


class TestJogoPelaAPI(unittest.TestCase):
    """O jogo do protótipo jogando de verdade através da API (evidência: o jogo não chama o Ollama direto)."""

    def setUp(self):
        OllamaSimulado.modo = "ok"
        OllamaSimulado.atraso = 0.0
        OllamaSimulado.recebidos = []
        self.srv = Servidores()
        self.pasta = tempfile.TemporaryDirectory()
        self.saida = []
        self.cliente = ClienteComFallback(
            ClienteAPI(self.srv.url, api_key=CHAVE), ClienteFalso(), avisar=self.saida.append
        )
        mundo = carregar_mundo(PROTOTIPO / "dados" / "mundo.json")
        self.jogo = Jogo(
            self.cliente, mundo, Path(self.pasta.name) / "save.json", carregar=False, saida=self.saida.append
        )

    def tearDown(self):
        self.srv.encerrar()
        self.pasta.cleanup()

    def test_turno_completo_passa_pela_api(self):
        self.cliente.principal.verificar()
        self.jogo.processar("Solte esse homem ou eu arranco sua cabeça!")
        self.assertIn("\nTomás: Por favor, senhor!", self.saida)
        # Dois pedidos por turno: classificador (temperatura 0) e fala do NPC, ambos com o prompt real do jogo.
        classificacao, turno = OllamaSimulado.recebidos
        self.assertEqual(classificacao["options"], {"temperature": 0})
        self.assertIn("Classifique a intenção", classificacao["messages"][0]["content"])
        self.assertEqual(set(turno["format"]["properties"]), {"emocao", "fala", "memoria"})
        self.assertEqual(self.jogo.jogador.pecados["ira"], 6)
        self.assertIn("Fui ameaçado.", self.jogo.npcs["tomas"].memorias)
        self.assertEqual(self.cliente.modelo, "qwen2.5:7b via API")

    def test_ollama_cai_no_meio_e_o_jogo_segue_offline(self):
        self.jogo.processar("Solte esse homem!")
        self.srv.derrubar_ollama()
        self.jogo.processar("Calma, eu só quero ajudar")
        self.assertTrue(self.cliente.em_fallback)
        self.assertTrue(any("IA indisponível" in linha and "503" in linha for linha in self.saida))
        self.assertFalse(self.jogo.encerrado)
        self.assertEqual(self.cliente.modelo, "falso")

    def test_chave_errada_impede_o_jogo_de_abrir(self):
        with self.assertRaises(ErroLLM) as contexto:
            ClienteAPI(self.srv.url, api_key="errada").verificar()
        self.assertIn("OS7_API_KEY", str(contexto.exception))


PIPER_VOZ = os.environ.get("PIPER_VOZ")


def duracao_wav(dados):
    with wave.open(io.BytesIO(dados)) as arquivo:
        return arquivo.getnframes() / arquivo.getframerate(), arquivo.getnchannels(), arquivo.getsampwidth()


@unittest.skipUnless(
    PIPER_VOZ and Path(PIPER_VOZ).exists(), "defina PIPER_VOZ com o .onnx da voz para testar o Piper real"
)
class TestVozPiperReal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = Servidores(piper_voz=Path(PIPER_VOZ))
        cls.http = httpx.Client(base_url=cls.srv.url, timeout=60, headers=CABECALHO)

    @classmethod
    def tearDownClass(cls):
        cls.http.close()
        cls.srv.encerrar()

    def voz(self, texto, velocidade=1.0):
        resposta = self.http.post("/v1/ia-generativa/voz", json={"texto": texto, "velocidade": velocidade})
        self.assertEqual(resposta.status_code, 200, resposta.text)
        return resposta.content

    def test_wav_valido(self):
        segundos, canais, bytes_amostra = duracao_wav(self.voz("Cinzaforte, cidade tomada pela Ira."))
        self.assertEqual((canais, bytes_amostra), (1, 2))
        self.assertGreater(segundos, 1)

    def test_gestos_nao_sao_falados(self):
        sem, _, _ = duracao_wav(self.voz("Minha filha está doente."))
        com, _, _ = duracao_wav(self.voz("*recua, trêmulo, olhando para a multidão* Minha filha está doente."))
        self.assertAlmostEqual(com, sem, delta=0.15)

    def test_velocidade_muda_a_duracao(self):
        normal, _, _ = duracao_wav(self.voz("A Ira não é barata, inquisidor.", 1.0))
        rapida, _, _ = duracao_wav(self.voz("A Ira não é barata, inquisidor.", 2.0))
        self.assertLess(rapida, normal * 0.7)

    def test_chamadas_simultaneas(self):
        with ThreadPoolExecutor(4) as pool:
            audios = list(pool.map(lambda i: self.voz(f"Fala número {i} do teste."), range(4)))
        self.assertTrue(all(duracao_wav(a)[0] > 0.5 for a in audios))

    def test_texto_so_com_gesto_e_502(self):
        resposta = self.http.post("/v1/ia-generativa/voz", json={"texto": "*fica em silêncio*"})
        self.assertEqual(resposta.status_code, 502)


if __name__ == "__main__":
    unittest.main()
