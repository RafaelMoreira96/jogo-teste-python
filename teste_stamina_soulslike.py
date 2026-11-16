"""Suíte de testes para o Sistema de Stamina e HUD Soulslike (Prompt Atual)."""
import os
import pygame

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
pygame.init()

from main import App
from rpg import SistemaRPG
from player import Jogador
from hud import desenhar_hud
from entrada import Entrada


class EntradaDummy(Entrada):
    def __init__(self, cfg):
        super().__init__(cfg)
        self._apertos = set()
        self._segura = set()

    def apertou(self, acao):
        return acao in self._apertos

    def segurando(self, acao):
        return acao in self._segura

    def simular_aperto(self, acao):
        self._apertos.add(acao)
        self._segura.add(acao)

    def simular_soltura(self, acao):
        self._apertos.discard(acao)
        self._segura.discard(acao)

    def limpar_apertos(self):
        self._apertos.clear()


class NivelDummy:
    def __init__(self):
        self.cama_pos = None
        self.objetos_3d = []
        self.eh_interior = False
        self.caminho = None
        self.tochas = []

    def colide_parede(self, rect):
        return False

    def colisoes(self, rect, pode_nadar=True):
        return []

    def eh_agua_em(self, x, y):
        return False

    def cortar_arbustos(self, rect):
        return []


def test_stamina_escala_com_nivel():
    print("--- 1. Testando Escala de Stamina com Nível do Personagem ---")
    rpg = SistemaRPG()
    assert rpg.nivel == 1
    assert rpg.stamina_maxima == 60.0, f"Nível 1 deveria ter 60 de stamina, obteve {rpg.stamina_maxima}"
    print("✓ Nível 1: Stamina Máxima = 60.0")

    # Sobe para Nível 2
    rpg.ganhar_xp(rpg.xp_proximo)
    assert rpg.nivel == 2
    assert rpg.stamina_maxima == 68.0, f"Nível 2 deveria ter 68 de stamina, obteve {rpg.stamina_maxima}"
    assert rpg.stamina == 68.0, "Stamina deve ser preenchida ao subir de nível"
    print("✓ Nível 2: Stamina Máxima = 68.0 (restaurada ao subir de nível)")

    # Simula Nível 5
    rpg.nivel = 5
    assert rpg.stamina_maxima == 60.0 + (5 - 1) * 8.0  # 92.0
    print(f"✓ Nível 5: Stamina Máxima = {rpg.stamina_maxima}")

    # Simula Nível 15 (Endgame)
    rpg.nivel = 15
    assert rpg.stamina_maxima == 60.0 + (15 - 1) * 8.0  # 172.0
    print(f"✓ Nível 15: Stamina Máxima = {rpg.stamina_maxima}")


def test_consumo_stamina_ataques():
    print("\n--- 2. Testando Consumo de Stamina nos Ataques e Combos ---")
    app = App()
    rpg = SistemaRPG()
    jogador = Jogador(100, 100)
    jogador.rpg = rpg
    nivel = NivelDummy()
    entrada = EntradaDummy(app.config)

    stamina_inicial = rpg.stamina
    # Golpe 1 (Corte Ágil)
    jogador.atacar()
    assert jogador.atacando, "Golpe 1 deveria iniciar"
    assert rpg.stamina < stamina_inicial, "Stamina deveria diminuir após ataque"
    esperado_pos_golpe1 = stamina_inicial - 14.0
    assert abs(rpg.stamina - esperado_pos_golpe1) < 0.01, f"Esperava {esperado_pos_golpe1}, obteve {rpg.stamina}"
    print(f"✓ Golpe 1 consumiu 14 stamina (Restante: {rpg.stamina}/{rpg.stamina_maxima})")

    # Atualiza até fim do golpe 1
    jogador.atualizar(0.16, entrada, nivel)
    # Golpe 2 (Corte Cruzado)
    jogador.atacar()
    assert jogador.combo_etapa == 1
    esperado_pos_golpe2 = esperado_pos_golpe1 - 16.0
    assert abs(rpg.stamina - esperado_pos_golpe2) < 0.01
    print(f"✓ Golpe 2 consumiu 16 stamina (Restante: {rpg.stamina}/{rpg.stamina_maxima})")

    # Esgota a stamina para testar bloqueio de ataque sem fôlego
    rpg.stamina = 5.0
    rpg.exaustao_stamina = True
    jogador.tempo_ataque = 0.0
    jogador.atacar()
    assert not jogador.atacando, "Jogador em exaustão NÃO deve conseguir atacar!"
    print("✓ Jogador sem fôlego/exaurido é impedido de atacar!")


