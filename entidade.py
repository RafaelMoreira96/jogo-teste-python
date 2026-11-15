"""Base para tudo que anda pelo mapa (jogador, NPCs, inimigos)."""
import math
import random

import pygame

from ui import AMARELO, BRANCO, desenhar_texto


class Entidade:
    def __init__(self, x, y, largura, altura):
        # `rect` é a hitbox (só os pés). O sprite é desenhado em volta dela.
        self.rect = pygame.Rect(0, 0, largura, altura)
        self.rect.midbottom = (x, y)
        self.pos = pygame.Vector2(self.rect.topleft)  # posição com fração
        self.empurrao = pygame.Vector2()
        self.tempo_empurrao = 0.0

        # Pulo vertical, poses, emoções, squash & stretch e movimento por roteiro
        self.z = 0.0
        self.vel_z = 0.0
        self.escala_x = 1.0
        self.escala_y = 1.0
        self.inclinacao = 0.0
        self.tempo_idle = random.uniform(0.0, 5.0)
        self.acabou_de_pousar = False
        self.pose = "normal"
        self.tempo_pose = 0.0
        self.emocao = None
        self.tempo_emocao = 0.0
        self.duracao_emocao = 1.8
        self.zs = []
        self.timer_z = 0.1
        self.destino_roteiro = None
        self.vel_roteiro = 56.0
        self.tempo_roteiro = 0.0
        self.direcao = "baixo"
        self.anim = 0.0
        self.andando = False
        self.pode_nadar = False
        self.nadando = False
        self.protecao_pulo = 0.0

    def deformar(self, sx, sy):
        """Aplica squash & stretch imediato (volta ao normal suavemente)."""
        self.escala_x = sx
        self.escala_y = sy

    @property
    def andando_roteiro(self):
        return self.destino_roteiro is not None

    def posicionar(self, x, y):
        self.rect.midbottom = (round(x), round(y))
        self.pos = pygame.Vector2(self.rect.topleft)
        self.destino_roteiro = None

    @property
    def no_ar(self):
        return self.z > 0 or self.vel_z > 0 or self.protecao_pulo > 0

    def pular(self, forca=155.0):
        if self.z <= 0:
            self.vel_z = forca
            self.z = 0.1
            self.deformar(0.82, 1.22)

    def definir_pose(self, pose):
        if pose in ("acordar", "normal"):
            self.pose = "normal"
            self.zs.clear()
        elif pose == "assustar":
            self.pose = "normal"
            self.zs.clear()
            self.pular(115.0)
            self.mostrar_emocao("!")
        else:
            self.pose = pose
            self.tempo_pose = 0.0

    def mostrar_emocao(self, tipo, duracao=1.8):
        self.emocao = tipo
        self.tempo_emocao = duracao
        self.duracao_emocao = max(0.1, duracao)

    def ir_para(self, x, y, velocidade=56.0):
        self.destino_roteiro = pygame.Vector2(x, y)
        self.vel_roteiro = velocidade
        self.tempo_roteiro = 0.0

    def olhar_para_ponto(self, x, y):
        dx = x - self.rect.centerx
        dy = y - self.rect.centery
        if abs(dx) > abs(dy):
            self.direcao = "direita" if dx > 0 else "esquerda"
        else:
            self.direcao = "baixo" if dy > 0 else "cima"

    def empurrar(self, origem, forca, duracao):
        """Knockback para longe de `origem`."""
        direcao = pygame.Vector2(self.rect.center) - pygame.Vector2(origem)
        if direcao.length_squared() == 0:
            direcao = pygame.Vector2(0, 1)
        self.empurrao = direcao.normalize() * forca
        self.tempo_empurrao = duracao
        self.deformar(1.22, 0.80)

    def mover(self, deslocamento, nivel):
        """Move com sub-passos contínuos para evitar qualquer tunneling em alta velocidade e deslizar suave nas paredes."""
        dist = math.hypot(deslocamento.x, deslocamento.y)
        passos = max(1, math.ceil(dist / 6.0))
        sub_dx = deslocamento.x / passos
        sub_dy = deslocamento.y / passos
        bateu = False

        for _ in range(passos):
            if sub_dx:
                self.pos.x += sub_dx
                self.rect.x = round(self.pos.x)
                for bloco in nivel.colisoes(self.rect, pode_nadar=self.pode_nadar):
                    if sub_dx > 0:
                        self.rect.right = bloco.left
                    else:
                        self.rect.left = bloco.right
                    self.pos.x = self.rect.x
                    bateu = True
            if sub_dy:
                self.pos.y += sub_dy
                self.rect.y = round(self.pos.y)
                for bloco in nivel.colisoes(self.rect, pode_nadar=self.pode_nadar):
                    if sub_dy > 0:
                        self.rect.bottom = bloco.top
                    else:
                        self.rect.top = bloco.bottom
                    self.pos.y = self.rect.y
                    bateu = True

        if hasattr(nivel, "largura_px") and hasattr(nivel, "altura_px"):
            self.rect.left = max(0, min(self.rect.left, nivel.largura_px - self.rect.width))
            self.rect.top = max(0, min(self.rect.top, nivel.altura_px - self.rect.height))
            self.pos.update(self.rect.topleft)

        return bateu

    def atualizar_empurrao(self, dt, nivel):
        """Aplica o knockback, se houver. Devolve True enquanto está sendo empurrado."""
        if self.tempo_empurrao <= 0:
            return False
        self.tempo_empurrao -= dt
        self.mover(self.empurrao * dt, nivel)
        return True

    def atualizar_base(self, dt, nivel):
        """Atualiza pulo, squash & stretch, poses, emoções e caminhada de roteiro."""
        self.tempo_pose += dt
        self.tempo_idle += dt
        self.protecao_pulo = max(0.0, self.protecao_pulo - dt)
        self.acabou_de_pousar = False
        self.nadando = (
            self.pode_nadar
            and nivel.eh_agua_em(self.rect.centerx, self.rect.centery)
            and self.z <= 2.0
        )

        # Mola suave de retorno para escala e inclinação
        fator_mola = min(1.0, dt * 14.0)
        self.escala_x += (1.0 - self.escala_x) * fator_mola
        self.escala_y += (1.0 - self.escala_y) * fator_mola
        self.inclinacao += (0.0 - self.inclinacao) * fator_mola

        if self.tempo_emocao > 0:
            self.tempo_emocao = max(0.0, self.tempo_emocao - dt)
            if self.tempo_emocao <= 0:
                self.emocao = None

        if self.z > 0 or self.vel_z > 0:
            self.z += self.vel_z * dt
            self.vel_z -= 420.0 * dt
            if self.z <= 0:
                self.z = 0.0
                self.vel_z = 0.0
                self.protecao_pulo = 0.16
                self.deformar(1.24, 0.78)  # achata ao tocar o chão
                self.acabou_de_pousar = True

        if self.pose == "comemorar" and self.z <= 0:
            self.pular(95.0)

        if self.pose == "dormir":
            self.timer_z -= dt
            if self.timer_z <= 0:
                self.timer_z = 0.45
                self.zs.append({
                    "x": float(self.rect.centerx + 2),
                    "y": float(self.rect.top - 16),
                    "t": 0.0,
                    "fase": random.uniform(0, math.tau),
                })
        for z in self.zs:
            z["t"] += dt
            z["y"] -= 13.0 * dt
        self.zs = [z for z in self.zs if z["t"] < 1.8]

        if self.destino_roteiro is not None:
            atual = pygame.Vector2(self.rect.midbottom)
            diff = self.destino_roteiro - atual
            dist = diff.length()
            self.tempo_roteiro += dt
            if dist <= 2.0 or self.tempo_roteiro > 6.0:
                self.posicionar(self.destino_roteiro.x, self.destino_roteiro.y)
                self.andando = False
                self.anim = 0.0
                return False
            self.olhar_para_ponto(self.destino_roteiro.x, self.destino_roteiro.y)
            passo = diff.normalize() * min(dist, self.vel_roteiro * dt)
            self.andando = True
            self.anim += dt * 9.0
            bateu = self.mover(passo, nivel)
            if bateu and self.tempo_roteiro > 0.6:
                self.destino_roteiro = None
                self.andando = False
            return True
        return False

    def quadro_personagem(self, quadros):
        """Escolhe o quadro certo: ciclo de 6 passos andando ou respiração/piscada parado."""
        if len(quadros) < 8:
            return quadros[int(self.anim) % len(quadros) if self.andando else 0]
        if self.andando:
            return quadros[int(self.anim) % 6]
        # Parado: pisca rapidamente a cada ~3.6s e respira suavemente no resto do tempo
        ciclo_piscar = self.tempo_idle % 3.6
        if ciclo_piscar > 3.46:
            return quadros[7]
        respirando = math.sin(self.tempo_idle * 2.8) > 0.35
        return quadros[6 if respirando else 2]

    def transformar_sprite(self, img, rect_mundo, camera):
        """Aplica squash & stretch, pulo e inclinação mantendo os pés ancorados."""
        dx, dy = self.offset_pose()
        rect_tela = camera.aplicar(rect_mundo).move(dx, dy)
        sx, sy = self.escala_x, self.escala_y
        if not self.andando and self.z <= 0 and self.pose == "normal":
            # Leve respiração elástica adicional
            resp = math.sin(self.tempo_idle * 2.8) * 0.025
            sx *= 1.0 - resp * 0.5
            sy *= 1.0 + resp

        if abs(sx - 1.0) > 0.02 or abs(sy - 1.0) > 0.02:
            nova_larg = max(4, round(img.get_width() * sx))
            nova_alt = max(4, round(img.get_height() * sy))
            img = pygame.transform.scale(img, (nova_larg, nova_alt))
        if abs(self.inclinacao) > 1.0:
            img = pygame.transform.rotate(img, self.inclinacao)
        ancorado = img.get_rect(midbottom=rect_tela.midbottom)
        return img, ancorado

    def desenhar_sombra(self, tela, camera, gfx, centro_chao=None):
        ponto = centro_chao or self.rect.midbottom
        fator = max(0.55, 1.0 - self.z / 55.0) * self.escala_x
        sombra = gfx.sombra
        if abs(fator - 1.0) > 0.06:
            larg = max(6, round(sombra.get_width() * fator))
            alt = max(3, round(sombra.get_height() * fator))
            sombra = pygame.transform.scale(sombra, (larg, alt))
        tela.blit(sombra, camera.aplicar(sombra.get_rect(center=ponto)))

    def offset_pose(self):
        """Deslocamento (dx, dy) extra para tremer ou pular."""
        dx = round(math.sin(self.tempo_pose * 45) * 1.5) if self.pose == "tremer" else 0
        dy = -round(self.z)
        return dx, dy

    def desenhar_extras_cabeca(self, tela, camera, fonte, topo_cabeca):
        ox, oy = camera.offset
        # Animação de "zzzzzz"
        for z in self.zs:
            oscilacao = math.sin(z["t"] * 5 + z["fase"]) * 3.5
            sx = round(z["x"] + oscilacao) - ox
            sy = round(z["y"]) - oy
            letra = "z" if z["t"] < 0.7 else "Z"
            cor = (255, 240, 150) if z["t"] > 1.2 else (240, 240, 255)
            desenhar_texto(tela, fonte, letra, (sx, sy), cor, centro=True)

        # Balão de emoção (!, ?, ..., coracao) com pop-in elástico e flutuação
        if self.emocao and self.tempo_emocao > 0:
            decorrido = self.duracao_emocao - self.tempo_emocao
            pop = min(1.0, decorrido * 9.0)
            salto_pop = round(math.sin(pop * math.pi) * 4) if decorrido < 0.2 else round(math.sin(decorrido * 6) * 1.2)
            bx = topo_cabeca[0] - ox
            by = topo_cabeca[1] - oy - round(self.z) - 8 - salto_pop
            balao = pygame.Rect(0, 0, 14, 12)
            balao.center = (bx, by)
            pygame.draw.rect(tela, (245, 245, 250), balao, border_radius=3)
            pygame.draw.rect(tela, (30, 24, 40), balao, 1, border_radius=3)
            cor_txt = (220, 40, 60) if self.emocao in ("!", "coracao") else (40, 32, 56)
            simbolo = "<3" if self.emocao == "coracao" else self.emocao
            desenhar_texto(tela, fonte, simbolo, (bx, by - 1), cor_txt, centro=True)
            _ = (AMARELO, BRANCO)

