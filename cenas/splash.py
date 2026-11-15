"""Cena de abertura estilizada em 16-bits com os logos da Bossbyte, Pygame, Antigravity e Claude.

Exibe sequencialmente as 4 marcas com transições suaves (fade-in / exibição / fade-out),
efeitos visuais retro (partículas flutuantes, brilho 16-bits, anéis de gravidade,
brilhos de diamante e centelhas quentes) e jingles sonoros temáticos antes de
iniciar o Menu Principal.
"""
import math
import random
import pygame

from cenas.base import Cena
from settings import ALTURA, LARGURA
from ui import desenhar_texto


class ParticulaIntro:
    """Pequena partícula pixel art decorativa do fundo de cada tela."""
    def __init__(self, tipo="cyber"):
        self.tipo = tipo
        self.reset()

    def reset(self):
        self.x = random.randint(10, LARGURA - 10)
        self.y = random.randint(10, ALTURA - 20)
        self.vy = random.uniform(-18, -6) if self.tipo in ("antigrav", "ember") else random.uniform(6, 18)
        self.vx = random.uniform(-4, 4)
        self.vida = random.uniform(1.0, 2.5)
        self.max_vida = self.vida
        self.tamanho = random.choice([1, 1, 2])

    def atualizar(self, dt):
        self.vida -= dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.vida <= 0 or self.y < 5 or self.y > ALTURA - 5:
            self.reset()


def criar_logo_bossbyte():
    """Gera o brasão 16-bits da Bossbyte: coroa/chifres dourados de chefe sobre escudo cibernético com B estilizado."""
    surf = pygame.Surface((56, 48), pygame.SRCALPHA)
    
    # 1. Base do escudo / crista cibernética
    pontos_escudo = [
        (12, 16), (43, 16), (49, 22), (49, 36), (28, 46), (6, 36), (6, 22)
    ]
    pygame.draw.polygon(surf, (15, 12, 25), pontos_escudo)
    pygame.draw.polygon(surf, (36, 30, 56), [(p[0], p[1] - 1) for p in pontos_escudo])
    pygame.draw.polygon(surf, (54, 46, 82), [(28, 18), (45, 22), (45, 34), (28, 43), (10, 34), (10, 22)])

    # 2. Chifres / Coroa de Chefe em ouro 16-bits
    chifre_esq = [(14, 18), (8, 10), (4, 4), (8, 4), (12, 8), (18, 14)]
    pygame.draw.polygon(surf, (245, 190, 40), chifre_esq)
    pygame.draw.polygon(surf, (255, 235, 120), [(p[0] + 1, p[1]) for p in chifre_esq[:3]])
    pygame.draw.lines(surf, (90, 60, 15), False, chifre_esq, 1)

    chifre_dir = [(41, 18), (47, 10), (51, 4), (47, 4), (43, 8), (37, 14)]
    pygame.draw.polygon(surf, (245, 190, 40), chifre_dir)
    pygame.draw.polygon(surf, (255, 235, 120), [(p[0] - 1, p[1]) for p in chifre_dir[:3]])
    pygame.draw.lines(surf, (90, 60, 15), False, chifre_dir, 1)

    coroa_centro = [(24, 16), (28, 7), (32, 16)]
    pygame.draw.polygon(surf, (255, 215, 50), coroa_centro)
    pygame.draw.polygon(surf, (255, 245, 180), [(27, 8), (28, 7), (29, 8), (28, 14)])
    surf.set_at((28, 6), (255, 255, 255))

    # 3. Trilhas de circuito ciano (byte lines)
    pygame.draw.line(surf, (0, 220, 255), (12, 24), (16, 24), 1)
    pygame.draw.line(surf, (0, 220, 255), (16, 24), (19, 27), 1)
    pygame.draw.line(surf, (0, 220, 255), (43, 24), (39, 24), 1)
    pygame.draw.line(surf, (0, 220, 255), (39, 24), (36, 27), 1)

    # 4. Letra "B" pixel art 16-bits estilizada
    pygame.draw.rect(surf, (255, 255, 255), (20, 21, 3, 17))
    pygame.draw.rect(surf, (0, 240, 255), (21, 22, 2, 15))
    # Curva superior
    pygame.draw.rect(surf, (255, 255, 255), (23, 21, 9, 3))
    pygame.draw.rect(surf, (255, 255, 255), (29, 23, 4, 6))
    pygame.draw.rect(surf, (255, 255, 255), (23, 27, 8, 3))
    pygame.draw.rect(surf, (0, 240, 255), (23, 23, 7, 3))
    # Curva inferior
    pygame.draw.rect(surf, (255, 255, 255), (30, 30, 5, 7))
    pygame.draw.rect(surf, (255, 255, 255), (23, 35, 9, 3))
    pygame.draw.rect(surf, (0, 240, 255), (23, 31, 8, 4))

    # Recortes internos escuros do B
    surf.set_at((25, 24), (36, 30, 56))
    surf.set_at((26, 24), (36, 30, 56))
    pygame.draw.rect(surf, (36, 30, 56), (25, 32, 3, 2))

    # Nós cibernéticos brilhantes (magenta e ciano)
    surf.set_at((14, 30), (255, 45, 120))
    surf.set_at((41, 30), (255, 45, 120))
    surf.set_at((28, 41), (0, 240, 255))
    surf.set_at((28, 42), (255, 255, 255))

    return surf


