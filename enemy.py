"""Inimigos do jogo: Slimes (azuis e verdes), Goblins/Duendes, Zumbis Arqueiros e Trolls.

Cada inimigo possui IA própria, atributos, recompensas de XP e padrões
de ataque bem telegrafados e divertidos.
"""
import math
import random

import pygame

from entidade import Entidade
from settings import (
    SLIME_ALCANCE_VISAO,
    SLIME_VEL_PASSEIO,
    SLIME_VEL_PERSEGUIR,
    SLIME_VIDA,
    TILE,
)

CORES_SLIME_AZUL = [(70, 150, 230), (150, 210, 255), (40, 90, 170)]
CORES_SLIME_VERDE = [(68, 205, 78), (145, 245, 120), (32, 130, 42)]
CORES_DUENDE = [(115, 175, 55), (185, 55, 45), (120, 70, 40)]
CORES_ZUMBI = [(100, 145, 125), (60, 95, 80), (160, 105, 55)]
CORES_TROLL = [(110, 128, 102), (72, 86, 68), (165, 172, 180)]


class FlechaInimigo:
    """Projétil disparado pelo Zumbi Arqueiro."""

    def __init__(self, pos, vel, dano=1):
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(vel)
        self.dano = dano
        self.tempo_vida = 3.2
        self.raio = 3

    def reset(self, pos, vel, dano=1):
        self.pos.x = float(pos[0])
        self.pos.y = float(pos[1])
        self.vel.x = float(vel[0])
        self.vel.y = float(vel[1])
        self.dano = dano
        self.tempo_vida = 3.2
        self.raio = 3

    @property
    def rect(self):
        r = pygame.Rect(0, 0, 8, 8)
        r.center = (round(self.pos.x), round(self.pos.y))
        return r

    def atualizar(self, dt, nivel):
        self.tempo_vida -= dt
        if self.tempo_vida <= 0:
            return False
        self.pos += self.vel * dt
        cx, cy = int(self.pos.x // TILE), int(self.pos.y // TILE)
        if not nivel.dentro(cx, cy) or nivel.solido(cx, cy):
            return False
        return True

    def desenhar(self, tela, camera, gfx):
        pos_tela = camera.aplicar_ponto(self.pos)
        ang = math.degrees(math.atan2(-self.vel.y, self.vel.x))
        if abs(self.vel.x) >= abs(self.vel.y):
            dir_str = "direita" if self.vel.x > 0 else "esquerda"
        else:
            dir_str = "baixo" if self.vel.y > 0 else "cima"
        img = gfx.flecha.get(dir_str, gfx.flecha["direita"])
        r = img.get_rect(center=pos_tela)
        tela.blit(img, r)


class Inimigo(Entidade):
    """Classe base para todos os inimigos comuns."""

    def __init__(self, x, y, larg, alt, vida_max, xp, dano=1, cor_particulas=None):
        super().__init__(x, y, larg, alt)
        self.vida_max = vida_max
        self.vida = vida_max
        self.xp_recompensa = xp
        self.dano_contato = dano
        self.cor_particulas = cor_particulas or CORES_SLIME_AZUL

        self.anim = random.random() * math.tau
        self.direcao = pygame.Vector2()
        self.tempo_direcao = 0.0
        self.atordoado = 0.0
        self.congelado = 0.0
        self.piscar = 0.0
        self.ultimo_golpe = -1

    @property
    def vivo(self):
        return self.vida > 0

    def _nova_direcao(self):
        self.tempo_direcao = random.uniform(1.0, 2.5)
        if random.random() < 0.3:
            self.direcao = pygame.Vector2()
        else:
            self.direcao = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))

    def receber_golpe(self, golpe_id, origem, dano=1):
        if golpe_id == self.ultimo_golpe:
            return False
        self.ultimo_golpe = golpe_id
        self.vida -= dano
        self.piscar = 0.15
        self.atordoado = 0.35
        self.empurrar(origem, 190, 0.16)
        self.deformar(1.3, 0.7)
        return True


