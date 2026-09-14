import unittest

import corrupcao
from corrupcao import PECADOS


def zerados():
    return {p: 0 for p in PECADOS}


class TestCorrupcao(unittest.TestCase):
    def test_deltas_multiplicam_pela_intensidade(self):
        self.assertEqual(corrupcao.deltas_intencao("violencia", 3), {"ira": 18})
        self.assertEqual(corrupcao.deltas_intencao("neutro", 3), {})

    def test_intencao_desconhecida_vira_neutro(self):
        self.assertEqual(corrupcao.deltas_intencao("inventada", 2), {})
        self.assertEqual(corrupcao.delta_relacao("inventada", 2), 0)

    def test_aplicar_limita_entre_0_e_100(self):
        pecados = zerados()
        pecados["ira"] = 95
        aplicados, _ = corrupcao.aplicar(pecados, {"ira": 20, "avareza": -5})
        self.assertEqual(pecados["ira"], 100)
        self.assertEqual(pecados["avareza"], 0)
        self.assertEqual(aplicados, {"ira": 5, "avareza": 0})

    def test_manifestacao_so_ao_cruzar_limiar_e_uma_vez(self):
        pecados = zerados()
        pecados["ira"] = 35
        _, novas = corrupcao.aplicar(pecados, {"ira": 10})
        self.assertEqual(novas, ["ira"])
        pecados["ira"] = 30
        _, novas = corrupcao.aplicar(pecados, {"ira": 20}, ja_manifestados=["ira"])
        self.assertEqual(novas, [])

    def test_npc_corrompido_aprova_o_proprio_pecado(self):
        self.assertLess(corrupcao.delta_relacao("violencia", 2), 0)
        self.assertEqual(corrupcao.delta_relacao("violencia", 2, ["violencia"]), 6)
        # gostar de algo que já é bem visto não pode render menos que o normal
        self.assertEqual(corrupcao.delta_relacao("compaixao", 2, ["compaixao"]), 16)

    def test_consumido_e_aparencia(self):
        pecados = zerados()
        pecados["avareza"] = 45
        self.assertIsNone(corrupcao.pecado_consumidor(pecados))
        self.assertEqual(corrupcao.aparencia(pecados), ["dedos manchados de ouro"])
        pecados["ira"] = 100
        self.assertEqual(corrupcao.pecado_consumidor(pecados), "ira")


if __name__ == "__main__":
    unittest.main()