def criar_logo_pygame():
    """Gera o modelo 16-bits do controle retrô com a mascote serpente Pygame enroscada."""
    surf = pygame.Surface((56, 44), pygame.SRCALPHA)
    
    # 1. Corpo do Gamepad retrô
    pygame.draw.rect(surf, (18, 20, 28), (8, 14, 40, 22), border_radius=6)
    pygame.draw.rect(surf, (55, 62, 78), (9, 15, 38, 20), border_radius=5)
    pygame.draw.rect(surf, (78, 88, 110), (10, 16, 36, 8), border_radius=3)

    pygame.draw.circle(surf, (40, 45, 58), (14, 24), 8)
    pygame.draw.circle(surf, (40, 45, 58), (42, 24), 8)

    # 2. D-pad cruz no lado esquerdo
    pygame.draw.rect(surf, (18, 20, 28), (12, 22, 10, 4))
    pygame.draw.rect(surf, (18, 20, 28), (15, 19, 4, 10))
    pygame.draw.rect(surf, (32, 36, 46), (13, 23, 8, 2))
    pygame.draw.rect(surf, (32, 36, 46), (16, 20, 2, 8))
    surf.set_at((17, 24), (55, 62, 78))

    # 3. Quatro botões de ação coloridos no lado direito (Amarelo, Azul, Vermelho, Verde)
    pygame.draw.circle(surf, (241, 196, 15), (41, 20), 2)
    surf.set_at((41, 19), (255, 240, 120))
    pygame.draw.circle(surf, (52, 152, 219), (37, 24), 2)
    surf.set_at((37, 23), (120, 200, 255))
    pygame.draw.circle(surf, (231, 76, 60), (45, 24), 2)
    surf.set_at((45, 23), (255, 140, 130))
    pygame.draw.circle(surf, (46, 204, 113), (41, 28), 2)
    surf.set_at((41, 27), (140, 255, 180))

    pygame.draw.line(surf, (30, 34, 44), (24, 25), (26, 24), 1)
    pygame.draw.line(surf, (30, 34, 44), (29, 25), (31, 24), 1)

    # 4. Serpente Python 16-bits enrolada no topo
    cor_corpo = (46, 204, 113)
    cor_sombra = (24, 105, 55)
    cor_topo = (90, 230, 150)
    cor_barriga = (245, 220, 80)

    # Cauda à direita
    pygame.draw.circle(surf, cor_sombra, (38, 12), 4)
    pygame.draw.circle(surf, cor_corpo, (38, 11), 3)
    # Arco do corpo cruzando o topo
    pygame.draw.rect(surf, cor_sombra, (22, 7, 16, 7), border_radius=3)
    pygame.draw.rect(surf, cor_corpo, (22, 6, 16, 6), border_radius=3)
    pygame.draw.line(surf, cor_topo, (23, 6), (36, 6), 1)
    pygame.draw.line(surf, cor_barriga, (23, 11), (35, 11), 1)

    # Cabeça simpática sobre o D-pad
    pygame.draw.circle(surf, (15, 70, 35), (18, 9), 6)
    pygame.draw.circle(surf, cor_corpo, (18, 9), 5)
    pygame.draw.circle(surf, cor_topo, (17, 8), 3)
    pygame.draw.rect(surf, cor_corpo, (11, 7, 6, 5), border_radius=2)
    # Olho pixel
    surf.set_at((16, 7), (255, 255, 255))
    surf.set_at((17, 7), (255, 255, 255))
    surf.set_at((16, 8), (20, 20, 20))
    # Língua vermelha bífida
    pygame.draw.line(surf, (231, 76, 60), (10, 10), (7, 10), 1)
    surf.set_at((6, 9), (231, 76, 60))
    surf.set_at((6, 11), (231, 76, 60))

    return surf


