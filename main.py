"""A Lenda Perdida: um RPG de ação e aventura em 16-bits.

Este arquivo cuida da janela, do loop principal e da pilha de cenas
(menu, jogo, pausa, configurações). A lógica de cada tela fica em cenas/.
"""
import pygame

import config
from audio import SistemaAudio
from cenas.menu import MenuPrincipal
from cenas.splash import CenaAberturaLogos
from entrada import Entrada
from settings import ALTURA, FPS, LARGURA, TITULO
from sprites import Graficos
from ui import Fontes


class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITULO)
        self.config = config.carregar()
        self.tela = pygame.Surface((LARGURA, ALTURA))  # onde tudo é desenhado
        self.aplicar_video()
        self.relogio = pygame.time.Clock()
        self.entrada = Entrada(self.config)
        self.fontes = Fontes()
        self.gfx = Graficos()
        self.audio = SistemaAudio(self.config)
        self.rodando = True
        self.eventos_quadro = []
        self.cenas = [CenaAberturaLogos(self)]

    # ------------------------------------------------------------ janela
    def aplicar_video(self):
        if self.config["tela_cheia"]:
            self.janela = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            escala = self.config["escala"]
            self.janela = pygame.display.set_mode((LARGURA * escala, ALTURA * escala))

    def pos_mouse(self):
        """Converte a posição do mouse na janela para a tela interna 320x180."""
        largura, altura = self.janela.get_size()
        escala = max(1, min(largura // LARGURA, altura // ALTURA))
        ox = (largura - LARGURA * escala) // 2
        oy = (altura - ALTURA * escala) // 2
        mx, my = pygame.mouse.get_pos()
        return max(0, min(LARGURA - 1, (mx - ox) // escala)), max(0, min(ALTURA - 1, (my - oy) // escala))

    def apresentar(self):
        """Amplia a tela pequena pelo maior múltiplo inteiro que couber (pixels nítidos)."""
        largura, altura = self.janela.get_size()
        escala = max(1, min(largura // LARGURA, altura // ALTURA))
        tamanho = (LARGURA * escala, ALTURA * escala)
        self.janela.fill((0, 0, 0))
        ampliada = pygame.transform.scale(self.tela, tamanho)
        self.janela.blit(ampliada, ampliada.get_rect(center=self.janela.get_rect().center))
        pygame.display.flip()

    # ------------------------------------------------------------ cenas
    def empilhar(self, cena):
        self.cenas.append(cena)

    def desempilhar(self):
        if len(self.cenas) > 1:
            self.cenas.pop()

    def trocar(self, cena):
        self.cenas = [cena]

    def sair(self):
        self.rodando = False

    # ------------------------------------------------------------ loop
    def processar_eventos(self):
        from cenas.editor import Editor
        from cenas.jogo import Jogo

        self.entrada.iniciar_quadro()
        self.eventos_quadro = pygame.event.get()
        for evento in self.eventos_quadro:
            if evento.type == pygame.QUIT:
                self.sair()
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_F11:
                    self.config["tela_cheia"] = not self.config["tela_cheia"]
                    self.aplicar_video()
                    config.salvar(self.config)
                elif evento.key == pygame.K_F2 and not isinstance(self.cenas[-1], Editor):
                    mapa_atual = getattr(getattr(self.cenas[-1], "nivel", None), "caminho", None)
                    self.trocar(Editor(self, mapa_atual))
                elif evento.key == pygame.K_F5 and isinstance(self.cenas[-1], Jogo):
                    self.cenas[-1].recarregar_historia()
                    self.cenas[-1].iniciar_dialogo("inicio", opcional=True)
            self.entrada.processar(evento)

    def passo(self, dt):
        self.cenas[-1].atualizar(dt)
        # Desenha a partir da última cena que não é transparente.
        inicio = len(self.cenas) - 1
        while inicio > 0 and self.cenas[inicio].transparente:
            inicio -= 1
        for cena in self.cenas[inicio:]:
            cena.desenhar(self.tela)

    def rodar(self):
        while self.rodando:
            dt = min(self.relogio.tick(FPS) / 1000, 1 / 20)  # evita saltos se travar
            self.processar_eventos()
            self.passo(dt)
            self.apresentar()
        pygame.quit()


if __name__ == "__main__":
    App().rodar()
