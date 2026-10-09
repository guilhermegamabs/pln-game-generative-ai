"""ClienteAPI contra um servidor HTTP local que imita a API (api/), e o fallback para o modo offline."""

import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from llm import ClienteAPI, ClienteComFallback, ClienteFalso, ErroLLM

SCHEMA = {"type": "object", "properties": {"intencao": {"type": "string"}}}


class ApiFalsa(BaseHTTPRequestHandler):
    recebidos = []
    codigo_texto = 200

    def _responder(self, codigo, corpo):
        dados = json.dumps(corpo).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(dados)

    def do_GET(self):
        if self.headers.get("X-API-Key") != "certa":
            return self._responder(401, {"detail": "API Key ausente ou inválida."})
        self._responder(200, {"texto": True, "voz": False, "modelo_texto": "qwen2.5:7b", "detalhe": {"texto": "ok", "voz": "-"}})

    def do_POST(self):
        corpo = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        ApiFalsa.recebidos.append((self.path, self.headers, corpo))  # headers: busca sem caixa
        if ApiFalsa.codigo_texto != 200:
            return self._responder(ApiFalsa.codigo_texto, {"detail": "Ollama não está acessível"})
        self._responder(200, {"conteudo": {"intencao": "ameaca"}, "modelo": "qwen2.5:7b", "latencia_ms": 5})

    def log_message(self, *args):
        pass


class TestClienteAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.servidor = HTTPServer(("127.0.0.1", 0), ApiFalsa)
        cls.url = f"http://127.0.0.1:{cls.servidor.server_port}"
        threading.Thread(target=cls.servidor.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.servidor.shutdown()

    def setUp(self):
        ApiFalsa.recebidos = []
        ApiFalsa.codigo_texto = 200

    def test_envia_para_a_rota_da_api_com_a_chave(self):
        cliente = ClienteAPI(self.url, api_key="certa")
        resposta = cliente.gerar_json([{"role": "user", "content": "Solte esse homem!"}], SCHEMA, 0)
        self.assertEqual(resposta, {"intencao": "ameaca"})
        rota, cabecalhos, corpo = ApiFalsa.recebidos[0]
        self.assertEqual(rota, "/v1/ia-generativa/texto")
        self.assertEqual(cabecalhos["X-API-Key"], "certa")
        self.assertEqual(corpo["schema_resposta"], SCHEMA)
        self.assertEqual(corpo["temperatura"], 0)
        self.assertEqual(cliente.modelo, "qwen2.5:7b via API")

    def test_chave_errada_explica_o_que_fazer(self):
        with self.assertRaises(ErroLLM) as contexto:
            ClienteAPI(self.url, api_key="errada").verificar()
        self.assertIn("OS7_API_KEY", str(contexto.exception))

    def test_503_da_api_e_indisponivel(self):
        ApiFalsa.codigo_texto = 503
        with self.assertRaises(ErroLLM) as contexto:
            ClienteAPI(self.url, api_key="certa").gerar_json([{"role": "user", "content": "oi"}], SCHEMA)
        self.assertTrue(contexto.exception.indisponivel)

    def test_502_da_api_nao_e_indisponivel(self):
        ApiFalsa.codigo_texto = 502
        with self.assertRaises(ErroLLM) as contexto:
            ClienteAPI(self.url, api_key="certa").gerar_json([{"role": "user", "content": "oi"}], SCHEMA)
        self.assertFalse(contexto.exception.indisponivel)

    def test_api_desligada_e_indisponivel(self):
        with self.assertRaises(ErroLLM) as contexto:
            ClienteAPI("http://127.0.0.1:1", api_key="certa").verificar()
        self.assertTrue(contexto.exception.indisponivel)


class Quebrado:
    modelo = "quebrado"

    def __init__(self, indisponivel):
        self.indisponivel = indisponivel
        self.chamadas = 0

    def gerar_json(self, mensagens, schema, temperatura=None):
        self.chamadas += 1
        raise ErroLLM("falhou", indisponivel=self.indisponivel)


class TestFallback(unittest.TestCase):
    def test_ia_fora_do_ar_troca_para_offline_uma_vez(self):
        avisos = []
        principal = Quebrado(indisponivel=True)
        cliente = ClienteComFallback(principal, ClienteFalso(), avisar=avisos.append)
        mensagens = [{"role": "user", "content": "Eu vou te matar"}]
        self.assertEqual(cliente.gerar_json(mensagens, SCHEMA)["intencao"], "violencia")
        cliente.gerar_json(mensagens, SCHEMA)
        self.assertEqual(principal.chamadas, 1)  # Depois de cair, não fica batendo na API a cada turno.
        self.assertEqual(len(avisos), 1)
        self.assertEqual(cliente.modelo, "falso")

    def test_resposta_ruim_nao_ativa_fallback(self):
        cliente = ClienteComFallback(Quebrado(indisponivel=False), ClienteFalso(), avisar=lambda _: None)
        with self.assertRaises(ErroLLM):
            cliente.gerar_json([{"role": "user", "content": "oi"}], SCHEMA)
        self.assertFalse(cliente.em_fallback)


if __name__ == "__main__":
    unittest.main()
