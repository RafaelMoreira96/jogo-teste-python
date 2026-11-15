"""Módulo de Chefões e Chefe Final (15 Chefes + A Entidade Maligna).

Inclui IA, animações procedurais em 16-bits, ataques telegrafados,
projéteis, barras de vida e o Boss Rush do Salão do Trono.
"""
import math
import random

import pygame

from entidade import Entidade
from render3d import criar_cristal_3d
from settings import ALTURA, LARGURA, TILE
from arte_chefes import ARTE
from ui import AMARELO, BRANCO, CINZA, desenhar_painel, desenhar_texto

VERMELHO = (245, 65, 75)


# Elemento de cada Guardião (define cor dos projéteis e o estilo dos ataques especiais)
ELEMENTO_CHEFE = {
    "rei_slime": "agua", "golem_pedra": "terra", "serpente_dunas": "areia", "colosso_solar": "sol",
    "bruxa_brumas": "veneno", "ceifador_espectral": "trevas", "leviata_aquatico": "oceano",
    "guardiao_diamante": "cristal", "troll_rochas": "rocha", "yeti_glacial": "gelo",
    "valquiria_caida": "luz", "cavaleiro_negro": "aco", "quimera_abissal": "fogo",
    "arquimago": "arcano", "paladino_juizo": "sagrado", "entidade_maligna": "vazio",
}
# (cor principal, brilho)
CORES_ELEMENTO = {
    "agua": ((80, 180, 250), (210, 245, 255)), "terra": ((160, 150, 128), (230, 220, 190)),
    "areia": ((232, 172, 80), (255, 234, 160)), "sol": ((255, 196, 60), (255, 250, 200)),
    "veneno": ((170, 80, 240), (130, 255, 170)), "trevas": ((90, 220, 240), (225, 255, 255)),
    "oceano": ((60, 150, 255), (195, 238, 255)), "cristal": ((150, 230, 255), (255, 255, 255)),
    "rocha": ((170, 120, 80), (232, 204, 164)), "gelo": ((160, 230, 255), (255, 255, 255)),
    "luz": ((255, 232, 130), (255, 255, 236)), "aco": ((235, 50, 70), (255, 190, 200)),
    "fogo": ((255, 110, 40), (255, 232, 120)), "arcano": ((190, 90, 255), (242, 205, 255)),
    "sagrado": ((255, 226, 110), (255, 255, 242)), "vazio": ((240, 40, 90), (255, 175, 205)),
}
# Golpes especiais de cada Guardião (alternados; ficam mais frequentes na fúria)
ESPECIAIS_CHEFE = {
    "rei_slime": ["chuva", "anel"], "golem_pedra": ["anel", "chuva"],
    "serpente_dunas": ["muralha", "investida"], "colosso_solar": ["espiral", "chuva"],
    "bruxa_brumas": ["teleguiado", "anel"], "ceifador_espectral": ["investida", "teleguiado"],
    "leviata_aquatico": ["muralha", "chuva"], "guardiao_diamante": ["espiral", "anel"],
    "troll_rochas": ["chuva", "investida"], "yeti_glacial": ["chuva", "muralha"],
    "valquiria_caida": ["investida", "chuva"], "cavaleiro_negro": ["investida", "muralha"],
    "quimera_abissal": ["espiral", "investida"], "arquimago": ["teleguiado", "espiral"],
    "paladino_juizo": ["chuva", "anel"], "entidade_maligna": ["espiral", "teleguiado", "chuva", "muralha"],
}
ESTILO_PROJETIL = {
    "fogo": "chama", "sol": "chama", "gelo": "estilhaco", "cristal": "estilhaco",
    "trevas": "orbe", "arcano": "orbe", "vazio": "orbe", "agua": "gota", "oceano": "gota",
    "veneno": "gota", "terra": "pedra", "rocha": "pedra", "areia": "pedra",
    "luz": "raio", "sagrado": "raio", "aco": "raio",
}
SOLIDOS_PROJETIL = set("#TBWRCM")  # projéteis voam por cima de água, lava e abismos


