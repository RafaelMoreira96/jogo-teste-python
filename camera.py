import pygame

from settings import ALTURA, LARGURA


class Camera:
    """Segue o jogador suavemente sem mostrar nada fora do mapa, com Look-Ahead dinâmico nos 8 eixos."""

    def __init__(self, largura_mundo, altura_mundo):
        self.largura_mundo = largura_mundo
        self.altura_mundo = altura_mundo
        self.pos = pygame.Vector2()
        self.lookahead = pygame.Vector2()
        self.suavidade_lookahead = 4.5
        self.suavidade_camera = 7.5
        self.tremor_intensidade = 0.0
        self.tremor_duracao = 0.0
        self.tremor_total = 0.0
        self.offset_tremor = pygame.Vector2()

    def tremer(self, intensidade=2.5, duracao=0.12):
        self.tremor_intensidade = max(self.tremor_intensidade, intensidade)
        self.tremor_duracao = max(self.tremor_duracao, duracao)
        self.tremor_total = max(self.tremor_total, duracao)

    def atualizar_tremor(self, dt):
        if self.tremor_duracao > 0:
            import random
            self.tremor_duracao = max(0.0, self.tremor_duracao - dt)
            if self.tremor_duracao <= 0:
                self.offset_tremor = pygame.Vector2()
                self.tremor_intensidade = 0.0
            else:
                frac = self.tremor_duracao / max(0.01, self.tremor_total)
                amp = self.tremor_intensidade * frac
                self.offset_tremor = pygame.Vector2(random.uniform(-amp, amp), random.uniform(-amp, amp))
        else:
            self.offset_tremor = pygame.Vector2()

    def _alvo(self, rect, offset_lookahead=None):
        centro_x = rect.centerx + (offset_lookahead.x if offset_lookahead else 0.0)
        centro_y = rect.centery + (offset_lookahead.y if offset_lookahead else 0.0)

        x = centro_x - LARGURA / 2
        y = centro_y - ALTURA / 2
        x = max(0.0, min(x, self.largura_mundo - LARGURA))
        y = max(0.0, min(y, self.altura_mundo - ALTURA))
        # Mapa menor que a tela: centraliza.
        if self.largura_mundo < LARGURA:
            x = (self.largura_mundo - LARGURA) / 2
        if self.altura_mundo < ALTURA:
            y = (self.altura_mundo - ALTURA) / 2
        return pygame.Vector2(x, y)

    def centralizar(self, rect):
        self.lookahead = pygame.Vector2(0, 0)
        self.pos = self._alvo(rect)

    def seguir(self, rect, dt, lookahead=None):
        if lookahead is not None:
            taxa_la = min(1.0, dt * self.suavidade_lookahead)
            self.lookahead += (lookahead - self.lookahead) * taxa_la
        else:
            taxa_la = min(1.0, dt * self.suavidade_lookahead)
            self.lookahead += (pygame.Vector2(0, 0) - self.lookahead) * taxa_la

        alvo_final = self._alvo(rect, self.lookahead)
        self.pos += (alvo_final - self.pos) * min(1.0, dt * self.suavidade_camera)

    @property
    def offset(self):
        tx = getattr(self, "offset_tremor", pygame.Vector2()).x
        ty = getattr(self, "offset_tremor", pygame.Vector2()).y
        return round(self.pos.x + tx), round(self.pos.y + ty)

    def aplicar(self, rect):
        ox, oy = self.offset
        return rect.move(-ox, -oy)

    def aplicar_rect(self, rect):
        return self.aplicar(rect)

    def aplicar_ponto(self, pos):
        ox, oy = self.offset
        return round(pos[0] - ox), round(pos[1] - oy)

    def aplicar_pos(self, pos):
        return self.aplicar_ponto(pos)
