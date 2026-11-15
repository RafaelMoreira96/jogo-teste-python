"""Mapa-múndi ilustrado do Reino Esquecido (pergaminho pintado em pixel art).

O desenho é gerado uma vez a partir das posições das regiões no Atlas:
continente com litoral irregular, mar com ondas, biomas pintados por
região, estradas tracejadas, ícones dos lugares, rosa dos ventos e cartela.
A névoa das regiões não visitadas e os marcadores são desenhados por cima
na tela do Atlas (cenas/mapa_mundo.py).
"""
import math
import random

import pygame

# Bioma de cada região do mundo
BIOMA_POR_MAPA = {
    "templo_sol.txt": "deserto", "oasis.txt": "deserto", "deserto.txt": "deserto",
    "caverna_cristal.txt": "cristal", "lago.txt": "lago", "bosque_outono.txt": "outono",
    "pico_congelado.txt": "neve", "montanha.txt": "montanha",
    "vila.txt": "campo", "mundo.txt": "floresta", "casa.txt": "campo",
    "pantano.txt": "pantano", "santuario.txt": "sombrio", "ruinas.txt": "ruinas", "cripta.txt": "ruinas",
}
CORES_BIOMA = {
    "deserto": (222, 194, 124), "cristal": (170, 150, 196), "lago": (150, 190, 160),
    "outono": (206, 150, 84), "neve": (232, 236, 240), "montanha": (170, 160, 130),
    "campo": (164, 196, 110), "floresta": (120, 170, 96), "pantano": (110, 140, 104),
    "sombrio": (150, 120, 150), "ruinas": (176, 164, 132), "castelo": (120, 100, 120),
}
NOMES_CURTOS = {
    "vila.txt": "Aurora", "lago.txt": "Lago", "deserto.txt": "Deserto", "templo_sol.txt": "Templo",
    "pico_congelado.txt": "Pico", "pantano.txt": "Pântano", "castelo.txt": "Castelo",
    "ruinas.txt": "Ruínas", "bosque_outono.txt": "Bosque",
}
TINTA = (70, 46, 30)
PAPEL = (232, 214, 170)


def _bioma(arq):
    if arq.startswith("castelo"):
        return "castelo"
    return BIOMA_POR_MAPA.get(arq, "campo")


def _ruido(rng_tab, x, y):
    """Ruído de valor suave a partir de uma tabela de números aleatórios."""
    x0, y0 = int(math.floor(x)), int(math.floor(y))
    fx, fy = x - x0, y - y0
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)

    def h(i, j):
        return rng_tab[(i * 73 + j * 151) % len(rng_tab)]

    a = h(x0, y0) + (h(x0 + 1, y0) - h(x0, y0)) * fx
    b = h(x0, y0 + 1) + (h(x0 + 1, y0 + 1) - h(x0, y0 + 1)) * fx
    return a + (b - a) * fy


def _misturar(a, b, f):
    return tuple(round(a[i] + (b[i] - a[i]) * f) for i in range(3))


# ------------------------------------------------------------------ ícones
def _icone_arvore(s, x, y, cor=(60, 120, 60)):
    pygame.draw.line(s, TINTA, (x, y), (x, y + 2))
    pygame.draw.circle(s, cor, (x, y - 1), 2)
    s.set_at((x - 1, y - 2), _misturar(cor, (255, 255, 200), 0.4))


def _icone_pinheiro(s, x, y, cor=(50, 100, 70)):
    pygame.draw.polygon(s, cor, [(x - 2, y + 1), (x + 2, y + 1), (x, y - 4)])
    s.set_at((x, y + 2), TINTA)


def _icone_montanha(s, x, y, neve=False, cor=(150, 136, 110)):
    pts = [(x - 5, y + 3), (x, y - 4), (x + 5, y + 3)]
    pygame.draw.polygon(s, cor, pts)
    pygame.draw.polygon(s, _misturar(cor, (40, 30, 20), 0.35), [(x, y - 4), (x + 5, y + 3), (x + 1, y + 3)])
    if neve:
        pygame.draw.polygon(s, (250, 250, 255), [(x - 2, y - 1), (x, y - 4), (x + 2, y - 1)])
    pygame.draw.lines(s, TINTA, False, pts)


def _icone_duna(s, x, y):
    pygame.draw.arc(s, (176, 140, 80), (x - 4, y - 1, 8, 4), 0, math.pi)


