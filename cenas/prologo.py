"""Capítulo Prólogo: o sonho na casinha e a visão da Entidade Maligna."""
import math
import random

import pygame

from caixa_dialogo import CaixaDialogo
from camera import Camera
from cenas.base import Cena
from config import VELOCIDADES_TEXTO
from efeitos import AmbienteVivo, Particula, explosao
from historia import Conversa, Historia
from level import Nivel
from render3d import criar_cristal_3d
from settings import ALTURA, ARQUIVO_HISTORIA, COR_FUNDO, LARGURA, MAPA_CASA, TILE
from ui import desenhar_texto

CORES_FOGO = [(255, 90, 40), (255, 160, 50), (255, 220, 90), (180, 40, 40)]
CORES_FUMACA = [(60, 50, 65), (90, 75, 95), (40, 35, 45)]
CORES_PODER = [(255, 230, 120), (255, 200, 70), (255, 250, 200)]


def _sprite_dormindo(gfx):
    """Monta o herói deitado na cama com os olhos fechados e cobertor por cima."""
    surf = gfx.tiles["cama"].copy()
    heroi = gfx.jogador["baixo"][0]
    cabeca = heroi.subsurface((8, 4, 16, 13)).copy()
    cor_pele = (252, 214, 176)
    cor_olho_fechado = (104, 56, 30)
    for y in (8, 9):
        for x in range(3, 13):
            if cabeca.get_at((x, y))[:3] in ((40, 32, 56), (255, 255, 255), (68, 128, 228)):
                cabeca.set_at((x, y), cor_olho_fechado if y == 9 else cor_pele)
    surf.blit(cabeca, (0, 0))
    pygame.draw.rect(surf, (226, 86, 86), (2, 10, 12, 2))
    pygame.draw.rect(surf, (190, 48, 52), (2, 12, 12, 3))
    return surf


