"""Temas visuais dos covis de chefes.

Cada covil declara no próprio mapa (`[mapa] tema = lava`) qual tema usa.
O tema troca o chão, o líquido (`~`), as paredes (`W`), os blocos 3D (`#`),
as decorações espalhadas pelo chão, as partículas no ar e a iluminação,
para que cada arena combine com o Guardião que mora ali.

Tudo é gerado proceduralmente (pixel art 16x16), sem arquivos extras.
"""
import math
import random

import pygame

from settings import TILE


def _cor(c, delta):
    return tuple(max(0, min(255, v + delta)) for v in c[:3])


def _mistura(a, b, f):
    return tuple(round(a[i] * (1 - f) + b[i] * f) for i in range(3))


# ---------------------------------------------------------------------------
# Catálogo de temas
# ---------------------------------------------------------------------------
# chao:      (cor base, cor clara, cor escura) e o padrão do piso
# liquido:   (base, brilho, escura), tipo de animação e se dá para nadar
# bloco:     cores da extrusão 3D do "#" (topo, esquerda, direita, frente, borda)
# parede:    (base, clara, escura) dos tijolos do "W"
# decor:     decorações espalhadas no chão
# particulas:(tipo, cor, quantidade)
# luz:       (cor, alfa) da penumbra; brilhos: o líquido ilumina o ambiente
TEMAS = {
    "gosma": {
        "chao": ((62, 104, 78), (88, 136, 98), (40, 72, 56)), "padrao": "musgo",
        "liquido": ((70, 196, 120), (170, 255, 190), (34, 120, 76)), "anim": "gosma", "nadavel": False,
        "bloco": ((88, 150, 110), (66, 116, 86), (48, 88, 64), (42, 76, 56), (24, 44, 34)),
        "parede": ((54, 86, 70), (80, 120, 96), (32, 54, 44)),
        "decor": "gosma", "particulas": ("bolhas", (150, 255, 190), 26),
        "luz": ((10, 30, 26), 92), "brilha": True, "margem": (40, 120, 76),
    },
    "ruinas": {
        "chao": ((120, 118, 108), (150, 148, 136), (88, 86, 80)), "padrao": "lajes",
        "liquido": ((60, 120, 160), (150, 210, 240), (34, 76, 110)), "anim": "agua", "nadavel": True,
        "bloco": ((150, 150, 140), (118, 118, 110), (88, 88, 84), (78, 78, 74), (40, 40, 40)),
        "parede": ((104, 102, 96), (138, 136, 126), (70, 68, 64)),
        "decor": "runas", "particulas": ("poeira", (220, 214, 190), 22),
        "luz": ((14, 18, 30), 96), "brilha": False, "margem": (120, 112, 96),
    },
    "areia": {
        "chao": ((214, 176, 106), (236, 204, 140), (182, 142, 80)), "padrao": "areia",
        "liquido": ((168, 124, 70), (206, 166, 104), (122, 86, 46)), "anim": "areia", "nadavel": False,
        "bloco": ((206, 160, 96), (172, 128, 72), (138, 98, 54), (124, 88, 48), (78, 52, 28)),
        "parede": ((176, 132, 78), (212, 170, 110), (130, 92, 50)),
        "decor": "ossos_areia", "particulas": ("areia", (240, 210, 150), 40),
        "luz": ((120, 70, 20), 38), "brilha": False, "margem": (150, 110, 60),
    },
    "solar": {
        "chao": ((214, 184, 120), (246, 222, 160), (170, 136, 80)), "padrao": "marmore",
        "liquido": ((255, 168, 40), (255, 240, 150), (210, 90, 20)), "anim": "lava", "nadavel": False,
        "bloco": ((240, 206, 120), (206, 168, 84), (168, 128, 56), (150, 112, 48), (90, 62, 24)),
        "parede": ((196, 160, 92), (232, 200, 130), (150, 112, 56)),
        "decor": "sol", "particulas": ("brasas", (255, 210, 90), 30),
        "luz": ((140, 70, 10), 30), "brilha": True, "margem": (190, 120, 40),
    },
    "pantano": {
        "chao": ((70, 74, 52), (92, 98, 66), (46, 50, 36)), "padrao": "lama",
        "liquido": ((88, 64, 120), (170, 120, 220), (52, 36, 76)), "anim": "veneno", "nadavel": False,
        "bloco": ((92, 84, 70), (72, 66, 54), (54, 50, 40), (48, 44, 36), (26, 24, 20)),
        "parede": ((62, 58, 46), (86, 82, 64), (40, 38, 30)),
        "decor": "cogumelos", "particulas": ("esporos", (190, 140, 255), 34),
        "luz": ((26, 12, 40), 118), "brilha": True, "margem": (60, 70, 44),
    },
    "sepulcro": {
        "chao": ((70, 72, 84), (94, 96, 110), (48, 50, 60)), "padrao": "lajes",
        "liquido": ((16, 12, 26), (90, 200, 220), (6, 4, 12)), "anim": "vazio", "nadavel": False,
        "bloco": ((120, 124, 140), (92, 96, 110), (68, 70, 84), (60, 62, 74), (28, 28, 36)),
        "parede": ((58, 60, 72), (84, 86, 100), (36, 38, 48)),
        "decor": "ossos", "particulas": ("almas", (130, 240, 255), 18),
        "luz": ((6, 14, 26), 140), "brilha": True, "margem": (40, 42, 54),
    },
    "abismo_mar": {
        "chao": ((176, 160, 120), (204, 190, 150), (138, 124, 92)), "padrao": "areia",
        "liquido": ((36, 92, 168), (140, 210, 255), (18, 54, 112)), "anim": "agua", "nadavel": True,
        "bloco": ((96, 150, 150), (70, 118, 124), (50, 88, 96), (44, 78, 86), (20, 40, 48)),
        "parede": ((64, 100, 112), (96, 140, 150), (40, 66, 78)),
        "decor": "conchas", "particulas": ("bolhas", (180, 230, 255), 30),
        "luz": ((6, 30, 70), 104), "brilha": True, "margem": (210, 200, 160),
    },
    "cristal": {
        "chao": ((54, 44, 92), (78, 66, 128), (36, 28, 64)), "padrao": "cristal",
        "liquido": ((70, 200, 255), (220, 250, 255), (30, 110, 190)), "anim": "mana", "nadavel": False,
        "bloco": ((150, 230, 255), (96, 180, 230), (60, 130, 190), (54, 112, 170), (24, 48, 90)),
        "parede": ((70, 58, 120), (104, 92, 160), (44, 36, 82)),
        "decor": "cristais", "particulas": ("brilhos", (190, 245, 255), 34),
        "luz": ((14, 6, 40), 118), "brilha": True, "margem": (110, 150, 220),
    },
    "caverna": {
        "chao": ((112, 88, 66), (138, 112, 86), (82, 64, 48)), "padrao": "rocha",
        "liquido": ((50, 96, 120), (130, 190, 210), (28, 60, 80)), "anim": "agua", "nadavel": True,
        "bloco": ((140, 112, 84), (112, 88, 64), (86, 66, 48), (76, 58, 42), (40, 30, 22)),
        "parede": ((96, 74, 56), (126, 100, 76), (64, 48, 36)),
        "decor": "pedregulhos", "particulas": ("poeira", (200, 170, 130), 26),
        "luz": ((20, 12, 8), 132), "brilha": False, "margem": (90, 74, 56),
    },
    "gelo": {
        "chao": ((196, 226, 244), (232, 246, 255), (150, 192, 222)), "padrao": "gelo",
        "liquido": ((80, 150, 210), (210, 240, 255), (44, 100, 160)), "anim": "agua", "nadavel": False,
        "bloco": ((220, 244, 255), (170, 214, 240), (124, 176, 214), (110, 160, 200), (60, 96, 140)),
        "parede": ((150, 190, 220), (200, 230, 250), (100, 140, 180)),
        "decor": "neve", "particulas": ("neve", (255, 255, 255), 46),
        "luz": ((30, 60, 110), 64), "brilha": False, "margem": (236, 248, 255),
    },
    "celeste": {
        "chao": ((228, 226, 238), (250, 250, 255), (188, 186, 208)), "padrao": "marmore",
        "liquido": ((150, 190, 240), (255, 255, 255), (100, 140, 210)), "anim": "nuvem", "nadavel": False,
        "bloco": ((250, 246, 230), (214, 206, 180), (178, 168, 140), (160, 150, 124), (110, 96, 60)),
        "parede": ((214, 210, 226), (244, 242, 252), (170, 166, 190)),
        "decor": "ouro", "particulas": ("penas", (255, 250, 230), 22),
        "luz": ((80, 60, 120), 34), "brilha": False, "margem": (255, 236, 160),
    },
    "arena": {
        "chao": ((150, 116, 82), (178, 142, 104), (116, 88, 60)), "padrao": "terra",
        "liquido": ((120, 24, 30), (220, 70, 70), (70, 10, 16)), "anim": "lava", "nadavel": False,
        "bloco": ((110, 112, 124), (84, 86, 98), (62, 64, 76), (56, 58, 68), (24, 24, 30)),
        "parede": ((84, 70, 64), (112, 96, 86), (56, 46, 42)),
        "decor": "estandartes", "particulas": ("cinzas", (200, 190, 190), 28),
        "luz": ((40, 6, 10), 100), "brilha": True, "margem": (90, 60, 40),
    },
    "lava": {
        "chao": ((54, 40, 44), (78, 60, 62), (34, 24, 28)), "padrao": "obsidiana",
        "liquido": ((236, 90, 30), (255, 220, 100), (170, 36, 16)), "anim": "lava", "nadavel": False,
        "bloco": ((84, 66, 70), (62, 48, 52), (44, 34, 38), (38, 30, 34), (18, 12, 14)),
        "parede": ((60, 44, 46), (86, 64, 64), (36, 26, 28)),
        "decor": "rachaduras", "particulas": ("brasas", (255, 150, 60), 44),
        "luz": ((50, 8, 4), 112), "brilha": True, "margem": (120, 40, 20),
    },
    "astral": {
        "chao": ((34, 36, 80), (56, 60, 118), (22, 22, 54)), "padrao": "estrelas",
        "liquido": ((20, 14, 48), (200, 160, 255), (8, 4, 24)), "anim": "vazio", "nadavel": False,
        "bloco": ((120, 100, 200), (90, 74, 160), (66, 52, 124), (58, 46, 110), (26, 18, 56)),
        "parede": ((46, 42, 96), (72, 66, 140), (28, 26, 64)),
        "decor": "circulos", "particulas": ("runas", (200, 150, 255), 24),
        "luz": ((14, 6, 46), 120), "brilha": True, "margem": (120, 90, 220),
    },
    "sagrado": {
        "chao": ((232, 224, 200), (252, 248, 232), (196, 184, 150)), "padrao": "xadrez",
        "liquido": ((255, 226, 120), (255, 255, 220), (220, 170, 60)), "anim": "luz", "nadavel": False,
        "bloco": ((246, 236, 210), (214, 196, 150), (180, 160, 112), (164, 142, 96), (110, 86, 40)),
        "parede": ((206, 196, 170), (236, 228, 206), (164, 150, 118)),
        "decor": "ouro", "particulas": ("luz", (255, 240, 170), 30),
        "luz": ((60, 40, 10), 40), "brilha": True, "margem": (220, 180, 80),
    },
    "coliseu": {
        "chao": ((176, 150, 120), (204, 180, 150), (138, 114, 88)), "padrao": "lajes",
        "liquido": ((90, 40, 140), (220, 160, 255), (50, 18, 90)), "anim": "vazio", "nadavel": False,
        "bloco": ((206, 186, 156), (170, 150, 120), (136, 118, 92), (122, 104, 80), (64, 52, 38)),
        "parede": ((150, 126, 100), (186, 162, 134), (110, 90, 70)),
        "decor": "estandartes", "particulas": ("runas", (220, 160, 255), 22),
        "luz": ((40, 10, 60), 96), "brilha": True, "margem": (120, 90, 70),
    },
}

