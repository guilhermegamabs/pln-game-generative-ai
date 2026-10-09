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

    def test_espacos_duplos_do_modelo_sao_limpos(self):
        # Saída real do qwen2.5:7b na fala da Fera: espaço duplo entre todas as palavras.
        fala = "Tu  ousou  te  atrever  contra  mim?\n  A  escolha  é  tua."
        resposta = {"intencao": "violencia", "intensidade": 3, "emocao": "raiva", "fala": fala, "memoria": "Ele  me  ameaçou. "}
        jogo = self.novo_jogo(ClienteFixo(resposta))
        jogo.jogador.pecados["ira"] = 39
        jogo.processar("Eu vou te matar")
        self.assertIn("\nTomás: Tu ousou te atrever contra mim? A escolha é tua.", self.linhas)
        self.assertTrue(any(linha.endswith("A Fera: Tu ousou te atrever contra mim? A escolha é tua.") for linha in self.linhas))
        self.assertEqual(jogo.npcs["tomas"].memorias, ["Ele me ameaçou."])
        self.assertEqual(jogo.npcs["tomas"].historico[-1]["content"], "Tu ousou te atrever contra mim? A escolha é tua.")

    def test_veredito_sem_pecado_alto_e_redencao(self):
        self.jogo.processar("/veredito absolver")
        self.assertTrue(self.jogo.encerrado)
        self.assertEqual(self.jogo.jogador.final, "Redenção")
        self.assertEqual(self.jogo.ultimo["final"]["titulo"], "Redenção")
        self.assertIn("declara Tomás livre", self.jogo.ultimo["final"]["texto"])

    def test_veredito_com_pecado_manifestado_e_final_de_pecado(self):
        self.matar("brenna")
        self.matar("odran")
        self.jogo.processar("/falar tomas")
        self.jogo.processar("/veredito condenar")
        self.assertEqual(self.jogo.jogador.final, "Marcado pela Ira")
        self.assertIn("A Fera fala junto", self.jogo.ultimo["final"]["texto"])

    def test_veredito_exige_decisao_e_nao_encerra_sem_ela(self):
        self.jogo.processar("/veredito talvez")
        self.assertFalse(self.jogo.encerrado)
        self.assertIn("Uso: /veredito", self.linhas[-1])

    def test_veredito_com_acusado_morto_aceita_sem_decisao(self):
        self.jogo.processar("/atacar")
        self.jogo.processar("/veredito")
        self.assertTrue(self.jogo.encerrado)
        self.assertIn("não resta ninguém a julgar", self.jogo.ultimo["final"]["texto"])

    def test_partida_encerrada_nao_aceita_mais_comandos(self):
        self.jogo.processar("/veredito absolver")
        ouro = self.jogo.jogador.ouro
        self.jogo.processar("/doar 5")
        self.assertEqual(self.jogo.jogador.ouro, ouro)

    def test_resultado_estruturado_do_turno(self):
        self.jogo.processar("Solta ele ou eu te mato")
        ultimo = self.jogo.ultimo
        self.assertEqual(ultimo["fala"]["npc"], "tomas")
        self.assertEqual(ultimo["leitura"]["intencao"], "violencia")
        self.assertEqual(ultimo["pecados"], {"ira": 12})
        self.assertIn("memoria", ultimo)
        self.jogo.processar("/status")
        self.assertEqual(self.jogo.ultimo, {})  # cada comando começa limpo

    def test_resultado_registra_manifestacao_e_consumido(self):
        self.jogo.jogador.pecados["ira"] = 35
        self.jogo.processar("/atacar")  # 35 -> 55: cruza o limiar de 40
        self.assertEqual(self.jogo.ultimo["manifestacao"]["nome"], "A Fera")
        self.assertNotIn("final", self.jogo.ultimo)
        self.jogo.processar("/falar brenna")
        self.jogo.jogador.pecados["ira"] = 80
        self.matar("brenna")  # atacar +5 e matar +15: 80 -> 100
        self.assertNotIn("manifestacao", self.jogo.ultimo)  # A Fera já tinha despertado
        self.assertEqual(self.jogo.ultimo["final"]["titulo"], "Consumido pela Ira")

    def test_estado_para_a_interface(self):
        self.jogo.processar("/atacar")
        estado = self.jogo.estado()
        self.assertEqual(estado["atual"], "tomas")
        self.assertEqual(estado["jogador"]["pecados"]["ira"], 20)
        tomas = next(n for n in estado["npcs"] if n["id"] == "tomas")
        self.assertFalse(tomas["vivo"])
        self.assertEqual(estado["manifestacoes"]["ira"]["nome"], "A Fera")
        self.assertEqual(estado["limiares"], {"manifestacao": 40, "consumido": 100})

    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.save = Path(self.pasta.name) / "partida.json"
        self.linhas = []
        self.jogo = self.novo_jogo(ClienteFalso())

    def tearDown(self):
        self.pasta.cleanup()

    def matar(self, npc):
        """Combate até o NPC cair (com vida infinita, para o teste não depender do balanceamento de dano)."""
        self.jogo.processar(f"/falar {npc}")
        self.jogo.jogador.vida_max = self.jogo.jogador.vida = 10_000
        self.jogo.processar("/atacar")
        while self.jogo.jogador.combate and not self.jogo.encerrado:
            self.jogo.processar("/atacar")

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
        self.matar("brenna")
        self.matar("odran")
        self.assertEqual(self.jogo.jogador.manifestacoes, ["ira"])
        self.assertTrue(any("A Fera desperta" in linha for linha in self.linhas))

    def test_consumido_encerra_o_jogo(self):
        self.jogo.jogador.pecados["ira"] = 95
        self.jogo.jogador.manifestacoes.append("ira")
        continuar = self.jogo.processar("/atacar")
        self.assertFalse(continuar)
        self.assertEqual(self.jogo.jogador.final, "Consumido pela Ira")

    # ---------- combate por turnos (M5) ----------

    def test_combate_em_turnos_com_revide(self):
        self.jogo.processar("/falar brenna")
        self.jogo.processar("/atacar")
        brenna = self.jogo.npcs["brenna"]
        self.assertEqual(brenna.vida, 75)  # 100 - 25
        self.assertEqual(self.jogo.jogador.vida, 70)  # revide de 30
        self.assertEqual(self.jogo.jogador.combate, {"npc": "brenna", "brecha": False})
        self.assertEqual(self.jogo.jogador.pecados["ira"], 5)  # só atacar; matar vem quando ela cair
        self.assertEqual(self.jogo.ultimo["combate"]["resultado"], "continua")
        for _ in range(3):
            self.jogo.processar("/atacar")
        self.assertFalse(brenna.vivo)
        self.assertIsNone(self.jogo.jogador.combate)
        self.assertEqual(self.jogo.jogador.pecados["ira"], 20)
        self.assertEqual(self.jogo.jogador.vida, 100 - 3 * 30)  # o golpe que derruba não sofre revide
        self.assertEqual(self.jogo.ultimo["combate"]["resultado"], "venceu")
        self.assertIn("Viu o inquisitor matar Capitã Brenna na praça.", self.jogo.npcs["odran"].memorias)

    def test_defender_reduz_dano_e_dobra_o_proximo_golpe(self):
        self.jogo.processar("/falar brenna")
        self.jogo.processar("/atacar")
        self.jogo.processar("/defender")
        self.assertEqual(self.jogo.jogador.vida, 70 - 8)  # 30 * 1/4, arredondado
        self.jogo.processar("/atacar")
        self.assertEqual(self.jogo.ultimo["combate"]["dano_causado"], 50)
        self.assertEqual(self.jogo.npcs["brenna"].vida, 25)

    def test_em_combate_nao_da_para_conversar_nem_julgar(self):
        self.jogo.processar("/falar odran")
        self.jogo.processar("/atacar")
        for entrada in ("Calma, vamos conversar", "/falar tomas", "/veredito absolver", "/roubar"):
            self.jogo.processar(entrada)
            self.assertIn("Você está em combate com Odran", self.linhas[-1])
        self.assertFalse(self.jogo.encerrado)
        self.assertEqual(self.jogo.atual, "odran")

    def test_fugir_encerra_o_combate_e_o_npc_lembra(self):
        self.jogo.processar("/falar brenna")
        self.jogo.processar("/atacar")
        self.jogo.processar("/fugir")
        brenna = self.jogo.npcs["brenna"]
        self.assertIsNone(self.jogo.jogador.combate)
        self.assertTrue(brenna.vivo)
        self.assertEqual(brenna.vida, 75)  # o ferimento continua
        self.assertIn("O inquisitor me atacou e fugiu da luta.", brenna.memorias)

    def test_poder_demoniaco_exige_manifestacao_e_custa_pecado(self):
        self.jogo.processar("/falar brenna")
        self.jogo.processar("/atacar")
        self.jogo.processar("/poder")
        self.assertIn("Nenhum pecado despertou", self.linhas[-1])
        self.jogo.jogador.pecados["ira"] = 50
        self.jogo.jogador.manifestacoes.append("ira")
        self.jogo.processar("/poder")
        self.assertEqual(self.jogo.jogador.pecados["ira"], 58)
        self.assertEqual(self.jogo.npcs["brenna"].vida, 30)  # 75 - 45
        self.assertEqual(self.jogo.ultimo["combate"]["poder"], "ira")

    def test_morrer_em_combate_e_derrota(self):
        self.jogo.processar("/falar brenna")
        self.jogo.jogador.vida = 20
        self.jogo.processar("/atacar")  # revide de 30
        self.assertTrue(self.jogo.encerrado)
        self.assertEqual(self.jogo.jogador.final, "Morto em Cinzaforte")
        self.assertEqual(self.jogo.ultimo["combate"]["resultado"], "derrota")

    def test_tomas_amarrado_nao_revida(self):
        self.jogo.processar("/atacar")
        self.assertFalse(self.jogo.npcs["tomas"].vivo)  # 20 de vida: cai no primeiro golpe
        self.assertEqual(self.jogo.jogador.vida, 100)

    def test_itens_do_inventario(self):
        self.jogo.processar("/item pocao")
        self.assertIn("vida já está cheia", self.linhas[-1])
        self.jogo.jogador.vida = 50
        self.jogo.processar("/item pocao")
        self.assertEqual(self.jogo.jogador.vida, 85)
        self.assertEqual(self.jogo.jogador.inventario["pocao"], 1)
        self.jogo.jogador.pecados["avareza"] = 30
        self.jogo.processar("/item agua benta")
        self.assertEqual(self.jogo.jogador.pecados["avareza"], 20)
        self.assertEqual(self.jogo.ultimo["pecados"], {"avareza": -10})
        self.jogo.processar("/item agua")
        self.assertIn("Você não tem", self.linhas[-1])

    def test_usar_item_em_combate_gasta_o_turno(self):
        self.jogo.processar("/falar brenna")
        self.jogo.processar("/atacar")
        self.jogo.processar("/item pocao")
        self.assertEqual(self.jogo.jogador.vida, 100 - 30)  # 70 + 35 limitado a 100, depois o revide
        self.assertEqual(self.jogo.ultimo["combate"]["acao"], "item")

    def test_save_preserva_combate_em_andamento(self):
        self.jogo.processar("/falar brenna")
        self.jogo.processar("/atacar")
        carregado = self.novo_jogo(ClienteFalso(), carregar=True)
        self.assertEqual(carregado.jogador.combate["npc"], "brenna")
        self.assertEqual(carregado.npcs["brenna"].vida, 75)
        self.assertEqual(carregado.jogador.vida, 70)

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
