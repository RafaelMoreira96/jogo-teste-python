"""Itens coletáveis, partículas e vida ambiental do cenário."""
import math
import random

import pygame

from settings import ALTURA, LARGURA, TILE
from ui import desenhar_painel, desenhar_texto


class Coracao:
    """Coração no chão: item proporcional com brilho e sombra que recupera 1 coração inteiro."""

    def __init__(self, centro):
        self.rect = pygame.Rect(0, 0, 12, 10)
        self.rect.center = centro
        self.t = random.random() * 6

    def atualizar(self, dt):
        self.t += dt

    def desenhar(self, tela, camera, gfx):
        # Sombra no solo
        sombra = pygame.Surface((10, 4), pygame.SRCALPHA)
        pygame.draw.ellipse(sombra, (0, 0, 0, 70), sombra.get_rect())
        tela.blit(sombra, camera.aplicar_pos((self.rect.centerx - 5, self.rect.bottom - 2)))

        flutuar = round(math.sin(self.t * 5.0) * 1.5)
        img = getattr(gfx, "item_coracao", gfx.coracao_cheio)
        tela.blit(img, camera.aplicar(self.rect).move(-1, flutuar - 1))


class Particula:
    def __init__(self, pos, cor):
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(1, 0).rotate(random.uniform(0, 360)) * random.uniform(30, 90)
        self.vida = random.uniform(0.3, 0.6)
        self.cor = cor

    def atualizar(self, dt):
        self.pos += self.vel * dt
        self.vel *= 0.02**dt  # vai freando
        self.vida -= dt
        return self.vida > 0

    def desenhar(self, tela, camera):
        ox, oy = camera.offset
        tela.fill(self.cor, (round(self.pos.x) - ox, round(self.pos.y) - oy, 2, 2))


def explosao(centro, cores, quantidade=8):
    return [Particula(centro, random.choice(cores)) for _ in range(quantidade)]


CORES_BORBOLETA = [
    (255, 225, 85),
    (120, 215, 255),
    (255, 145, 195),
    (255, 175, 80),
]

CORES_FOLHA_VENTO = [
    (70, 156, 62),
    (110, 190, 90),
    (165, 205, 85),
    (230, 180, 75),
]


