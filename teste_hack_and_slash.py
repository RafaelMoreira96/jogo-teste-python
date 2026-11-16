import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame

pygame.init()
pygame.display.set_mode((320, 180))

from camera import Camera
from main import App
from player import Jogador
from settings import LARGURA, ALTURA


class EntradaSimulada:
    def __init__(self):
        self._apertou = set()
        self._segurando = set()

    def apertou(self, acao):
        return acao in self._apertou

    def segurando(self, acao):
        return acao in self._segurando

    def simular_aperto(self, acao):
        self._apertou.add(acao)
        self._segurando.add(acao)

    def simular_soltura(self, acao):
        self._apertou.discard(acao)
        self._segurando.discard(acao)

    def limpar_apertos(self):
        self._apertou.clear()


class NivelFalso:
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


def testar_hack_and_slash():
    print("--- Testando Sistema 2D Hack & Slash ---")
    jogador = Jogador(100, 100)
    nivel = NivelFalso()
    entrada = EntradaSimulada()

    # 1. Golpe 1 (Corte Ágil)
    jogador.atacar()
    assert jogador.atacando, "Jogador deveria estar atacando no Golpe 1"
    assert jogador.combo_etapa == 0, f"Esperava etapa 0, obteve {jogador.combo_etapa}"
    assert jogador.duracao_ataque_atual == 0.15, "Duração do golpe 1 incorreta"
    print("✓ Golpe 1 executado com sucesso")

    # Atualiza até terminar o Golpe 1
    jogador.atualizar(0.16, entrada, nivel)
    assert not jogador.atacando, "Golpe 1 deveria ter finalizado"
    assert jogador.tempo_combo_janela > 0, "Janela de combo deveria estar ativa"

    # 2. Golpe 2 (Corte Cruzado)
    jogador.atacar()
    assert jogador.atacando, "Jogador deveria estar atacando no Golpe 2"
    assert jogador.combo_etapa == 1, f"Esperava etapa 1, obteve {jogador.combo_etapa}"
    print("✓ Golpe 2 (Combo x2) encadeado com sucesso")

    # 3. Buffer de input: aperta ataque enquanto golpe 2 está quase acabando
    jogador.tempo_ataque = 0.05
    jogador.atacar()  # dentro da janela de buffer
    assert jogador.buffer_ataque, "Buffer de ataque deveria estar ativado"

    # Ao atualizar para 0, deve consumir o buffer e iniciar Golpe 3 (Finalizador)
    jogador.atualizar(0.06, entrada, nivel)
    assert jogador.atacando, "Buffer deveria ter disparado Golpe 3"
    assert jogador.combo_etapa == 2, f"Esperava etapa 2 (Finalizador), obteve {jogador.combo_etapa}"
    assert jogador.duracao_ataque_atual == 0.24, "Duração do finalizador incorreta"
    rect_finisher = jogador.rect_espada()
    assert rect_finisher.width >= 35, f"Área de 360° do finalizador esperada, tamanho: {rect_finisher.size}"
    print("✓ Buffer de ataque e Golpe 3 (Finalizador 360°) validados")

    # 4. Dash-Cancel de animação de golpe
    jogador.atacar()
    assert jogador.atacando
    entrada.simular_aperto("correr")
    jogador.atualizar(0.01, entrada, nivel)
    entrada.limpar_apertos()
    assert not jogador.atacando, "Dash-cancel deveria ter cancelado a animação do ataque"
    assert jogador.tempo_dash > 0, "Dash deveria ter iniciado"
    print("✓ Dash-Cancel de recuperação de ataque validado com sucesso")

    # 5. Dash i-frames (invulnerabilidade durante a esquiva)
    assert jogador.tempo_dash > 0
    dano_levado = jogador.levar_dano(2, (50, 50))
    assert not dano_levado, "Jogador não deveria levar dano durante o Dash (i-frames)"
    assert jogador.vida == jogador.vida_maxima, "Vida não deveria ter diminuído"
    print("✓ I-frames de esquiva do Dash validados")

    # 6. Dash-Strike (Estocada em arrancada)
    jogador.atacar()
    assert jogador.dash_strike, "Deveria ser Dash-Strike"
    rect_dash = jogador.rect_espada()
    assert rect_dash.width > 16, "Alcance de Dash-Strike estendido"
    print("✓ Dash-Strike em arrancada validado com sucesso")

    # 7. Teste de cena de jogo com Combo, Multiplicador e Estilo
    from cenas.jogo import Jogo
    app = App()
    jogo = Jogo(app, dialogo_inicial=None)
    jogo.combo_acertos = 0
    jogo.tempo_combo = 0.0

    # Simula acertos em inimigo
    jogo.combo_acertos = 5
    jogo.tempo_combo = 2.0
    jogo.atualizar(0.01)
    assert jogo.jogador.fator_frenesi == 1.08, "Fator frenesi para combo 5 deveria ser 1.08"

    jogo.combo_acertos = 12
    jogo.tempo_combo = 2.0
    jogo.atualizar(0.01)
    assert jogo.jogador.fator_frenesi == 1.25, "Fator frenesi para combo 12 deveria ser 1.25"

    # Testa decaimento do combo
    jogo.atualizar(2.5)
    assert jogo.combo_acertos == 0, "Combo deveria ter resetado após expiração"
    print("✓ Contador de Combo, Estilo e Frenesi na cena de jogo validados")

    # 8. Testa desenho da interface de combo
    tela = pygame.Surface((320, 180))
    jogo.combo_acertos = 9
    jogo.tempo_combo = 2.0
    jogo._desenhar_combo(tela, app.fontes.normal)
    print("✓ Renderização da badge de combo Hack & Slash validada")

    # 9. Verificação de remoção do Editor
    assert not os.path.exists("cenas/editor.py"), "cenas/editor.py não deve mais existir"
    with open("main.py", "r") as f:
        conteudo_main = f.read()
    assert "Editor" not in conteudo_main, "Referência ao Editor não deve constar em main.py"
    with open("cenas/menu.py", "r") as f:
        conteudo_menu = f.read()
    assert "Editor de jogo" not in conteudo_menu, "'Editor de jogo' não deve constar no menu"
    print("✓ Remoção completa do Editor de Fases verificada")

    print("\nTODOS OS TESTES DE HACK & SLASH PASSARAM COM 100% DE SUCESSO!")


if __name__ == "__main__":
    testar_hack_and_slash()
