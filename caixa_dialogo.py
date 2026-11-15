"""Caixa de diálogo com efeito de máquina de escrever e escolhas."""
import pygame

from settings import ALTURA, LARGURA
from ui import AMARELO, BRANCO, desenhar_texto, quebrar_linhas

CAIXA = pygame.Rect(6, ALTURA - 52, LARGURA - 12, 46)
MARGEM = 7
ALTURA_LINHA = 12
LINHAS_POR_PAGINA = 3
COR_CAIXA = (16, 20, 44)
COR_BORDA_INTERNA = (90, 100, 150)


def _moldura(tela, rect):
    pygame.draw.rect(tela, COR_CAIXA, rect)
    pygame.draw.rect(tela, BRANCO, rect, 1)
    pygame.draw.rect(tela, COR_BORDA_INTERNA, rect.inflate(-4, -4), 1)


class CaixaDialogo:
    def __init__(self, conversa, fonte, letras_por_segundo):
        self.conversa = conversa
        self.fonte = fonte
        self.velocidade = letras_por_segundo
        self.terminou = False
        self.nome = ""
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
            self.nome = no[1]
            linhas = quebrar_linhas(self.fonte, no[2], CAIXA.width - MARGEM * 2)
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

    def desenhar(self, tela):
        if self.em_espera or not self.pagina:
            return
        # Abertura suave da caixa nos primeiros 0.12s
        abertura = min(1.0, self.t / 0.12)
        if abertura < 1.0:
            altura_atual = max(8, round(CAIXA.height * abertura))
            rect_anim = pygame.Rect(CAIXA.x, CAIXA.centery - altura_atual // 2, CAIXA.width, altura_atual)
            _moldura(tela, rect_anim)
            return
        _moldura(tela, CAIXA)

        if self.nome:
            largura = self.fonte.size(self.nome)[0] + 10
            aba = pygame.Rect(CAIXA.x + 6, CAIXA.y - 12, largura, 14)
            pygame.draw.rect(tela, COR_CAIXA, aba)
            pygame.draw.rect(tela, BRANCO, aba, 1)
            desenhar_texto(tela, self.fonte, self.nome, (aba.x + 5, aba.y + 2), AMARELO)

        restante = int(self.visiveis)
        for i, linha in enumerate(self.pagina):
            parte = linha[: max(0, restante)]
            restante -= len(linha)
            desenhar_texto(tela, self.fonte, parte, (CAIXA.x + MARGEM, CAIXA.y + 6 + i * ALTURA_LINHA))

        if self.opcoes:
            self._desenhar_opcoes(tela)
        elif self.visiveis >= self.total and int(self.t * 3) % 2 == 0:
            x, y = CAIXA.right - 11, CAIXA.bottom - 9
            pygame.draw.polygon(tela, AMARELO, [(x, y), (x + 6, y), (x + 3, y + 3)])

    def _desenhar_opcoes(self, tela):
        largura = max(self.fonte.size(t)[0] for t, _ in self.opcoes) + 22
        altura = len(self.opcoes) * ALTURA_LINHA + 8
        rect = pygame.Rect(0, 0, largura, altura)
        rect.bottomright = (CAIXA.right, CAIXA.top - 2)
        _moldura(tela, rect)
        for i, (texto, _) in enumerate(self.opcoes):
            y = rect.y + 5 + i * ALTURA_LINHA
            if i == self.cursor:
                desenhar_texto(tela, self.fonte, ">", (rect.x + 6, y), AMARELO)
            cor = AMARELO if i == self.cursor else BRANCO
            desenhar_texto(tela, self.fonte, texto, (rect.x + 14, y), cor)