def test_consumo_stamina_dash():
    print("\n--- 3. Testando Consumo de Stamina no Dash e Esquiva ---")
    app = App()
    rpg = SistemaRPG()
    jogador = Jogador(100, 100)
    jogador.rpg = rpg
    nivel = NivelDummy()
    entrada = EntradaDummy(app.config)

    # Executa Dash
    stamina_antes = rpg.stamina
    entrada.simular_aperto("correr")
    jogador.atualizar(0.01, entrada, nivel)
    entrada.limpar_apertos()
    assert jogador.tempo_dash > 0, "Dash deveria ter sido ativado"
    assert abs(rpg.stamina - (stamina_antes - 18.0)) < 0.01, "Dash deve consumir 18 de stamina"
    print(f"✓ Dash consumiu 18 de stamina com sucesso (Restante: {rpg.stamina})")

    # Reseta dash cooldown e esvazia stamina
    jogador.tempo_dash = 0.0
    jogador.recarga_dash = 0.0
    rpg.stamina = 5.0
    rpg.exaustao_stamina = True
    entrada.simular_aperto("correr")
    jogador.atualizar(0.01, entrada, nivel)
    assert jogador.tempo_dash <= 0, "Dash NÃO deve ativar se estiver sem stamina ou em exaustão!"
    print("✓ Jogador sem stamina é impedido de realizar Dash!")


def test_guard_break_escudo():
    print("\n--- 4. Testando Bloqueio de Escudo e Quebra de Guarda (Guard Break) ---")
    rpg = SistemaRPG()
    jogador = Jogador(100, 100)
    jogador.rpg = rpg
    jogador.escudo_equipado = "escudo_madeira"
    jogador.defendendo = True
    jogador.direcao = "baixo"

    # Bloqueio normal com stamina suficiente
    rpg.stamina = 50.0
    dano_levado = jogador.levar_dano(2, (100, 150), rpg=rpg)
    assert not dano_levado, "Bloqueio deve anular o dano se houver stamina suficiente"
    assert rpg.stamina < 50.0, "Bloqueio deve consumir stamina"
    print(f"✓ Bloqueio bem-sucedido absorveu impacto e consumiu stamina (Restante: {rpg.stamina})")

    # Bloqueio com stamina insuficiente -> QUEBRA DE GUARDA
    rpg.stamina = 5.0
    jogador.defendendo = True
    dano_levado = jogador.levar_dano(4, (100, 150), rpg=rpg)
    assert dano_levado, "Quebra de guarda deve causar dano parcial ao herói"
    assert not jogador.defendendo, "Quebra de guarda deve baixar o escudo"
    assert rpg.exaustao_stamina, "Quebra de guarda deve induzir estado de exaustão"
    assert jogador.tempo_empurrao > 0, "Quebra de guarda deve induzir stagger/atordoamento"
    print("✓ Quebra de Guarda (Guard Break) Soulslike acionada com sucesso!")


def test_hud_soulslike():
    print("\n--- 5. Testando Renderização do HUD Soulslike ---")
    app = App()
    tela = pygame.Surface((320, 180))
    rpg = SistemaRPG()
    rpg.nivel = 7
    rpg.stamina = 45.0
    rpg.vida_fantasma = 6.0
    rpg.stamina_fantasma = 75.0

    desenhar_hud(
        tela,
        app.gfx,
        app.fontes.normal,
        vida=4,
        vida_maxima=6,
        inimigos_restantes=2,
        rpg=rpg,
        tempo=1.5,
        config={"tamanho_hud": "normal"},
    )
    print("✓ HUD Soulslike Normal (Barras Vermelha, Azul e Verde) renderizado com sucesso!")

    # Teste HUD Expandido
    desenhar_hud(
        tela,
        app.gfx,
        app.fontes.normal,
        vida=6,
        vida_maxima=10,
        inimigos_restantes=0,
        rpg=rpg,
        tempo=2.0,
        config={"tamanho_hud": "expandido"},
    )
    print("✓ HUD Soulslike Expandido com escala dinâmica de vida, mana e stamina renderizado com sucesso!")


if __name__ == "__main__":
    test_stamina_escala_com_nivel()
    test_consumo_stamina_ataques()
    test_consumo_stamina_dash()
    test_guard_break_escudo()
    test_hud_soulslike()
    print("\n🎉 TODOS OS TESTES DE STAMINA E HUD SOULSLIKE PASSARAM COM 100% DE SUCESSO!")
