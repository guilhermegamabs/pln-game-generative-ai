"""Testes da API sem Ollama nem Piper: o provider é trocado por um falso, e o Ollama por respostas simuladas."""

import json
import unittest
from unittest import mock

import httpx
from fastapi.testclient import TestClient

from config import Config
from main import criar_app
from providers.ia_provider import ErroProvedor, ProviderIA

CHAVE = "chave-de-teste"
CABECALHO = {"X-API-Key": CHAVE}
PEDIDO_TEXTO = {"mensagens": [{"role": "user", "content": "Solte esse homem!"}], "temperatura": 0}


class ProviderFalso:
    def __init__(self, config, erro=None):
        self.config = config
        self.erro = erro
        self.chamadas = []

    def gerar_texto(self, mensagens, schema=None, temperatura=None):
        self.chamadas.append((mensagens, schema, temperatura))
        if self.erro:
            raise self.erro
        return {"conteudo": {"intencao": "ameaca", "intensidade": 2}, "modelo": "falso", "latencia_ms": 1}

    def sintetizar_voz(self, texto, velocidade=1.0):
        if self.erro:
            raise self.erro
        return b"RIFF....WAVE"

    def status_texto(self):
        return True, "ok"

    def status_voz(self):
        return False, "PIPER_VOZ não configurado"


def cliente(api_key=CHAVE, erro=None):
    config = Config(api_key=api_key)
    provider = ProviderFalso(config, erro)
    return TestClient(criar_app(config, provider)), provider


class TestAutenticacao(unittest.TestCase):
    def test_sem_chave_recusa(self):
        http, provider = cliente()
        resposta = http.post("/v1/ia-generativa/texto", json=PEDIDO_TEXTO)
        self.assertEqual(resposta.status_code, 401)
        self.assertEqual(provider.chamadas, [])

    def test_chave_errada_recusa(self):
        http, _ = cliente()
        resposta = http.post("/v1/ia-generativa/texto", json=PEDIDO_TEXTO, headers={"X-API-Key": "outra"})
        self.assertEqual(resposta.status_code, 401)

    def test_servidor_sem_chave_configurada_nao_fica_aberto(self):
        http, provider = cliente(api_key="")
        resposta = http.post("/v1/ia-generativa/texto", json=PEDIDO_TEXTO, headers={"X-API-Key": ""})
        self.assertEqual(resposta.status_code, 500)
        self.assertEqual(provider.chamadas, [])

    def test_health_e_docs_sao_publicos(self):
        http, _ = cliente()
        self.assertEqual(http.get("/health").status_code, 200)
        self.assertEqual(http.get("/docs").status_code, 200)
        esquema = http.get("/openapi.json").json()
        self.assertIn("X-API-Key", json.dumps(esquema["components"]["securitySchemes"]))


class TestRotas(unittest.TestCase):
    def test_texto_repassa_pedido_ao_provider(self):
        http, provider = cliente()
        schema = {"type": "object", "properties": {"intencao": {"type": "string"}}}
        resposta = http.post("/v1/ia-generativa/texto", json={**PEDIDO_TEXTO, "schema_resposta": schema}, headers=CABECALHO)
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()["conteudo"]["intencao"], "ameaca")
        mensagens, schema_recebido, temperatura = provider.chamadas[0]
        self.assertEqual(mensagens, [{"role": "user", "content": "Solte esse homem!"}])
        self.assertEqual(schema_recebido, schema)
        self.assertEqual(temperatura, 0)

    def test_texto_valida_entrada(self):
        http, _ = cliente()
        self.assertEqual(http.post("/v1/ia-generativa/texto", json={"mensagens": []}, headers=CABECALHO).status_code, 422)
        invalida = {"mensagens": [{"role": "hacker", "content": "x"}]}
        self.assertEqual(http.post("/v1/ia-generativa/texto", json=invalida, headers=CABECALHO).status_code, 422)

    def test_ia_indisponivel_vira_503(self):
        http, _ = cliente(erro=ErroProvedor("Ollama fora", indisponivel=True))
        resposta = http.post("/v1/ia-generativa/texto", json=PEDIDO_TEXTO, headers=CABECALHO)
        self.assertEqual(resposta.status_code, 503)
        self.assertEqual(resposta.json()["detail"], "Ollama fora")

    def test_resposta_invalida_da_ia_vira_502(self):
        http, _ = cliente(erro=ErroProvedor("JSON inválido"))
        resposta = http.post("/v1/ia-generativa/texto", json=PEDIDO_TEXTO, headers=CABECALHO)
        self.assertEqual(resposta.status_code, 502)

    def test_voz_devolve_wav(self):
        http, _ = cliente()
        resposta = http.post("/v1/ia-generativa/voz", json={"texto": "Cinzaforte arde."}, headers=CABECALHO)
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.headers["content-type"], "audio/wav")

    def test_status(self):
        http, _ = cliente()
        corpo = http.get("/v1/ia-generativa/status", headers=CABECALHO).json()
        self.assertTrue(corpo["texto"])
        self.assertFalse(corpo["voz"])

    def test_cors_libera_front_e_header_da_chave(self):
        http, _ = cliente()
        resposta = http.options(
            "/v1/ia-generativa/texto",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type,x-api-key",
            },
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.headers["access-control-allow-origin"], "http://localhost:5173")
        bloqueada = http.options(
            "/v1/ia-generativa/texto",
            headers={"Origin": "http://site-estranho.com", "Access-Control-Request-Method": "POST"},
        )
        self.assertNotIn("access-control-allow-origin", bloqueada.headers)


