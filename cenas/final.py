"""Cena de Final Feliz, Alvorecer da Paz e Subida dos Créditos 16-bits."""
import math
import random

import pygame

from cenas.base import Cena
from settings import ALTURA, LARGURA
from ui import AMARELO, BRANCO, CINZA, desenhar_texto


LINHAS_CREDITOS = [
    ("AVENTURA PIXEL", "titulo"),
    ("A LENDA DO HERÓI DE ESMERALDA", "subtitulo"),
    ("", "espaco"),
    ("A paz foi restaurada em todo o reino.", "texto"),
    ("As trevas do Apocalipse foram dissipadas.", "texto"),
    ("", "espaco"),
    ("=== CRÉDITOS ===", "cabecalho"),
    ("", "espaco"),
    ("DIREÇÃO E PROGRAMAÇÃO", "cargo"),
    ("Sistema Top-Down em Python 3.12", "nome"),
    ("Motor Gráfico Pygame-CE 16-Bits", "nome"),
    ("", "espaco"),
    ("ARTE VISUAL & SPRITES PROCEDURAIS", "cargo"),
    ("Paleta Estilo 16-Bits (SNES / Mega Drive)", "nome"),
    ("Renderizador de Cristais e Projeção 3D", "nome"),
    ("Animações Dinâmicas de Squash & Stretch", "nome"),
    ("", "espaco"),
    ("TRILHA SONORA & DESIGN DE ÁUDIO", "cargo"),
    ("Sintetizador Chiptune Polifônico", "nome"),
    ("17 Faixas Originais com Bateria e Eco", "nome"),
    ("", "espaco"),
    ("SISTEMA DE RPG & PROGRESSÃO", "cargo"),
    ("Árvore de Habilidades em 3 Ramos Místicos", "nome"),
    ("Magias: Fogo, Gelo, Raios, Cura e Barreira", "nome"),
    ("Escalonamento Dinâmico de Poder dos Chefões", "nome"),
    ("", "espaco"),
    ("OS 15 GUARDIÕES SUPERADOS", "cargo"),
    ("1. Rei Slime Coroado", "nome"),
    ("2. Golem de Pedra Ancestral", "nome"),
    ("3. Serpente das Dunas", "nome"),
    ("4. Colosso Solar", "nome"),
    ("5. Bruxa das Brumas", "nome"),
    ("6. Ceifador Espectral", "nome"),
    ("7. Leviatã Aquático", "nome"),
    ("8. Guardião dos Cristais", "nome"),
    ("9. Troll das Cavernas", "nome"),
    ("10. Yeti Glacial", "nome"),
    ("11. Valquíria Sombria", "nome"),
    ("12. Cavaleiro Negro", "nome"),
    ("13. Quimera Abissal", "nome"),
    ("14. Arquimago Corrompido", "nome"),
    ("15. Paladino do Juízo", "nome"),
    ("", "espaco"),
    ("O CLÍMAX DO SALÃO DO TRONO", "cargo"),
    ("O Desafio das Sombras (Boss Rush)", "nome"),
    ("Derrota de A Entidade Maligna", "nome"),
    ("", "espaco"),
    ("AGRADECIMENTO ESPECIAL", "cargo"),
    ("A Você, por salvar o reino em A Lenda Perdida!", "nome"),
    ("", "espaco"),
    ("F I M", "titulo"),
    ("OBRIGADO POR JOGAR!", "subtitulo"),
]


class Confete:
    def __init__(self):
        self.x = random.uniform(0, LARGURA)
        self.y = random.uniform(-ALTURA, 0)
        self.vel_y = random.uniform(22, 45)
        self.oscilacao = random.uniform(0, math.tau)
        self.cor = random.choice([
            (255, 220, 80),
            (110, 240, 160),
            (255, 110, 140),
            (120, 215, 255),
            (225, 140, 255),
        ])

    def atualizar(self, dt):
        self.y += self.vel_y * dt
        self.oscilacao += dt * 3.5
        if self.y > ALTURA + 10:
            self.y = -10
            self.x = random.uniform(0, LARGURA)

    def desenhar(self, tela):
        px = self.x + math.sin(self.oscilacao) * 8
        pygame.draw.circle(tela, self.cor, (round(px), round(self.y)), 2)