class ProjetilChefe:
    """Projétil disparado pelos chefões contra o jogador (visual muda com o elemento)."""

    def __init__(self, pos, vel, dano=1, raio=4, cor=(255, 90, 60), cor_borda=(160, 20, 30), duracao=4.5, elemento=None, estilo=None):
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(vel)
        self.dano = dano
        self.raio = raio
        self.cor = cor
        self.cor_borda = cor_borda
        self.vida = duracao
        self.duracao = duracao
        self.tempo = 0.0
        self.elemento = elemento
        self.estilo = estilo
        self.rastro = []
        self.alvo = None  # entidade perseguida (orbes teleguiados)
        self.giro = 0.0

    @property
    def rect(self):
        r = pygame.Rect(0, 0, self.raio * 2, self.raio * 2)
        r.center = (round(self.pos.x), round(self.pos.y))
        return r

    def atualizar(self, dt, nivel):
        self.tempo += dt
        self.vida -= dt
        if self.vida <= 0:
            return False
        if self.alvo is not None and self.vel.length_squared() > 0:
            desejo = pygame.Vector2(self.alvo.rect.center) - self.pos
            if desejo.length_squared() > 1:
                ang = self.vel.angle_to(desejo)
                ang = (ang + 180) % 360 - 180
                limite = math.degrees(self.giro) * dt
                self.vel.rotate_ip(max(-limite, min(limite, ang)))
        if self.vel.length_squared() > 0:
            self.rastro.append((self.pos.x, self.pos.y))
            if len(self.rastro) > 5:
                self.rastro.pop(0)
        self.pos += self.vel * dt
        cx, cy = int(self.pos.x // TILE), int(self.pos.y // TILE)
        if not nivel.dentro(cx, cy) or nivel.grade[cy][cx] in SOLIDOS_PROJETIL:
            return False
        return True

    def desenhar(self, tela, camera):
        ox, oy = camera.offset
        cx, cy = round(self.pos.x - ox), round(self.pos.y - oy)
        cor_principal, brilho = CORES_ELEMENTO.get(self.elemento, (self.cor, (255, 255, 240)))
        cor = self.cor or cor_principal
        estilo = self.estilo or ESTILO_PROJETIL.get(self.elemento, "padrao")

        if estilo == "explosao":
            prog = 1 - self.vida / max(0.01, self.duracao)
            r = max(2, round(self.raio * (0.6 + prog * 0.6)))
            pygame.draw.circle(tela, brilho, (cx, cy), r)
            pygame.draw.circle(tela, cor, (cx, cy), r, 2)
            pygame.draw.circle(tela, (255, 255, 255), (cx, cy), max(1, r // 2))
            return

        # Rastro que vai sumindo
        for i, (rx, ry) in enumerate(self.rastro):
            tam = max(1, round(self.raio * (i + 1) / (len(self.rastro) + 2)))
            pygame.draw.circle(tela, cor, (round(rx - ox), round(ry - oy)), tam)

        direcao = self.vel.normalize() if self.vel.length_squared() > 0 else pygame.Vector2(1, 0)
        if estilo == "estilhaco":
            frente = direcao * (self.raio + 3)
            lado = direcao.rotate(90) * (self.raio - 1)
            pts = [(cx + frente.x, cy + frente.y), (cx + lado.x, cy + lado.y), (cx - frente.x * 0.7, cy - frente.y * 0.7), (cx - lado.x, cy - lado.y)]
            pygame.draw.polygon(tela, (20, 30, 60), [(px + 1, py + 1) for px, py in pts])
            pygame.draw.polygon(tela, cor, pts)
            pygame.draw.line(tela, brilho, pts[0], pts[2])
        elif estilo == "chama":
            osc = round(math.sin(self.tempo * 30) * 1)
            pygame.draw.circle(tela, (160, 30, 10), (cx, cy), self.raio + 1)
            pygame.draw.circle(tela, cor, (cx, cy), self.raio + osc)
            pygame.draw.circle(tela, brilho, (cx - 1, cy - 1), max(1, self.raio // 2 + 1))
        elif estilo == "orbe":
            pygame.draw.circle(tela, (16, 8, 24), (cx, cy), self.raio + 2)
            pygame.draw.circle(tela, cor, (cx, cy), self.raio + 1, 2)
            pygame.draw.circle(tela, brilho, (cx, cy), max(1, self.raio - 2))
            a = self.tempo * 10
            tela.set_at((cx + round(math.cos(a) * (self.raio + 2)), cy + round(math.sin(a) * (self.raio + 2))), (255, 255, 255))
        elif estilo == "pedra":
            r = self.raio
            pts = [(cx - r, cy), (cx - r // 2, cy - r), (cx + r // 2, cy - r), (cx + r, cy - 1), (cx + r // 2, cy + r), (cx - r // 2, cy + r)]
            pygame.draw.polygon(tela, (40, 30, 24), [(px + 1, py + 1) for px, py in pts])
            pygame.draw.polygon(tela, cor, pts)
            pygame.draw.line(tela, brilho, pts[1], pts[2])
        elif estilo == "raio":
            tras = direcao * (self.raio + 5)
            pygame.draw.line(tela, cor, (cx - tras.x, cy - tras.y), (cx, cy), 3)
            pygame.draw.line(tela, brilho, (cx - tras.x * 0.7, cy - tras.y * 0.7), (cx, cy), 1)
            pygame.draw.circle(tela, brilho, (cx, cy), 2)
        else:  # gota / padrão
            pygame.draw.circle(tela, self.cor_borda if estilo == "padrao" else (20, 30, 60), (cx, cy), self.raio + 1)
            pygame.draw.circle(tela, cor, (cx, cy), self.raio)
            pygame.draw.circle(tela, brilho, (cx - 1, cy - 1), max(1, self.raio // 2))


class _CameraLocal:
    """Câmera falsa para desenhar o chefe numa Surface própria (permite contorno e efeitos)."""

    def __init__(self, offset):
        self.offset = offset

    def aplicar(self, rect):
        return pygame.Rect(rect).move(-self.offset[0], -self.offset[1])


class Chefe(Entidade):
    """Classe base para todos os chefões do jogo."""

    LARG_ARTE, ALT_ARTE = 128, 112

    def __init__(self, x, y, larg_hitbox, alt_hitbox, id_chefe, nome, titulo, vida_max, cor_aura=(255, 210, 80), nivel_minimo=1):
        super().__init__(x, y, larg_hitbox, alt_hitbox)
        self.id_chefe = id_chefe
        self.nome = nome
        self.titulo = titulo
        self.vida_base = vida_max
        self.vida_max = vida_max
        self.vida = vida_max
        self.vida_exibida = float(vida_max)
        self.cor_aura = cor_aura
        self.nivel_minimo = nivel_minimo
        self.nivel_chefe = nivel_minimo
        self.fantasma = False  # True quando invocado no Boss Rush do Salão do Trono
        self.piscar = 0.0
        self.atordoado = 0.0
        self.congelado = 0.0
        self.ultimo_golpe = -1
        self.tempo_vida = 0.0
        self.tempo_ataque = 1.0
        self.ataque_em_curso = None
        self.estado_ia = "passeio"
        self.direcao_olhar = "baixo"
        self.velocidade_base = 45.0
        self.xp_recompensa = 120
        self.dano_contato = 2
        self.fator_poder = 1.0
        self.morrendo = False
        self.tempo_morte = 0.0
        # Fúria, golpes especiais e alertas no chão
        self.elemento = ELEMENTO_CHEFE.get(id_chefe, "arcano")
        self.especiais = ESPECIAIS_CHEFE.get(id_chefe, ["chuva"])
        self.indice_especial = 0
        self.tempo_especial = 5.0
        self.furia = False
        self.anuncio_furia = 0.0
        self.alertas = []  # {"pos", "raio", "t", "total", "acao", "linha"}
        self.rajada = None
        self.investida = None

    def aplicar_escalonamento(self, rpg):
        """Escalona a vida e o poder do chefe de acordo com o nível e progressão do herói."""
        self.nivel_chefe = max(self.nivel_minimo, rpg.nivel)
        # Mais vida e agressividade com o nível do herói
        crescimento = (self.nivel_chefe - 1) * 0.16 + len(rpg.desbloqueadas) * 0.05
        mult_vida = 1.0 + crescimento * 0.8
        self.vida_max = int(self.vida_base * mult_vida)
        self.vida = self.vida_max
        self.vida_exibida = float(self.vida_max)
        self.dano_contato = max(2, 1 + self.nivel_chefe // 5)
        self.fator_poder = min(1.65, 1.0 + crescimento * 0.22)

    @property
    def vivo(self):
        return self.vida > 0

    def receber_golpe(self, golpe_id, origem, dano=1):
        if golpe_id == self.ultimo_golpe or self.morrendo:
            return False
        self.ultimo_golpe = golpe_id
        self.vida = max(0, self.vida - dano)
        self.piscar = 0.18
        self.atordoado = 0.15
        if self.investida is None:
            self.empurrar(origem, 85, 0.12)
        self.deformar(1.22, 0.78)
        if self.vida <= 0:
            self.morrendo = True
            self.tempo_morte = 1.2
            self.alertas.clear()
            self.rajada = None
            self.investida = None
        return True

    # ------------------------------------------------------------------ IA
    def atualizar_chefe(self, dt, nivel, jogador, projeteis, particulas, ondas, audio):
        self.tempo_vida += dt
        self.piscar = max(0.0, self.piscar - dt)
        self.atordoado = max(0.0, self.atordoado - dt)
        self.congelado = max(0.0, self.congelado - dt)
        self.anuncio_furia = max(0.0, self.anuncio_furia - dt)
        self.vida_exibida += (self.vida - self.vida_exibida) * min(1.0, dt * 3.0)
        self.atualizar_base(dt, nivel)

        if self.morrendo:
            self.tempo_morte -= dt
            if random.random() < 0.35:
                from efeitos import explosao
                cx = self.rect.centerx + random.uniform(-14, 14)
                cy = self.rect.centery + random.uniform(-14, 14)
                cor_a, cor_b = CORES_ELEMENTO.get(self.elemento, ((255, 90, 40), (255, 230, 90)))
                particulas += explosao((cx, cy), [cor_a, cor_b, (240, 240, 255)], 8)
                if audio and random.random() < 0.2:
                    audio.sfx("hit_inimigo")
            return

        qtd_antes = len(projeteis)
        self._atualizar_alertas(dt, projeteis, ondas, audio)
        self._atualizar_rajada(dt, projeteis, audio)

        # Fúria: metade da vida libera golpes mais rápidos e frequentes
        if not self.furia and self.vida <= self.vida_max * 0.5:
            from rpg import OndaMagica
            self.furia = True
            self.anuncio_furia = 2.0
            self.fator_poder *= 1.18
            self.velocidade_base *= 1.15
            self.tempo_especial = 0.8
            ondas.append(OndaMagica(self.rect.center, 70, (255, 70, 80), 0.6))
            if audio:
                audio.sfx("rugido_chefe")

        if self.investida is not None:
            self._atualizar_investida(dt, nivel, particulas)
            self._marcar_projeteis(projeteis, qtd_antes)
            return

        if self.atualizar_empurrao(dt, nivel) or self.congelado > 0:
            self._marcar_projeteis(projeteis, qtd_antes)
            return

        ate_j = pygame.Vector2(jogador.rect.center) - pygame.Vector2(self.rect.center)
        if abs(ate_j.x) > abs(ate_j.y):
            self.direcao_olhar = "direita" if ate_j.x > 0 else "esquerda"
        else:
            self.direcao_olhar = "baixo" if ate_j.y > 0 else "cima"

        self.tempo_especial -= dt
        if self.tempo_especial <= 0 and self.rajada is None and not self.alertas:
            tipo = self.especiais[self.indice_especial % len(self.especiais)]
            self.indice_especial += 1
            self.tempo_especial = (4.6 if self.furia else 7.5) / self.fator_poder
            self.iniciar_especial(tipo, jogador, ate_j, projeteis, audio)

        self.atualizar_comportamento(dt, nivel, jogador, ate_j, projeteis, particulas, ondas, audio)
        self._marcar_projeteis(projeteis, qtd_antes)

    def _marcar_projeteis(self, projeteis, qtd_antes):
        for p in projeteis[qtd_antes:]:
            if p.elemento is None:
                p.elemento = self.elemento

    def atualizar_comportamento(self, dt, nivel, jogador, ate_j, projeteis, particulas, ondas, audio):
        """Sobrescrito por cada chefe com seus padrões únicos de ataque."""
        pass

    # ------------------------------------------------------------------ golpes especiais
    def _projetil(self, pos, vel, **kw):
        kw.setdefault("dano", self.dano_contato)
        kw.setdefault("cor", CORES_ELEMENTO.get(self.elemento, ((255, 90, 60),))[0])
        return ProjetilChefe(pos, vel, elemento=self.elemento, **kw)

    def _alerta(self, pos, raio, tempo, acao, linha=None):
        self.alertas.append({"pos": pygame.Vector2(pos), "raio": raio, "t": tempo, "total": tempo, "acao": acao, "linha": linha})

    def iniciar_especial(self, tipo, jogador, ate_j, projeteis, audio):
        centro = pygame.Vector2(self.rect.center)
        alvo = pygame.Vector2(jogador.rect.center)
        direcao = ate_j.normalize() if ate_j.length_squared() > 0 else pygame.Vector2(0, 1)
        vel = 1.0 * self.fator_poder

        if tipo == "chuva":
            # Impactos telegrafados em volta do herói (círculos vermelhos no chão)
            qtd = 5 if self.furia else 3
            for i in range(qtd):
                desvio = pygame.Vector2() if i == 0 else pygame.Vector2(random.uniform(-34, 34), random.uniform(-26, 26))
                pos = alvo + desvio
                self._alerta(pos, 11, 0.95 + i * 0.12, lambda p, ps: self._explosao(p, ps))
            if audio:
                audio.sfx("magia_raio")
        elif tipo == "espiral":
            self.rajada = {"tipo": "espiral", "t": 1.6 if self.furia else 1.1, "passo": 0.0, "ang": random.uniform(0, 360)}
            if audio:
                audio.sfx("laser")
        elif tipo == "anel":
            # Dois anéis seguidos, o segundo girado para fechar os vãos
            def anel(p, ps, giro):
                for ang in range(0, 360, 30):
                    v = pygame.Vector2(1, 0).rotate(ang + giro) * (105 * vel)
                    ps.append(self._projetil(p, v, raio=4))
            self._alerta(centro, 22, 0.55, lambda p, ps: anel(p, ps, 0))
            self._alerta(centro, 0, 1.05, lambda p, ps: anel(pygame.Vector2(self.rect.center), ps, 15))
            if self.furia:
                self._alerta(centro, 0, 1.55, lambda p, ps: anel(pygame.Vector2(self.rect.center), ps, 7))
        elif tipo == "muralha":
            # Muralha de projéteis com um vão: o herói precisa achar a brecha
            lateral = direcao.rotate(90)
            vao = random.randint(-2, 2)

            def muralha(p, ps):
                for k in range(-5, 6):
                    if abs(k - vao) <= 1:
                        continue
                    ponto = pygame.Vector2(self.rect.center) + lateral * (k * 14)
                    ps.append(self._projetil(ponto, direcao * (90 * vel), raio=5, duracao=3.5))
            self._alerta(centro, 18, 0.7, muralha, linha=(lateral, 75))
        elif tipo == "investida":
            self.investida = {"preparo": 0.65, "duracao": 0.45, "dir": direcao}
            self.alertas.append({"pos": centro, "raio": 0, "t": 0.65, "total": 0.65, "acao": None, "linha": ("investida", direcao)})
            if audio:
                audio.sfx("rugido_chefe")
        elif tipo == "teleguiado":
            qtd = 4 if self.furia else 3
            for i in range(qtd):
                ang = -40 + i * (80 / max(1, qtd - 1))
                p = self._projetil(centro, direcao.rotate(ang) * (70 * vel), raio=5, duracao=4.0, estilo="orbe")
                p.alvo = jogador
                p.giro = 2.0
                projeteis.append(p)
            if audio:
                audio.sfx("magia_raio")

    def _explosao(self, pos, projeteis):
        projeteis.append(self._projetil(pos, (0, 0), raio=10, duracao=0.28, estilo="explosao"))
        for ang in range(0, 360, 90 if not self.furia else 60):
            v = pygame.Vector2(1, 0).rotate(ang + 45) * 70
            projeteis.append(self._projetil(pos, v, raio=3, duracao=0.6))

    def _atualizar_alertas(self, dt, projeteis, ondas, audio):
        restantes = []
        for a in self.alertas:
            a["t"] -= dt
            if a["t"] <= 0:
                if a["acao"]:
                    a["acao"](a["pos"], projeteis)
                    if audio and a["raio"] > 0:
                        audio.sfx("impacto_pesado")
            else:
                restantes.append(a)
        self.alertas = restantes

    def _atualizar_rajada(self, dt, projeteis, audio):
        r = self.rajada
        if r is None:
            return
        r["t"] -= dt
        r["passo"] -= dt
        while r["passo"] <= 0 and r["t"] > 0:
            r["passo"] += 0.075
            r["ang"] += 23
            for k in (0, 180) if not self.furia else (0, 120, 240):
                v = pygame.Vector2(1, 0).rotate(r["ang"] + k) * (115 * self.fator_poder)
                projeteis.append(self._projetil(self.rect.center, v, raio=4))
        if r["t"] <= 0:
            self.rajada = None

    def _atualizar_investida(self, dt, nivel, particulas):
        inv = self.investida
        if inv["preparo"] > 0:
            inv["preparo"] -= dt
            self.deformar(0.86, 1.12)
            return
        inv["duracao"] -= dt
        bateu = self.mover(inv["dir"] * (270 * self.fator_poder * dt), nivel)
        if random.random() < 0.6:
            from efeitos import explosao
            cor_a, cor_b = CORES_ELEMENTO.get(self.elemento, ((255, 255, 255), (255, 255, 255)))
            particulas += explosao(self.rect.midbottom, [cor_a, cor_b], 2)
        if inv["duracao"] <= 0 or bateu:
            self.investida = None
            self.deformar(1.25, 0.8)

    # ------------------------------------------------------------------ desenho
    def desenhar_chefe(self, tela, camera, gfx, fonte):
        """Desenho 16-bits do chefe (arte em arte_chefes.py)."""
        ox, oy = camera.offset
        arte = ARTE.get(self.id_chefe)
        if arte:
            arte(self, tela, self.rect.centerx - ox, self.rect.bottom - oy, self.tempo_vida)

    def _desenhar_alertas(self, tela, camera):
        ox, oy = camera.offset
        for a in self.alertas:
            prog = 1 - a["t"] / max(0.01, a["total"])
            pisca = int(a["t"] * 12) % 2 == 0
            cor = (255, 60, 60) if pisca else (255, 200, 80)
            px, py = round(a["pos"].x - ox), round(a["pos"].y - oy)
            linha = a.get("linha")
            if linha and linha[0] == "investida":
                fim = a["pos"] + linha[1] * 120
                pygame.draw.line(tela, cor, (px, py), (round(fim.x - ox), round(fim.y - oy)), 1 + round(prog * 2))
                continue
            if linha:
                lateral, metade = linha
                p1 = a["pos"] - lateral * metade
                p2 = a["pos"] + lateral * metade
                pygame.draw.line(tela, cor, (round(p1.x - ox), round(p1.y - oy)), (round(p2.x - ox), round(p2.y - oy)), 1)
            if a["raio"] > 0:
                raio = a["raio"]
                camada = pygame.Surface((raio * 2 + 2, raio + 2), pygame.SRCALPHA)
                pygame.draw.ellipse(camada, (*cor, round(60 + prog * 90)), (0, 0, raio * 2 + 2, raio + 2))
                tela.blit(camada, (px - raio - 1, py - raio // 2 - 1))
                interno = max(1, round(raio * prog))
                pygame.draw.ellipse(tela, (255, 240, 200), (px - interno, py - interno // 2, interno * 2, max(2, interno)), 1)

    def desenhar(self, tela, camera, gfx, fonte=None):
        ox, oy = camera.offset
        self._desenhar_alertas(tela, camera)

        # Aura elemental pulsante no chão
        cor_aura = (255, 60, 70) if self.furia and int(self.tempo_vida * 6) % 2 == 0 else self.cor_aura
        raio_aura = 20 + round(math.sin(self.tempo_vida * 4) * 2) + (4 if self.furia else 0)
        aura = pygame.Surface((raio_aura * 2, raio_aura), pygame.SRCALPHA)
        pygame.draw.ellipse(aura, (*cor_aura[:3], 70), aura.get_rect())
        pygame.draw.ellipse(aura, (*cor_aura[:3], 140), aura.get_rect(), 1)
        tela.blit(aura, (self.rect.centerx - ox - raio_aura, self.rect.bottom - oy - raio_aura // 2 - 1))
        self.desenhar_sombra(tela, camera, gfx)

        # Desenha a arte numa Surface própria para aplicar contorno, clarão e fúria
        larg, alt = self.LARG_ARTE, self.ALT_ARTE
        ax, ay = larg // 2, alt - 14
        corpo = pygame.Surface((larg, alt), pygame.SRCALPHA)
        self.desenhar_chefe(corpo, _CameraLocal((self.rect.centerx - ax, self.rect.bottom - ay)), gfx, fonte)
        if self.direcao_olhar == "esquerda":
            corpo = pygame.transform.flip(corpo, True, False)

        mascara = pygame.mask.from_surface(corpo)
        final = pygame.Surface((larg, alt), pygame.SRCALPHA)
        contorno = mascara.to_surface(setcolor=(12, 8, 20, 255), unsetcolor=(0, 0, 0, 0))
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            final.blit(contorno, (dx, dy))
        final.blit(corpo, (0, 0))

        if self.piscar > 0:
            branco = mascara.to_surface(setcolor=(255, 255, 255, 210), unsetcolor=(0, 0, 0, 0))
            final.blit(branco, (0, 0))
        elif self.furia and math.sin(self.tempo_vida * 10) > 0.3:
            vermelho = mascara.to_surface(setcolor=(255, 40, 40, 70), unsetcolor=(0, 0, 0, 0))
            final.blit(vermelho, (0, 0))
        if self.fantasma:
            roxo = mascara.to_surface(setcolor=(170, 60, 255, 90), unsetcolor=(0, 0, 0, 0))
            final.blit(roxo, (0, 0))
            final.set_alpha(215)
        if self.morrendo:
            final.set_alpha(max(40, round(255 * self.tempo_morte / 1.2)))

        # Squash & stretch ancorado nos pés
        sx, sy = getattr(self, "escala_x", 1.0), getattr(self, "escala_y", 1.0)
        if abs(sx - 1) > 0.02 or abs(sy - 1) > 0.02:
            final = pygame.transform.scale(final, (max(4, round(larg * sx)), max(4, round(alt * sy))))
            ax, ay = round(ax * sx), round(ay * sy)
        tela.blit(final, (self.rect.centerx - ox - ax, self.rect.bottom - oy - ay))

    def desenhar_barra_vida_hud(self, tela, fonte):
        """Barra de vida do chefe com moldura 16-bits, dano recente e marcador da fúria."""
        larg_barra = 170
        alt_barra = 7
        x = (LARGURA - larg_barra) // 2
        y = 5
        painel = pygame.Rect(x - 6, y - 3, larg_barra + 12, alt_barra + 20)
        desenhar_painel(tela, painel, "perigo" if self.furia else "padrao", alfa=225, cantos=False)

        pygame.draw.rect(tela, (12, 6, 14), (x - 1, y - 1, larg_barra + 2, alt_barra + 2))
        prop = max(0.0, min(1.0, self.vida / max(1, self.vida_max)))
        prop_ex = max(prop, min(1.0, self.vida_exibida / max(1, self.vida_max)))
        if prop_ex > prop:
            pygame.draw.rect(tela, (255, 236, 170), (x, y, round(larg_barra * prop_ex), alt_barra))
        if prop > 0:
            larg_preench = round(larg_barra * prop)
            cor_vida = (225, 45, 65) if not self.furia else (255, 90, 40)
            pygame.draw.rect(tela, cor_vida, (x, y, larg_preench, alt_barra))
            pygame.draw.line(tela, (255, 190, 170), (x, y), (x + larg_preench - 1, y))
            pygame.draw.line(tela, (120, 20, 30), (x, y + alt_barra - 1), (x + larg_preench - 1, y + alt_barra - 1))
        # Marcador da metade (fúria)
        meio = x + larg_barra // 2
        pygame.draw.line(tela, (255, 220, 120), (meio, y - 1), (meio, y + alt_barra))

        rotulo = f"{self.nome}  Nv{self.nivel_chefe}"
        cor_rot = (255, 150, 120) if self.furia else (255, 230, 140)
        desenhar_texto(tela, fonte, rotulo, (LARGURA // 2, y + alt_barra + 6), cor_rot, centro=True)
        if self.anuncio_furia > 0 and int(self.anuncio_furia * 6) % 2 == 0:
            desenhar_texto(tela, fonte, "FÚRIA!", (LARGURA // 2, y + alt_barra + 18), (255, 80, 60), centro=True)


# =====================================================================
# 15 CHEFÕES ÚNICOS DO MUNDO
# =====================================================================

class ReiSlime(Chefe):
    """Chefe 1 (Covil do Rei Slime): Slime Real Gigante com coroa rubi e saltos sísmicos."""

    def __init__(self, x, y, fantasma=False):
        super().__init__(x, y, 24, 18, "rei_slime", "Rei Slime", "Soberano dos Bosques", 26, (120, 215, 255), nivel_minimo=1)
        self.fantasma = fantasma
        self.velocidade_base = 55.0
        self.fase_salto = 0.0

    def atualizar_comportamento(self, dt, nivel, jogador, ate_j, projeteis, particulas, ondas, audio):
        from rpg import OndaMagica
        self.fase_salto += dt * (4.5 * self.fator_poder)
        dist = ate_j.length()

        self.tempo_ataque -= dt
        if self.tempo_ataque <= 0:
            self.tempo_ataque = random.uniform(2.4, 3.4) / self.fator_poder
            # Salto sísmico com onda de choque
            self.pular(155.0)
            if audio:
                audio.sfx("rugido_chefe")

        if self.acabou_de_pousar:
            ondas.append(OndaMagica(self.rect.center, 44, (110, 215, 255), 0.45))
            if audio:
                audio.sfx("impacto_pesado")
            # Dispara 6 projéteis de gosma em círculo
            for ang in range(0, 360, 60):
                rad = math.radians(ang)
                vel = pygame.Vector2(math.cos(rad), math.sin(rad)) * (95.0 * self.fator_poder)
                projeteis.append(ProjetilChefe(self.rect.center, vel, dano=self.dano_contato, raio=4, cor=(75, 175, 245)))

        if dist > 8 and self.no_ar:
            self.mover(ate_j.normalize() * (self.velocidade_base * 1.5 * dt * self.fator_poder), nivel)
        elif dist > 8:
            self.mover(ate_j.normalize() * (self.velocidade_base * 0.6 * dt), nivel)

class GolemPedra(Chefe):
    """Chefe 2 (Câmara do Golem Ancestral): Titã de pedra com runas celestes e socos de terra."""

    def __init__(self, x, y, fantasma=False):
        super().__init__(x, y, 26, 26, "golem_pedra", "Golem de Pedra", "Guardião das Ruínas", 32, (150, 165, 190), nivel_minimo=2)
        self.fantasma = fantasma

    def atualizar_comportamento(self, dt, nivel, jogador, ate_j, projeteis, particulas, ondas, audio):
        from rpg import OndaMagica
        dist = ate_j.length()
        self.tempo_ataque -= dt

        if self.tempo_ataque <= 0:
            self.tempo_ataque = random.uniform(2.8, 3.8) / self.fator_poder
            # Soco no chão com estacas em 4 direções
            ondas.append(OndaMagica(self.rect.center, 42, (180, 175, 160), 0.4))
            if audio:
                audio.sfx("impacto_pesado")
            for dir_v in (pygame.Vector2(1, 0), pygame.Vector2(-1, 0), pygame.Vector2(0, 1), pygame.Vector2(0, -1)):
                projeteis.append(ProjetilChefe(self.rect.center, dir_v * (115.0 * self.fator_poder), dano=self.dano_contato, raio=5, cor=(145, 140, 135)))

        if dist > 14:
            self.mover(ate_j.normalize() * (self.velocidade_base * dt * self.fator_poder), nivel)

class SerpenteDunas(Chefe):
    """Chefe 3 (Fosso das Dunas): Leviatã arenoso com baforada de fogo e areia abrasiva."""

    def __init__(self, x, y, fantasma=False):
        super().__init__(x, y, 22, 22, "serpente_dunas", "Serpente das Dunas", "Terror do Deserto", 28, (245, 190, 85), nivel_minimo=3)
        self.fantasma = fantasma
        self.submersa = 0.0

    def atualizar_comportamento(self, dt, nivel, jogador, ate_j, projeteis, particulas, ondas, audio):
        self.tempo_ataque -= dt
        if self.tempo_ataque <= 0:
            self.tempo_ataque = random.uniform(3.0, 4.0) / self.fator_poder
            if audio:
                audio.sfx("rugido_chefe")
            # Dispara 3 bolas de fogo e areia em cone
            dir_base = ate_j.normalize() if ate_j.length() > 0 else pygame.Vector2(1, 0)
            for ang in (-25, 0, 25):
                vel = dir_base.rotate(ang) * (130.0 * self.fator_poder)
                projeteis.append(ProjetilChefe(self.rect.center, vel, dano=self.dano_contato, raio=5, cor=(255, 130, 45)))

        if ate_j.length() > 16:
            self.mover(ate_j.normalize() * (self.velocidade_base * 1.25 * dt * self.fator_poder), nivel)

class ColossoSolar(Chefe):
    """Chefe 4 (Altar Solar das Chamas): Guerreiro dourado com feixe de chamas e disco solar."""

    def __init__(self, x, y, fantasma=False):
        super().__init__(x, y, 24, 28, "colosso_solar", "Colosso Solar", "Campeão do Sol", 32, (255, 220, 70), nivel_minimo=4)
        self.fantasma = fantasma

    def atualizar_comportamento(self, dt, nivel, jogador, ate_j, projeteis, particulas, ondas, audio):
        self.tempo_ataque -= dt
        if self.tempo_ataque <= 0:
            self.tempo_ataque = random.uniform(2.6, 3.6) / self.fator_poder
            if audio:
                audio.sfx("laser")
            # Explosão solar em 8 direções
            for ang in range(0, 360, 45):
                rad = math.radians(ang)
                vel = pygame.Vector2(math.cos(rad), math.sin(rad)) * (120.0 * self.fator_poder)
                projeteis.append(ProjetilChefe(self.rect.center, vel, dano=self.dano_contato, raio=4, cor=(255, 225, 80)))

        if ate_j.length() > 20:
            self.mover(ate_j.normalize() * (self.velocidade_base * 0.95 * dt * self.fator_poder), nivel)

class BruxaBrumas(Chefe):
    """Chefe 5 (Antro da Bruxa): Feiticeira com orbes venenosos e névoa espectral."""

    def __init__(self, x, y, fantasma=False):
        super().__init__(x, y, 20, 24, "bruxa_brumas", "Bruxa das Brumas", "Senhora dos Pântanos", 28, (140, 65, 220), nivel_minimo=5)
        self.fantasma = fantasma

    def atualizar_comportamento(self, dt, nivel, jogador, ate_j, projeteis, particulas, ondas, audio):
        self.tempo_ataque -= dt
        if self.tempo_ataque <= 0:
            self.tempo_ataque = random.uniform(2.3, 3.3) / self.fator_poder
            if audio:
                audio.sfx("magia_raio")
            # 4 orbes venenosos teleguiados lentos
            dir_v = ate_j.normalize() if ate_j.length() > 0 else pygame.Vector2(0, 1)
            for a in (-32, -10, 10, 32):
                projeteis.append(ProjetilChefe(self.rect.center, dir_v.rotate(a) * (90.0 * self.fator_poder), dano=self.dano_contato, raio=4, cor=(165, 70, 245)))

        if ate_j.length() > 32:
            self.mover(ate_j.normalize() * (self.velocidade_base * dt * self.fator_poder), nivel)

class CeifadorEspectral(Chefe):
    """Chefe 6 (Sepulcro Espectral): Espectro com foice das almas e lâminas cortantes."""

    def __init__(self, x, y, fantasma=False):
        super().__init__(x, y, 22, 26, "ceifador_espectral", "Ceifador Espectral", "Ceifador de Almas", 30, (90, 220, 235), nivel_minimo=6)
        self.fantasma = fantasma

    def atualizar_comportamento(self, dt, nivel, jogador, ate_j, projeteis, particulas, ondas, audio):
        from rpg import OndaMagica
        self.tempo_ataque -= dt
        if self.tempo_ataque <= 0:
            self.tempo_ataque = random.uniform(2.3, 3.2) / self.fator_poder
            if audio:
                audio.sfx("magia_corte")
            ondas.append(OndaMagica(self.rect.center, 46, (90, 225, 240), 0.35))
            dir_v = ate_j.normalize() if ate_j.length() > 0 else pygame.Vector2(0, 1)
            projeteis.append(ProjetilChefe(self.rect.center, dir_v * (145.0 * self.fator_poder), dano=self.dano_contato, raio=5, cor=(120, 245, 255)))

        if ate_j.length() > 14:
            self.mover(ate_j.normalize() * (self.velocidade_base * 1.15 * dt * self.fator_poder), nivel)

class LeviataAquatico(Chefe):
    """Chefe 7 (Abismo Aquático): Serpente marítima com jatos d'água perfurantes."""

    def __init__(self, x, y, fantasma=False):
        super().__init__(x, y, 26, 22, "leviata_aquatico", "Leviatã Aquático", "Lorde das Marés", 34, (60, 160, 255), nivel_minimo=7)
        self.fantasma = fantasma

    def atualizar_comportamento(self, dt, nivel, jogador, ate_j, projeteis, particulas, ondas, audio):
        self.tempo_ataque -= dt
        if self.tempo_ataque <= 0:
            self.tempo_ataque = random.uniform(2.6, 3.6) / self.fator_poder
            if audio:
                audio.sfx("nado")
            dir_v = ate_j.normalize() if ate_j.length() > 0 else pygame.Vector2(1, 0)
            for a in (-22, 0, 22):
                projeteis.append(ProjetilChefe(self.rect.center, dir_v.rotate(a) * (135.0 * self.fator_poder), dano=self.dano_contato, raio=5, cor=(90, 195, 255)))

        if ate_j.length() > 16:
            self.mover(ate_j.normalize() * (self.velocidade_base * dt * self.fator_poder), nivel)

class GuardiaoDiamante(Chefe):
    """Chefe 8 (Núcleo de Cristal): Prisma geométrico que refrata feixes laser."""

    def __init__(self, x, y, fantasma=False):
        super().__init__(x, y, 24, 24, "guardiao_diamante", "Guardião dos Cristais", "Prisma Eterno", 32, (180, 245, 255), nivel_minimo=8)
        self.fantasma = fantasma

    def atualizar_comportamento(self, dt, nivel, jogador, ate_j, projeteis, particulas, ondas, audio):
        self.tempo_ataque -= dt
        if self.tempo_ataque <= 0:
            self.tempo_ataque = random.uniform(2.8, 3.8) / self.fator_poder
            if audio:
                audio.sfx("laser")
            # 6 feixes de cristal prismáticos
            for ang in range(0, 360, 60):
                rad = math.radians(ang + self.tempo_vida * 30)
                vel = pygame.Vector2(math.cos(rad), math.sin(rad)) * (115.0 * self.fator_poder)
                projeteis.append(ProjetilChefe(self.rect.center, vel, dano=self.dano_contato, raio=4, cor=(215, 245, 255)))

        if ate_j.length() > 22:
            self.mover(ate_j.normalize() * (self.velocidade_base * 0.85 * dt * self.fator_poder), nivel)

class TrollRochas(Chefe):
    """Chefe 9 (Covil do Troll): Gigante das cavernas com clava pesada e tremor de terra."""

    def __init__(self, x, y, fantasma=False):
        super().__init__(x, y, 28, 26, "troll_rochas", "Troll das Cavernas", "Bruto das Montanhas", 36, (185, 130, 80), nivel_minimo=9)
        self.fantasma = fantasma

    def atualizar_comportamento(self, dt, nivel, jogador, ate_j, projeteis, particulas, ondas, audio):
        from rpg import OndaMagica
        self.tempo_ataque -= dt
        if self.tempo_ataque <= 0:
            self.tempo_ataque = random.uniform(3.0, 4.0) / self.fator_poder
            if audio:
                audio.sfx("impacto_pesado")
            ondas.append(OndaMagica(self.rect.center, 48, (195, 145, 90), 0.45))
            dir_v = ate_j.normalize() if ate_j.length() > 0 else pygame.Vector2(0, 1)
            projeteis.append(ProjetilChefe(self.rect.center, dir_v * (110.0 * self.fator_poder), dano=self.dano_contato, raio=6, cor=(165, 115, 75)))

        if ate_j.length() > 14:
            self.mover(ate_j.normalize() * (self.velocidade_base * dt * self.fator_poder), nivel)

class YetiGlacial(Chefe):
    """Chefe 10 (Caverna Glacial do Yeti): Besta albina que congela o ar e atira estacas de gelo."""

    def __init__(self, x, y, fantasma=False):
        super().__init__(x, y, 26, 26, "yeti_glacial", "Yeti Glacial", "Guardião das Neves", 34, (220, 245, 255), nivel_minimo=10)
        self.fantasma = fantasma

    def atualizar_comportamento(self, dt, nivel, jogador, ate_j, projeteis, particulas, ondas, audio):
        self.tempo_ataque -= dt
        if self.tempo_ataque <= 0:
            self.tempo_ataque = random.uniform(2.6, 3.6) / self.fator_poder
            if audio:
                audio.sfx("magia_gelo")
            dir_v = ate_j.normalize() if ate_j.length() > 0 else pygame.Vector2(0, 1)
            for a in (-35, -15, 0, 15, 35):
                projeteis.append(ProjetilChefe(self.rect.center, dir_v.rotate(a) * (120.0 * self.fator_poder), dano=self.dano_contato, raio=4, cor=(160, 235, 255)))

        if ate_j.length() > 16:
            self.mover(ate_j.normalize() * (self.velocidade_base * dt * self.fator_poder), nivel)

class ValquiriaCaida(Chefe):
    """Chefe 11 (Altar da Valquíria): Guerreira alada com lanças de luz sagrada."""

    def __init__(self, x, y, fantasma=False):
        super().__init__(x, y, 22, 26, "valquiria_caida", "Valquíria Sombria", "Juíza Celeste", 36, (255, 235, 120), nivel_minimo=11)
        self.fantasma = fantasma

    def atualizar_comportamento(self, dt, nivel, jogador, ate_j, projeteis, particulas, ondas, audio):
        self.tempo_ataque -= dt
        if self.tempo_ataque <= 0:
            self.tempo_ataque = random.uniform(2.4, 3.4) / self.fator_poder
            if audio:
                audio.sfx("magia_raio")
            dir_v = ate_j.normalize() if ate_j.length() > 0 else pygame.Vector2(0, 1)
            for a in (-25, 0, 25):
                projeteis.append(ProjetilChefe(self.rect.center, dir_v.rotate(a) * (150.0 * self.fator_poder), dano=self.dano_contato, raio=4, cor=(255, 240, 140)))

        if ate_j.length() > 16:
            self.mover(ate_j.normalize() * (self.velocidade_base * 1.2 * dt * self.fator_poder), nivel)

class CavaleiroNegro(Chefe):
    """Chefe 12 (Arena do Cavaleiro): Guerreiro blindado com zweihander sombria."""

    def __init__(self, x, y, fantasma=False):
        super().__init__(x, y, 24, 28, "cavaleiro_negro", "Cavaleiro Negro", "Campeão das Trevas", 40, (180, 45, 65), nivel_minimo=12)
        self.fantasma = fantasma

    def atualizar_comportamento(self, dt, nivel, jogador, ate_j, projeteis, particulas, ondas, audio):
        from rpg import OndaMagica
        self.tempo_ataque -= dt
        if self.tempo_ataque <= 0:
            self.tempo_ataque = random.uniform(2.5, 3.5) / self.fator_poder
            if audio:
                audio.sfx("espada")
            ondas.append(OndaMagica(self.rect.center, 46, (220, 50, 75), 0.35))
            dir_v = ate_j.normalize() if ate_j.length() > 0 else pygame.Vector2(1, 0)
            projeteis.append(ProjetilChefe(self.rect.center, dir_v * (155.0 * self.fator_poder), dano=self.dano_contato, raio=5, cor=(235, 45, 65)))

        if ate_j.length() > 14:
            self.mover(ate_j.normalize() * (self.velocidade_base * 1.15 * dt * self.fator_poder), nivel)

class QuimeraAbissal(Chefe):
    """Chefe 13 (Fosso da Quimera): Monstro tricéfalo com baforada de fogo e veneno."""

    def __init__(self, x, y, fantasma=False):
        super().__init__(x, y, 26, 26, "quimera_abissal", "Quimera Abissal", "Monstro dos Calabouços", 38, (215, 80, 50), nivel_minimo=13)
        self.fantasma = fantasma

    def atualizar_comportamento(self, dt, nivel, jogador, ate_j, projeteis, particulas, ondas, audio):
        self.tempo_ataque -= dt
        if self.tempo_ataque <= 0:
            self.tempo_ataque = random.uniform(2.6, 3.6) / self.fator_poder
            if audio:
                audio.sfx("rugido_chefe")
            dir_v = ate_j.normalize() if ate_j.length() > 0 else pygame.Vector2(0, 1)
            for a in (-30, -10, 10, 30):
                projeteis.append(ProjetilChefe(self.rect.center, dir_v.rotate(a) * (125.0 * self.fator_poder), dano=self.dano_contato, raio=5, cor=(255, 95, 45)))

        if ate_j.length() > 16:
            self.mover(ate_j.normalize() * (self.velocidade_base * dt * self.fator_poder), nivel)

class ArquimagoCorrompido(Chefe):
    """Chefe 14 (Observatório do Arquimago): Sábio das sombras com chuva de raios e esferas místicas."""

    def __init__(self, x, y, fantasma=False):
        super().__init__(x, y, 22, 26, "arquimago", "Arquimago Corrompido", "Grão-Mestre Proibido", 42, (175, 80, 255), nivel_minimo=14)
        self.fantasma = fantasma

    def atualizar_comportamento(self, dt, nivel, jogador, ate_j, projeteis, particulas, ondas, audio):
        self.tempo_ataque -= dt
        if self.tempo_ataque <= 0:
            self.tempo_ataque = random.uniform(2.1, 3.0) / self.fator_poder
            if audio:
                audio.sfx("magia_raio")
            # 8 projéteis arcanos em espiral
            for ang in range(0, 360, 45):
                rad = math.radians(ang + self.tempo_vida * 45)
                vel = pygame.Vector2(math.cos(rad), math.sin(rad)) * (130.0 * self.fator_poder)
                projeteis.append(ProjetilChefe(self.rect.center, vel, dano=self.dano_contato, raio=4, cor=(190, 85, 255)))

        if ate_j.length() > 28:
            self.mover(ate_j.normalize() * (self.velocidade_base * 0.95 * dt * self.fator_poder), nivel)

class PaladinoJuizo(Chefe):
    """Chefe 15 (Tribunal do Paladino): Guardião divino profanado com martelo do juízo."""

    def __init__(self, x, y, fantasma=False):
        super().__init__(x, y, 26, 28, "paladino_juizo", "Paladino do Juízo", "Guardião do Selo Final", 46, (255, 215, 90), nivel_minimo=15)
        self.fantasma = fantasma

    def atualizar_comportamento(self, dt, nivel, jogador, ate_j, projeteis, particulas, ondas, audio):
        from rpg import OndaMagica
        self.tempo_ataque -= dt
        if self.tempo_ataque <= 0:
            self.tempo_ataque = random.uniform(2.3, 3.2) / self.fator_poder
            if audio:
                audio.sfx("impacto_pesado")
            ondas.append(OndaMagica(self.rect.center, 54, (255, 230, 110), 0.45))
            # 4 feixes de martelo sagrado
            for d in (pygame.Vector2(1, 0), pygame.Vector2(-1, 0), pygame.Vector2(0, 1), pygame.Vector2(0, -1)):
                projeteis.append(ProjetilChefe(self.rect.center, d * (145.0 * self.fator_poder), dano=self.dano_contato, raio=5, cor=(255, 240, 130)))

        if ate_j.length() > 14:
            self.mover(ate_j.normalize() * (self.velocidade_base * dt * self.fator_poder), nivel)



# =====================================================================
# CHEFE FINAL: A ENTIDADE MALIGNA (O SOBERANO DAS TREVAS)
# =====================================================================

class EntidadeMalignaChefe(Chefe):
    """O CHEFE FINAL do jogo no Salão do Trono com 2 Fases dramáticas."""

    def __init__(self, x, y):
        super().__init__(x, y, 38, 34, "entidade_maligna", "A ENTIDADE MALIGNA", "Soberano do Apocalipse", 70, (235, 45, 95), nivel_minimo=15)
        self.fase = 1
        self.timer_magia = 0.5
        self.velocidade_base = 34.0

    def atualizar_comportamento(self, dt, nivel, jogador, ate_j, projeteis, particulas, ondas, audio):
        from rpg import OndaMagica
        dist = ate_j.length()

        # Transição de fase na metade da vida máxima
        if self.fase == 1 and self.vida <= (self.vida_max // 2):
            self.fase = 2
            self.timer_magia = 0.2
            ondas.append(OndaMagica(self.rect.center, 75, (255, 50, 110), 0.6))
            if audio:
                audio.sfx("rugido_chefe")

        self.timer_magia -= dt
        if self.timer_magia <= 0:
            if self.fase == 1:
                self.timer_magia = random.uniform(1.6, 2.4) / self.fator_poder
                if audio:
                    audio.sfx("magia_fogo")
                # Onda quádrupla de fogo abissal teleguiado
                dir_v = ate_j.normalize() if dist > 0 else pygame.Vector2(0, 1)
                for a in (-40, -15, 15, 40):
                    projeteis.append(ProjetilChefe(self.rect.center, dir_v.rotate(a) * (120.0 * self.fator_poder), dano=self.dano_contato, raio=5, cor=(255, 60, 95)))
            else:
                # Fase 2: Chuva infernal em espiral bullet-hell
                self.timer_magia = random.uniform(0.9, 1.5) / self.fator_poder
                if audio:
                    audio.sfx("laser")
                ondas.append(OndaMagica(self.rect.center, 58, (255, 80, 140), 0.4))
                for ang in range(0, 360, 36):
                    rad = math.radians(ang + self.tempo_vida * 60)
                    vel = pygame.Vector2(math.cos(rad), math.sin(rad)) * (135.0 * self.fator_poder)
                    projeteis.append(ProjetilChefe(self.rect.center, vel, dano=self.dano_contato, raio=5, cor=(255, 35, 75)))

        if dist > 24:
            self.mover(ate_j.normalize() * (self.velocidade_base * dt * self.fator_poder), nivel)



# Catálogo com a fábrica de todos os chefes
CRIADORES_CHEFES = {
    "rei_slime": ReiSlime,
    "golem_pedra": GolemPedra,
    "serpente_dunas": SerpenteDunas,
    "colosso_solar": ColossoSolar,
    "bruxa_brumas": BruxaBrumas,
    "ceifador_espectral": CeifadorEspectral,
    "leviata_aquatico": LeviataAquatico,
    "guardiao_diamante": GuardiaoDiamante,
    "troll_rochas": TrollRochas,
    "yeti_glacial": YetiGlacial,
    "valquiria_caida": ValquiriaCaida,
    "cavaleiro_negro": CavaleiroNegro,
    "quimera_abissal": QuimeraAbissal,
    "arquimago": ArquimagoCorrompido,
    "paladino_juizo": PaladinoJuizo,
    "entidade_maligna": EntidadeMalignaChefe,
}
