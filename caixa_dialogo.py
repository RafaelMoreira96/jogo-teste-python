"""Caixa de diálogo com efeito de máquina de escrever, retrato do personagem e escolhas."""
import math

import pygame

from settings import ALTURA, LARGURA
from ui import AMARELO, BRANCO, desenhar_cursor, desenhar_painel, desenhar_texto, quebrar_linhas

CAIXA = pygame.Rect(6, ALTURA - 52, LARGURA - 12, 46)
MARGEM = 7
ALTURA_LINHA = 12
LINHAS_POR_PAGINA = 3
TAM_RETRATO = 38


class CaixaDialogo:
    def __init__(self, conversa, fonte, letras_por_segundo, retratos=None):
        """`retratos(nome)` devolve a Surface do rosto de quem fala (ou None)."""
        self.conversa = conversa
        self.fonte = fonte
        self.velocidade = letras_por_segundo
        self.retratos = retratos
        self.terminou = False
        self.nome = ""
        self.retrato = None
        self.paginas = []
        self.pagina = []
        self.visiveis = 0.0
        self.opcoes = None
        self.cursor = 0
        self.t = 0.0
        self.tempo_espera = 0.0
        self.condicao_espera = None
        self._avancar()

    @property
    def em_espera(self):
        return self.tempo_espera > 0 or self.condicao_espera is not None

    @property
    def total(self):
        return sum(len(l) for l in self.pagina)

    @property
    def x_texto(self):
        return CAIXA.x + MARGEM + (TAM_RETRATO + 6 if self.retrato is not None else 0)

    def _avancar(self):
        self.tempo_espera = 0.0
        self.condicao_espera = None
        if self.paginas:
            self._mostrar_pagina(self.paginas.pop(0))
            return
        no = self.conversa.proximo()
        if no is None:
            self.terminou = True
        elif no[0] == "espera":
            alvo = no[1]
            if callable(alvo):
                self.condicao_espera = alvo
            else:
                self.tempo_espera = float(alvo)
        elif no[0] == "fala":
            if no[1] != self.nome or self.retrato is None:
                self.retrato = self.retratos(no[1]) if (self.retratos and no[1]) else None
            self.nome = no[1]
            largura_texto = CAIXA.right - MARGEM - self.x_texto
            linhas = quebrar_linhas(self.fonte, no[2], largura_texto)
            self.paginas = [
                linhas[i : i + LINHAS_POR_PAGINA] for i in range(0, len(linhas), LINHAS_POR_PAGINA)
            ]
            self._mostrar_pagina(self.paginas.pop(0))
        else:  # opções: o texto anterior continua na caixa
            self.opcoes = no[1]
            self.cursor = 0

    def _mostrar_pagina(self, pagina):
        if not self.pagina:
            self.t = 0.0  # anima a abertura da caixa ao aparecer
        self.pagina = pagina
        self.visiveis = 0.0
        self.opcoes = None

    def atualizar(self, dt, entrada):
        self.t += dt
        if self.em_espera:
            if self.tempo_espera > 0:
                self.tempo_espera -= dt
                if self.tempo_espera <= 0:
                    self._avancar()
            elif self.condicao_espera is not None:
                if not self.condicao_espera():
                    self._avancar()
            return

        if self.opcoes:
            if entrada.apertou("cima"):
                self.cursor = (self.cursor - 1) % len(self.opcoes)
            if entrada.apertou("baixo"):
                self.cursor = (self.cursor + 1) % len(self.opcoes)
            if entrada.apertou("confirmar"):
                self.conversa.escolher(self.opcoes[self.cursor][1])
                self.opcoes = None
                self._avancar()
            return

        self.visiveis = min(self.total, self.visiveis + self.velocidade * dt)
        if entrada.apertou("confirmar") or entrada.apertou("acao"):
            if self.visiveis < self.total:
                self.visiveis = self.total  # mostra tudo de uma vez
            else:
                self._avancar()

    # ------------------------------------------------------------------ desenho
    def desenhar(self, tela):
        if self.em_espera or not self.pagina:
            return
        # Abertura suave da caixa nos primeiros 0.12s
        abertura = min(1.0, self.t / 0.12)
        if abertura < 1.0:
            altura_atual = max(8, round(CAIXA.height * abertura))
            rect_anim = pygame.Rect(CAIXA.x, CAIXA.centery - altura_atual // 2, CAIXA.width, altura_atual)
            desenhar_painel(tela, rect_anim, cantos=False)
            return
        desenhar_painel(tela, CAIXA, alfa=240)

        if self.retrato is not None:
            self._desenhar_retrato(tela)

        if self.nome:
            largura = self.fonte.size(self.nome)[0] + 12
            x_aba = self.x_texto - 4
            aba = pygame.Rect(x_aba, CAIXA.y - 11, largura, 14)
            desenhar_painel(tela, aba, "dourado", alfa=250, cantos=False)
            desenhar_texto(tela, self.fonte, self.nome, (aba.x + 6, aba.y + 2), (255, 232, 140))

        restante = int(self.visiveis)
        for i, linha in enumerate(self.pagina):
            parte = linha[: max(0, restante)]
            restante -= len(linha)
            desenhar_texto(tela, self.fonte, parte, (self.x_texto, CAIXA.y + 6 + i * ALTURA_LINHA), BRANCO)

        if self.opcoes:
            self._desenhar_opcoes(tela)
        elif self.visiveis >= self.total:
            # Indicador "continuar" quicando suavemente
            x = CAIXA.right - 12
            y = CAIXA.bottom - 10 + round(math.sin(self.t * 7) * 1.5)
            pygame.draw.polygon(tela, (8, 8, 16), [(x, y + 1), (x + 7, y + 1), (x + 3, y + 5)])
            pygame.draw.polygon(tela, AMARELO, [(x, y), (x + 6, y), (x + 3, y + 3)])

    def _desenhar_retrato(self, tela):
        moldura = pygame.Rect(CAIXA.x + 4, CAIXA.y + 4, TAM_RETRATO, TAM_RETRATO)
        pygame.draw.rect(tela, (8, 8, 16), moldura)
        fundo = moldura.inflate(-2, -2)
        # Fundo em gradiente radial suave atrás do rosto
        for y in range(fundo.height):
            f = y / max(1, fundo.height - 1)
            cor = (round(60 - 36 * f), round(74 - 44 * f), round(130 - 70 * f))
            pygame.draw.line(tela, cor, (fundo.x, fundo.y + y), (fundo.right - 1, fundo.y + y))
        img = self.retrato
        # Leve "fala": o retrato balança 1px enquanto o texto está sendo escrito
        falando = self.visiveis < self.total and int(self.t * 10) % 2 == 0
        tela.blit(img, img.get_rect(midbottom=(fundo.centerx, fundo.bottom + (1 if falando else 0))))
        pygame.draw.rect(tela, (236, 196, 104), moldura, 1)
        pygame.draw.rect(tela, (120, 84, 40), moldura.inflate(-2, -2), 1)
        for cx, cy in (moldura.topleft, (moldura.right - 2, moldura.y), (moldura.x, moldura.bottom - 2), (moldura.right - 2, moldura.bottom - 2)):
            pygame.draw.rect(tela, (255, 240, 170), (cx, cy, 2, 2))

    def _desenhar_opcoes(self, tela):
        largura = max(self.fonte.size(t)[0] for t, _ in self.opcoes) + 24
        altura = len(self.opcoes) * ALTURA_LINHA + 8
        rect = pygame.Rect(0, 0, largura, altura)
        rect.bottomright = (CAIXA.right, CAIXA.top - 2)
        desenhar_painel(tela, rect, alfa=245)
        for i, (texto, _) in enumerate(self.opcoes):
            y = rect.y + 5 + i * ALTURA_LINHA
            if i == self.cursor:
                faixa = pygame.Surface((rect.width - 6, 11), pygame.SRCALPHA)
                faixa.fill((255, 210, 90, 48))
                tela.blit(faixa, (rect.x + 3, y - 1))
                desenhar_cursor(tela, rect.x + 6, y + 1, t=self.t)
            cor = AMARELO if i == self.cursor else BRANCO
            desenhar_texto(tela, self.fonte, texto, (rect.x + 15, y), cor)