class CenaFinal(Cena):
    """Exibe animação de vitória festiva e sobe os créditos com música alegre."""

    def __init__(self, app, rpg=None):
        super().__init__(app)
        self.rpg = rpg
        self.tempo = 0.0
        self.y_creditos = float(ALTURA + 20)
        self.confetes = [Confete() for _ in range(40)]
        self.concluido = False

        audio = getattr(app, "audio", None)
        if audio:
            audio.tocar_bgm("encerramento", forcar=True)

    def atualizar(self, dt):
        entrada = self.app.entrada
        self.tempo += dt

        for c in self.confetes:
            c.atualizar(dt)

        # Velocidade de subida dos créditos (acelera se segurar confirmação)
        fator_vel = 3.5 if entrada.segurando("confirmar") or entrada.segurando("ataque") else 1.0
        self.y_creditos -= dt * 18.0 * fator_vel

        # Chegou ao final dos créditos
        total_altura = len(LINHAS_CREDITOS) * 14 + 100
        if self.y_creditos < -total_altura:
            self.concluido = True

        if entrada.apertou("voltar") or (self.concluido and entrada.apertou("confirmar")):
            from cenas.menu import MenuPrincipal
            self.app.trocar(MenuPrincipal(self.app))

    def desenhar(self, tela):
        # 1. Alvorecer Dourado (Gradiente suave no céu da manhã)
        progresso_ceu = min(1.0, self.tempo * 0.25)
        for y in range(ALTURA):
            p = y / ALTURA
            r = int(35 + p * 160 * progresso_ceu)
            g = int(45 + p * 185 * progresso_ceu)
            b = int(75 + p * 190 * progresso_ceu)
            tela.fill((min(255, r), min(255, g), min(255, b)), (0, y, LARGURA, 1))

        # 2. Sol nascente dourado com raios de luz
        sol_cx = LARGURA // 2
        sol_cy = 46
        raio_sol = 26 + int(math.sin(self.tempo * 2.0) * 2)
        pygame.draw.circle(tela, (255, 235, 140), (sol_cx, sol_cy), raio_sol)
        pygame.draw.circle(tela, (255, 250, 190), (sol_cx, sol_cy), raio_sol - 4)

        # Raios solares em leque
        for i in range(12):
            ang = (self.tempo * 0.4) + i * (math.tau / 12)
            p1 = (sol_cx + math.cos(ang) * (raio_sol + 2), sol_cy + math.sin(ang) * (raio_sol + 2))
            p2 = (sol_cx + math.cos(ang) * (raio_sol + 22), sol_cy + math.sin(ang) * (raio_sol + 22))
            pygame.draw.line(tela, (255, 240, 150), p1, p2, 2)

        # 3. Silhueta das muralhas e montanhas no horizonte
        pts_montanha = [
            (0, ALTURA - 38), (40, ALTURA - 62), (80, ALTURA - 48),
            (130, ALTURA - 74), (180, ALTURA - 52), (230, ALTURA - 78),
            (280, ALTURA - 56), (320, ALTURA - 42), (320, ALTURA), (0, ALTURA)
        ]
        pygame.draw.polygon(tela, (55, 115, 65), pts_montanha)

        # Chão de grama esmeralda pacífica
        pygame.draw.rect(tela, (42, 95, 52), (0, ALTURA - 28, LARGURA, 28))
        pygame.draw.line(tela, (88, 175, 75), (0, ALTURA - 28), (LARGURA, ALTURA - 28), 2)

        # 4. Confetes festivos caindo
        for c in self.confetes:
            c.desenhar(tela)

        # 5. Herói e NPCs celebrando em miniatura no centro
        ox = LARGURA // 2
        oy = ALTURA - 16
        # Pódio comemorativo do Herói
        pygame.draw.circle(tela, (255, 215, 80), (ox, oy - 2), 5)
        # Amigos comemorando ao lado
        pygame.draw.circle(tela, (110, 180, 255), (ox - 18, oy - 1), 4)
        pygame.draw.circle(tela, (255, 140, 160), (ox + 18, oy - 1), 4)
        pygame.draw.circle(tela, (240, 200, 100), (ox - 34, oy), 4)
        pygame.draw.circle(tela, (180, 140, 240), (ox + 34, oy), 4)

        # 6. Painel semitransparente para os créditos rolantes
        camada_creditos = pygame.Surface((LARGURA - 32, ALTURA), pygame.SRCALPHA)
        camada_creditos.fill((16, 20, 36, 175))
        pygame.draw.rect(camada_creditos, (215, 180, 75, 210), camada_creditos.get_rect(), 1)
        tela.blit(camada_creditos, (16, 0))

        # 7. Renderização dos créditos
        fontes = self.app.fontes
        cy = self.y_creditos

        for texto, tipo in LINHAS_CREDITOS:
            if -20 < cy < ALTURA + 20:
                if tipo == "titulo":
                    desenhar_texto(tela, fontes.titulo, texto, (LARGURA // 2, round(cy)), AMARELO, centro=True)
                elif tipo == "subtitulo":
                    desenhar_texto(tela, fontes.normal, texto, (LARGURA // 2, round(cy)), (255, 235, 140), centro=True)
                elif tipo == "cabecalho":
                    desenhar_texto(tela, fontes.normal, texto, (LARGURA // 2, round(cy)), (110, 240, 160), centro=True)
                elif tipo == "cargo":
                    desenhar_texto(tela, fontes.normal, texto, (LARGURA // 2, round(cy)), AMARELO, centro=True)
                elif tipo == "nome":
                    desenhar_texto(tela, fontes.normal, texto, (LARGURA // 2, round(cy)), BRANCO, centro=True)
                elif tipo == "texto":
                    desenhar_texto(tela, fontes.normal, texto, (LARGURA // 2, round(cy)), (210, 230, 255), centro=True)

            if tipo == "titulo":
                cy += 20
            elif tipo == "espaco":
                cy += 12
            else:
                cy += 14

        # Dica no rodapé
        dica = "Segure Espaço/Enter para acelerar | Esc: Sair" if not self.concluido else "Enter / Espaço: Voltar ao Menu Principal"
        desenhar_texto(tela, fontes.normal, dica, (LARGURA // 2, ALTURA - 8), (255, 240, 160), centro=True)
