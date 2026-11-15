"""Motor de elementos 3D em tempo real: malhas poligonais 3D, iluminação por normais e extrusão em perspectiva HD-2D."""
import math

import pygame

from settings import ALTURA, LARGURA, TILE

CENTRO_TELA_X = LARGURA * 0.5
CENTRO_TELA_Y = ALTURA * 0.5
FOCO_PERSPECTIVA = 260.0

# Direção da luz solar / principal normalizada (vindo da esquerda-cima-frente)
LUZ_DIR = (-0.45, -0.55, 0.70)


def _rotacionar_ponto(x, y, z, rx, ry, rz):
    """Aplica rotações 3D nos eixos X, Y e Z."""
    if ry:
        cy, sy = math.cos(ry), math.sin(ry)
        x, z = x * cy + z * sy, -x * sy + z * cy
    if rx:
        cx, sx = math.cos(rx), math.sin(rx)
        y, z = y * cx - z * sx, y * sx + z * cx
    if rz:
        cz, sz = math.cos(rz), math.sin(rz)
        x, y = x * cz - y * sz, x * sz + y * cz
    return x, y, z


def projetar_ponto_3d(x_tela, y_tela, z_altura):
    """Projeta um ponto com altura `z_altura` acima do chão usando perspectiva real a partir do centro da câmera."""
    fator = z_altura / FOCO_PERSPECTIVA
    px = x_tela + (x_tela - CENTRO_TELA_X) * fator
    py = y_tela - z_altura + (y_tela - CENTRO_TELA_Y) * (fator * 0.55)
    return px, py


def _normal_face(p0, p1, p2):
    ux, uy, uz = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]
    vx, vy, vz = p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2]
    nx = uy * vz - uz * vy
    ny = uz * vx - ux * vz
    nz = ux * vy - uy * vx
    comp = math.sqrt(nx * nx + ny * ny + nz * nz)
    if comp <= 1e-6:
        return 0.0, 0.0, 1.0
    return nx / comp, ny / comp, nz / comp


def _sombrear_cor(cor, intensidade, brilho_especular=0.0):
    r, g, b = cor
    r = min(255, max(0, int(r * intensidade + brilho_especular * 180)))
    g = min(255, max(0, int(g * intensidade + brilho_especular * 195)))
    b = min(255, max(0, int(b * intensidade + brilho_especular * 220)))
    return r, g, b


