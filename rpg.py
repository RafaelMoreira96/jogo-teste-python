"""Sistema de RPG, atributos, poderes ativos, projéteis mágicos e Árvore de Habilidades."""
import math
import random

import pygame

from equipamentos import CATALOGO_ARMAS, CATALOGO_ESCUDOS, CATALOGO_TUNICAS
from ui import desenhar_texto

# Definição dos 3 ramos x 3 níveis da Árvore de Habilidades
RAMOS_HABILIDADES = [
    {
        "nome": "Lâmina Solar",
        "cor": (255, 200, 75),
        "habilidades": [
            {
                "id": "golpe_vorpal",
                "nome": "Golpe Vorpal",
                "tipo": "passiva",
                "custo_ph": 1,
                "custo_mana": 0,
                "req": None,
                "cor": (255, 215, 90),
                "desc": "Passiva: +1 de dano na espada e lâmina energizada.",
            },
            {
                "id": "corte_giratorio",
                "nome": "Corte Giratório",
                "tipo": "ativa",
                "custo_ph": 1,
                "custo_mana": 6,
                "req": "golpe_vorpal",
                "cor": (255, 230, 110),
                "desc": "Poder (6 MP): Giro 360° que corta todos ao redor.",
            },
            {
                "id": "furia_escolhido",
                "nome": "Fúria Solar",
                "tipo": "passiva",
                "custo_ph": 2,
                "custo_mana": 0,
                "req": "corte_giratorio",
                "cor": (255, 140, 60),
                "desc": "Passiva: +1 de dano total e +20% de velocidade.",
            },
        ],
    },
    {
        "nome": "Chama Astral",
        "cor": (110, 215, 255),
        "habilidades": [
            {
                "id": "esfera_fogo",
                "nome": "Esfera de Fogo",
                "tipo": "ativa",
                "custo_ph": 0,
                "custo_mana": 5,
                "req": None,
                "cor": (255, 110, 50),
                "desc": "Poder Inicial (5 MP): Dispara bola de fogo explosiva.",
            },
            {
                "id": "nova_gelo",
                "nome": "Nova de Gelo",
                "tipo": "ativa",
                "custo_ph": 1,
                "custo_mana": 8,
                "req": "esfera_fogo",
                "cor": (110, 230, 255),
                "desc": "Poder (8 MP): Congela e causa dano em área ao redor.",
            },
            {
                "id": "tempestade_raios",
                "nome": "Raio Celestial",
                "tipo": "ativa",
                "custo_ph": 2,
                "custo_mana": 12,
                "req": "nova_gelo",
                "cor": (215, 130, 255),
                "desc": "Poder (12 MP): Invoca relâmpagos nos inimigos próximos.",
            },
        ],
    },
    {
        "nome": "Luz Ancestral",
        "cor": (120, 240, 150),
        "habilidades": [
            {
                "id": "fonte_mana",
                "nome": "Fonte de Mana",
                "tipo": "passiva",
                "custo_ph": 1,
                "custo_mana": 0,
                "req": None,
                "cor": (95, 195, 255),
                "desc": "Passiva: +10 de Mana Máxima e regeneração 2x mais rápida.",
            },
            {
                "id": "cura_celestial",
                "nome": "Cura Celestial",
                "tipo": "ativa",
                "custo_ph": 1,
                "custo_mana": 10,
                "req": "fonte_mana",
                "cor": (120, 245, 155),
                "desc": "Poder (10 MP): Restaura 2 corações de vida na hora.",
            },
            {
                "id": "barreira_astral",
                "nome": "Barreira Astral",
                "tipo": "passiva",
                "custo_ph": 2,
                "custo_mana": 0,
                "req": "cura_celestial",
                "cor": (255, 240, 150),
                "desc": "Passiva: +1 coração máximo e explode luz ao sofrer dano.",
            },
        ],
    },
]

CATALOGO_HABILIDADES = {
    hab["id"]: hab
    for ramo in RAMOS_HABILIDADES
    for hab in ramo["habilidades"]
}