class Slime(Inimigo):
    """Slime azul clássico: saltita calmamente e persegue com pulinhos elásticos."""

    def __init__(self, x, y):
        super().__init__(x, y, 12, 8, vida_max=SLIME_VIDA, xp=15, dano=1, cor_particulas=CORES_SLIME_AZUL)

    def atualizar(self, dt, nivel, jogador, projeteis_inimigos=None, particulas=None):
        self.piscar = max(0.0, self.piscar - dt)
        self.atordoado = max(0.0, self.atordoado - dt)
        self.congelado = max(0.0, self.congelado - dt)
        self.atualizar_base(dt, nivel)

        if self.atualizar_empurrao(dt, nivel) or self.atordoado > 0 or self.congelado > 0:
            return

        ate_jogador = pygame.Vector2(jogador.rect.center) - pygame.Vector2(self.rect.center)
        distancia = ate_jogador.length()
        if 0 < distancia < SLIME_ALCANCE_VISAO:
            self.anim += dt * 7.5
            pulso = max(0.2, math.sin(self.anim) * 0.6 + 0.8)
            self.mover(ate_jogador.normalize() * (SLIME_VEL_PERSEGUIR * pulso) * dt, nivel)
        else:
            self.anim += dt * 4.5
            self.tempo_direcao -= dt
            if self.tempo_direcao <= 0:
                self._nova_direcao()
            if self.mover(self.direcao * SLIME_VEL_PASSEIO * dt, nivel):
                self._nova_direcao()

    def desenhar(self, tela, camera, gfx, fonte=None):
        onda = math.sin(self.anim)
        quadro = 0 if onda > 0 else 1
        img = (gfx.slime_branco if self.piscar > 0 else gfx.slime)[quadro]

        salto = max(0.0, onda) * 3.5
        self.z = salto
        self.desenhar_sombra(tela, camera, gfx)

        sx = self.escala_x * (1.0 - onda * 0.12)
        sy = self.escala_y * (1.0 + onda * 0.14)
        nova_larg = max(6, round(img.get_width() * sx))
        nova_alt = max(6, round(img.get_height() * sy))
        img_elastica = pygame.transform.scale(img, (nova_larg, nova_alt))
        r = img_elastica.get_rect(midbottom=(self.rect.centerx, self.rect.bottom + 1 - round(salto)))
        pos_tela = camera.aplicar(r)
        tela.blit(img_elastica, pos_tela)

        if self.congelado > 0:
            gelo = pygame.Surface(pos_tela.size, pygame.SRCALPHA)
            gelo.fill((110, 235, 255, 110))
            pygame.draw.rect(gelo, (210, 250, 255, 190), gelo.get_rect(), 1)
            tela.blit(gelo, pos_tela)


class SlimeVerde(Inimigo):
    """Slime verde ácido: mais resistente, mais rápido e dá saltos longos."""

    def __init__(self, x, y):
        super().__init__(x, y, 12, 8, vida_max=3, xp=25, dano=1, cor_particulas=CORES_SLIME_VERDE)

    def atualizar(self, dt, nivel, jogador, projeteis_inimigos=None, particulas=None):
        self.piscar = max(0.0, self.piscar - dt)
        self.atordoado = max(0.0, self.atordoado - dt)
        self.congelado = max(0.0, self.congelado - dt)
        self.atualizar_base(dt, nivel)

        if self.atualizar_empurrao(dt, nivel) or self.atordoado > 0 or self.congelado > 0:
            return

        ate_jogador = pygame.Vector2(jogador.rect.center) - pygame.Vector2(self.rect.center)
        distancia = ate_jogador.length()
        if 0 < distancia < 95:
            self.anim += dt * 9.0
            pulso = max(0.3, math.sin(self.anim) * 0.8 + 0.9)
            self.mover(ate_jogador.normalize() * (72 * pulso) * dt, nivel)
        else:
            self.anim += dt * 5.0
            self.tempo_direcao -= dt
            if self.tempo_direcao <= 0:
                self._nova_direcao()
            if self.mover(self.direcao * 35 * dt, nivel):
                self._nova_direcao()

    def desenhar(self, tela, camera, gfx, fonte=None):
        onda = math.sin(self.anim)
        quadro = 0 if onda > 0 else 1
        img = (gfx.slime_verde_branco if self.piscar > 0 else gfx.slime_verde)[quadro]

        salto = max(0.0, onda) * 4.5
        self.z = salto
        self.desenhar_sombra(tela, camera, gfx)

        sx = self.escala_x * (1.0 - onda * 0.15)
        sy = self.escala_y * (1.0 + onda * 0.16)
        nova_larg = max(6, round(img.get_width() * sx))
        nova_alt = max(6, round(img.get_height() * sy))
        img_elastica = pygame.transform.scale(img, (nova_larg, nova_alt))
        r = img_elastica.get_rect(midbottom=(self.rect.centerx, self.rect.bottom + 1 - round(salto)))
        pos_tela = camera.aplicar(r)
        tela.blit(img_elastica, pos_tela)

        if self.congelado > 0:
            gelo = pygame.Surface(pos_tela.size, pygame.SRCALPHA)
            gelo.fill((110, 235, 255, 110))
            pygame.draw.rect(gelo, (210, 250, 255, 190), gelo.get_rect(), 1)
            tela.blit(gelo, pos_tela)


