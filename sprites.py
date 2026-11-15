"""Gráficos do jogo.

Na primeira execução, cada sprite é desenhado a partir das grades de texto
abaixo e salvo como PNG em assets/sprites/. Daí em diante o jogo carrega o
PNG. Para trocar a arte, é só editar esses PNGs no LibreSprite, Aseprite,
Pixelorama etc., mantendo o mesmo tamanho. Para voltar à arte padrão,
apague o PNG.
"""
import random

import pygame

from personagens import PERSONAGENS, QUADRO, QUADROS_POR_LINHA, folha_personagem
from settings import PASTA_SPRITES, TILE

# Cada caractere das grades vira uma cor. "." é transparente.
PALETA = {
    ".": None,
    "k": (24, 20, 37),  # contorno
    "g": (88, 179, 63),  # túnica
    "G": (52, 120, 50),  # túnica escura
    "s": (247, 200, 160),  # pele
    "h": (140, 82, 48),  # cabelo
    "b": (120, 70, 40),  # cinto / cabo
    "B": (90, 55, 35),  # botas
    "y": (240, 200, 60),  # dourado
    "w": (240, 240, 240),  # branco
    "l": (180, 190, 205),  # lâmina
    "m": (70, 150, 230),  # slime
    "L": (150, 210, 255),  # slime claro
    "d": (40, 90, 170),  # slime escuro
    "r": (220, 40, 60),  # coração
    "e": (70, 40, 50),  # coração vazio
    # Slime verde
    "v": (68, 205, 78),    # slime verde
    "V": (145, 245, 120),  # slime verde claro
    "u": (32, 130, 42),    # slime verde escuro
    # Goblin / Duende
    "o": (115, 175, 55),   # pele goblin
    "O": (75, 125, 35),    # pele goblin escura
    "c": (185, 55, 45),    # capuz duende vermelho
    "C": (130, 35, 30),    # capuz escuro
    # Zumbi Arqueiro
    "z": (100, 145, 125),  # pele zumbi morta
    "Z": (60, 95, 80),     # sombra zumbi
    "R": (255, 60, 60),    # olhos zumbi vermelhos
    "a": (160, 105, 55),   # madeira do arco
    # Troll
    "t": (110, 128, 102),  # pele troll
    "T": (72, 86, 68),     # pele troll escura
    "p": (165, 172, 180),  # pedra da clava
}

# Espada apontando para cima; as outras direções são rotações dela.
ESPADA = [
    ".......kk.......",
    "......kwlk......",
    "......kwlk......",
    "......kwlk......",
    "......kwlk......",
    "......kwlk......",
    "......kwlk......",
    "......kwlk......",
    "......kwlk......",
    "......kwlk......",
    "....kkkkkkkk....",
    "....kyyyyyyk....",
    "....kkkkkkkk....",
    "......kbbk......",
    "......kbbk......",
    "......kkkk......",
]

SLIME_QUADROS = [
    [
        "................",
        "................",
        "................",
        "................",
        "................",
        "......kkkk......",
        "....kkLLLLkk....",
        "...kLLmmmmLLk...",
        "..kmmmmmmmmmmk..",
        "..kmmkmmmmkmmk..",
        ".kmmmmmmmmmmmmk.",
        ".kmmmmmmmmmmmmk.",
        ".kdmmmmmmmmmmdk.",
        "..kddddddddddk..",
        "...kkkkkkkkkk...",
        "................",
    ],
    [
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "....kkkkkkkk....",
        "..kkLLLLLLLLkk..",
        ".kmmkmmmmmmkmmk.",
        "kmmmmmmmmmmmmmmk",
        "kmmmmmmmmmmmmmmk",
        "kdmmmmmmmmmmmmdk",
        ".kddddddddddddk.",
        "..kkkkkkkkkkkk..",
        "................",
    ],
]

