import math

import pygame

from entidade import Entidade
from personagens import QUADRO
from settings import (
    TEMPO_ATAQUE,
    TEMPO_INVENCIVEL,
    TILE,
    VELOCIDADE_JOGADOR,
    VIDA_MAXIMA,
)

DIAG = 0.7071067811865475  # 1 / sqrt(2)

VETORES = {
    "cima": pygame.Vector2(0, -1),
    "baixo": pygame.Vector2(0, 1),
    "esquerda": pygame.Vector2(-1, 0),
    "direita": pygame.Vector2(1, 0),
    "cima_esquerda": pygame.Vector2(-DIAG, -DIAG),
    "cima_direita": pygame.Vector2(DIAG, -DIAG),
    "baixo_esquerda": pygame.Vector2(-DIAG, DIAG),
    "baixo_direita": pygame.Vector2(DIAG, DIAG),
}

MAPA_DIRECOES_8 = {
    (0, -1): "cima",
    (0, 1): "baixo",
    (-1, 0): "esquerda",
    (1, 0): "direita",
    (-1, -1): "cima_esquerda",
    (1, -1): "cima_direita",
    (-1, 1): "baixo_esquerda",
    (1, 1): "baixo_direita",
}

ANGULO_BASE_ESPADA = {
    "cima": 0,
    "baixo": 180,
    "direita": -90,
    "esquerda": 90,
    "cima_direita": -45,
    "cima_esquerda": 45,
    "baixo_direita": -135,
    "baixo_esquerda": 135,
}


_CACHE_TUNICAS = {}


def _aplicar_tunica(img, tunica_id):
    if tunica_id == "tunica_verde":
        return img
    chave = (id(img), tunica_id)
    if chave in _CACHE_TUNICAS:
        return _CACHE_TUNICAS[chave]

    surf = img.copy()
    w, h = surf.get_size()
    if tunica_id == "armadura_carmesim":
        cor_clara, cor_escura = (195, 48, 58), (128, 30, 38)
    elif tunica_id == "manto_astral":
        cor_clara, cor_escura = (70, 145, 235), (38, 85, 175)
    else:
        return img

    for y in range(h):
        for x in range(w):
            p = surf.get_at((x, y))
            if p.a > 0:
                if (70 <= p.r <= 105 and 150 <= p.g <= 200 and 45 <= p.b <= 80):
                    surf.set_at((x, y), (*cor_clara, p.a))
                elif (40 <= p.r <= 65 and 95 <= p.g <= 135 and 35 <= p.b <= 65):
                    surf.set_at((x, y), (*cor_escura, p.a))

    _CACHE_TUNICAS[chave] = surf
    return surf