class Objeto3D:
    """Objeto poligonal 3D posicionado no mundo (cristal, obelisco, coroa rúnica)."""

    def __init__(self, x, y, z_base, vertices, faces, tipo="cristal", cor_luz=(110, 230, 255)):
        self.x = float(x)
        self.y = float(y)
        self.z_base = float(z_base)
        self.vertices = vertices
        self.faces = faces  # [(indices, cor_base, contorno)]
        self.tipo = tipo
        self.cor_luz = cor_luz
        self.rx = 0.0
        self.ry = 0.0
        self.rz = 0.0
        self.fase = (x * 0.13 + y * 0.29) % math.tau

    @property
    def y_ord(self):
        """Coordenada Y na base para ordenação de profundidade (Y-sorting) com personagens."""
        return self.y

    def atualizar(self, tempo):
        if self.tipo == "cristal":
            self.ry = tempo * 1.85 + self.fase
            self.rx = math.sin(tempo * 1.4 + self.fase) * 0.22
        elif self.tipo == "anel_cristal":
            self.ry = -tempo * 2.4 + self.fase
            self.rx = 0.35 + math.sin(tempo * 1.8 + self.fase) * 0.15
        elif self.tipo == "obelisco":
            # Obeliscos são monumentos fixos, mas seu cristal no topo pulsa
            self.ry = 0.28

    def desenhar(self, tela, ox, oy, tempo):
        sx_base = self.x - ox
        sy_base = self.y - oy
        if sx_base < -36 or sx_base > LARGURA + 36 or sy_base < -36 or sy_base > ALTURA + 48:
            return

        flutuacao = math.sin(tempo * 2.8 + self.fase) * 2.8 if self.tipo != "obelisco" else 0.0
        z_centro = self.z_base + flutuacao

        # Sombra projetada no chão abaixo do objeto 3D
        raio_sombra = 6 if self.tipo == "cristal" else 8
        sombra = pygame.Surface((raio_sombra * 2 + 4, 6), pygame.SRCALPHA)
        pygame.draw.ellipse(sombra, (8, 12, 24, 95), sombra.get_rect())
        tela.blit(sombra, (round(sx_base) - raio_sombra - 2, round(sy_base) - 3))

        # Transforma os vértices no espaço 3D e projeta para a tela
        v_rot = []
        v_proj = []
        for vx, vy, vz in self.vertices:
            rx, ry, rz = _rotacionar_ponto(vx, vy, vz, self.rx, self.ry, self.rz)
            # No nosso espaço: rx = esquerda/direita, ry = altura acima da base, rz = profundidade (frente/trás)
            mundo_x = sx_base + rx
            mundo_y = sy_base - rz * 0.55
            altura_z = z_centro + ry
            px, py = projetar_ponto_3d(mundo_x, mundo_y, altura_z)
            v_rot.append((rx, -ry, rz))
            v_proj.append((px, py))

        # Calcula profundidade e iluminação de cada face (Algoritmo do Pintor + Sombreamento Lambertiano/Especular)
        faces_ordenadas = []
        for indices, cor_base, cor_borda in self.faces:
            p0, p1, p2 = v_rot[indices[0]], v_rot[indices[1]], v_rot[indices[2]]
            nx, ny, nz = _normal_face(p0, p1, p2)
            # Backface culling suave (descarta faces totalmente viradas para trás em malhas fechadas)
            if nz < -0.35 and self.tipo != "anel_cristal":
                continue
            z_medio = sum(v_rot[i][2] for i in indices) / len(indices)
            dot_luz = max(0.0, nx * LUZ_DIR[0] + ny * LUZ_DIR[1] + nz * LUZ_DIR[2])
            intensidade = 0.52 + dot_luz * 0.68
            especular = (dot_luz ** 5) * 0.55 if self.tipo != "obelisco" else (dot_luz ** 6) * 0.18
            cor_final = _sombrear_cor(cor_base, intensidade, especular)
            pts_2d = [(round(v_proj[i][0]), round(v_proj[i][1])) for i in indices]
            faces_ordenadas.append((z_medio, pts_2d, cor_final, cor_borda))

        faces_ordenadas.sort(key=lambda item: item[0])
        for _, pts_2d, cor_final, cor_borda in faces_ordenadas:
            pygame.draw.polygon(tela, cor_final, pts_2d)
            if cor_borda:
                pygame.draw.polygon(tela, cor_borda, pts_2d, 1)

        # Halo luminoso e partículas orbitando cristais 3D
        if self.tipo in ("cristal", "anel_cristal"):
            cx_proj, cy_proj = projetar_ponto_3d(sx_base, sy_base, z_centro)
            raio_halo = round(14 + math.sin(tempo * 5.0 + self.fase) * 2)
            halo = pygame.Surface((raio_halo * 2, raio_halo * 2), pygame.SRCALPHA)
            pygame.draw.circle(halo, (*self.cor_luz, 38), (raio_halo, raio_halo), raio_halo)
            pygame.draw.circle(halo, (255, 255, 255, 55), (raio_halo, raio_halo), max(3, raio_halo // 3))
            tela.blit(halo, (round(cx_proj) - raio_halo, round(cy_proj) - raio_halo))

            # Partículas orbitando em 3D ao redor do cristal
            for i in range(3):
                ang = tempo * 2.6 + self.fase + i * (math.tau / 3)
                ox_p = math.cos(ang) * 7.5
                oz_p = math.sin(ang) * 7.5
                oy_p = math.sin(tempo * 4.0 + i) * 3.0
                px_orb, py_orb = projetar_ponto_3d(sx_base + ox_p, sy_base - oz_p * 0.5, z_centro + oy_p)
                if 0 <= round(px_orb) < LARGURA and 0 <= round(py_orb) < ALTURA:
                    tela.set_at((round(px_orb), round(py_orb)), (240, 255, 255))


def criar_cristal_3d(x, y, z_base=11.0, raio=4.5, altura=8.5, cor=(85, 215, 255), cor_borda=(30, 95, 145)):
    """Cria um cristal octaedro 3D lapidado que gira no espaço."""
    vertices = [
        (0.0, altura, 0.0),      # 0: topo da pirâmide
        (0.0, -altura, 0.0),     # 1: ponta inferior
        (-raio, 0.0, raio),      # 2: frente-esquerda
        (raio, 0.0, raio),       # 3: frente-direita
        (raio, 0.0, -raio),      # 4: trás-direita
        (-raio, 0.0, -raio),     # 5: trás-esquerda
    ]
    faces = [
        ((0, 2, 3), cor, cor_borda),
        ((0, 3, 4), cor, cor_borda),
        ((0, 4, 5), cor, cor_borda),
        ((0, 5, 2), cor, cor_borda),
        ((1, 3, 2), cor, cor_borda),
        ((1, 4, 3), cor, cor_borda),
        ((1, 5, 4), cor, cor_borda),
        ((1, 2, 5), cor, cor_borda),
    ]
    return Objeto3D(x, y, z_base, vertices, faces, tipo="cristal", cor_luz=cor)


def criar_obelisco_3d(x, y, cor=(130, 136, 156), cor_topo=(255, 215, 110)):
    """Cria um obelisco/pilar monolítico 3D com ponta piramidal dourada/arcana."""
    rb = 4.5  # raio da base
    rt = 3.2  # raio do topo do corpo
    h_corpo = 14.0
    h_ponta = 20.0
    vertices = [
        # Base (y = 0)
        (-rb, 0.0, rb), (rb, 0.0, rb), (rb, 0.0, -rb), (-rb, 0.0, -rb),
        # Topo do pilar (y = h_corpo)
        (-rt, h_corpo, rt), (rt, h_corpo, rt), (rt, h_corpo, -rt), (-rt, h_corpo, -rt),
        # Ápice da pirâmide (y = h_ponta)
        (0.0, h_ponta, 0.0),
    ]
    borda = (46, 48, 64)
    borda_topo = (140, 95, 35)
    faces = [
        # Faces laterais do pilar
        ((0, 1, 5, 4), cor, borda),
        ((1, 2, 6, 5), cor, borda),
        ((2, 3, 7, 6), cor, borda),
        ((3, 0, 4, 7), cor, borda),
        # Ponta piramidal
        ((8, 4, 5), cor_topo, borda_topo),
        ((8, 5, 6), cor_topo, borda_topo),
        ((8, 6, 7), cor_topo, borda_topo),
        ((8, 7, 4), cor_topo, borda_topo),
    ]
    return Objeto3D(x, y, 0.0, vertices, faces, tipo="obelisco", cor_luz=cor_topo)


def desenhar_relevo_3d_mapa(nivel, tela, ox, oy, tempo):
    """Desenha extrusão 3D com perspectiva real (estilo Octopath Traveler) para paredes, ruínas e telhados."""
    cx_ini = max(0, ox // TILE - 1)
    cy_ini = max(0, oy // TILE - 1)
    cx_fim = min(nivel.colunas, (ox + LARGURA) // TILE + 2)
    cy_fim = min(nivel.linhas, (oy + ALTURA) // TILE + 2)

    # Percorre da borda mais afastada do centro da tela para a mais próxima (ordem do pintor em perspectiva)
    celulas = []
    for cy in range(cy_ini, cy_fim):
        linha = nivel.grade[cy]
        for cx in range(cx_ini, cx_fim):
            c = linha[cx]
            if c == "#":
                sx = cx * TILE - ox + TILE * 0.5
                sy = cy * TILE - oy + TILE * 0.5
                dist = abs(sx - CENTRO_TELA_X) + abs(sy - CENTRO_TELA_Y) * 1.4
                celulas.append((dist, cx, cy, c))

    celulas.sort(key=lambda item: item[0], reverse=True)
    _ = tempo

    for _, cx, cy, c in celulas:
        x0 = cx * TILE - ox
        y0 = cy * TILE - oy
        x1 = x0 + TILE
        y1 = y0 + TILE

        tema = getattr(nivel, "tema", None)
        if c == "#" and tema:
            z_alt = 9.0
            cor_topo, cor_esq, cor_dir, cor_frente, cor_borda = tema["bloco"]
        elif c == "#":
            z_alt = 7.0
            cor_esq = (92, 98, 114)
            cor_dir = (68, 72, 88)
            cor_frente = (58, 62, 78)
            cor_topo = (134, 140, 158)
            cor_borda = (42, 44, 58)
        elif c == "W":
            z_alt = 8.0
            cor_esq = (108, 72, 44)
            cor_dir = (78, 50, 30)
            cor_frente = (88, 56, 34)
            cor_topo = (138, 94, 58)
            cor_borda = (48, 30, 18)
        else:  # "R" (Telhado elevado em 3D)
            z_alt = 11.0
            cor_esq = (158, 52, 42)
            cor_dir = (118, 36, 30)
            cor_frente = (128, 40, 34)
            cor_topo = (192, 72, 58)
            cor_borda = (78, 22, 20)

        # Vértices do topo deslocados pela perspectiva real da câmera
        t00 = projetar_ponto_3d(x0, y0, z_alt)
        t10 = projetar_ponto_3d(x1, y0, z_alt)
        t11 = projetar_ponto_3d(x1, y1, z_alt)
        t01 = projetar_ponto_3d(x0, y1, z_alt)

        p_t00 = (round(t00[0]), round(t00[1]))
        p_t10 = (round(t10[0]), round(t10[1]))
        p_t11 = (round(t11[0]), round(t11[1]))
        p_t01 = (round(t01[0]), round(t01[1]))

        esq_livre = nivel._simbolo_em(cx - 1, cy) != c
        dir_livre = nivel._simbolo_em(cx + 1, cy) != c
        baixo_livre = nivel._simbolo_em(cx, cy + 1) != c

        # Parede lateral esquerda visível quando o bloco está à direita do centro da tela
        if esq_livre and p_t00[0] > x0:
            pygame.draw.polygon(tela, cor_esq, [(x0, y0), p_t00, p_t01, (x0, y1)])
            pygame.draw.line(tela, cor_borda, (x0, y0), p_t00)
            pygame.draw.line(tela, cor_borda, (x0, y1), p_t01)

        # Parede lateral direita visível quando o bloco está à esquerda do centro da tela
        if dir_livre and p_t10[0] < x1:
            pygame.draw.polygon(tela, cor_dir, [(x1, y0), p_t10, p_t11, (x1, y1)])
            pygame.draw.line(tela, cor_borda, (x1, y0), p_t10)
            pygame.draw.line(tela, cor_borda, (x1, y1), p_t11)

        # Parede frontal 3D conectando a base ao topo elevado
        if baixo_livre and p_t01[1] < y1:
            pygame.draw.polygon(tela, cor_frente, [(x0, y1), (x1, y1), p_t11, p_t01])
            pygame.draw.line(tela, cor_borda, (x0, y1), (x1, y1))

        # Face superior em perspectiva 3D
        if c == "#" and tema:
            surf_tile = nivel.gfx_tema.bloco
        else:
            surf_tile = nivel.gfx.tiles["pedra" if c == "#" else ("parede" if c == "W" else "telhado")]
        pygame.draw.polygon(tela, cor_topo, [p_t00, p_t10, p_t11, p_t01])
        tela.blit(surf_tile, p_t00)
        if esq_livre:
            pygame.draw.line(tela, cor_borda, p_t00, p_t01)
        if dir_livre:
            pygame.draw.line(tela, cor_borda, p_t10, p_t11)
        if baixo_livre:
            cor_quina = tuple(min(255, v + 50) for v in cor_topo) if tema else (215, 220, 235)
            pygame.draw.line(tela, cor_quina if c == "#" else cor_borda, p_t01, p_t11)


_COPAS = []


def _gerar_copas():
    """Três variações de copa (carvalho redondo, árvore frutífera e pinheiro) em pixel art."""
    import random as _r
    copas = []
    for variante in range(3):
        rng = _r.Random(variante * 17 + 3)
        s = pygame.Surface((24, 24), pygame.SRCALPHA)
        if variante == 2:
            # Pinheiro: três camadas triangulares
            for i, (larg, y) in enumerate(((20, 14), (16, 9), (10, 4))):
                pts = [(12 - larg // 2, y + 8), (12 + larg // 2, y + 8), (12, y - 2)]
                pygame.draw.polygon(s, (20, 66, 46), pts)
                pygame.draw.polygon(s, (36, 104, 62), [(12 - larg // 2 + 2, y + 7), (12, y + 7), (12, y)])
                pygame.draw.polygon(s, (58, 132, 72), [(12, y + 7), (12 + larg // 2 - 2, y + 7), (12, y)])
                pygame.draw.line(s, (120, 188, 104), (12 - larg // 2 + 3, y + 6), (12 - 1, y + 1))
        else:
            cachos = [(12, 13, 9), (7, 11, 6), (17, 11, 6), (12, 7, 7), (8, 15, 5), (16, 15, 5)]
            for cx, cy, r in cachos:
                pygame.draw.circle(s, (20, 58, 38), (cx, cy), r + 1)
            for cx, cy, r in cachos:
                pygame.draw.circle(s, (40, 110, 54), (cx, cy), r)
            for cx, cy, r in cachos:
                pygame.draw.circle(s, (74, 152, 66), (cx - 1, cy - 2), max(1, r - 3))
            for _ in range(10):
                x, y = rng.randrange(5, 19), rng.randrange(3, 14)
                if s.get_at((x, y)).a:
                    s.set_at((x, y), (150, 212, 98))
            # Sombra interna na base da copa (volume)
            for x in range(4, 21):
                for y in range(16, 22):
                    c = s.get_at((x, y))
                    if c.a and c[:3] != (20, 58, 38):
                        s.set_at((x, y), (30, 86, 48))
            if variante == 1:
                for fx, fy in ((8, 9), (15, 7), (17, 14), (10, 16)):
                    s.set_at((fx, fy), (236, 72, 70))
                    s.set_at((fx, fy - 1), (255, 170, 160))
        copas.append(s)
    return copas


def desenhar_copas_3d_arvores(nivel, tela, ox, oy, tempo):
    """Desenha a copa volumosa das árvores elevada em perspectiva 3D, balançando ao vento."""
    if not _COPAS:
        _COPAS.extend(_gerar_copas())
    cx_ini = max(0, ox // TILE - 1)
    cy_ini = max(0, oy // TILE - 1)
    cx_fim = min(nivel.colunas, (ox + LARGURA) // TILE + 2)
    cy_fim = min(nivel.linhas, (oy + ALTURA) // TILE + 2)

    for cy in range(cy_ini, cy_fim):
        linha = nivel.grade[cy]
        for cx in range(cx_ini, cx_fim):
            if linha[cx] != "T":
                continue
            sx = cx * TILE - ox + 8
            sy = cy * TILE - oy + 4
            vento = math.sin(tempo * 2.6 - cx * 0.45 - cy * 0.25) * 1.2
            px, py = projetar_ponto_3d(sx + vento, sy, 6.5)
            sorteio = (cx * 7 + cy * 13) % 10
            copa = _COPAS[2 if sorteio < 2 else (1 if sorteio < 4 else 0)]
            tela.blit(copa, (round(px) - 12, round(py) - 14))


def gerar_objetos_3d_nivel(nivel):
    """Cria cristais 3D giratórios e obeliscos 3D de acordo com os pontos notáveis do mapa."""
    objetos = []
    if nivel.eh_interior:
        return objetos

    nome_arq = nivel.caminho.stem.lower()
    eh_sombrio = nivel.clima_padrao in ("trevas", "noite") or "santuario" in nome_arq

    # 1. Cristais 3D flutuando sobre altares/mesas externas (ex.: Santuário Sombrio e Vila)
    for i, (mx, my) in enumerate(nivel.mesas):
        cor = (195, 75, 255) if eh_sombrio else ((85, 220, 255) if i % 2 == 0 else (255, 215, 90))
        borda = (75, 20, 120) if eh_sombrio else (25, 90, 135)
        objetos.append(criar_cristal_3d(mx, my - 2, z_base=12.0, raio=4.2, altura=7.5, cor=cor, cor_borda=borda))

    # Covis temáticos usam só a própria decoração (sem objetos genéricos da floresta)
    if getattr(nivel, "tema", None):
        return objetos

    # 2. Cristais de Mana 3D e Obeliscos 3D específicos de cada região
    if "santuario" in nome_arq:
        # Grande Cristal Arcano central no Santuário + 2 Obeliscos guardiões
        cx_meio = (nivel.colunas // 2) * TILE
        objetos.append(
            criar_cristal_3d(
                cx_meio, 10 * TILE, z_base=15.0, raio=6.0, altura=11.0,
                cor=(220, 65, 195), cor_borda=(90, 15, 95)
            )
        )
        objetos.append(criar_obelisco_3d(cx_meio - 3 * TILE, 12 * TILE, cor=(95, 88, 120), cor_topo=(215, 75, 245)))
        objetos.append(criar_obelisco_3d(cx_meio + 3 * TILE, 12 * TILE, cor=(95, 88, 120), cor_topo=(215, 75, 245)))
    elif "lago" in nome_arq:
        # Cristal de Água 3D na ilha central e perto do Mago das Águas
        objetos.append(
            criar_cristal_3d(
                8 * TILE + 8, 5 * TILE + 8, z_base=13.0, raio=5.0, altura=9.5,
                cor=(75, 220, 255), cor_borda=(20, 95, 150)
            )
        )
        objetos.append(
            criar_cristal_3d(
                24 * TILE + 8, 4 * TILE + 8, z_base=12.0, raio=4.2, altura=8.0,
                cor=(120, 245, 220), cor_borda=(30, 115, 110)
            )
        )
    elif "ruinas" in nome_arq:
        # Obeliscos antigos 3D e Cristal de Relíquia Dourado nas Ruínas
        objetos.append(criar_obelisco_3d(19 * TILE + 8, 6 * TILE + 8, cor=(128, 132, 148), cor_topo=(255, 215, 95)))
        objetos.append(criar_obelisco_3d(25 * TILE + 8, 6 * TILE + 8, cor=(128, 132, 148), cor_topo=(255, 215, 95)))
        objetos.append(
            criar_cristal_3d(
                22 * TILE, 11 * TILE, z_base=13.0, raio=4.8, altura=9.0,
                cor=(255, 215, 85), cor_borda=(140, 85, 20)
            )
        )
    elif "vila" in nome_arq:
        # Obeliscos nas pontes da Vila Aurora
        objetos.append(criar_obelisco_3d(10 * TILE + 8, 11 * TILE + 8, cor=(142, 138, 152), cor_topo=(110, 225, 255)))
        objetos.append(criar_obelisco_3d(33 * TILE + 8, 11 * TILE + 8, cor=(142, 138, 152), cor_topo=(110, 225, 255)))
    elif "montanha" in nome_arq:
        # Cristais de Vento 3D e Obeliscos do Pico
        cx_meio = (nivel.colunas // 2) * TILE
        objetos.append(
            criar_cristal_3d(
                cx_meio, 10 * TILE, z_base=14.0, raio=5.0, altura=9.5,
                cor=(145, 255, 220), cor_borda=(30, 120, 105)
            )
        )
        objetos.append(criar_obelisco_3d(cx_meio - 3 * TILE, 16 * TILE, cor=(130, 140, 160), cor_topo=(145, 255, 220)))
        objetos.append(criar_obelisco_3d(cx_meio + 3 * TILE, 16 * TILE, cor=(130, 140, 160), cor_topo=(145, 255, 220)))
    elif "pantano" in nome_arq:
        # Cristais Bioluminescentes 3D no Pântano Nebuloso
        objetos.append(
            criar_cristal_3d(
                22 * TILE + 8, 13 * TILE + 8, z_base=12.5, raio=4.6, altura=8.5,
                cor=(95, 250, 175), cor_borda=(20, 110, 75)
            )
        )
        objetos.append(criar_obelisco_3d(16 * TILE + 8, 7 * TILE + 8, cor=(95, 115, 105), cor_topo=(95, 250, 175)))
        objetos.append(criar_obelisco_3d(28 * TILE + 8, 7 * TILE + 8, cor=(95, 115, 105), cor_topo=(95, 250, 175)))
    elif "deserto" in nome_arq:
        # Cristal Solar 3D no centro do Oásis Dourado e Obeliscos do Deserto
        objetos.append(
            criar_cristal_3d(
                23 * TILE, 9 * TILE, z_base=14.0, raio=5.2, altura=9.8,
                cor=(255, 210, 70), cor_borda=(150, 85, 20)
            )
        )
        objetos.append(criar_obelisco_3d(12 * TILE + 8, 6 * TILE + 8, cor=(185, 155, 105), cor_topo=(255, 215, 80)))
        objetos.append(criar_obelisco_3d(34 * TILE + 8, 6 * TILE + 8, cor=(185, 155, 105), cor_topo=(255, 215, 80)))
    elif "castelo" in nome_arq:
        # Grande Núcleo Abissal 3D e Obeliscos Negros na Cidadela Abissal
        cx_meio = (nivel.colunas // 2) * TILE
        objetos.append(
            criar_cristal_3d(
                cx_meio, 9 * TILE, z_base=16.0, raio=6.5, altura=12.0,
                cor=(255, 55, 105), cor_borda=(110, 10, 45)
            )
        )
        objetos.append(criar_obelisco_3d(cx_meio - 3 * TILE, 11 * TILE, cor=(75, 65, 95), cor_topo=(255, 55, 105)))
        objetos.append(criar_obelisco_3d(cx_meio + 3 * TILE, 11 * TILE, cor=(75, 65, 95), cor_topo=(255, 55, 105)))
    else:
        # Floresta Esmeralda (mundo.txt): Cristal de Mana perto do Sábio e Obelisco nas ruínas da floresta
        objetos.append(
            criar_cristal_3d(
                9 * TILE + 8, 13 * TILE + 8, z_base=12.5, raio=4.4, altura=8.2,
                cor=(110, 240, 150), cor_borda=(25, 110, 65)
            )
        )
        objetos.append(criar_obelisco_3d(21 * TILE + 8, 9 * TILE + 8, cor=(128, 132, 148), cor_topo=(255, 215, 95)))

    return objetos
