import pygame

from settings import ALTURA, LARGURA


class Camera:
    """Segue o jogador suavemente sem mostrar nada fora do mapa."""

    def __init__(self, largura_mundo, altura_mundo):
        self.largura_mundo = largura_mundo
        self.altura_mundo = altura_mundo
        self.pos = pygame.Vector2()

    def _alvo(self, rect):
        x = rect.centerx - LARGURA / 2
        y = rect.centery - ALTURA / 2
        x = max(0, min(x, self.largura_mundo - LARGURA))
        y = max(0, min(y, self.altura_mundo - ALTURA))
        # Mapa menor que a tela: centraliza.
        if self.largura_mundo < LARGURA:
            x = (self.largura_mundo - LARGURA) / 2
        if self.altura_mundo < ALTURA:
            y = (self.altura_mundo - ALTURA) / 2
        return pygame.Vector2(x, y)

    def centralizar(self, rect):
        self.pos = self._alvo(rect)

    def seguir(self, rect, dt):
        self.pos += (self._alvo(rect) - self.pos) * min(1.0, dt * 8)

    @property
    def offset(self):
        return round(self.pos.x), round(self.pos.y)

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