SLIME_VERDE_QUADROS = [
    [
        "................",
        "................",
        "................",
        "................",
        "................",
        "......kkkk......",
        "....kkVVVVkk....",
        "...kVVvvvvVVk...",
        "..kvvvvvvvvvvk..",
        "..kvvkvvvvkvvk..",
        ".kvvvvvvvvvvvvk.",
        ".kvvvvvvvvvvvvk.",
        ".kuvvvvvvvvvvuk.",
        "..kuuuuuuuuuuk..",
        "...kkkkkkkkkk...",
        "................",
    ],
    [
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "....kkkkkkkk....",
        "..kkVVVVVVVVkk..",
        ".kvvkvvvvvvkvvk.",
        "kvvvvvvvvvvvvvvk",
        "kvvvvvvvvvvvvvvk",
        "kuvvvvvvvvvvvvuk",
        ".kuuuuuuuuuuuuk.",
        "..kkkkkkkkkkkk..",
        "................",
    ],
]

DUENDE_QUADROS = [
    [
        ".......kk.......",
        "......kcck......",
        ".....kcccck.....",
        "....kcccccck....",
        "..kkoooyyookk...",
        ".koooyyyyyoook..",
        ".koookkbbkkoook.",
        "..kooooooooook..",
        "...kbbbkkbbk....",
        "..kbbbbbbbbk..w.",
        "..kbbbkkbbkk.klk",
        "...kookkooky..k.",
        "...koookook.....",
        "...koookook.....",
        "...kBBk.kBBk....",
        "...kBBk.kBBk....",
        "....kk...kk.....",
        "................",
    ],
    [
        ".......kk.......",
        "......kcck......",
        ".....kcccck.....",
        "....kcccccck....",
        "..kkoooyyookk...",
        ".koooyyyyyoook..",
        ".koookkbbkkoook.",
        "..kooooooooook..",
        "...kbbbkkbbk.ww.",
        "..kbbbbbbbbkklk.",
        "..kbbbkkbbkk.kk.",
        "....kookkooky...",
        "...koookook.....",
        "...kBBkk.kBBk...",
        "...kBBk...kBBk..",
        "....kk.....kk...",
        "................",
        "................",
    ],
]

ZUMBI_ARQUEIRO_QUADROS = [
    [
        "......kkkk......",
        ".....kzzzzk.....",
        "....kzzRzzRzk...",
        "....kzzkzzkzk...",
        "....kzzzzzzzk...",
        "....kZZkkZZk....",
        "...akbbkkbbka...",
        "..a.kbbbbbbk.a..",
        "..a.kbbkkbbk.a..",
        ".a..kbbkkbbk..a.",
        ".a..kbbkkbbk..a.",
        ".a...kzzkzk...a.",
        ".a...kzzkzk...a.",
        ".....kzzkzk.....",
        ".....kzzkzk.....",
        "....kBBk.kBBk...",
        "....kBBk.kBBk...",
        "....kBBk.kBBk...",
        "....kBBk.kBBk...",
        ".....kk...kk....",
        "................",
        "................",
    ],
    [
        "......kkkk......",
        ".....kzzzzk.....",
        "....kzzRzzRzk...",
        "....kzzkzzkzk.a.",
        "....kzzzzzzzka.a",
        "....kZZkkZZkallw",
        "...akbbkkbbka...",
        "..a.kbbbbbbk.a..",
        "..a.kbbkkbbk.a..",
        "....kbbkkbbk..a.",
        "....kbbkkbbk...a",
        ".....kzzkzk....a",
        ".....kzzkzk.....",
        "....kBBk.kBBk...",
        "....kBBk.kBBk...",
        "....kBBk.kBBk...",
        ".....kk...kk....",
        "................",
        "................",
        "................",
        "................",
        "................",
    ],
]