class Jogador(Entidade):
    def __init__(self, x, y):
        super().__init__(x, y, 10, 6)
        self.direcao = "baixo"
        self.pode_nadar = True
        self.vida_maxima = VIDA_MAXIMA
        self.vida = VIDA_MAXIMA
        self.fator_velocidade_rpg = 1.0
        self.tempo_ataque = 0.0
        self.golpe_id = 0  # cada golpe tem um id, para acertar cada inimigo só uma vez
        self.invencivel = 0.0
        self.anim = 0.0
        self.andando = False
        self.correndo = False
        self.tempo_dash = 0.0
        self.recarga_dash = 0.0
        self.vel_atual = pygame.Vector2()
        self.rastros = []  # fantasmas deixados durante o dash
        self.timer_rastro = 0.0
        self.timer_manter_diagonal = 0.0
        self.impulso_ataque = False
        self.cama_pos = None

        # Equipamentos (Pilar 1)
        self.defendendo = False
        self.escudo_equipado = "nenhum"
        self.tunica_equipada = "tunica_verde"
        self.arma_equipada = "espada_ferro"

        # Sistema Hack & Slash (Combos, Buffering e Cancelamentos)
        self.combo_etapa = 0  # 0: corte ágil, 1: corte cruzado, 2: finalizador giratório 360°
        self.tempo_combo_janela = 0.0
        self.buffer_ataque = False
        self.duracao_ataque_atual = 0.16
        self.dash_strike = False
        self.fator_frenesi = 1.0

        # Stamina (Estilo Soulslike)
        self.rpg = None
        self._stamina = 60.0
        self._stamina_maxima = 60.0

    @property
    def stamina(self):
        return self.rpg.stamina if self.rpg else self._stamina

    @stamina.setter
    def stamina(self, valor):
        if self.rpg:
            self.rpg.stamina = float(valor)
        else:
            self._stamina = float(valor)

    @property
    def stamina_maxima(self):
        return self.rpg.stamina_maxima if self.rpg else self._stamina_maxima

    @property
    def atacando(self):
        return self.tempo_ataque > 0

    def atacar(self):
        if self.tempo_empurrao > 0 or self.pose != "normal":
            return

        if self.tempo_dash > 0:
            custo_stamina = 22.0
        elif self.tempo_combo_janela > 0:
            etapa_prevista = (self.combo_etapa + 1) % 3
            custo_stamina = 16.0 if etapa_prevista == 1 else 24.0
        else:
            custo_stamina = 14.0

        if self.rpg and not self.rpg.pode_gastar_stamina(custo_stamina):
            return

        if self.atacando:
            # Buffer de input nos últimos 0.11s do golpe para encadear sem perder frame
            if self.tempo_ataque <= 0.11:
                self.buffer_ataque = True
            return

        # Solta o escudo para atacar de imediato se estiver defendendo
        self.defendendo = False

        if self.rpg:
            self.rpg.gastar_stamina(custo_stamina)

        if self.tempo_dash > 0:
            # Dash-Strike (Estocada de Choque em arrancada)
            self.dash_strike = True
            self.combo_etapa = 0
            self.duracao_ataque_atual = 0.16
            self.tempo_ataque = self.duracao_ataque_atual
            self.golpe_id += 1
            self.impulso_ataque = True
            self.deformar(1.32, 0.70)
            return

        self.dash_strike = False
        if self.tempo_combo_janela > 0:
            self.combo_etapa = (self.combo_etapa + 1) % 3
        else:
            self.combo_etapa = 0

        # Tempos frenéticos: 0.15s, 0.16s, 0.24s (Finalizador)
        duracoes = (0.15, 0.16, 0.24)
        self.duracao_ataque_atual = duracoes[self.combo_etapa]
        self.tempo_ataque = self.duracao_ataque_atual
        self.tempo_combo_janela = 0.0
        self.golpe_id += 1
        self.impulso_ataque = True
        self.deformar(1.22 if self.combo_etapa < 2 else 1.36, 0.82 if self.combo_etapa < 2 else 0.70)

    def levar_dano(self, quantidade, origem, rpg=None, audio=None):
        if self.invencivel > 0:
            return False

        # Esquiva perfeita com i-frames durante o Dash (Hack and Slash)
        if self.tempo_dash > 0:
            return False

        # Bloqueio frontal com escudo (suporta os 8 eixos)
        if self.defendendo and self.escudo_equipado != "nenhum":
            ox = origem[0] if isinstance(origem, (tuple, list)) else getattr(origem, "x", getattr(origem, "centerx", self.rect.centerx))
            oy = origem[1] if isinstance(origem, (tuple, list)) else getattr(origem, "y", getattr(origem, "centery", self.rect.centery))
            dx = ox - self.rect.centerx
            dy = oy - self.rect.centery
            vetor_olhar = VETORES.get(self.direcao, pygame.Vector2(0, 1))
            vetor_ataque = pygame.Vector2(dx, dy)
            if vetor_ataque.length_squared() == 0:
                bloqueou = True
            else:
                bloqueou = vetor_olhar.dot(vetor_ataque.normalize()) >= -0.25

            if bloqueou:
                custo_bloqueio = max(14.0, float(quantidade) * 9.0)
                guard_break = False
                rpg_ativo = rpg or self.rpg
                if rpg_ativo:
                    if rpg_ativo.stamina < custo_bloqueio:
                        rpg_ativo.stamina = 0.0
                        rpg_ativo.exaustao_stamina = True
                        rpg_ativo.delay_regen_stamina = 0.9
                        guard_break = True
                    else:
                        rpg_ativo.gastar_stamina(custo_bloqueio, delay=0.5)

                if guard_break:
                    self.defendendo = False
                    self.empurrar(origem, 160, 0.45)
                    self.deformar(0.75, 1.35)
                    if audio:
                        audio.sfx("escudo_bloqueio")
                    dano_gb = max(1, quantidade // 2)
                    self.vida = max(0, self.vida - dano_gb)
                    self.invencivel = 0.6
                    return True
                else:
                    if audio:
                        audio.sfx("escudo_bloqueio")
                    self.empurrar(origem, 85, 0.12)
                    self.deformar(0.9, 1.15)
                    return False

        # Redução por túnica/armadura
        red = rpg.fator_reducao_dano if rpg else 1.0
        dano_final = max(1, round(quantidade * red))
        self.vida = max(0, self.vida - dano_final)
        self.invencivel = TEMPO_INVENCIVEL
        self.tempo_ataque = 0
        self.empurrar(origem, 180, 0.15)
        return True

    def area_interacao(self):
        """Pedacinho à frente do jogador, para falar com NPCs (nos 8 eixos)."""
        dx, dy = VETORES.get(self.direcao, pygame.Vector2(0, 1))
        return self.rect.move(round(dx * 8), round(dy * 8)).inflate(4, 4)

    def curar(self, quantidade):
        self.vida = min(self.vida_maxima, self.vida + quantidade)

    def atualizar_cena(self, dt, nivel):
        """Atualiza animações, poses, pulo e caminhada de roteiro mesmo durante diálogos."""
        self.cama_pos = getattr(nivel, "cama_pos", None)
        if self.pose == "dormir" and self.cama_pos:
            cx, cy = self.cama_pos
            self.rect.midbottom = (cx + TILE // 2, cy + TILE)
            self.pos = pygame.Vector2(self.rect.topleft)
        self.vel_atual = pygame.Vector2()
        self.atualizar_base(dt, nivel)

    def atualizar(self, dt, entrada, nivel):
        tempo_ataque_ant = self.tempo_ataque
        self.tempo_ataque = max(0.0, self.tempo_ataque - dt)
        if tempo_ataque_ant > 0 and self.tempo_ataque <= 0:
            self.tempo_combo_janela = 0.42
            if self.buffer_ataque:
                self.buffer_ataque = False
                self.atacar()

        self.tempo_combo_janela = max(0.0, self.tempo_combo_janela - dt)
        if self.tempo_combo_janela <= 0 and not self.atacando:
            self.combo_etapa = 0

        self.invencivel = max(0.0, self.invencivel - dt)
        self.tempo_dash = max(0.0, self.tempo_dash - dt)
        self.recarga_dash = max(0.0, self.recarga_dash - dt)
        self.andando = False
        self.correndo = False
        self.cama_pos = getattr(nivel, "cama_pos", None)
        self.defendendo = (
            entrada.segurando("defender")
            and self.escudo_equipado != "nenhum"
            and not self.atacando
            and not self.nadando
        )

        for r in self.rastros:
            r["vida"] -= dt
        self.rastros = [r for r in self.rastros if r["vida"] > 0]

        if self.atualizar_base(dt, nivel):
            return

        if self.pose != "normal":
            return

        # Dash e Dash-Cancel (cancela animação de ataque com esquiva instantânea)
        if entrada.apertou("correr") and self.recarga_dash <= 0 and not self.nadando and self.tempo_empurrao <= 0:
            custo_dash = 18.0
            pode_dash = True
            if self.rpg:
                pode_dash = self.rpg.pode_gastar_stamina(custo_dash)
            if pode_dash:
                if self.rpg:
                    self.rpg.gastar_stamina(custo_dash)
                if self.atacando:
                    self.tempo_ataque = 0.0
                    self.buffer_ataque = False
                    self.tempo_combo_janela = 0.38
                self.tempo_dash = 0.16
                self.recarga_dash = 0.35
                self.deformar(1.25, 0.78)

        if entrada.apertou("pular"):
            self.pular(160.0)

        self.nadando = nivel.eh_agua_em(self.rect.centerx, self.rect.centery) and self.z <= 2.0

        if self.impulso_ataque:
            self.impulso_ataque = False
            mult_imp = 6.0 if getattr(self, "dash_strike", False) else (5.0 if getattr(self, "combo_etapa", 0) == 2 else 3.8)
            self.mover(VETORES[self.direcao] * mult_imp, nivel)

        if self.atualizar_empurrao(dt, nivel) or self.atacando:
            self.vel_atual *= max(0.0, 1.0 - dt * 18)
            return

        eixo_x = (1 if entrada.segurando("direita") else 0) - (1 if entrada.segurando("esquerda") else 0)
        eixo_y = (1 if entrada.segurando("baixo") else 0) - (1 if entrada.segurando("cima") else 0)
        movimento = pygame.Vector2(eixo_x, eixo_y)

        if movimento.length_squared() > 0:
            nova_dir = MAPA_DIRECOES_8.get((eixo_x, eixo_y), self.direcao)
            if "_" in nova_dir:
                self.direcao = nova_dir
                self.timer_manter_diagonal = 0.055
            else:
                if "_" in self.direcao and nova_dir in self.direcao.split("_") and self.timer_manter_diagonal > 0:
                    self.timer_manter_diagonal = max(0.0, self.timer_manter_diagonal - dt)
                    if self.timer_manter_diagonal <= 0:
                        self.direcao = nova_dir
                else:
                    self.timer_manter_diagonal = 0.0
                    self.direcao = nova_dir

            quer_correr = entrada.segurando("correr") and not self.defendendo
            if quer_correr and self.rpg:
                if self.rpg.stamina <= 0 or getattr(self.rpg, "exaustao_stamina", False):
                    quer_correr = False
                else:
                    self.rpg.gastar_stamina_continua(12.0 * dt)
            self.correndo = (quer_correr or self.tempo_dash > 0) and not self.defendendo
            fator_agua = 0.78 if self.nadando else 1.0
            fator_defesa = 0.65 if self.defendendo else 1.0
            fator_vel = (2.2 if self.tempo_dash > 0 else (1.45 if self.correndo else 1.0)) * self.fator_velocidade_rpg * fator_agua * fator_defesa * getattr(self, "fator_frenesi", 1.0)
            vel_alvo = movimento.normalize() * (VELOCIDADE_JOGADOR * fator_vel)
            self.vel_atual += (vel_alvo - self.vel_atual) * min(1.0, dt * 18.0)
            self.andando = True
            self.anim += dt * (14.0 if self.correndo else 9.5)

            # Inclinação suave na direção horizontal do movimento
            if abs(movimento.x) > 0:
                ang_alvo = -7.0 * (1 if movimento.x > 0 else -1) * (1.3 if self.correndo else 1.0)
                self.inclinacao += (ang_alvo - self.inclinacao) * min(1.0, dt * 14.0)

            if self.tempo_dash > 0:
                self.timer_rastro -= dt
                if self.timer_rastro <= 0:
                    self.timer_rastro = 0.035
                    self.rastros.append({
                        "rect": self.rect_sprite().copy(),
                        "direcao": self.direcao,
                        "quadro": int(self.anim) % 6,
                        "vida": 0.14,
                    })
        else:
            self.timer_manter_diagonal = 0.0
            # Desaceleração suave ao parar
            self.vel_atual *= max(0.0, 1.0 - dt * 20.0)
            if self.vel_atual.length_squared() < 12.0:
                self.vel_atual = pygame.Vector2()

        if self.vel_atual.length_squared() > 0:
            self.mover(self.vel_atual * dt, nivel)
        self.nadando = nivel.eh_agua_em(self.rect.centerx, self.rect.centery) and self.z <= 2.0

    # ------------------------------------------------------------ desenho
    def rect_sprite(self):
        """Quadro de 32x32 do desenho; os pés ficam na base da hitbox."""
        r = pygame.Rect(0, 0, QUADRO, QUADRO)
        r.midbottom = (self.rect.centerx, self.rect.bottom + 1)
        return r

    def rect_corpo(self):
        """Área aproximada do corpo (sem o topo da cabeça)."""
        r = pygame.Rect(0, 0, TILE, 22)
        r.midbottom = self.rect.midbottom
        return r

    def _ancora_espada(self):
        """Onde a espada aparece, saindo da mão. Devolve (atributo do rect, ponto)."""
        c = self.rect_corpo()
        return {
            "cima": ("midbottom", (c.centerx + 8, c.bottom - 9)),
            "baixo": ("midtop", (c.centerx - 4, c.bottom - 10)),
            "direita": ("midleft", (c.right - 2, c.bottom - 9)),
            "esquerda": ("midright", (c.left + 2, c.bottom - 9)),
            "cima_direita": ("bottomleft", (c.centerx + 2, c.bottom - 12)),
            "cima_esquerda": ("bottomright", (c.centerx - 2, c.bottom - 12)),
            "baixo_direita": ("topleft", (c.centerx + 2, c.bottom - 10)),
            "baixo_esquerda": ("topright", (c.centerx - 2, c.bottom - 10)),
        }[self.direcao]

    def rect_espada_normal(self):
        attr, ponto = self._ancora_espada()
        r = pygame.Rect(0, 0, TILE, TILE)
        setattr(r, attr, ponto)
        if self.direcao in ("cima", "baixo"):
            r.inflate_ip(-4, 0)
        elif self.direcao in ("esquerda", "direita"):
            r.inflate_ip(0, -2)
        else:
            r.inflate_ip(-2, -2)
        # Inclui o corpo, para acertar também inimigos colados no jogador.
        return r.union(self.rect_corpo().inflate(-2, -2))

    def rect_espada(self):
        if getattr(self, "combo_etapa", 0) == 2:
            # Finalizador giratório 360°: atinge todos os inimigos ao redor
            return self.rect.inflate(28, 28)
        if getattr(self, "dash_strike", False):
            # Estocada do dash: alcance extra e perfuração frontal
            dx, dy = VETORES.get(self.direcao, pygame.Vector2(0, 1))
            return self.rect_espada_normal().move(round(dx * 8), round(dy * 8)).inflate(6, 6)
        return self.rect_espada_normal()

    def _pos_ombro(self):
        """Posição do ombro do braço da espada no mundo."""
        cx, base_y = self.rect.centerx, self.rect.bottom
        return {
            "baixo": pygame.Vector2(cx - 5, base_y - 11),
            "cima": pygame.Vector2(cx + 5, base_y - 11),
            "direita": pygame.Vector2(cx + 2, base_y - 11),
            "esquerda": pygame.Vector2(cx - 2, base_y - 11),
            "baixo_direita": pygame.Vector2(cx - 1, base_y - 11),
            "baixo_esquerda": pygame.Vector2(cx + 1, base_y - 11),
            "cima_direita": pygame.Vector2(cx + 4, base_y - 11),
            "cima_esquerda": pygame.Vector2(cx - 4, base_y - 11),
        }[self.direcao]

    @staticmethod
    def _vetor_angulo(angulo_graus):
        """Converte o ângulo do pygame.transform.rotate (0° = cima) em vetor unitário na tela."""
        rad = math.radians(angulo_graus)
        return pygame.Vector2(-math.sin(rad), -math.cos(rad))

    def _fases_ataque(self, progresso):
        """Devolve (fator_arco_braco, fator_arco_espada, comprimento_braco) para o progresso 0..1."""
        if progresso < 0.22:
            # Fase 1: Preparação (ergue o braço e a espada à frente para armar o golpe)
            t = progresso / 0.22
            return -0.60 - 0.10 * t, -0.70 - 0.12 * t, 5.0
        if progresso < 0.74:
            # Fase 2: Corte rápido (braço estica e varre com força na direção do olhar)
            t = (progresso - 0.22) / 0.52
            suave = 1.0 - (1.0 - t) ** 2
            return -0.70 + suave * 1.35, -0.82 + suave * 1.55, 6.8
        # Fase 3: Finalização (desacelera no fim do arco à frente)
        t = (progresso - 0.74) / 0.26
        return 0.65 + t * 0.06, 0.73 + t * 0.06, 6.0 - t * 0.8

    def _desenhar_golpe_espada(self, tela, camera, gfx, dx, dy):
        duracao = max(0.01, getattr(self, "duracao_ataque_atual", TEMPO_ATAQUE))
        progresso = 1.0 - (self.tempo_ataque / duracao)
        ang_base = ANGULO_BASE_ESPADA[self.direcao]
        ox, oy = camera.offset
        ombro_tela = self._pos_ombro() - pygame.Vector2(ox - dx, oy - dy)

        is_finisher = getattr(self, "combo_etapa", 0) == 2
        is_dash_strike = getattr(self, "dash_strike", False)
        is_cross = getattr(self, "combo_etapa", 0) == 1

        if is_dash_strike:
            # Estocada perfurante frontal
            suave = math.sin(progresso * math.pi)
            ang_espada = ang_base
            ang_braco = ang_base
            u_braco = self._vetor_angulo(ang_braco)
            u_espada = self._vetor_angulo(ang_espada)
            compr_braco = 6.0 + suave * 4.5
            mao_tela = ombro_tela + u_braco * compr_braco
            cotovelo_tela = ombro_tela.lerp(mao_tela, 0.5)

            # Rastro de estocada pontiaguda
            if 0.15 < progresso < 0.85:
                ponta_esp = mao_tela + u_espada * 17.0
                p1 = (round(ponta_esp.x), round(ponta_esp.y))
                p0 = (round(ombro_tela.x), round(ombro_tela.y))
                pygame.draw.line(tela, (255, 255, 255), p0, p1, 2)
                pygame.draw.circle(tela, (140, 235, 255), p1, 3)
        elif is_finisher:
            # Finalizador Giratório 360° (Whirlwind)
            sentido = -1 if "direita" in self.direcao else 1
            ang_rot = (progresso * 360.0) * sentido
            ang_braco = ang_base + ang_rot
            ang_espada = ang_base + ang_rot + 15.0 * sentido
            u_braco = self._vetor_angulo(ang_braco)
            u_espada = self._vetor_angulo(ang_espada)
            compr_braco = 6.8
            mao_tela = ombro_tela + u_braco * compr_braco
            cotovelo_tela = ombro_tela.lerp(mao_tela, 0.5)

            # Rastro circular de 360° em volta do herói
            if 0.10 < progresso < 0.95:
                pontos_arco = []
                for p in range(8):
                    prog_p = max(0.05, progresso - p * 0.05)
                    ang_p = ang_base + (prog_p * 360.0) * sentido
                    u_p = self._vetor_angulo(ang_p)
                    pt = ombro_tela + u_p * 18.0
                    pontos_arco.append((round(pt.x), round(pt.y)))
                if len(pontos_arco) >= 2:
                    pygame.draw.lines(tela, (255, 235, 120), False, pontos_arco, 2)
                    pygame.draw.lines(tela, (255, 255, 255), False, pontos_arco[:4], 1)
        else:
            # Golpes 0 e 1 (Corte horizontal e Corte cruzado inverso)
            sentido_base = -1 if "direita" in self.direcao else 1
            sentido = -sentido_base if is_cross else sentido_base
            f_braco, f_espada, compr_braco = self._fases_ataque(progresso)

            ang_braco = ang_base + (f_braco * 72.0) * sentido
            ang_espada = ang_base + (f_espada * 78.0) * sentido

            u_braco = self._vetor_angulo(ang_braco)
            u_espada = self._vetor_angulo(ang_espada)

            mao_tela = ombro_tela + u_braco * compr_braco
            cotovelo_tela = ombro_tela.lerp(mao_tela, 0.5)

            # Rastro de corte
            if 0.16 < progresso < 0.86:
                pontos_externos = []
                pontos_internos = []
                for p in range(6):
                    prog_p = max(0.16, progresso - p * 0.06)
                    fb_p, fe_p, cb_p = self._fases_ataque(prog_p)
                    ang_b_p = ang_base + (fb_p * 72.0) * sentido
                    ang_e_p = ang_base + (fe_p * 78.0) * sentido
                    u_b_p = self._vetor_angulo(ang_b_p)
                    u_e_p = self._vetor_angulo(ang_e_p)
                    mao_p = ombro_tela + u_b_p * cb_p
                    ponta_ext = mao_p + u_e_p * 13.5
                    ponta_int = mao_p + u_e_p * 9.0
                    pontos_externos.append((round(ponta_ext.x), round(ponta_ext.y)))
                    pontos_internos.append((round(ponta_int.x), round(ponta_int.y)))
                if len(pontos_externos) >= 2:
                    cor_rastro_ext = (255, 252, 215)
                    cor_rastro_int = (190, 225, 255)
                    if self.arma_equipada == "lamina_vulcanica":
                        cor_rastro_ext = (255, 120, 40)
                        cor_rastro_int = (255, 220, 80)
                    elif self.arma_equipada == "sabre_tempestade":
                        cor_rastro_ext = (110, 235, 255)
                        cor_rastro_int = (240, 250, 255)
                    elif self.arma_equipada == "lamina_lendaria":
                        cor_rastro_ext = (255, 240, 110)
                        cor_rastro_int = (255, 255, 240)
                    pygame.draw.lines(tela, cor_rastro_int, False, pontos_internos, 2)
                    pygame.draw.lines(tela, cor_rastro_ext, False, pontos_externos, 2)

        p_ombro = (round(ombro_tela.x), round(ombro_tela.y))
        p_cotovelo = (round(cotovelo_tela.x), round(cotovelo_tela.y))
        p_mao = (round(mao_tela.x), round(mao_tela.y))

        # Manga do braço saindo do ombro até a mão
        pygame.draw.line(tela, (34, 24, 40), p_ombro, p_mao, 5)
        pygame.draw.circle(tela, (34, 24, 40), p_ombro, 2)
        pygame.draw.line(tela, (52, 92, 184), p_ombro, p_cotovelo, 3)
        pygame.draw.line(tela, (88, 130, 220), p_ombro, p_cotovelo, 1)

        # Espada ancorada pelo cabo dentro da mão
        espada_rot = pygame.transform.rotate(gfx.espada["cima"], ang_espada)
        centro_espada = mao_tela + u_espada * 5.5
        rect_espada = espada_rot.get_rect(center=(round(centro_espada.x), round(centro_espada.y)))
        tela.blit(espada_rot, rect_espada)

        # Mão / punho do herói
        pygame.draw.circle(tela, (34, 24, 40), p_mao, 3)
        pygame.draw.circle(tela, (226, 168, 128), p_mao, 2)
        tela.set_at(p_mao, (252, 214, 176))

    def _quadro_ataque(self, quadros):
        if len(quadros) < 11:
            return self.quadro_personagem(quadros)
        duracao = max(0.01, getattr(self, "duracao_ataque_atual", TEMPO_ATAQUE))
        progresso = 1.0 - (self.tempo_ataque / duracao)
        if progresso < 0.22:
            return quadros[8]  # preparação
        if progresso < 0.74:
            return quadros[9]  # impacto / corte
        return quadros[10]  # finalização

    def _desenhar_escudo(self, tela, camera, dx, dy):
        if self.escudo_equipado == "nenhum":
            return
        ox, oy = camera.offset
        cx = self.rect.centerx - ox + dx
        base_y = self.rect.bottom - oy + dy

        eh_guardiao = (self.escudo_equipado == "escudo_guardiao")
        cor_borda = (215, 175, 60) if eh_guardiao else (90, 55, 35)
        cor_corpo = (55, 95, 175) if eh_guardiao else (145, 90, 50)
        cor_metal = (245, 230, 110) if eh_guardiao else (190, 195, 205)

        recuo = 2 if self.defendendo else 0
        if self.direcao == "baixo":
            pos_esc = (cx - 5, base_y - 12 + recuo)
            dim = (10, 12)
        elif self.direcao == "baixo_direita":
            pos_esc = (cx - 2 + recuo, base_y - 12 + recuo)
            dim = (8, 11)
        elif self.direcao == "baixo_esquerda":
            pos_esc = (cx - 6 - recuo, base_y - 12 + recuo)
            dim = (8, 11)
        elif self.direcao == "cima":
            pos_esc = (cx - 5, base_y - 17 - recuo)
            dim = (10, 11)
        elif self.direcao == "cima_direita":
            pos_esc = (cx - 2 + recuo, base_y - 16 - recuo)
            dim = (8, 11)
        elif self.direcao == "cima_esquerda":
            pos_esc = (cx - 6 - recuo, base_y - 16 - recuo)
            dim = (8, 11)
        elif self.direcao == "direita":
            pos_esc = (cx + 2 + recuo, base_y - 13)
            dim = (6, 11)
        else:  # esquerda
            pos_esc = (cx - 8 - recuo, base_y - 13)
            dim = (6, 11)

        r_esc = pygame.Rect(pos_esc, dim)
        pygame.draw.rect(tela, cor_corpo, r_esc, border_radius=2)
        pygame.draw.rect(tela, cor_borda, r_esc, 1, border_radius=2)
        if dim[0] >= 8:
            pygame.draw.circle(tela, cor_metal, r_esc.center, 2)
        else:
            tela.set_at(r_esc.center, cor_metal)

        if self.defendendo:
            halo = pygame.Surface((dim[0] + 6, dim[1] + 6), pygame.SRCALPHA)
            pygame.draw.rect(halo, (*cor_metal, 60), halo.get_rect(), border_radius=3)
            tela.blit(halo, (r_esc.x - 3, r_esc.y - 3))

    def desenhar(self, tela, camera, gfx, fonte=None):
        if self.pose == "dormir" and self.cama_pos:
            rect_cama = pygame.Rect(self.cama_pos[0], self.cama_pos[1], TILE, TILE)
            tela.blit(gfx.heroi_dormindo, camera.aplicar(rect_cama))
            if fonte:
                self.desenhar_extras_cabeca(tela, camera, fonte, (rect_cama.centerx, rect_cama.top))
            return

        # Rastro de fantasmas translúcidos durante o dash
        for r in self.rastros:
            fantasma = gfx.jogador[r["direcao"]][r["quadro"]].copy()
            fantasma.set_alpha(int((r["vida"] / 0.14) * 110))
            tela.blit(fantasma, camera.aplicar(r["rect"]))

        if self.nadando:
            ox, oy = camera.offset
            sx = self.rect.centerx - ox
            sy = self.rect.bottom - oy - 1
            raio_onda = 7 + round(math.sin(self.tempo_idle * 7.0) * 1.5)
            pygame.draw.ellipse(tela, (110, 195, 248), (sx - raio_onda, sy - 3, raio_onda * 2, 6), 1)
            pygame.draw.ellipse(tela, (220, 250, 255), (sx - raio_onda + 2, sy - 2, (raio_onda - 2) * 2, 4), 1)
        else:
            self.desenhar_sombra(tela, camera, gfx)

        # Pisca enquanto está invencível.
        if self.invencivel > 0 and int(self.invencivel * 20) % 2 == 0:
            return

        quadros = gfx.jogador[self.direcao]
        img = self._quadro_ataque(quadros) if self.atacando else self.quadro_personagem(quadros)
        img = _aplicar_tunica(img, self.tunica_equipada)
        if self.pose == "caido":
            img = pygame.transform.rotate(img, 90)

        dx, dy = self.offset_pose()
        olhando_costas = self.direcao in ("cima", "cima_direita", "cima_esquerda")
        if self.nadando:
            # Enquanto nada, apenas o tronco/cabeça aparece acima da superfície da água, balançando com as ondas
            balanco_agua = round(math.sin(self.tempo_idle * 6.0) * 1.2)
            topo_submerso = img.subsurface((0, 0, QUADRO, 22))
            rect_nado = camera.aplicar(self.rect_sprite()).move(dx, dy + 6 + balanco_agua)
            tela.blit(topo_submerso, rect_nado.topleft)
        else:
            # Quando olha para cima/costas, o escudo e braço com espada passam por trás das costas
            if self.escudo_equipado != "nenhum" and olhando_costas and self.pose == "normal":
                self._desenhar_escudo(tela, camera, dx, dy)
            if self.atacando and olhando_costas:
                self._desenhar_golpe_espada(tela, camera, gfx, dx, dy)

            img_transf, rect_desenho = self.transformar_sprite(img, self.rect_sprite(), camera)
            tela.blit(img_transf, rect_desenho)

            # Quando olha para os lados ou para baixo, o escudo fica na frente
            if self.escudo_equipado != "nenhum" and not olhando_costas and self.pose == "normal":
                self._desenhar_escudo(tela, camera, dx, dy)

        if self.atacando and (not olhando_costas or self.nadando):
            self._desenhar_golpe_espada(tela, camera, gfx, dx, dy)
        elif self.pose == "poder":
            espada = gfx.espada["cima"]
            rect_espada = espada.get_rect(midbottom=(self.rect.centerx + 4, self.rect.top - 14))
            tela.blit(espada, camera.aplicar(rect_espada).move(dx, dy))

        if fonte:
            self.desenhar_extras_cabeca(tela, camera, fonte, (self.rect.centerx, self.rect.bottom - 24))