# Tema padrão de cada Guardião (usado pelo Modo Chefões e pelo seletor).
TEMA_POR_CHEFE = {
    "rei_slime": "gosma",
    "golem_pedra": "ruinas",
    "serpente_dunas": "areia",
    "colosso_solar": "solar",
    "bruxa_brumas": "pantano",
    "ceifador_espectral": "sepulcro",
    "leviata_aquatico": "abismo_mar",
    "guardiao_diamante": "cristal",
    "troll_rochas": "caverna",
    "yeti_glacial": "gelo",
    "valquiria_caida": "celeste",
    "cavaleiro_negro": "arena",
    "quimera_abissal": "lava",
    "arquimago": "astral",
    "paladino_juizo": "sagrado",
    "entidade_maligna": "coliseu",
}


def obter_tema(nome):
    """Devolve o dicionário do tema (com o nome) ou None."""
    if not nome or nome not in TEMAS:
        return None
    return {"nome": nome, **TEMAS[nome]}


# ---------------------------------------------------------------------------
# Geração dos tiles
# ---------------------------------------------------------------------------
def _piso(tema, semente):
    base, clara, escura = tema["chao"]
    padrao = tema["padrao"]
    rnd = random.Random(semente * 7919 + sum(map(ord, tema["nome"])))
    s = pygame.Surface((TILE, TILE))
    s.fill(base)

    def pontos(qtd, cores):
        for _ in range(qtd):
            s.set_at((rnd.randrange(TILE), rnd.randrange(TILE)), rnd.choice(cores))

    if padrao == "lajes":
        # Lajes de pedra deslocadas, com quina iluminada e rejunte escuro
        meio = 8 if semente % 2 == 0 else 0
        for y in (0, 8):
            pygame.draw.line(s, escura, (0, y), (TILE - 1, y))
            pygame.draw.line(s, clara, (0, y + 1), (TILE - 1, y + 1))
        for x in ((meio + 4) % TILE, (meio + 12) % TILE):
            pygame.draw.line(s, escura, (x, 1), (x, 7))
        for x in ((meio + 0) % TILE, (meio + 8) % TILE):
            pygame.draw.line(s, escura, (x, 9), (x, 15))
        pontos(10, [clara, escura])
    elif padrao == "areia":
        pontos(28, [clara, escura, _cor(base, 10)])
        for k in range(2):
            y0 = rnd.randrange(3, 13)
            for x in range(TILE):
                y = y0 + round(math.sin((x + semente * 3) * 0.6 + k) * 1.2)
                if 0 <= y < TILE:
                    s.set_at((x, y), clara)
                    if y + 1 < TILE:
                        s.set_at((x, y + 1), escura)
    elif padrao == "gelo":
        for i in range(-TILE, TILE, 6):
            pygame.draw.line(s, clara, (i, TILE), (i + TILE, 0))
        x, y = rnd.randrange(TILE), rnd.randrange(TILE)
        for _ in range(6):
            nx, ny = x + rnd.choice((-2, -1, 1, 2)), y + rnd.choice((1, 2))
            pygame.draw.line(s, escura, (x, y), (nx, ny))
            x, y = nx, ny
        pontos(6, [(255, 255, 255)])
    elif padrao == "musgo":
        pontos(20, [escura, clara])
        for _ in range(3):
            cx, cy = rnd.randrange(TILE), rnd.randrange(TILE)
            pygame.draw.circle(s, clara, (cx, cy), rnd.randint(1, 3))
            s.set_at((cx, cy), _cor(clara, 30))
    elif padrao == "lama":
        pontos(24, [escura, clara])
        if semente % 3 == 0:
            pygame.draw.ellipse(s, escura, (3, 6, 10, 5))
            pygame.draw.line(s, clara, (5, 7), (9, 7))
    elif padrao == "rocha":
        for _ in range(4):
            r = pygame.Rect(rnd.randrange(-2, 12), rnd.randrange(-2, 12), rnd.randint(4, 8), rnd.randint(3, 6))
            pygame.draw.ellipse(s, clara if rnd.random() < 0.5 else escura, r)
        pygame.draw.line(s, escura, (rnd.randrange(TILE), 0), (rnd.randrange(TILE), TILE - 1))
        pontos(10, [escura])
    elif padrao == "cristal":
        for _ in range(3):
            x, y = rnd.randrange(TILE), rnd.randrange(TILE)
            pts = [(x, y), (x + rnd.randint(3, 7), y + rnd.randint(-3, 3)), (x + rnd.randint(0, 4), y + rnd.randint(3, 6))]
            pygame.draw.polygon(s, clara, pts)
            pygame.draw.line(s, _cor(clara, 50), pts[0], pts[1])
        pontos(4, [(200, 240, 255)])
    elif padrao == "marmore":
        pygame.draw.rect(s, escura, (0, 0, TILE, TILE), 1)
        pygame.draw.line(s, clara, (1, 1), (TILE - 2, 1))
        pygame.draw.line(s, clara, (1, 1), (1, TILE - 2))
        x, y = rnd.randrange(2, 14), 1
        while y < TILE - 2:
            nx = max(1, min(TILE - 2, x + rnd.choice((-1, 0, 1))))
            s.set_at((nx, y), _mistura(base, escura, 0.6))
            x, y = nx, y + 1
    elif padrao == "xadrez":
        if semente % 2:
            s.fill(_mistura(base, escura, 0.55))
        pygame.draw.rect(s, escura, (0, 0, TILE, TILE), 1)
        pygame.draw.line(s, clara, (1, 1), (TILE - 2, 1))
        pygame.draw.rect(s, (230, 190, 90), (7, 7, 2, 2))
    elif padrao == "obsidiana":
        pontos(14, [clara, escura])
        if semente % 2 == 0:
            x, y = rnd.randrange(TILE), 0
            for _ in range(8):
                nx, ny = x + rnd.choice((-2, -1, 1, 2)), y + 2
                pygame.draw.line(s, (200, 70, 30), (x, y), (nx, ny))
                x, y = nx, ny
    elif padrao == "estrelas":
        pygame.draw.rect(s, escura, (0, 0, TILE, TILE), 1)
        pontos(5, [(230, 220, 255), (160, 150, 230)])
    elif padrao == "terra":
        pontos(30, [clara, escura])
        for _ in range(2):
            pygame.draw.rect(s, _cor(base, -26), (rnd.randrange(TILE - 2), rnd.randrange(TILE - 2), 2, 1))
    return s


