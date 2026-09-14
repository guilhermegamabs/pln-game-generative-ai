import json
import tempfile
import unittest
from pathlib import Path

from estado import carregar_mundo
from jogo import Jogo
from llm import ClienteFalso, ClienteRegistrado, ErroLLM

MUNDO = Path(__file__).resolve().parent.parent / "dados" / "mundo.json"


class ClienteQuebrado:
    modelo = "quebrado"

    def gerar_json(self, mensagens, schema, temperatura=None):
        raise ErroLLM("sem conexão")


class ClienteFixo:
    modelo = "fixo"

    def __init__(self, resposta):
        self.resposta = resposta
        self.chamadas = []

    @property
    def mensagens(self):
        return self.chamadas[-1][0]

    def gerar_json(self, mensagens, schema, temperatura=None):
        self.chamadas.append((mensagens, schema, temperatura))
        return self.resposta


class TestJogo(unittest.TestCase):
    def test_classifica_antes_e_npc_recebe_a_intencao(self):
        resposta = {"intencao": "ganancia", "intensidade": 2, "emocao": "medo", "fala": "Não!", "memoria": ""}
        cliente = ClienteFixo(resposta)
        jogo = self.novo_jogo(cliente)
        jogo.processar("Passa todo o ouro que você tem.")
        (msg_classe, schema_classe, temp_classe), (msg_npc, schema_npc, _) = cliente.chamadas
        self.assertEqual(temp_classe, 0)
        self.assertIn("intencao", schema_classe["properties"])
        self.assertNotIn("intencao", schema_npc["properties"])
        self.assertIn("foi ganancia (intensidade 2 de 3)", msg_npc[0]["content"])
        self.assertEqual(jogo.jogador.pecados["avareza"], 10)

    def test_falar_com_nome_sem_acento_e_fala_na_mesma_linha(self):
        resposta = {"intencao": "compaixao", "intensidade": 2, "emocao": "alívio", "fala": "Obrigado!", "memoria": "x"}
        cliente = ClienteFixo(resposta)
        jogo = self.novo_jogo(cliente)
        jogo.processar("/falar brenna")
        jogo.processar("/falar Tomas Soltem ele")
        self.assertEqual(jogo.atual, "tomas")
        self.assertIn('Frase: "Soltem ele"', cliente.chamadas[0][0][-1]["content"])
        self.assertEqual(cliente.mensagens[-1]["content"], "O inquisitor diz: Soltem ele")
        jogo.processar("/falar capitã brenna")
        self.assertEqual(jogo.atual, "brenna")

    def test_memoria_repetida_nao_duplica(self):
        resposta = {"intencao": "neutro", "intensidade": 1, "emocao": "x", "fala": "Hm.", "memoria": "A capitã hesitou."}
        jogo = self.novo_jogo(ClienteFixo(resposta))
        jogo.processar("oi")
        jogo.processar("oi de novo")
        self.assertEqual(jogo.npcs["tomas"].memorias, ["A capitã hesitou."])

    def test_segredo_so_entra_no_prompt_com_confianca(self):
        resposta = {"intencao": "neutro", "intensidade": 1,
                    "emocao": "calmo", "fala": "Hm.", "memoria": ""}
        cliente = ClienteFixo(resposta)
        jogo = self.novo_jogo(cliente)
        segredo = jogo.npcs["tomas"].segredo
        jogo.processar("oi")
        self.assertNotIn(segredo, cliente.mensagens[0]["content"])
        jogo.npcs["tomas"].relacao = 40
        jogo.processar("oi")
        self.assertIn(segredo, cliente.mensagens[0]["content"])

    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.save = Path(self.pasta.name) / "partida.json"
        self.linhas = []
        self.jogo = self.novo_jogo(ClienteFalso())

    def tearDown(self):
        self.pasta.cleanup()

    def novo_jogo(self, cliente, carregar=False):
        return Jogo(cliente, carregar_mundo(MUNDO), self.save, carregar=carregar, saida=self.linhas.append)

    def test_fala_violenta_aumenta_ira_e_gera_memoria(self):
        self.jogo.processar("Solta ele ou eu te mato")
        self.assertEqual(self.jogo.jogador.pecados["ira"], 12)
        tomas = self.jogo.npcs["tomas"]
        self.assertLess(tomas.relacao, 0)
        self.assertEqual(len(tomas.memorias), 1)
        self.assertEqual(len(tomas.historico), 2)

    def test_atacar_mata_e_testemunhas_lembram(self):
        self.jogo.processar("/atacar")
        self.assertFalse(self.jogo.npcs["tomas"].vivo)
        brenna = self.jogo.npcs["brenna"]
        odran = self.jogo.npcs["odran"]
        self.assertGreater(brenna.relacao, 0)  # Brenna é da Ira: aprova a violência
        self.assertLess(odran.relacao, 0)
        self.assertIn("matar Tomás", odran.memorias[0])
        self.jogo.processar("oi")
        self.assertIn("está morto", self.linhas[-1])

    def test_manifestacao_desperta_ao_cruzar_40(self):
        self.jogo.processar("/falar brenna")
        self.jogo.processar("/atacar")
        self.jogo.processar("/falar odran")
        self.jogo.processar("/atacar")
        self.assertEqual(self.jogo.jogador.manifestacoes, ["ira"])
        self.assertTrue(any("A Fera desperta" in linha for linha in self.linhas))

    def test_consumido_encerra_o_jogo(self):
        self.jogo.jogador.pecados["ira"] = 95
        self.jogo.jogador.manifestacoes.append("ira")
        continuar = self.jogo.processar("/atacar")
        self.assertFalse(continuar)
        self.assertEqual(self.jogo.jogador.final, "Consumido pela Ira")

    def test_save_e_load_preservam_estado(self):
        self.jogo.processar("/roubar")
        carregado = self.novo_jogo(ClienteFalso(), carregar=True)
        self.assertTrue(carregado.carregado)
        self.assertEqual(carregado.jogador.pecados["avareza"], 15)
        self.assertEqual(carregado.npcs["tomas"].ouro, 0)

    def test_erro_da_ia_nao_derruba_o_jogo(self):
        jogo = self.novo_jogo(ClienteQuebrado())
        self.assertTrue(jogo.processar("olá"))
        self.assertIn("[erro da IA] sem conexão", self.linhas[-1])
        self.assertEqual(jogo.npcs["tomas"].historico, [])

    def test_registro_grava_prompt_e_resposta(self):
        log = Path(self.pasta.name) / "log.jsonl"
        jogo = self.novo_jogo(ClienteRegistrado(ClienteFalso(), log))
        jogo.processar("Eu posso te ajudar")
        classificacao, turno = (json.loads(linha) for linha in log.read_text(encoding="utf-8").splitlines())
        self.assertEqual(classificacao["resposta"]["intencao"], "compaixao")
        self.assertIn("Tomás", turno["mensagens"][0]["content"])


if __name__ == "__main__":
    unittest.main()