class AmbienteVivo:
    """Animações contínuas de cenário: vento, folhas, borboletas, nuvens, vagalumes, raios de sol e vinheta HD-2D."""

    _vinheta_cache = None

    def __init__(self, nivel):
        self.tempo = 0.0
        if AmbienteVivo._vinheta_cache is None:
            AmbienteVivo._vinheta_cache = self._criar_vinheta()
        self.vinheta = AmbienteVivo._vinheta_cache
        self.configurar(nivel)

    @staticmethod
    def _criar_vinheta():
        """Vinheta cinematográfica suave estilo Octopath Traveler (escurece bordas e cantos)."""
        surf = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        # Bandas suaves de profundidade de campo no topo e na base
        for i in range(18):
            alfa_topo = int(((18 - i) / 18) ** 1.8 * 48)
            alfa_base = int(((18 - i) / 18) ** 1.8 * 56)
            pygame.draw.line(surf, (8, 10, 22, alfa_topo), (0, i), (LARGURA - 1, i))
            pygame.draw.line(surf, (8, 10, 22, alfa_base), (0, ALTURA - 1 - i), (LARGURA - 1, ALTURA - 1 - i))
        for i in range(14):
            alfa_lat = int(((14 - i) / 14) ** 1.8 * 38)
            pygame.draw.line(surf, (8, 10, 22, alfa_lat), (i, 0), (i, ALTURA - 1))
            pygame.draw.line(surf, (8, 10, 22, alfa_lat), (LARGURA - 1 - i, 0), (LARGURA - 1 - i, ALTURA - 1))
        return surf

    def configurar(self, nivel):
        self.nivel = nivel
        self.eh_interior = getattr(nivel, "eh_interior", False)
        rng = random.Random(42)

        self.borboletas = []
        self.folhas = []
        self.nuvens = []
        self.vagalumes = []
        self.poeira = []

        if self.eh_interior:
            # Poeira dourada flutuando suavemente no ar da casinha
            for _ in range(18):
                self.poeira.append({
                    "x": rng.uniform(16, max(32, nivel.largura_px - 16)),
                    "y": rng.uniform(16, max(32, nivel.altura_px - 16)),
                    "vx": rng.uniform(-3.5, 3.5),
                    "vy": rng.uniform(-5.0, -1.5),
                    "fase": rng.uniform(0, math.tau),
                })
        else:
            # Borboletas voando perto dos canteiros de flores
            flores = getattr(nivel, "flores_pos", [])
            locais = flores[:] if flores else [(nivel.largura_px // 2, nivel.altura_px // 2)]
            rng.shuffle(locais)
            for cx, cy in locais[: min(10, len(locais))]:
                self.borboletas.append({
                    "ancora_x": float(cx),
                    "ancora_y": float(cy),
                    "x": float(cx),
                    "y": float(cy),
                    "raio_x": rng.uniform(10.0, 24.0),
                    "raio_y": rng.uniform(7.0, 16.0),
                    "vel": rng.uniform(1.1, 1.9),
                    "fase": rng.uniform(0, math.tau),
                    "cor": rng.choice(CORES_BORBOLETA),
                })

            # Folhas e pólen soprados pelo vento (em coordenadas da câmera para cobrir a tela toda)
            for _ in range(16):
                eh_polen = rng.random() < 0.38
                self.folhas.append({
                    "x": rng.uniform(0, LARGURA),
                    "y": rng.uniform(0, ALTURA),
                    "vx": rng.uniform(14.0, 28.0),
                    "vy": rng.uniform(5.0, 13.0),
                    "fase": rng.uniform(0, math.tau),
                    "polen": eh_polen,
                    "cor": (255, 245, 165) if eh_polen else rng.choice(CORES_FOLHA_VENTO),
                })

            # Sombras suaves de nuvens passando pelo chão do mapa
            qtd_nuvens = max(3, (nivel.largura_px * nivel.altura_px) // 28000)
            for _ in range(qtd_nuvens):
                self.nuvens.append({
                    "x": rng.uniform(-60, nivel.largura_px),
                    "y": rng.uniform(0, nivel.altura_px - 40),
                    "larg": rng.randint(68, 120),
                    "alt": rng.randint(28, 48),
                    "vel": rng.uniform(7.0, 13.0),
                })

            if getattr(nivel, "tema", None):
                # Covis temáticos têm partículas próprias (temas.py): sem folhas, nuvens e borboletas
                self.borboletas, self.folhas, self.nuvens = [], [], []
                return

            # Vagalumes / espíritos da floresta (brilham à noite ou nas sombras)
            for _ in range(18):
                self.vagalumes.append({
                    "x": rng.uniform(24, max(48, nivel.largura_px - 24)),
                    "y": rng.uniform(24, max(48, nivel.altura_px - 24)),
                    "vx": rng.uniform(-9.0, 9.0),
                    "vy": rng.uniform(-9.0, 9.0),
                    "fase": rng.uniform(0, math.tau),
                })

    def atualizar(self, dt):
        self.tempo += dt
        larg_mapa = max(LARGURA, self.nivel.largura_px)
        alt_mapa = max(ALTURA, self.nivel.altura_px)

        if self.eh_interior:
            for p in self.poeira:
                p["x"] += (p["vx"] + math.sin(self.tempo * 1.4 + p["fase"]) * 2.5) * dt
                p["y"] += p["vy"] * dt
                if p["y"] < 14:
                    p["y"] = alt_mapa - 18
                if p["x"] < 14 or p["x"] > larg_mapa - 14:
                    p["vx"] = -p["vx"]
            return

        for b in self.borboletas:
            t = self.tempo * b["vel"] + b["fase"]
            b["x"] = b["ancora_x"] + math.sin(t) * b["raio_x"]
            b["y"] = b["ancora_y"] + math.sin(t * 2.0) * b["raio_y"]

        for f in self.folhas:
            osc_x = math.sin(self.tempo * 2.2 + f["fase"]) * 6.0
            osc_y = math.cos(self.tempo * 2.8 + f["fase"]) * 4.5
            f["x"] = (f["x"] + (f["vx"] + osc_x) * dt) % LARGURA
            f["y"] = (f["y"] + (f["vy"] + osc_y) * dt) % ALTURA

        for n in self.nuvens:
            n["x"] += n["vel"] * dt
            if n["x"] > larg_mapa + 40:
                n["x"] = -n["larg"] - 20

        for v in self.vagalumes:
            v["x"] = (v["x"] + (v["vx"] + math.sin(self.tempo * 2.0 + v["fase"]) * 6.0) * dt) % larg_mapa
            v["y"] = (v["y"] + (v["vy"] + math.cos(self.tempo * 1.7 + v["fase"]) * 6.0) * dt) % alt_mapa

    def desenhar_chao(self, tela, ox, oy, clima="dia"):
        """Camada abaixo dos personagens (velas sobre mesas/altares e sombras de nuvens)."""
        self._desenhar_velas_mesa(tela, ox, oy)
        if self.eh_interior:
            return

        if clima == "dia":
            for n in self.nuvens:
                sx = round(n["x"]) - ox
                sy = round(n["y"]) - oy
                if sx + n["larg"] < 0 or sx >= LARGURA or sy + n["alt"] < 0 or sy >= ALTURA:
                    continue
                sombra = pygame.Surface((n["larg"], n["alt"]), pygame.SRCALPHA)
                pygame.draw.ellipse(sombra, (10, 22, 18, 28), (0, 0, n["larg"], n["alt"]))
                pygame.draw.ellipse(
                    sombra,
                    (10, 22, 18, 18),
                    (6, 4, max(8, n["larg"] - 12), max(6, n["alt"] - 8)),
                )
                tela.blit(sombra, (sx, sy))

    def desenhar_ar(self, tela, ox, oy, clima="dia"):
        """Camada acima dos personagens (luzes HD-2D, raios solares, borboletas, folhas, vagalumes e vinheta)."""
        self._desenhar_luzes_mundo(tela, ox, oy, clima)

        if self.eh_interior:
            for i, p in enumerate(self.poeira):
                sx = round(p["x"]) - ox
                sy = round(p["y"]) - oy
                if 0 <= sx < LARGURA and 0 <= sy < ALTURA:
                    brilho = math.sin(self.tempo * 3.0 + p["fase"] + i)
                    if brilho > -0.2:
                        cor = (255, 238, 175) if brilho > 0.4 else (210, 190, 140)
                        tela.set_at((sx, sy), cor)
            tela.blit(self.vinheta, (0, 0))
            return

        # Feixes diagonais de luz solar / luar (God Rays estilo Octopath Traveler)
        self._desenhar_raios_luz(tela, clima)

        # Borboletas batendo asas perto das flores
        for b in self.borboletas:
            sx = round(b["x"]) - ox
            sy = round(b["y"]) - oy
            if -6 <= sx < LARGURA + 6 and -6 <= sy < ALTURA + 6:
                if 0 <= sx < LARGURA and 0 <= sy + 5 < ALTURA:
                    tela.set_at((sx, sy + 5), (26, 64, 30))
                asa_aberta = math.sin(self.tempo * 20.0 + b["fase"]) > -0.15
                cor = b["cor"]
                if asa_aberta:
                    pygame.draw.rect(tela, cor, (sx - 2, sy - 1, 2, 2))
                    pygame.draw.rect(tela, cor, (sx + 1, sy - 1, 2, 2))
                    tela.set_at((sx, sy), (40, 32, 46))
                else:
                    pygame.draw.rect(tela, cor, (sx, sy - 2, 1, 3))
                    tela.set_at((sx, sy), (40, 32, 46))

        # Folhas e pólen dourado levados pela brisa
        for f in self.folhas:
            sx = round(f["x"])
            sy = round(f["y"])
            if 0 <= sx < LARGURA - 2 and 0 <= sy < ALTURA - 2:
                if f["polen"]:
                    tela.set_at((sx, sy), f["cor"])
                else:
                    girando = math.sin(self.tempo * 7.5 + f["fase"]) > 0
                    if girando:
                        pygame.draw.rect(tela, f["cor"], (sx, sy, 2, 1))
                        tela.set_at((sx + 1, sy + 1), (38, 110, 48))
                    else:
                        pygame.draw.rect(tela, f["cor"], (sx, sy, 1, 2))

        # Vagalumes e orbes de luz pulsantes (estilo Legend of Mana / Octopath)
        qtd_ativa = len(self.vagalumes) if clima in ("noite", "trevas", "chuva") else 6
        cor_halo = (130, 235, 255) if clima == "trevas" else (190, 255, 110)
        for v in self.vagalumes[:qtd_ativa]:
            sx = round(v["x"]) - ox
            sy = round(v["y"]) - oy
            if -8 <= sx < LARGURA + 8 and -8 <= sy < ALTURA + 8:
                pulso = 0.5 + 0.5 * math.sin(self.tempo * 4.2 + v["fase"])
                if pulso > 0.25:
                    raio = round(4 + pulso * 4)
                    halo = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
                    alfa = int(pulso * (115 if clima in ("noite", "trevas") else 48))
                    pygame.draw.circle(halo, (*cor_halo, alfa), (raio, raio), raio)
                    tela.blit(halo, (sx - raio, sy - raio))
                    if 0 <= sx < LARGURA and 0 <= sy < ALTURA:
                        tela.set_at((sx, sy), (245, 255, 210))

        tela.blit(self.vinheta, (0, 0))

    def _desenhar_raios_luz(self, tela, clima):
        """Desenha feixes diagonais translúcidos de luz solar (ou luar místico) atravessando a tela."""
        if clima == "chuva":
            return
        camada = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        cor_base = (150, 195, 255) if clima in ("noite", "trevas") else (255, 240, 175)
        intensidade = 14 if clima in ("noite", "trevas") else 20

        for i, pos_x in enumerate((38, 132, 236)):
            osc = math.sin(self.tempo * 0.7 + i * 1.9) * 14.0
            x_topo = round(pos_x + osc)
            larg = 24 + (i % 2) * 10
            alfa = int(intensidade * (0.7 + 0.3 * math.sin(self.tempo * 1.3 + i)))
            pontos = [
                (x_topo, 0),
                (x_topo + larg, 0),
                (x_topo + larg + 58, ALTURA),
                (x_topo + 58, ALTURA),
            ]
            pygame.draw.polygon(camada, (*cor_base, alfa), pontos)
        tela.blit(camada, (0, 0))

    def _desenhar_velas_mesa(self, tela, ox, oy):
        """Desenha uma pequena vela acesa com chama oscilante no centro de cada mesa/altar."""
        for mx, my in getattr(self.nivel, "mesas", []):
            sx = mx - ox
            sy = my - oy - 2
            if -8 <= sx < LARGURA + 8 and -8 <= sy < ALTURA + 8:
                pygame.draw.rect(tela, (90, 62, 34), (sx - 2, sy + 2, 4, 1))
                pygame.draw.rect(tela, (245, 236, 210), (sx - 1, sy - 1, 2, 3))
                osc = round(math.sin(self.tempo * 14.0 + mx) * 0.7)
                alt_chama = 3 if math.sin(self.tempo * 19.0 + my) > -0.3 else 2
                pygame.draw.rect(tela, (255, 145, 35), (sx - 1 + osc, sy - 1 - alt_chama, 2, alt_chama))
                tela.set_at((sx + osc, sy - 2), (255, 245, 160))

    def _desenhar_luzes_mundo(self, tela, ox, oy, clima):
        """Halos de luz quente (Bloom estilo Octopath) em velas, janelas, tochas e cristais."""
        fator = 1.35 if clima in ("noite", "trevas") else 1.0

        # 1. Luz das velas nas mesas
        for mx, my in getattr(self.nivel, "mesas", []):
            sx, sy = mx - ox, my - oy - 4
            if -32 <= sx < LARGURA + 32 and -32 <= sy < ALTURA + 32:
                raio = round(20 + math.sin(self.tempo * 8.5 + mx * 0.3) * 2.0)
                halo = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
                pygame.draw.circle(halo, (255, 185, 80, min(90, int(30 * fator))), (raio, raio), raio)
                pygame.draw.circle(halo, (255, 225, 130, min(110, int(46 * fator))), (raio, raio), max(4, raio // 2))
                tela.blit(halo, (sx - raio, sy - raio))

        # 2. Luz quente saindo das janelas das cabanas
        for jx, jy in getattr(self.nivel, "janelas", []):
            sx, sy = jx - ox, jy - oy
            if -24 <= sx < LARGURA + 24 and -24 <= sy < ALTURA + 24:
                raio = 14
                halo = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
                pygame.draw.circle(halo, (255, 210, 105, min(85, int(28 * fator))), (raio, raio), raio)
                tela.blit(halo, (sx - raio, sy - raio))

        # 3. Luz das tochas de parede e cristais arcanos nas ruínas/santuário
        for tx, ty, tipo in getattr(self.nivel, "tochas", []):
            sx, sy = tx - ox, ty - oy - 2
            if -28 <= sx < LARGURA + 28 and -28 <= sy < ALTURA + 28:
                raio = round(16 + math.sin(self.tempo * 9.0 + tx) * 1.5)
                halo = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
                cor = (80, 220, 255) if tipo == "cristal" else (255, 165, 65)
                pygame.draw.circle(halo, (*cor, min(95, int(34 * fator))), (raio, raio), raio)
                pygame.draw.circle(halo, (255, 245, 200, min(110, int(44 * fator))), (raio, raio), max(3, raio // 2))
                tela.blit(halo, (sx - raio, sy - raio))

        # 4. Luz dos postes de lanterna à beira dos caminhos
        for lx, ly in getattr(self.nivel, "postes_luz", []):
            sx, sy = lx - ox, ly - oy
            if -24 <= sx < LARGURA + 24 and -24 <= sy < ALTURA + 24:
                raio = 13
                halo = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
                pygame.draw.circle(halo, (255, 205, 95, min(85, int(26 * fator))), (raio, raio), raio)
                tela.blit(halo, (sx - raio, sy - raio))


class Moeda:
    """Moeda de 16-bits (Cobre: 1, Prata: 5, Ouro: 20) com giro, quique e atração magnética."""

    CORES = {
        "cobre": {"cor": (210, 115, 60), "luz": (255, 175, 120), "sombra": (120, 50, 25), "valor": 1},
        "prata": {"cor": (195, 205, 220), "luz": (250, 252, 255), "sombra": (110, 120, 135), "valor": 5},
        "ouro": {"cor": (245, 195, 45), "luz": (255, 245, 150), "sombra": (155, 110, 20), "valor": 20},
    }

    def __init__(self, pos, tipo="cobre"):
        self.pos = pygame.Vector2(pos)
        self.tipo = tipo
        self.dados = self.CORES.get(tipo, self.CORES["cobre"])
        self.valor = self.dados["valor"]
        self.vel = pygame.Vector2(random.uniform(-35, 35), random.uniform(-65, -30))
        self.z = 8.0
        self.vz = random.uniform(40, 80)
        self.tempo = random.random() * 3.0
        self.tempo_vida = 35.0

    @property
    def rect(self):
        r = pygame.Rect(0, 0, 8, 8)
        r.center = (round(self.pos.x), round(self.pos.y - self.z))
        return r

    def atualizar(self, dt, jogador, rpg, audio=None, textos=None):
        self.tempo += dt
        self.tempo_vida -= dt
        if self.tempo_vida <= 0:
            return False

        # Física de quique inicial
        if self.z > 0:
            self.pos.x += self.vel.x * dt
            self.z += self.vz * dt
            self.vz -= 320.0 * dt
            if self.z <= 0:
                self.z = 0
                self.vz = -self.vz * 0.45
                self.vel.x *= 0.6
                if abs(self.vz) < 18:
                    self.vz = 0

        # Atração magnética (< 42px base ou ampliado com relíquias)
        raio_mag = getattr(rpg, "alcance_magnetico_moedas", 42.0)
        dist = self.pos.distance_to(jogador.rect.center)
        if dist < raio_mag:
            if dist > 0.001:
                direcao = (pygame.Vector2(jogador.rect.center) - self.pos).normalize()
                vel_mag = max(85.0, (raio_mag - dist) * 7.5)
                self.pos += direcao * vel_mag * dt
            self.z = max(0.0, self.z - dt * 25)

        # Coleta ao tocar no herói
        if dist < 12.0:
            rpg.ouro += self.valor
            if audio:
                audio.sfx("moeda")
            if textos is not None:
                from rpg import TextoFlutuante
                textos.append(TextoFlutuante(self.pos, f"+{self.valor}G", self.dados["luz"]))
            return False

        return True

    def desenhar(self, tela, camera):
        ox, oy = camera.offset
        sx = round(self.pos.x) - ox
        sy = round(self.pos.y) - oy
        sz = round(self.z)

        # Sombra no solo
        sombra = pygame.Surface((8, 4), pygame.SRCALPHA)
        pygame.draw.ellipse(sombra, (0, 0, 0, 65), (0, 0, 8, 4))
        tela.blit(sombra, (sx - 4, sy - 2))

        # Giro em 3 fases
        fase = math.sin(self.tempo * 9.5)
        larg_fase = max(1, round(abs(fase) * 5))
        y_moeda = sy - sz - 4

        cor_principal = self.dados["cor"]
        cor_luz = self.dados["luz"]
        cor_sombra = self.dados["sombra"]

        rect_m = pygame.Rect(sx - larg_fase // 2, y_moeda, max(2, larg_fase), 6)
        pygame.draw.rect(tela, cor_sombra, rect_m, border_radius=1)
        if larg_fase >= 3:
            pygame.draw.rect(tela, cor_principal, rect_m.inflate(-1, -1), border_radius=1)
            tela.set_at((rect_m.centerx, rect_m.centery - 1), cor_luz)
        else:
            pygame.draw.line(tela, cor_luz, (rect_m.centerx, rect_m.top + 1), (rect_m.centerx, rect_m.bottom - 1))


class BauTesouro:
    """Baú de tesouro em 16-bits (madeira, ferro trancado ou ouro lendário)."""

    TIPOS = {
        "madeira": {"nome": "Baú de Madeira", "requer_chave": False, "cor_base": (120, 72, 38), "cor_borda": (65, 38, 20), "cor_ferro": (175, 180, 195)},
        "ferro": {"nome": "Baú de Ferro Trancado", "requer_chave": True, "cor_base": (115, 125, 140), "cor_borda": (50, 58, 70), "cor_ferro": (225, 185, 65)},
        "ouro": {"nome": "Baú dos Reis Guardiões", "requer_chave": False, "cor_base": (230, 175, 45), "cor_borda": (140, 95, 20), "cor_ferro": (255, 245, 160)},
    }

    def __init__(self, pos, tipo="madeira", conteudo=None):
        self.pos = pygame.Vector2(pos)
        self.tipo = tipo
        self.info = self.TIPOS.get(tipo, self.TIPOS["madeira"])
        self.conteudo = conteudo or {}
        self.aberto = False
        self.anim_abertura = 0.0
        self.rect = pygame.Rect(0, 0, 16, 14)
        self.rect.midbottom = (round(self.pos.x), round(self.pos.y))

    def interagir(self, jogo):
        if self.aberto:
            return False

        rpg = jogo.rpg
        audio = getattr(jogo.app, "audio", None)

        if self.info["requer_chave"]:
            if rpg.chaves <= 0:
                if audio:
                    audio.sfx("bloqueio")
                from rpg import TextoFlutuante
                jogo.textos_flutuantes.append(TextoFlutuante(self.rect.midtop, "Trancado! Precisa de Chave!", (255, 160, 130)))
                return False
            rpg.chaves -= 1

        self.aberto = True
        self.anim_abertura = 1.0

        if self.tipo == "ouro":
            if audio:
                audio.sfx("fanfarra_item")
            jogo.conquistas.desbloquear("mestre_dos_baus", jogo)
        else:
            if audio:
                audio.sfx("bau_abrir")

        from rpg import TextoFlutuante
        ouro_rec = self.conteudo.get("ouro", 25 if self.tipo == "madeira" else (50 if self.tipo == "ferro" else 100))
        rpg.ouro += ouro_rec
        jogo.soltar_moeda(self.rect.center, "ouro" if ouro_rec >= 20 else "prata", qtd=min(4, max(1, ouro_rec // 20)))

        if "bombas" in self.conteudo:
            rpg.bombas += self.conteudo["bombas"]
            jogo.textos_flutuantes.append(TextoFlutuante(self.rect.midtop, f"+{self.conteudo['bombas']} Bombas!", (255, 235, 90)))
        if "chave" in self.conteudo:
            rpg.chaves += self.conteudo["chave"]
            jogo.textos_flutuantes.append(TextoFlutuante(self.rect.midtop, "+1 Chave de Masmorra!", (255, 220, 80)))
        if "item_quest" in self.conteudo:
            item_id = self.conteudo["item_quest"]
            jogo.missoes.adicionar_item_quest(item_id, 1, jogo)
        if "arma" in self.conteudo:
            rpg.arma_equipada = self.conteudo["arma"]
            jogo.textos_flutuantes.append(TextoFlutuante(self.rect.midtop, "Arma Encontrada!", (255, 245, 140)))

        return True

    def atualizar(self, dt):
        if self.aberto and self.anim_abertura > 0:
            self.anim_abertura = max(0.0, self.anim_abertura - dt * 2.5)

    def desenhar(self, tela, camera):
        ox, oy = camera.offset
        sx = self.rect.x - ox
        sy = self.rect.y - oy

        cor_b = self.info["cor_base"]
        cor_bord = self.info["cor_borda"]
        cor_met = self.info["cor_ferro"]

        # Sombra
        sombra = pygame.Surface((18, 6), pygame.SRCALPHA)
        pygame.draw.ellipse(sombra, (0, 0, 0, 80), sombra.get_rect())
        tela.blit(sombra, (sx - 1, sy + 10))

        # Base do baú
        pygame.draw.rect(tela, cor_bord, (sx, sy + 4, 16, 10), border_radius=2)
        pygame.draw.rect(tela, cor_b, (sx + 1, sy + 5, 14, 8), border_radius=1)

        # Dobradiças/cintas metálicas
        pygame.draw.line(tela, cor_met, (sx + 3, sy + 4), (sx + 3, sy + 13))
        pygame.draw.line(tela, cor_met, (sx + 12, sy + 4), (sx + 12, sy + 13))

        if not self.aberto:
            pygame.draw.rect(tela, cor_bord, (sx, sy, 16, 6), border_radius=2)
            pygame.draw.rect(tela, cor_b, (sx + 1, sy + 1, 14, 4), border_radius=1)
            pygame.draw.rect(tela, cor_met, (sx + 7, sy + 4, 2, 3))
            tela.set_at((sx + 7, sy + 5), (35, 25, 20))
        else:
            pygame.draw.rect(tela, cor_bord, (sx + 1, sy - 4, 14, 5), border_radius=2)
            pygame.draw.rect(tela, (255, 235, 120), (sx + 2, sy + 4, 12, 3))
            halo = pygame.Surface((16, 14), pygame.SRCALPHA)
            pygame.draw.ellipse(halo, (255, 245, 160, 95), (0, 0, 16, 14))
            tela.blit(halo, (sx, sy - 6))


class PlacaPressao:
    """Placa de pressão no piso que ativa mecanismos quando pisada."""

    def __init__(self, pos, id_gatilho="portao_1"):
        self.pos = pygame.Vector2(pos)
        self.id_gatilho = id_gatilho
        self.pressionada = False
        self.rect = pygame.Rect(0, 0, 14, 14)
        self.rect.center = (round(self.pos.x), round(self.pos.y))

    def atualizar(self, entidades_sobre, audio=None):
        antes = self.pressionada
        self.pressionada = any(self.rect.colliderect(getattr(e, "rect", e)) for e in entidades_sobre)
        if self.pressionada and not antes and audio:
            audio.sfx("menu_confirmar")
        return self.pressionada

    def desenhar(self, tela, camera):
        ox, oy = camera.offset
        sx = self.rect.x - ox
        sy = self.rect.y - oy
        if self.pressionada:
            pygame.draw.rect(tela, (72, 75, 88), (sx + 1, sy + 2, 12, 10), border_radius=2)
            pygame.draw.rect(tela, (115, 215, 140), (sx + 3, sy + 4, 6, 6), 1)
        else:
            pygame.draw.rect(tela, (45, 48, 58), (sx, sy + 1, 14, 13), border_radius=2)
            pygame.draw.rect(tela, (120, 125, 145), (sx + 1, sy, 12, 11), border_radius=2)
            pygame.draw.rect(tela, (175, 180, 205), (sx + 3, sy + 2, 8, 7), 1)


class BlocoPedra:
    """Bloco de pedra esculpido que pode ser empurrado pelo herói."""

    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 16, 16)
        self.pos = pygame.Vector2(x, y)
        self.tempo_empurrao = 0.0
        self.deslizando = False
        self.alvo_deslize = pygame.Vector2(x, y)

    def empurrar(self, direcao_vetor, dt, nivel, audio=None):
        if self.deslizando:
            return
        self.tempo_empurrao += dt
        if self.tempo_empurrao >= 0.35:
            dx = 16 if direcao_vetor.x > 0.4 else (-16 if direcao_vetor.x < -0.4 else 0)
            dy = 16 if direcao_vetor.y > 0.4 else (-16 if direcao_vetor.y < -0.4 else 0)
            tx = int((self.pos.x + dx) // 16)
            ty = int((self.pos.y + dy) // 16)
            if nivel.dentro(tx, ty) and not nivel.solido(tx, ty):
                self.alvo_deslize = self.pos + pygame.Vector2(dx, dy)
                self.deslizando = True
                self.tempo_empurrao = 0.0
                if audio:
                    audio.sfx("pedra_arrastar")

    def atualizar(self, dt):
        if self.deslizando:
            diff = self.alvo_deslize - self.pos
            if diff.length() < 1.5:
                self.pos = pygame.Vector2(self.alvo_deslize)
                self.rect.topleft = (round(self.pos.x), round(self.pos.y))
                self.deslizando = False
            else:
                self.pos += diff.normalize() * 45.0 * dt
                self.rect.topleft = (round(self.pos.x), round(self.pos.y))
        else:
            self.tempo_empurrao = max(0.0, self.tempo_empurrao - dt * 1.5)

    def desenhar(self, tela, camera):
        ox, oy = camera.offset
        sx = self.rect.x - ox
        sy = self.rect.y - oy
        sombra = pygame.Surface((16, 4), pygame.SRCALPHA)
        pygame.draw.ellipse(sombra, (0, 0, 0, 75), (0, 0, 16, 4))
        tela.blit(sombra, (sx, sy + 13))
        pygame.draw.rect(tela, (40, 42, 52), (sx, sy, 16, 16), border_radius=2)
        pygame.draw.rect(tela, (110, 118, 132), (sx + 1, sy + 1, 14, 14), border_radius=1)
        pygame.draw.line(tela, (160, 170, 185), (sx + 2, sy + 2), (sx + 13, sy + 2))
        pygame.draw.rect(tela, (72, 80, 94), (sx + 5, sy + 5, 6, 6))
        tela.set_at((sx + 7, sy + 7), (180, 220, 255))
        tela.set_at((sx + 8, sy + 8), (180, 220, 255))


class PortaoFerro:
    """Portão de grades de ferro que abre com placas de pressão ou chave."""

    def __init__(self, x, y, id_gatilho="portao_1", aberto=False):
        self.rect = pygame.Rect(x, y, 16, 16)
        self.id_gatilho = id_gatilho
        self.aberto = aberto
        self.progresso = 1.0 if aberto else 0.0

    def definir_aberto(self, estado, audio=None):
        if self.aberto != estado:
            self.aberto = estado
            if audio:
                audio.sfx("pedra_arrastar" if estado else "bloqueio")

    def atualizar(self, dt):
        alvo = 1.0 if self.aberto else 0.0
        if self.progresso < alvo:
            self.progresso = min(alvo, self.progresso + dt * 3.0)
        elif self.progresso > alvo:
            self.progresso = max(alvo, self.progresso - dt * 3.0)

    @property
    def solido(self):
        return self.progresso < 0.65

    def desenhar(self, tela, camera):
        ox, oy = camera.offset
        sx = self.rect.x - ox
        sy = self.rect.y - oy
        desloc_y = round(self.progresso * 14)
        if desloc_y < 14:
            pygame.draw.rect(tela, (30, 32, 42), (sx, sy + desloc_y, 16, 16 - desloc_y))
            for gx in (sx + 2, sx + 6, sx + 10, sx + 14):
                pygame.draw.line(tela, (170, 180, 195), (gx, sy + desloc_y), (gx, sy + 15))
            pygame.draw.line(tela, (215, 175, 65), (sx, sy + desloc_y), (sx + 15, sy + desloc_y))


class Bomba:
    """Bomba explosiva colocada pelo herói com pavio aceso e dano em área."""

    def __init__(self, pos, dano=4):
        self.pos = pygame.Vector2(pos)
        self.dano = dano
        self.tempo = 2.0
        self.rect = pygame.Rect(0, 0, 12, 12)
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        self.explodiu = False

    def atualizar(self, dt, jogo):
        self.tempo -= dt
        if random.random() < 0.7:
            faisca = Particula((self.pos.x + 2, self.pos.y - 7), (255, 235, 70))
            faisca.vel = pygame.Vector2(random.uniform(-10, 10), random.uniform(-25, -10))
            faisca.vida = 0.18
            jogo.particulas.append(faisca)

        if self.tempo <= 0 and not self.explodiu:
            self.explodiu = True
            self.detonar(jogo)
            return False
        return True

    def detonar(self, jogo):
        audio = getattr(jogo.app, "audio", None)
        if audio:
            audio.sfx("explosao_bomba")

        jogo.tremor = 4.0
        jogo.tempo_tremor = 0.28
        from rpg import OndaMagica
        jogo.ondas.append(OndaMagica(self.pos, 32, (255, 140, 50), 0.35))
        jogo.particulas += explosao(self.pos, [(255, 90, 40), (255, 220, 80), (70, 70, 80)], 18)

        # Destrói paredes rachadas
        for parede in list(jogo.paredes_rachadas):
            if self.pos.distance_to(parede.rect.center) < 28.0:
                parede.destruir(jogo)

        # Destrói vasos de cerâmica próximos
        for vaso in list(getattr(jogo, "vasos", [])):
            if not vaso.quebrado and self.pos.distance_to(vaso.rect.center) < 32.0:
                vaso.quebrar(jogo)

        area_dano = pygame.Rect(0, 0, 48, 48)
        area_dano.center = (round(self.pos.x), round(self.pos.y))
        golpe_bomba = random.randint(10000, 999999)

        for inimigo in jogo.inimigos:
            if area_dano.colliderect(inimigo.rect):
                inimigo.receber_golpe(golpe_bomba, self.pos, dano=self.dano)
                from rpg import TextoFlutuante
                jogo.textos_flutuantes.append(TextoFlutuante(inimigo.rect.midtop, f"-{self.dano} Bomba!", (255, 140, 60)))

        for chefe in jogo.chefes:
            if not chefe.morrendo and area_dano.colliderect(chefe.rect):
                chefe.receber_golpe(golpe_bomba, self.pos, dano=self.dano)
                from rpg import TextoFlutuante
                jogo.textos_flutuantes.append(TextoFlutuante(chefe.rect.midtop, f"-{self.dano} Bomba!", (255, 140, 60)))

        if area_dano.inflate(-18, -18).colliderect(jogo.jogador.rect):
            jogo.jogador.levar_dano(1, self.pos, jogo.rpg, audio)

    def desenhar(self, tela, camera):
        ox, oy = camera.offset
        sx = round(self.pos.x) - ox
        sy = round(self.pos.y) - oy
        sombra = pygame.Surface((12, 4), pygame.SRCALPHA)
        pygame.draw.ellipse(sombra, (0, 0, 0, 70), (0, 0, 12, 4))
        tela.blit(sombra, (sx - 6, sy + 3))
        pygame.draw.circle(tela, (25, 25, 32), (sx, sy), 5)
        pygame.draw.circle(tela, (55, 60, 75), (sx, sy), 4)
        tela.set_at((sx - 1, sy - 1), (140, 150, 175))
        pygame.draw.line(tela, (140, 95, 50), (sx, sy - 4), (sx + 2, sy - 7), 1)
        tela.set_at((sx + 2, sy - 7), (255, 230, 80))


class ParedeRachada:
    """Parede de masmorra ou caverna que pode ser explodida com uma bomba."""

    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 16, 16)
        self.destruida = False

    def destruir(self, jogo):
        if self.destruida:
            return
        self.destruida = True
        if self in jogo.paredes_rachadas:
            jogo.paredes_rachadas.remove(self)
        cx, cy = self.rect.x // 16, self.rect.y // 16
        if jogo.nivel.dentro(cx, cy):
            jogo.nivel.grade[cy][cx] = "," if not jogo.nivel.eh_interior else "_"
            jogo.nivel._desenhar_tile(cx, cy)
        jogo.particulas += explosao(self.rect.center, [(130, 135, 145), (85, 90, 100), (210, 215, 225)], 16)
        jogo.conquistas.desbloquear("explorador_segredos", jogo)

    def desenhar(self, tela, camera):
        ox, oy = camera.offset
        sx = self.rect.x - ox
        sy = self.rect.y - oy
        pygame.draw.rect(tela, (48, 52, 64), (sx, sy, 16, 16))
        pygame.draw.rect(tela, (92, 98, 112), (sx + 1, sy + 1, 14, 14))
        pygame.draw.line(tela, (24, 26, 34), (sx + 4, sy + 2), (sx + 8, sy + 7))
        pygame.draw.line(tela, (24, 26, 34), (sx + 8, sy + 7), (sx + 6, sy + 13))
        pygame.draw.line(tela, (24, 26, 34), (sx + 8, sy + 7), (sx + 12, sy + 9))


class PonteGelo:
    """Tile de água congelado pela magia Nova de Gelo, permitindo travessia."""

    def __init__(self, cx, cy, duracao=9.0):
        self.cx = cx
        self.cy = cy
        self.rect = pygame.Rect(cx * 16, cy * 16, 16, 16)
        self.duracao = duracao
        self.tempo = 0.0

    def atualizar(self, dt):
        self.tempo += dt
        return self.tempo < self.duracao

    def desenhar(self, tela, camera):
        ox, oy = camera.offset
        sx = self.rect.x - ox
        sy = self.rect.y - oy
        prog = self.tempo / self.duracao
        alfa = int((1.0 - prog) * 230)
        surf = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.rect(surf, (160, 235, 255, alfa), (0, 0, 16, 16))
        pygame.draw.rect(surf, (220, 250, 255, alfa), (1, 1, 14, 14), 1)
        pygame.draw.line(surf, (255, 255, 255, alfa), (3, 4), (12, 11))
        pygame.draw.line(surf, (255, 255, 255, alfa), (12, 5), (6, 12))
        tela.blit(surf, (sx, sy))


class ItemQuest:
    """Item de missão no cenário (Cogumelo Noturno do Pântano, Minério de Cristal da Caverna)."""

    CORES = {
        "cogumelo_noturno": {"nome": "Cogumelo Noturno", "cor": (145, 75, 215), "luz": (215, 160, 255)},
        "minerio_cristal": {"nome": "Minério de Cristal", "cor": (75, 205, 255), "luz": (190, 245, 255)},
    }

    def __init__(self, pos, item_id="cogumelo_noturno"):
        self.pos = pygame.Vector2(pos)
        self.item_id = item_id
        self.info = self.CORES.get(item_id, self.CORES["cogumelo_noturno"])
        self.rect = pygame.Rect(0, 0, 12, 12)
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        self.tempo = random.random() * 4.0

    def atualizar(self, dt, jogo):
        self.tempo += dt
        if self.rect.colliderect(jogo.jogador.rect):
            jogo.missoes.adicionar_item_quest(self.item_id, 1, jogo)
            audio = getattr(jogo.app, "audio", None)
            if audio:
                audio.sfx("menu_confirmar")
            from rpg import TextoFlutuante
            jogo.textos_flutuantes.append(TextoFlutuante(self.rect.midtop, f"+1 {self.info['nome']}!", self.info["luz"]))
            return False
        return True

    def desenhar(self, tela, camera):
        ox, oy = camera.offset
        sx = self.rect.centerx - ox
        sy = self.rect.centery - oy

        sombra = pygame.Surface((10, 4), pygame.SRCALPHA)
        pygame.draw.ellipse(sombra, (0, 0, 0, 60), (0, 0, 10, 4))
        tela.blit(sombra, (sx - 5, sy + 4))

        flutuar = round(math.sin(self.tempo * 4.5) * 1.5)
        cor = self.info["cor"]
        cor_luz = self.info["luz"]

        halo = pygame.Surface((16, 16), pygame.SRCALPHA)
        alfa = int(60 + 35 * math.sin(self.tempo * 5.0))
        pygame.draw.circle(halo, (*cor, alfa), (8, 8), 7)
        tela.blit(halo, (sx - 8, sy - 8 + flutuar))

        if self.item_id == "cogumelo_noturno":
            pygame.draw.rect(tela, (215, 210, 225), (sx - 2, sy + flutuar, 4, 5))
            pygame.draw.circle(tela, cor, (sx, sy - 1 + flutuar), 5)
            tela.set_at((sx - 1, sy - 2 + flutuar), cor_luz)
            tela.set_at((sx + 1, sy - 2 + flutuar), cor_luz)
        else:
            pontos = [
                (sx, sy - 5 + flutuar),
                (sx + 4, sy + flutuar),
                (sx, sy + 5 + flutuar),
                (sx - 4, sy + flutuar),
            ]
            pygame.draw.polygon(tela, cor, pontos)
            pygame.draw.polygon(tela, cor_luz, [(sx, sy - 3 + flutuar), (sx + 2, sy + flutuar), (sx, sy + 3 + flutuar)], 1)


# =====================================================================
# PILAR 2: PORTAIS MÍSTICOS & PORTAIS FANTASMAS (PROMPT 2)
# =====================================================================

CORES_ELEMENTO_PORTAL = {
    "agua":    {"nucleo": (35, 140, 240),  "borda": (140, 225, 255), "runa": (195, 245, 255)},
    "terra":   {"nucleo": (195, 135, 50),  "borda": (245, 205, 95),  "runa": (255, 235, 160)},
    "areia":   {"nucleo": (230, 165, 45),  "borda": (255, 220, 120), "runa": (255, 245, 185)},
    "sol":     {"nucleo": (245, 90, 25),   "borda": (255, 215, 75),  "runa": (255, 245, 165)},
    "veneno":  {"nucleo": (160, 45, 215),  "borda": (110, 245, 145), "runa": (210, 175, 255)},
    "trevas":  {"nucleo": (50, 210, 205),  "borda": (145, 65, 225),  "runa": (185, 245, 255)},
    "oceano":  {"nucleo": (25, 105, 240),  "borda": (120, 205, 255), "runa": (205, 245, 255)},
    "cristal": {"nucleo": (85, 225, 255),  "borda": (215, 245, 255), "runa": (255, 255, 255)},
    "rocha":   {"nucleo": (175, 120, 65),  "borda": (235, 195, 130), "runa": (250, 230, 180)},
    "gelo":    {"nucleo": (165, 225, 255), "borda": (235, 250, 255), "runa": (255, 255, 255)},
    "luz":     {"nucleo": (255, 220, 95),  "borda": (255, 255, 215), "runa": (255, 255, 245)},
    "aco":     {"nucleo": (185, 40, 60),   "borda": (245, 135, 155), "runa": (255, 200, 210)},
    "fogo":    {"nucleo": (245, 70, 35),   "borda": (255, 195, 75),  "runa": (255, 240, 150)},
    "arcano":  {"nucleo": (180, 75, 250),  "borda": (245, 150, 255), "runa": (255, 220, 255)},
    "sagrado": {"nucleo": (245, 205, 75),  "borda": (255, 250, 190), "runa": (255, 255, 245)},
    "vazio":   {"nucleo": (225, 30, 80),   "borda": (145, 25, 210),  "runa": (255, 140, 180)},
}


class PortalMistico:
    """Monumento de Portal 16-bits para arenas de chefes.
    
    No estado normal: Grande arco de pedra esculpida com pilares guardiões e
    vórtice elemental giratório. Se o herói não tem nível suficiente, correntes
    vermelhas fecham a entrada.
    
    Após derrotar o chefe: A matéria física se desfaz e resta apenas o 'Fantasma
    da Porta', uma silhueta etérea translúcida oscilante com poeira estelar.
    """

    def __init__(self, rect_porta, destino, chefe_id, req_nivel, elemento="arcano", nome_chefe="Guardião"):
        self.rect_porta = rect_porta
        self.destino = destino
        self.chefe_id = chefe_id
        self.req_nivel = req_nivel
        self.elemento = elemento
        self.nome_chefe = nome_chefe
        self.paleta = CORES_ELEMENTO_PORTAL.get(elemento, CORES_ELEMENTO_PORTAL["arcano"])
        
        # O arco centraliza-se sobre a porta de transição
        self.cx = rect_porta.centerx
        self.cy = rect_porta.centery
        self.largura = 32
        self.altura = 36
        self.rect = pygame.Rect(0, 0, self.largura, self.altura)
        self.rect.midbottom = (self.cx, rect_porta.bottom)
        
        self.t = random.random() * 6.0
        self.particulas_vortice = []

    def atualizar(self, dt, jogo):
        self.t += dt
        esta_derrotado = self.chefe_id in jogo.rpg.chefes_derrotados

        # Spawna partículas de energia
        if not esta_derrotado:
            if random.random() < 0.65:
                ang = random.uniform(0, math.tau)
                raio_s = random.uniform(10, 16)
                px = self.cx + math.cos(ang) * raio_s
                py = self.cy - 6 + math.sin(ang) * (raio_s * 0.75)
                cor = random.choice([self.paleta["nucleo"], self.paleta["borda"], self.paleta["runa"]])
                p = Particula((px, py), cor)
                # Velocidade espiral em direção ao centro
                p.vel = pygame.Vector2(self.cx - px, (self.cy - 6) - py).rotate(30).normalize() * random.uniform(22, 55)
                p.vida = random.uniform(0.35, 0.65)
                self.particulas_vortice.append(p)
        else:
            # Fantasma da porta emite poeira estelar ascendente
            if random.random() < 0.35:
                px = self.cx + random.uniform(-10, 10)
                py = self.cy + random.uniform(-4, 4)
                cor = random.choice([(160, 220, 255), (200, 240, 255), (255, 255, 230)])
                p = Particula((px, py), cor)
                p.vel = pygame.Vector2(random.uniform(-8, 8), random.uniform(-25, -12))
                p.vida = random.uniform(0.6, 1.2)
                self.particulas_vortice.append(p)

        self.particulas_vortice = [p for p in self.particulas_vortice if p.atualizar(dt)]

    def desenhar(self, tela, camera, fonte, rpg):
        ox, oy = camera.offset
        sx = self.rect.centerx - ox
        sy = self.rect.bottom - oy
        esta_derrotado = self.chefe_id in rpg.chefes_derrotados

        if esta_derrotado:
            self._desenhar_fantasma(tela, sx, sy, fonte)
        else:
            self._desenhar_ativo(tela, sx, sy, fonte, rpg)

        # Desenha partículas do portal
        for p in self.particulas_vortice:
            p.desenhar(tela, camera)

    def _desenhar_fantasma(self, tela, sx, sy, fonte):
        """Silhueta espectral translúcida que oscila no ar como uma miragem."""
        alfa_base = int(105 + 40 * math.sin(self.t * 3.2))
        surf_fantasma = pygame.Surface((self.largura + 16, self.altura + 16), pygame.SRCALPHA)
        fcx = (self.largura + 16) // 2
        fbase = self.altura + 8

        # Sombra espectral circular no chão
        pygame.draw.ellipse(surf_fantasma, (110, 180, 255, max(15, alfa_base // 4)), (fcx - 14, fbase - 4, 28, 8))

        # Pilares espectrais translúcidos
        cor_espectral = (140, 210, 255, alfa_base)
        cor_brilho = (220, 245, 255, min(255, alfa_base + 60))

        # Pilar esquerdo e direito fantasma
        pygame.draw.rect(surf_fantasma, cor_espectral, (fcx - 14, fbase - 26, 6, 26), 1)
        pygame.draw.rect(surf_fantasma, cor_espectral, (fcx + 8, fbase - 26, 6, 26), 1)

        # Arco superior
        pygame.draw.arc(surf_fantasma, cor_espectral, (fcx - 14, fbase - 34, 28, 16), 0, math.pi, 2)
        # Glifo de paz no centro do topo
        pygame.draw.circle(surf_fantasma, cor_brilho, (fcx, fbase - 26), 3, 1)

        # Brilho central suave
        halo_c = pygame.Surface((20, 24), pygame.SRCALPHA)
        pygame.draw.ellipse(halo_c, (120, 210, 255, alfa_base // 3), (0, 0, 20, 24))
        surf_fantasma.blit(halo_c, (fcx - 10, fbase - 26))

        tela.blit(surf_fantasma, (sx - (self.largura + 16) // 2, sy - (self.altura + 16)))

    def _desenhar_ativo(self, tela, sx, sy, fonte, rpg):
        """Portal Místico sólido com arco de pedra, pilares guardiões e vórtice turbilhonante."""
        # 1. Base e sombra
        sombra = pygame.Surface((self.largura + 8, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(sombra, (0, 0, 0, 95), sombra.get_rect())
        tela.blit(sombra, (sx - (self.largura + 8) // 2, sy - 4))

        # 2. Vórtice Elemental no Centro
        vx = sx
        vy = sy - 18
        larg_v = 16
        alt_v = 22

        # Halo de brilho exterior do vórtice
        halo = pygame.Surface((larg_v * 2, alt_v * 2), pygame.SRCALPHA)
        alfa_halo = int(65 + 30 * math.sin(self.t * 4.5))
        pygame.draw.ellipse(halo, (*self.paleta["nucleo"], alfa_halo), (larg_v // 2, alt_v // 2, larg_v, alt_v))
        tela.blit(halo, (vx - larg_v, vy - alt_v))

        # Camadas do redemoinho (espiral girando)
        pygame.draw.ellipse(tela, (18, 14, 28), (vx - 7, vy - 10, 14, 20))
        for camada in range(3):
            fase = self.t * (3.5 + camada * 1.2)
            c_larg = max(4, round(6 + 3 * math.sin(fase)))
            c_alt = max(6, round(9 + 4 * math.cos(fase)))
            cor_cam = self.paleta["borda"] if camada % 2 == 0 else self.paleta["nucleo"]
            pygame.draw.ellipse(tela, cor_cam, (vx - c_larg, vy - c_alt, c_larg * 2, c_alt * 2), 1)

        # Núcleo fulgurante central
        r_nucleo = max(2, round(3 + math.sin(self.t * 8.0) * 1.2))
        pygame.draw.circle(tela, (255, 255, 255), (vx, vy), r_nucleo)
        pygame.draw.circle(tela, self.paleta["runa"], (vx, vy), max(1, r_nucleo - 1))

        # 3. Monumento de Pedra: Pilares Guardiões Ladeando
        # Pilar Esquerdo
        pygame.draw.rect(tela, (36, 40, 52), (sx - 14, sy - 30, 6, 30))
        pygame.draw.rect(tela, (68, 76, 96), (sx - 13, sy - 29, 4, 28))
        tela.set_at((sx - 11, sy - 16), self.paleta["runa"])
        tela.set_at((sx - 11, sy - 10), self.paleta["runa"])

        # Pilar Direito
        pygame.draw.rect(tela, (36, 40, 52), (sx + 8, sy - 30, 6, 30))
        pygame.draw.rect(tela, (68, 76, 96), (sx + 9, sy - 29, 4, 28))
        tela.set_at((sx + 11, sy - 16), self.paleta["runa"])
        tela.set_at((sx + 11, sy - 10), self.paleta["runa"])

        # Arco Superior de Pedra esculpida
        pygame.draw.rect(tela, (36, 40, 52), (sx - 14, sy - 34, 28, 5))
        pygame.draw.rect(tela, (82, 92, 115), (sx - 13, sy - 33, 26, 3))
        # Pedra de Fecho (Keystone) com joia elemental
        pygame.draw.rect(tela, (48, 54, 70), (sx - 4, sy - 36, 8, 7))
        pygame.draw.circle(tela, self.paleta["runa"], (sx, sy - 33), 2)

        # 4. Correntes Carmesins se nível insuficiente
        nivel_atual = rpg.nivel
        if nivel_atual < self.req_nivel:
            alfa_corrente = int(195 + 50 * math.sin(self.t * 6.0))
            surf_selo = pygame.Surface((self.largura, self.altura), pygame.SRCALPHA)
            cor_c = (255, 45, 60, alfa_corrente)
            cor_l = (255, 220, 110, alfa_corrente)

            # Correntes cruzadas
            pygame.draw.line(surf_selo, cor_c, (4, 8), (self.largura - 4, self.altura - 6), 2)
            pygame.draw.line(surf_selo, cor_c, (self.largura - 4, 8), (4, self.altura - 6), 2)
            # Cadeado Rúnico no Centro
            mid_x, mid_y = self.largura // 2, self.altura // 2
            pygame.draw.circle(surf_selo, (40, 10, 15, alfa_corrente), (mid_x, mid_y), 6)
            pygame.draw.circle(surf_selo, cor_c, (mid_x, mid_y), 5, 1)
            pygame.draw.circle(surf_selo, cor_l, (mid_x, mid_y), 2)
            tela.blit(surf_selo, (sx - self.largura // 2, sy - self.altura))


# =====================================================================
# PILAR 3: MONÓLITOS ASTRAIS DE TELEPORTE (PROMPT 2)
# =====================================================================

class MonolitoTeleporte:
    """Monólito Astral de Teleporte (Waypoints de Viagem Rápida).
    
    Presente em pontos estratégicos do reino. Ao se aproximar pela 1ª vez, desperta
    com animação celestial e som de sino. Ao interagir, abre o mapa de teleporte.
    """

    WAYPOINTS_INFO = {
        "vila":     {"nome": "Vila de Aurora",          "mapa": "vila.txt",           "pos": (200, 160)},
        "mundo":    {"nome": "Encruzilhada Central",    "mapa": "mundo.txt",          "pos": (240, 180)},
        "oasis":    {"nome": "Oásis do Deserto",        "mapa": "oasis.txt",          "pos": (220, 160)},
        "bosque":   {"nome": "Bosque de Outono",        "mapa": "bosque_outono.txt",   "pos": (240, 160)},
        "caverna":  {"nome": "Caverna de Cristal",      "mapa": "caverna_cristal.txt", "pos": (190, 140)},
        "castelo":  {"nome": "Entrada do Castelo",      "mapa": "castelo.txt",         "pos": (240, 170)},
    }

    def __init__(self, pos, id_waypoint, nome_regiao=None):
        self.pos = pygame.Vector2(pos)
        self.id_waypoint = id_waypoint
        info = self.WAYPOINTS_INFO.get(id_waypoint, {})
        self.nome_regiao = nome_regiao or info.get("nome", "Monólito Astral")
        self.mapa_destino = info.get("mapa", "vila.txt")
        self.rect = pygame.Rect(0, 0, 16, 24)
        self.rect.midbottom = (round(self.pos.x), round(self.pos.y))
        self.t = random.random() * 4.0
        self.particulas = []
        self.despertando = 0.0

    def atualizar(self, dt, jogo):
        self.t += dt
        esta_desperto = self.id_waypoint in jogo.rpg.waypoint_descobertos

        # Despertar ao se aproximar pela primeira vez
        dist_jogador = self.pos.distance_to(jogo.jogador.rect.center)
        if not esta_desperto and dist_jogador < 32.0:
            jogo.rpg.waypoint_descobertos.add(self.id_waypoint)
            self.despertando = 1.2
            audio = getattr(jogo.app, "audio", None)
            if audio:
                audio.sfx("ativar_monolito")
            jogo.clarao = 0.45
            jogo.cor_clarao = (140, 215, 255)
            from rpg import OndaMagica, TextoFlutuante
            jogo.ondas.append(OndaMagica(self.pos, 40, (110, 220, 255), 0.55))
            jogo.textos_flutuantes.append(
                TextoFlutuante(self.rect.midtop, f"★ Monólito Desperto: {self.nome_regiao}! ★", (140, 235, 255))
            )
            for _ in range(16):
                p = Particula(self.pos, random.choice([(120, 225, 255), (255, 255, 230), (70, 160, 255)]))
                p.vel = pygame.Vector2(random.uniform(-40, 40), random.uniform(-55, -15))
                self.particulas.append(p)
            jogo.conquistas.desbloquear("viajante_astral", jogo)
            if hasattr(jogo, "definir_checkpoint"):
                jogo.definir_checkpoint(jogo.nivel.caminho, (self.pos.x, self.pos.y + 16), "baixo", f"Monólito: {self.nome_regiao}", notificar=True)

        # Partículas contínuas se ativo
        if esta_desperto:
            if random.random() < 0.35:
                p = Particula((self.pos.x + random.uniform(-6, 6), self.pos.y - 18), (140, 230, 255))
                p.vel = pygame.Vector2(random.uniform(-6, 6), random.uniform(-18, -6))
                p.vida = 0.45
                self.particulas.append(p)

        self.particulas = [p for p in self.particulas if p.atualizar(dt)]

    def desenhar(self, tela, camera, fonte, rpg):
        ox, oy = camera.offset
        sx = round(self.pos.x) - ox
        sy = round(self.pos.y) - oy
        esta_desperto = self.id_waypoint in rpg.waypoint_descobertos

        # Sombra na base
        sombra = pygame.Surface((18, 6), pygame.SRCALPHA)
        pygame.draw.ellipse(sombra, (0, 0, 0, 80), sombra.get_rect())
        tela.blit(sombra, (sx - 9, sy - 3))

        # Pedestal de Pedra cinza
        pygame.draw.rect(tela, (42, 46, 60), (sx - 7, sy - 8, 14, 6))
        pygame.draw.rect(tela, (76, 84, 106), (sx - 6, sy - 7, 12, 4))

        # Pilar Obelisco
        pygame.draw.rect(tela, (28, 32, 44), (sx - 4, sy - 20, 8, 12))
        pygame.draw.rect(tela, (54, 62, 80), (sx - 3, sy - 19, 6, 10))

        # Cristal Astral Flutuante no topo
        flutuar = round(math.sin(self.t * 3.8) * 1.5)
        cy_cristal = sy - 26 + flutuar

        if esta_desperto:
            # Halo celestial
            halo = pygame.Surface((18, 18), pygame.SRCALPHA)
            alfa_h = int(75 + 40 * math.sin(self.t * 4.5))
            pygame.draw.circle(halo, (90, 210, 255, alfa_h), (9, 9), 8)
            tela.blit(halo, (sx - 9, cy_cristal - 9))

            # Cristal em losango azul-celeste
            pontos = [(sx, cy_cristal - 6), (sx + 4, cy_cristal), (sx, cy_cristal + 6), (sx - 4, cy_cristal)]
            pygame.draw.polygon(tela, (65, 175, 255), pontos)
            pygame.draw.polygon(tela, (185, 245, 255), [(sx, cy_cristal - 4), (sx + 2, cy_cristal), (sx, cy_cristal + 4)], 1)
            tela.set_at((sx, cy_cristal), (255, 255, 255))
        else:
            # Cristal adormecido (pedra fosca escura)
            pontos = [(sx, cy_cristal - 5), (sx + 3, cy_cristal), (sx, cy_cristal + 5), (sx - 3, cy_cristal)]
            pygame.draw.polygon(tela, (45, 52, 68), pontos)
            pygame.draw.polygon(tela, (85, 95, 120), pontos, 1)

        for p in self.particulas:
            p.desenhar(tela, camera)


# =====================================================================
# PILAR 1: TOTENS E PLACAS DE SINALIZAÇÃO DE ESTRADA (PROMPT 2)
# =====================================================================

class TotemSinalizacao:
    """Totem de pedra esculpida com indicações geográficas de rotas e direções."""

    def __init__(self, pos, rotas):
        self.pos = pygame.Vector2(pos)
        self.rotas = rotas  # lista de strings, ex.: ["← Vila de Aurora", "Deserto →", "↑ Covil"]
        self.rect = pygame.Rect(0, 0, 14, 18)
        self.rect.midbottom = (round(self.pos.x), round(self.pos.y))

    def desenhar(self, tela, camera, fonte, jogador_rect):
        ox, oy = camera.offset
        sx = round(self.pos.x) - ox
        sy = round(self.pos.y) - oy

        # Sombra
        sombra = pygame.Surface((14, 4), pygame.SRCALPHA)
        pygame.draw.ellipse(sombra, (0, 0, 0, 70), (0, 0, 14, 4))
        tela.blit(sombra, (sx - 7, sy - 2))

        # Totem de pedra
        pygame.draw.rect(tela, (46, 50, 62), (sx - 5, sy - 16, 10, 15))
        pygame.draw.rect(tela, (86, 92, 110), (sx - 4, sy - 15, 8, 13))
        # Placas de madeira esculpidas nas laterais
        pygame.draw.rect(tela, (135, 90, 48), (sx - 7, sy - 14, 14, 4))
        pygame.draw.rect(tela, (175, 120, 68), (sx - 6, sy - 13, 12, 2))

        # Exibe letreiro elegante na tela se o jogador estiver próximo (< 28px)
        dist = self.pos.distance_to(jogador_rect.center)
        if dist < 32.0:
            # Letreiro da estrada: uma linha se couber, senão duas rotas por linha
            texto_completo = " | ".join(self.rotas)
            if fonte.size(texto_completo)[0] <= LARGURA - 40:
                linhas = [texto_completo]
            else:
                linhas = [" | ".join(self.rotas[i : i + 2]) for i in range(0, len(self.rotas), 2)]
            larg_t = max(fonte.size(l)[0] for l in linhas) + 16
            alt_t = 6 + 10 * len(linhas)
            desenhar_painel(tela, (LARGURA // 2 - larg_t // 2, 44, larg_t, alt_t), "dourado", alfa=230, cantos=False)
            for i, linha in enumerate(linhas):
                desenhar_texto(tela, fonte, linha, (LARGURA // 2, 44 + 8 + i * 10), (255, 235, 140), centro=True)


# =====================================================================
# PILAR 4: VASOS QUEBRÁVEIS & RELÍQUIAS SECRETAS (PROMPT 2)
# =====================================================================

class VasoQuebravel:
    """Vaso de cerâmica 16-bits que estilhaça com golpe de espada ou bomba."""

    def __init__(self, pos):
        self.pos = pygame.Vector2(pos)
        self.rect = pygame.Rect(0, 0, 12, 12)
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        self.quebrado = False

    def quebrar(self, jogo):
        if self.quebrado:
            return
        self.quebrado = True
        audio = getattr(jogo.app, "audio", None)
        if audio:
            audio.sfx("quebrar_vaso")

        # Partículas de cerâmica estilhaçada
        cores_cera = [(195, 110, 60), (160, 85, 45), (235, 145, 95)]
        jogo.particulas += explosao(self.pos, cores_cera, 10)
        jogo.conquistas.desbloquear("quebrador_de_potes", jogo)

        # Drop balanceado: 50% moedas, 25% coração, 25% mana
        sorteio = random.random()
        if sorteio < 0.50:
            qtd_moedas = random.randint(1, 3)
            valores = [1, 5, 10]
            val = random.choices(valores, weights=[65, 30, 5])[0]
            for _ in range(qtd_moedas):
                jogo.moedas.append(Moeda(self.pos, val))
        elif sorteio < 0.75:
            jogo.coracoes.append(Coracao(self.pos))
        else:
            # Orbe de Mana
            jogo.rpg.mana = min(jogo.rpg.mana_maxima, jogo.rpg.mana + 5.0)
            from rpg import TextoFlutuante
            jogo.textos_flutuantes.append(TextoFlutuante(self.pos, "+5 MP", (120, 205, 255)))

    def desenhar(self, tela, camera):
        if self.quebrado:
            return
        ox, oy = camera.offset
        sx = self.rect.centerx - ox
        sy = self.rect.bottom - oy

        # Sombra
        sombra = pygame.Surface((10, 3), pygame.SRCALPHA)
        pygame.draw.ellipse(sombra, (0, 0, 0, 60), (0, 0, 10, 3))
        tela.blit(sombra, (sx - 5, sy - 1))

        # Jarro de cerâmica 16-bits
        pygame.draw.ellipse(tela, (175, 95, 50), (sx - 5, sy - 11, 10, 10))
        pygame.draw.ellipse(tela, (215, 135, 80), (sx - 4, sy - 10, 8, 8))
        # Bocal do vaso
        pygame.draw.rect(tela, (145, 75, 35), (sx - 3, sy - 13, 6, 3))
        pygame.draw.rect(tela, (235, 160, 105), (sx - 2, sy - 12, 4, 1))


class ReliquiaGuardiao:
    """Relíquia Secreta Colecionável deixada pelos Guardiões Antigos.
    
    Existem 6 espalhadas pelo mundo. Ao entregar ao Ancião da Vila,
    ele expande as bolsas de bombas, alcance de moedas e atributos vitais.
    """

    RELIQUIAS_INFO = {
        "reliquia_vento":    {"nome": "Cálice dos Ventos",     "cor": (140, 235, 210)},
        "reliquia_areias":   {"nome": "Escaravelho Solar",     "cor": (255, 215, 75)},
        "reliquia_cristais": {"nome": "Prisma Diamante",       "cor": (160, 235, 255)},
        "reliquia_pantanos": {"nome": "Totem das Brumas",      "cor": (195, 125, 255)},
        "reliquia_gelo":     {"nome": "Coração Glacial",       "cor": (215, 250, 255)},
        "reliquia_cripta":   {"nome": "Selo dos Reis Mortos",  "cor": (255, 140, 160)},
    }

    def __init__(self, pos, id_reliquia):
        self.pos = pygame.Vector2(pos)
        self.id_reliquia = id_reliquia
        info = self.RELIQUIAS_INFO.get(id_reliquia, {"nome": "Relíquia Ancestral", "cor": (255, 225, 90)})
        self.nome = info["nome"]
        self.cor = info["cor"]
        self.rect = pygame.Rect(0, 0, 14, 14)
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        self.t = random.random() * 5.0

    def atualizar(self, dt, jogo):
        self.t += dt
        if self.id_reliquia in jogo.rpg.reliquias_coletadas or self.id_reliquia in jogo.rpg.reliquias_entregues:
            return False

        if self.rect.colliderect(jogo.jogador.rect):
            jogo.rpg.reliquias_coletadas.add(self.id_reliquia)
            audio = getattr(jogo.app, "audio", None)
            if audio:
                audio.sfx("fanfarra_item")
            from rpg import OndaMagica, TextoFlutuante
            jogo.ondas.append(OndaMagica(self.pos, 36, self.cor, 0.45))
            jogo.textos_flutuantes.append(TextoFlutuante(self.rect.midtop, f"★ {self.nome} Coletada! ★", self.cor))
            tot = len(jogo.rpg.reliquias_coletadas) + len(jogo.rpg.reliquias_entregues)
            jogo.aviso_mapa = f"Relíquia Antiga ({tot}/6): Entregue ao Ancião na Vila de Aurora!"
            jogo.tempo_aviso_mapa = 4.0
            return False
        return True

    def desenhar(self, tela, camera):
        ox, oy = camera.offset
        sx = self.rect.centerx - ox
        sy = self.rect.centery - oy

        # Sombra
        sombra = pygame.Surface((12, 4), pygame.SRCALPHA)
        pygame.draw.ellipse(sombra, (0, 0, 0, 70), (0, 0, 12, 4))
        tela.blit(sombra, (sx - 6, sy + 5))

        flutuar = round(math.sin(self.t * 4.0) * 2.0)
        halo = pygame.Surface((18, 18), pygame.SRCALPHA)
        alfa_h = int(80 + 40 * math.sin(self.t * 5.0))
        pygame.draw.circle(halo, (*self.cor, alfa_h), (9, 9), 8)
        tela.blit(halo, (sx - 9, sy - 9 + flutuar))

        # Pingente dourado antigo
        pontos = [(sx, sy - 5 + flutuar), (sx + 5, sy + flutuar), (sx, sy + 5 + flutuar), (sx - 5, sy + flutuar)]
        pygame.draw.polygon(tela, (255, 215, 70), pontos)
        pygame.draw.polygon(tela, self.cor, [(sx, sy - 3 + flutuar), (sx + 3, sy + flutuar), (sx, sy + 3 + flutuar)], 1)
        tela.set_at((sx, sy + flutuar), (255, 255, 255))


class VentoGuia:
    """Brisa Arcana Luminosa que sopra suavemente indicando a direção do próximo desafio."""

    def __init__(self, pos_origem, pos_destino):
        self.pos = pygame.Vector2(pos_origem)
        self.origem = pygame.Vector2(pos_origem)
        self.destino = pygame.Vector2(pos_destino)
        diff = self.destino - self.origem
        self.dir = diff.normalize() if diff.length() > 0.1 else pygame.Vector2(0, -1)
        self.vel = self.dir * 110.0
        self.vida = 1.6
        self.tempo = 0.0
        self.rastro = []

    def atualizar(self, dt):
        self.tempo += dt
        self.vida -= dt
        # Curvatura suave de brisa
        ondulacao = pygame.Vector2(-self.dir.y, self.dir.x) * (math.sin(self.tempo * 9.0) * 25.0)
        self.pos += (self.vel + ondulacao) * dt
        self.rastro.append((pygame.Vector2(self.pos), 0.28))
        for i in range(len(self.rastro)):
            p, v = self.rastro[i]
            self.rastro[i] = (p, v - dt)
        self.rastro = [r for r in self.rastro if r[1] > 0]
        return self.vida > 0

    def desenhar(self, tela, camera):
        ox, oy = camera.offset
        for p, vida_r in self.rastro:
            alfa = int((vida_r / 0.28) * 190)
            surf_p = pygame.Surface((4, 4), pygame.SRCALPHA)
            pygame.draw.circle(surf_p, (255, 235, 140, alfa), (2, 2), 2)
            tela.blit(surf_p, (round(p.x) - ox - 2, round(p.y) - oy - 2))
        sx = round(self.pos.x) - ox
        sy = round(self.pos.y) - oy
        pygame.draw.circle(tela, (255, 255, 255), (sx, sy), 2)