def _icone_junco(s, x, y):
    for dx in (-1, 1):
        pygame.draw.line(s, (60, 90, 60), (x + dx, y + 1), (x + dx * 2, y - 2))


def _icone_casa(s, x, y, telhado=(196, 70, 54)):
    pygame.draw.rect(s, (240, 226, 196), (x - 3, y - 1, 6, 4))
    pygame.draw.polygon(s, telhado, [(x - 4, y - 1), (x + 4, y - 1), (x, y - 5)])
    pygame.draw.rect(s, TINTA, (x - 3, y - 1, 6, 4), 1)
    s.set_at((x, y + 1), TINTA)


def _icone_local(s, arq, x, y):
    """Ícone ilustrado de cada lugar notável."""
    if arq == "vila.txt":
        _icone_casa(s, x - 4, y + 1)
        _icone_casa(s, x + 4, y + 1, (70, 110, 200))
        _icone_casa(s, x, y - 3, (200, 150, 60))
    elif arq == "casa.txt":
        _icone_casa(s, x, y)
    elif arq == "castelo.txt":
        for dx, alt in ((-6, 7), (0, 11), (6, 7)):
            pygame.draw.rect(s, (110, 96, 120), (x + dx - 2, y - alt + 3, 5, alt))
            pygame.draw.polygon(s, (170, 50, 70), [(x + dx - 3, y - alt + 3), (x + dx + 3, y - alt + 3), (x + dx, y - alt - 1)])
        pygame.draw.rect(s, (90, 78, 100), (x - 7, y, 15, 4))
        pygame.draw.rect(s, TINTA, (x - 7, y, 15, 4), 1)
    elif arq == "templo_sol.txt":
        pygame.draw.polygon(s, (230, 190, 90), [(x - 6, y + 3), (x + 6, y + 3), (x, y - 5)])
        pygame.draw.polygon(s, TINTA, [(x - 6, y + 3), (x + 6, y + 3), (x, y - 5)], 1)
        pygame.draw.circle(s, (255, 120, 40), (x, y - 7), 2)
    elif arq == "oasis.txt":
        pygame.draw.ellipse(s, (90, 160, 210), (x - 4, y, 8, 4))
        pygame.draw.line(s, (120, 80, 40), (x + 3, y + 1), (x + 4, y - 4))
        for a in (-1, 0, 1):
            pygame.draw.line(s, (60, 140, 60), (x + 4, y - 4), (x + 4 + a * 3, y - 6 + abs(a)))
    elif arq in ("caverna_cristal.txt", "cripta.txt"):
        pygame.draw.ellipse(s, (60, 50, 60), (x - 4, y - 3, 8, 7))
        pygame.draw.ellipse(s, TINTA, (x - 4, y - 3, 8, 7), 1)
        if arq == "caverna_cristal.txt":
            pygame.draw.polygon(s, (140, 230, 255), [(x + 4, y - 1), (x + 6, y - 6), (x + 8, y - 1)])
        else:
            pygame.draw.line(s, (230, 230, 230), (x + 5, y - 5), (x + 5, y + 1))
            pygame.draw.line(s, (230, 230, 230), (x + 3, y - 3), (x + 7, y - 3))
    elif arq == "ruinas.txt":
        for dx, alt in ((-4, 6), (0, 4), (4, 7)):
            pygame.draw.rect(s, (200, 190, 170), (x + dx - 1, y + 2 - alt, 3, alt))
            pygame.draw.rect(s, TINTA, (x + dx - 1, y + 2 - alt, 3, alt), 1)
    elif arq == "santuario.txt":
        pygame.draw.rect(s, (120, 90, 140), (x - 2, y - 7, 5, 10))
        pygame.draw.polygon(s, (190, 80, 220), [(x - 3, y - 7), (x + 3, y - 7), (x, y - 11)])
        pygame.draw.rect(s, TINTA, (x - 2, y - 7, 5, 10), 1)
    elif arq == "pico_congelado.txt":
        _icone_montanha(s, x, y - 1, neve=True, cor=(200, 210, 226))
    elif arq == "montanha.txt":
        _icone_montanha(s, x - 3, y, neve=False)
        _icone_montanha(s, x + 3, y + 1, neve=True)
    elif arq == "lago.txt":
        pass  # o próprio lago já é desenhado no terreno
    elif arq == "pantano.txt":
        _icone_junco(s, x - 3, y)
        _icone_junco(s, x + 3, y + 1)
    elif arq == "bosque_outono.txt":
        _icone_arvore(s, x - 3, y, (220, 120, 50))
        _icone_arvore(s, x + 3, y + 1, (200, 80, 40))
    elif arq == "mundo.txt":
        _icone_arvore(s, x - 3, y)
        _icone_pinheiro(s, x + 3, y + 1)


