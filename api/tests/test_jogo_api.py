"""Rotas /v1/jogo: partida completa pela API, com a IA falsa (sem Ollama)."""

import json
import tempfile
import unittest
from pathlib import Path

from config import Config
from fastapi.testclient import TestClient
from main import criar_app
from providers.ia_provider import ErroProvedor

CHAVE = "chave-jogo"
CAB = {"X-API-Key": CHAVE}


class ProviderRoteiro:
    """Responde como o Ollama responderia a cada tipo de pedido do jogo (classificação, fala, manifestação)."""

    def __init__(self, config):
        self.config = config
        self.fora = False
        self.pedidos = []

    def gerar_texto(self, mensagens, schema=None, temperatura=None):
        self.pedidos.append(list(schema["properties"]))
        if self.fora:
            raise ErroProvedor("Ollama fora", indisponivel=True)
        campos = set(schema["properties"])
        if campos == {"intencao", "intensidade"}:
            texto = mensagens[-1]["content"].lower()
            conteudo = {"intencao": "violencia" if "mato" in texto else "compaixao", "intensidade": 3}
        elif campos == {"fala"}:
            conteudo = {"fala": "Deixe  o  sangue  ferver."}
        else:
            conteudo = {"emocao": "medo", "fala": "Por favor, senhor!", "memoria": "Ele me ameaçou."}
        return {"conteudo": conteudo, "modelo": "qwen2.5:7b", "latencia_ms": 1}

    def status_texto(self):
        return True, "ok"

    def status_voz(self):
        return True, "ok"


class TestJogoAPI(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.config = Config(api_key=CHAVE, pasta_partidas=Path(self.pasta.name))
        self.provider = ProviderRoteiro(self.config)
        self.http = TestClient(criar_app(self.config, self.provider))

    def tearDown(self):
        self.pasta.cleanup()

    def nova(self):
        resposta = self.http.post("/v1/jogo/partidas", headers=CAB)
        self.assertEqual(resposta.status_code, 201)
        return resposta.json()

    def cmd(self, id_partida, entrada, codigo=200):
        resposta = self.http.post(f"/v1/jogo/partidas/{id_partida}/comandos", json={"entrada": entrada}, headers=CAB)
        self.assertEqual(resposta.status_code, codigo, resposta.text)
        return resposta.json()

    def test_exige_chave(self):
        self.assertEqual(self.http.post("/v1/jogo/partidas").status_code, 401)
        self.assertEqual(self.http.get("/v1/jogo/partidas/" + "a" * 32).status_code, 401)

    def test_nova_partida_traz_introducao_e_estado(self):
        partida = self.nova()
        self.assertRegex(partida["id"], r"^[0-9a-f]{32}$")
        self.assertTrue(any("Praça do Pelourinho" in linha for linha in partida["linhas"]))
        self.assertEqual(partida["estado"]["atual"], "tomas")
        self.assertEqual(len(partida["estado"]["npcs"]), 3)
        self.assertFalse(partida["offline"])

    def test_fala_passa_pela_ia_e_volta_estruturada(self):
        partida = self.nova()
        r = self.cmd(partida["id"], "Solta ele ou eu te mato")
        self.assertEqual(self.provider.pedidos[:2], [["intencao", "intensidade"], ["emocao", "fala", "memoria"]])
        self.assertEqual(r["ultimo"]["fala"], {"npc": "tomas", "texto": "Por favor, senhor!", "emocao": "medo"})
        self.assertEqual(r["ultimo"]["leitura"]["intencao"], "violencia")
        self.assertEqual(r["ultimo"]["pecados"], {"ira": 18})
        self.assertEqual(r["ultimo"]["memoria"]["texto"], "Ele me ameaçou.")
        self.assertEqual(r["estado"]["jogador"]["pecados"]["ira"], 18)

    def test_partida_completa_ate_o_final_de_pecado(self):
        pid = self.nova()["id"]
        self.cmd(pid, "/falar brenna")
        self.cmd(pid, "/atacar")
        r = self.cmd(pid, "/falar tomas Eu te mato também")  # 20 + 18 = 38
        self.assertNotIn("manifestacao", r["ultimo"])
        r = self.cmd(pid, "/roubar")
        r = self.cmd(pid, "Eu te mato")  # passa de 40
        self.assertEqual(r["ultimo"]["manifestacao"]["nome"], "A Fera")
        self.assertEqual(r["ultimo"]["manifestacao"]["fala"], "Deixe o sangue ferver.")
        r = self.cmd(pid, "/veredito condenar")
        self.assertEqual(r["ultimo"]["final"]["titulo"], "Marcado pela Ira")
        self.assertTrue(r["estado"]["encerrado"])
        self.cmd(pid, "Olá?", codigo=409)

    def test_final_redencao(self):
        pid = self.nova()["id"]
        self.cmd(pid, "Calma, eu vou te ajudar")
        r = self.cmd(pid, "/veredito absolver")
        self.assertEqual(r["ultimo"]["final"]["titulo"], "Redenção")

    def test_ia_cai_e_partida_segue_offline(self):
        pid = self.nova()["id"]
        self.provider.fora = True
        r = self.cmd(pid, "Calma, eu vou te ajudar")
        self.assertTrue(r["offline"])
        self.assertTrue(any("IA indisponível" in linha for linha in r["linhas"]))
        self.assertIn("fala", r["ultimo"])

    def test_continuar_depois_de_reiniciar_a_api(self):
        pid = self.nova()["id"]
        self.cmd(pid, "/doar 10")
        reiniciada = TestClient(criar_app(self.config, ProviderRoteiro(self.config)))
        r = reiniciada.get(f"/v1/jogo/partidas/{pid}", headers=CAB)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["estado"]["jogador"]["ouro"], 20)

    def test_id_invalido_ou_inexistente_e_404(self):
        for id_ruim in ("..%2F..%2Fetc%2Fpasswd", "nao-existe", "b" * 32):
            self.assertEqual(self.http.get(f"/v1/jogo/partidas/{id_ruim}", headers=CAB).status_code, 404)

    def test_entrada_vazia_ou_gigante_e_422(self):
        pid = self.nova()["id"]
        self.cmd(pid, "", codigo=422)
        self.cmd(pid, "a" * 501, codigo=422)

    def test_log_de_cada_chamada_a_ia(self):
        pid = self.nova()["id"]
        self.cmd(pid, "Calma, eu vou te ajudar")
        registros = [json.loads(linha) for linha in (Path(self.pasta.name) / f"{pid}.jsonl").read_text().splitlines()]
        self.assertEqual(len(registros), 2)
        self.assertEqual(registros[0]["modelo"], "qwen2.5:7b")


if __name__ == "__main__":
    unittest.main()