def _parede(tema, semente):
    base, clara, escura = tema["parede"]
    s = pygame.Surface((TILE, TILE))
    s.fill(base)
    deslocar = 4 if semente % 2 else 0
    for y in (0, 5, 10, 15):
        pygame.draw.line(s, escura, (0, y), (TILE - 1, y))
    for i, y in enumerate((0, 5, 10)):
        off = (deslocar + i * 4) % 8
        for x in range(off, TILE, 8):
            pygame.draw.line(s, escura, (x, y + 1), (x, y + 4))
            pygame.draw.line(s, clara, (x + 1, y + 1), (min(TILE - 1, x + 6), y + 1))
    return s


def _bloco(tema):
    """Topo do bloco 3D (#), com chanfro e um símbolo do tema entalhado."""
    topo, esq, _dir, _frente, borda = tema["bloco"]
    s = pygame.Surface((TILE, TILE))
    s.fill(topo)
    clara = _cor(topo, 28)
    pygame.draw.rect(s, esq, (2, 2, TILE - 4, TILE - 4), 1)
    pygame.draw.line(s, clara, (1, 1), (TILE - 2, 1))
    pygame.draw.line(s, clara, (1, 1), (1, TILE - 2))
    pygame.draw.rect(s, borda, (0, 0, TILE, TILE), 1)
    nome = tema["nome"]
    meio = TILE // 2
    if nome == "sepulcro":  # lápide com cruz
        pygame.draw.line(s, borda, (meio, 4), (meio, 11))
        pygame.draw.line(s, borda, (meio - 3, 6), (meio + 3, 6))
    elif nome == "cristal":
        pygame.draw.polygon(s, (230, 252, 255), [(meio, 3), (meio + 4, meio), (meio, 12), (meio - 4, meio)], 1)
    elif nome in ("solar", "sagrado", "celeste"):
        pygame.draw.polygon(s, (240, 190, 70), [(meio, 4), (meio + 3, meio), (meio, 11), (meio - 3, meio)])
    elif nome == "gosma":
        pygame.draw.rect(s, (110, 220, 150), (4, 3, 8, 3))
        pygame.draw.rect(s, (110, 220, 150), (6, 6, 2, 4))
    elif nome == "lava":
        pygame.draw.line(s, (255, 120, 40), (4, 4), (8, 9))
        pygame.draw.line(s, (255, 120, 40), (8, 9), (11, 7))
    elif nome == "astral":
        pygame.draw.line(s, (200, 160, 255), (meio, 4), (meio, 11))
        pygame.draw.line(s, (200, 160, 255), (4, meio), (11, meio))
    elif nome == "ruinas":
        pygame.draw.rect(s, (90, 220, 255), (meio - 1, 5, 2, 6))
    elif nome == "gelo":
        pygame.draw.line(s, (255, 255, 255), (3, 10), (10, 3))
    return s