# ------------------------------------------------------------------ geração
_cache = {}


def gerar_mapa_mundi(tamanho, nos):
    """Pergaminho do mapa (Surface) com `nos` = [{"arq", "pos", "conexoes"}] em coordenadas locais."""
    chave = (tamanho, tuple((n["arq"], n["pos"]) for n in nos))
    if chave in _cache:
        return _cache[chave]
    larg, alt = tamanho
    rng = random.Random(1987)
    tab = [rng.random() for _ in range(997)]
    s = pygame.Surface((larg, alt))

    # Continente: envoltória suave das regiões, com litoral recortado por ruído
    pos = [(n["pos"], _bioma(n["arq"]), n["arq"]) for n in nos if not n["arq"].startswith("castelo_")]
    pos_castelo = [n["pos"] for n in nos if n["arq"].startswith("castelo")]
    if pos_castelo:
        cx = sum(p[0] for p in pos_castelo) / len(pos_castelo)
        cy = sum(p[1] for p in pos_castelo) / len(pos_castelo)
        pos.append(((round(cx), round(cy)), "castelo", "castelo.txt"))

    grade_terra = [[False] * larg for _ in range(alt)]
    for y in range(alt):
        for x in range(larg):
            perto = min((x - p[0]) ** 2 + (y - p[1]) ** 2 for p, _, _ in pos) ** 0.5
            grade_terra[y][x] = perto < 20 + _ruido(tab, x / 9, y / 9) * 14

    def terra(x, y):
        return 0 <= x < larg and 0 <= y < alt and grade_terra[y][x]

    lago = next((p for p, b, _ in pos if b == "lago"), None)
    for y in range(alt):
        for x in range(larg):
            if terra(x, y):
                # Bioma da região mais próxima (com fronteiras irregulares)
                jx = x + (_ruido(tab, x / 6 + 40, y / 6) - 0.5) * 14
                jy = y + (_ruido(tab, x / 6, y / 6 + 40) - 0.5) * 14
                _, bioma, _ = min(pos, key=lambda p: (jx - p[0][0]) ** 2 + (jy - p[0][1]) ** 2)
                cor = CORES_BIOMA[bioma]
                luz = _ruido(tab, x / 4 + 9, y / 4 + 9)
                cor = _misturar(cor, (255, 250, 220) if luz > 0.5 else (60, 40, 30), abs(luz - 0.5) * 0.35)
                if lago and math.hypot((x - lago[0]) * 0.8, y - lago[1]) < 7 + _ruido(tab, x / 3, y / 3) * 3:
                    cor = (110, 170, 214)
            else:
                prof = _ruido(tab, x / 10 + 70, y / 10)
                cor = _misturar((150, 186, 196), (110, 150, 176), prof)
            # Envelhece o papel
            papel = _ruido(tab, x / 3 + 100, y / 3 + 100)
            s.set_at((x, y), _misturar(cor, PAPEL, 0.18 + papel * 0.12))

    # Contorno do litoral em tinta
    terra_mask = pygame.Mask((larg, alt))
    for y in range(alt):
        for x in range(larg):
            if terra(x, y):
                terra_mask.set_at((x, y))
    for componente in terra_mask.connected_components():
        for x, y in componente.outline():
            s.set_at((x, y), TINTA)

    # Ondas no mar
    for _ in range(36):
        x, y = rng.randrange(4, larg - 8), rng.randrange(4, alt - 4)
        if not terra(x, y) and not terra(x + 4, y):
            pygame.draw.arc(s, (210, 230, 236), (x, y, 4, 3), 0, math.pi)
            pygame.draw.arc(s, (210, 230, 236), (x + 3, y, 4, 3), 0, math.pi)

    # Decoração dos biomas
    for _ in range(420):
        x, y = rng.randrange(3, larg - 3), rng.randrange(5, alt - 3)
        if not terra(x, y):
            continue
        _, bioma, _ = min(pos, key=lambda p: (x - p[0][0]) ** 2 + (y - p[0][1]) ** 2)
        perto = min(math.hypot(x - p[0], y - p[1]) for p, _, _ in pos)
        if perto < 7:
            continue  # deixa espaço para o ícone do lugar
        r = rng.random()
        if bioma == "floresta" and r < 0.55:
            (_icone_pinheiro if r < 0.25 else _icone_arvore)(s, x, y)
        elif bioma == "campo" and r < 0.15:
            _icone_arvore(s, x, y, (90, 150, 70))
        elif bioma == "outono" and r < 0.45:
            _icone_arvore(s, x, y, rng.choice([(220, 120, 50), (200, 80, 40), (230, 170, 60)]))
        elif bioma == "deserto" and r < 0.22:
            _icone_duna(s, x, y)
        elif bioma in ("montanha", "neve") and r < 0.3:
            _icone_montanha(s, x, y, neve=bioma == "neve" or r < 0.1, cor=(200, 210, 226) if bioma == "neve" else (150, 136, 110))
        elif bioma == "pantano" and r < 0.35:
            _icone_junco(s, x, y)
        elif bioma == "cristal" and r < 0.2:
            pygame.draw.polygon(s, (170, 220, 255), [(x, y - 3), (x + 2, y + 1), (x - 2, y + 1)])
        elif bioma in ("sombrio", "castelo") and r < 0.18:
            _icone_pinheiro(s, x, y, (70, 50, 80))
        elif bioma == "ruinas" and r < 0.1:
            pygame.draw.rect(s, (200, 190, 170), (x, y - 2, 2, 3))

    # Estradas tracejadas entre as regiões ligadas
    pos_arq = {n["arq"]: n["pos"] for n in nos}
    feitas = set()
    for n in nos:
        for dest in n["conexoes"]:
            par = tuple(sorted((n["arq"], dest)))
            if dest not in pos_arq or par in feitas or (n["arq"].startswith("castelo_") and dest.startswith("castelo")):
                continue
            feitas.add(par)
            (x1, y1), (x2, y2) = n["pos"], pos_arq[dest]
            dist = max(1, math.hypot(x2 - x1, y2 - y1))
            for k in range(0, int(dist), 4):
                f = k / dist
                curva = math.sin(f * math.pi) * 3
                px = x1 + (x2 - x1) * f + (y2 - y1) / dist * curva
                py = y1 + (y2 - y1) * f - (x2 - x1) / dist * curva
                pygame.draw.line(s, (130, 84, 50), (round(px), round(py)), (round(px + (x2 - x1) / dist * 2), round(py + (y2 - y1) / dist * 2)))

    # Ícones dos lugares
    for p, bioma, arq in pos:
        _icone_local(s, arq, p[0], p[1])

    # Rosa dos ventos (canto inferior direito)
    rx, ry = larg - 14, alt - 14
    pygame.draw.circle(s, (200, 180, 140), (rx, ry), 8, 1)
    for ang, comp, cor in ((-90, 9, (180, 50, 40)), (90, 7, TINTA), (0, 7, TINTA), (180, 7, TINTA)):
        a = math.radians(ang)
        ponta = (rx + math.cos(a) * comp, ry + math.sin(a) * comp)
        lado = (math.cos(a + math.pi / 2) * 2, math.sin(a + math.pi / 2) * 2)
        pygame.draw.polygon(s, cor, [ponta, (rx + lado[0], ry + lado[1]), (rx - lado[0], ry - lado[1])])
    pygame.draw.circle(s, (240, 220, 160), (rx, ry), 1)

    # Moldura de pergaminho com bordas escurecidas
    vinheta = pygame.Surface((larg, alt), pygame.SRCALPHA)
    for i in range(6):
        pygame.draw.rect(vinheta, (90, 60, 30, 70 - i * 11), (i, i, larg - i * 2, alt - i * 2), 1)
    s.blit(vinheta, (0, 0))
    pygame.draw.rect(s, TINTA, s.get_rect(), 1)
    pygame.draw.rect(s, (180, 140, 90), s.get_rect().inflate(-4, -4), 1)

    _cache[chave] = s
    return s


def desenhar_nevoa(tela, rect, pos, t):
    """Nuvem de névoa sobre uma região ainda não visitada."""
    x, y = pos
    for i, (dx, dy, r) in enumerate(((-4, 0, 5), (3, -2, 6), (6, 2, 4), (-1, 3, 4))):
        oscila = round(math.sin(t * 1.5 + i) * 1)
        pygame.draw.circle(tela, (236, 228, 210), (x + dx + oscila, y + dy), r)
        pygame.draw.circle(tela, (200, 190, 170), (x + dx + oscila, y + dy + 1), r, 1)