TROLL_QUADROS = [
    [
        ".......kkkkkkkkk........",
        "......ktttttttttk.......",
        ".....ktttykkkkytttk.....",
        "....kttttwwwwktttttk....",
        "....ktTttktTtkttTttk..kk",
        "...ktTTkktTTkktTTttktkpk",
        "...ktttyykkkkyyttttk.kpk",
        "...ktttttttttttttttk.kpk",
        "....kTTkkTTkkTTkkTTk.kpk",
        "...kTTTTTTTTTTTTTTTTkkpk",
        "..kTTkkTTkkTTkkTTkkTTkpk",
        ".kttttttttttttttttttktpk",
        ".kttttkkTTTTTTTTkkttktpk",
        ".kttttkttttttttkttttk.pk",
        "..ktttkttttttttktttk..pk",
        "..ktttkttkkkkttktttk..pk",
        "...kTTkkk....kkkTTk...pk",
        "...kttttk....kttttk...pk",
        "...kttttk....kttttk...pk",
        "...kTTTTk....kTTTTk...pk",
        "...kBBBBk....kBBBBk...kk",
        "...kBBBBk....kBBBBk.....",
        "....kkkk......kkkk......",
        "........................",
    ],
    [
        ".......kkkkkkkkk......kk",
        "......ktttttttttk.....kp",
        ".....ktttykkkkytttk..kpk",
        "....kttttwwwwktttttk.kpk",
        "....ktTttktTtkttTttkkpk.",
        "...ktTTkktTTkktTTttkpk..",
        "...ktttyykkkkyyttttkpk..",
        "...ktttttttttttttttkk...",
        "....kTTkkTTkkTTkkTTk....",
        "...kTTTTTTTTTTTTTTTTk...",
        "..kTTkkTTkkTTkkTTkkTTk..",
        ".kttttttttttttttttttttk.",
        ".kttttkkTTTTTTTTkkttttk.",
        ".kttttkttttttttkttttk...",
        "..ktttkttttttttktttk....",
        "..ktttkttkkkkttktttk....",
        "...kTTkkk....kkkTTk.....",
        "...kttttk....kttttk.....",
        "...kttttk....kttttk.....",
        "...kTTTTk....kTTTTk.....",
        "...kBBBBk....kBBBBk.....",
        "...kBBBBk....kBBBBk.....",
        "....kkkk......kkkk......",
        "........................",
    ],
]

ITEM_CORACAO = [
    "...kk....kk...",
    "..krrk..krrk..",
    ".krrrrkkrrrrk.",
    ".krrrrrrrrrrk.",
    "krrrrrrrrrrrrk",
    "krrrrrrrrrrrrk",
    "krrrrwrrrrrrrk",
    ".krrrrwrrrrrk.",
    "..krrrrrrrrk..",
    "...krrrrrrk...",
    "....krrrrk....",
    ".....kkkk.....",
]

FLECHA = [
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "....kwl.........",
    "kaaaaaaalllllkw.",
    "kaaaaaaalllllkw.",
    "....kwl.........",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
]

CORACAO = [
    ".kk.kk..",
    "krrkrrk.",
    "krrrrrk.",
    "krrrrrk.",
    ".krrrk..",
    "..krk...",
    "...k....",
    "........",
]


def desenhar_grade(linhas, trocas=None):
    """Transforma uma grade de texto em uma Surface. `trocas` muda cores da paleta."""
    paleta = {**PALETA, **(trocas or {})}
    largura = len(linhas[0])
    surf = pygame.Surface((largura, len(linhas)), pygame.SRCALPHA)
    for y, linha in enumerate(linhas):
        if len(linha) != largura:
            raise ValueError(f"linha {y} tem {len(linha)} pixels (esperado {largura}): {linha!r}")
        for x, c in enumerate(linha):
            cor = paleta[c]
            if cor:
                surf.set_at((x, y), cor)
    return surf


def carregar(nome, gerar, tamanho=None):
    """Gera o sprite procedural atualizado, salva em assets/sprites/<nome>.png e devolve a Surface."""
    _ = tamanho
    caminho = PASTA_SPRITES / f"{nome}.png"
    surf = gerar()
    PASTA_SPRITES.mkdir(parents=True, exist_ok=True)
    pygame.image.save(surf, caminho)
    return surf.convert_alpha()


def silhueta_branca(surf):
    """Versão toda branca do sprite (para o efeito de 'levou dano')."""
    return pygame.mask.from_surface(surf).to_surface(
        setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0)
    )


# ---------------------------------------------------------------- folhas
def _fatiar_personagem(folha):
    """Corta a folha em {direcao: [quadros]}; esquerda é a direita espelhada."""
    quadros = {}
    for linha, direcao in enumerate(("baixo", "cima", "direita")):
        quadros[direcao] = [
            folha.subsurface((c * QUADRO, linha * QUADRO, QUADRO, QUADRO))
            for c in range(QUADROS_POR_LINHA)
        ]
    quadros["esquerda"] = [pygame.transform.flip(q, True, False) for q in quadros["direita"]]
    return quadros


