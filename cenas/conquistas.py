"""Tela de Galeria de Conquistas em 16-bits para A Lenda Perdida."""
import math
import pygame

from cenas.base import Cena
from conquistas import CONQUISTAS_DEF
from settings import ALTURA, LARGURA
from ui import AMARELO, BRANCO, CINZA, desenhar_texto, escurecer


class CenaConquistas(Cena):
    transparente = True

    def __init__(self, app, conquistas_mgr):
        super().__init__(app)
        self.mgr = conquistas_mgr
        self.lista_chaves = list(CONQUISTAS_DEF.keys())
        self.indice = 0
        self.scroll_y = 0
        self.t = 0.0

    def atualizar(self, dt):
        self.t += dt
        entrada = self.app.entrada
        audio = getattr(self.app, "audio", None)

        ant = self.indice
        if entrada.apertou("cima"):
            self.indice = (self.indice - 1) % len(self.lista_chaves)
        elif entrada.apertou("baixo"):
            self.indice = (self.indice + 1) % len(self.lista_chaves)

        if self.indice != ant and audio:
            audio.sfx("menu_mover")

        if entrada.apertou("voltar") or entrada.apertou("pausa"):
            if audio:
                audio.sfx("menu_voltar")
            self.app.desempilhar()

        # Ajusta scroll vertical suave para manter o item selecionado visível
        alvo_scroll = max(0, min(len(self.lista_chaves) - 4, self.indice - 1))
        self.scroll_y += (alvo_scroll - self.scroll_y) * 12.0 * dt

    def desenhar(self, tela):
        escurecer(tela, 215)
        fonte = self.app.fontes.normal

        # Painel central
        painel = pygame.Rect(12, 8, LARGURA - 24, ALTURA - 16)
        pygame.draw.rect(tela, (16, 20, 36), painel, border_radius=4)
        pygame.draw.rect(tela, (215, 175, 65), painel, 1, border_radius=4)
        pygame.draw.rect(tela, (55, 65, 95), painel.inflate(-2, -2), 1, border_radius=3)

        # Cabeçalho
        total_desbloq = len(self.mgr.desbloqueadas)
        total_geral = len(self.lista_chaves)
        desenhar_texto(tela, fonte, "GALERIA DE CONQUISTAS", (20, 14), AMARELO)
        desenhar_texto(
            tela,
            fonte,
            f"{total_desbloq}/{total_geral} Desbloqueadas",
            (LARGURA - 24, 14),
            (110, 255, 140) if total_desbloq == total_geral else BRANCO,
            centro=False,
        )
        pygame.draw.line(tela, (65, 75, 110), (16, 26), (LARGURA - 16, 26))

        # Área dos cards de conquistas
        base_y = 32
        card_altura = 28
        espaco_card = 4

        # Área de recorte para o scroll
        clip_rect = pygame.Rect(14, base_y, LARGURA - 28, 114)
        antigo_clip = tela.get_clip()
        tela.set_clip(clip_rect)

        for i, chave in enumerate(self.lista_chaves):
            conq = CONQUISTAS_DEF[chave]
            desbloqueada = chave in self.mgr.desbloqueadas

            y_pos = base_y + int((i - self.scroll_y) * (card_altura + espaco_card))
            if y_pos < base_y - card_altura or y_pos > base_y + 114:
                continue

            rect_card = pygame.Rect(16, y_pos, LARGURA - 32, card_altura)
            eh_selecionado = (i == self.indice)

            # Fundo do card
            if eh_selecionado:
                pygame.draw.rect(tela, (34, 44, 76), rect_card, border_radius=3)
                pygame.draw.rect(tela, AMARELO, rect_card, 1, border_radius=3)
            else:
                cor_bg = (24, 28, 48) if desbloqueada else (18, 20, 32)
                pygame.draw.rect(tela, cor_bg, rect_card, border_radius=3)
                cor_borda = (95, 115, 160) if desbloqueada else (42, 48, 70)
                pygame.draw.rect(tela, cor_borda, rect_card, 1, border_radius=3)

            # Ícone de troféu ou cadeado
            if desbloqueada:
                pygame.draw.circle(tela, (255, 215, 60), (30, y_pos + 14), 6)
                pygame.draw.circle(tela, (180, 130, 20), (30, y_pos + 14), 6, 1)
                cor_tit = AMARELO if eh_selecionado else BRANCO
                cor_desc = (210, 215, 235)
                tit_texto = conq["titulo"]
                desc_texto = conq["desc"]
            else:
                pygame.draw.circle(tela, (65, 70, 90), (30, y_pos + 14), 6)
                pygame.draw.circle(tela, (40, 44, 58), (30, y_pos + 14), 6, 1)
                cor_tit = (130, 135, 155)
                cor_desc = (95, 100, 120)
                tit_texto = "??? Bloqueada"
                desc_texto = conq["desc"] if eh_selecionado else "Requisito misterioso..."

            desenhar_texto(tela, fonte, tit_texto, (42, y_pos + 4), cor_tit)
            desenhar_texto(tela, fonte, desc_texto, (42, y_pos + 16), cor_desc)

        tela.set_clip(antigo_clip)

        # Barra de rolagem à direita
        barra_x = LARGURA - 18
        altura_barra = 110
        pygame.draw.line(tela, (35, 42, 65), (barra_x, base_y), (barra_x, base_y + altura_barra), 2)
        tam_cursor = max(14, int(altura_barra / len(self.lista_chaves)))
        prog = self.indice / max(1, len(self.lista_chaves) - 1)
        y_cursor = base_y + int(prog * (altura_barra - tam_cursor))
        pygame.draw.line(tela, (215, 180, 75), (barra_x, y_cursor), (barra_x, y_cursor + tam_cursor), 2)

        # Rodapé
        rodape = "Setas: Navegar | Esc / X: Voltar"
        desenhar_texto(tela, fonte, rodape, (LARGURA // 2, ALTURA - 12), CINZA, centro=True)