# Tabela canônica de progressão recomendada dos 15 Guardiões + Chefe Final
# (id, nome, nv_req, arq_covil, arq_origem, elemento, nome_covil)
LISTA_CHEFES_PROGRESSAO = [
    ("rei_slime", "Rei Slime Coroado", 1, "covil_rei_slime.txt", "mundo.txt", "agua", "Covil dos Slimes"),
    ("golem_pedra", "Golem de Pedra Ancestral", 2, "camara_golem.txt", "ruinas.txt", "terra", "Câmara do Golem"),
    ("serpente_dunas", "Serpente das Dunas", 3, "abismo_dunas.txt", "deserto.txt", "areia", "Abismo das Dunas"),
    ("colosso_solar", "Colosso Solar", 4, "altar_colosso.txt", "templo_sol.txt", "sol", "Altar do Colosso"),
    ("bruxa_brumas", "Bruxa das Brumas", 5, "antro_bruxa.txt", "pantano.txt", "veneno", "Antro da Bruxa"),
    ("ceifador_espectral", "Ceifador Espectral", 6, "sepulcro_ceifador.txt", "cripta.txt", "trevas", "Sepulcro do Ceifador"),
    ("leviata_aquatico", "Leviatã Aquático", 7, "abismo_marinho.txt", "lago.txt", "oceano", "Abismo Marinho"),
    ("guardiao_diamante", "Guardião dos Cristais", 8, "nucleo_cristal.txt", "caverna_cristal.txt", "cristal", "Núcleo de Cristal"),
    ("troll_rochas", "Troll das Cavernas", 9, "caverna_troll.txt", "montanha.txt", "rocha", "Caverna do Troll"),
    ("yeti_glacial", "Yeti Glacial", 10, "covil_yeti.txt", "pico_congelado.txt", "gelo", "Covil do Yeti"),
    ("valquiria_caida", "Valquíria Sombria", 11, "altar_valquiria.txt", "santuario.txt", "luz", "Altar da Valquíria"),
    ("cavaleiro_negro", "Cavaleiro Negro", 12, "arena_cavaleiro.txt", "castelo_patio.txt", "aco", "Arena do Cavaleiro"),
    ("quimera_abissal", "Quimera Abissal", 13, "fosso_quimera.txt", "castelo_masmorra.txt", "fogo", "Fosso da Quimera"),
    ("arquimago", "Arquimago Corrompido", 14, "observatorio_arquimago.txt", "castelo_biblioteca.txt", "arcano", "Observatório"),
    ("paladino_juizo", "Paladino do Juízo", 15, "tribunal_paladino.txt", "castelo_ante_camara.txt", "sagrado", "Tribunal do Juízo"),
    ("entidade_maligna", "A Entidade Maligna", 15, "castelo_salao_trono.txt", "castelo_sala_salvamento.txt", "vazio", "Salão do Trono"),
]

# Categorias narrativas canônicas dos 16 Chefes (Prompt 4)
CATEGORIAS_CHEFES = {
    # Guardiões das Relíquias (6)
    "rei_slime": "Guardião da Relíquia (Água)",
    "golem_pedra": "Guardião da Relíquia (Terra)",
    "serpente_dunas": "Guardião da Relíquia (Areia)",
    "colosso_solar": "Guardião da Relíquia (Sol)",
    "ceifador_espectral": "Guardião da Relíquia (Trevas)",
    "leviata_aquatico": "Guardião da Relíquia (Marés)",
    # Arautos do Eclipse (4)
    "cavaleiro_negro": "Arauto do Eclipse (Aço)",
    "quimera_abissal": "Arauto do Eclipse (Fogo)",
    "arquimago": "Arauto do Eclipse (Arcano)",
    "paladino_juizo": "Arauto do Eclipse (Juízo)",
    # Lendas Ocultas (5)
    "bruxa_brumas": "Lenda Oculta (Pântano)",
    "guardiao_diamante": "Lenda Oculta (Cristal)",
    "troll_rochas": "Lenda Oculta (Rocha)",
    "yeti_glacial": "Lenda Oculta (Gelo)",
    "valquiria_caida": "Lenda Oculta (Luz)",
    # Soberano do Apocalipse (1)
    "entidade_maligna": "Soberano do Apocalipse",
}


