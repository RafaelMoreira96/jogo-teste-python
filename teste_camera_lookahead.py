"""Testes de Validação da Câmera Dinâmica com Look-Ahead nos 8 Eixos (Fase 3)."""
import os
import pygame

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from camera import Camera
from main import App
from cenas.jogo import Jogo
from player import VETORES


def testar_camera_lookahead_direcoes():
    print("--- Testando Look-Ahead nos 8 Eixos ---")
    cam = Camera(1000, 1000)
    rect_centro = pygame.Rect(500, 500, 16, 16)
    cam.centralizar(rect_centro)

    # 1. Movimento para a Direita
    lookahead_dir = VETORES["direita"] * 24.0
    for _ in range(30):
        cam.seguir(rect_centro, 1 / 60, lookahead=lookahead_dir)

    assert cam.lookahead.x > 18.0
    assert abs(cam.lookahead.y) < 1.0
    print(f"✓ Look-ahead 'direita' aplicado suavemente: lookahead=({cam.lookahead.x:.1f}, {cam.lookahead.y:.1f})")

    # 2. Movimento Diagonal (cima_direita)
    lookahead_diag = VETORES["cima_direita"] * 24.0
    for _ in range(45):
        cam.seguir(rect_centro, 1 / 60, lookahead=lookahead_diag)

    assert cam.lookahead.x > 10.0
    assert cam.lookahead.y < -10.0
    print(f"✓ Look-ahead diagonal 'cima_direita' validado: lookahead=({cam.lookahead.x:.1f}, {cam.lookahead.y:.1f})")

    # 3. Retorno ao parar (lookahead nulo)
    for _ in range(60):
        cam.seguir(rect_centro, 1 / 60, lookahead=None)

    assert abs(cam.lookahead.x) < 1.5
    assert abs(cam.lookahead.y) < 1.5
    print(f"✓ Retorno suave ao centro validado: lookahead=({cam.lookahead.x:.1f}, {cam.lookahead.y:.1f})")


def testar_limites_mundo_clamping():
    print("\n--- Testando Limites do Mapa (Clamping sem Black Bars) ---")
    cam = Camera(640, 360)
    # Jogador colado no canto superior esquerdo (0, 0) olhando para cima_esquerda
    rect_canto = pygame.Rect(4, 4, 16, 16)
    cam.centralizar(rect_canto)
    lookahead_canto = VETORES["cima_esquerda"] * 35.0

    for _ in range(30):
        cam.seguir(rect_canto, 1 / 60, lookahead=lookahead_canto)

    assert cam.pos.x == 0.0 and cam.pos.y == 0.0, f"Câmera não pode passar de (0,0), atual: {cam.pos}"

    # Jogador colado no canto inferior direito olhando para baixo_direita
    rect_canto_dir = pygame.Rect(630, 350, 16, 16)
    lookahead_baixo_dir = VETORES["baixo_direita"] * 35.0
    for _ in range(45):
        cam.seguir(rect_canto_dir, 1 / 60, lookahead=lookahead_baixo_dir)

    max_x = 640 - 320
    max_y = 360 - 180
    assert cam.pos.x <= max_x and cam.pos.y <= max_y
    print(f"✓ Clamping em quinas do mundo validado: pos=({cam.pos.x:.1f}, {cam.pos.y:.1f}) <= ({max_x}, {max_y})")


def testar_integracao_jogo_e_corrida():
    print("\n--- Testando Integração com o Jogador (Andando vs Correndo vs Diálogo) ---")
    app = App()
    jogo = Jogo(app, dialogo_inicial=None)
    cam = jogo.camera

    # 1. Parado
    jogo._seguir_camera(0.1)
    la_parado = cam.lookahead.length()

    # 2. Andando
    jogo.jogador.andando = True
    jogo.jogador.correndo = False
    jogo.jogador.direcao = "direita"
    for _ in range(30):
        jogo._seguir_camera(1 / 60)
    la_andando = cam.lookahead.length()
    assert la_andando > la_parado + 5.0
    print(f"✓ Andando expande lookahead para {la_andando:.1f}px (campo de visão ampliado)!")

    # 3. Correndo / Dash
    jogo.jogador.correndo = True
    for _ in range(30):
        jogo._seguir_camera(1 / 60)
    la_correndo = cam.lookahead.length()
    assert la_correndo > la_andando + 5.0
    print(f"✓ Correndo/Dash expande lookahead para {la_correndo:.1f}px para maior tempo de reação!")

    # 4. Em diálogo (deve centralizar e anular lookahead)
    jogo.iniciar_dialogo("placa_inicio")
    assert jogo.dialogo is not None
    for _ in range(45):
        jogo._seguir_camera(1 / 60)
    assert cam.lookahead.length() < 3.0
    print("✓ Diálogo ativo anula lookahead suavemente para foco total no interlocutor!")

    print("\n🎉 SISTEMA DE CÂMERA DINÂMICA COM LOOK-AHEAD VALIDADO COM 100% DE SUCESSO!")


if __name__ == "__main__":
    testar_camera_lookahead_direcoes()
    testar_limites_mundo_clamping()
    testar_integracao_jogo_e_corrida()