class Prologo(Cena):
    def __init__(self, app):
        super().__init__(app)
        self.historia = Historia.carregar(ARQUIVO_HISTORIA)
        self.flags = set()
        self.dialogo = None

        # Fase 1: dormindo dentro da casinha
        self.estado = "casa"  # "casa" -> "cidade"
        if hasattr(app, "audio"):
            app.audio.tocar_bgm("abertura_sombria")
        self.tempo = 0.0
        self.casa = Nivel(MAPA_CASA, app.gfx)
        self.ambiente_casa = AmbienteVivo(self.casa)
        self.camera = Camera(self.casa.largura_px, self.casa.altura_px)
        cx, cy = self.casa.cama_pos
        self.rect_cama = pygame.Rect(cx, cy, TILE, TILE)
        self.camera.centralizar(self.rect_cama)
        self.img_dormindo = _sprite_dormindo(app.gfx)

        # Animação de "zzzzzz" sobre a cabeça
        self.zs = []
        self.timer_z = 0.1
        self.particulas = []
        self.falou_sonho = False

        # Fase 2: entidade maligna despertando e destruindo o reino medieval
        self._inicializar_dados_cidade(destruindo=False)

    def _inicializar_dados_cidade(self, destruindo=False):
        self.tempo_cidade = 1.5 if destruindo else 0.0
        self.destruindo = destruindo
        self.falou_visao = False
        self.claroes = 0.0
        self.tremor = 0.0
        self.predios = self._gerar_cidade()
        self.estrelas = self._gerar_estrelas()
        self.nuvens = self._gerar_nuvens()
        self.montanhas = self._gerar_montanhas()
        self.meteoros = []
        self.raios = []
        self.ondas_choque = []
        self.timer_ataque = 0.12

    def _gerar_estrelas(self):
        rng = random.Random(91)
        return [
            (rng.randint(4, LARGURA - 4), rng.randint(4, 72), rng.uniform(0, math.tau), rng.choice([1, 1, 2]))
            for _ in range(38)
        ]

    def _gerar_nuvens(self):
        rng = random.Random(42)
        nuvens = []
        for i in range(9):
            nuvens.append({
                "x": float(rng.randint(-20, LARGURA)),
                "y": rng.randint(14, 86),
                "larg": rng.randint(44, 78),
                "alt": rng.randint(10, 18),
                "vel": rng.uniform(4.0, 9.5) * (1 if i % 2 == 0 else -1),
                "camada": i % 2,
            })
        return nuvens

    def _gerar_montanhas(self):
        rng = random.Random(33)
        # Duas cadeias de montanhas ao fundo (distante e média)
        fundo = [(0, 126)]
        for mx in range(0, LARGURA + 24, 22):
            fundo.append((mx, rng.randint(76, 104)))
        fundo.append((LARGURA, 126))

        media = [(0, 126)]
        for mx in range(0, LARGURA + 18, 16):
            media.append((mx, rng.randint(90, 114)))
        media.append((LARGURA, 126))
        return {"fundo": fundo, "media": media}

    def _gerar_cidade(self):
        """Gera um reino medieval 16-bits com cidadela, catedrais, torres de vigia e casarões enxaimel."""
        rng = random.Random(23)
        predios = []

        # Camada 0 (Fundo): Silhueta de torres reais, aquedutos e catedral gótica (emoldurando a Entidade no centro)
        layout_fundo = [
            (6, 22, 56, "torre"),
            (26, 28, 44, "casarao"),
            (52, 26, 62, "catedral"),
            (76, 28, 46, "casarao"),
            (102, 24, 52, "torre"),
            (126, 68, 36, "castelo_central"),
            (194, 24, 52, "torre"),
            (216, 28, 46, "casarao"),
            (242, 26, 62, "catedral"),
            (266, 28, 44, "casarao"),
            (292, 22, 56, "torre"),
        ]
        # Camada 1 (Frente): Casarões medievais, capelas, torres de guarda e muralhas
        layout_frente = [
            (2, 20, 40, "torre"),
            (20, 26, 32, "casarao"),
            (44, 22, 46, "torre"),
            (64, 32, 36, "catedral"),
            (94, 24, 28, "casarao"),
            (116, 22, 26, "casarao"),
            (136, 24, 22, "casarao"),
            (158, 26, 24, "casarao"),
            (182, 22, 28, "casarao"),
            (202, 26, 32, "casarao"),
            (226, 30, 38, "catedral"),
            (254, 22, 46, "torre"),
            (274, 26, 32, "casarao"),
            (298, 20, 40, "torre"),
        ]

        for camada, lista in ((0, layout_fundo), (1, layout_frente)):
            for x, largura, altura, tipo in lista:
                janelas = []
                passo_y = 9 if tipo in ("catedral", "castelo_central") else 8
                passo_x = 6
                for jy in range(8, altura - 8, passo_y):
                    for jx in range(4, largura - 5, passo_x):
                        if rng.random() < (0.82 if camada == 1 else 0.55):
                            janelas.append((jx, jy))

                if camada == 0:
                    cor = rng.choice([(34, 26, 48), (40, 30, 56), (30, 22, 44)])
                    cor_telhado = (52, 24, 46)
                else:
                    cor = rng.choice([(54, 44, 68), (64, 50, 76), (48, 38, 62)])
                    cor_telhado = rng.choice([(128, 42, 52), (96, 36, 58), (72, 48, 78)])

                rachaduras = [
                    (rng.randint(3, max(4, largura - 5)), rng.randint(4, max(5, altura - 8)))
                    for _ in range(4)
                ]
                predios.append({
                    "x": x,
                    "largura": largura,
                    "altura": float(altura),
                    "altura_max": float(altura),
                    "altura_min": max(18.0, round(altura * 0.62)),
                    "tipo": tipo,
                    "camada": camada,
                    "cor": cor,
                    "cor_telhado": cor_telhado,
                    "torre": tipo in ("torre", "castelo_central", "catedral"),
                    "janelas": janelas,
                    "rachaduras": rachaduras,
                    "fogo": False,
                    "intensidade_fogo": 0.0,
                    "destruido": False,
                })
        return predios

    def _iniciar_dialogo(self, nome):
        if nome not in self.historia.dialogos:
            return
        conversa = Conversa(self.historia, nome, self.flags)
        velocidade = VELOCIDADES_TEXTO[self.app.config["velocidade_texto"]]
        self.dialogo = CaixaDialogo(conversa, self.app.fontes.normal, velocidade)

    # ------------------------------------------------------------ atualização
    def atualizar(self, dt):
        from cenas.jogo import Jogo
        from cenas.pausa import Pausa

        entrada = self.app.entrada
        if entrada.apertou("pausa"):
            self.app.empilhar(Pausa(self.app))
            return

        self.claroes = max(0.0, self.claroes - dt * 2.2)
        self.tremor = max(0.0, self.tremor - dt * 10.0)
        self.particulas = [p for p in self.particulas if p.atualizar(dt)]

        if self.estado == "casa":
            self._atualizar_casa(dt, entrada)
        elif self.estado == "cidade":
            if self._atualizar_cidade(dt, entrada):
                self.app.trocar(Jogo(self.app))

    def _atualizar_casa(self, dt, entrada):
        self.tempo += dt
        self.ambiente_casa.atualizar(dt)

        self.timer_z -= dt
        if self.timer_z <= 0:
            self.timer_z = 0.45
            self.zs.append({
                "x": float(self.rect_cama.centerx + 2),
                "y": float(self.rect_cama.top - 2),
                "t": 0.0,
                "fase": random.uniform(0, math.tau),
            })
        for z in self.zs:
            z["t"] += dt
            z["y"] -= 13 * dt
        self.zs = [z for z in self.zs if z["t"] < 1.8]

        if self.falou_sonho and random.random() < dt * 10:
            px = self.rect_cama.centerx + random.uniform(-10, 10)
            py = self.rect_cama.centery + random.uniform(-8, 8)
            p = Particula((px, py), random.choice(CORES_PODER))
            p.vel = pygame.Vector2(random.uniform(-8, 8), random.uniform(-25, -10))
            self.particulas.append(p)

        if not self.falou_sonho and self.tempo >= 1.6:
            self.falou_sonho = True
            self._iniciar_dialogo("prologo_sonho")

        if self.dialogo:
            self.dialogo.atualizar(dt, entrada)
            if self.dialogo.terminou:
                self.dialogo = None
                self.estado = "cidade"
                self.claroes = 1.0
                self.particulas.clear()

    def _atualizar_elementos_cidade(self, dt, entrada, disparar_ataques):
        for n in self.nuvens:
            n["x"] += n["vel"] * dt
            if n["vel"] > 0 and n["x"] > LARGURA + 20:
                n["x"] = -n["larg"] - 10
            elif n["vel"] < 0 and n["x"] + n["larg"] < -20:
                n["x"] = LARGURA + 10

        # Partículas de aura abissal da Entidade Maligna
        if random.random() < dt * 32:
            ang = random.uniform(0, math.tau)
            dist = random.uniform(12, 68)
            pos = (LARGURA // 2 + math.cos(ang) * dist, 48 + math.sin(ang) * dist * 0.55)
            p = Particula(pos, random.choice([(220, 40, 95), (145, 30, 185), (255, 95, 120), (255, 210, 130)]))
            p.vel = pygame.Vector2(random.uniform(-10, 10), random.uniform(-34, -10))
            self.particulas.append(p)

        if disparar_ataques:
            self.timer_ataque -= dt
            if self.timer_ataque <= 0:
                self.timer_ataque = random.uniform(0.24, 0.44)
                self._disparar_ataque_entidade(entrada)

        # Atualiza meteoros abissais
        novos_meteoros = []
        for m in self.meteoros:
            m["pos"] += m["vel"] * dt
            if random.random() < 0.85:
                rastro = Particula(m["pos"], random.choice(CORES_FOGO + [(235, 50, 110)]))
                rastro.vel = -m["vel"] * 0.12 + pygame.Vector2(random.uniform(-12, 12), random.uniform(-12, 12))
                rastro.vida = 0.28
                self.particulas.append(rastro)
            if m["pos"].y >= m["alvo_y"]:
                self._impactar_cidade(m["pos"].x, m["pos"].y, entrada)
            else:
                novos_meteoros.append(m)
        self.meteoros = novos_meteoros

        for r in self.raios:
            r["vida"] -= dt
        self.raios = [r for r in self.raios if r["vida"] > 0]

        for oc in self.ondas_choque:
            oc["raio"] += dt * 68.0
            oc["vida"] -= dt
        self.ondas_choque = [oc for oc in self.ondas_choque if oc["vida"] > 0]

        # Castelos e edificações em chamas sofrem danos graduais sem perder a silhueta medieval
        chao_y = 126
        for p in self.predios:
            if p["fogo"]:
                p["intensidade_fogo"] = min(1.0, p["intensidade_fogo"] + dt * 1.4)
                if p["altura"] > p["altura_min"]:
                    p["altura"] = max(p["altura_min"], p["altura"] - dt * 5.5)
                else:
                    p["destruido"] = True
                if random.random() < dt * (14 if p["camada"] == 1 else 7):
                    fx = p["x"] + random.uniform(2, p["largura"] - 2)
                    fy = chao_y - random.uniform(4, p["altura"])
                    part = Particula((fx, fy), random.choice(CORES_FOGO + CORES_FUMACA))
                    part.vel = pygame.Vector2(random.uniform(-14, 14), random.uniform(-48, -16))
                    self.particulas.append(part)

    def _atualizar_cidade(self, dt, entrada):
        self.tempo_cidade += dt

        if self.tempo_cidade >= 1.5 and not self.falou_visao:
            self.falou_visao = True
            self.destruindo = True
            self.tremor = 4.0
            self.claroes = 0.8
            entrada.vibrar(0.7, 250)
            if hasattr(self.app, "audio"):
                self.app.audio.tocar_bgm("apocalipse")
                self.app.audio.sfx("magia_raio")
            self._iniciar_dialogo("prologo_visao")

        self._atualizar_elementos_cidade(dt, entrada, disparar_ataques=(self.tempo_cidade >= 1.5))

        if self.dialogo:
            self.dialogo.atualizar(dt, entrada)
            if self.dialogo.terminou and self.tempo_cidade >= 3.8:
                self.dialogo = None
                return True
        elif self.falou_visao and self.tempo_cidade >= 3.8:
            return True
        return False

    def _disparar_ataque_entidade(self, entrada):
        candidatos = [p for p in self.predios if not p["destruido"] and p["camada"] == 1]
        if not candidatos:
            candidatos = self.predios
        alvo = random.choice(candidatos)
        alvo_x = alvo["x"] + alvo["largura"] / 2
        alvo_y = 126 - alvo["altura"] * 0.45

        # Dispara das garras ou do núcleo da Entidade Maligna
        origens = [
            pygame.Vector2(LARGURA // 2 - 44, 54),
            pygame.Vector2(LARGURA // 2 + 44, 54),
            pygame.Vector2(LARGURA // 2, 62),
        ]
        origem = random.choice(origens) + pygame.Vector2(random.uniform(-6, 6), random.uniform(-4, 4))

        if random.random() < 0.48:
            destino = pygame.Vector2(alvo_x, 124)
            pontos = [origem]
            ramos = []
            for passo in range(1, 7):
                interp = origem.lerp(destino, passo / 7)
                interp.x += random.uniform(-12, 12)
                pontos.append(interp)
                if random.random() < 0.55:
                    ramo_fim = interp + pygame.Vector2(random.uniform(-18, 18), random.uniform(8, 22))
                    ramos.append((interp, ramo_fim))
            pontos.append(destino)
            self.raios.append({
                "origem": origem,
                "destino": destino,
                "pontos": pontos,
                "ramos": ramos,
                "vida": 0.22,
            })
            self._impactar_cidade(alvo_x, alvo_y, entrada)
        else:
            direcao = (pygame.Vector2(alvo_x, alvo_y) - origem).normalize()
            self.meteoros.append({
                "pos": pygame.Vector2(origem),
                "vel": direcao * random.uniform(165, 235),
                "alvo_y": alvo_y,
                "raio": random.choice([4, 5, 6]),
            })

    def _impactar_cidade(self, x, y, entrada):
        self.tremor = max(self.tremor, 3.2)
        self.claroes = max(self.claroes, 0.32)
        entrada.vibrar(0.5, 120)
        self.particulas += explosao((x, y), CORES_FOGO, 16)
        self.particulas += explosao((x, y), CORES_FUMACA, 8)
        self.ondas_choque.append({"x": x, "y": min(125.0, y + 6), "raio": 3.0, "vida": 0.35})
        for p in self.predios:
            if abs((p["x"] + p["largura"] / 2) - x) <= p["largura"] * 0.95:
                p["fogo"] = True
                p["altura"] = max(p["altura_min"], p["altura"] - 4.0)

    # ------------------------------------------------------------ desenho
    def desenhar(self, tela):
        if self.estado == "casa":
            self._desenhar_casa(tela)
        else:
            self._desenhar_cidade(tela)

        if self.claroes > 0:
            camada = pygame.Surface(tela.get_size(), pygame.SRCALPHA)
            cor = (255, 60, 80) if self.estado == "cidade" else (255, 255, 255)
            camada.fill((*cor, int(min(1.0, self.claroes) * 200)))
            tela.blit(camada, (0, 0))

        if self.dialogo:
            self.dialogo.desenhar(tela)

    def _desenhar_casa(self, tela):
        tela.fill(COR_FUNDO)
        ox, oy = self.camera.offset
        self.casa.desenhar_cenario_vivo(tela, ox, oy, self.tempo)
        self.ambiente_casa.desenhar_chao(tela, ox, oy, "noite")
        tela.blit(self.img_dormindo, self.camera.aplicar(self.rect_cama))

        for p in self.particulas:
            p.desenhar(tela, self.camera)

        noite = pygame.Surface(tela.get_size(), pygame.SRCALPHA)
        noite.fill((12, 16, 40, 95))
        tela.blit(noite, (0, 0))
        self.ambiente_casa.desenhar_ar(tela, ox, oy, "noite")

        fonte = self.app.fontes.normal
        for z in self.zs:
            oscilacao = math.sin(z["t"] * 5 + z["fase"]) * 3.5
            sx = round(z["x"] + oscilacao) - ox
            sy = round(z["y"]) - oy
            letra = "z" if z["t"] < 0.7 else "Z"
            cor = (255, 240, 150) if z["t"] > 1.2 else (240, 240, 255)
            desenhar_texto(tela, fonte, letra, (sx, sy), cor, centro=True)

    def _desenhar_ceu_apocaliptico(self, tela, dx, dy):
        # 1. Degradê suave de 18 faixas no céu (índigo abissal -> púrpura -> carmesim incandescente)
        cores_ceu = [
            (10, 6, 20), (14, 7, 24), (18, 8, 28), (24, 10, 34),
            (30, 11, 38), (38, 13, 44), (46, 14, 48), (56, 16, 50),
            (68, 18, 52), (80, 20, 50), (94, 22, 48), (110, 26, 46),
            (128, 30, 44), (146, 36, 44), (166, 44, 46), (188, 56, 48),
        ]
        alt_faixa = 8
        for i, cor in enumerate(cores_ceu):
            pygame.draw.rect(tela, cor, (0, i * alt_faixa, LARGURA, alt_faixa + 1))

        # 2. Estrelas cintilando nas camadas altas do céu
        for sx, sy, fase, tam in self.estrelas:
            pulso = 0.5 + 0.5 * math.sin(self.tempo_cidade * 3.2 + fase)
            cor_e = (
                int(160 + 85 * pulso),
                int(130 + 70 * pulso),
                int(195 + 55 * pulso),
            )
            tela.fill(cor_e, (sx, sy, tam, tam))

        # 3. Lua de Sangue / Eclipse Astral atrás da Entidade Maligna
        lx, ly = LARGURA // 2 + dx // 2, 44 + dy // 2
        corona = pygame.Surface((LARGURA, 130), pygame.SRCALPHA)
        pulso_lua = round(math.sin(self.tempo_cidade * 2.5) * 2)
        pygame.draw.circle(corona, (180, 25, 60, 42), (lx, ly), 52 + pulso_lua)
        pygame.draw.circle(corona, (220, 40, 70, 75), (lx, ly), 38 + pulso_lua)
        pygame.draw.circle(corona, (255, 85, 95, 130), (lx, ly), 28)
        # Disco carmesim da Lua de Sangue com eclipse escuro no centro
        pygame.draw.circle(corona, (195, 32, 54, 240), (lx, ly), 25)
        pygame.draw.circle(corona, (140, 18, 42, 240), (lx - 6, ly + 4), 7)
        pygame.draw.circle(corona, (155, 22, 46, 240), (lx + 8, ly - 5), 5)
        pygame.draw.circle(corona, (255, 165, 110, 210), (lx, ly), 25, 1)
        tela.blit(corona, (0, 0))

        # 4. Nuvens de tempestade com iluminação inferior carmesim
        for n in self.nuvens:
            nx = round(n["x"]) + dx // 2
            ny = n["y"] + dy // 2
            larg, alt = n["larg"], n["alt"]
            cor_topo = (24, 12, 32) if n["camada"] == 0 else (34, 16, 42)
            cor_base = (115, 28, 52) if (self.destruindo or self.tempo_cidade >= 1.5) else (72, 22, 48)
            pygame.draw.ellipse(tela, cor_base, (nx, ny + 2, larg, alt))
            pygame.draw.ellipse(tela, cor_topo, (nx + 2, ny, larg - 4, alt - 2))
            pygame.draw.ellipse(tela, cor_topo, (nx + larg // 5, ny - 3, larg // 2, alt))

        # 5. Cadeias de montanhas no horizonte com rios de lava durante o cataclismo
        pts_fundo = [(x + dx // 3, y + dy // 3) for x, y in self.montanhas["fundo"]]
        pts_media = [(x + dx // 2, y + dy // 2) for x, y in self.montanhas["media"]]
        pygame.draw.polygon(tela, (26, 12, 32), pts_fundo)
        pygame.draw.lines(tela, (84, 26, 48), False, pts_fundo[1:-1], 1)
        pygame.draw.polygon(tela, (18, 9, 24), pts_media)
        pygame.draw.lines(tela, (120, 34, 52), False, pts_media[1:-1], 1)

    def _desenhar_predio_medieval(self, tela, p, chao_y, dx, dy):
        px = p["x"] + dx
        alt = round(p["altura"])
        py = chao_y - alt + dy
        larg = p["largura"]
        tipo = p["tipo"]
        camada = p["camada"]

        cor_base = (38, 22, 32) if (p["fogo"] and camada == 1) else p["cor"]
        cor_borda = (16, 10, 22)
        cor_pedra_clara = (
            min(255, cor_base[0] + 18),
            min(255, cor_base[1] + 14),
            min(255, cor_base[2] + 20),
        )

        # Corpo de alvenaria de pedra
        rect = pygame.Rect(px, py, larg, alt)
        pygame.draw.rect(tela, cor_base, rect)
        pygame.draw.line(tela, cor_pedra_clara, (px + 1, py + 1), (px + 1, chao_y + dy - 1))

        # Textura de blocos de cantaria em 16-bits
        if camada == 1:
            for by in range(py + 5, chao_y + dy - 2, 6):
                pygame.draw.line(tela, (28, 18, 34), (px + 1, by), (px + larg - 2, by))
                offset_x = 4 if ((by // 6) % 2 == 0) else 8
                for bx in range(px + offset_x, px + larg - 2, 8):
                    pygame.draw.line(tela, (28, 18, 34), (bx, by - 5), (bx, by))

        pygame.draw.rect(tela, cor_borda, rect, 1)

        # Topo arquitetônico (Cidadela Real, Catedral Gótica, Torre com Ameias ou Casarão com Telhado)
        meio = px + larg // 2
        if not p["fogo"] or p["altura"] > p["altura_max"] - 6:
            if tipo == "castelo_central":
                # Ameias reais e três pináculos góticos com vitral rosácea central
                for ax in range(px - 1, px + larg, 5):
                    pygame.draw.rect(tela, cor_base, (ax, py - 4, 3, 4))
                    pygame.draw.rect(tela, cor_borda, (ax, py - 4, 3, 4), 1)
                for tx_off, t_alt in ((-22, 12), (0, 15), (22, 12)):
                    tcx = meio + tx_off
                    pygame.draw.rect(tela, cor_base, (tcx - 6, py - t_alt + 6, 12, t_alt - 6))
                    pygame.draw.polygon(
                        tela,
                        p["cor_telhado"],
                        [(tcx - 8, py - t_alt + 6), (tcx + 8, py - t_alt + 6), (tcx, py - t_alt - 4)],
                    )
                    pygame.draw.line(tela, (210, 150, 95), (tcx, py - t_alt - 4), (tcx, py - t_alt - 7))
                # Grande vitral rosácea gótico no centro do castelo
                pygame.draw.circle(tela, (24, 14, 30), (meio, py + 14), 7)
                pygame.draw.circle(tela, (255, 195, 90), (meio, py + 14), 5)
                pygame.draw.circle(tela, (220, 70, 95), (meio, py + 14), 3)
                pygame.draw.line(tela, (24, 14, 30), (meio - 6, py + 14), (meio + 6, py + 14))
                pygame.draw.line(tela, (24, 14, 30), (meio, py + 8), (meio, py + 20))
            elif tipo == "catedral":
                # Frontão triangular íngreme com pináculos laterais e rosácea
                pygame.draw.polygon(
                    tela,
                    p["cor_telhado"],
                    [(px - 2, py), (px + larg + 1, py), (meio, py - 14)],
                )
                pygame.draw.polygon(
                    tela,
                    cor_borda,
                    [(px - 2, py), (px + larg + 1, py), (meio, py - 14)],
                    1,
                )
                pygame.draw.line(tela, (225, 185, 95), (meio, py - 14), (meio, py - 18))
                pygame.draw.line(tela, (225, 185, 95), (meio - 2, py - 16), (meio + 2, py - 16))
                if alt > 22:
                    pygame.draw.circle(tela, (255, 205, 105), (meio, py + 8), 4)
                    pygame.draw.circle(tela, (215, 65, 85), (meio, py + 8), 2)
                    pygame.draw.circle(tela, cor_borda, (meio, py + 8), 4, 1)
            elif tipo == "torre":
                # Mísulas, ameias de pedra e chapéu cônico de ardósia
                pygame.draw.rect(tela, cor_pedra_clara, (px - 1, py, larg + 2, 3))
                for ax in range(px - 1, px + larg, 4):
                    pygame.draw.rect(tela, cor_base, (ax, py - 3, 3, 3))
                pygame.draw.polygon(
                    tela,
                    p["cor_telhado"],
                    [(px - 2, py - 3), (px + larg + 1, py - 3), (meio, py - 15)],
                )
                pygame.draw.polygon(
                    tela,
                    cor_borda,
                    [(px - 2, py - 3), (px + larg + 1, py - 3), (meio, py - 15)],
                    1,
                )
                pygame.draw.line(tela, (215, 165, 90), (meio, py - 15), (meio, py - 18))
            else:
                # Casarão medieval com telhado de duas águas e chaminé
                pygame.draw.rect(tela, (78, 48, 36), (px + larg - 6, py - 8, 4, 6))
                pygame.draw.polygon(
                    tela,
                    p["cor_telhado"],
                    [(px - 2, py), (px + larg + 1, py), (px + larg - 3, py - 7), (px + 2, py - 7)],
                )
                pygame.draw.polygon(
                    tela,
                    cor_borda,
                    [(px - 2, py), (px + larg + 1, py), (px + larg - 3, py - 7), (px + 2, py - 7)],
                    1,
                )
                if camada == 1:
                    # Vigas enxaimel no andar superior
                    pygame.draw.line(tela, (42, 26, 22), (px + 1, py + 8), (px + larg - 2, py + 8))
        else:
            # Silhueta de ruínas denteadas e incandescentes quando danificado
            for rx in range(px, px + larg - 3, 4):
                dente = ((rx * 7) % 5) + 2
                pygame.draw.rect(tela, cor_base, (rx, py - dente, 3, dente))
                pygame.draw.line(tela, (255, 120, 45), (rx, py - dente), (rx + 2, py - dente))

        # Janelas góticas / medievais acesas (ou em chamas se o prédio foi atingido)
        for jx, jy in p["janelas"]:
            if jy < alt - 5:
                wx, wy = px + jx, py + jy
                if p["fogo"]:
                    pulso_f = 0.5 + 0.5 * math.sin(self.tempo_cidade * 14.0 + jx + jy)
                    cor_j = (255, int(85 + 135 * pulso_f), 40)
                else:
                    cor_j = (252, 212, 105) if camada == 1 else (195, 145, 85)
                pygame.draw.rect(tela, (22, 14, 28), (wx - 1, wy - 1, 5, 6))
                pygame.draw.rect(tela, cor_j, (wx, wy, 3, 4))
                if tipo in ("catedral", "torre", "castelo_central"):
                    tela.set_at((wx + 1, wy - 1), cor_j)

        # Fissuras de magma e brasas nas paredes em chamas
        if p["fogo"]:
            pygame.draw.line(tela, (255, 110, 40), (px + 2, py), (px + larg - 3, py), 2)
            for rx, ry in p["rachaduras"]:
                if ry < alt - 4:
                    cx_r, cy_r = px + rx, py + ry
                    pygame.draw.line(tela, (255, 95, 35), (cx_r, cy_r), (cx_r + 3, cy_r + 5), 1)
                    pygame.draw.line(tela, (255, 220, 95), (cx_r, cy_r), (cx_r + 1, cy_r + 2), 1)

    def _desenhar_cidade(self, tela):
        dx = round(random.uniform(-self.tremor, self.tremor)) if self.tremor > 0 else 0
        dy = round(random.uniform(-self.tremor, self.tremor)) if self.tremor > 0 else 0

        # 1. Céu apocalíptico, estrelas, Lua de Sangue, nuvens e cordilheiras
        self._desenhar_ceu_apocaliptico(tela, dx, dy)

        # 2. Entidade Maligna colossal despertando no céu
        self._desenhar_entidade_maligna(tela, dx, dy)

        # 3. Raios ramificados disparados pela entidade
        for r in self.raios:
            pts = [(round(p.x) + dx, round(p.y) + dy) for p in r.get("pontos", [r["origem"], r["destino"]])]
            if len(pts) >= 2:
                pygame.draw.lines(tela, (190, 25, 85), False, pts, 5)
                pygame.draw.lines(tela, (255, 95, 150), False, pts, 3)
                pygame.draw.lines(tela, (255, 240, 245), False, pts, 1)
            for r_ini, r_fim in r.get("ramos", []):
                p1 = (round(r_ini.x) + dx, round(r_ini.y) + dy)
                p2 = (round(r_fim.x) + dx, round(r_fim.y) + dy)
                pygame.draw.line(tela, (235, 60, 120), p1, p2, 2)
                pygame.draw.line(tela, (255, 225, 235), p1, p2, 1)

        # 4. Horizonte e Reino Medieval em duas camadas de profundidade
        chao_y = 126
        for camada_alvo in (0, 1):
            for p in self.predios:
                if p["camada"] == camada_alvo:
                    self._desenhar_predio_medieval(tela, p, chao_y, dx, dy)
            if camada_alvo == 0:
                # Névoa rubra entre a cidadela ao fundo e os prédios da frente
                nevoa = pygame.Surface((LARGURA, 44), pygame.SRCALPHA)
                nevoa.fill((120, 24, 48, 45))
                tela.blit(nevoa, (0, chao_y - 40 + dy))

        # 5. Muralha fortificada do reino na base da cena
        muralha_y = chao_y + dy
        pygame.draw.rect(tela, (26, 18, 32), (0, muralha_y, LARGURA, ALTURA - muralha_y))
        for mx in range(0, LARGURA, 8):
            pygame.draw.rect(tela, (42, 30, 50), (mx + dx % 8, muralha_y - 3, 5, 3))
            pygame.draw.rect(tela, (16, 10, 22), (mx + dx % 8, muralha_y - 3, 5, 3), 1)
        pygame.draw.line(tela, (140, 42, 58), (0, muralha_y), (LARGURA, muralha_y))

        # 6. Ondas de choque nos pontos de impacto
        for oc in self.ondas_choque:
            ox_c = round(oc["x"]) + dx
            oy_c = round(oc["y"]) + dy
            r_oc = max(2, round(oc["raio"]))
            rect_oc = pygame.Rect(ox_c - r_oc, oy_c - max(2, r_oc // 3), r_oc * 2, max(4, (r_oc // 3) * 2))
            pygame.draw.ellipse(tela, (255, 185, 95), rect_oc, 1)

        # 7. Meteoros abissais caindo com cauda incandescente
        for m in self.meteoros:
            mx, my = round(m["pos"].x) + dx, round(m["pos"].y) + dy
            raio_m = m.get("raio", 5)
            vel_norm = m["vel"].normalize() if m["vel"].length_squared() > 0 else pygame.Vector2(0, 1)
            cauda = (round(mx - vel_norm.x * 14), round(my - vel_norm.y * 14))
            pygame.draw.line(tela, (220, 45, 75), (mx, my), cauda, raio_m + 2)
            pygame.draw.line(tela, (255, 165, 60), (mx, my), cauda, max(2, raio_m - 1))
            pygame.draw.circle(tela, (210, 35, 70), (mx, my), raio_m + 2)
            pygame.draw.circle(tela, (255, 120, 45), (mx, my), raio_m)
            pygame.draw.circle(tela, (255, 245, 190), (mx, my), max(2, raio_m - 2))

        # 8. Partículas de fogo, fumaça e cinzas
        for p in self.particulas:
            tela.fill(p.cor, (round(p.pos.x) + dx, round(p.pos.y) + dy, 2, 2))

    def _desenhar_entidade_maligna(self, tela, dx, dy):
        progresso = min(1.0, self.tempo_cidade / 1.4)
        flutuacao = math.sin(self.tempo_cidade * 3.0) * 2.5
        cx = LARGURA // 2 + dx + round(math.cos(self.tempo_cidade * 1.6) * 2.0)
        cy = round(38 - (1.0 - progresso) * 12 + flutuacao) + dy

        aura = pygame.Surface((LARGURA, 132), pygame.SRCALPHA)
        alfa_p = int(245 * progresso)

        # 1. Halo rúnico e vórtice abissal girando atrás do Soberano das Trevas
        raio_halo = round(38 + math.sin(self.tempo_cidade * 4.2) * 3)
        pygame.draw.circle(aura, (135, 18, 65, int(90 * progresso)), (cx, cy + 4), raio_halo + 14)
        pygame.draw.circle(aura, (220, 45, 95, int(150 * progresso)), (cx, cy + 4), raio_halo + 4, 1)
        pygame.draw.circle(aura, (175, 35, 110, int(130 * progresso)), (cx, cy + 4), raio_halo - 4, 1)
        for i in range(8):
            ang_r = self.tempo_cidade * 0.9 + i * (math.tau / 8)
            rx = cx + round(math.cos(ang_r) * (raio_halo + 4))
            ry = cy + 4 + round(math.sin(ang_r) * (raio_halo + 4))
            pygame.draw.circle(aura, (255, 120, 165, int(190 * progresso)), (rx, ry), 2)

        # 2. Seis Asas Colossais de Sombra e Carmesim (3 pares articulados com nervuras)
        if progresso > 0.25:
            bater_1 = round(math.sin(self.tempo_cidade * 4.2) * 7)
            bater_2 = round(math.sin(self.tempo_cidade * 4.2 - 0.8) * 6)
            bater_3 = round(math.sin(self.tempo_cidade * 4.2 - 1.6) * 5)

            for lado in (-1, 1):
                # Par Superior (grande envergadura com membrana recortada e nervuras)
                w1_ombro = (cx + lado * 14, cy - 4)
                w1_cotovelo = (cx + lado * round(52 * progresso), cy - 26 + bater_1)
                w1_ponta = (cx + lado * round(112 * progresso), cy - 14 + bater_1)
                w1_recorte1 = (cx + lado * round(82 * progresso), cy + 6 + bater_1 // 2)
                w1_recorte2 = (cx + lado * round(54 * progresso), cy + 14 + bater_1 // 2)
                w1_base = (cx + lado * 18, cy + 12)
                pol_asa1 = [w1_ombro, w1_cotovelo, w1_ponta, w1_recorte1, w1_recorte2, w1_base]
                pygame.draw.polygon(aura, (26, 8, 36, alfa_p), pol_asa1)
                pygame.draw.lines(aura, (155, 32, 78, alfa_p), False, [w1_ombro, w1_cotovelo, w1_ponta], 2)
                pygame.draw.line(aura, (95, 20, 56, alfa_p), w1_cotovelo, w1_recorte1, 1)
                pygame.draw.line(aura, (95, 20, 56, alfa_p), w1_cotovelo, w1_recorte2, 1)

                # Par Médio
                w2_ombro = (cx + lado * 16, cy + 6)
                w2_ponta = (cx + lado * round(86 * progresso), cy + 8 + bater_2)
                w2_base = (cx + lado * round(42 * progresso), cy + 26 + bater_2 // 2)
                pygame.draw.polygon(
                    aura,
                    (20, 6, 30, alfa_p),
                    [w2_ombro, (cx + lado * round(48 * progresso), cy - 6 + bater_2), w2_ponta, w2_base],
                )
                pygame.draw.line(aura, (130, 26, 68, alfa_p), w2_ombro, w2_ponta, 2)

                # Par Inferior (manto de sombras)
                w3_ombro = (cx + lado * 12, cy + 14)
                w3_ponta = (cx + lado * round(58 * progresso), cy + 30 + bater_3)
                w3_base = (cx + lado * 16, cy + 36)
                pygame.draw.polygon(aura, (16, 4, 24, alfa_p), [w3_ombro, w3_ponta, w3_base])
                pygame.draw.line(aura, (105, 22, 58, alfa_p), w3_ombro, w3_ponta, 1)

        # 3. Torso couraçado, ombreiras espinhosas e cabeça coroada com chifres curvos
        # Torso e manto abissal
        pol_torso = [
            (cx - 22, cy - 6),
            (cx + 22, cy - 6),
            (cx + 28, cy + 14),
            (cx + 14, cy + 38),
            (cx, cy + 44),
            (cx - 14, cy + 38),
            (cx - 28, cy + 14),
        ]
        pygame.draw.polygon(aura, (18, 6, 28, alfa_p), pol_torso)
        pygame.draw.polygon(aura, (145, 30, 74, alfa_p), pol_torso, 1)

        # Costelas/placas de armadura espectral no peito
        for ry_off, larg_c in ((6, 16), (12, 13), (28, 10)):
            pygame.draw.line(aura, (90, 20, 52, alfa_p), (cx - larg_c, cy + ry_off), (cx - 4, cy + ry_off + 3), 2)
            pygame.draw.line(aura, (90, 20, 52, alfa_p), (cx + larg_c, cy + ry_off), (cx + 4, cy + ry_off + 3), 2)

        # Ombreiras dracônicas (Pauldrons)
        for lado in (-1, 1):
            pol_ombro = [
                (cx + lado * 14, cy - 8),
                (cx + lado * 32, cy - 14),
                (cx + lado * 36, cy - 2),
                (cx + lado * 22, cy + 8),
            ]
            pygame.draw.polygon(aura, (28, 10, 40, alfa_p), pol_ombro)
            pygame.draw.polygon(aura, (185, 42, 92, alfa_p), pol_ombro, 1)
            pygame.draw.circle(aura, (255, 90, 145, alfa_p), (cx + lado * 24, cy - 4), 2)

        # Cabeça e elmo sombrio
        pol_cabeca = [
            (cx - 14, cy - 18),
            (cx + 14, cy - 18),
            (cx + 16, cy - 4),
            (cx + 10, cy + 6),
            (cx, cy + 9),
            (cx - 10, cy + 6),
            (cx - 16, cy - 4),
        ]
        pygame.draw.polygon(aura, (14, 4, 22, alfa_p), pol_cabeca)
        pygame.draw.polygon(aura, (165, 36, 82, alfa_p), pol_cabeca, 1)

        # Chifres curvos segmentados e coroa central de obsidiana
        if progresso > 0.3:
            for lado in (-1, 1):
                pol_chifre = [
                    (cx + lado * 10, cy - 15),
                    (cx + lado * 24, cy - 24),
                    (cx + lado * 38, cy - 38),
                    (cx + lado * 30, cy - 20),
                    (cx + lado * 16, cy - 10),
                ]
                pygame.draw.polygon(aura, (24, 8, 34, alfa_p), pol_chifre)
                pygame.draw.lines(
                    aura,
                    (220, 58, 102, alfa_p),
                    False,
                    [(cx + lado * 10, cy - 15), (cx + lado * 24, cy - 24), (cx + lado * 38, cy - 38)],
                    2,
                )
            # Crista central da coroa
            pygame.draw.polygon(
                aura,
                (195, 40, 88, alfa_p),
                [(cx - 5, cy - 17), (cx, cy - 30), (cx + 5, cy - 17)],
            )

        # 4. Garras espectrais flutuantes nas laterais canalizando poder
        if progresso > 0.5:
            osc_garra = round(math.sin(self.tempo_cidade * 5.0) * 3.0)
            for lado in (-1, 1):
                gx = cx + lado * 48
                gy = cy + 16 + osc_garra * lado
                # Palma blindada
                pygame.draw.circle(aura, (24, 8, 36, alfa_p), (gx, gy), 7)
                pygame.draw.circle(aura, (195, 42, 92, alfa_p), (gx, gy), 7, 1)
                pygame.draw.circle(aura, (255, 110, 155, alfa_p), (gx, gy), 3)
                # Dedos em garra apontados para baixo/centro
                for d_i, ang_d in enumerate((-0.5, -0.15, 0.2, 0.55)):
                    px_d = gx + round(math.sin(ang_d - lado * 0.25) * 11)
                    py_d = gy + round(math.cos(ang_d) * 12)
                    pygame.draw.line(aura, (32, 10, 44, alfa_p), (gx + (d_i - 1) * 2, gy + 3), (px_d, py_d), 3)
                    pygame.draw.line(aura, (235, 75, 120, alfa_p), (gx + (d_i - 1) * 2, gy + 3), (px_d, py_d), 1)
                # Arco de energia ligando a garra ao núcleo 3D central
                meio_arco = ((gx + cx) // 2, gy - 6 + round(math.sin(self.tempo_cidade * 12 + lado) * 4))
                pygame.draw.lines(aura, (255, 95, 155, int(170 * progresso)), False, [(gx, gy), meio_arco, (cx, cy + 18)], 1)

        tela.blit(aura, (0, 0))

        # 5. Olhos flamejantes (dois olhos oblíquos + terceiro olho abissal na testa)
        abertura = max(1, round(5 * progresso))
        for lado in (-1, 1):
            ox = cx + lado * 8
            oy = cy - 7
            pts_olho = [
                (ox - 5, oy - lado * 1),
                (ox, oy - abertura // 2 - 1),
                (ox + 5, oy + lado * 1),
                (ox, oy + abertura // 2 + 1),
            ]
            pygame.draw.polygon(tela, (255, 35, 65), pts_olho)
            if abertura >= 3:
                pygame.draw.line(tela, (255, 245, 185), (ox, oy - 2), (ox, oy + 2), 2)
                # Rastro de chama subindo do canto externo do olho
                chama_y = round(math.sin(self.tempo_cidade * 10 + lado) * 2)
                pygame.draw.line(tela, (255, 95, 130), (ox + lado * 4, oy), (ox + lado * 8, oy - 4 + chama_y), 1)

        # Terceiro olho vertical na fronte
        if abertura >= 3:
            pygame.draw.ellipse(tela, (255, 75, 135), (cx - 2, cy - 16, 4, 6))
            pygame.draw.line(tela, (255, 245, 200), (cx, cy - 15), (cx, cy - 12))

        # 6. Núcleo poligonal 3D giratório de energia maligna no peito da Entidade
        if progresso > 0.6:
            nucleo_3d = criar_cristal_3d(
                cx, cy + 19, z_base=8.0, raio=6.5, altura=10.5,
                cor=(235, 35, 95), cor_borda=(90, 10, 45)
            )
            nucleo_3d.atualizar(self.tempo_cidade * 1.6)
            nucleo_3d.desenhar(tela, 0, 0, self.tempo_cidade)


class CenarioCidade(Prologo):
    """Cenário de cutscene reutilizável pelo diretor de cenas (@cenario cidade / cidade_destruicao)."""

    def __init__(self, app, destruindo=False):
        self.app = app
        self.particulas = []
        self._inicializar_dados_cidade(destruindo=destruindo)

    def atualizar_cenario(self, dt, entrada):
        self.tempo_cidade += dt
        self.claroes = max(0.0, self.claroes - dt * 2.2)
        self.tremor = max(0.0, self.tremor - dt * 10.0)
        self.particulas = [p for p in self.particulas if p.atualizar(dt)]
        self._atualizar_elementos_cidade(dt, entrada, disparar_ataques=self.destruindo)

    def desenhar_cenario(self, tela):
        self._desenhar_cidade(tela)
        if self.claroes > 0:
            camada = pygame.Surface(tela.get_size(), pygame.SRCALPHA)
            camada.fill((255, 60, 80, int(min(1.0, self.claroes) * 180)))
            tela.blit(camada, (0, 0))