def _liquido(tema, quadro):
    base, brilho, escura = tema["liquido"]
    anim = tema["anim"]
    s = pygame.Surface((TILE, TILE))
    s.fill(base)
    rnd = random.Random(31 + quadro)
    fase = quadro * (math.tau / 4)
    if anim in ("agua", "nuvem", "areia"):
        for k in range(3):
            y = 3 + k * 5
            for x in range(TILE):
                if math.sin(x * 0.7 + fase + k * 1.7) > 0.55:
                    s.set_at((x, y), brilho if anim != "areia" else escura)
        if anim == "nuvem":
            for _ in range(3):
                pygame.draw.circle(s, brilho, (rnd.randrange(TILE), rnd.randrange(TILE)), 2)
    elif anim == "lava":
        for _ in range(5):
            x, y = rnd.randrange(TILE), rnd.randrange(TILE)
            pygame.draw.circle(s, escura, (x, y), 2)
        for x in range(TILE):
            y = 8 + round(math.sin(x * 0.5 + fase) * 3)
            s.set_at((x, y % TILE), brilho)
            s.set_at((x, (y + 1) % TILE), _mistura(base, brilho, 0.5))
    elif anim in ("gosma", "veneno", "mana", "luz"):
        for _ in range(4):
            x, y = rnd.randrange(2, TILE - 2), rnd.randrange(2, TILE - 2)
            pygame.draw.circle(s, brilho if anim != "veneno" else _mistura(base, brilho, 0.6), (x, y), 1 + quadro % 2)
        for x in range(TILE):
            if math.sin(x * 0.9 + fase) > 0.6:
                s.set_at((x, 2 + quadro * 3 % 12), _mistura(base, brilho, 0.5))
    elif anim == "vazio":
        s.fill(escura)
        for _ in range(4):
            s.set_at((rnd.randrange(TILE), rnd.randrange(TILE)), brilho if rnd.random() < 0.3 else _mistura(escura, brilho, 0.35))
    return s