class SistemaRPG:
    """Gerencia nível, XP, mana, atributos e árvore de habilidades do herói."""

    def __init__(self):
        self.nivel = 1
        self.xp = 0
        self.xp_proximo = 30
        self.pontos_habilidade = 1  # começa com 1 ponto para o jogador já experimentar a árvore!
        self.desbloqueadas = {"esfera_fogo"}
        self.poderes_ativos = ["esfera_fogo"]
        self.indice_poder = 0
        self.mana_base = 20.0
        self.mana = 20.0
        self.chefes_derrotados = set()

        # Economia, Consumíveis e Equipamentos (Pilar 1)
        self.ouro = 0
        self.bombas = 3
        self.chaves = 0
        self.arma_equipada = "espada_ferro"
        self.escudo_equipado = "nenhum"
        self.tunica_equipada = "tunica_verde"

        # Amuletos & Forja (Prompt 3)
        self.amuletos = set()  # "rapidez", "ima"
        self.nivel_espada = 1  # 1 a 4 (+1 dano por nível acima de 1)

        # Viagem Rápida e Relíquias Colecionáveis (Prompt 2)
        self.waypoint_descobertos = set()
        self.reliquias_coletadas = set()
        self.reliquias_entregues = set()

        # Fator Replay & Endgame (Prompt 3)
        self.tempo_speedrun = 0.0
        self.splits_speedrun = {}  # {id_chefe: tempo}
        self.derrotas_monstros = {}  # {id_monstro: int}
        self.new_game_plus = False
        self.ciclo_ng = 0

    def proximo_chefe(self):
        """Retorna o próximo chefe recomendado que ainda não foi derrotado."""
        for c in LISTA_CHEFES_PROGRESSAO:
            if c[0] not in self.chefes_derrotados:
                return c
        return None

    @property
    def capacidade_max_bombas(self):
        bonus = 3 if len(self.reliquias_entregues) >= 2 else 0
        return 3 + bonus

    @property
    def alcance_magnetico_moedas(self):
        bonus = 50.0 if len(self.reliquias_entregues) >= 4 else 0.0
        if "ima" in getattr(self, "amuletos", set()):
            bonus += 65.0
        return 42.0 + bonus

    @property
    def mana_maxima(self):
        bonus = 10.0 if "fonte_mana" in self.desbloqueadas else 0.0
        if len(self.reliquias_entregues) >= 6:
            bonus += 10.0
        return self.mana_base + (self.nivel - 1) * 4.0 + bonus

    @property
    def bonus_vida_maxima(self):
        bonus_hab = 2 if "barreira_astral" in self.desbloqueadas else 0
        bonus_rel = 2 if len(self.reliquias_entregues) >= 6 else 0
        return (self.nivel - 1) * 2 + bonus_hab + bonus_rel

    @property
    def dano_espada(self):
        arma = CATALOGO_ARMAS.get(self.arma_equipada, {})
        dano = arma.get("dano", 1)
        if "golpe_vorpal" in self.desbloqueadas:
            dano += 1
        if "furia_escolhido" in self.desbloqueadas:
            dano += 1
        dano += max(0, getattr(self, "nivel_espada", 1) - 1)
        return dano

    @property
    def fator_velocidade(self):
        fator = 1.2 if "furia_escolhido" in self.desbloqueadas else 1.0
        if self.arma_equipada == "sabre_tempestade":
            fator *= 1.15
        if "rapidez" in getattr(self, "amuletos", set()):
            fator *= 1.15
        return fator

    @property
    def fator_reducao_dano(self):
        tunica = CATALOGO_TUNICAS.get(self.tunica_equipada, {})
        return tunica.get("red_dano", 1.0)

    @property
    def regen_mana(self):
        base = 3.4 if "fonte_mana" in self.desbloqueadas else 1.7
        tunica = CATALOGO_TUNICAS.get(self.tunica_equipada, {})
        return base * tunica.get("regen_mana", 1.0)

    @property
    def poder_atual(self):
        if not self.poderes_ativos:
            return None
        id_hab = self.poderes_ativos[self.indice_poder % len(self.poderes_ativos)]
        return CATALOGO_HABILIDADES[id_hab]

    def trocar_poder(self):
        if len(self.poderes_ativos) > 1:
            self.indice_poder = (self.indice_poder + 1) % len(self.poderes_ativos)
        return self.poder_atual

    def atualizar(self, dt):
        self.mana = min(self.mana_maxima, self.mana + self.regen_mana * dt)

    def ganhar_xp(self, quantidade):
        """Soma XP e devolve True se subiu de nível. No New Game+, dobra os pontos de XP."""
        if getattr(self, "new_game_plus", False):
            quantidade *= 2
        self.xp += quantidade
        subiu = False
        while self.xp >= self.xp_proximo:
            self.xp -= self.xp_proximo
            self.nivel += 1
            # Curva de progressão anti-grind suave: crescimento controlado para atingir nv 15 naturalmente
            self.xp_proximo = int(self.xp_proximo * 1.32 + 10)
            self.pontos_habilidade += 1
            self.mana = self.mana_maxima
            subiu = True
        return subiu

    def pode_desbloquear(self, id_hab):
        if id_hab in self.desbloqueadas:
            return False
        hab = CATALOGO_HABILIDADES.get(id_hab)
        if not hab:
            return False
        if hab["req"] and hab["req"] not in self.desbloqueadas:
            return False
        return self.pontos_habilidade >= hab["custo_ph"]

    def desbloquear(self, id_hab):
        if not self.pode_desbloquear(id_hab):
            return False
        hab = CATALOGO_HABILIDADES[id_hab]
        self.pontos_habilidade -= hab["custo_ph"]
        self.desbloqueadas.add(id_hab)
        if hab["tipo"] == "ativa" and id_hab not in self.poderes_ativos:
            self.poderes_ativos.append(id_hab)
            self.indice_poder = len(self.poderes_ativos) - 1
        self.mana = self.mana_maxima
        return True


