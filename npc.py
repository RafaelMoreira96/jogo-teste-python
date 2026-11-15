import random

import pygame

from entidade import Entidade


class NPC(Entidade):
    """Personagem do mapa que conversa, anda em cenas ou passeia perto de onde nasceu."""

    def __init__(self, x, y, aparencia, dialogo, codigo=""):
        super().__init__(x, y, 12, 8)
        self.aparencia = aparencia
        self.dialogo = dialogo
        self.codigo = str(codigo)
        self.direcao = "baixo"
        self.origem = pygame.Vector2(x, y)
        self.timer_passeio = random.uniform(2.0, 5.0)
        self.dir_passeio = pygame.Vector2()

    def olhar_para(self, rect):
        self.olhar_para_ponto(rect.centerx, rect.centery)

    def atualizar(self, dt, nivel, em_dialogo=False):
        if self.atualizar_base(dt, nivel):
            return
        if self.aparencia == "placa" or self.pose != "normal" or em_dialogo:
            self.andando = False
            self.anim = 0.0
            return

        # Pequeno passeio natural ao redor do ponto de origem
        self.timer_passeio -= dt
        if self.timer_passeio <= 0:
            self.timer_passeio = random.uniform(1.8, 4.0)
            if random.random() < 0.65:
                self.dir_passeio = pygame.Vector2()
            else:
                para_origem = self.origem - pygame.Vector2(self.rect.midbottom)
                if para_origem.length() > 24:
                    self.dir_passeio = para_origem.normalize()
                else:
                    self.dir_passeio = random.choice([
                        pygame.Vector2(1, 0),
                        pygame.Vector2(-1, 0),
                        pygame.Vector2(0, 1),
                        pygame.Vector2(0, -1),
                    ])

        if self.dir_passeio.length_squared() > 0:
            self.olhar_para_ponto(
                self.rect.centerx + self.dir_passeio.x * 10,
                self.rect.centery + self.dir_passeio.y * 10,
            )
            self.andando = True
            self.anim += dt * 7.0
            if self.mover(self.dir_passeio * 22.0 * dt, nivel):
                self.dir_passeio = pygame.Vector2()
        else:
            self.andando = False
            self.anim = 0.0

    def desenhar(self, tela, camera, gfx, fonte=None):
        quadros = gfx.npcs[self.aparencia][self.direcao]
        img = self.quadro_personagem(quadros) if self.aparencia != "placa" else quadros[0]
        if self.pose == "caido" and self.aparencia != "placa":
            img = pygame.transform.rotate(img, 90)

        if self.aparencia != "placa":
            self.desenhar_sombra(tela, camera, gfx, (self.rect.centerx, self.rect.bottom - 1))
        # +1: o contorno de baixo dos personagens fica abaixo dos pés.
        r = img.get_rect(midbottom=(self.rect.centerx, self.rect.bottom + 1))
        if self.aparencia != "placa":
            img_transf, rect_desenho = self.transformar_sprite(img, r, camera)
            tela.blit(img_transf, rect_desenho)
        else:
            tela.blit(img, camera.aplicar(r))
        if fonte and self.aparencia != "placa":
            self.desenhar_extras_cabeca(tela, camera, fonte, (self.rect.centerx, self.rect.bottom - 24))