class Duende(Inimigo):
    """Goblin ágil: corre em ziguezague rápido e dá botes perigosos com a adaga."""

    def __init__(self, x, y):
        super().__init__(x, y, 10, 10, vida_max=4, xp=35, dano=1, cor_particulas=CORES_DUENDE)
        self.fase_zigue = 0.0
        self.tempo_bote = 0.0

    def atualizar(self, dt, nivel, jogador, projeteis_inimigos=None, particulas=None):
        self.piscar = max(0.0, self.piscar - dt)
        self.atordoado = max(0.0, self.atordoado - dt)
        self.congelado = max(0.0, self.congelado - dt)
        self.atualizar_base(dt, nivel)

        if self.atualizar_empurrao(dt, nivel) or self.atordoado > 0 or self.congelado > 0:
            return

        self.fase_zigue += dt * 8.0
        ate_jogador = pygame.Vector2(jogador.rect.center) - pygame.Vector2(self.rect.center)
        distancia = ate_jogador.length()

        if 0 < distancia < 110:
            # Perseguição em ziguezague cortante
            direcao_base = ate_jogador.normalize()
            perpendicular = pygame.Vector2(-direcao_base.y, direcao_base.x)
            desvio = perpendicular * (math.sin(self.fase_zigue) * 0.45)
            vel = (direcao_base + desvio).normalize() * 68.0
            self.mover(vel * dt, nivel)
            self.anim += dt * 9.0
        else:
            self.anim += dt * 4.0
            self.tempo_direcao -= dt
            if self.tempo_direcao <= 0:
                self._nova_direcao()
            if self.mover(self.direcao * 30.0 * dt, nivel):
                self._nova_direcao()

    def desenhar(self, tela, camera, gfx, fonte=None):
        quadro = 0 if int(self.anim) % 2 == 0 else 1
        img = (gfx.duende_branco if self.piscar > 0 else gfx.duende)[quadro]
        self.desenhar_sombra(tela, camera, gfx)
        r = img.get_rect(midbottom=(self.rect.centerx, self.rect.bottom + 1))
        pos_tela = camera.aplicar(r)
        tela.blit(img, pos_tela)

        if self.congelado > 0:
            gelo = pygame.Surface(pos_tela.size, pygame.SRCALPHA)
            gelo.fill((110, 235, 255, 110))
            tela.blit(gelo, pos_tela)


class ZumbiArqueiro(Inimigo):
    """Zumbi com arco: mantém distância do jogador e atira flechas rápidas telegrafadas."""

    def __init__(self, x, y):
        super().__init__(x, y, 10, 12, vida_max=4, xp=45, dano=1, cor_particulas=CORES_ZUMBI)
        self.cooldown_tiro = random.uniform(1.5, 2.5)
        self.mirando = 0.0

    def atualizar(self, dt, nivel, jogador, projeteis_inimigos=None, particulas=None):
        self.piscar = max(0.0, self.piscar - dt)
        self.atordoado = max(0.0, self.atordoado - dt)
        self.congelado = max(0.0, self.congelado - dt)
        self.atualizar_base(dt, nivel)

        if self.atualizar_empurrao(dt, nivel) or self.atordoado > 0 or self.congelado > 0:
            return

        ate_jogador = pygame.Vector2(jogador.rect.center) - pygame.Vector2(self.rect.center)
        distancia = ate_jogador.length()

        if 0 < distancia < 130:
            # Mantém distância tática de cerca de 70 a 110 pixels
            if distancia < 65:
                # Afasta-se do jogador
                fuga = -ate_jogador.normalize()
                self.mover(fuga * 35.0 * dt, nivel)
                self.anim += dt * 5.0
            elif distancia > 105:
                # Aproxima-se para campo de tiro
                self.mover(ate_jogador.normalize() * 32.0 * dt, nivel)
                self.anim += dt * 5.0

            self.cooldown_tiro -= dt
            if self.cooldown_tiro <= 0.6:
                self.mirando = self.cooldown_tiro  # Puxando o arco

            if self.cooldown_tiro <= 0:
                self.cooldown_tiro = random.uniform(2.2, 3.2)
                self.mirando = 0.0
                if projeteis_inimigos is not None:
                    from pooling import PoolProjeteis
                    vel_flecha = ate_jogador.normalize() * 140.0
                    projeteis_inimigos.append(PoolProjeteis.obter_flecha(self.rect.center, vel_flecha, dano=1))
        else:
            self.anim += dt * 3.0
            self.tempo_direcao -= dt
            if self.tempo_direcao <= 0:
                self._nova_direcao()
            if self.mover(self.direcao * 22.0 * dt, nivel):
                self._nova_direcao()

    def desenhar(self, tela, camera, gfx, fonte=None):
        quadro = 1 if self.mirando > 0 else (0 if int(self.anim) % 2 == 0 else 1)
        img = (gfx.zumbi_arqueiro_branco if self.piscar > 0 else gfx.zumbi_arqueiro)[quadro]
        self.desenhar_sombra(tela, camera, gfx)
        r = img.get_rect(midbottom=(self.rect.centerx, self.rect.bottom + 1))
        pos_tela = camera.aplicar(r)
        tela.blit(img, pos_tela)

        # Brilho de mira no arco
        if self.mirando > 0:
            brilho_pos = (pos_tela.centerx + 4, pos_tela.centery - 1)
            pygame.draw.circle(tela, (255, 60, 60), brilho_pos, 2)

        if self.congelado > 0:
            gelo = pygame.Surface(pos_tela.size, pygame.SRCALPHA)
            gelo.fill((110, 235, 255, 110))
            tela.blit(gelo, pos_tela)