class GraficosTema:
    """Tiles gerados para um tema (cacheados por nome do tema)."""

    _cache = {}

    def __new__(cls, tema):
        nome = tema["nome"]
        if nome not in cls._cache:
            obj = super().__new__(cls)
            obj.pisos = [_piso(tema, i) for i in range(6)]
            obj.paredes = [_parede(tema, i) for i in range(2)]
            obj.bloco = _bloco(tema)
            obj.liquido = [_liquido(tema, q) for q in range(4)]
            cls._cache[nome] = obj
        return cls._cache[nome]


# ---------------------------------------------------------------------------
# Decorações do chão (desenhadas uma vez na camada de detalhes)
# ---------------------------------------------------------------------------
def desenhar_decoracao(det, tema, px, py, h_val):
    tipo = tema["decor"]
    base, clara, escura = tema["chao"]
    if h_val % 9 not in (2, 5):
        return
    x, y = px + 3 + h_val % 8, py + 3 + (h_val // 3) % 8
    if tipo == "gosma":
        pygame.draw.ellipse(det, (90, 210, 130, 200), (x - 2, y, 7, 3))
        det.set_at((x, y), (200, 255, 220, 255))
    elif tipo == "runas":
        cor = (90, 220, 255, 200)
        pygame.draw.rect(det, cor, (x, y, 3, 1))
        pygame.draw.rect(det, cor, (x + 1, y, 1, 4))
    elif tipo in ("ossos", "ossos_areia"):
        cor = (226, 218, 196, 240)
        pygame.draw.line(det, cor, (x, y), (x + 4, y + 2))
        det.set_at((x - 1, y), cor)
        det.set_at((x + 5, y + 2), cor)
        if h_val % 2:
            pygame.draw.circle(det, cor, (x + 2, y - 3), 2)
            det.set_at((x + 1, y - 3), (30, 26, 30, 255))
    elif tipo == "sol":
        pygame.draw.circle(det, (255, 210, 90, 150), (px + 8, py + 8), 3, 1)
    elif tipo == "cogumelos":
        pygame.draw.rect(det, (230, 220, 200, 255), (x, y, 1, 2))
        pygame.draw.rect(det, (180, 110, 255, 255), (x - 1, y - 1, 3, 1))
    elif tipo == "conchas":
        pygame.draw.circle(det, (250, 210, 210, 255), (x, y), 2)
        det.set_at((x, y), (200, 140, 150, 255))
    elif tipo == "cristais":
        pygame.draw.polygon(det, (150, 235, 255, 240), [(x, y - 4), (x - 2, y), (x + 2, y)])
        det.set_at((x, y - 3), (255, 255, 255, 255))
    elif tipo == "pedregulhos":
        pygame.draw.ellipse(det, (*escura, 255), (x - 1, y, 5, 3))
        det.set_at((x, y), (*clara, 255))
    elif tipo == "neve":
        pygame.draw.ellipse(det, (255, 255, 255, 230), (x - 2, y, 6, 3))
    elif tipo == "ouro":
        pygame.draw.rect(det, (236, 196, 90, 200), (x, y, 2, 2))
    elif tipo == "estandartes":
        pygame.draw.circle(det, (110, 30, 30, 120), (x, y), 2)
    elif tipo == "rachaduras":
        pygame.draw.line(det, (255, 120, 40, 230), (x, y), (x + 3, y + 2))
        pygame.draw.line(det, (255, 120, 40, 230), (x + 3, y + 2), (x + 2, y + 5))
    elif tipo == "circulos":
        if h_val % 18 == 2:
            pygame.draw.circle(det, (150, 110, 255, 120), (px + 8, py + 8), 6, 1)


# ---------------------------------------------------------------------------
# Atmosfera: partículas no ar (sem estado, calculadas pelo tempo)
# ---------------------------------------------------------------------------
def desenhar_atmosfera(tela, tema, ox, oy, tempo):
    tipo, cor, qtd = tema["particulas"]
    larg, alt = tela.get_size()
    for i in range(qtd):
        semente = i * 97.13
        vel = 8 + (i * 37) % 23
        fase = (semente % 1.0) * math.tau
        x0 = (i * 53.7 + ox * 0.3) % (larg + 20) - 10
        y0 = (i * 91.3 + oy * 0.3) % (alt + 20) - 10
        if tipo in ("neve", "cinzas", "penas", "luz"):
            y = (y0 + tempo * vel) % (alt + 20) - 10
            x = x0 + math.sin(tempo * 1.4 + fase) * 6
        elif tipo in ("brasas", "bolhas", "almas", "esporos", "runas", "brilhos"):
            y = (y0 - tempo * vel) % (alt + 20) - 10
            x = x0 + math.sin(tempo * 1.8 + fase) * 4
        else:  # poeira / areia: sopra de lado
            x = (x0 + tempo * vel * (3 if tipo == "areia" else 1)) % (larg + 20) - 10
            y = y0 + math.sin(tempo * 2 + fase) * 2
        x, y = round(x), round(y)
        pisca = math.sin(tempo * 5 + fase) > -0.3
        if tipo == "bolhas":
            pygame.draw.circle(tela, cor, (x, y), 1 + i % 2, 1)
        elif tipo == "brasas":
            if pisca:
                tela.set_at((x, y), cor) if 0 <= x < larg and 0 <= y < alt else None
                if i % 3 == 0 and 0 <= x < larg and 0 <= y + 1 < alt:
                    tela.set_at((x, y + 1), (255, 90, 40))
        elif tipo == "almas":
            s = pygame.Surface((5, 7), pygame.SRCALPHA)
            pygame.draw.ellipse(s, (*cor, 90), (0, 0, 5, 5))
            pygame.draw.line(s, (*cor, 60), (2, 4), (2 + round(math.sin(tempo * 4 + i)), 6))
            tela.blit(s, (x, y))
        elif tipo == "penas":
            pygame.draw.line(tela, cor, (x, y), (x + 2, y + 1))
        elif tipo == "neve":
            pygame.draw.rect(tela, cor, (x, y, 1 + i % 2, 1 + i % 2))
        elif tipo == "runas":
            if pisca:
                pygame.draw.rect(tela, cor, (x, y, 2, 1))
                pygame.draw.rect(tela, cor, (x, y - 1, 1, 3))
        elif tipo == "brilhos":
            if pisca:
                pygame.draw.line(tela, cor, (x - 1, y), (x + 1, y))
                pygame.draw.line(tela, cor, (x, y - 1), (x, y + 1))
        else:
            if 0 <= x < larg and 0 <= y < alt:
                tela.set_at((x, y), cor)
