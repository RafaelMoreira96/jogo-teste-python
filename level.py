"""Mapa do jogo, lido de um arquivo de texto (veja maps/mundo.txt).

Legenda:
    .  grama           ,  caminho        *  flores
    _  piso (madeira)  D  porta/tapete
    T  árvore (sólido) #  pedra (sólido) ~  água (sólido)
    W  parede (sólido) R  telhado        C  cama          M  mesa
    B  arbusto (sólido, dá para cortar com a espada)
    P  início do jogador   S  slime   H  coração
    1-9  NPC (definido na seção [npcs] no fim do arquivo)
"""
import math
from pathlib import Path

import pygame

from render3d import (
    criar_cristal_3d,
    desenhar_copas_3d_arvores,
    desenhar_relevo_3d_mapa,
    gerar_objetos_3d_nivel,
)
from settings import ALTURA, LARGURA, TILE
from temas import GraficosTema, desenhar_decoracao, obter_tema

SIMBOLOS = {
    ",": "caminho",
    "*": "flores",
    "~": "agua",
    "#": "pedra",
    "T": "arvore",
    "B": "arbusto",
    "_": "piso",
    "W": "parede",
    "R": "telhado",
    "C": "cama",
    "M": "mesa",
    "D": "porta",
}
SOLIDOS_TERRA = set("#TBWRCM")
SOLIDOS = set("~#TBWRCM")


def _ruido(x, y):
    """Ruído de valor suave (0..1) para manchas grandes de luz e sombra no terreno."""
    def h(ix, iy):
        n = (ix * 374761393 + iy * 668265263) & 0xFFFFFFFF
        n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
        return (n & 0xFFFF) / 0xFFFF

    x0, y0 = math.floor(x), math.floor(y)
    fx, fy = x - x0, y - y0
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a = h(x0, y0) + (h(x0 + 1, y0) - h(x0, y0)) * fx
    b = h(x0, y0 + 1) + (h(x0 + 1, y0 + 1) - h(x0, y0 + 1)) * fx
    return a + (b - a) * fy


_MANCHAS = {}


def _mancha(cor, alfa):
    chave = (cor, alfa)
    if chave not in _MANCHAS:
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        s.fill((*cor, alfa))
        _MANCHAS[chave] = s
    return _MANCHAS[chave]