class ProjetilMagico:
    """Projétil elemental (ex.: Esfera de Fogo) disparado pelo herói."""

    def __init__(self, pos, direcao_vetor, dano=2, cor=(255, 115, 45)):
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(direcao_vetor).normalize() * 165.0
        self.dano = dano
        self.cor = cor
        self.vida = 0.95
        self.tempo = 0.0
        self.golpe_id = random.randint(10000, 999999)

    def reset(self, pos, direcao_vetor, dano=2, cor=(255, 115, 45)):
        self.pos.x = float(pos[0])
        self.pos.y = float(pos[1])
        v = pygame.Vector2(direcao_vetor)
        if v.length_squared() > 0:
            v = v.normalize() * 165.0
        else:
            v = pygame.Vector2(0, 1) * 165.0
        self.vel.x = v.x
        self.vel.y = v.y
        self.dano = dano
        self.cor = cor
        self.vida = 0.95
        self.tempo = 0.0
        self.golpe_id = random.randint(10000, 999999)

    @property
    def rect(self):
        r = pygame.Rect(0, 0, 8, 8)
        r.center = (round(self.pos.x), round(self.pos.y))
        return r

    def atualizar(self, dt, nivel):
        self.tempo += dt
        self.vida -= dt
        self.pos += self.vel * dt
        if self.vida <= 0:
            return False
        # Verifica colisão com paredes/pedras/árvores (mas atravessa água ~)
        cx, cy = int(self.pos.x) // 16, int(self.pos.y) // 16
        if not nivel.dentro(cx, cy):
            return False
        simb = nivel.grade[cy][cx]
        if simb in ("#", "T", "W", "R"):
            return False
        return True

    def desenhar(self, tela, camera):
        ox, oy = camera.offset
        sx = round(self.pos.x) - ox
        sy = round(self.pos.y) - oy
        raio = 5 + round(math.sin(self.tempo * 28.0) * 1.0)
        halo = pygame.Surface((raio * 4, raio * 4), pygame.SRCALPHA)
        pygame.draw.circle(halo, (*self.cor, 85), (raio * 2, raio * 2), raio * 2)
        tela.blit(halo, (sx - raio * 2, sy - raio * 2))
        pygame.draw.circle(tela, self.cor, (sx, sy), raio)
        pygame.draw.circle(tela, (255, 245, 180), (sx, sy), max(2, raio - 2))


class OndaMagica:
    """Anel expansivo de magia (Corte Giratório, Nova de Gelo, Cura Celestial, Raio)."""

    def __init__(self, centro, raio_max, cor, duracao=0.35):
        self.centro = pygame.Vector2(centro)
        self.raio_max = float(raio_max)
        self.cor = cor
        self.duracao = duracao
        self.tempo = 0.0

    def atualizar(self, dt):
        self.tempo += dt
        return self.tempo < self.duracao

    def desenhar(self, tela, camera):
        ox, oy = camera.offset
        prog = min(1.0, self.tempo / self.duracao)
        raio = max(4, round(self.raio_max * (1.0 - (1.0 - prog) ** 2)))
        alfa = int((1.0 - prog) * 190)
        surf = pygame.Surface((raio * 2 + 6, raio * 2 + 6), pygame.SRCALPHA)
        cx, cy = raio + 3, raio + 3
        pygame.draw.circle(surf, (*self.cor, alfa // 3), (cx, cy), raio)
        pygame.draw.circle(surf, (*self.cor, alfa), (cx, cy), raio, 2)
        pygame.draw.circle(surf, (255, 255, 255, alfa), (cx, cy), max(2, raio - 2), 1)
        sx = round(self.centro.x) - ox - cx
        sy = round(self.centro.y) - oy - cy
        tela.blit(surf, (sx, sy))


class TextoFlutuante:
    """Texto animado subindo no mundo (+XP, LEVEL UP, dano, cura)."""

    def __init__(self, pos, texto, cor=(255, 235, 110)):
        self.pos = pygame.Vector2(pos)
        self.texto = texto
        self.cor = cor
        self.vida = 0.85

    def atualizar(self, dt):
        self.pos.y -= 18.0 * dt
        self.vida -= dt
        return self.vida > 0

    def desenhar(self, tela, camera, fonte):
        ox, oy = camera.offset
        sx = round(self.pos.x) - ox
        sy = round(self.pos.y) - oy
        desenhar_texto(tela, fonte, self.texto, (sx, sy), self.cor, centro=True)