def _sombra():
    s = pygame.Surface((14, 5), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (0, 0, 0, 70), s.get_rect())
    return s


PLACA = [
    "................",
    "................",
    "..kkkkkkkkkkkk..",
    "..khhhhhhhhhhk..",
    "..khbbbhbbbbhk..",
    "..khhhhhhhhhhk..",
    "..khbbbbbhbbhk..",
    "..khhhhhhhhhhk..",
    "..kkkkkkkkkkkk..",
    "......kbbk......",
    "......kbbk......",
    "......kbbk......",
    "......kbbk......",
    ".....kkbbkk.....",
    "................",
    "................",
]


def _folha_slime():
    folha = pygame.Surface((TILE * 2, TILE), pygame.SRCALPHA)
    for i, quadro in enumerate(SLIME_QUADROS):
        folha.blit(desenhar_grade(quadro), (i * TILE, 0))
    return folha


def _folha_slime_verde():
    folha = pygame.Surface((TILE * 2, TILE), pygame.SRCALPHA)
    for i, quadro in enumerate(SLIME_VERDE_QUADROS):
        folha.blit(desenhar_grade(quadro), (i * TILE, 0))
    return folha


def _folha_duende():
    folha = pygame.Surface((16 * 2, 18), pygame.SRCALPHA)
    for i, quadro in enumerate(DUENDE_QUADROS):
        folha.blit(desenhar_grade(quadro), (i * 16, 0))
    return folha


def _folha_zumbi_arqueiro():
    folha = pygame.Surface((16 * 2, 22), pygame.SRCALPHA)
    for i, quadro in enumerate(ZUMBI_ARQUEIRO_QUADROS):
        folha.blit(desenhar_grade(quadro), (i * 16, 0))
    return folha


def _folha_troll():
    folha = pygame.Surface((24 * 2, 24), pygame.SRCALPHA)
    for i, quadro in enumerate(TROLL_QUADROS):
        folha.blit(desenhar_grade(quadro), (i * 24, 0))
    return folha


def _folha_coracoes():
    """Três corações 8x8: cheio, metade, vazio."""
    cheio = CORACAO
    metade = [linha[:4] + linha[4:].replace("r", "e") for linha in CORACAO]
    vazio = [linha.replace("r", "e") for linha in CORACAO]
    folha = pygame.Surface((24, 8), pygame.SRCALPHA)
    for i, grade in enumerate((cheio, metade, vazio)):
        folha.blit(desenhar_grade(grade), (i * 8, 0))
    return folha


# ---------------------------------------------------------------- tiles (estilo Legend of Mana / Zelda ALttP)
VERDE = (76, 152, 64)
VERDE_MUSGO = (64, 134, 58)
VERDE_SOMBRA = (44, 104, 52)
VERDE_CLARO = (116, 186, 82)
VERDE_SOL = (162, 214, 102)


def _grama(semente, vento=0):
    rng = random.Random(semente)
    s = pygame.Surface((TILE, TILE))
    s.fill(VERDE)
    # Manchas pictóricas sutis de musgo e luz no solo (estilo Legend of Mana)
    for _ in range(4):
        mx, my = rng.randrange(0, TILE - 3), rng.randrange(0, TILE - 2)
        pygame.draw.rect(s, VERDE_MUSGO, (mx, my, 3, 2))
    # Tufos de grama em 3 tons que inclinam com o vento
    for _ in range(6):
        x, y = rng.randrange(2, TILE - 3), rng.randrange(3, TILE - 1)
        s.set_at((x, y), VERDE_SOMBRA)
        s.set_at((x, y - 1), VERDE_MUSGO)
        s.set_at((x + vento, y - 2), VERDE_CLARO)
        if rng.random() < 0.55:
            s.set_at((x + 1 + vento, y - 1), VERDE_SOL)
    # Pequenos trevos e pontinhos de luz dourada
    for _ in range(3):
        tx, ty = rng.randrange(1, TILE - 2), rng.randrange(1, TILE - 2)
        s.set_at((tx, ty), VERDE_SOL if rng.random() < 0.6 else (54, 118, 52))
    return s