class Troll(Inimigo):
    """Troll selvagem: enorme, resistente (8 HP), causa tremor no chão e 2 de dano."""

    def __init__(self, x, y):
        super().__init__(x, y, 18, 12, vida_max=8, xp=70, dano=2, cor_particulas=CORES_TROLL)
        self.cooldown_esmagar = 2.0
        self.preparando_esmagar = 0.0

    def atualizar(self, dt, nivel, jogador, projeteis_inimigos=None, particulas=None):
        self.piscar = max(0.0, self.piscar - dt)
        self.atordoado = max(0.0, self.atordoado - dt)
        self.congelado = max(0.0, self.congelado - dt)
        self.atualizar_base(dt, nivel)

        if self.atualizar_empurrao(dt, nivel) or self.atordoado > 0 or self.congelado > 0:
            return

        ate_jogador = pygame.Vector2(jogador.rect.center) - pygame.Vector2(self.rect.center)
        distancia = ate_jogador.length()

        if self.preparando_esmagar > 0:
            self.preparando_esmagar -= dt
            if self.preparando_esmagar <= 0:
                # Esmaga o chão!
                if distancia < 38 and not jogador.no_ar:
                    jogador.levar_dano(2, self.rect.center)
                    jogador.empurrar(self.rect.center, 220, 0.25)
                self.cooldown_esmagar = random.uniform(2.5, 3.8)
            return

        self.cooldown_esmagar = max(0.0, self.cooldown_esmagar - dt)

        if 0 < distancia < 100:
            if distancia < 36 and self.cooldown_esmagar <= 0:
                # Inicia telegrafia do golpe com a clava
                self.preparando_esmagar = 0.55
                return

            self.anim += dt * 4.5
            self.mover(ate_jogador.normalize() * 38.0 * dt, nivel)
        else:
            self.anim += dt * 2.5
            self.tempo_direcao -= dt
            if self.tempo_direcao <= 0:
                self._nova_direcao()
            if self.mover(self.direcao * 20.0 * dt, nivel):
                self._nova_direcao()

    def desenhar(self, tela, camera, gfx, fonte=None):
        quadro = 1 if self.preparando_esmagar > 0 else (0 if int(self.anim) % 2 == 0 else 1)
        img = (gfx.troll_branco if self.piscar > 0 else gfx.troll)[quadro]
        sombra = pygame.Surface((22, 7), pygame.SRCALPHA)
        pygame.draw.ellipse(sombra, (0, 0, 0, 75), sombra.get_rect())
        tela.blit(sombra, camera.aplicar_pos((self.rect.centerx - 11, self.rect.bottom - 3)))
        r = img.get_rect(midbottom=(self.rect.centerx, self.rect.bottom + 1))
        pos_tela = camera.aplicar(r)
        tela.blit(img, pos_tela)

        # Círculo vermelho de perigo telegrafado no chão antes do impacto
        if self.preparando_esmagar > 0:
            centro_tela = camera.aplicar_ponto(self.rect.center)
            raio_aviso = int(32 * (1.0 - self.preparando_esmagar / 0.55))
            aviso = pygame.Surface((72, 72), pygame.SRCALPHA)
            pygame.draw.circle(aviso, (255, 80, 60, 90), (36, 36), max(4, raio_aviso))
            pygame.draw.circle(aviso, (255, 220, 100, 180), (36, 36), 36, 1)
            tela.blit(aviso, (centro_tela[0] - 36, centro_tela[1] - 36))

        if self.congelado > 0:
            gelo = pygame.Surface(pos_tela.size, pygame.SRCALPHA)
            gelo.fill((110, 235, 255, 110))
            tela.blit(gelo, pos_tela)


CRIADORES_INIMIGOS = {
    "slime": Slime,
    "slime_verde": SlimeVerde,
    "duende": Duende,
    "zumbi_arqueiro": ZumbiArqueiro,
    "troll": Troll,
}


def criar_inimigo(tipo, x, y):
    """Instancia o inimigo apropriado a partir de uma chave textual."""
    classe = CRIADORES_INIMIGOS.get(tipo, Slime)
    return classe(x, y)
