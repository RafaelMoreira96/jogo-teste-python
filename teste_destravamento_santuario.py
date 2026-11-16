"""Teste de regressão para entrada no Santuário Sombrio e destravamento de pose."""
import os
import pathlib
import pygame

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
pygame.init()

from main import App
import salvamento
from entrada import Entrada


def test_carregar_save_santuario():
    app = App()
    jogo = salvamento.carregar_jogo(app, slot=1)
    assert jogo is not None, "Falha ao carregar save slot 1"
    assert jogo.jogador.pose == "normal", f"Pose esperada 'normal', obtida: {jogo.jogador.pose}"

    class MockEntrada(Entrada):
        def __init__(self):
            super().__init__(app.config)
        def segurando(self, acao):
            return acao in ("cima",)
        def esta_pressionada(self, acao):
            return acao in ("cima",)
        def apertou(self, acao):
            return False
        def liberou(self, acao):
            return False
        def duracao(self, acao):
            return 0.5 if acao == "cima" else 0.0

    pos_y_antes = jogo.jogador.rect.centery
    app.entrada = MockEntrada()
    jogo.fade_estado = None
    for _ in range(30):
        jogo.atualizar(1 / 60)

    assert jogo.jogador.rect.centery < pos_y_antes, "Herói não se moveu após carregar savegame!"
    print("✓ Teste carregar_save_santuario passou!")


def test_cutscene_despertar_santuario():
    from cenas.jogo import Jogo
    app = App()
    jogo = Jogo(app)
    jogo.em_abertura = False
    jogo.flags.discard("santuario_desperto")

    caminho_santuario = pathlib.Path("maps/santuario.txt")
    jogo.trocar_mapa(caminho_santuario, usar_porta=False)
    assert jogo.dialogo is not None, "Cutscene do santuário não iniciou"

    class AvancaDialogo(Entrada):
        def __init__(self):
            super().__init__(app.config)
            self.tick = 0
        def apertou(self, acao):
            return acao in ("confirmar", "acao") and (self.tick % 4 == 0)
        def segurando(self, acao):
            return False
        def esta_pressionada(self, acao):
            return False
        def liberou(self, acao):
            return False

    avanca = AvancaDialogo()
    app.entrada = avanca
    for f in range(500):
        avanca.tick = f
        jogo.atualizar(0.1)
        if not jogo.dialogo:
            break

    assert jogo.dialogo is None, "Cutscene não terminou a tempo"
    assert "santuario_desperto" in jogo.flags, "Flag santuario_desperto não definida"
    assert jogo.jogador.pose == "normal", f"Pose pós-cutscene deve ser normal, obtida: {jogo.jogador.pose}"
    print("✓ Teste cutscene_despertar_santuario passou!")


if __name__ == "__main__":
    test_carregar_save_santuario()
    test_cutscene_despertar_santuario()
    print("TODOS OS TESTES DE DESTRAVAMENTO DO SANTUÁRIO PASSARAM COM SUCESSO!")