def _flores(vento=0):
    rng = random.Random(42)
    s = _grama(99, max(0, vento))
    paletas_flor = [
        ((255, 250, 240), (220, 195, 180), (255, 210, 65)),  # margarida alva
        ((255, 145, 190), (205, 85, 135), (255, 225, 90)),   # rosa silvestre
        ((165, 185, 255), (105, 125, 215), (255, 235, 120)), # flor azul de mana
    ]
    for i in range(3):
        x, y = rng.randrange(3, TILE - 3), rng.randrange(3, TILE - 3)
        petala, sombra_p, miolo = paletas_flor[i % len(paletas_flor)]
        cx = max(2, min(TILE - 3, x + vento))
        # Caule e folhinhas na base
        s.set_at((x, min(TILE - 1, y + 2)), (38, 94, 46))
        s.set_at((max(0, x - 1), min(TILE - 1, y + 2)), (58, 132, 56))
        # Pétalas sombreadas e iluminadas
        s.set_at((cx - 1, y), petala)
        s.set_at((cx + 1, y), sombra_p)
        s.set_at((cx, y - 1), petala)
        s.set_at((cx, y + 1), sombra_p)
        s.set_at((cx, y), miolo)
    return s


def _caminho():
    rng = random.Random(5)
    s = pygame.Surface((TILE, TILE))
    s.fill((198, 164, 114))
    # Textura de terra batida e pedrinhas de calçamento (estilo Zelda ALttP)
    for _ in range(18):
        cor = rng.choice([(176, 142, 94), (186, 152, 102), (214, 182, 132)])
        s.set_at((rng.randrange(TILE), rng.randrange(TILE)), cor)
    pedras = [(2, 3, 4, 3), (9, 2, 5, 3), (4, 9, 5, 4), (11, 10, 3, 3), (1, 12, 3, 2)]
    for px, py, pl, pa in pedras:
        pygame.draw.rect(s, (164, 130, 84), (px, py, pl, pa))
        pygame.draw.line(s, (226, 198, 150), (px, py), (px + pl - 2, py))
        s.set_at((px, py + 1), (226, 198, 150))
    return s