def criar_logo_antigravity(t=0.0):
    """Gera o cristal levitante 16-bits da Google Antigravity em gravidade zero."""
    surf = pygame.Surface((56, 52), pygame.SRCALPHA)
    
    # 1. Base pedestal emissora
    pedestal_y = 44
    pygame.draw.polygon(surf, (20, 24, 42), [(16, pedestal_y + 4), (40, pedestal_y + 4), (46, pedestal_y + 7), (10, pedestal_y + 7)])
    pygame.draw.polygon(surf, (45, 55, 85), [(18, pedestal_y + 2), (38, pedestal_y + 2), (44, pedestal_y + 5), (12, pedestal_y + 5)])
    pygame.draw.line(surf, (0, 240, 255), (20, pedestal_y + 2), (36, pedestal_y + 2), 2)
    
    # Feixe de luz quântico ascendente
    beam_surf = pygame.Surface((20, 24), pygame.SRCALPHA)
    for yb in range(24):
        alpha = int(45 * (1.0 - yb / 24.0))
        pygame.draw.line(beam_surf, (0, 230, 255, alpha), (2 + yb // 6, yb), (18 - yb // 6, yb))
    surf.blit(beam_surf, (18, 22))

    # 2. Anel orbital de gravidade zero (com nodo de energia pulsante)
    ring_cx, ring_cy = 28, 20 + int(math.sin(t * 3.0) * 2.0)
    pontos_anel = []
    for ang_deg in range(0, 360, 15):
        rad = math.radians(ang_deg)
        rx = ring_cx + math.cos(rad) * 20.0
        ry = ring_cy + math.sin(rad) * 6.0 + math.cos(rad) * 2.0
        pontos_anel.append((int(rx), int(ry)))
    if len(pontos_anel) > 2:
        pygame.draw.lines(surf, (124, 77, 255, 160), True, pontos_anel, 1)
        p_node = pontos_anel[int((t * 8) % len(pontos_anel))]
        pygame.draw.circle(surf, (0, 240, 255), p_node, 2)
        surf.set_at(p_node, (255, 255, 255))

    # 3. Cristal diamante levitante lapidado
    cy = 18 + int(math.sin(t * 3.0) * 2.5)
    # Facetas
    pygame.draw.polygon(surf, (120, 240, 255), [(28, cy - 12), (28, cy), (16, cy)])
    pygame.draw.polygon(surf, (220, 255, 255), [(28, cy - 12), (28, cy), (24, cy)])
    pygame.draw.polygon(surf, (41, 150, 255), [(28, cy - 12), (28, cy), (40, cy)])
    pygame.draw.polygon(surf, (0, 180, 230), [(28, cy + 12), (28, cy), (16, cy)])
    pygame.draw.polygon(surf, (25, 80, 200), [(28, cy + 12), (28, cy), (40, cy)])
    
    # Linhas de aresta cristalinas
    pygame.draw.polygon(surf, (255, 255, 255), [(28, cy - 12), (40, cy), (28, cy + 12), (16, cy)], 1)
    pygame.draw.line(surf, (255, 255, 255), (16, cy), (40, cy), 1)
    pygame.draw.line(surf, (255, 255, 255), (28, cy - 12), (28, cy + 12), 1)
    
    # Ponto de brilho especular
    surf.set_at((28, cy - 12), (255, 255, 255))
    surf.set_at((27, cy - 11), (255, 255, 255))

    return surf


def criar_logo_claude(t=0.0):
    """Gera o ícone de centelha / asterisco 16-bits da Anthropic Claude com paleta terracota."""
    surf = pygame.Surface((52, 50), pygame.SRCALPHA)
    cx, cy = 26, 25
    
    c_cream = (255, 246, 240)
    c_peach = (244, 162, 133)
    c_terra = (217, 119, 87)
    c_rust  = (170, 75, 48)
    c_dark  = (85, 34, 24)
    
    raio_prim = 18.0 + math.sin(t * 3.5) * 0.8
    raio_diag = 13.5 + math.sin(t * 3.5 + 1.0) * 0.6
    raio_val  = 5.5
    
    pontos_externos = []
    for i in range(16):
        ang = math.radians(i * 22.5 - 90.0)
        if i % 4 == 0:
            r = raio_prim
        elif i % 2 == 0:
            r = raio_diag
        else:
            r = raio_val
        px = cx + math.cos(ang) * r
        py = cy + math.sin(ang) * r
        pontos_externos.append((px, py))
        
    pygame.draw.polygon(surf, c_dark, [(p[0], p[1]) for p in pontos_externos])
    
    pontos_internos = []
    for px, py in pontos_externos:
        vx = px - cx
        vy = py - cy
        pontos_internos.append((cx + vx * 0.88, cy + vy * 0.88))
    pygame.draw.polygon(surf, c_terra, pontos_internos)
    
    # Camadas de sombreamento 16-bits
    pygame.draw.polygon(surf, c_rust, [
        (cx - 14, cy + 2), (cx + 14, cy + 2), (cx + 10, cy + 14), (cx, cy + 16), (cx - 10, cy + 14)
    ])
    pygame.draw.polygon(surf, c_peach, [
        (cx - 3, cy - 14), (cx + 3, cy - 14), (cx + 2, cy - 2), (cx - 2, cy - 2)
    ])
    pygame.draw.polygon(surf, c_peach, [
        (cx - 13, cy - 3), (cx - 2, cy - 2), (cx - 2, cy + 2), (cx - 13, cy + 1)
    ])
    pygame.draw.polygon(surf, c_peach, [
        (cx - 10, cy - 10), (cx - 2, cy - 2), (cx - 8, cy - 8)
    ])
    
    pygame.draw.circle(surf, c_cream, (cx, cy), 3)
    surf.set_at((cx, cy), (255, 255, 255))
    surf.set_at((cx - 1, cy - 1), (255, 255, 255))
    
    return surf


class CenaAberturaLogos(Cena):
    """Apresenta a sequência cinematográfica inicial dos logos com áudio e transições."""

    FADE_IN = 0.40
    EXIBICAO = 1.45
    FADE_OUT = 0.40

    def __init__(self, app):
        super().__init__(app)
        self.indice_card = 0
        self.tempo_card = 0.0
        self.tempo_total = 0.0
        self.transicao_iniciada = False

        # Cache de logos estáticos para performance
        self.logo_bossbyte = criar_logo_bossbyte()
        self.logo_pygame = criar_logo_pygame()

        # Partículas decorativas de fundo
        self.particulas = [ParticulaIntro(tipo="cyber") for _ in range(16)]

        # Definição dos 4 cards de abertura
        self.cards = [
            {
                "chave": "bossbyte",
                "bg_cor": (12, 10, 24),
                "sub_sup": "APRESENTA",
                "titulo": "BOSSBYTE",
                "sub_inf": "GAME STUDIOS",
                "cor_sub": (255, 220, 90),
                "cor_tit": (0, 240, 255),
                "sfx": "logo_bossbyte",
                "tipo_part": "cyber",
            },
            {
                "chave": "pygame",
                "bg_cor": (14, 16, 26),
                "sub_sup": "DESENVOLVIDO COM",
                "titulo": "PYGAME-CE",
                "sub_inf": "PYTHON GAME ENGINE",
                "cor_sub": (200, 210, 230),
                "cor_tit": (46, 204, 113),
                "sfx": "logo_pygame",
                "tipo_part": "retro",
            },
            {
                "chave": "antigravity",
                "bg_cor": (10, 14, 28),
                "sub_sup": "DESENVOLVIDO COM",
                "titulo": "ANTIGRAVITY",
                "sub_inf": "GOOGLE DEEPMIND",
                "cor_sub": (180, 210, 255),
                "cor_tit": (0, 240, 255),
                "sfx": "logo_antigravity",
                "tipo_part": "antigrav",
            },
            {
                "chave": "claude",
                "bg_cor": (18, 14, 16),
                "sub_sup": "DESENVOLVIDO COM",
                "titulo": "CLAUDE",
                "sub_inf": "ANTHROPIC",
                "cor_sub": (235, 200, 190),
                "cor_tit": (217, 119, 87),
                "sfx": "logo_claude",
                "tipo_part": "ember",
            },
        ]

        self._tocar_sfx_card(0)

    def _tocar_sfx_card(self, idx):
        if 0 <= idx < len(self.cards):
            sfx_nome = self.cards[idx]["sfx"]
            if hasattr(self.app, "audio"):
                self.app.audio.sfx(sfx_nome)

    def pular_card(self):
        """Avança para o próximo logo ou pula direto para o Menu Principal."""
        self.indice_card += 1
        if self.indice_card >= len(self.cards):
            self.ir_para_menu()
        else:
            self.tempo_card = 0.0
            # Ajusta o tipo de partículas do novo card
            tipo = self.cards[self.indice_card]["tipo_part"]
            for p in self.particulas:
                p.tipo = tipo
                p.reset()
            self._tocar_sfx_card(self.indice_card)

    def ir_para_menu(self):
        """Conclui a sequência de abertura e entrega o controle ao Menu Principal."""
        from cenas.menu import MenuPrincipal
        self.app.trocar(MenuPrincipal(self.app))

    def atualizar(self, dt):
        self.tempo_total += dt
        self.tempo_card += dt

        # Atualiza partículas
        for p in self.particulas:
            p.atualizar(dt)

        # Checa entradas para avançar/pular
        # ESC / Voltar / Pausa vai direto ao Menu; Enter / Espaço / Botão A avança o slide atual
        if self.app.entrada.apertou("voltar") or self.app.entrada.apertou("pausa"):
            self.ir_para_menu()
            return

        pressionou_skip = (
            self.app.entrada.apertou("confirmar")
            or self.app.entrada.apertou("acao")
        )
        if hasattr(self.app, "eventos_quadro"):
            for ev in self.app.eventos_quadro:
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    pressionou_skip = True

        if pressionou_skip:
            self.pular_card()
            return

        # Duração total do ciclo de cada card
        duracao_total_card = self.FADE_IN + self.EXIBICAO + self.FADE_OUT
        if self.tempo_card >= duracao_total_card:
            self.pular_card()

    def desenhar(self, tela):
        if self.indice_card >= len(self.cards):
            return

        card = self.cards[self.indice_card]
        
        # Calcula opacidade (alpha de 0 a 255)
        tc = self.tempo_card
        if tc < self.FADE_IN:
            fator = max(0.0, min(1.0, tc / self.FADE_IN))
        elif tc < self.FADE_IN + self.EXIBICAO:
            fator = 1.0
        else:
            fim = self.FADE_IN + self.EXIBICAO + self.FADE_OUT
            fator = max(0.0, min(1.0, (fim - tc) / self.FADE_OUT))

        alpha = int(255 * fator)

        # Renderiza o card completo em uma superfície temporária para aplicar fade suave
        surf_card = pygame.Surface((LARGURA, ALTURA))
        surf_card.fill(card["bg_cor"])

        # Desenha partículas temáticas de fundo
        for p in self.particulas:
            cor_part = card["cor_tit"] if p.tamanho > 1 else card["cor_sub"]
            pygame.draw.rect(surf_card, cor_part, (int(p.x), int(p.y), p.tamanho, p.tamanho))

        # Subtítulo superior
        desenhar_texto(
            surf_card,
            self.app.fontes.normal,
            card["sub_sup"],
            (LARGURA // 2, 26),
            cor=card["cor_sub"],
            centro=True,
        )

        # Seleciona / renderiza o logo central
        chave = card["chave"]
        if chave == "bossbyte":
            logo_surf = self.logo_bossbyte
        elif chave == "pygame":
            logo_surf = self.logo_pygame
        elif chave == "antigravity":
            logo_surf = criar_logo_antigravity(self.tempo_total)
        elif chave == "claude":
            logo_surf = criar_logo_claude(self.tempo_total)
        else:
            logo_surf = self.logo_bossbyte

        r_logo = logo_surf.get_rect(center=(LARGURA // 2, 78))
        surf_card.blit(logo_surf, r_logo)

        # Título principal
        desenhar_texto(
            surf_card,
            self.app.fontes.titulo,
            card["titulo"],
            (LARGURA // 2, 126),
            cor=card["cor_tit"],
            centro=True,
        )

        # Subtítulo inferior
        desenhar_texto(
            surf_card,
            self.app.fontes.normal,
            card["sub_inf"],
            (LARGURA // 2, 150),
            cor=(180, 185, 205),
            centro=True,
        )

        # Dica discreta de pular no canto inferior direito
        img_pular = self.app.fontes.normal.render("[Espaço] Pular", False, (110, 115, 135))
        surf_card.blit(img_pular, (LARGURA - img_pular.get_width() - 8, ALTURA - 14))

        # Aplica a transparência geral do card e blita na tela
        surf_card.set_alpha(alpha)
        tela.blit(surf_card, (0, 0))
