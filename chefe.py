"""Módulo de Chefões e Chefe Final (15 Chefes + A Entidade Maligna).

Inclui IA, animações procedurais em 16-bits, ataques telegrafados,
projéteis, barras de vida e o Boss Rush do Salão do Trono.
"""
import math
import random

import pygame

from entidade import Entidade
from render3d import criar_cristal_3d
from settings import ALTURA, LARGURA, TILE
from ui import AMARELO, BRANCO, CINZA, desenhar_texto

VERMELHO = (245, 65, 75)


class ProjetilChefe:
    """Projétil disparado pelos chefões contra o jogador."""

    def __init__(self, pos, vel, dano=1, raio=4, cor=(255, 90, 60), cor_borda=(160, 20, 30), duracao=4.5):
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(vel)
        self.dano = dano
        self.raio = raio
        self.cor = cor
        self.cor_borda = cor_borda
        self.vida = duracao
        self.tempo = 0.0

    @property
    def rect(self):
        r = pygame.Rect(0, 0, self.raio * 2, self.raio * 2)
        r.center = (round(self.pos.x), round(self.pos.y))
        return r

    def atualizar(self, dt, nivel):
        self.tempo += dt
        self.vida -= dt
        if self.vida <= 0:
            return False
        self.pos += self.vel * dt
        cx, cy = int(self.pos.x // TILE), int(self.pos.y // TILE)
        if not nivel.dentro(cx, cy) or nivel.solido(cx, cy):
            return False
        return True

    def desenhar(self, tela, camera):
        ox, oy = camera.offset
        cx, cy = round(self.pos.x - ox), round(self.pos.y - oy)
        pygame.draw.circle(tela, self.cor_borda, (cx, cy), self.raio + 1)
        pygame.draw.circle(tela, self.cor, (cx, cy), self.raio)
        pygame.draw.circle(tela, (255, 255, 240), (cx - 1, cy - 1), max(1, self.raio // 2))


class Chefe(Entidade):
    """Classe base para todos os chefões do jogo."""

    def __init__(self, x, y, larg_hitbox, alt_hitbox, id_chefe, nome, titulo, vida_max, cor_aura=(255, 210, 80), nivel_minimo=1):
        super().__init__(x, y, larg_hitbox, alt_hitbox)
        self.id_chefe = id_chefe
        self.nome = nome
        self.titulo = titulo
        self.vida_base = vida_max
        self.vida_max = vida_max
        self.vida = vida_max
        self.cor_aura = cor_aura
        self.nivel_minimo = nivel_minimo
        self.nivel_chefe = nivel_minimo
        self.fantasma = False  # True quando invocado no Boss Rush do Salão do Trono
        self.piscar = 0.0
        self.atordoado = 0.0
        self.congelado = 0.0
        self.ultimo_golpe = -1
        self.tempo_vida = 0.0
        self.tempo_ataque = 1.0
        self.ataque_em_curso = None
        self.estado_ia = "passeio"
        self.direcao_olhar = "baixo"
        self.velocidade_base = 45.0
        self.xp_recompensa = 120
        self.dano_contato = 2
        self.fator_poder = 1.0
        self.morrendo = False
        self.tempo_morte = 0.0

    def aplicar_escalonamento(self, rpg):
        """Escalona a vida e o poder do chefe de acordo com o nível e progressão do herói."""
        self.nivel_chefe = max(self.nivel_minimo, rpg.nivel)
        # Mais vida e agressividade com o nível do herói
        crescimento = (self.nivel_chefe - 1) * 0.16 + len(rpg.desbloqueadas) * 0.05
        mult_vida = 1.0 + crescimento * 0.8
        self.vida_max = int(self.vida_base * mult_vida)
        self.vida = self.vida_max
        self.dano_contato = max(2, 1 + self.nivel_chefe // 5)
        self.fator_poder = min(1.65, 1.0 + crescimento * 0.22)

    @property
    def vivo(self):
        return self.vida > 0

    def receber_golpe(self, golpe_id, origem, dano=1):
        if golpe_id == self.ultimo_golpe or self.morrendo:
            return False
        self.ultimo_golpe = golpe_id
        self.vida = max(0, self.vida - dano)
        self.piscar = 0.18
        self.atordoado = 0.15
        self.empurrar(origem, 85, 0.12)
        self.deformar(1.22, 0.78)
        if self.vida <= 0:
            self.morrendo = True
            self.tempo_morte = 1.2
        return True

    def atualizar_chefe(self, dt, nivel, jogador, projeteis, particulas, ondas, audio):
        self.tempo_vida += dt
        self.piscar = max(0.0, self.piscar - dt)
        self.atordoado = max(0.0, self.atordoado - dt)
        self.congelado = max(0.0, self.congelado - dt)
        self.atualizar_base(dt, nivel)

        if self.morrendo:
            self.tempo_morte -= dt
            if random.random() < 0.35:
                from efeitos import explosao
                cx = self.rect.centerx + random.uniform(-14, 14)
                cy = self.rect.centery + random.uniform(-14, 14)
                particulas += explosao((cx, cy), [(255, 230, 90), (255, 90, 40), (240, 240, 255)], 8)
                if audio and random.random() < 0.2:
                    audio.sfx("hit_inimigo")
            return

        if self.atualizar_empurrao(dt, nivel) or self.congelado > 0:
            return

        ate_j = pygame.Vector2(jogador.rect.center) - pygame.Vector2(self.rect.center)
        if abs(ate_j.x) > abs(ate_j.y):
            self.direcao_olhar = "direita" if ate_j.x > 0 else "esquerda"
        else:
            self.direcao_olhar = "baixo" if ate_j.y > 0 else "cima"

        self.atualizar_comportamento(dt, nivel, jogador, ate_j, projeteis, particulas, ondas, audio)

    def atualizar_comportamento(self, dt, nivel, jogador, ate_j, projeteis, particulas, ondas, audio):
        """Sobrescrito por cada chefe com seus padrões únicos de ataque."""
        pass

    def desenhar_chefe(self, tela, camera, gfx, fonte):
        """Desenho 16-bits customizado do chefe."""
        pass

    def desenhar(self, tela, camera, gfx, fonte=None):
        self.desenhar_sombra(tela, camera, gfx)
        if self.piscar > 0 and int(self.piscar * 24) % 2 == 0:
            # Efeito piscar de dano (flash branco/dourado)
            return
        self.desenhar_chefe(tela, camera, gfx, fonte)

        if self.fantasma:
            # Aura etérea púrpura se for versão fantasma do Boss Rush
            ox, oy = camera.offset
            pos_t = camera.aplicar(self.rect.inflate(12, 12))
            aura = pygame.Surface(pos_t.size, pygame.SRCALPHA)
            pygame.draw.ellipse(aura, (180, 50, 240, 85), aura.get_rect(), 2)
            tela.blit(aura, pos_t)

    def desenhar_barra_vida_hud(self, tela, fonte):
        """Desenha barra de vida de chefe no topo da tela com moldura 16-bits."""
        larg_barra = 160
        alt_barra = 8
        x = (LARGURA - larg_barra) // 2
        y = 6

        # Fundo e moldura
        pygame.draw.rect(tela, (14, 10, 22), (x - 2, y - 2, larg_barra + 4, alt_barra + 4))
        pygame.draw.rect(tela, (215, 175, 65), (x - 2, y - 2, larg_barra + 4, alt_barra + 4), 1)

        # Preenchimento de vida
        prop = max(0.0, min(1.0, self.vida / max(1, self.vida_max)))
        if prop > 0:
            larg_preench = round((larg_barra) * prop)
            cor_vida = (245, 65, 75) if prop < 0.3 else ((255, 180, 50) if prop < 0.6 else (225, 45, 65))
            pygame.draw.rect(tela, cor_vida, (x, y, larg_preench, alt_barra))
            pygame.draw.line(tela, (255, 215, 160), (x, y + 1), (x + larg_preench - 1, y + 1))

        # Nome e título do chefe com indicador de nível escalonado
        rotulo = f"👑 {self.nome} [Nv. {self.nivel_chefe}] - {self.titulo}"
        desenhar_texto(tela, fonte, rotulo, (LARGURA // 2, y + alt_barra + 7), AMARELO, centro=True)


# =====================================================================
# 15 CHEFÕES ÚNICOS DO MUNDO
# =====================================================================

class ReiSlime(Chefe):
    """Chefe 1 (Covil do Rei Slime): Slime Real Gigante com coroa rubi e saltos sísmicos."""

    def __init__(self, x, y, fantasma=False):
        super().__init__(x, y, 24, 18, "rei_slime", "Rei Slime", "Soberano dos Bosques", 26, (120, 215, 255), nivel_minimo=1)
        self.fantasma = fantasma
        self.velocidade_base = 55.0
        self.fase_salto = 0.0

    def atualizar_comportamento(self, dt, nivel, jogador, ate_j, projeteis, particulas, ondas, audio):
        from rpg import OndaMagica
        self.fase_salto += dt * (4.5 * self.fator_poder)
        dist = ate_j.length()

        self.tempo_ataque -= dt
        if self.tempo_ataque <= 0:
            self.tempo_ataque = random.uniform(2.4, 3.4) / self.fator_poder
            # Salto sísmico com onda de choque
            self.pular(155.0)
            if audio:
                audio.sfx("rugido_chefe")

        if self.acabou_de_pousar:
            ondas.append(OndaMagica(self.rect.center, 44, (110, 215, 255), 0.45))
            if audio:
                audio.sfx("impacto_pesado")
            # Dispara 6 projéteis de gosma em círculo
            for ang in range(0, 360, 60):
                rad = math.radians(ang)
                vel = pygame.Vector2(math.cos(rad), math.sin(rad)) * (95.0 * self.fator_poder)
                projeteis.append(ProjetilChefe(self.rect.center, vel, dano=self.dano_contato, raio=4, cor=(75, 175, 245)))

        if dist > 8 and self.no_ar:
            self.mover(ate_j.normalize() * (self.velocidade_base * 1.5 * dt * self.fator_poder), nivel)
        elif dist > 8:
            self.mover(ate_j.normalize() * (self.velocidade_base * 0.6 * dt), nivel)

    def desenhar_chefe(self, tela, camera, gfx, fonte):
        ox, oy = camera.offset
        cx, cy = self.rect.centerx - ox, self.rect.bottom - oy - round(self.z)
        onda = math.sin(self.fase_salto)
        larg = 32 + round(onda * 4)
        alt = 24 - round(onda * 4)

        # Manto real de veludo na base
        rect_manto = pygame.Rect(0, 0, larg + 6, 6)
        rect_manto.midbottom = (cx, cy + 1)
        pygame.draw.ellipse(tela, (130, 24, 40), rect_manto)
        pygame.draw.ellipse(tela, (215, 180, 50), rect_manto, 1)

        # Corpo do Slime Real
        rect_corpo = pygame.Rect(0, 0, larg, alt)
        rect_corpo.midbottom = (cx, cy)
        cor_slime = (65, 145, 235) if not self.fantasma else (145, 65, 225)
        cor_slime_esc = (35, 90, 180) if not self.fantasma else (90, 30, 160)
        pygame.draw.ellipse(tela, (20, 16, 36), rect_corpo.inflate(4, 4))
        pygame.draw.ellipse(tela, cor_slime_esc, rect_corpo)
        pygame.draw.ellipse(tela, cor_slime, rect_corpo.inflate(-4, -4))
        # Brilho de gelatina especular
        pygame.draw.ellipse(tela, (180, 230, 255), (cx - larg // 3, cy - alt + 4, larg // 2, 6))

        # Olhos reais com expressão majestosa
        pygame.draw.circle(tela, (255, 255, 255), (cx - 6, cy - alt // 2), 3)
        pygame.draw.circle(tela, (255, 255, 255), (cx + 6, cy - alt // 2), 3)
        pygame.draw.circle(tela, (18, 22, 40), (cx - 5, cy - alt // 2), 1)
        pygame.draw.circle(tela, (18, 22, 40), (cx + 7, cy - alt // 2), 1)

        # Coroa dourada real com 3 rubis cintilantes
        coroa_y = rect_corpo.top - 6
        pts_coroa = [
            (cx - 10, coroa_y + 5), (cx - 10, coroa_y - 4),
            (cx - 5, coroa_y + 1), (cx, coroa_y - 7),
            (cx + 5, coroa_y + 1), (cx + 10, coroa_y - 4),
            (cx + 10, coroa_y + 5),
        ]
        pygame.draw.polygon(tela, (245, 215, 65), pts_coroa)
        pygame.draw.polygon(tela, (40, 24, 12), pts_coroa, 1)
        pygame.draw.circle(tela, (245, 45, 65), (cx - 7, coroa_y), 2)
        pygame.draw.circle(tela, (255, 235, 120), (cx, coroa_y - 3), 2)
        pygame.draw.circle(tela, (245, 45, 65), (cx + 7, coroa_y), 2)


class GolemPedra(Chefe):
    """Chefe 2 (Câmara do Golem Ancestral): Titã de pedra com runas celestes e socos de terra."""

    def __init__(self, x, y, fantasma=False):
        super().__init__(x, y, 26, 26, "golem_pedra", "Golem de Pedra", "Guardião das Ruínas", 32, (150, 165, 190), nivel_minimo=2)
        self.fantasma = fantasma

    def atualizar_comportamento(self, dt, nivel, jogador, ate_j, projeteis, particulas, ondas, audio):
        from rpg import OndaMagica
        dist = ate_j.length()
        self.tempo_ataque -= dt

        if self.tempo_ataque <= 0:
            self.tempo_ataque = random.uniform(2.8, 3.8) / self.fator_poder
            # Soco no chão com estacas em 4 direções
            ondas.append(OndaMagica(self.rect.center, 42, (180, 175, 160), 0.4))
            if audio:
                audio.sfx("impacto_pesado")
            for dir_v in (pygame.Vector2(1, 0), pygame.Vector2(-1, 0), pygame.Vector2(0, 1), pygame.Vector2(0, -1)):
                projeteis.append(ProjetilChefe(self.rect.center, dir_v * (115.0 * self.fator_poder), dano=self.dano_contato, raio=5, cor=(145, 140, 135)))

        if dist > 14:
            self.mover(ate_j.normalize() * (self.velocidade_base * dt * self.fator_poder), nivel)

    def desenhar_chefe(self, tela, camera, gfx, fonte):
        ox, oy = camera.offset
        cx, cy = self.rect.centerx - ox, self.rect.bottom - oy
        r = pygame.Rect(0, 0, 28, 30)
        r.midbottom = (cx, cy)
        # Ombros de megálito e cabeça de pedra
        pygame.draw.rect(tela, (25, 24, 32), r.inflate(4, 4))
        pygame.draw.rect(tela, (95, 100, 115), r)
        pygame.draw.rect(tela, (135, 142, 160), r.inflate(-4, -4))
        # Ombreiras de pedra
        pygame.draw.rect(tela, (75, 80, 95), (r.left - 4, r.top + 2, 5, 12))
        pygame.draw.rect(tela, (75, 80, 95), (r.right - 1, r.top + 2, 5, 12))
        # Musgo e fendas antigas
        pygame.draw.rect(tela, (65, 125, 60), (r.left + 3, r.bottom - 8, 4, 3))
        # Runas brilhantes esculpidas
        cor_runa = (95, 235, 255) if not self.fantasma else (215, 95, 255)
        pygame.draw.circle(tela, cor_runa, (cx, r.centery - 3), 4)
        pygame.draw.line(tela, cor_runa, (cx, r.centery - 3), (cx, r.bottom - 4), 2)
        pygame.draw.line(tela, cor_runa, (cx - 6, r.centery + 3), (cx + 6, r.centery + 3), 2)
        # Olhos de energia rúnica
        pygame.draw.rect(tela, cor_runa, (cx - 6, r.top + 6, 3, 2))
        pygame.draw.rect(tela, cor_runa, (cx + 3, r.top + 6, 3, 2))


class SerpenteDunas(Chefe):
    """Chefe 3 (Fosso das Dunas): Leviatã arenoso com baforada de fogo e areia abrasiva."""

    def __init__(self, x, y, fantasma=False):
        super().__init__(x, y, 22, 22, "serpente_dunas", "Serpente das Dunas", "Terror do Deserto", 28, (245, 190, 85), nivel_minimo=3)
        self.fantasma = fantasma
        self.submersa = 0.0

    def atualizar_comportamento(self, dt, nivel, jogador, ate_j, projeteis, particulas, ondas, audio):
        self.tempo_ataque -= dt
        if self.tempo_ataque <= 0:
            self.tempo_ataque = random.uniform(3.0, 4.0) / self.fator_poder
            if audio:
                audio.sfx("rugido_chefe")
            # Dispara 3 bolas de fogo e areia em cone
            dir_base = ate_j.normalize() if ate_j.length() > 0 else pygame.Vector2(1, 0)
            for ang in (-25, 0, 25):
                vel = dir_base.rotate(ang) * (130.0 * self.fator_poder)
                projeteis.append(ProjetilChefe(self.rect.center, vel, dano=self.dano_contato, raio=5, cor=(255, 130, 45)))

        if ate_j.length() > 16:
            self.mover(ate_j.normalize() * (self.velocidade_base * 1.25 * dt * self.fator_poder), nivel)

    def desenhar_chefe(self, tela, camera, gfx, fonte):
        ox, oy = camera.offset
        cx, cy = self.rect.centerx - ox, self.rect.bottom - oy
        r = pygame.Rect(0, 0, 26, 28)
        r.midbottom = (cx, cy)
        pygame.draw.ellipse(tela, (28, 20, 16), r.inflate(3, 3))
        pygame.draw.ellipse(tela, (185, 115, 45), r)
        pygame.draw.ellipse(tela, (235, 175, 85), r.inflate(-4, -4))
        # Escamas de serpente ósseas
        for sy in range(r.top + 4, r.bottom - 4, 5):
            pygame.draw.arc(tela, (140, 80, 25), (r.left + 4, sy, 18, 6), 0, math.pi, 2)
        # Olhos dourados reptilianos com fenda negra
        pygame.draw.circle(tela, (255, 240, 90), (cx - 5, r.top + 8), 3)
        pygame.draw.circle(tela, (255, 240, 90), (cx + 5, r.top + 8), 3)
        pygame.draw.line(tela, (20, 14, 10), (cx - 5, r.top + 6), (cx - 5, r.top + 10), 1)
        pygame.draw.line(tela, (20, 14, 10), (cx + 5, r.top + 6), (cx + 5, r.top + 10), 1)


class ColossoSolar(Chefe):
    """Chefe 4 (Altar Solar das Chamas): Guerreiro dourado com feixe de chamas e disco solar."""

    def __init__(self, x, y, fantasma=False):
        super().__init__(x, y, 24, 28, "colosso_solar", "Colosso Solar", "Campeão do Sol", 32, (255, 220, 70), nivel_minimo=4)
        self.fantasma = fantasma

    def atualizar_comportamento(self, dt, nivel, jogador, ate_j, projeteis, particulas, ondas, audio):
        self.tempo_ataque -= dt
        if self.tempo_ataque <= 0:
            self.tempo_ataque = random.uniform(2.6, 3.6) / self.fator_poder
            if audio:
                audio.sfx("laser")
            # Explosão solar em 8 direções
            for ang in range(0, 360, 45):
                rad = math.radians(ang)
                vel = pygame.Vector2(math.cos(rad), math.sin(rad)) * (120.0 * self.fator_poder)
                projeteis.append(ProjetilChefe(self.rect.center, vel, dano=self.dano_contato, raio=4, cor=(255, 225, 80)))

        if ate_j.length() > 20:
            self.mover(ate_j.normalize() * (self.velocidade_base * 0.95 * dt * self.fator_poder), nivel)

    def desenhar_chefe(self, tela, camera, gfx, fonte):
        ox, oy = camera.offset
        cx, cy = self.rect.centerx - ox, self.rect.bottom - oy
        r = pygame.Rect(0, 0, 26, 32)
        r.midbottom = (cx, cy)
        # Disco solar giratório às costas
        ang_sol = self.tempo_vida * 2.0
        for i in range(8):
            a = ang_sol + i * (math.pi / 4)
            px = cx + round(math.cos(a) * 16)
            py = (r.centery - 4) + round(math.sin(a) * 16)
            pygame.draw.line(tela, (255, 220, 60), (cx, r.centery - 4), (px, py), 2)

        # Armadura dourada real
        pygame.draw.rect(tela, (36, 24, 12), r.inflate(2, 2))
        pygame.draw.rect(tela, (215, 160, 45), r)
        pygame.draw.rect(tela, (255, 215, 95), r.inflate(-4, -4))
        # Escudo solar central com gema incandescente
        pygame.draw.circle(tela, (255, 80, 35), (cx, r.centery), 7)
        pygame.draw.circle(tela, (255, 245, 140), (cx, r.centery), 4)


class BruxaBrumas(Chefe):
    """Chefe 5 (Antro da Bruxa): Feiticeira com orbes venenosos e névoa espectral."""

    def __init__(self, x, y, fantasma=False):
        super().__init__(x, y, 20, 24, "bruxa_brumas", "Bruxa das Brumas", "Senhora dos Pântanos", 28, (140, 65, 220), nivel_minimo=5)
        self.fantasma = fantasma

    def atualizar_comportamento(self, dt, nivel, jogador, ate_j, projeteis, particulas, ondas, audio):
        self.tempo_ataque -= dt
        if self.tempo_ataque <= 0:
            self.tempo_ataque = random.uniform(2.3, 3.3) / self.fator_poder
            if audio:
                audio.sfx("magia_raio")
            # 4 orbes venenosos teleguiados lentos
            dir_v = ate_j.normalize() if ate_j.length() > 0 else pygame.Vector2(0, 1)
            for a in (-32, -10, 10, 32):
                projeteis.append(ProjetilChefe(self.rect.center, dir_v.rotate(a) * (90.0 * self.fator_poder), dano=self.dano_contato, raio=4, cor=(165, 70, 245)))

        if ate_j.length() > 32:
            self.mover(ate_j.normalize() * (self.velocidade_base * dt * self.fator_poder), nivel)

    def desenhar_chefe(self, tela, camera, gfx, fonte):
        ox, oy = camera.offset
        cx, cy = self.rect.centerx - ox, self.rect.bottom - oy
        r = pygame.Rect(0, 0, 22, 28)
        r.midbottom = (cx, cy)
        # Névoa escura nos pés
        nevoa_r = pygame.Rect(0, 0, 26, 6)
        nevoa_r.midbottom = (cx, cy)
        pygame.draw.ellipse(tela, (45, 20, 65), nevoa_r)
        # Manto e chapéu pontudo de bruxa
        pygame.draw.polygon(tela, (42, 18, 58), [(cx - 10, cy), (cx + 10, cy), (cx, r.top + 8)])
        pygame.draw.polygon(tela, (26, 10, 36), [(cx - 11, r.top + 8), (cx + 11, r.top + 8), (cx, r.top - 7)])
        pygame.draw.circle(tela, (215, 110, 255), (cx, r.top + 8), 3)
        # Cajado de madeira com orbe venenoso
        pygame.draw.line(tela, (110, 75, 45), (cx + 9, cy), (cx + 13, r.top - 4), 2)
        pygame.draw.circle(tela, (110, 255, 150), (cx + 13, r.top - 6), 3)


class CeifadorEspectral(Chefe):
    """Chefe 6 (Sepulcro Espectral): Espectro com foice das almas e lâminas cortantes."""

    def __init__(self, x, y, fantasma=False):
        super().__init__(x, y, 22, 26, "ceifador_espectral", "Ceifador Espectral", "Ceifador de Almas", 30, (90, 220, 235), nivel_minimo=6)
        self.fantasma = fantasma

    def atualizar_comportamento(self, dt, nivel, jogador, ate_j, projeteis, particulas, ondas, audio):
        from rpg import OndaMagica
        self.tempo_ataque -= dt
        if self.tempo_ataque <= 0:
            self.tempo_ataque = random.uniform(2.3, 3.2) / self.fator_poder
            if audio:
                audio.sfx("magia_corte")
            ondas.append(OndaMagica(self.rect.center, 46, (90, 225, 240), 0.35))
            dir_v = ate_j.normalize() if ate_j.length() > 0 else pygame.Vector2(0, 1)
            projeteis.append(ProjetilChefe(self.rect.center, dir_v * (145.0 * self.fator_poder), dano=self.dano_contato, raio=5, cor=(120, 245, 255)))

        if ate_j.length() > 14:
            self.mover(ate_j.normalize() * (self.velocidade_base * 1.15 * dt * self.fator_poder), nivel)

    def desenhar_chefe(self, tela, camera, gfx, fonte):
        ox, oy = camera.offset
        cx, cy = self.rect.centerx - ox, self.rect.bottom - oy
        r = pygame.Rect(0, 0, 24, 30)
        r.midbottom = (cx, cy)
        # Capuz e túnica rasgada
        pygame.draw.polygon(tela, (16, 18, 28), [(cx - 12, cy), (cx + 12, cy), (cx, r.top)])
        pygame.draw.polygon(tela, (28, 32, 48), [(cx - 9, cy - 2), (cx + 9, cy - 2), (cx, r.top + 3)])
        # Olhos espectrais azul-celestes
        pygame.draw.circle(tela, (110, 240, 255), (cx - 3, r.top + 8), 2)
        pygame.draw.circle(tela, (110, 240, 255), (cx + 3, r.top + 8), 2)
        # Foice espectral das almas
        pygame.draw.line(tela, (90, 70, 50), (cx + 8, cy), (cx + 14, r.top - 6), 2)
        pygame.draw.arc(tela, (120, 245, 255), (cx + 6, r.top - 12, 16, 16), 0, math.pi, 3)


class LeviataAquatico(Chefe):
    """Chefe 7 (Abismo Aquático): Serpente marítima com jatos d'água perfurantes."""

    def __init__(self, x, y, fantasma=False):
        super().__init__(x, y, 26, 22, "leviata_aquatico", "Leviatã Aquático", "Lorde das Marés", 34, (60, 160, 255), nivel_minimo=7)
        self.fantasma = fantasma

    def atualizar_comportamento(self, dt, nivel, jogador, ate_j, projeteis, particulas, ondas, audio):
        self.tempo_ataque -= dt
        if self.tempo_ataque <= 0:
            self.tempo_ataque = random.uniform(2.6, 3.6) / self.fator_poder
            if audio:
                audio.sfx("nado")
            dir_v = ate_j.normalize() if ate_j.length() > 0 else pygame.Vector2(1, 0)
            for a in (-22, 0, 22):
                projeteis.append(ProjetilChefe(self.rect.center, dir_v.rotate(a) * (135.0 * self.fator_poder), dano=self.dano_contato, raio=5, cor=(90, 195, 255)))

        if ate_j.length() > 16:
            self.mover(ate_j.normalize() * (self.velocidade_base * dt * self.fator_poder), nivel)

    def desenhar_chefe(self, tela, camera, gfx, fonte):
        ox, oy = camera.offset
        cx, cy = self.rect.centerx - ox, self.rect.bottom - oy
        r = pygame.Rect(0, 0, 30, 26)
        r.midbottom = (cx, cy)
        # Redemoinho de água na base
        pygame.draw.ellipse(tela, (30, 80, 140, 150), (cx - 16, cy - 6, 32, 10))
        # Corpo de dragão aquático
        pygame.draw.ellipse(tela, (14, 28, 54), r.inflate(2, 2))
        pygame.draw.ellipse(tela, (42, 115, 205), r)
        pygame.draw.ellipse(tela, (85, 175, 255), r.inflate(-6, -6))
        # Barbatanas dorsais luminosas
        pygame.draw.polygon(tela, (110, 235, 255), [(cx, r.top - 4), (cx - 6, r.top + 4), (cx + 6, r.top + 4)])
        # Olhos bioluminescentes
        pygame.draw.circle(tela, (210, 250, 255), (cx - 6, r.top + 7), 2)
        pygame.draw.circle(tela, (210, 250, 255), (cx + 6, r.top + 7), 2)


class GuardiaoDiamante(Chefe):
    """Chefe 8 (Núcleo de Cristal): Prisma geométrico que refrata feixes laser."""

    def __init__(self, x, y, fantasma=False):
        super().__init__(x, y, 24, 24, "guardiao_diamante", "Guardião dos Cristais", "Prisma Eterno", 32, (180, 245, 255), nivel_minimo=8)
        self.fantasma = fantasma

    def atualizar_comportamento(self, dt, nivel, jogador, ate_j, projeteis, particulas, ondas, audio):
        self.tempo_ataque -= dt
        if self.tempo_ataque <= 0:
            self.tempo_ataque = random.uniform(2.8, 3.8) / self.fator_poder
            if audio:
                audio.sfx("laser")
            # 6 feixes de cristal prismáticos
            for ang in range(0, 360, 60):
                rad = math.radians(ang + self.tempo_vida * 30)
                vel = pygame.Vector2(math.cos(rad), math.sin(rad)) * (115.0 * self.fator_poder)
                projeteis.append(ProjetilChefe(self.rect.center, vel, dano=self.dano_contato, raio=4, cor=(215, 245, 255)))

        if ate_j.length() > 22:
            self.mover(ate_j.normalize() * (self.velocidade_base * 0.85 * dt * self.fator_poder), nivel)

    def desenhar_chefe(self, tela, camera, gfx, fonte):
        ox, oy = camera.offset
        cx, cy = self.rect.centerx - ox, self.rect.bottom - oy
        cristal = criar_cristal_3d(cx, cy - 12, z_base=6.0, raio=9.0, altura=13.0, cor=(140, 220, 255), cor_borda=(40, 80, 130))
        cristal.atualizar(self.tempo_vida * 2.2)
        cristal.desenhar(tela, 0, 0, self.tempo_vida)


class TrollRochas(Chefe):
    """Chefe 9 (Covil do Troll): Gigante das cavernas com clava pesada e tremor de terra."""

    def __init__(self, x, y, fantasma=False):
        super().__init__(x, y, 28, 26, "troll_rochas", "Troll das Cavernas", "Bruto das Montanhas", 36, (185, 130, 80), nivel_minimo=9)
        self.fantasma = fantasma

    def atualizar_comportamento(self, dt, nivel, jogador, ate_j, projeteis, particulas, ondas, audio):
        from rpg import OndaMagica
        self.tempo_ataque -= dt
        if self.tempo_ataque <= 0:
            self.tempo_ataque = random.uniform(3.0, 4.0) / self.fator_poder
            if audio:
                audio.sfx("impacto_pesado")
            ondas.append(OndaMagica(self.rect.center, 48, (195, 145, 90), 0.45))
            dir_v = ate_j.normalize() if ate_j.length() > 0 else pygame.Vector2(0, 1)
            projeteis.append(ProjetilChefe(self.rect.center, dir_v * (110.0 * self.fator_poder), dano=self.dano_contato, raio=6, cor=(165, 115, 75)))

        if ate_j.length() > 14:
            self.mover(ate_j.normalize() * (self.velocidade_base * dt * self.fator_poder), nivel)

    def desenhar_chefe(self, tela, camera, gfx, fonte):
        ox, oy = camera.offset
        cx, cy = self.rect.centerx - ox, self.rect.bottom - oy
        r = pygame.Rect(0, 0, 30, 30)
        r.midbottom = (cx, cy)
        # Corpo corpulento de pedra e pelo
        pygame.draw.rect(tela, (36, 24, 16), r.inflate(4, 4))
        pygame.draw.rect(tela, (140, 95, 60), r)
        pygame.draw.rect(tela, (175, 125, 85), r.inflate(-4, -4))
        # Presas de javali e olhos coléricos
        pygame.draw.circle(tela, (255, 60, 40), (cx - 5, r.top + 8), 2)
        pygame.draw.circle(tela, (255, 60, 40), (cx + 5, r.top + 8), 2)
        # Clava colossal com espinhos
        pygame.draw.line(tela, (75, 45, 25), (cx + 13, cy - 2), (cx + 19, cy - 28), 4)
        pygame.draw.circle(tela, (120, 120, 130), (cx + 19, cy - 28), 5)


class YetiGlacial(Chefe):
    """Chefe 10 (Caverna Glacial do Yeti): Besta albina que congela o ar e atira estacas de gelo."""

    def __init__(self, x, y, fantasma=False):
        super().__init__(x, y, 26, 26, "yeti_glacial", "Yeti Glacial", "Guardião das Neves", 34, (220, 245, 255), nivel_minimo=10)
        self.fantasma = fantasma

    def atualizar_comportamento(self, dt, nivel, jogador, ate_j, projeteis, particulas, ondas, audio):
        self.tempo_ataque -= dt
        if self.tempo_ataque <= 0:
            self.tempo_ataque = random.uniform(2.6, 3.6) / self.fator_poder
            if audio:
                audio.sfx("magia_gelo")
            dir_v = ate_j.normalize() if ate_j.length() > 0 else pygame.Vector2(0, 1)
            for a in (-35, -15, 0, 15, 35):
                projeteis.append(ProjetilChefe(self.rect.center, dir_v.rotate(a) * (120.0 * self.fator_poder), dano=self.dano_contato, raio=4, cor=(160, 235, 255)))

        if ate_j.length() > 16:
            self.mover(ate_j.normalize() * (self.velocidade_base * dt * self.fator_poder), nivel)

    def desenhar_chefe(self, tela, camera, gfx, fonte):
        ox, oy = camera.offset
        cx, cy = self.rect.centerx - ox, self.rect.bottom - oy
        r = pygame.Rect(0, 0, 28, 30)
        r.midbottom = (cx, cy)
        # Pelagem branca volumosa
        pygame.draw.ellipse(tela, (28, 45, 68), r.inflate(4, 4))
        pygame.draw.ellipse(tela, (230, 242, 255), r)
        pygame.draw.ellipse(tela, (255, 255, 255), r.inflate(-4, -4))
        # Chifres congelados pontiagudos
        pygame.draw.line(tela, (95, 205, 245), (cx - 8, r.top + 4), (cx - 15, r.top - 5), 3)
        pygame.draw.line(tela, (95, 205, 245), (cx + 8, r.top + 4), (cx + 15, r.top - 5), 3)
        # Olhos azuis brilhantes
        pygame.draw.circle(tela, (70, 175, 255), (cx - 5, r.top + 8), 2)
        pygame.draw.circle(tela, (70, 175, 255), (cx + 5, r.top + 8), 2)


class ValquiriaCaida(Chefe):
    """Chefe 11 (Altar da Valquíria): Guerreira alada com lanças de luz sagrada."""

    def __init__(self, x, y, fantasma=False):
        super().__init__(x, y, 22, 26, "valquiria_caida", "Valquíria Sombria", "Juíza Celeste", 36, (255, 235, 120), nivel_minimo=11)
        self.fantasma = fantasma

    def atualizar_comportamento(self, dt, nivel, jogador, ate_j, projeteis, particulas, ondas, audio):
        self.tempo_ataque -= dt
        if self.tempo_ataque <= 0:
            self.tempo_ataque = random.uniform(2.4, 3.4) / self.fator_poder
            if audio:
                audio.sfx("magia_raio")
            dir_v = ate_j.normalize() if ate_j.length() > 0 else pygame.Vector2(0, 1)
            for a in (-25, 0, 25):
                projeteis.append(ProjetilChefe(self.rect.center, dir_v.rotate(a) * (150.0 * self.fator_poder), dano=self.dano_contato, raio=4, cor=(255, 240, 140)))

        if ate_j.length() > 16:
            self.mover(ate_j.normalize() * (self.velocidade_base * 1.2 * dt * self.fator_poder), nivel)

    def desenhar_chefe(self, tela, camera, gfx, fonte):
        ox, oy = camera.offset
        cx, cy = self.rect.centerx - ox, self.rect.bottom - oy
        r = pygame.Rect(0, 0, 24, 30)
        r.midbottom = (cx, cy)
        # Asas angelicais negras e douradas
        bater_asa = math.sin(self.tempo_vida * 6.0) * 4
        pygame.draw.polygon(tela, (36, 18, 45), [(cx - 4, r.top + 8), (cx - 22, r.top - 2 + bater_asa), (cx - 6, cy)])
        pygame.draw.polygon(tela, (36, 18, 45), [(cx + 4, r.top + 8), (cx + 22, r.top - 2 + bater_asa), (cx + 6, cy)])
        # Armadura e elmo com asas
        pygame.draw.rect(tela, (215, 185, 80), r)
        pygame.draw.rect(tela, (255, 235, 140), r.inflate(-4, -4))
        # Lança radiante sagrada
        pygame.draw.line(tela, (255, 245, 180), (cx + 10, cy), (cx + 15, r.top - 8), 2)


class CavaleiroNegro(Chefe):
    """Chefe 12 (Arena do Cavaleiro): Guerreiro blindado com zweihander sombria."""

    def __init__(self, x, y, fantasma=False):
        super().__init__(x, y, 24, 28, "cavaleiro_negro", "Cavaleiro Negro", "Campeão das Trevas", 40, (180, 45, 65), nivel_minimo=12)
        self.fantasma = fantasma

    def atualizar_comportamento(self, dt, nivel, jogador, ate_j, projeteis, particulas, ondas, audio):
        from rpg import OndaMagica
        self.tempo_ataque -= dt
        if self.tempo_ataque <= 0:
            self.tempo_ataque = random.uniform(2.5, 3.5) / self.fator_poder
            if audio:
                audio.sfx("espada")
            ondas.append(OndaMagica(self.rect.center, 46, (220, 50, 75), 0.35))
            dir_v = ate_j.normalize() if ate_j.length() > 0 else pygame.Vector2(1, 0)
            projeteis.append(ProjetilChefe(self.rect.center, dir_v * (155.0 * self.fator_poder), dano=self.dano_contato, raio=5, cor=(235, 45, 65)))

        if ate_j.length() > 14:
            self.mover(ate_j.normalize() * (self.velocidade_base * 1.15 * dt * self.fator_poder), nivel)

    def desenhar_chefe(self, tela, camera, gfx, fonte):
        ox, oy = camera.offset
        cx, cy = self.rect.centerx - ox, self.rect.bottom - oy
        r = pygame.Rect(0, 0, 26, 32)
        r.midbottom = (cx, cy)
        # Capa carmesim tremulando
        pygame.draw.polygon(tela, (175, 28, 42), [(cx - 11, r.top + 6), (cx + 11, r.top + 6), (cx, cy + 3)])
        # Armadura gótica negra
        pygame.draw.rect(tela, (20, 16, 26), r.inflate(2, 2))
        pygame.draw.rect(tela, (42, 36, 52), r)
        # Viseira carmesim ardente
        pygame.draw.line(tela, (255, 45, 65), (cx - 5, r.top + 8), (cx + 5, r.top + 8), 2)
        # Zweihander sombria nas mãos
        pygame.draw.line(tela, (180, 185, 205), (cx + 10, cy), (cx + 16, r.top - 10), 3)


class QuimeraAbissal(Chefe):
    """Chefe 13 (Fosso da Quimera): Monstro tricéfalo com baforada de fogo e veneno."""

    def __init__(self, x, y, fantasma=False):
        super().__init__(x, y, 26, 26, "quimera_abissal", "Quimera Abissal", "Monstro dos Calabouços", 38, (215, 80, 50), nivel_minimo=13)
        self.fantasma = fantasma

    def atualizar_comportamento(self, dt, nivel, jogador, ate_j, projeteis, particulas, ondas, audio):
        self.tempo_ataque -= dt
        if self.tempo_ataque <= 0:
            self.tempo_ataque = random.uniform(2.6, 3.6) / self.fator_poder
            if audio:
                audio.sfx("rugido_chefe")
            dir_v = ate_j.normalize() if ate_j.length() > 0 else pygame.Vector2(0, 1)
            for a in (-30, -10, 10, 30):
                projeteis.append(ProjetilChefe(self.rect.center, dir_v.rotate(a) * (125.0 * self.fator_poder), dano=self.dano_contato, raio=5, cor=(255, 95, 45)))

        if ate_j.length() > 16:
            self.mover(ate_j.normalize() * (self.velocidade_base * dt * self.fator_poder), nivel)

    def desenhar_chefe(self, tela, camera, gfx, fonte):
        ox, oy = camera.offset
        cx, cy = self.rect.centerx - ox, self.rect.bottom - oy
        r = pygame.Rect(0, 0, 28, 30)
        r.midbottom = (cx, cy)
        pygame.draw.ellipse(tela, (42, 18, 16), r.inflate(4, 4))
        pygame.draw.ellipse(tela, (185, 65, 42), r)
        # Cauda de escorpião articulada
        pygame.draw.arc(tela, (130, 32, 22), (cx - 18, r.top - 10, 18, 22), 0, math.pi, 3)
        # Chifres de cabra e juba draconiana
        pygame.draw.line(tela, (65, 45, 35), (cx - 6, r.top + 4), (cx - 12, r.top - 4), 2)
        pygame.draw.line(tela, (65, 45, 35), (cx + 6, r.top + 4), (cx + 12, r.top - 4), 2)


class ArquimagoCorrompido(Chefe):
    """Chefe 14 (Observatório do Arquimago): Sábio das sombras com chuva de raios e esferas místicas."""

    def __init__(self, x, y, fantasma=False):
        super().__init__(x, y, 22, 26, "arquimago", "Arquimago Corrompido", "Grão-Mestre Proibido", 42, (175, 80, 255), nivel_minimo=14)
        self.fantasma = fantasma

    def atualizar_comportamento(self, dt, nivel, jogador, ate_j, projeteis, particulas, ondas, audio):
        self.tempo_ataque -= dt
        if self.tempo_ataque <= 0:
            self.tempo_ataque = random.uniform(2.1, 3.0) / self.fator_poder
            if audio:
                audio.sfx("magia_raio")
            # 8 projéteis arcanos em espiral
            for ang in range(0, 360, 45):
                rad = math.radians(ang + self.tempo_vida * 45)
                vel = pygame.Vector2(math.cos(rad), math.sin(rad)) * (130.0 * self.fator_poder)
                projeteis.append(ProjetilChefe(self.rect.center, vel, dano=self.dano_contato, raio=4, cor=(190, 85, 255)))

        if ate_j.length() > 28:
            self.mover(ate_j.normalize() * (self.velocidade_base * 0.95 * dt * self.fator_poder), nivel)

    def desenhar_chefe(self, tela, camera, gfx, fonte):
        ox, oy = camera.offset
        cx, cy = self.rect.centerx - ox, self.rect.bottom - oy
        r = pygame.Rect(0, 0, 24, 30)
        r.midbottom = (cx, cy)
        # Manto astral com estrelas
        pygame.draw.polygon(tela, (32, 12, 48), [(cx - 11, cy), (cx + 11, cy), (cx, r.top)])
        pygame.draw.circle(tela, (230, 130, 255), (cx + 12, cy - 15), 4)
        pygame.draw.circle(tela, (130, 230, 255), (cx - 12, cy - 15), 4)


class PaladinoJuizo(Chefe):
    """Chefe 15 (Tribunal do Paladino): Guardião divino profanado com martelo do juízo."""

    def __init__(self, x, y, fantasma=False):
        super().__init__(x, y, 26, 28, "paladino_juizo", "Paladino do Juízo", "Guardião do Selo Final", 46, (255, 215, 90), nivel_minimo=15)
        self.fantasma = fantasma

    def atualizar_comportamento(self, dt, nivel, jogador, ate_j, projeteis, particulas, ondas, audio):
        from rpg import OndaMagica
        self.tempo_ataque -= dt
        if self.tempo_ataque <= 0:
            self.tempo_ataque = random.uniform(2.3, 3.2) / self.fator_poder
            if audio:
                audio.sfx("impacto_pesado")
            ondas.append(OndaMagica(self.rect.center, 54, (255, 230, 110), 0.45))
            # 4 feixes de martelo sagrado
            for d in (pygame.Vector2(1, 0), pygame.Vector2(-1, 0), pygame.Vector2(0, 1), pygame.Vector2(0, -1)):
                projeteis.append(ProjetilChefe(self.rect.center, d * (145.0 * self.fator_poder), dano=self.dano_contato, raio=5, cor=(255, 240, 130)))

        if ate_j.length() > 14:
            self.mover(ate_j.normalize() * (self.velocidade_base * dt * self.fator_poder), nivel)

    def desenhar_chefe(self, tela, camera, gfx, fonte):
        ox, oy = camera.offset
        cx, cy = self.rect.centerx - ox, self.rect.bottom - oy
        r = pygame.Rect(0, 0, 28, 32)
        r.midbottom = (cx, cy)
        # Auréola radiante
        pygame.draw.circle(tela, (255, 235, 120), (cx, r.top - 3), 6, 2)
        # Armadura reluzente
        pygame.draw.rect(tela, (48, 38, 22), r.inflate(2, 2))
        pygame.draw.rect(tela, (235, 205, 95), r)
        # Martelo de guerra colossal
        pygame.draw.line(tela, (140, 95, 45), (cx + 13, cy), (cx + 15, r.top - 8), 3)
        pygame.draw.rect(tela, (255, 245, 170), (cx + 10, r.top - 12, 11, 7))


# =====================================================================
# CHEFE FINAL: A ENTIDADE MALIGNA (O SOBERANO DAS TREVAS)
# =====================================================================

class EntidadeMalignaChefe(Chefe):
    """O CHEFE FINAL do jogo no Salão do Trono com 2 Fases dramáticas."""

    def __init__(self, x, y):
        super().__init__(x, y, 38, 34, "entidade_maligna", "A ENTIDADE MALIGNA", "Soberano do Apocalipse", 70, (235, 45, 95), nivel_minimo=15)
        self.fase = 1
        self.timer_magia = 0.5
        self.velocidade_base = 34.0

    def atualizar_comportamento(self, dt, nivel, jogador, ate_j, projeteis, particulas, ondas, audio):
        from rpg import OndaMagica
        dist = ate_j.length()

        # Transição de fase na metade da vida máxima
        if self.fase == 1 and self.vida <= (self.vida_max // 2):
            self.fase = 2
            self.timer_magia = 0.2
            ondas.append(OndaMagica(self.rect.center, 75, (255, 50, 110), 0.6))
            if audio:
                audio.sfx("rugido_chefe")

        self.timer_magia -= dt
        if self.timer_magia <= 0:
            if self.fase == 1:
                self.timer_magia = random.uniform(1.6, 2.4) / self.fator_poder
                if audio:
                    audio.sfx("magia_fogo")
                # Onda quádrupla de fogo abissal teleguiado
                dir_v = ate_j.normalize() if dist > 0 else pygame.Vector2(0, 1)
                for a in (-40, -15, 15, 40):
                    projeteis.append(ProjetilChefe(self.rect.center, dir_v.rotate(a) * (120.0 * self.fator_poder), dano=self.dano_contato, raio=5, cor=(255, 60, 95)))
            else:
                # Fase 2: Chuva infernal em espiral bullet-hell
                self.timer_magia = random.uniform(0.9, 1.5) / self.fator_poder
                if audio:
                    audio.sfx("laser")
                ondas.append(OndaMagica(self.rect.center, 58, (255, 80, 140), 0.4))
                for ang in range(0, 360, 36):
                    rad = math.radians(ang + self.tempo_vida * 60)
                    vel = pygame.Vector2(math.cos(rad), math.sin(rad)) * (135.0 * self.fator_poder)
                    projeteis.append(ProjetilChefe(self.rect.center, vel, dano=self.dano_contato, raio=5, cor=(255, 35, 75)))

        if dist > 24:
            self.mover(ate_j.normalize() * (self.velocidade_base * dt * self.fator_poder), nivel)

    def desenhar_chefe(self, tela, camera, gfx, fonte):
        ox, oy = camera.offset
        cx, cy = self.rect.centerx - ox, self.rect.bottom - oy
        flutuacao = math.sin(self.tempo_vida * 3.5) * 3.5
        cy_f = cy - round(flutuacao)

        # 6 Asas demoníacas colossais
        cor_asa = (24, 8, 34) if self.fase == 1 else (48, 12, 38)
        for lado in (-1, 1):
            bater = round(math.sin(self.tempo_vida * 4.5) * 6)
            p1 = (cx + lado * 10, cy_f - 10)
            p2 = (cx + lado * 42, cy_f - 24 + bater)
            p3 = (cx + lado * 24, cy_f + 8)
            pygame.draw.polygon(tela, cor_asa, [p1, p2, p3])
            pygame.draw.line(tela, (235, 45, 95), p1, p2, 2)

        # Torso e coroa sombria
        r = pygame.Rect(0, 0, 34, 32)
        r.midbottom = (cx, cy_f)
        pygame.draw.rect(tela, (14, 6, 20), r.inflate(2, 2))
        pygame.draw.rect(tela, (36, 12, 44), r)

        # 3 Olhos flamejantes
        pygame.draw.line(tela, (255, 45, 75), (cx - 7, r.top + 8), (cx - 3, r.top + 8), 2)
        pygame.draw.line(tela, (255, 45, 75), (cx + 3, r.top + 8), (cx + 7, r.top + 8), 2)
        if self.fase == 2:
            # Terceiro olho escarlate ardente
            pygame.draw.circle(tela, (255, 235, 120), (cx, r.top + 4), 3)

        # Núcleo 3D de Cristal Negro no peito
        cristal = criar_cristal_3d(cx, r.centery + 4, z_base=8.0, raio=7.0, altura=11.0, cor=(235, 35, 95), cor_borda=(85, 12, 40))
        cristal.atualizar(self.tempo_vida * 2.2)
        cristal.desenhar(tela, 0, 0, self.tempo_vida)


# Catálogo com a fábrica de todos os chefes
CRIADORES_CHEFES = {
    "rei_slime": ReiSlime,
    "golem_pedra": GolemPedra,
    "serpente_dunas": SerpenteDunas,
    "colosso_solar": ColossoSolar,
    "bruxa_brumas": BruxaBrumas,
    "ceifador_espectral": CeifadorEspectral,
    "leviata_aquatico": LeviataAquatico,
    "guardiao_diamante": GuardiaoDiamante,
    "troll_rochas": TrollRochas,
    "yeti_glacial": YetiGlacial,
    "valquiria_caida": ValquiriaCaida,
    "cavaleiro_negro": CavaleiroNegro,
    "quimera_abissal": QuimeraAbissal,
    "arquimago": ArquimagoCorrompido,
    "paladino_juizo": PaladinoJuizo,
    "entidade_maligna": EntidadeMalignaChefe,
}
