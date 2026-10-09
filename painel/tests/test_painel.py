"""Painel clicado de verdade (Streamlit AppTest), com as respostas HTTP da API simuladas no requests."""

import json
import unittest
from pathlib import Path
from unittest import mock

import requests
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")
STATUS = {
    "texto": True,
    "voz": False,
    "modelo_texto": "qwen2.5:7b",
    "detalhe": {"texto": "ok", "voz": "PIPER_VOZ não configurado"},
}
CLASSE = {"conteudo": {"intencao": "ameaca", "intensidade": 2}, "modelo": "qwen2.5:7b", "latencia_ms": 900}
TURNO = {
    "conteudo": {"emocao": "medo", "fala": "Por favor, senhor!", "memoria": "Fui ameaçado."},
    "modelo": "qwen2.5:7b",
    "latencia_ms": 2100,
}


def resposta(codigo, corpo=None, binario=None):
    r = requests.Response()
    r.status_code = codigo
    r._content = binario if binario is not None else json.dumps(corpo).encode()
    return r


class FalsaAPI:
    """Substitui requests.Session.request: responde por rota e guarda cada chamada (com headers)."""

    def __init__(self, codigo_texto=200):
        self.codigo_texto = codigo_texto
        self.chamadas = []

    def __call__(self, sessao, metodo, url, **kwargs):
        self.chamadas.append((metodo, url, dict(sessao.headers), kwargs.get("json")))
        if url.endswith("/health"):
            return resposta(200, {"status": "ok"})
        if url.endswith("/status"):
            return resposta(200, STATUS)
        if url.endswith("/voz"):
            return resposta(200, binario=b"RIFF\x00\x00\x00\x00WAVE")
        if self.codigo_texto != 200:
            return resposta(self.codigo_texto, {"detail": "Ollama não está acessível"})
        schema = kwargs["json"]["schema_resposta"]
        return resposta(200, TURNO if "fala" in schema["properties"] else CLASSE)


class TestPainel(unittest.TestCase):
    def abrir(self, api, chave="minha-chave"):
        self.patch = mock.patch.object(requests.Session, "request", autospec=True, side_effect=api)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        at = AppTest.from_file(APP, default_timeout=30)
        at.run()
        at.sidebar.text_input[0].set_value("http://api-teste:8000")
        at.sidebar.text_input[1].set_value(chave)
        at.run()
        return at

    def clicar(self, at, rotulo):
        next(b for b in at.button if b.label == rotulo).click()
        at.run()
        self.assertEqual([e.value for e in at.exception], [])

    def test_carrega_sem_erro(self):
        at = self.abrir(FalsaAPI())
        self.assertEqual(len(at.tabs), 4)

    def test_status(self):
        at = self.abrir(FalsaAPI())
        self.clicar(at, "Verificar status")
        self.assertEqual([s.value for s in at.sidebar.success], ["Texto: ok"])
        self.assertEqual([w.value for w in at.sidebar.warning], ["Voz: PIPER_VOZ não configurado"])

    def test_fala_de_npc_faz_o_turno_do_jogo_pela_api(self):
        api = FalsaAPI()
        at = self.abrir(api)
        self.clicar(at, "Enviar")
        self.assertIn("**Tomás** (medo): Por favor, senhor!", [m.value for m in at.markdown])
        self.assertEqual(at.metric[0].value, "ameaca (2)")
        self.assertEqual(at.metric[1].value, "3000 ms")
        self.assertEqual(len(at.get("audio")), 1)
        rotas = [url.rsplit("/", 1)[-1] for _, url, _, _ in api.chamadas]
        self.assertEqual(rotas, ["texto", "texto", "voz"])  # classificação, fala do NPC, voz
        self.assertTrue(all(h["X-API-Key"] == "minha-chave" for _, _, h, _ in api.chamadas))
        self.assertTrue(all(url.startswith("http://api-teste:8000/v1/") for _, url, _, _ in api.chamadas))

    def test_chave_recusada(self):
        at = self.abrir(FalsaAPI(codigo_texto=401))
        self.clicar(at, "Classificar")
        self.assertIn("Chave recusada (401)", at.error[0].value)

    def test_ia_fora_do_ar(self):
        at = self.abrir(FalsaAPI(codigo_texto=503))
        self.clicar(at, "Enviar")
        self.assertIn("IA indisponível (503)", at.warning[0].value)

    def test_api_desligada(self):
        def recusar(*args, **kwargs):
            raise requests.ConnectionError("recusado")

        at = self.abrir(recusar)
        self.clicar(at, "Classificar")
        self.assertIn("API fora do ar", at.error[0].value)

    def test_schema_invalido_no_texto_livre_nao_chama_a_api(self):
        api = FalsaAPI()
        at = self.abrir(api)
        at.text_area[-1].set_value("{isso não é json")
        at.run()
        self.clicar(at, "Gerar")
        self.assertIn("JSON Schema inválido", at.error[0].value)
        self.assertEqual(api.chamadas, [])


if __name__ == "__main__":
    unittest.main()
