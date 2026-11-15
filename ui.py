"""Peças de interface reutilizáveis: fonte pixel 16-bits proporcional, painéis, ícones e menus."""
import math
import unicodedata

import pygame

AMARELO = (255, 225, 95)
BRANCO = (246, 246, 252)
CINZA = (176, 180, 198)

# Grade 16-bits proporcional de 8 linhas de altura:
# - Linhas 0..1: acentos e topo de ascendentes
# - Linhas 1..6: maiúsculas, números e ascendentes (6px de altura)
# - Linhas 2..6: corpo das minúsculas (5px de altura -> linhas 2, 4 e 6 com aberturas nas linhas 3 e 5!)
# - Linha 7: descendentes (g, j, p, q, y, ç)
GLIFOS_16BITS = {
    " ": (
        "...",
        "...",
        "...",
        "...",
        "...",
        "...",
        "...",
        "...",
    ),
    # Maiúsculas A-Z
    "A": (".....", ".###.", "#...#", "#####", "#...#", "#...#", "#...#", "....."),
    "B": (".....", "####.", "#...#", "####.", "#...#", "#...#", "####.", "....."),
    "C": (".....", ".####", "#....", "#....", "#....", "#....", ".####", "....."),
    "D": (".....", "####.", "#...#", "#...#", "#...#", "#...#", "####.", "....."),
    "E": (".....", "#####", "#....", "####.", "#....", "#....", "#####", "....."),
    "F": (".....", "#####", "#....", "####.", "#....", "#....", "#....", "....."),
    "G": (".....", ".####", "#....", "#.###", "#...#", "#...#", ".###.", "....."),
    "H": (".....", "#...#", "#...#", "#####", "#...#", "#...#", "#...#", "....."),
    "I": ("...", "###", ".#.", ".#.", ".#.", ".#.", "###", "..."),
    "J": (".....", "..###", "...#.", "...#.", "...#.", "#..#.", ".##..", "....."),
    "K": (".....", "#...#", "#..#.", "###..", "#..#.", "#...#", "#...#", "....."),
    "L": (".....", "#....", "#....", "#....", "#....", "#....", "#####", "....."),
    "M": (".....", "#...#", "##.##", "#.#.#", "#...#", "#...#", "#...#", "....."),
    "N": (".....", "#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "....."),
    "O": (".....", ".###.", "#...#", "#...#", "#...#", "#...#", ".###.", "....."),
    "P": (".....", "####.", "#...#", "####.", "#....", "#....", "#....", "....."),
    "Q": (".....", ".###.", "#...#", "#...#", "#.#.#", "#..#.", ".##.#", "....."),
    "R": (".....", "####.", "#...#", "####.", "#..#.", "#...#", "#...#", "....."),
    "S": (".....", ".####", "#....", ".###.", "....#", "....#", "####.", "....."),
    "T": (".....", "#####", "..#..", "..#..", "..#..", "..#..", "..#..", "....."),
    "U": (".....", "#...#", "#...#", "#...#", "#...#", "#...#", ".###.", "....."),
    "V": (".....", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#..", "....."),
    "W": (".....", "#...#", "#...#", "#...#", "#.#.#", "##.##", "#...#", "....."),
    "X": (".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#", "....."),
    "Y": (".....", "#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "....."),
    "Z": (".....", "#####", "...#.", "..#..", ".#...", "#....", "#####", "....."),
    # Minúsculas a-z (5px de corpo nas linhas 2..6 para abertura total das letras!)
    "a": (".....", ".....", ".###.", "....#", ".####", "#...#", ".####", "....."),
    "b": (".....", "#....", "####.", "#...#", "#...#", "#...#", "####.", "....."),
    "c": ("....", "....", ".###", "#...", "#...", "#...", ".###", "...."),
    "d": (".....", "....#", ".####", "#...#", "#...#", "#...#", ".####", "....."),
    "e": (".....", ".....", ".###.", "#...#", "#####", "#....", ".####", "....."),
    "f": ("....", ".##.", "#...", "###.", "#...", "#...", "#...", "...."),
    "g": (".....", ".....", ".####", "#...#", ".####", "....#", ".###.", "....."),
    "h": (".....", "#....", "####.", "#...#", "#...#", "#...#", "#...#", "....."),
    "i": ("..", ".#", "..", "##", ".#", ".#", "##", ".."),
    "j": ("...", "..#", "...", ".##", "..#", "..#", "..#", "##."),
    "k": ("....", "#...", "#..#", "###.", "#.#.", "#..#", "#..#", "...."),
    "l": ("..", ".#", ".#", ".#", ".#", ".#", "##", ".."),
    "m": (".....", ".....", "##.#.", "#.#.#", "#.#.#", "#...#", "#...#", "....."),
    "n": (".....", ".....", "####.", "#...#", "#...#", "#...#", "#...#", "....."),
    "o": (".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###.", "....."),
    "p": (".....", ".....", "####.", "#...#", "#...#", "####.", "#....", "#...."),
    "q": (".....", ".....", ".####", "#...#", "#...#", ".####", "....#", "....#"),
    "r": ("....", "....", "#.##", "##..", "#...", "#...", "#...", "...."),
    "s": ("....", "....", ".###", "#...", ".##.", "...#", "###.", "...."),
    "t": ("....", ".#..", "###.", ".#..", ".#..", ".#..", "..##", "...."),
    "u": (".....", ".....", "#...#", "#...#", "#...#", "#...#", ".####", "....."),
    "v": (".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#..", "....."),
    "w": (".....", ".....", "#...#", "#...#", "#.#.#", "##.##", "#...#", "....."),
    "x": ("....", "....", "#..#", ".##.", ".##.", "#..#", "#..#", "...."),
    "y": (".....", ".....", "#...#", "#...#", ".####", "....#", ".###.", "....."),
    "z": ("....", "....", "####", "..#.", ".#..", "#...", "####", "...."),
    # Algarismos 0-9
    "0": (".....", ".###.", "#..##", "#.#.#", "##..#", "#...#", ".###.", "....."),
    "1": ("...", ".#.", "##.", ".#.", ".#.", ".#.", "###", "..."),
    "2": (".....", ".###.", "#...#", "...#.", ".##..", "#....", "#####", "....."),
    "3": (".....", "####.", "....#", ".###.", "....#", "#...#", ".###.", "....."),
    "4": (".....", "#..#.", "#..#.", "#..#.", "#####", "...#.", "...#.", "....."),
    "5": (".....", "#####", "#....", "####.", "....#", "#...#", ".###.", "....."),
    "6": (".....", ".###.", "#....", "####.", "#...#", "#...#", ".###.", "....."),
    "7": (".....", "#####", "....#", "...#.", "..#..", ".#...", ".#...", "....."),
    "8": (".....", ".###.", "#...#", ".###.", "#...#", "#...#", ".###.", "....."),
    "9": (".....", ".###.", "#...#", ".####", "....#", "#...#", ".###.", "....."),
    # Acentuadas minúsculas
    "á": ("..#..", ".#...", ".###.", "....#", ".####", "#...#", ".####", "....."),
    "à": (".#...", "..#..", ".###.", "....#", ".####", "#...#", ".####", "....."),
    "â": (".###.", "#...#", ".###.", "....#", ".####", "#...#", ".####", "....."),
    "ã": (".##.#", "#..##", ".###.", "....#", ".####", "#...#", ".####", "....."),
    "é": ("..#..", ".#...", ".###.", "#...#", "#####", "#....", ".####", "....."),
    "ê": (".###.", "#...#", ".###.", "#...#", "#####", "#....", ".####", "....."),
    "í": ("..#", ".#.", "...", ".##", "..#", "..#", ".##", "..."),
    "ó": ("..#..", ".#...", ".###.", "#...#", "#...#", "#...#", ".###.", "....."),
    "ô": (".###.", "#...#", ".###.", "#...#", "#...#", "#...#", ".###.", "....."),
    "õ": (".##.#", "#..##", ".###.", "#...#", "#...#", "#...#", ".###.", "....."),
    "ú": ("..#..", ".#...", "#...#", "#...#", "#...#", "#...#", ".####", "....."),
    "ç": ("....", "....", ".###", "#...", "#...", ".###", "..#.", ".##."),
    # Acentuadas maiúsculas
    "Á": ("..#..", ".#...", ".###.", "#...#", "#####", "#...#", "#...#", "....."),
    "À": (".#...", "..#..", ".###.", "#...#", "#####", "#...#", "#...#", "....."),
    "Â": (".###.", ".....", ".###.", "#...#", "#####", "#...#", "#...#", "....."),
    "Ã": (".##.#", ".....", ".###.", "#...#", "#####", "#...#", "#...#", "....."),
    "É": ("..#..", "#####", "#....", "####.", "#....", "#....", "#####", "....."),
    "Ê": (".###.", "#####", "#....", "####.", "#....", "#....", "#####", "....."),
    "Í": ("..#", ".#.", "###", ".#.", ".#.", ".#.", "###", "..."),
    "Ó": ("..#..", ".###.", "#...#", "#...#", "#...#", "#...#", ".###.", "....."),
    "Ô": (".###.", ".###.", "#...#", "#...#", "#...#", "#...#", ".###.", "....."),
    "Õ": (".##.#", ".###.", "#...#", "#...#", "#...#", "#...#", ".###.", "....."),
    "Ú": ("..#..", "#...#", "#...#", "#...#", "#...#", "#...#", ".###.", "....."),
    "Ç": (".....", ".####", "#....", "#....", "#....", ".####", "..#..", ".##.."),
    # Pontuação e símbolos
    ".": ("..", "..", "..", "..", "..", "..", "##", ".."),
    ",": ("..", "..", "..", "..", "..", ".#", ".#", "#."),
    ":": ("..", "..", "##", "..", "..", "##", "..", ".."),
    ";": ("..", "..", ".#", "..", "..", ".#", ".#", "#."),
    "!": ("..", "##", "##", "##", "##", "..", "##", ".."),
    "?": ("....", "###.", "...#", ".##.", ".#..", "....", ".#..", "...."),
    "-": ("....", "....", "....", "####", "....", "....", "....", "...."),
    "—": (".....", ".....", ".....", "#####", ".....", ".....", ".....", "....."),
    "+": (".....", ".....", "..#..", "#####", "..#..", ".....", ".....", "....."),
    "*": (".....", ".#.#.", "..#..", "#####", "..#..", ".#.#.", ".....", "....."),
    "/": ("....", "...#", "...#", "..#.", ".#..", "#...", "#...", "...."),
    "|": ("..", ".#", ".#", ".#", ".#", ".#", ".#", ".."),
    "(": ("...", ".#.", "#..", "#..", "#..", "#..", ".#.", "..."),
    ")": ("...", ".#.", "..#", "..#", "..#", "..#", ".#.", "..."),
    "[": ("...", "###", "#..", "#..", "#..", "#..", "###", "..."),
    "]": ("...", "###", "..#", "..#", "..#", "..#", "###", "..."),
    "<": ("....", "...#", "..#.", ".#..", "..#.", "...#", "....", "...."),
    ">": ("....", "#...", ".#..", "..#.", ".#..", "#...", "....", "...."),
    "'": ("..", ".#", ".#", "..", "..", "..", "..", ".."),
    '"': ("....", "#..#", "#..#", "....", "....", "....", "....", "...."),
    "°": ("...", ".#.", "#.#", ".#.", "...", "...", "...", "..."),
    "%": (".....", "##..#", "##.#.", "..#..", ".#.##", "#..##", ".....", "....."),
    "=": ("....", "....", "####", "....", "####", "....", "....", "...."),
    "_": (".....", ".....", ".....", ".....", ".....", ".....", "#####", "....."),
    "@": (".....", ".###.", "#...#", "#.###", "#.#.#", "#....", ".###.", "....."),
    "•": ("...", "...", "...", ".#.", "...", "...", "...", "..."),
    "★": (".....", "..#..", "#####", ".###.", "##.##", "#...#", ".....", "....."),
    "✓": (".....", ".....", "....#", "...#.", "#.#..", ".#...", ".....", "....."),
    "←": (".....", ".....", ".#...", "#####", ".#...", ".....", ".....", "....."),
    "→": (".....", ".....", "...#.", "#####", "...#.", ".....", ".....", "....."),
    "↑": (".....", "..#..", ".###.", "#.#.#", "..#..", "..#..", "..#..", "....."),
    "↓": (".....", "..#..", "..#..", "..#..", "#.#.#", ".###.", "..#..", "....."),
    "♥": (".....", ".....", "##.##", "#####", "#####", ".###.", "..#..", "....."),
    "♦": (".....", "..#..", ".###.", "#####", ".###.", "..#..", ".....", "....."),
    "“": ("....", "#.#.", "#.#.", "....", "....", "....", "....", "...."),
    "”": ("....", ".#.#", ".#.#", "....", "....", "....", "....", "...."),
    "ª": ("...", "##.", ".##", "###", "...", "###", "...", "..."),
    "º": ("...", ".#.", "#.#", ".#.", "...", "###", "...", "..."),
}

# Emojis viram símbolos da fonte (ou somem) em vez de aparecer como "?".
TROCAS_EMOJI = {
    "✨": "*", "⭐": "★", "🌟": "★", "🔴": "•", "🟡": "•", "⚪": "•",
}


def limpar_texto(texto):
    """Troca/remove caracteres que a fonte bitmap não tem (emojis, acentos raros)."""
    saida = []
    for ch in str(texto):
        if ch in GLIFOS_16BITS or ch.upper() in GLIFOS_16BITS:
            saida.append(ch)
        elif ch in TROCAS_EMOJI:
            saida.append(TROCAS_EMOJI[ch])
        elif ord(ch) >= 0x2190 or unicodedata.category(ch) in ("Mn", "Cf", "So"):
            continue  # emoji, seletor de variação, símbolo sem desenho
        else:
            base = unicodedata.normalize("NFD", ch)[0]
            saida.append(base if base in GLIFOS_16BITS else "?")
    resultado = "".join(saida)
    while "  " in resultado:
        resultado = resultado.replace("  ", " ")
    return resultado.strip() if resultado != str(texto) else resultado


class Fonte16Bits:
    """Fonte bitmap proporcional estilo SNES/16-bits com contorno nítido e gradiente luminoso."""

    def __init__(self, escala=1):
        self.escala = escala
        self._cache = {}

    def _glifo(self, ch):
        return GLIFOS_16BITS.get(ch, GLIFOS_16BITS.get(ch.upper(), GLIFOS_16BITS["?"]))

    def size(self, texto):
        texto = limpar_texto(texto)
        if not texto:
            return (0, 8 * self.escala)
        larg = sum(len(self._glifo(ch)[0]) + 1 for ch in str(texto)) - 1
        return ((larg + 2) * self.escala, 10 * self.escala)

    def render(self, texto, _antialias, cor):
        texto = limpar_texto(texto)
        cor_tupla = tuple(cor[:3])
        chave = (texto, cor_tupla, self.escala)
        if chave in self._cache:
            return self._cache[chave]

        larg_base = max(1, sum(len(self._glifo(ch)[0]) + 1 for ch in texto) + 1)
        alt_base = 10
        surf = pygame.Surface((larg_base, alt_base), pygame.SRCALPHA)

        # Topo iluminado (estilo 16-bits de Chrono Trigger / Zelda ALttP) e base na cor escolhida
        cor_topo = (
            min(255, cor_tupla[0] + 35),
            min(255, cor_tupla[1] + 35),
            min(255, cor_tupla[2] + 35),
        )
        cor_borda = (10, 12, 24, 245)

        # 1. Desenha os pixels de cada glifo e marca o contorno 16-bits
        mascara = []
        cursor_x = 1
        for ch in texto:
            grade = self._glifo(ch)
            larg_g = len(grade[0])
            for gy, linha in enumerate(grade):
                for gx, c in enumerate(linha):
                    if c == "#":
                        mascara.append((cursor_x + gx, 1 + gy))
            cursor_x += larg_g + 1

        # Contorno escuro completo de 1px + sombra inferior direita
        for px, py in mascara:
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (1, 1)):
                nx, ny = px + dx, py + dy
                if 0 <= nx < larg_base and 0 <= ny < alt_base:
                    surf.set_at((nx, ny), cor_borda)

        # Corpo da letra com brilho 16-bits na metade superior
        for px, py in mascara:
            surf.set_at((px, py), cor_topo if py <= 3 else cor_tupla)

        if self.escala > 1:
            surf = pygame.transform.scale(
                surf, (larg_base * self.escala, alt_base * self.escala)
            )

        if len(self._cache) > 600:
            self._cache.clear()
        self._cache[chave] = surf
        return surf


class Fontes:
    def __init__(self):
        self.normal = Fonte16Bits(escala=1)
        self.titulo = Fonte16Bits(escala=2)


def desenhar_texto(tela, fonte, texto, pos, cor=BRANCO, centro=False):
    """Desenha texto com a fonte 16-bits (já inclui contorno e brilho)."""
    img = fonte.render(texto, False, cor)
    r = img.get_rect(center=pos) if centro else img.get_rect(topleft=pos)
    tela.blit(img, r)


def quebrar_linhas(fonte, texto, largura):
    """Quebra o texto em linhas que cabem em `largura` pixels."""
    linhas, atual = [], ""
    for palavra in texto.split():
        tentativa = f"{atual} {palavra}".strip()
        if fonte.size(tentativa)[0] <= largura or not atual:
            atual = tentativa
        else:
            linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas or [""]


def ajustar_texto(fonte, texto, largura):
    """Corta o texto com '..' se ele passar de `largura` pixels."""
    texto = limpar_texto(texto)
    if fonte.size(texto)[0] <= largura:
        return texto
    while texto and fonte.size(texto + "..")[0] > largura:
        texto = texto[:-1]
    return texto.rstrip() + ".."


def desenhar_rodape(tela, fonte, texto, cor=CINZA):
    """Barra de dicas de controle no pé da tela; encurta as dicas se não couberem."""
    largura_tela, altura_tela = tela.get_size()
    texto = limpar_texto(texto)
    if fonte.size(texto)[0] > largura_tela - 8:
        texto = texto.replace(" | ", "  ").replace("Setas: ", "").replace(" / X", "").replace(" / B", "")
    texto = ajustar_texto(fonte, texto, largura_tela - 8)
    faixa = pygame.Surface((largura_tela, 12), pygame.SRCALPHA)
    faixa.fill((6, 8, 18, 235))
    pygame.draw.line(faixa, (120, 100, 60, 255), (0, 0), (largura_tela, 0))
    tela.blit(faixa, (0, altura_tela - 12))
    desenhar_texto(tela, fonte, texto, (largura_tela // 2, altura_tela - 6), cor, centro=True)


def escurecer(tela, alpha=150):
    camada = pygame.Surface(tela.get_size(), pygame.SRCALPHA)
    camada.fill((0, 0, 0, alpha))
    tela.blit(camada, (0, 0))


# ------------------------------------------------------------------ painéis
ESTILOS_PAINEL = {
    # topo do gradiente, base do gradiente, borda clara, borda escura, cantos
    "padrao": ((34, 42, 82), (14, 16, 38), (150, 164, 214), (54, 62, 110), (255, 214, 96)),
    "dourado": ((52, 40, 30), (20, 14, 16), (236, 196, 104), (120, 84, 40), (255, 240, 170)),
    "perigo": ((70, 22, 32), (26, 8, 16), (236, 110, 110), (120, 40, 50), (255, 190, 120)),
    "magico": ((40, 26, 76), (14, 10, 34), (184, 150, 255), (80, 56, 140), (140, 240, 255)),
}
_cache_painel = {}


def desenhar_painel(tela, rect, estilo="padrao", alfa=235, cantos=True):
    """Painel 16-bits: gradiente vertical, borda dupla chanfrada e cantos dourados."""
    rect = pygame.Rect(rect)
    if rect.width < 6 or rect.height < 6:
        return
    chave = (rect.size, estilo, alfa, cantos)
    surf = _cache_painel.get(chave)
    if surf is None:
        topo, base, clara, escura, cor_canto = ESTILOS_PAINEL.get(estilo, ESTILOS_PAINEL["padrao"])
        w, h = rect.size
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        for y in range(h):
            f = y / max(1, h - 1)
            cor = tuple(round(topo[i] * (1 - f) + base[i] * f) for i in range(3))
            pygame.draw.line(surf, (*cor, alfa), (1, y), (w - 2, y))
        # Contorno externo escuro com cantos arredondados (1px)
        contorno = (8, 8, 18, 255)
        pygame.draw.line(surf, contorno, (1, 0), (w - 2, 0))
        pygame.draw.line(surf, contorno, (1, h - 1), (w - 2, h - 1))
        pygame.draw.line(surf, contorno, (0, 1), (0, h - 2))
        pygame.draw.line(surf, contorno, (w - 1, 1), (w - 1, h - 2))
        # Borda chanfrada: clara em cima/esquerda, escura embaixo/direita
        pygame.draw.line(surf, (*clara, 255), (2, 1), (w - 3, 1))
        pygame.draw.line(surf, (*clara, 255), (1, 2), (1, h - 3))
        pygame.draw.line(surf, (*escura, 255), (2, h - 2), (w - 3, h - 2))
        pygame.draw.line(surf, (*escura, 255), (w - 2, 2), (w - 2, h - 3))
        # Brilho especular na quina superior esquerda
        surf.set_at((2, 2), (255, 255, 255, 200))
        if cantos and w >= 14 and h >= 14:
            for cx, cy in ((2, 2), (w - 4, 2), (2, h - 4), (w - 4, h - 4)):
                pygame.draw.rect(surf, (*cor_canto, 255), (cx, cy, 2, 2))
                surf.set_at((cx, cy), (255, 255, 255, 255))
        if len(_cache_painel) > 200:
            _cache_painel.clear()
        _cache_painel[chave] = surf
    tela.blit(surf, rect.topleft)


def desenhar_barra(tela, rect, proporcao, cor, cor_fundo=(12, 14, 28), brilho=True):
    """Barra de status com fundo afundado, preenchimento em dois tons e borda."""
    rect = pygame.Rect(rect)
    pygame.draw.rect(tela, (6, 6, 14), rect.inflate(2, 2))
    pygame.draw.rect(tela, cor_fundo, rect)
    cheio = round(rect.width * max(0.0, min(1.0, proporcao)))
    if cheio > 0:
        pygame.draw.rect(tela, cor, (rect.x, rect.y, cheio, rect.height))
        if brilho and rect.height >= 3:
            clara = tuple(min(255, c + 70) for c in cor)
            escura = tuple(max(0, c - 60) for c in cor)
            pygame.draw.line(tela, clara, (rect.x, rect.y), (rect.x + cheio - 1, rect.y))
            pygame.draw.line(tela, escura, (rect.x, rect.bottom - 1), (rect.x + cheio - 1, rect.bottom - 1))


# ------------------------------------------------------------------ ícones 7x7
ICONES = {
    "moeda": (
        "..###..", ".#yyy#.", "#yYyyy#", "#yYyyy#", "#yyyYy#", ".#yyy#.", "..###..",
    ),
    "bomba": (
        "....#y.", "...#...", "..###..", ".#bbb#.", "#bwbbb#", "#bbbbb#", ".#####.",
    ),
    "chave": (
        ".###...", "#y.y#..", "#y.y#..", ".###...", "..y....", "..yy...", "..yyy..",
    ),
    "escudo": (
        "#######", "#cCcCc#", "#ccccc#", "#cCcCc#", ".#ccc#.", "..#c#..", "...#...",
    ),
    "gota": (
        "...#...", "..#g#..", ".#ggg#.", "#ggwgg#", "#ggggg#", ".#ggg#.", "..###..",
    ),
    "estrela": (
        "...#...", "..#y#..", "##yyy##", "#yyyyy#", ".#yyy#.", "#y#.#y#", "#.....#",
    ),
    "coracao": (
        ".##.##.", "#rr#rr#", "#rrrrr#", "#rrrrr#", ".#rrr#.", "..#r#..", "...#...",
    ),
    "caveira": (
        ".#####.", "#wwwww#", "#w#w#w#", "#wwwww#", ".#w#w#.", ".#####.", ".......",
    ),
}
CORES_ICONE = {
    "#": (14, 12, 24), "y": (255, 216, 72), "Y": (255, 250, 200), "b": (58, 58, 78),
    "w": (236, 240, 255), "c": (90, 150, 240), "C": (170, 210, 255), "g": (80, 180, 255),
    "r": (232, 52, 72),
}
_cache_icone = {}


def icone(nome):
    if nome not in _cache_icone:
        grade = ICONES[nome]
        surf = pygame.Surface((7, 7), pygame.SRCALPHA)
        for y, linha in enumerate(grade):
            for x, c in enumerate(linha):
                if c != ".":
                    surf.set_at((x, y), CORES_ICONE[c])
        _cache_icone[nome] = surf
    return _cache_icone[nome]


def desenhar_icone(tela, nome, pos):
    tela.blit(icone(nome), pos)


def desenhar_tecla(tela, fonte, rotulo, pos):
    """Pequena 'tecla' 16-bits (ex.: [F]) para dicas de controle."""
    largura = max(9, fonte.size(rotulo)[0] + 2)
    r = pygame.Rect(pos[0], pos[1], largura, 10)
    pygame.draw.rect(tela, (8, 8, 16), r)
    pygame.draw.rect(tela, (70, 76, 110), r.inflate(-2, -2))
    pygame.draw.line(tela, (150, 158, 196), (r.x + 1, r.y + 1), (r.right - 2, r.y + 1))
    pygame.draw.line(tela, (34, 36, 58), (r.x + 1, r.bottom - 2), (r.right - 2, r.bottom - 2))
    desenhar_texto(tela, fonte, rotulo, (r.centerx + 1, r.centery), (255, 255, 255), centro=True)
    return r.width


def desenhar_cursor(tela, x, y, cor=AMARELO, t=None):
    """Seta de seleção que 'respira' horizontalmente."""
    if t is None:
        t = pygame.time.get_ticks() / 1000
    dx = round(math.sin(t * 8) * 1.2)
    pts = [(x + dx, y), (x + dx + 4, y + 3), (x + dx, y + 6)]
    pygame.draw.polygon(tela, (8, 8, 16), [(px + 1, py + 1) for px, py in pts])
    pygame.draw.polygon(tela, cor, pts)


class MenuLista:
    """Lista vertical de opções navegável com cima/baixo."""

    def __init__(self, opcoes):
        self.opcoes = list(opcoes)
        self.indice = 0

    def atualizar(self, entrada):
        """Devolve 'confirmar', 'voltar', 'esquerda', 'direita' ou None."""
        if entrada.apertou("cima"):
            self.indice = (self.indice - 1) % len(self.opcoes)
        if entrada.apertou("baixo"):
            self.indice = (self.indice + 1) % len(self.opcoes)
        for resultado in ("confirmar", "voltar", "esquerda", "direita"):
            if entrada.apertou(resultado):
                return resultado
        return None

    def desenhar(self, tela, fonte, centro_x, y, espaco=14, largura=None):
        """Desenha as opções centralizadas; a selecionada ganha faixa luminosa e cursor."""
        if largura is None:
            largura = max(fonte.size(t)[0] for t in self.opcoes) + 28
        t = pygame.time.get_ticks() / 1000
        for i, texto in enumerate(self.opcoes):
            cy = y + i * espaco
            if i == self.indice:
                faixa = pygame.Surface((largura, 11), pygame.SRCALPHA)
                for fx in range(largura):
                    borda = min(fx, largura - 1 - fx) / (largura / 2)
                    a = round(150 * min(1.0, borda * 2.2))
                    pygame.draw.line(faixa, (255, 200, 80, a // 3), (fx, 0), (fx, 10))
                pygame.draw.line(faixa, (255, 226, 130, 140), (largura // 6, 0), (largura * 5 // 6, 0))
                pygame.draw.line(faixa, (255, 226, 130, 140), (largura // 6, 10), (largura * 5 // 6, 10))
                tela.blit(faixa, (centro_x - largura // 2, cy - 5))
                pulso = int(230 + 25 * math.sin(t * 5.0))
                desenhar_texto(tela, fonte, texto, (centro_x, cy), (255, pulso, 110), centro=True)
                larg_txt = fonte.size(texto)[0]
                desenhar_cursor(tela, centro_x - larg_txt // 2 - 9, cy - 3, t=t)
            else:
                desenhar_texto(tela, fonte, texto, (centro_x, cy), CINZA, centro=True)