class Nivel:
    def __init__(self, caminho, gfx):
        self.gfx = gfx
        self.caminho = Path(caminho)
        linhas_grade, definicoes_npc, definicoes_porta, info_mapa, definicoes_chefe, definicoes_inimigo = self._ler_arquivo()
        self.nome = info_mapa.get("nome", self.caminho.stem.replace("_", " ").title())
        self.clima_padrao = info_mapa.get("clima", "dia")
        # Tema visual do covil (chão, líquido, paredes, partículas e luz próprios)
        self.tema = obter_tema(info_mapa.get("tema"))
        self.gfx_tema = GraficosTema(self.tema) if self.tema else None
        largura = max(len(l) for l in linhas_grade)
        # Linhas mais curtas são completadas com árvores.
        self.grade = [list(l.ljust(largura, "T")) for l in linhas_grade]
        self.colunas, self.linhas = largura, len(self.grade)
        self.largura_px, self.altura_px = self.colunas * TILE, self.linhas * TILE
        self.obstaculos = []  # retângulos extras que bloqueiam (ex.: NPCs)
        self.eh_interior = any("_" in l for l in self.grade)
        chao_padrao = "_" if self.eh_interior else "."

        # Pontos de nascimento (meio da base do tile), portas e itens.
        self.inicio = (TILE + TILE // 2, TILE * 2)
        self.cama_pos = (TILE * 2, TILE * 2)
        self.mesas = []
        self.flores_pos = []
        self.slimes = []
        self.inimigos = []  # [(tipo, x, y)]
        self.coracoes = []
        self.pontos_salvamento = []
        self.chefes = []  # [(id_chefe, x, y)]
        self.npcs = []  # (x, y, aparencia, dialogo)
        self.portas = []  # (rect, arquivo_destino)

        # Elementos interativos de Masmorra, Puzzles e Economia (Pilares 1 e 2)
        self.baus = []
        self.placas = []
        self.blocos = []
        self.portoes = []
        self.paredes_rachadas = []
        self.itens_quest = []
        # Pilares de Navegação, Viagem Rápida, Vasos e Relíquias (Prompt 2)
        self.monolitos = []
        self.totens = []
        self.vasos = []
        self.reliquias = []
        for cy, linha in enumerate(self.grade):
            for cx, c in enumerate(linha):
                base = (cx * TILE + TILE // 2, cy * TILE + TILE)
                if c == "C":
                    self.cama_pos = (cx * TILE, cy * TILE)
                    continue
                if c == "M":
                    self.mesas.append((cx * TILE + TILE // 2, cy * TILE + TILE // 2))
                    continue
                if c == "*":
                    self.flores_pos.append((cx * TILE + TILE // 2, cy * TILE + TILE // 2))
                    continue
                if c == "$":
                    self.pontos_salvamento.append((cx * TILE + TILE // 2, cy * TILE + TILE // 2))
                    linha[cx] = chao_padrao
                    continue
                if c in definicoes_porta:
                    rect_porta = pygame.Rect(cx * TILE, cy * TILE, TILE, TILE)
                    self.portas.append((rect_porta, self.caminho.parent / definicoes_porta[c]))
                    eh_porta_casa = (
                        c == "D"
                        or self.eh_interior
                        or (cx > 0 and linha[cx - 1] == "W")
                        or (cx + 1 < largura and linha[cx + 1] == "W")
                        or (cy > 0 and self.grade[cy - 1][cx] in ("W", "R"))
                    )
                    linha[cx] = "D" if eh_porta_casa else ","
                    continue
                if c == "P":
                    self.inicio = base
                elif c == "S":
                    self.slimes.append(base)
                    self.inimigos.append(("slime", *base))
                elif c == "V":
                    self.slimes.append(base)
                    self.inimigos.append(("slime_verde", *base))
                elif c == "G":
                    self.inimigos.append(("duende", *base))
                elif c == "Z":
                    self.inimigos.append(("zumbi_arqueiro", *base))
                elif c == "X":
                    self.inimigos.append(("troll", *base))
                elif c == "H":
                    self.coracoes.append((cx * TILE + TILE // 2, cy * TILE + TILE // 2))
                elif c.isdigit():
                    if c not in definicoes_npc:
                        raise ValueError(
                            f"{self.caminho.name}: o NPC '{c}' está no mapa (linha {cy + 1}) "
                            f"mas não foi definido em [npcs]."
                        )
                    self.npcs.append((*base, *definicoes_npc[c], c))
                else:
                    continue
                linha[cx] = chao_padrao

        # Inimigos definidos na seção [inimigos]
        for tipo_ini, cx, cy in definicoes_inimigo:
            self.inimigos.append((tipo_ini, cx * TILE + TILE // 2, cy * TILE + TILE))

        # Chefões definidos na seção [chefes]
        for id_chefe, cx, cy in definicoes_chefe:
            self.chefes.append((id_chefe, cx * TILE + TILE // 2, cy * TILE + TILE))

        # O chão inteiro é desenhado uma vez numa Surface grande.
        self.superficie = pygame.Surface((self.largura_px, self.altura_px))
        for cy in range(self.linhas):
            for cx in range(self.colunas):
                self._desenhar_tile(cx, cy)

        # Camada de detalhes de mundo (auto-tiling, pontes, margens, sombras 3D, janelas e flora)
        self.bioma = self._detectar_bioma()
        self.tochas = []
        self.janelas = []
        self.cachoeiras = []
        self.chamines = []
        self.postes_luz = []
        self.camada_detalhes = pygame.Surface((self.largura_px, self.altura_px), pygame.SRCALPHA)
        self._construir_camada_detalhes()
        self.objetos_3d = gerar_objetos_3d_nivel(self)
        self._carregar_elementos_interativos()

    def _carregar_elementos_interativos(self):
        nome_mapa = self.caminho.stem.lower()

        # Monólitos Astrais de Teleporte (Rede dos 6 Waypoints)
        if "vila" == nome_mapa:
            self.monolitos.append(((28 * TILE, 8 * TILE), "vila", "Vila de Aurora"))
        elif "mundo" == nome_mapa:
            self.monolitos.append(((16 * TILE, 14 * TILE), "mundo", "Encruzilhada Central"))
        elif "oasis" == nome_mapa:
            self.monolitos.append(((16 * TILE, 12 * TILE), "oasis", "Oásis do Deserto"))
        elif "bosque_outono" == nome_mapa:
            self.monolitos.append(((16 * TILE, 12 * TILE), "bosque", "Bosque de Outono"))
        elif "caverna_cristal" == nome_mapa:
            self.monolitos.append(((14 * TILE, 8 * TILE), "caverna", "Caverna de Cristal"))
        elif "castelo" == nome_mapa:
            self.monolitos.append(((16 * TILE, 14 * TILE), "castelo", "Entrada do Castelo"))

        # Totens de Sinalização de Estrada
        if "mundo" == nome_mapa:
            self.totens.append(((14 * TILE, 15 * TILE), ["← Vila de Aurora", "Ruínas →", "↑ Lago Cristalino", "↓ Pântano Sombrio"]))
        elif "lago" == nome_mapa:
            self.totens.append(((18 * TILE, 12 * TILE), ["← Deserto dos Sussurros", "Vila de Aurora →", "↑ Caverna de Cristal"]))
        elif "deserto" == nome_mapa:
            self.totens.append(((12 * TILE, 8 * TILE), ["↑ Oásis do Deserto", "Abismo das Dunas →", "← Lago Cristalino"]))
        elif "ruinas" == nome_mapa:
            self.totens.append(((14 * TILE, 10 * TILE), ["← Floresta Esmeralda", "Cripta dos Reis →", "↑ Câmara do Golem"]))
        elif "montanha" == nome_mapa:
            self.totens.append(((12 * TILE, 8 * TILE), ["↓ Vila de Aurora", "↑ Pico Congelado", "→ Caverna do Troll"]))
        elif "oasis" == nome_mapa:
            self.totens.append(((12 * TILE, 10 * TILE), ["↓ Deserto dos Sussurros", "↑ Templo do Sol"]))
        elif "pantano" == nome_mapa:
            self.totens.append(((16 * TILE, 8 * TILE), ["↑ Floresta Esmeralda", "→ Antro da Bruxa", "← Bosque de Outono"]))

        # Relíquias Secretas dos Guardiões Antigos
        if "bosque_outono" == nome_mapa:
            self.reliquias.append(((28 * TILE, 16 * TILE), "reliquia_vento"))
        elif "templo_sol" == nome_mapa:
            self.reliquias.append(((24 * TILE, 8 * TILE), "reliquia_areias"))
        elif "caverna_cristal" == nome_mapa:
            self.reliquias.append(((28 * TILE, 3 * TILE), "reliquia_cristais"))
        elif "pantano" == nome_mapa:
            self.reliquias.append(((36 * TILE, 16 * TILE), "reliquia_pantanos"))
        elif "pico_congelado" == nome_mapa:
            self.reliquias.append(((26 * TILE, 6 * TILE), "reliquia_gelo"))
        elif "cripta" == nome_mapa:
            self.reliquias.append(((25 * TILE, 3 * TILE), "reliquia_cripta"))

        # Vasos de Cerâmica Quebráveis
        if "casa" == nome_mapa:
            self.vasos += [(5 * TILE, 3 * TILE), (8 * TILE, 3 * TILE)]
        elif "casa_anciao" == nome_mapa:
            self.vasos += [(4 * TILE, 3 * TILE), (9 * TILE, 3 * TILE)]
        elif "bazar_oasis" == nome_mapa:
            self.vasos += [(3 * TILE, 3 * TILE), (8 * TILE, 3 * TILE)]
        elif "taverna_vila" == nome_mapa:
            self.vasos += [(3 * TILE, 4 * TILE), (11 * TILE, 4 * TILE)]
        elif "ruinas" == nome_mapa:
            self.vasos += [(16 * TILE, 6 * TILE), (22 * TILE, 6 * TILE), (28 * TILE, 12 * TILE)]
        elif "templo_sol" == nome_mapa:
            self.vasos += [(10 * TILE, 6 * TILE), (18 * TILE, 6 * TILE), (26 * TILE, 12 * TILE)]
        elif "cripta" == nome_mapa:
            self.vasos += [(12 * TILE, 4 * TILE), (18 * TILE, 4 * TILE), (30 * TILE, 8 * TILE)]
        elif "caverna_cristal" == nome_mapa:
            self.vasos += [(8 * TILE, 6 * TILE), (16 * TILE, 6 * TILE)]
        elif "castelo_masmorra" == nome_mapa:
            self.vasos += [(10 * TILE, 6 * TILE), (24 * TILE, 6 * TILE)]
        elif "castelo_biblioteca" == nome_mapa:
            self.vasos += [(6 * TILE, 4 * TILE), (14 * TILE, 4 * TILE)]

        # Configurações existentes de quests, baús e puzzles
        if "pantano" in nome_mapa:
            self.itens_quest.append(("cogumelo_noturno", 14 * TILE, 10 * TILE))
            self.itens_quest.append(("cogumelo_noturno", 24 * TILE, 12 * TILE))
            self.itens_quest.append(("cogumelo_noturno", 38 * TILE, 18 * TILE))
            self.baus.append(("madeira", 34 * TILE, 19 * TILE, {"ouro": 35, "bombas": 2}))

        elif "caverna_cristal" in nome_mapa:
            self.itens_quest.append(("minerio_cristal", 10 * TILE, 4 * TILE))
            self.itens_quest.append(("minerio_cristal", 38 * TILE, 4 * TILE))
            self.baus.append(("ferro", 24 * TILE, 4 * TILE, {"ouro": 60, "chave": 1, "bombas": 3}))
            self.placas.append((22 * TILE, 12 * TILE, "porta_cristal"))
            self.blocos.append((18 * TILE, 12 * TILE))

        elif "cripta" in nome_mapa:
            self.baus.append(("ferro", 39 * TILE, 10 * TILE, {"ouro": 50, "chave": 1}))
            self.paredes_rachadas.append((24 * TILE, 1 * TILE))
            self.baus.append(("ouro", 24 * TILE, 3 * TILE, {"ouro": 90, "arma": "lamina_vulcanica"}))

        elif "ruinas" in nome_mapa:
            self.baus.append(("madeira", 12 * TILE, 8 * TILE, {"ouro": 30, "bombas": 2}))
            self.paredes_rachadas.append((30 * TILE, 6 * TILE))
            self.baus.append(("ferro", 32 * TILE, 6 * TILE, {"ouro": 70, "chave": 1}))

        elif "castelo_masmorra" in nome_mapa:
            self.placas.append((16 * TILE, 10 * TILE, "portao_masmorra"))
            self.blocos.append((14 * TILE, 10 * TILE))
            self.portoes.append((18 * TILE, 10 * TILE, "portao_masmorra"))
            self.baus.append(("ferro", 22 * TILE, 10 * TILE, {"ouro": 80, "chave": 1}))

        elif "santuario" in nome_mapa:
            self.baus.append(("ouro", 16 * TILE, 8 * TILE, {"ouro": 120, "arma": "lamina_lendaria"}))

    def _detectar_bioma(self):
        nome_arq = self.caminho.stem.lower()
        if any(k in nome_arq for k in ("deserto", "oasis", "templo_sol")):
            return "deserto"
        if any(k in nome_arq for k in ("congelado", "gelo")):
            return "gelo"
        if "outono" in nome_arq:
            return "outono"
        if "pantano" in nome_arq:
            return "pantano"
        if any(k in nome_arq for k in ("santuario", "castelo", "cripta", "caverna")):
            return "arcano"
        return "padrao"

    def ponto_entrada_porta(self, origem=None):
        """Posição (x, y, direcao) logo em frente à porta que veio de `origem`."""
        if not self.portas:
            return (*self.inicio, "baixo")

        portas_alvo = []
        if origem is not None:
            origem_resolvida = Path(origem).resolve()
            portas_alvo = [r for r, dest in self.portas if dest.resolve() == origem_resolvida]
        if not portas_alvo:
            portas_alvo = [self.portas[0][0]]

        rect = portas_alvo[len(portas_alvo) // 2]
        cx, cy = rect.x // TILE, rect.y // TILE
        portas_coords = {(r.x // TILE, r.y // TILE) for r, _ in self.portas}

        # Se a saída fica na borda do mapa, posiciona o herói um passo para dentro
        if cy == 0 and self.dentro(cx, cy + 1) and not self.solido(cx, cy + 1):
            return (cx * TILE + TILE // 2, (cy + 1) * TILE + TILE, "baixo")
        if cy == self.linhas - 1 and self.dentro(cx, cy - 1) and not self.solido(cx, cy - 1):
            return (cx * TILE + TILE // 2, (cy - 1) * TILE + TILE, "cima")
        if cx == 0 and self.dentro(cx + 1, cy) and not self.solido(cx + 1, cy):
            return ((cx + 1) * TILE + TILE // 2, cy * TILE + TILE, "direita")
        if cx == self.colunas - 1 and self.dentro(cx - 1, cy) and not self.solido(cx - 1, cy):
            return ((cx - 1) * TILE + TILE // 2, cy * TILE + TILE, "esquerda")

        for dx, dy, direcao in ((0, -1, "cima"), (0, 1, "baixo"), (-1, 0, "esquerda"), (1, 0, "direita")):
            nx, ny = cx + dx, cy + dy
            if self.dentro(nx, ny) and not self.solido(nx, ny) and (nx, ny) not in portas_coords:
                return (nx * TILE + TILE // 2, ny * TILE + TILE, direcao)
        return (*self.inicio, "baixo")

    def _ler_arquivo(self):
        """Separa a grade do mapa das seções [npcs], [portas], [chefes], [inimigos] e [mapa]."""
        grade, npcs, portas, info, chefes, inimigos, secao = [], {}, {}, {}, [], [], None
        for n, bruta in enumerate(self.caminho.read_text(encoding="utf-8").splitlines(), 1):
            linha = bruta.rstrip()
            if linha.startswith("["):
                secao = linha.strip("[] ").lower()
                continue
            if secao is None:
                if linha:
                    grade.append(linha)
                continue
            linha = linha.strip()
            if not linha or linha.startswith("#"):
                continue
            if secao == "npcs":
                chave, _, resto = linha.partition("=")
                partes = [p.strip() for p in resto.split(",")]
                if len(partes) != 2 or not chave.strip() or not all(partes):
                    raise ValueError(f"{self.caminho.name}, linha {n}: use '1 = aparencia, dialogo'.")
                if partes[0] not in self.gfx.npcs:
                    opcoes = ", ".join(self.gfx.npcs)
                    raise ValueError(
                        f"{self.caminho.name}, linha {n}: aparência '{partes[0]}' não existe "
                        f"(opções: {opcoes})."
                    )
                npcs[chave.strip()] = tuple(partes)
            elif secao == "portas":
                chave, _, destino = linha.partition("=")
                if not chave.strip() or not destino.strip():
                    raise ValueError(f"{self.caminho.name}, linha {n}: use 'D = mapa.txt'.")
                portas[chave.strip()] = destino.strip()
            elif secao == "chefes":
                chave, _, pos_str = linha.partition("=")
                partes = [p.strip() for p in pos_str.split(",")]
                if len(partes) == 2 and partes[0].isdigit() and partes[1].isdigit():
                    chefes.append((chave.strip().lower(), int(partes[0]), int(partes[1])))
            elif secao == "inimigos":
                chave, _, pos_str = linha.partition("=")
                partes = [p.strip() for p in pos_str.split(",")]
                if len(partes) == 2 and partes[0].isdigit() and partes[1].isdigit():
                    inimigos.append((chave.strip().lower(), int(partes[0]), int(partes[1])))
            elif secao == "mapa":
                chave, _, valor = linha.partition("=")
                if chave.strip() and valor.strip():
                    info[chave.strip().lower()] = valor.strip()
        return grade, npcs, portas, info, chefes, inimigos

    def _simbolo_em(self, cx, cy):
        if 0 <= cx < self.colunas and 0 <= cy < self.linhas:
            return self.grade[cy][cx]
        return None

    def _construir_camada_detalhes(self):
        """Gera transições de borda (Zelda ALttP), micro-flora (Legend of Mana) e sombras (Octopath)."""
        det = self.camada_detalhes
        det.fill((0, 0, 0, 0))
        self.tochas.clear()
        self.janelas.clear()
        self.cachoeiras.clear()
        self.chamines.clear()
        self.postes_luz.clear()
        eh_sombrio = self.clima_padrao in ("trevas", "noite") or self.bioma == "arcano"

        # Tintura sutil de bioma sobre o terreno (Deserto Dourado, Pico Gélido, Bosque de Outono, Pântano)
        tintas_bioma = {
            "deserto": (235, 190, 95, 48),
            "gelo": (185, 230, 255, 52),
            "outono": (235, 140, 45, 38),
            "pantano": (40, 85, 55, 42),
            "arcano": (45, 30, 85, 36),
        }
        cor_bioma = None if self.tema else tintas_bioma.get(self.bioma)

        for cy in range(self.linhas):
            for cx in range(self.colunas):
                c = self.grade[cy][cx]
                px, py = cx * TILE, cy * TILE
                cima = self._simbolo_em(cx, cy - 1)
                baixo = self._simbolo_em(cx, cy + 1)
                esq = self._simbolo_em(cx - 1, cy)
                dir_ = self._simbolo_em(cx + 1, cy)
                h_val = (cx * 37 + cy * 73) % 100

                if cor_bioma and c in (".", "*", "T", "B", "#"):
                    pygame.draw.rect(det, cor_bioma, (px, py, TILE, TILE))

                # 1. Margens orgânicas, reflexos, cachoeiras, espuma e vitórias-régias na água (~)
                if c == "~":
                    cor_margem = (186, 156, 104, 235)
                    cor_espuma = (210, 245, 255, 210)
                    if self.tema:
                        cor_margem = (*self.tema["margem"], 235)
                        cor_espuma = (*self.tema["liquido"][1], 200)
                    else:
                        # Água rasa e mais clara junto à margem (dá profundidade ao lago)
                        raso = (110, 190, 230, 110)
                        for viz, ret in ((cima, (px, py, TILE, 5)), (baixo, (px, py + TILE - 5, TILE, 5)),
                                         (esq, (px, py, 5, TILE)), (dir_, (px + TILE - 5, py, 5, TILE))):
                            if viz and viz != "~":
                                pygame.draw.rect(det, raso, ret)
                    if cima == "#" and (not self.tema or self.tema["anim"] == "agua"):
                        # Cachoeira desaguando da falésia de pedra superior
                        self.cachoeiras.append((px, py))
                    elif cima and cima != "~":
                        pygame.draw.rect(det, cor_margem, (px, py, TILE, 2))
                        pygame.draw.line(det, cor_espuma, (px + 1, py + 2), (px + TILE - 2, py + 2))
                        if cima in ("T", "W", "R"):
                            # Reflexo espelhado na água
                            pygame.draw.rect(det, (20, 55, 95, 78), (px + 2, py + 3, TILE - 4, 5))
                    if baixo and baixo != "~":
                        pygame.draw.rect(det, cor_margem, (px, py + TILE - 2, TILE, 2))
                        pygame.draw.line(det, cor_espuma, (px + 1, py + TILE - 3), (px + TILE - 2, py + TILE - 3))
                    if esq and esq != "~":
                        pygame.draw.rect(det, cor_margem, (px, py, 2, TILE))
                        pygame.draw.line(det, cor_espuma, (px + 2, py + 1), (px + 2, py + TILE - 2))
                    if dir_ and dir_ != "~":
                        pygame.draw.rect(det, cor_margem, (px + TILE - 2, py, 2, TILE))
                        pygame.draw.line(det, cor_espuma, (px + TILE - 3, py + 1), (px + TILE - 3, py + TILE - 2))
                    # Vitórias-régias (lilypads) com flor de lótus
                    if h_val < 18 and cima != "#" and not self.tema:
                        lx, ly = px + 5 + (h_val % 5), py + 5 + ((h_val // 3) % 5)
                        pygame.draw.circle(det, (44, 134, 62, 240), (lx, ly), 3)
                        pygame.draw.circle(det, (86, 178, 84, 240), (lx - 1, ly - 1), 2)
                        det.set_at((lx + 2, ly), (46, 108, 188, 255))
                        if h_val % 3 == 0:
                            det.set_at((lx, ly - 1), (255, 175, 210, 255))
                            det.set_at((lx - 1, ly), (255, 235, 245, 255))

                # 2. Pontes de madeira sobre a água, calçamento de pedras e bordas de caminho (,)
                elif c == ",":
                    agua_h = esq == "~" or dir_ == "~"
                    agua_v = cima == "~" or baixo == "~"
                    if agua_h or agua_v:
                        # Ponte de tábuas de madeira com guarda-corpo (Zelda ALttP)
                        pygame.draw.rect(det, (132, 84, 46, 255), (px, py, TILE, TILE))
                        if agua_h:
                            for ty in range(0, TILE, 4):
                                pygame.draw.line(det, (92, 54, 28, 255), (px, py + ty), (px + TILE - 1, py + ty))
                                pygame.draw.line(det, (166, 110, 64, 255), (px + 2, py + ty + 1), (px + TILE - 3, py + ty + 1))
                            pygame.draw.rect(det, (78, 44, 22, 255), (px, py, 2, TILE))
                            pygame.draw.rect(det, (78, 44, 22, 255), (px + TILE - 2, py, 2, TILE))
                            pygame.draw.rect(det, (188, 132, 78, 255), (px, py + 2, 2, 2))
                            pygame.draw.rect(det, (188, 132, 78, 255), (px + TILE - 2, py + 2, 2, 2))
                        else:
                            for tx in range(0, TILE, 4):
                                pygame.draw.line(det, (92, 54, 28, 255), (px + tx, py), (px + tx, py + TILE - 1))
                                pygame.draw.line(det, (166, 110, 64, 255), (px + tx + 1, py + 2), (px + tx + 1, py + TILE - 3))
                            pygame.draw.rect(det, (78, 44, 22, 255), (px, py, TILE, 2))
                            pygame.draw.rect(det, (78, 44, 22, 255), (px, py + TILE - 2, TILE, 2))
                    else:
                        # Ladrilhos de pedra antigos no caminho (estilo Legend of Mana)
                        if h_val % 3 == 0:
                            ox_p, oy_p = 3 + (h_val % 5), 4 + ((h_val // 2) % 5)
                            pygame.draw.rect(det, (168, 138, 96, 165), (px + ox_p, py + oy_p, 5, 4), 1)
                            det.set_at((px + ox_p + 1, py + oy_p + 1), (218, 192, 146, 180))
                        # Transição suave de grama invadindo a borda do caminho
                        cor_borda = (76, 152, 64, 235)
                        cor_sombra_borda = (148, 116, 74, 210)
                        if cima in (".", "*", "T", "B"):
                            pygame.draw.line(det, cor_borda, (px, py), (px + TILE - 1, py))
                            pygame.draw.line(det, cor_sombra_borda, (px + 1, py + 1), (px + TILE - 2, py + 1))
                        if baixo in (".", "*", "T", "B"):
                            pygame.draw.line(det, cor_borda, (px, py + TILE - 1), (px + TILE - 1, py + TILE - 1))
                        if esq in (".", "*", "T", "B"):
                            pygame.draw.line(det, cor_borda, (px, py), (px, py + TILE - 1))
                            pygame.draw.line(det, cor_sombra_borda, (px + 1, py + 1), (px + 1, py + TILE - 2))
                        if dir_ in (".", "*", "T", "B"):
                            pygame.draw.line(det, cor_borda, (px + TILE - 1, py), (px + TILE - 1, py + TILE - 1))

                # 3. Arquitetura 16-bits das Casas (W = paredes enxaimel, R = telhados, D = portas)
                elif c == "W":
                    if self.eh_interior:
                        # Decoração interna nas paredes do fundo (estantes de livros, lareira, janelas)
                        if baixo in ("_", "C", "M"):
                            mod = (cx + cy) % 4
                            if mod == 0:
                                # Estante de livros 16-bits
                                pygame.draw.rect(det, (78, 46, 24, 255), (px + 2, py + 2, 12, 13))
                                pygame.draw.rect(det, (118, 72, 38, 255), (px + 2, py + 2, 12, 13), 1)
                                pygame.draw.line(det, (118, 72, 38, 255), (px + 3, py + 7), (px + 12, py + 7))
                                cores_livros = [(210, 55, 55), (55, 125, 210), (70, 165, 75), (235, 190, 60)]
                                for lx in range(3, 12, 2):
                                    cor_l = (*cores_livros[(lx + cx) % 4], 255)
                                    pygame.draw.rect(det, cor_l, (px + lx, py + 3, 2, 4))
                                    pygame.draw.rect(det, cor_l, (px + lx, py + 8, 2, 4))
                            elif mod == 2:
                                # Janela interna com luz do dia/luar
                                pygame.draw.rect(det, (68, 42, 22, 255), (px + 3, py + 2, 10, 8))
                                pygame.draw.rect(det, (175, 225, 255, 255), (px + 4, py + 3, 8, 6))
                                pygame.draw.line(det, (68, 42, 22, 255), (px + 7, py + 3), (px + 7, py + 8))
                                pygame.draw.line(det, (68, 42, 22, 255), (px + 4, py + 5), (px + 11, py + 5))
                                self.janelas.append((px + TILE // 2, py + 6))
                    else:
                        # Fachada externa enxaimel 16-bits
                        if cima == "R":
                            # Prolongamento do beiral do telhado sobre o topo da parede (5px) + sombra projetada
                            pygame.draw.rect(det, (172, 58, 48, 255), (px, py, TILE, 4))
                            for tx in range(0, TILE, 4):
                                pygame.draw.line(det, (214, 92, 72, 255), (px + tx + 1, py), (px + tx + 2, py))
                                pygame.draw.line(det, (122, 34, 30, 255), (px + tx, py), (px + tx, py + 4))
                                pygame.draw.rect(det, (96, 26, 24, 255), (px + tx, py + 4, 4, 1))
                            pygame.draw.rect(det, (28, 16, 14, 135), (px, py + 5, TILE, 3))
                            # Mão-francesa diagonal de carvalho (enxaimel) ou janela se for chalé de 1 andar
                            if baixo == "D":
                                pygame.draw.polygon(
                                    det,
                                    (92, 56, 32, 255),
                                    [(px + 2, py + 15), (px + 8, py + 8), (px + 13, py + 15)],
                                    1,
                                )
                                pygame.draw.rect(det, (255, 220, 110, 255), (px + 7, py + 11, 2, 3))
                                self.janelas.append((px + 8, py + 12))
                            elif esq == "D" or dir_ == "D":
                                pygame.draw.rect(det, (48, 98, 58, 255), (px + 1, py + 6, 2, 6))
                                pygame.draw.rect(det, (48, 98, 58, 255), (px + 13, py + 6, 2, 6))
                                pygame.draw.rect(det, (64, 38, 20, 255), (px + 3, py + 5, 10, 7))
                                pygame.draw.rect(det, (255, 224, 120, 255), (px + 4, py + 6, 8, 5))
                                pygame.draw.line(det, (74, 44, 24, 255), (px + 7, py + 6), (px + 7, py + 10))
                                pygame.draw.line(det, (74, 44, 24, 255), (px + 4, py + 8), (px + 11, py + 8))
                                pygame.draw.rect(det, (58, 138, 56, 255), (px + 3, py + 12, 10, 2))
                                det.set_at((px + 5, py + 12), (240, 75, 85, 255))
                                det.set_at((px + 10, py + 12), (255, 225, 85, 255))
                                self.janelas.append((px + TILE // 2, py + 8))
                            else:
                                pygame.draw.line(det, (92, 56, 32, 255), (px + 2, py + 7), (px + 13, py + 14))
                                pygame.draw.line(det, (92, 56, 32, 255), (px + 13, py + 7), (px + 2, py + 14))
                        elif cima == "W":
                            # Parte inferior da fachada (ao lado da porta): Janela iluminada com venezianas e floreira
                            pygame.draw.rect(det, (48, 98, 58, 255), (px + 1, py + 2, 2, 7))
                            pygame.draw.rect(det, (48, 98, 58, 255), (px + 13, py + 2, 2, 7))
                            pygame.draw.rect(det, (64, 38, 20, 255), (px + 3, py + 1, 10, 8))
                            pygame.draw.rect(det, (255, 224, 120, 255), (px + 4, py + 2, 8, 6))
                            pygame.draw.line(det, (255, 248, 200, 255), (px + 5, py + 3), (px + 6, py + 3))
                            pygame.draw.line(det, (74, 44, 24, 255), (px + 7, py + 2), (px + 7, py + 7))
                            pygame.draw.line(det, (74, 44, 24, 255), (px + 4, py + 4), (px + 11, py + 4))
                            # Floreira sob a janela
                            pygame.draw.rect(det, (112, 68, 36, 255), (px + 3, py + 9, 10, 3))
                            pygame.draw.rect(det, (58, 138, 56, 255), (px + 3, py + 8, 10, 2))
                            det.set_at((px + 5, py + 8), (240, 75, 85, 255))
                            det.set_at((px + 8, py + 8), (255, 225, 85, 255))
                            det.set_at((px + 11, py + 8), (240, 75, 85, 255))
                            self.janelas.append((px + TILE // 2, py + 5))

                # 3b. Porta de entrada externa da casa (D) com arco de pedra e porta de carvalho
                elif c == "D" and not self.eh_interior:
                    # Parede enxaimel ao redor do batente
                    pygame.draw.rect(det, (224, 206, 176, 255), (px, py, TILE, TILE))
                    pygame.draw.rect(det, (108, 110, 124, 255), (px, py + 12, TILE, 4))
                    # Arco de cantaria de pedra
                    pygame.draw.rect(det, (124, 128, 144, 255), (px + 2, py + 1, 12, 14))
                    pygame.draw.line(det, (168, 172, 188, 255), (px + 3, py + 1), (px + 12, py + 1))
                    # Folha da porta de carvalho arqueada com ferragens e maçaneta dourada
                    pygame.draw.rect(det, (104, 58, 30, 255), (px + 4, py + 3, 8, 12))
                    pygame.draw.line(det, (136, 82, 44, 255), (px + 5, py + 3), (px + 10, py + 3))
                    for dx_p in (6, 9):
                        pygame.draw.line(det, (74, 40, 20, 255), (px + dx_p, py + 3), (px + dx_p, py + 14))
                    pygame.draw.line(det, (52, 54, 66, 255), (px + 4, py + 6), (px + 6, py + 6))
                    pygame.draw.line(det, (52, 54, 66, 255), (px + 4, py + 11), (px + 6, py + 11))
                    det.set_at((px + 10, py + 9), (250, 210, 75, 255))
                    # Soleira de pedra na entrada
                    pygame.draw.rect(det, (152, 156, 170, 255), (px + 2, py + 14, 12, 2))

                # 4. Telhados (R) com cumeeira ornamentada, beirais laterais e chaminés com fumaça
                elif c == "R":
                    if cima != "R":
                        pygame.draw.rect(det, (128, 68, 38, 255), (px, py, TILE, 3))
                        pygame.draw.line(det, (238, 148, 96, 255), (px, py + 1), (px + TILE - 1, py + 1))
                        pygame.draw.line(det, (92, 26, 22, 255), (px, py + 3), (px + TILE - 1, py + 3))
                        if dir_ != "R" and esq == "R":
                            # Chaminé de tijolos no canto superior direito do telhado
                            pygame.draw.rect(det, (92, 42, 36, 255), (px + 9, py - 2, 5, 6))
                            pygame.draw.rect(det, (138, 66, 54, 255), (px + 8, py - 2, 7, 2))
                            self.chamines.append((px + 11, py - 2))
                    if esq != "R":
                        pygame.draw.rect(det, (112, 58, 32, 255), (px, py, 2, TILE))
                        pygame.draw.line(det, (218, 128, 86, 255), (px + 1, py + 1), (px + 1, py + TILE - 1))
                    if dir_ != "R":
                        pygame.draw.rect(det, (112, 58, 32, 255), (px + TILE - 2, py, 2, TILE))
                        pygame.draw.line(det, (78, 22, 20, 255), (px + TILE - 1, py + 1), (px + TILE - 1, py + TILE - 1))
                    if baixo != "R":
                        pygame.draw.rect(det, (104, 30, 26, 255), (px, py + TILE - 2, TILE, 2))

                # 5a. Blocos temáticos dos covis: só ganham tochas/cristais combinando com o tema
                elif c == "#" and self.tema:
                    if baixo in (".", ",") and h_val < 18:
                        fogo = self.tema["nome"] in ("lava", "solar", "arena", "caverna", "ruinas", "coliseu", "areia")
                        self.tochas.append((px + TILE // 2, py + 10, "tocha" if fogo else "cristal"))
                # 5. Muralhas e falésias de pedra (#) com face 3D, musgo/trepadeiras e tochas/cristais
                elif c == "#":
                    if h_val % 4 == 0:
                        # Musgo ou runa ancestral na rocha
                        cor_musgo = (80, 210, 255, 150) if eh_sombrio else (54, 128, 56, 175)
                        pygame.draw.line(det, cor_musgo, (px + 4, py + 3), (px + 6, py + 8))
                        det.set_at((px + 5, py + 5), cor_musgo)
                    if baixo and baixo not in ("#", "T", "W"):
                        # Face frontal escura 3D na base da parede de pedra
                        pygame.draw.rect(det, (54, 58, 74, 255), (px + 1, py + 11, TILE - 2, 4))
                        pygame.draw.line(det, (36, 38, 50, 255), (px, py + 15), (px + TILE - 1, py + 15))
                        if h_val < 24 and baixo in (".", ","):
                            self.tochas.append((px + TILE // 2, py + 10, "cristal" if eh_sombrio else "tocha"))

                # 6. Micro-decorações naturais na grama (.) — cogumelos, pedrinhas, folhas de outono e postes
                elif c == "." and self.tema:
                    desenhar_decoracao(det, self.tema, px, py, h_val)
                elif c == "." and not self.eh_interior:
                    if (esq == "," or dir_ == ",") and cima == "." and h_val < 12:
                        # Poste de lanterna de madeira à beira da estrada
                        pygame.draw.rect(det, (82, 50, 28, 255), (px + 7, py + 3, 2, 11))
                        pygame.draw.rect(det, (112, 70, 38, 255), (px + 6, py + 2, 4, 2))
                        pygame.draw.rect(det, (255, 225, 115, 255), (px + 6, py + 4, 4, 3))
                        self.postes_luz.append((px + 8, py + 5))
                    elif h_val in (3, 27, 41):
                        # Cogumelo silvestre (vermelho com pintas ou ciano bioluminescente)
                        mx, my = px + 6 + (h_val % 4), py + 7 + (h_val % 3)
                        pygame.draw.rect(det, (235, 225, 200, 255), (mx, my, 2, 2))
                        cor_chapeu = (90, 235, 255, 255) if eh_sombrio else (228, 62, 62, 255)
                        pygame.draw.rect(det, cor_chapeu, (mx - 1, my - 2, 4, 2))
                        det.set_at((mx, my - 2), (255, 250, 240, 255))
                    elif h_val in (11, 29, 67, 88):
                        # Pedrinhas musgosas ou cristais de gelo/areia no chão
                        rx, ry = px + 4 + (h_val % 7), py + 5 + (h_val % 6)
                        cor_pedra = (180, 230, 255, 245) if self.bioma == "gelo" else (118, 124, 134, 245)
                        pygame.draw.rect(det, cor_pedra, (rx, ry, 3, 2))
                        det.set_at((rx, ry), (215, 225, 240, 245))
                        det.set_at((rx + 2, ry + 1), (64, 128, 62, 245))
                    elif h_val in (19, 35, 53, 74, 83):
                        # Florzinhas silvestres / folhas douradas
                        fx, fy = px + 3 + (h_val % 9), py + 4 + (h_val % 8)
                        cor_flor = (255, 145, 55, 245) if self.bioma == "outono" else (255, 225, 95, 240)
                        det.set_at((fx, fy), cor_flor)
                        det.set_at((fx + 1, fy), (255, 245, 200, 230))
                        det.set_at((fx + 1, fy + 1), (48, 114, 52, 240))

                # 7. Sombras projetadas no chão por objetos altos ao norte ou oeste (Octopath HD-2D)
                if c in (".", ",", "*", "_", "D"):
                    if cima in ("T", "#", "W", "R"):
                        alt_sombra = 5 if cima in ("T", "W", "R") else 4
                        pygame.draw.rect(det, (10, 16, 28, 62), (px, py, TILE, alt_sombra))
                    if esq in ("T", "#", "W", "R"):
                        pygame.draw.rect(det, (10, 16, 28, 44), (px, py, 4, TILE))
    def _desenhar_tile(self, cx, cy):
        if self.tema:
            self._desenhar_tile_tema(cx, cy)
            return
        c = self.grade[cy][cx]
        nome = SIMBOLOS.get(c)
        if c == "W" and self.eh_interior:
            img = self.gfx.tiles["parede_interna"]
        elif nome:
            img = self.gfx.tiles[nome]
        else:
            img = self.gfx.gramas[(cx * 7 + cy * 13 + (cx * cy) % 3) % len(self.gfx.gramas)]
        pos = (cx * TILE, cy * TILE)
        self.superficie.blit(img, pos)
        # Manchas grandes de sol e sombra para os campos não parecerem um tapete repetido
        if c in (".", "*", "T", "B") and not self.eh_interior:
            v = _ruido(cx / 6.0, cy / 6.0)
            if v > 0.62:
                self.superficie.blit(_mancha((255, 240, 150), round((v - 0.62) * 200)), pos)
            elif v < 0.38:
                self.superficie.blit(_mancha((8, 36, 28), round((0.38 - v) * 260)), pos)

    def _desenhar_tile_tema(self, cx, cy):
        c = self.grade[cy][cx]
        g = self.gfx_tema
        pos = (cx * TILE, cy * TILE)
        variante = (cx * 7 + cy * 13 + (cx * cy) % 5) % len(g.pisos)
        if c == "#":
            self.superficie.blit(g.bloco, pos)
        elif c == "W":
            self.superficie.blit(g.paredes[cy % 2], pos)
        elif c == "~":
            self.superficie.blit(g.liquido[0], pos)
        elif c == "D":
            self.superficie.blit(self.gfx.tiles["porta"], pos)
        else:
            self.superficie.blit(g.pisos[variante], pos)
            if c == ",":
                sombra = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
                sombra.fill((0, 0, 0, 50))
                self.superficie.blit(sombra, pos)

    def desenhar_cenario_vivo(self, tela, ox, oy, tempo):
        """Desenha o mapa com auto-tiling, sombras projetadas, água, vento e tochas/cristais."""
        tela.blit(self.superficie, (-ox, -oy))
        cx_ini = max(0, ox // TILE)
        cy_ini = max(0, oy // TILE)
        cx_fim = min(self.colunas, (ox + LARGURA) // TILE + 1)
        cy_fim = min(self.linhas, (oy + ALTURA) // TILE + 1)
        animados = self.gfx.tiles_animados
        gramas_vento = self.gfx.gramas_vento

        # 1. Camada base animada: água (~) e ondas de vento na grama (.)
        for cy in range(cy_ini, cy_fim):
            linha = self.grade[cy]
            sy = cy * TILE - oy
            for cx in range(cx_ini, cx_fim):
                c = linha[cx]
                sx = cx * TILE - ox
                if c == "~":
                    fase = int(tempo * 3.6 + (cx * 3 + cy * 5) * 0.25) % 4
                    quadros_liq = self.gfx_tema.liquido if self.tema else animados["~"]
                    tela.blit(quadros_liq[fase], (sx, sy))
                elif c == "." and not self.tema:
                    onda = math.sin(tempo * 2.6 - cx * 0.45 - cy * 0.25)
                    if onda > 0.55:
                        tela.blit(gramas_vento[(cx * 7 + cy * 13) % 4], (sx, sy))

        # 2. Camada de auto-tiling (margens, pontes, caminhos orgânicos, sombras 3D e flora)
        tela.blit(self.camada_detalhes, (0, 0), (ox, oy, LARGURA, ALTURA))

        # 3. Extrusão 3D em perspectiva real para paredes, ruínas e telhados (estilo Octopath Traveler)
        desenhar_relevo_3d_mapa(self, tela, ox, oy, tempo)

        # 4. Copa das árvores (T), arbustos (B) e flores (*) balançando ao vento + volume 3D das árvores
        for cy in range(cy_ini, cy_fim):
            linha = self.grade[cy]
            sy = cy * TILE - oy
            for cx in range(cx_ini, cx_fim):
                c = linha[cx]
                if c in ("*", "T", "B") and not self.tema:
                    sx = cx * TILE - ox
                    onda = math.sin(tempo * 2.6 - cx * 0.45 - cy * 0.25)
                    if onda > 0.45:
                        tela.blit(animados[c][2], (sx, sy))
                    elif onda < -0.58:
                        tela.blit(animados[c][0], (sx, sy))
        desenhar_copas_3d_arvores(self, tela, ox, oy, tempo)

        # 4. Tochas de parede, cachoeiras animadas, fumaça de chaminé e cristais arcanos
        fase_cach = int(tempo * 14.0)
        for wx, wy in self.cachoeiras:
            sx, sy = wx - ox, wy - oy
            if -TILE <= sx < LARGURA + TILE and -TILE <= sy < ALTURA + TILE:
                pygame.draw.rect(tela, (80, 175, 245), (sx + 2, sy, TILE - 4, TILE))
                for col in range(3, TILE - 3, 3):
                    dy = (fase_cach + col * 2) % 8
                    pygame.draw.line(tela, (215, 248, 255), (sx + col, sy + dy), (sx + col, sy + dy + 4))
                esp = (fase_cach % 3) - 1
                pygame.draw.line(tela, (235, 252, 255), (sx + 2, sy + TILE - 2 + esp), (sx + TILE - 3, sy + TILE - 2 + esp))

        for chx, chy in self.chamines:
            sx, sy = chx - ox, chy - oy
            if -16 <= sx < LARGURA + 16 and -16 <= sy < ALTURA + 16:
                for i in range(3):
                    prog = (tempo * 0.9 + i * 0.33) % 1.0
                    fx = round(sx + math.sin(tempo * 2.5 + i * 2.0) * (1.5 + prog * 3.0))
                    fy = round(sy - 2 - prog * 14.0)
                    raio = 1 if prog < 0.4 else 2
                    pygame.draw.circle(tela, (215, 220, 230), (fx, fy), raio)

        for tx, ty, tipo in self.tochas:
            sx, sy = tx - ox, ty - oy
            if -8 <= sx < LARGURA + 8 and -8 <= sy < ALTURA + 8:
                if tipo == "cristal":
                    pulso = 1 if math.sin(tempo * 6.0 + tx) > 0 else 0
                    pygame.draw.polygon(
                        tela,
                        (70, 210, 255),
                        [(sx, sy - 4 - pulso), (sx - 2, sy), (sx, sy + 2), (sx + 2, sy)],
                    )
                    tela.set_at((sx, sy - 2), (225, 255, 255))
                else:
                    pygame.draw.rect(tela, (72, 44, 26), (sx - 1, sy, 2, 4))
                    osc = round(math.sin(tempo * 15.0 + tx) * 0.8)
                    pygame.draw.rect(tela, (255, 130, 30), (sx - 1 + osc, sy - 3, 2, 3))
                    tela.set_at((sx + osc, sy - 2), (255, 240, 150))

        # 5. Altares e Cristais de Salvamento (Save Points)
        for psx, psy in getattr(self, "pontos_salvamento", []):
            sx, sy = psx - ox, psy - oy
            if -32 <= sx < LARGURA + 32 and -32 <= sy < ALTURA + 32:
                # Círculo rúnico celestial no solo
                raio_runa = 11 + round(math.sin(tempo * 4.0) * 1.5)
                pygame.draw.ellipse(tela, (255, 215, 80), (sx - raio_runa, sy + 3, raio_runa * 2, 7), 1)
                pygame.draw.ellipse(tela, (110, 220, 255), (sx - raio_runa + 2, sy + 4, (raio_runa - 2) * 2, 5), 1)
                # Pedestal de pedra/mármore
                pygame.draw.rect(tela, (65, 55, 75), (sx - 6, sy - 2, 12, 6))
                pygame.draw.rect(tela, (215, 185, 75), (sx - 7, sy - 4, 14, 2))
                # Cristal 3D flutuante giratório
                flutua = math.sin(tempo * 3.5) * 2.5
                cristal_save = criar_cristal_3d(sx, sy - 10 + flutua, z_base=4.0, raio=4.5, altura=7.5, cor=(255, 235, 110), cor_borda=(180, 130, 40))
                cristal_save.atualizar(tempo * 1.8)
                cristal_save.desenhar(tela, 0, 0, tempo)

    def _celulas(self, rect):
        for cy in range(rect.top // TILE, (rect.bottom - 1) // TILE + 1):
            for cx in range(rect.left // TILE, (rect.right - 1) // TILE + 1):
                yield cx, cy

    def dentro(self, cx, cy):
        return 0 <= cx < self.colunas and 0 <= cy < self.linhas

    def eh_agua_em(self, x, y):
        if self.tema and not self.tema["nadavel"]:
            return False
        cx, cy = int(x) // TILE, int(y) // TILE
        return self.dentro(cx, cy) and self.grade[cy][cx] == "~"

    def solido(self, cx, cy, pode_nadar=False):
        if not self.dentro(cx, cy):
            return True
        nadavel = not self.tema or self.tema["nadavel"]
        bloqueios = SOLIDOS_TERRA if (pode_nadar and nadavel) else SOLIDOS
        return self.grade[cy][cx] in bloqueios

    def colisoes(self, rect, pode_nadar=False):
        """Retângulos sólidos (tiles e obstáculos) que encostam em `rect`."""
        blocos = [
            pygame.Rect(cx * TILE, cy * TILE, TILE, TILE)
            for cx, cy in self._celulas(rect)
            if self.solido(cx, cy, pode_nadar=pode_nadar)
        ]
        return blocos + [o for o in self.obstaculos if o is not rect and o.colliderect(rect)]

    def cortar_arbustos(self, rect):
        """Remove arbustos atingidos pela espada. Devolve o centro de cada um."""
        cortados = []
        for cx, cy in self._celulas(rect):
            if self.dentro(cx, cy) and self.grade[cy][cx] == "B":
                self.grade[cy][cx] = "."
                self._desenhar_tile(cx, cy)
                cortados.append((cx * TILE + TILE // 2, cy * TILE + TILE // 2))
        return cortados
