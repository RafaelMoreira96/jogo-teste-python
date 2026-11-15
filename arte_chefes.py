"""Arte procedural 16-bits dos chefões.

Cada função desenha um Guardião com os pés em (x, y) numa Surface própria.
A classe Chefe (chefe.py) cuida do resto: contorno escuro automático,
clarão branco ao levar dano, brilho vermelho de fúria e espelhamento.

As formas usam sempre três tons (sombra, base e luz vinda do alto à
esquerda) para dar volume, no espírito dos chefes de SNES.
"""
import math

import pygame

from render3d import criar_cristal_3d


# ------------------------------------------------------------------ utilidades
def _tons(cor):
    """(sombra, base, luz) a partir de uma cor base."""
    sombra = tuple(max(0, round(v * 0.62)) for v in cor)
    luz = tuple(min(255, round(v + (255 - v) * 0.38)) for v in cor)
    return sombra, tuple(cor), luz


def oval(s, cor, rect, brilho=True):
    rect = pygame.Rect(rect)
    sombra, base, luz = _tons(cor)
    pygame.draw.ellipse(s, sombra, rect)
    pygame.draw.ellipse(s, base, rect.inflate(-2, -3).move(-1, -1))
    if brilho and rect.width > 6 and rect.height > 6:
        pygame.draw.ellipse(s, luz, (rect.x + rect.width // 5, rect.y + rect.height // 6, max(2, rect.width // 3), max(2, rect.height // 4)))


def caixa(s, cor, rect, raio=2):
    rect = pygame.Rect(rect)
    sombra, base, luz = _tons(cor)
    pygame.draw.rect(s, sombra, rect, border_radius=raio)
    pygame.draw.rect(s, base, (rect.x, rect.y, rect.width - 2, rect.height - 2), border_radius=raio)
    pygame.draw.line(s, luz, (rect.x + 1, rect.y + 1), (rect.right - 4, rect.y + 1))
    pygame.draw.line(s, luz, (rect.x + 1, rect.y + 1), (rect.x + 1, rect.bottom - 4))


def poli(s, cor, pts, luz=True):
    sombra, base, clara = _tons(cor)
    pygame.draw.polygon(s, sombra, pts)
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    menor = [(round(px + (cx - px) * 0.18) - 1, round(py + (cy - py) * 0.18) - 1) for px, py in pts]
    pygame.draw.polygon(s, base, menor)
    if luz:
        pygame.draw.line(s, clara, menor[0], menor[1 % len(menor)])


def olho(s, x, y, cor=(255, 60, 60), brilho=True):
    pygame.draw.rect(s, cor, (x - 1, y - 1, 3, 2))
    if brilho:
        s.set_at((x - 1, y - 1), (255, 255, 255))


def halo(s, cor, centro, raio, alfa=70):
    camada = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
    for r in range(raio, 0, -max(1, raio // 4)):
        pygame.draw.circle(camada, (*cor[:3], round(alfa * (1 - r / raio) + 10)), (raio, raio), r)
    s.blit(camada, (centro[0] - raio, centro[1] - raio))


# ------------------------------------------------------------------ 1. Rei Slime
def rei_slime(c, s, x, y, t):
    y -= round(c.z)
    onda = math.sin(getattr(c, "fase_salto", t * 4))
    larg, alt = 34 + round(onda * 4), 26 - round(onda * 4)
    cor = (150, 80, 230) if c.fantasma else (70, 170, 240)
    # Manto real
    pygame.draw.ellipse(s, (120, 22, 40), (x - larg // 2 - 4, y - 7, larg + 8, 9))
    pygame.draw.ellipse(s, (220, 180, 60), (x - larg // 2 - 4, y - 7, larg + 8, 9), 1)
    corpo = pygame.Rect(0, 0, larg, alt)
    corpo.midbottom = (x, y)
    oval(s, cor, corpo)
    # Bolhas internas e núcleo
    for i in range(4):
        bx = x - 9 + (i * 7) + round(math.sin(t * 2 + i) * 2)
        by = y - 6 - (i % 2) * 6 + round(math.cos(t * 3 + i) * 1.5)
        pygame.draw.circle(s, _tons(cor)[2], (bx, by), 1 + i % 2, 1)
    # Rosto
    oy = y - alt // 2 - 2
    for dx in (-6, 6):
        pygame.draw.ellipse(s, (255, 255, 255), (x + dx - 3, oy - 3, 6, 7))
        pygame.draw.rect(s, (20, 24, 50), (x + dx - 1 + (1 if dx > 0 else 0), oy - 1, 2, 3))
    pygame.draw.arc(s, (30, 40, 90), (x - 5, oy + 2, 10, 6), math.pi + 0.3, 2 * math.pi - 0.3, 1)
    # Coroa
    topo = corpo.top - 2
    pts = [(x - 11, topo + 4), (x - 11, topo - 5), (x - 6, topo), (x, topo - 9), (x + 6, topo), (x + 11, topo - 5), (x + 11, topo + 4)]
    poli(s, (245, 205, 60), pts)
    for gx, cg in ((x - 7, (230, 40, 70)), (x, (90, 230, 255)), (x + 7, (230, 40, 70))):
        pygame.draw.circle(s, cg, (gx, topo + 1), 2)
        s.set_at((gx - 1, topo), (255, 255, 255))


# ------------------------------------------------------------------ 2. Golem de Pedra
def golem_pedra(c, s, x, y, t):
    pedra = (128, 132, 146)
    runa = (215, 95, 255) if c.fantasma else (90, 235, 255)
    passo = math.sin(t * 3)
    # Pernas
    caixa(s, (98, 102, 116), (x - 11, y - 10 + round(passo), 8, 10))
    caixa(s, (98, 102, 116), (x + 3, y - 10 - round(passo), 8, 10))
    # Tronco
    caixa(s, pedra, (x - 14, y - 32, 28, 24), raio=3)
    pygame.draw.line(s, (80, 84, 98), (x - 8, y - 28), (x - 4, y - 18))
    pygame.draw.rect(s, (70, 130, 64), (x - 13, y - 14, 5, 3))
    # Braços balançando
    for lado in (-1, 1):
        bx = x + lado * 19
        by = y - 28 + round(math.sin(t * 3 + lado) * 2)
        caixa(s, (110, 114, 128), (bx - 5, by, 10, 12))
        caixa(s, (92, 96, 110), (bx - 6, by + 11, 12, 9), raio=3)
    # Cabeça
    caixa(s, (142, 146, 160), (x - 8, y - 42, 16, 12))
    pulso = 0.6 + 0.4 * math.sin(t * 5)
    cor_r = tuple(round(v * pulso + 40 * (1 - pulso)) for v in runa)
    pygame.draw.rect(s, cor_r, (x - 5, y - 37, 3, 2))
    pygame.draw.rect(s, cor_r, (x + 2, y - 37, 3, 2))
    # Runa no peito
    pygame.draw.circle(s, cor_r, (x, y - 22), 4, 1)
    pygame.draw.line(s, cor_r, (x, y - 26), (x, y - 15))
    pygame.draw.line(s, cor_r, (x - 4, y - 20), (x + 4, y - 20))


# ------------------------------------------------------------------ 3. Serpente das Dunas
def serpente_dunas(c, s, x, y, t):
    areia, listra = (222, 168, 84), (150, 88, 36)
    # Rolo de corpo com segmentos que ondulam
    for i in range(6):
        ang = t * 2 + i * 0.9
        sx = x + round(math.sin(ang) * (10 - i))
        sy = y - 4 - i * 5
        r = 9 - i // 2
        oval(s, areia, (sx - r, sy - r // 2 - 2, r * 2, r + 3))
        pygame.draw.arc(s, listra, (sx - r + 2, sy - r // 2, r * 2 - 4, r), 0, math.pi, 1)
    # Capuz de naja
    hx, hy = x + round(math.sin(t * 2 + 5.4) * 4), y - 36
    poli(s, (196, 130, 56), [(hx - 12, hy + 6), (hx - 7, hy - 6), (hx, hy - 9), (hx + 7, hy - 6), (hx + 12, hy + 6), (hx, hy + 10)])
    pygame.draw.polygon(s, (250, 210, 120), [(hx - 4, hy - 2), (hx + 4, hy - 2), (hx, hy + 6)])
    # Olhos com fenda e presas
    for dx in (-4, 4):
        pygame.draw.ellipse(s, (255, 236, 80), (hx + dx - 2, hy - 5, 4, 4))
        pygame.draw.line(s, (20, 12, 8), (hx + dx, hy - 5), (hx + dx, hy - 2))
    pygame.draw.line(s, (255, 255, 240), (hx - 2, hy + 6), (hx - 2, hy + 9))
    pygame.draw.line(s, (255, 255, 240), (hx + 2, hy + 6), (hx + 2, hy + 9))
    # Areia levantada na base
    for i in range(5):
        px = x - 14 + i * 7 + round(math.sin(t * 6 + i) * 2)
        pygame.draw.circle(s, (238, 206, 140), (px, y - 1), 2)


# ------------------------------------------------------------------ 4. Colosso Solar
def colosso_solar(c, s, x, y, t):
    ouro = (236, 178, 52)
    # Halo solar giratório
    centro = (x, y - 30)
    halo(s, (255, 200, 60), centro, 24, 60)
    for i in range(12):
        a = t * 1.5 + i * math.tau / 12
        r1, r2 = 15, 21 + (i % 2) * 3
        p1 = (centro[0] + round(math.cos(a) * r1), centro[1] + round(math.sin(a) * r1))
        p2 = (centro[0] + round(math.cos(a) * r2), centro[1] + round(math.sin(a) * r2))
        pygame.draw.line(s, (255, 226, 90), p1, p2, 2)
    # Pernas e saiote
    caixa(s, (190, 136, 40), (x - 9, y - 10, 7, 10))
    caixa(s, (190, 136, 40), (x + 2, y - 10, 7, 10))
    poli(s, (210, 70, 40), [(x - 11, y - 16), (x + 11, y - 16), (x + 13, y - 8), (x - 13, y - 8)])
    # Tronco com sol no peito
    caixa(s, ouro, (x - 12, y - 34, 24, 19), raio=3)
    pygame.draw.circle(s, (255, 90, 40), (x, y - 25), 5)
    pygame.draw.circle(s, (255, 246, 160), (x, y - 25), 3)
    # Ombreiras com pontas
    for lado in (-1, 1):
        poli(s, (250, 210, 90), [(x + lado * 10, y - 34), (x + lado * 19, y - 36), (x + lado * 16, y - 27), (x + lado * 10, y - 28)])
        caixa(s, (210, 150, 46), (x + lado * 16 - 3, y - 27, 6, 11))
    # Elmo com crista
    caixa(s, (250, 214, 100), (x - 6, y - 44, 12, 11))
    pygame.draw.rect(s, (30, 20, 10), (x - 4, y - 40, 8, 2))
    pygame.draw.rect(s, (255, 240, 170), (x - 3, y - 40, 2, 1))
    poli(s, (230, 60, 40), [(x - 2, y - 44), (x + 2, y - 44), (x + 1, y - 52), (x - 4, y - 49)])


# ------------------------------------------------------------------ 5. Bruxa das Brumas
def bruxa_brumas(c, s, x, y, t):
    flutua = round(math.sin(t * 2.4) * 2)
    y0 = y - 3 + flutua
    # Névoa
    halo(s, (130, 60, 200), (x, y - 2), 16, 50)
    # Vestido esfarrapado
    pts = [(x - 4, y0 - 26), (x + 4, y0 - 26), (x + 12, y0)]
    for i in range(5):
        pts.append((x + 10 - i * 5, y0 - (3 if i % 2 else 0)))
    pts.append((x - 12, y0))
    poli(s, (76, 34, 104), pts)
    pygame.draw.line(s, (150, 80, 200), (x - 3, y0 - 20), (x - 6, y0 - 4))
    # Rosto verde e nariz adunco
    oval(s, (120, 190, 110), (x - 5, y0 - 34, 10, 10), brilho=False)
    pygame.draw.line(s, (80, 140, 76), (x + 2, y0 - 29), (x + 5, y0 - 27))
    olho(s, x - 2, y0 - 31, (255, 230, 80))
    olho(s, x + 2, y0 - 31, (255, 230, 80))
    # Chapéu torto
    poli(s, (44, 20, 62), [(x - 13, y0 - 33), (x + 13, y0 - 33), (x + 8, y0 - 36), (x - 8, y0 - 36)])
    poli(s, (54, 24, 76), [(x - 7, y0 - 35), (x + 7, y0 - 35), (x + 10, y0 - 50), (x + 3, y0 - 44)])
    pygame.draw.rect(s, (110, 250, 150), (x - 6, y0 - 37, 12, 2))
    # Cajado com caveira e orbe venenoso
    pygame.draw.line(s, (110, 74, 44), (x + 12, y0 + 1), (x + 15, y0 - 38), 2)
    halo(s, (110, 255, 150), (x + 15, y0 - 42), 8, 90)
    pygame.draw.circle(s, (230, 230, 210), (x + 15, y0 - 41), 3)
    pygame.draw.rect(s, (20, 20, 20), (x + 14, y0 - 42, 1, 1))
    pygame.draw.rect(s, (20, 20, 20), (x + 16, y0 - 42, 1, 1))
    # Espíritos orbitando
    for i in range(3):
        a = t * 2 + i * math.tau / 3
        pygame.draw.circle(s, (180, 120, 255), (x + round(math.cos(a) * 18), y0 - 18 + round(math.sin(a) * 7)), 2)


# ------------------------------------------------------------------ 6. Ceifador Espectral
def ceifador_espectral(c, s, x, y, t):
    flutua = round(math.sin(t * 2) * 3)
    y0 = y - 4 + flutua
    # Manto rasgado
    pts = [(x, y0 - 40), (x + 12, y0 - 26), (x + 14, y0)]
    for i in range(6):
        pts.append((x + 12 - i * 5, y0 - (4 if i % 2 else 0) + round(math.sin(t * 6 + i) * 1.5)))
    pts.append((x - 14, y0))
    pts.append((x - 12, y0 - 26))
    poli(s, (34, 38, 56), pts)
    # Capuz escuro com olhos
    pygame.draw.ellipse(s, (8, 8, 14), (x - 6, y0 - 34, 12, 11))
    brilho = (120, 245, 255)
    olho(s, x - 3, y0 - 29, brilho)
    olho(s, x + 3, y0 - 29, brilho)
    # Mãos esqueléticas e foice
    pygame.draw.line(s, (230, 226, 210), (x + 8, y0 - 18), (x + 12, y0 - 20), 2)
    pygame.draw.line(s, (96, 72, 52), (x + 14, y0 + 2), (x + 10, y0 - 46), 2)
    pts_lamina = [(x + 10, y0 - 46), (x - 12, y0 - 42), (x - 18, y0 - 34), (x - 8, y0 - 40)]
    pygame.draw.polygon(s, (200, 240, 255), pts_lamina)
    pygame.draw.line(s, (255, 255, 255), pts_lamina[0], pts_lamina[1])
    pygame.draw.line(s, (60, 150, 180), pts_lamina[2], pts_lamina[3])
    # Almas orbitando
    for i in range(4):
        a = -t * 1.6 + i * math.tau / 4
        px, py = x + round(math.cos(a) * 20), y0 - 18 + round(math.sin(a) * 8)
        pygame.draw.circle(s, (130, 240, 255), (px, py), 2)
        s.set_at((px, py + 3), (90, 180, 210))


# ------------------------------------------------------------------ 7. Leviatã Aquático
def leviata_aquatico(c, s, x, y, t):
    azul = (50, 130, 220)
    # Redemoinho
    for i in range(3):
        r = 18 - i * 4
        pygame.draw.ellipse(s, (70 + i * 40, 160 + i * 30, 240), (x - r, y - 5 - i, r * 2, 8), 1)
    # Pescoço em arco
    for i in range(7):
        k = i / 6
        nx = x + round(math.sin(t * 2 + k * 2) * 6 * (1 - k)) - round(k * 2)
        ny = y - 4 - i * 6
        r = 10 - i
        oval(s, azul, (nx - r, ny - r // 2 - 1, r * 2, r + 2))
        pygame.draw.line(s, (200, 236, 255), (nx - r // 2, ny + r // 3), (nx + r // 2, ny + r // 3))
    hx, hy = x + round(math.sin(t * 2 + 2) * 2), y - 46
    # Cabeça de dragão marinho
    poli(s, (60, 150, 235), [(hx - 9, hy + 4), (hx - 7, hy - 6), (hx + 7, hy - 6), (hx + 11, hy + 2), (hx + 6, hy + 7), (hx - 6, hy + 7)])
    for lado in (-1, 1):
        poli(s, (120, 230, 255), [(hx + lado * 6, hy - 5), (hx + lado * 14, hy - 12), (hx + lado * 9, hy - 2)])
    olho(s, hx - 4, hy - 2, (230, 255, 255))
    olho(s, hx + 4, hy - 2, (230, 255, 255))
    pygame.draw.line(s, (20, 40, 80), (hx - 5, hy + 4), (hx + 6, hy + 4))
    # Gotas
    for i in range(4):
        fase = (t * 1.5 + i * 0.25) % 1
        pygame.draw.circle(s, (170, 230, 255), (x - 16 + i * 10, y - 4 - round(math.sin(fase * math.pi) * 10)), 1)


# ------------------------------------------------------------------ 8. Guardião dos Cristais
def guardiao_diamante(c, s, x, y, t):
    # Círculo rúnico no chão
    pygame.draw.ellipse(s, (120, 230, 255), (x - 18, y - 6, 36, 10), 1)
    pygame.draw.ellipse(s, (200, 150, 255), (x - 13, y - 4, 26, 6), 1)
    halo(s, (140, 230, 255), (x, y - 24), 22, 70)
    nucleo = criar_cristal_3d(x, y - 14, z_base=6.0, raio=9.0, altura=14.0, cor=(140, 220, 255), cor_borda=(40, 80, 130))
    nucleo.atualizar(t * 2.2)
    nucleo.desenhar(s, 0, 0, t)
    # Fragmentos orbitando
    for i in range(4):
        a = t * 1.8 + i * math.tau / 4
        fx, fy = x + round(math.cos(a) * 20), y - 22 + round(math.sin(a) * 8)
        tam = 3 + (i % 2)
        cor = (220, 250, 255) if math.sin(a) > 0 else (120, 180, 230)
        pygame.draw.polygon(s, cor, [(fx, fy - tam - 1), (fx + tam, fy), (fx, fy + tam + 1), (fx - tam, fy)])


# ------------------------------------------------------------------ 9. Troll das Cavernas
def troll_rochas(c, s, x, y, t):
    pele = (126, 140, 104)
    passo = round(math.sin(t * 3) * 1.5)
    caixa(s, (100, 112, 84), (x - 12, y - 11 + passo, 9, 11))
    caixa(s, (100, 112, 84), (x + 3, y - 11 - passo, 9, 11))
    # Barriga e tanga
    oval(s, pele, (x - 16, y - 36, 32, 28))
    oval(s, (160, 172, 130), (x - 9, y - 26, 18, 14), brilho=False)
    poli(s, (120, 80, 46), [(x - 12, y - 13), (x + 12, y - 13), (x + 8, y - 6), (x - 8, y - 6)])
    # Cabeça pequena com presas
    oval(s, (136, 150, 112), (x - 7, y - 44, 14, 12))
    olho(s, x - 3, y - 39, (255, 70, 40))
    olho(s, x + 3, y - 39, (255, 70, 40))
    pygame.draw.line(s, (255, 250, 230), (x - 4, y - 34), (x - 4, y - 31))
    pygame.draw.line(s, (255, 250, 230), (x + 4, y - 34), (x + 4, y - 31))
    # Braço com clava cravejada
    giro = math.sin(t * 2.5) * 0.4
    ombro = (x + 15, y - 30)
    mao = (ombro[0] + round(math.cos(giro) * 8), ombro[1] + 12)
    pygame.draw.line(s, pele, ombro, mao, 5)
    ponta = (mao[0] + round(math.sin(giro) * 4) + 4, mao[1] - 20)
    pygame.draw.line(s, (90, 58, 30), mao, ponta, 4)
    pygame.draw.circle(s, (110, 76, 40), ponta, 6)
    for a in range(0, 360, 60):
        r = math.radians(a)
        pygame.draw.line(s, (200, 200, 210), ponta, (ponta[0] + round(math.cos(r) * 8), ponta[1] + round(math.sin(r) * 8)))
    pygame.draw.line(s, pele, (x - 15, y - 30), (x - 19, y - 16), 5)


# ------------------------------------------------------------------ 10. Yeti Glacial
def yeti_glacial(c, s, x, y, t):
    pelo = (232, 240, 252)
    respira = round(math.sin(t * 2) * 1)
    caixa(s, (200, 212, 232), (x - 12, y - 9, 9, 9))
    caixa(s, (200, 212, 232), (x + 3, y - 9, 9, 9))
    # Corpo peludo com tufos
    corpo = pygame.Rect(x - 17, y - 40 - respira, 34, 34 + respira)
    oval(s, pelo, corpo)
    for i in range(8):
        a = math.pi + i * math.pi / 7
        px = corpo.centerx + round(math.cos(a) * 17)
        py = corpo.centery + round(math.sin(a) * 17)
        pygame.draw.polygon(s, pelo, [(px - 3, py + 2), (px + 3, py + 2), (px + round(math.cos(a) * 5), py + round(math.sin(a) * 5))])
    # Rosto azulado e chifres de gelo
    oval(s, (110, 170, 220), (x - 7, y - 33, 14, 11), brilho=False)
    olho(s, x - 3, y - 30, (30, 60, 120))
    olho(s, x + 3, y - 30, (30, 60, 120))
    pygame.draw.rect(s, (40, 70, 120), (x - 3, y - 26, 6, 2))
    s.set_at((x - 2, y - 25), (255, 255, 255))
    s.set_at((x + 1, y - 25), (255, 255, 255))
    for lado in (-1, 1):
        pygame.draw.polygon(s, (150, 220, 255), [(x + lado * 8, y - 38), (x + lado * 18, y - 48), (x + lado * 12, y - 36)])
        # Braços com garras
        bx = x + lado * 19
        pygame.draw.line(s, pelo, (x + lado * 14, y - 32), (bx, y - 16), 6)
        for g in (-2, 0, 2):
            pygame.draw.line(s, (120, 200, 255), (bx + g, y - 14), (bx + g + lado, y - 11))
    # Hálito gélido
    for i in range(3):
        fase = (t * 1.2 + i / 3) % 1
        pygame.draw.circle(s, (220, 245, 255), (x + 4 + round(fase * 10), y - 25 - round(fase * 4)), 1 + i % 2)


# ------------------------------------------------------------------ 11. Valquíria Sombria
def valquiria_caida(c, s, x, y, t):
    bate = round(math.sin(t * 6) * 4)
    # Asas de penas em camadas
    for lado in (-1, 1):
        for k in range(4):
            base = (x + lado * 6, y - 28 + k * 2)
            ponta = (x + lado * (30 - k * 4), y - 44 + k * 7 + bate)
            meio = (x + lado * (16 - k * 2), y - 20 + k * 3)
            cor = (60 + k * 14, 30 + k * 10, 80 + k * 14)
            pygame.draw.polygon(s, cor, [base, ponta, meio])
            pygame.draw.line(s, (230, 190, 90), base, ponta)
    # Saia e pernas
    poli(s, (90, 40, 110), [(x - 9, y - 18), (x + 9, y - 18), (x + 11, y - 6), (x - 11, y - 6)])
    caixa(s, (200, 170, 80), (x - 7, y - 7, 5, 7))
    caixa(s, (200, 170, 80), (x + 2, y - 7, 5, 7))
    # Peitoral dourado
    caixa(s, (226, 190, 80), (x - 8, y - 32, 16, 15), raio=3)
    pygame.draw.polygon(s, (120, 60, 160), [(x, y - 30), (x + 3, y - 25), (x, y - 20), (x - 3, y - 25)])
    # Elmo alado
    caixa(s, (236, 206, 110), (x - 6, y - 42, 12, 10))
    pygame.draw.rect(s, (20, 10, 30), (x - 4, y - 38, 8, 2))
    pygame.draw.rect(s, (255, 90, 160), (x - 3, y - 38, 2, 1))
    for lado in (-1, 1):
        pygame.draw.polygon(s, (250, 250, 255), [(x + lado * 6, y - 40), (x + lado * 13, y - 47), (x + lado * 7, y - 36)])
    # Lança de luz
    pygame.draw.line(s, (180, 150, 80), (x + 13, y), (x + 13, y - 50), 2)
    halo(s, (255, 240, 150), (x + 13, y - 52), 7, 110)
    pygame.draw.polygon(s, (255, 250, 200), [(x + 13, y - 60), (x + 16, y - 51), (x + 10, y - 51)])


# ------------------------------------------------------------------ 12. Cavaleiro Negro
def cavaleiro_negro(c, s, x, y, t):
    aco = (64, 58, 78)
    # Capa rubra ondulando
    onda = round(math.sin(t * 4) * 2)
    poli(s, (170, 26, 42), [(x - 11, y - 34), (x + 11, y - 34), (x + 14 + onda, y - 2), (x - 14 - onda, y - 2)])
    # Pernas e tronco
    caixa(s, aco, (x - 9, y - 12, 7, 12))
    caixa(s, aco, (x + 2, y - 12, 7, 12))
    caixa(s, (78, 72, 94), (x - 11, y - 34, 22, 23), raio=3)
    pygame.draw.line(s, (150, 30, 50), (x, y - 32), (x, y - 14))
    # Ombreiras espinhosas
    for lado in (-1, 1):
        poli(s, (90, 84, 110), [(x + lado * 9, y - 36), (x + lado * 18, y - 34), (x + lado * 16, y - 26), (x + lado * 9, y - 28)])
        pygame.draw.line(s, (200, 200, 220), (x + lado * 15, y - 35), (x + lado * 20, y - 41))
    # Elmo com chifres e visor vermelho
    caixa(s, (84, 78, 100), (x - 7, y - 46, 14, 13))
    brilho = 180 + round(75 * math.sin(t * 6))
    pygame.draw.rect(s, (255, brilho // 4, 60), (x - 5, y - 41, 10, 2))
    for lado in (-1, 1):
        pygame.draw.polygon(s, (220, 214, 200), [(x + lado * 6, y - 45), (x + lado * 13, y - 52), (x + lado * 9, y - 43)])
    # Espadão
    lamina_x = x + 16
    pygame.draw.rect(s, (60, 40, 30), (lamina_x - 1, y - 22, 3, 8))
    pygame.draw.rect(s, (200, 160, 60), (lamina_x - 4, y - 24, 9, 2))
    pygame.draw.polygon(s, (190, 196, 214), [(lamina_x - 2, y - 24), (lamina_x + 3, y - 24), (lamina_x + 1, y - 54)])
    pygame.draw.line(s, (250, 250, 255), (lamina_x - 1, y - 25), (lamina_x + 1, y - 52))


# ------------------------------------------------------------------ 13. Quimera Abissal
def quimera_abissal(c, s, x, y, t):
    corpo_c = (196, 96, 52)
    passo = round(math.sin(t * 5) * 1.5)
    # Cauda de serpente
    for i in range(5):
        px = x - 14 - i * 3
        py = y - 14 - i * 4 + round(math.sin(t * 4 + i) * 2)
        pygame.draw.circle(s, (80, 150, 70), (px, py), 3 - i // 2)
    pygame.draw.circle(s, (90, 170, 80), (x - 28, y - 32), 4)
    olho(s, x - 29, y - 33, (255, 230, 60))
    # Patas
    for dx, fase in ((-12, passo), (-6, -passo), (6, passo), (12, -passo)):
        caixa(s, (160, 74, 40), (x + dx - 2, y - 10 + fase, 5, 10 - fase))
    # Corpo de leão
    oval(s, corpo_c, (x - 17, y - 26, 34, 18))
    # Asas de morcego
    for lado in (-1, 1):
        pts = [(x + lado * 2, y - 24), (x + lado * 16, y - 42 + passo), (x + lado * 10, y - 30), (x + lado * 20, y - 30)]
        pygame.draw.polygon(s, (90, 30, 40), pts)
    # Cabeça de bode no dorso
    oval(s, (210, 200, 180), (x - 6, y - 36, 10, 9), brilho=False)
    pygame.draw.arc(s, (100, 80, 60), (x - 10, y - 42, 10, 10), 0.5, 3.0, 2)
    # Cabeça de leão com juba flamejante
    hx, hy = x + 14, y - 26
    for i in range(10):
        a = i * math.tau / 10 + t
        r = 9 + round(math.sin(t * 8 + i) * 1.5)
        pygame.draw.circle(s, (255, 130 + (i % 3) * 30, 40), (hx + round(math.cos(a) * r * 0.8), hy + round(math.sin(a) * r * 0.8)), 3)
    oval(s, (230, 150, 70), (hx - 6, hy - 6, 13, 12))
    olho(s, hx - 2, hy - 2, (255, 240, 80))
    olho(s, hx + 3, hy - 2, (255, 240, 80))
    pygame.draw.rect(s, (60, 10, 10), (hx - 2, hy + 2, 6, 2))
    if math.sin(t * 3) > 0.6:
        for i in range(4):
            pygame.draw.circle(s, (255, 200 - i * 40, 60), (hx + 8 + i * 3, hy + 3), 2 - i // 3)


# ------------------------------------------------------------------ 14. Arquimago Corrompido
def arquimago(c, s, x, y, t):
    flutua = round(math.sin(t * 2.2) * 2)
    y0 = y - 4 + flutua
    # Círculos arcanos girando atrás
    for i, (r, cor) in enumerate(((22, (180, 90, 255)), (15, (120, 220, 255)))):
        pygame.draw.circle(s, cor, (x, y0 - 26), r, 1)
        for k in range(6):
            a = t * (1.2 if i == 0 else -1.8) + k * math.tau / 6
            s.set_at((x + round(math.cos(a) * r), y0 - 26 + round(math.sin(a) * r)), (255, 255, 255))
    # Túnica estrelada
    poli(s, (54, 26, 96), [(x - 5, y0 - 30), (x + 5, y0 - 30), (x + 13, y0), (x - 13, y0)])
    for k in range(4):
        s.set_at((x - 6 + k * 4, y0 - 8 - (k % 2) * 6), (255, 230, 120))
    pygame.draw.line(s, (220, 180, 80), (x - 13, y0 - 1), (x + 12, y0 - 1))
    # Capuz com olhos brilhantes e barba
    poli(s, (70, 34, 120), [(x - 8, y0 - 28), (x + 8, y0 - 28), (x + 3, y0 - 44), (x - 6, y0 - 38)])
    pygame.draw.ellipse(s, (14, 8, 24), (x - 5, y0 - 37, 10, 8))
    olho(s, x - 2, y0 - 34, (255, 120, 255))
    olho(s, x + 2, y0 - 34, (255, 120, 255))
    pygame.draw.polygon(s, (200, 200, 214), [(x - 4, y0 - 30), (x + 4, y0 - 30), (x, y0 - 20)])
    # Cajado com olho arcano
    pygame.draw.line(s, (90, 60, 40), (x - 13, y0 + 1), (x - 13, y0 - 42), 2)
    halo(s, (200, 120, 255), (x - 13, y0 - 45), 9, 100)
    pygame.draw.ellipse(s, (255, 255, 255), (x - 17, y0 - 48, 8, 6))
    pygame.draw.rect(s, (150, 40, 220), (x - 14, y0 - 47, 2, 3))
    # Grimório flutuante
    lx, ly = x + 15, y0 - 24 + round(math.sin(t * 3) * 2)
    caixa(s, (140, 40, 60), (lx - 4, ly - 3, 8, 6), raio=1)
    pygame.draw.line(s, (240, 230, 200), (lx - 3, ly - 2), (lx - 3, ly + 1))


# ------------------------------------------------------------------ 15. Paladino do Juízo
def paladino_juizo(c, s, x, y, t):
    # Auréola
    halo(s, (255, 230, 120), (x, y - 52), 10, 80)
    pygame.draw.ellipse(s, (255, 236, 130), (x - 8, y - 56, 16, 5), 2)
    # Capa branca
    poli(s, (232, 228, 216), [(x - 12, y - 36), (x + 12, y - 36), (x + 14, y - 3), (x - 14, y - 3)])
    caixa(s, (210, 190, 120), (x - 9, y - 12, 7, 12))
    caixa(s, (210, 190, 120), (x + 2, y - 12, 7, 12))
    # Armadura e tabardo com cruz
    caixa(s, (236, 214, 130), (x - 11, y - 36, 22, 25), raio=3)
    poli(s, (246, 244, 236), [(x - 6, y - 32), (x + 6, y - 32), (x + 7, y - 12), (x - 7, y - 12)], luz=False)
    pygame.draw.rect(s, (220, 170, 50), (x - 1, y - 30, 3, 14))
    pygame.draw.rect(s, (220, 170, 50), (x - 5, y - 26, 11, 3))
    for lado in (-1, 1):
        oval(s, (250, 226, 140), (x + lado * 13 - 6, y - 39, 12, 8))
    # Elmo
    caixa(s, (246, 226, 150), (x - 7, y - 48, 14, 13))
    pygame.draw.rect(s, (40, 30, 10), (x - 5, y - 43, 10, 2))
    pygame.draw.rect(s, (40, 30, 10), (x - 1, y - 43, 2, 6))
    # Martelo do juízo
    giro = math.sin(t * 2) * 3
    pygame.draw.line(s, (140, 96, 50), (x + 16, y - 4), (x + 18, y - 40 + round(giro)), 3)
    caixa(s, (250, 240, 190), (x + 10, y - 48 + round(giro), 16, 10))
    pygame.draw.rect(s, (230, 180, 60), (x + 16, y - 47 + round(giro), 4, 8))


# ------------------------------------------------------------------ 16. A Entidade Maligna
def entidade_maligna(c, s, x, y, t):
    fase2 = getattr(c, "fase", 1) == 2
    flut = round(math.sin(t * 3.5) * 3)
    y0 = y - flut
    # Tentáculos de sombra
    for i in range(6):
        a0 = math.pi * (0.15 + i * 0.14)
        px, py = x, y0 - 6
        for k in range(5):
            a = a0 + math.sin(t * 3 + i + k * 0.6) * 0.3
            nx, ny = px + round(math.cos(a) * 5), py + round(math.sin(a) * 3) + 1
            pygame.draw.line(s, (40, 10, 50), (px, py), (nx, ny), 3 - k // 2)
            px, py = nx, ny
    # Asas demoníacas
    for lado in (-1, 1):
        bate = round(math.sin(t * 4.5) * 6)
        ombro = (x + lado * 10, y0 - 32)
        dedos = [(x + lado * 44, y0 - 52 + bate), (x + lado * 46, y0 - 32 + bate), (x + lado * 38, y0 - 16 + bate)]
        membrana = [ombro] + dedos + [(x + lado * 16, y0 - 12)]
        pygame.draw.polygon(s, (48, 12, 46) if not fase2 else (80, 16, 40), membrana)
        for d in dedos:
            pygame.draw.line(s, (235, 45, 95), ombro, d, 1)
    # Corpo
    oval(s, (60, 20, 70), (x - 18, y0 - 42, 36, 38))
    # Chifres
    for lado in (-1, 1):
        pygame.draw.polygon(s, (220, 210, 200), [(x + lado * 7, y0 - 40), (x + lado * 18, y0 - 58), (x + lado * 12, y0 - 38)])
    # Múltiplos olhos
    for ex, ey in ((-7, -32), (7, -32), (0, -36), (-4, -26), (4, -26)):
        pisca = math.sin(t * 2 + ex) > -0.9
        if pisca:
            olho(s, x + ex, y0 + ey, (255, 50, 80) if not fase2 else (255, 220, 80))
    # Rachaduras incandescentes na fase 2
    if fase2:
        for k in range(4):
            a = k * math.tau / 4 + 0.4
            pygame.draw.line(s, (255, 180, 60), (x, y0 - 20), (x + round(math.cos(a) * 14), y0 - 20 + round(math.sin(a) * 14)))
    nucleo = criar_cristal_3d(x, y0 - 12, z_base=6.0, raio=6.0, altura=9.0, cor=(235, 35, 95), cor_borda=(85, 12, 40))
    nucleo.atualizar(t * 2.2)
    nucleo.desenhar(s, 0, 0, t)


ARTE = {
    "rei_slime": rei_slime,
    "golem_pedra": golem_pedra,
    "serpente_dunas": serpente_dunas,
    "colosso_solar": colosso_solar,
    "bruxa_brumas": bruxa_brumas,
    "ceifador_espectral": ceifador_espectral,
    "leviata_aquatico": leviata_aquatico,
    "guardiao_diamante": guardiao_diamante,
    "troll_rochas": troll_rochas,
    "yeti_glacial": yeti_glacial,
    "valquiria_caida": valquiria_caida,
    "cavaleiro_negro": cavaleiro_negro,
    "quimera_abissal": quimera_abissal,
    "arquimago": arquimago,
    "paladino_juizo": paladino_juizo,
    "entidade_maligna": entidade_maligna,
}