def resposta_ollama(conteudo, codigo=200):
    return httpx.Response(codigo, json={"message": {"content": conteudo}}, request=httpx.Request("POST", "http://x"))


class TestProviderOllama(unittest.TestCase):
    def setUp(self):
        self.provider = ProviderIA(Config(api_key=CHAVE, ollama_modelo="qwen2.5:7b"))

    def test_envia_schema_e_temperatura_e_decodifica_json(self):
        schema = {"type": "object"}
        with mock.patch("httpx.post", return_value=resposta_ollama('{"fala": "Quem é você?"}')) as post:
            resultado = self.provider.gerar_texto([{"role": "user", "content": "oi"}], schema, 0)
        corpo = post.call_args.kwargs["json"]
        self.assertEqual(corpo["format"], schema)
        self.assertEqual(corpo["options"], {"temperature": 0})
        self.assertEqual(corpo["model"], "qwen2.5:7b")
        self.assertEqual(resultado["conteudo"], {"fala": "Quem é você?"})

    def test_sem_schema_devolve_texto_livre(self):
        with mock.patch("httpx.post", return_value=resposta_ollama("Texto livre")) as post:
            resultado = self.provider.gerar_texto([{"role": "user", "content": "oi"}])
        self.assertNotIn("format", post.call_args.kwargs["json"])
        self.assertEqual(resultado["conteudo"], "Texto livre")

    def test_ollama_desligado_e_indisponivel(self):
        with mock.patch("httpx.post", side_effect=httpx.ConnectError("recusado")):
            with self.assertRaises(ErroProvedor) as contexto:
                self.provider.gerar_texto([{"role": "user", "content": "oi"}])
        self.assertTrue(contexto.exception.indisponivel)

    def test_modelo_nao_baixado_e_indisponivel(self):
        with mock.patch("httpx.post", return_value=resposta_ollama("", codigo=404)):
            with self.assertRaises(ErroProvedor) as contexto:
                self.provider.gerar_texto([{"role": "user", "content": "oi"}])
        self.assertTrue(contexto.exception.indisponivel)
        self.assertIn("ollama pull", str(contexto.exception))

    def test_json_quebrado_nao_e_indisponivel(self):
        with mock.patch("httpx.post", return_value=resposta_ollama("{quebrado")):
            with self.assertRaises(ErroProvedor) as contexto:
                self.provider.gerar_texto([{"role": "user", "content": "oi"}], {"type": "object"})
        self.assertFalse(contexto.exception.indisponivel)

    def test_voz_sem_configuracao_e_indisponivel(self):
        with self.assertRaises(ErroProvedor) as contexto:
            self.provider.sintetizar_voz("Olá")
        self.assertTrue(contexto.exception.indisponivel)

    def test_voz_so_com_gestos_e_rejeitada(self):
        with self.assertRaises(ErroProvedor) as contexto:
            self.provider.sintetizar_voz("*recua, trêmulo*")
        self.assertFalse(contexto.exception.indisponivel)


if __name__ == "__main__":
    unittest.main()