def _agua(fase=0):
    rng = random.Random(8)
    s = pygame.Surface((TILE, TILE))
    s.fill((46, 108, 188))
    # Camadas cristalinas de profundidade (safira -> turquesa)
    for y in range(0, TILE, 2):
        tom = (38, 94, 172) if (y // 2 + fase) % 3 == 0 else ((56, 124, 204) if (y // 2 + fase) % 2 == 0 else (46, 108, 188))
        pygame.draw.line(s, tom, (0, y), (TILE - 1, y))
    # Reflexos caústicos e marolas cintilantes
    for i in range(5):
        x_base, y_base = rng.randrange(0, TILE - 4), rng.randrange(1, TILE - 1)
        x = (x_base + fase * 3 + i * 2) % (TILE - 4)
        y = (y_base + (1 if (fase + i) % 2 else 0)) % (TILE - 1)
        pygame.draw.line(s, (110, 188, 242), (x, y), (x + 3, y))
        if (fase + i) % 2 == 0:
            s.set_at((x + 1, y), (225, 250, 255))
    return s


def _pedra():
    s = pygame.Surface((TILE, TILE))
    # Bloco de ruína esculpido com musgo e chanfro 3D (Zelda ALttP)
    s.fill((112, 116, 132))
    pygame.draw.rect(s, (46, 48, 62), s.get_rect(), 1)
    # Topo iluminado e base sombreada
    pygame.draw.rect(s, (148, 154, 170), (1, 1, 14, 4))
    pygame.draw.line(s, (182, 188, 202), (2, 1), (13, 1))
    pygame.draw.rect(s, (82, 86, 102), (1, 11, 14, 4))
    pygame.draw.line(s, (62, 64, 78), (1, 14), (14, 14))
    # Divisões de blocos de cantaria e rachaduras
    pygame.draw.line(s, (68, 72, 88), (1, 7), (14, 7))
    pygame.draw.line(s, (142, 148, 164), (2, 8), (13, 8))
    pygame.draw.line(s, (68, 72, 88), (7, 1), (7, 7))
    pygame.draw.line(s, (68, 72, 88), (11, 7), (11, 14))
    # Toques de musgo antigo nas frestas
    for mx, my in ((2, 6), (3, 7), (12, 13), (13, 13), (6, 2)):
        s.set_at((mx, my), (72, 142, 68))
    return s


def _arvore(vento=0):
    s = _grama(7, max(0, vento))
    # Sombra da copa no chão e raízes do tronco (Legend of Mana)
    pygame.draw.ellipse(s, (32, 76, 42), (2, 11, 12, 5))
    pygame.draw.rect(s, (78, 46, 28), (5, 10, 6, 5))
    pygame.draw.line(s, (118, 74, 44), (6, 10), (6, 14))
    pygame.draw.line(s, (138, 90, 54), (7, 11), (7, 13))
    s.set_at((4, 14), (78, 46, 28))
    s.set_at((11, 14), (58, 34, 20))
    # Copa volumosa em 4 camadas de cor (sombra fria -> esmeralda -> topo dourado)
    pygame.draw.circle(s, (26, 68, 44), (8 + vento, 7), 7)
    pygame.draw.circle(s, (42, 108, 52), (8 + vento, 6), 6)
    pygame.draw.circle(s, (72, 152, 64), (7 + vento, 5), 5)
    pygame.draw.circle(s, (118, 192, 78), (6 + vento, 4), 3)
    for lx, ly in ((5, 2), (7, 2), (4, 4), (9, 3)):
        s.set_at((max(0, min(15, lx + vento)), ly), (168, 224, 104))
    # Pequenos frutos rubros na copa
    for fx, fy in ((10, 6), (5, 8)):
        s.set_at((max(0, min(15, fx + vento)), fy), (230, 75, 70))
    return s


def _arbusto(vento=0):
    s = _grama(13, max(0, vento))
    pygame.draw.ellipse(s, (30, 74, 40), (2, 11, 12, 4))
    pygame.draw.circle(s, (30, 86, 44), (8 + vento, 9), 6)
    pygame.draw.circle(s, (56, 136, 56), (8 + vento, 8), 5)
    pygame.draw.circle(s, (92, 174, 72), (7 + vento, 7), 3)
    for px, py in ((5, 6), (9, 5), (6, 8), (10, 8)):
        s.set_at((max(0, min(15, px + vento)), py), (148, 212, 94))
    # Frutinhas silvestres no arbusto
    s.set_at((max(0, min(15, 6 + vento)), 10), (235, 85, 95))
    s.set_at((max(0, min(15, 10 + vento)), 9), (235, 85, 95))
    return s


def _piso():
    s = pygame.Surface((TILE, TILE))
    s.fill((158, 106, 62))
    for y in (0, 4, 8, 12):
        pygame.draw.line(s, (182, 126, 78), (0, y), (TILE - 1, y))
        pygame.draw.line(s, (112, 70, 38), (0, y + 3), (TILE - 1, y + 3))
    for x, y in ((4, 0), (11, 4), (6, 8), (13, 12)):
        pygame.draw.line(s, (98, 60, 32), (x, y), (x, y + 3))
        s.set_at((max(0, x - 1), y + 1), (90, 54, 28))
    return s


def _parede():
    s = pygame.Surface((TILE, TILE))
    # Parede enxaimel 16-bits (reboco claro aquecido com vigas de carvalho e base de pedra)
    s.fill((224, 206, 176))
    # Textura sutil do reboco
    for px, py in ((3, 5), (10, 6), (5, 9), (12, 8)):
        s.set_at((px, py), (208, 188, 156))
    # Vigas horizontais e verticais de carvalho escuro
    pygame.draw.rect(s, (86, 52, 30), (0, 0, TILE, 2))
    pygame.draw.line(s, (124, 78, 44), (0, 2), (TILE - 1, 2))
    pygame.draw.line(s, (92, 56, 32), (0, 11), (TILE - 1, 11))
    pygame.draw.rect(s, (86, 52, 30), (0, 0, 2, 12))
    pygame.draw.rect(s, (86, 52, 30), (TILE - 2, 0, 2, 12))
    pygame.draw.line(s, (124, 78, 44), (1, 2), (1, 11))
    # Rodapé de blocos de pedra esculpida
    pygame.draw.rect(s, (108, 110, 124), (0, 12, TILE, 4))
    pygame.draw.line(s, (144, 148, 162), (1, 12), (14, 12))
    pygame.draw.line(s, (68, 70, 82), (7, 12), (7, 15))
    pygame.draw.line(s, (48, 46, 58), (0, 15), (15, 15))
    return s


def _telhado():
    s = pygame.Surface((TILE, TILE))
    s.fill((172, 58, 48))
    for y in range(0, TILE, 4):
        pygame.draw.line(s, (208, 86, 68), (0, y), (TILE - 1, y))
        pygame.draw.line(s, (116, 34, 30), (0, y + 3), (TILE - 1, y + 3))
        desloc = (y // 4 % 2) * 4
        for x in range(desloc, TILE, 4):
            pygame.draw.line(s, (138, 44, 36), (x, y), (x, y + 3))
            if x + 1 < TILE:
                s.set_at((x + 1, y + 1), (224, 108, 84))
    return s


def _cama():
    s = _piso()
    pygame.draw.rect(s, (58, 34, 20), (1, 0, 14, 16))
    pygame.draw.rect(s, (118, 74, 42), (2, 1, 12, 3))
    pygame.draw.line(s, (158, 104, 62), (3, 1), (12, 1))
    pygame.draw.rect(s, (246, 242, 230), (3, 4, 10, 4))
    pygame.draw.line(s, (214, 206, 192), (3, 7), (12, 7))
    pygame.draw.rect(s, (232, 92, 86), (2, 7, 12, 2))
    pygame.draw.rect(s, (186, 46, 52), (2, 9, 12, 6))
    pygame.draw.line(s, (240, 188, 78), (3, 11), (12, 11))
    return s


def _mesa():
    s = _piso()
    pygame.draw.rect(s, (42, 26, 16), (2, 12, 12, 3))
    pygame.draw.rect(s, (76, 46, 24), (1, 3, 14, 10))
    pygame.draw.rect(s, (148, 96, 54), (2, 4, 12, 7))
    pygame.draw.line(s, (184, 128, 78), (3, 4), (12, 4))
    # Toalha bordada no centro da mesa
    pygame.draw.rect(s, (218, 206, 178), (5, 4, 6, 7))
    pygame.draw.line(s, (190, 62, 58), (6, 4), (6, 10))
    pygame.draw.line(s, (190, 62, 58), (9, 4), (9, 10))
    pygame.draw.rect(s, (68, 40, 20), (2, 12, 2, 3))
    pygame.draw.rect(s, (68, 40, 20), (12, 12, 2, 3))
    return s


def _porta():
    s = _piso()
    pygame.draw.rect(s, (92, 40, 34), (1, 3, 14, 11))
    pygame.draw.rect(s, (164, 68, 54), (2, 4, 12, 9))
    pygame.draw.rect(s, (226, 182, 76), (3, 5, 10, 7), 1)
    pygame.draw.rect(s, (196, 104, 72), (5, 7, 6, 3))
    return s


def _heroi_dormindo(cama, heroi_frente):
    """Monta o herói deitado na cama com os olhos fechados e cobertor por cima."""
    surf = cama.copy()
    cabeca = heroi_frente.subsurface((8, 4, 16, 13)).copy()
    cor_pele = (252, 214, 176)
    cor_olho_fechado = (104, 56, 30)
    for y in (8, 9):
        for x in range(3, 13):
            if cabeca.get_at((x, y))[:3] in ((40, 32, 56), (255, 255, 255)):
                cabeca.set_at((x, y), cor_olho_fechado if y == 9 else cor_pele)
    surf.blit(cabeca, (0, 0))
    pygame.draw.rect(surf, (226, 86, 86), (2, 10, 12, 2))
    pygame.draw.rect(surf, (190, 48, 52), (2, 12, 12, 3))
    return surf


class Graficos:
    """Carrega tudo uma vez só. Precisa ser criado depois do set_mode()."""

    def __init__(self):
        tamanho = (QUADRO * QUADROS_POR_LINHA, QUADRO * 3)
        self.npcs = {
            nome: _fatiar_personagem(carregar(nome, lambda n=nome: folha_personagem(n), tamanho))
            for nome in PERSONAGENS
        }
        self.jogador = self.npcs["heroi"]
        self.sombra = _sombra()
        placa = carregar("npc_placa", lambda: desenhar_grade(PLACA))
        self.npcs["placa"] = {d: [placa] for d in ("baixo", "cima", "direita", "esquerda")}

        espada = carregar("espada", lambda: desenhar_grade(ESPADA))
        self.espada = {
            "cima": espada,
            "baixo": pygame.transform.rotate(espada, 180),
            "direita": pygame.transform.rotate(espada, -90),
            "esquerda": pygame.transform.rotate(espada, 90),
        }

        folha = carregar("slime", _folha_slime)
        self.slime = [folha.subsurface((i * TILE, 0, TILE, TILE)) for i in range(2)]
        self.slime_branco = [silhueta_branca(q) for q in self.slime]

        folha_sv = carregar("slime_verde", _folha_slime_verde)
        self.slime_verde = [folha_sv.subsurface((i * TILE, 0, TILE, TILE)) for i in range(2)]
        self.slime_verde_branco = [silhueta_branca(q) for q in self.slime_verde]

        folha_d = carregar("duende", _folha_duende)
        self.duende = [folha_d.subsurface((i * 16, 0, 16, 18)) for i in range(2)]
        self.duende_branco = [silhueta_branca(q) for q in self.duende]

        folha_za = carregar("zumbi_arqueiro", _folha_zumbi_arqueiro)
        self.zumbi_arqueiro = [folha_za.subsurface((i * 16, 0, 16, 22)) for i in range(2)]
        self.zumbi_arqueiro_branco = [silhueta_branca(q) for q in self.zumbi_arqueiro]

        folha_tr = carregar("troll", _folha_troll)
        self.troll = [folha_tr.subsurface((i * 24, 0, 24, 24)) for i in range(2)]
        self.troll_branco = [silhueta_branca(q) for q in self.troll]

        self.item_coracao = carregar("item_coracao", lambda: desenhar_grade(ITEM_CORACAO))

        flecha_s = carregar("flecha", lambda: desenhar_grade(FLECHA))
        self.flecha = {
            "direita": flecha_s,
            "esquerda": pygame.transform.rotate(flecha_s, 180),
            "cima": pygame.transform.rotate(flecha_s, 90),
            "baixo": pygame.transform.rotate(flecha_s, -90),
        }

        folha = carregar("coracoes", _folha_coracoes)
        self.coracao_cheio, self.coracao_metade, self.coracao_vazio = (
            folha.subsurface((i * 8, 0, 8, 8)) for i in range(3)
        )

        self.gramas = [carregar(f"grama_{i}", lambda i=i: _grama(i)) for i in range(4)]
        self.gramas_vento = [_grama(i, 1).convert() for i in range(4)]
        self.tiles = {
            "flores": carregar("flores", _flores),
            "caminho": carregar("caminho", _caminho),
            "agua": carregar("agua", _agua),
            "pedra": carregar("pedra", _pedra),
            "arvore": carregar("arvore", _arvore),
            "arbusto": carregar("arbusto", _arbusto),
            "piso": carregar("piso", _piso),
            "parede": carregar("parede", _parede),
            "telhado": carregar("telhado", _telhado),
            "cama": carregar("cama", _cama),
            "mesa": carregar("mesa", _mesa),
            "porta": carregar("porta", _porta),
        }
        self.tiles_animados = {
            "~": [_agua(q).convert() for q in range(4)],
            "*": [_flores(v).convert() for v in (-1, 0, 1)],
            "T": [_arvore(v).convert() for v in (-1, 0, 1)],
            "B": [_arbusto(v).convert() for v in (-1, 0, 1)],
        }
        self.heroi_dormindo = _heroi_dormindo(self.tiles["cama"], self.jogador["baixo"][0])
