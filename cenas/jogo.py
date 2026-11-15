import math
from pathlib import Path
import random

import pygame

from caixa_dialogo import CaixaDialogo
from temas import desenhar_atmosfera
from retratos import SEM_RETRATO, aparencia_por_nome
from camera import Camera
from cenas.base import Cena
from cenas.prologo import CORES_FOGO, CORES_FUMACA, CORES_PODER, CenarioCidade
from chefe import CRIADORES_CHEFES, EntidadeMalignaChefe
from config import VELOCIDADES_TEXTO
from conquistas import GerenciadorConquistas
from efeitos import (
    AmbienteVivo,
    BauTesouro,
    BlocoPedra,
    Bomba,
    Coracao,
    ItemQuest,
    Moeda,
    MonolitoTeleporte,
    ParedeRachada,
    Particula,
    PlacaPressao,
    PonteGelo,
    PortaoFerro,
    PortalMistico,
    ReliquiaGuardiao,
    TotemSinalizacao,
    VasoQuebravel,
    VentoGuia,
    explosao,
)
from enemy import CORES_SLIME_AZUL, CORES_ZUMBI, criar_inimigo
from historia import Conversa, Historia
from hud import desenhar_hud, desenhar_mensagem
from level import Nivel
from missoes import GerenciadorMissoes
from npc import NPC
from player import VETORES, Jogador
from rpg import LISTA_CHEFES_PROGRESSAO, OndaMagica, ProjetilMagico, SistemaRPG, TextoFlutuante
from salvamento import salvar_jogo
from ui import desenhar_texto

ELEMENTO_POR_CHEFE = {c[0]: c[5] for c in LISTA_CHEFES_PROGRESSAO}
from settings import (
    ALTURA,
    ARQUIVO_HISTORIA,
    CHANCE_CORACAO_ARBUSTO,
    CHANCE_CORACAO_SLIME,
    COR_FUNDO,
    LARGURA,
    MAPA_CASA,
    MAPA_INICIAL,
    PASTA_BASE,
    TILE,
    VIDA_MAXIMA,
)

REQUISITOS_MAPA_CHEFE = {
    "covil_rei_slime.txt": (1, "Rei Slime Coroado"),
    "camara_golem.txt": (2, "Golem de Pedra Ancestral"),
    "abismo_dunas.txt": (3, "Serpente das Dunas"),
    "altar_colosso.txt": (4, "Colosso Solar"),
    "antro_bruxa.txt": (5, "Bruxa das Brumas"),
    "sepulcro_ceifador.txt": (6, "Ceifador Espectral"),
    "abismo_marinho.txt": (7, "Leviatã Aquático"),
    "nucleo_cristal.txt": (8, "Guardião dos Cristais"),
    "caverna_troll.txt": (9, "Troll das Cavernas"),
    "covil_yeti.txt": (10, "Yeti Glacial"),
    "altar_valquiria.txt": (11, "Valquíria Sombria"),
    "arena_cavaleiro.txt": (12, "Cavaleiro Negro"),
    "fosso_quimera.txt": (13, "Quimera Abissal"),
    "observatorio_arquimago.txt": (14, "Arquimago Corrompido"),
    "tribunal_paladino.txt": (15, "Paladino do Juízo"),
    "castelo_salao_trono.txt": (15, "A Entidade Maligna"),
}

MAPA_PARA_CHEFE_ID = {
    "covil_rei_slime.txt": "rei_slime",
    "camara_golem.txt": "golem_pedra",
    "abismo_dunas.txt": "serpente_dunas",
    "altar_colosso.txt": "colosso_solar",
    "antro_bruxa.txt": "bruxa_brumas",
    "sepulcro_ceifador.txt": "ceifador_espectral",
    "abismo_marinho.txt": "leviata_aquatico",
    "nucleo_cristal.txt": "guardiao_diamante",
    "caverna_troll.txt": "troll_rochas",
    "covil_yeti.txt": "yeti_glacial",
    "altar_valquiria.txt": "valquiria_caida",
    "arena_cavaleiro.txt": "cavaleiro_negro",
    "fosso_quimera.txt": "quimera_abissal",
    "observatorio_arquimago.txt": "arquimago",
    "tribunal_paladino.txt": "paladino_juizo",
    "castelo_salao_trono.txt": "entidade_maligna",
}

CORES_FOLHAS = [(70, 156, 62), (38, 110, 48), (110, 190, 90)]
CORES_SLIME = [(70, 150, 230), (150, 210, 255), (40, 90, 170)]
CORES_CLARAO = {
    "branco": (255, 255, 255),
    "vermelho": (255, 60, 80),
    "roxo": (170, 50, 220),
    "dourado": (255, 225, 110),
}


class Jogo(Cena):
    def __init__(self, app, dialogo_inicial="inicio", modo_chefe=None):
        super().__init__(app)
        # Modo Chefões: {"chefe", "nivel", "dificuldade"} (None no modo história)
        self.modo_chefe = modo_chefe
        if modo_chefe:
            dialogo_inicial = None
        # A história é relida a cada "Novo jogo": dá para editar com o jogo aberto.
        self.historia = Historia.carregar(ARQUIVO_HISTORIA)
        self.flags = set()  # marcas da história (@marcar / @se)

        self.mapas = {}
        for arq_mapa in sorted((PASTA_BASE / "maps").glob("*.txt")):
            self._carregar_mapa(arq_mapa)

        self.jogador = Jogador(0, 0)
        self.rpg = SistemaRPG()
        self.projeteis = []
        self.ondas = []
        self.textos_flutuantes = []
        self.chefes = []
        self.projeteis_chefes = []
        self.boss_rush_ativo = False
        self.boss_rush_onda = 0
        self.boss_rush_timer_espera = 0.0
        self.boss_rush_concluido = False
        self.mapas_visitados = set()
        self.conquistas = GerenciadorConquistas()
        if not modo_chefe:
            self.conquistas.desbloquear("primeiro_passo", self)
        self.particulas = []
        self.estado = "jogando"  # ou "derrota"
        self.dialogo = None
        self.tempo_cenario = 0.0
        self.aviso_mapa = ""
        self.tempo_aviso_mapa = 0.0
        self.em_abertura = bool(dialogo_inicial == "inicio")
        self.fade_estado = "in"  # None, "out", "in"
        self.fade_alfa = 1.0
        self.fade_destino = None
        self.fade_usar_porta = True

        # Estado do Diretor de Cenas
        self.clima = "dia"  # "dia", "noite", "chuva", "trevas"
        self.clarao = 0.0
        self.cor_clarao = (255, 255, 255)
        self.tremor = 0.0
        self.tempo_tremor = 0.0
        self.efeito_ativo = None  # ("poder" | "fogo" | "fumaca", ator)
        self.cenario_especial = None  # ex.: CenarioCidade
        self.alvo_camera = None  # entidade ou pygame.Rect
        self.gotas_chuva = [
            [random.randrange(LARGURA), random.randrange(ALTURA)] for _ in range(45)
        ]

        # Sistemas de Economia, Missões, Puzzles e Ciclo Dia/Noite (Pilares 1, 2, 3 e 4)
        self.moedas = []
        self.baus = []
        self.placas = []
        self.blocos = []
        self.portoes = []
        self.bombas = []
        self.paredes_rachadas = []
        self.pontes_gelo = []
        self.itens_quest = []
        self.tochas_acesas = set()
        self.missoes = GerenciadorMissoes()
        self.hitstop = 0.0
        self.relogio_dia_noite = 0.35

        # Pilares do Prompt 2: Portais Místicos, Viagem Rápida, Vasos, Relíquias e Navegação
        self.portais_misticos = []
        self.monolitos = []
        self.totens = []
        self.vasos = []
        self.reliquias = []
        self.ventos_guia = []
        self.apresentacao_chefe = None
        self.feixe_teleporte = None

        if modo_chefe:
            self._preparar_modo_chefe()
            return
        self.trocar_mapa(MAPA_CASA, usar_porta=False)
        if dialogo_inicial:
            self.iniciar_dialogo(dialogo_inicial, opcional=True)

    # ------------------------------------------------------------ Modo Chefões
    def _preparar_modo_chefe(self):
        """Monta o herói no nível escolhido e abre a arena temática do chefe."""
        from cenas.modo_chefes import ARENA_POR_CHEFE, ID_DESAFIO
        from rpg import RAMOS_HABILIDADES

        modo = self.modo_chefe
        rpg = self.rpg
        nivel = max(1, int(modo.get("nivel", 1)))
        rpg.nivel = nivel
        rpg.xp = 0
        rpg.xp_proximo = int(30 * (1.45 ** (nivel - 1)))
        # Habilidades: uma por nível, alternando entre os três ramos da árvore
        rpg.pontos_habilidade = nivel
        fila = [hab["id"] for camada in zip(*[r["habilidades"] for r in RAMOS_HABILIDADES]) for hab in camada]
        for _ in range(3):
            for id_hab in fila:
                if rpg.pontos_habilidade <= 0:
                    break
                rpg.desbloquear(id_hab)
        rpg.pontos_habilidade = 0
        # Equipamento proporcional ao nível
        if nivel >= 14:
            rpg.arma_equipada, rpg.escudo_equipado, rpg.tunica_equipada = "lamina_lendaria", "escudo_guardiao", "manto_astral"
        elif nivel >= 9:
            rpg.arma_equipada, rpg.escudo_equipado, rpg.tunica_equipada = "sabre_tempestade", "escudo_madeira", "armadura_carmesim"
        elif nivel >= 5:
            rpg.arma_equipada = "lamina_vulcanica"
        rpg.bombas = 10
        rpg.mana = rpg.mana_maxima
        self.jogador.vida_maxima = self.vida_max_total()
        self.jogador.vida = self.jogador.vida_maxima

        id_chefe = modo["chefe"]
        self.trocar_mapa(PASTA_BASE / "maps" / ARENA_POR_CHEFE.get(id_chefe, "coliseu_eras.txt"), usar_porta=False)
        self.nivel.portas = []  # a arena só termina com vitória ou derrota
        self.portais_misticos = []
        if id_chefe == ID_DESAFIO:
            self.iniciar_boss_rush()
        elif id_chefe == "entidade_maligna":
            fb = EntidadeMalignaChefe(self.nivel.largura_px // 2, 6 * TILE)
            fb.aplicar_escalonamento(self.rpg)
            self._ajustar_chefe_modo(fb)
            self.chefes = [fb]
            self.iniciar_apresentacao_chefe(fb)
            if hasattr(self.app, "audio"):
                self.app.audio.tocar_bgm("chefe_final")
        self.tempo_luta = 0.0
        self.dano_luta = 0
        self._vida_ref = self.jogador.vida
        self.timer_resultado = None

    def _ajustar_chefe_modo(self, chefe):
        """Aplica a dificuldade escolhida no Modo Chefões."""
        if not self.modo_chefe:
            return
        from cenas.modo_chefes import DIFICULDADES
        mult_vida, mult_poder = DIFICULDADES.get(self.modo_chefe.get("dificuldade"), (1.0, 1.0))
        chefe.vida_max = max(1, int(chefe.vida_max * mult_vida))
        chefe.vida = chefe.vida_max
        chefe.vida_exibida = float(chefe.vida_max)
        chefe.fator_poder *= mult_poder

    def _atualizar_modo_chefe(self, dt):
        """Cronômetro, dano recebido e fim da luta no Modo Chefões."""
        if self.estado != "jogando":
            return
        if self.jogador.vida < self._vida_ref:
            self.dano_luta += self._vida_ref - self.jogador.vida
        self._vida_ref = self.jogador.vida
        terminou = not self.chefes and (not self.boss_rush_ativo or self.boss_rush_concluido)
        if self.timer_resultado is None:
            if terminou:
                self.timer_resultado = 1.8
            else:
                self.tempo_luta += dt
        else:
            self.timer_resultado -= dt
            if self.timer_resultado <= 0:
                from cenas.modo_chefes import ResultadoChefe
                self.timer_resultado = float("inf")
                self.app.empilhar(ResultadoChefe(self.app, self, self.tempo_luta, self.dano_luta))

    def recarregar_historia(self):
        self.historia = Historia.carregar(ARQUIVO_HISTORIA)

    def _carregar_mapa(self, caminho):
        chave = Path(caminho).resolve()
        if chave not in self.mapas:
            nivel = Nivel(chave, self.app.gfx)
            npcs = [NPC(*dados) for dados in nivel.npcs]
            nivel.obstaculos = [n.rect for n in npcs]
            if hasattr(nivel, "inimigos") and nivel.inimigos:
                inimigos_objs = [criar_inimigo(t, x, y) for t, x, y in nivel.inimigos]
            else:
                inimigos_objs = [criar_inimigo("slime", x, y) for x, y in nivel.slimes]
            self.mapas[chave] = {
                "nivel": nivel,
                "inimigos": inimigos_objs,
                "npcs": npcs,
                "coracoes": [Coracao(c) for c in nivel.coracoes],
                "ambiente": AmbienteVivo(nivel),
                "chefes_def": list(getattr(nivel, "chefes", [])),
            }
        return self.mapas[chave]

    def iniciar_transicao_mapa(self, caminho, usar_porta=True):
        """Inicia animação de fade-out antes de trocar de mapa (e fade-in ao entrar)."""
        if self.fade_estado == "out":
            return
        self.fade_estado = "out"
        self.fade_alfa = 0.0
        self.fade_destino = caminho
        self.fade_usar_porta = usar_porta
        audio = getattr(self.app, "audio", None)
        if audio and usar_porta:
            audio.sfx("porta")

    def trocar_mapa(self, caminho, usar_porta=True, tocar_sfx_porta=True):
        origem = self.nivel.caminho if hasattr(self, "nivel") else None
        dados = self._carregar_mapa(caminho)
        self.nivel = dados["nivel"]

        # Sempre respawna todos os inimigos ao entrar ou retornar ao mapa
        if hasattr(self.nivel, "inimigos") and self.nivel.inimigos:
            self.inimigos = [criar_inimigo(t, x, y) for t, x, y in self.nivel.inimigos]
        else:
            self.inimigos = [criar_inimigo("slime", x, y) for x, y in self.nivel.slimes]
        dados["inimigos"] = self.inimigos

        self.npcs = dados["npcs"]
        self.coracoes = dados["coracoes"]
        self.ambiente = dados["ambiente"]
        self.particulas = []
        self.projeteis = []
        self.ondas = []
        self.projeteis_chefes = []
        self.projeteis_inimigos = []
        self.chefes = []

        # Instancia objetos interativos do mapa
        self.baus = [BauTesouro((x, y), t, c) for t, x, y, c in getattr(self.nivel, "baus", [])]
        self.placas = [PlacaPressao((x, y), g) for x, y, g in getattr(self.nivel, "placas", [])]
        self.blocos = [BlocoPedra(x, y) for x, y in getattr(self.nivel, "blocos", [])]
        self.portoes = [PortaoFerro(x, y, g) for x, y, g in getattr(self.nivel, "portoes", [])]
        self.paredes_rachadas = [ParedeRachada(x, y) for x, y in getattr(self.nivel, "paredes_rachadas", [])]
        self.itens_quest = [ItemQuest((x, y), i_id) for i_id, x, y in getattr(self.nivel, "itens_quest", [])]
        self.moedas = []
        self.bombas = []
        self.pontes_gelo = []

        # Instancia elementos de Prompt 2 (Monólitos, Totens, Vasos, Relíquias e Portais Místicos)
        self.monolitos = [MonolitoTeleporte(pos, wid, nome) for pos, wid, nome in getattr(self.nivel, "monolitos", [])]
        self.totens = [TotemSinalizacao(pos, rotas) for pos, rotas in getattr(self.nivel, "totens", [])]
        self.vasos = [VasoQuebravel(pos) for pos in getattr(self.nivel, "vasos", [])]
        self.reliquias = [ReliquiaGuardiao(pos, r_id) for pos, r_id in getattr(self.nivel, "reliquias", [])]
        self.ventos_guia = []
        self.portais_misticos = []
        for rect_porta, destino in self.nivel.portas:
            if destino.name in MAPA_PARA_CHEFE_ID:
                chefe_id = MAPA_PARA_CHEFE_ID[destino.name]
                req_nv, nome_ch = REQUISITOS_MAPA_CHEFE.get(destino.name, (1, "Guardião"))
                elemento = ELEMENTO_POR_CHEFE.get(chefe_id, "arcano")
                self.portais_misticos.append(PortalMistico(rect_porta, destino, chefe_id, req_nv, elemento, nome_ch))

        self.mapas_visitados.add(self.nivel.caminho.name)
        self.jogador.cama_pos = getattr(self.nivel, "cama_pos", None)
        self.clima = getattr(self.nivel, "clima_padrao", "dia")
        self.aviso_mapa = getattr(self.nivel, "nome", self.nivel.caminho.stem.title())
        self.tempo_aviso_mapa = 2.4
        self.fade_estado = "in"
        self.fade_alfa = 1.0

        if self.nivel.caminho.name == "castelo_salao_trono.txt":
            self.iniciar_boss_rush()
        else:
            self.boss_rush_ativo = False
            for id_c, cx_p, cy_p in dados.get("chefes_def", []):
                if id_c not in self.rpg.chefes_derrotados and id_c in CRIADORES_CHEFES:
                    chefe_inst = CRIADORES_CHEFES[id_c](cx_p, cy_p)
                    chefe_inst.aplicar_escalonamento(self.rpg)
                    self._ajustar_chefe_modo(chefe_inst)
                    self.chefes.append(chefe_inst)

            if self.chefes and not self.em_abertura:
                self.iniciar_apresentacao_chefe(self.chefes[0])

        audio = getattr(self.app, "audio", None)
        if audio:
            if usar_porta and tocar_sfx_porta:
                audio.sfx("porta")
            if self.em_abertura:
                audio.tocar_bgm("abertura_sombria")
            elif self.chefes:
                audio.tocar_bgm("chefe_final" if any(isinstance(c, EntidadeMalignaChefe) for c in self.chefes) else "chefe")
            else:
                audio.tocar_bgm_mapa(self.nivel.caminho.name)

        if usar_porta:
            x, y, direcao = self.nivel.ponto_entrada_porta(origem)
            self.jogador.direcao = direcao
        else:
            x, y = self.nivel.inicio
            self.jogador.direcao = "baixo"

        self.jogador.posicionar(x, y)
        self.jogador.tempo_empurrao = 0.0
        self.camera = Camera(self.nivel.largura_px, self.nivel.altura_px)
        self.camera.centralizar(self.jogador.rect)

    def iniciar_boss_rush(self):
        self.boss_rush_ativo = True
        self.boss_rush_onda = 1
        self.boss_rush_timer_espera = 1.0
        self.boss_rush_concluido = False
        self.chefes = []
        self.projeteis_chefes = []
        self._spawnar_onda_boss_rush(1)

    def _spawnar_onda_boss_rush(self, onda):
        ondas_defs = {
            1: ["rei_slime", "golem_pedra", "serpente_dunas"],
            2: ["colosso_solar", "bruxa_brumas", "ceifador_espectral"],
            3: ["leviata_aquatico", "guardiao_diamante", "troll_rochas"],
            4: ["yeti_glacial", "valquiria_caida", "cavaleiro_negro"],
            5: ["quimera_abissal", "arquimago", "paladino_juizo"],
        }
        if onda in ondas_defs:
            self.chefes = []
            posicoes = [
                (self.nivel.largura_px // 2 - 80, self.nivel.altura_px // 2 - 20),
                (self.nivel.largura_px // 2, self.nivel.altura_px // 2 - 50),
                (self.nivel.largura_px // 2 + 80, self.nivel.altura_px // 2 - 20),
            ]
            for i, id_c in enumerate(ondas_defs[onda]):
                if id_c in CRIADORES_CHEFES:
                    px, py = posicoes[i % len(posicoes)]
                    c = CRIADORES_CHEFES[id_c](px, py, fantasma=True)
                    c.aplicar_escalonamento(self.rpg)
                    c.vida_max = int(c.vida_max * 0.65)
                    c.vida = c.vida_max
                    self._ajustar_chefe_modo(c)
                    self.chefes.append(c)
            audio = getattr(self.app, "audio", None)
            if audio:
                audio.tocar_bgm("chefe")
                audio.sfx("rugido_chefe")
            self.clarao = 0.55
            self.cor_clarao = (210, 80, 255)
            self.textos_flutuantes.append(
                TextoFlutuante(self.jogador.rect.midtop, f"ONDA {onda}/5 - O DESAFIO DAS SOMBRAS", (255, 140, 190))
            )
        elif onda == 6:
            # Clímax: O Final Boss desperta em sua forma completa!
            fb = EntidadeMalignaChefe(self.nivel.largura_px // 2, self.nivel.altura_px // 2 - 40)
            fb.aplicar_escalonamento(self.rpg)
            self._ajustar_chefe_modo(fb)
            self.chefes = [fb]
            audio = getattr(self.app, "audio", None)
            if audio:
                audio.tocar_bgm("chefe_final")
                audio.sfx("rugido_chefe")
            self.clarao = 0.9
            self.cor_clarao = (255, 40, 80)
            self.tremor = 4.8
            self.tempo_tremor = 1.4
            self.textos_flutuantes.append(
                TextoFlutuante(self.jogador.rect.midtop, "O SOBERANO DAS TREVAS DESPERTOU!", (255, 60, 90))
            )

    def _inimigos_restantes(self):
        return len(self.inimigos)

    def vida_max_total(self):
        return VIDA_MAXIMA + self.rpg.bonus_vida_maxima

    def _usar_poder_ativo(self):
        poder = self.rpg.poder_atual
        if not poder:
            return
        if self.rpg.mana < poder["custo_mana"]:
            self.textos_flutuantes.append(
                TextoFlutuante(self.jogador.rect.midtop, "Sem Mana!", (130, 185, 255))
            )
            return

        self.rpg.mana -= poder["custo_mana"]
        id_p = poder["id"]
        centro = self.jogador.rect.center
        audio = getattr(self.app, "audio", None)

        if id_p == "esfera_fogo":
            if audio:
                audio.sfx("magia_fogo")
            vetor = VETORES[self.jogador.direcao]
            dano = 2 + (1 if "furia_escolhido" in self.rpg.desbloqueadas else 0)
            self.projeteis.append(ProjetilMagico(centro, vetor, dano=dano, cor=(255, 110, 45)))
            self.jogador.atacar()
        elif id_p == "corte_giratorio":
            if audio:
                audio.sfx("magia_corte")
            self.ondas.append(OndaMagica(centro, 36, (255, 225, 95), 0.32))
            self.jogador.atacar()
            self.particulas += explosao(centro, CORES_PODER, 14)
            area = self.jogador.rect.inflate(64, 64)
            for c_arb in self.nivel.cortar_arbustos(area):
                self.particulas += explosao(c_arb, CORES_FOLHAS)
            golpe_giro = random.randint(10000, 999999)
            dano = self.rpg.dano_espada + 1
            for slime in self.inimigos:
                if area.colliderect(slime.rect):
                    if slime.receber_golpe(golpe_giro, centro, dano=dano):
                        self.textos_flutuantes.append(TextoFlutuante(slime.rect.midtop, f"-{dano}", (255, 225, 95)))
        elif id_p == "nova_gelo":
            if audio:
                audio.sfx("magia_gelo")
            self.ondas.append(OndaMagica(centro, 48, (110, 235, 255), 0.42))
            self.particulas += explosao(centro, [(120, 235, 255), (210, 250, 255)], 16)
            area = self.jogador.rect.inflate(88, 88)
            golpe_gelo = random.randint(10000, 999999)
            for slime in self.inimigos:
                if area.colliderect(slime.rect):
                    slime.receber_golpe(golpe_gelo, centro, dano=1)
                    slime.congelado = 2.6
                    self.textos_flutuantes.append(TextoFlutuante(slime.rect.midtop, "Congelado!", (130, 240, 255)))

            # Congela fontes e água ao redor criando pontes de gelo transitáveis (Pilar 2)
            raio_g = 3
            cx_j, cy_j = self.jogador.rect.centerx // 16, self.jogador.rect.centery // 16
            for dy_g in range(-raio_g, raio_g + 1):
                for dx_g in range(-raio_g, raio_g + 1):
                    tx, ty = cx_j + dx_g, cy_j + dy_g
                    if self.nivel.dentro(tx, ty) and self.nivel.grade[ty][tx] == "~":
                        if not any(pg.cx == tx and pg.cy == ty for pg in self.pontes_gelo):
                            self.pontes_gelo.append(PonteGelo(tx, ty, 9.0))
        elif id_p == "tempestade_raios":
            if audio:
                audio.sfx("magia_raio")
            self.clarao = 0.75
            self.cor_clarao = (210, 160, 255)
            self.tremor = 3.0
            self.tempo_tremor = 0.35
            golpe_raio = random.randint(10000, 999999)
            alvos = [
                s for s in self.inimigos
                if pygame.Vector2(s.rect.center).distance_to(centro) <= 120
            ]
            if not alvos:
                self.ondas.append(OndaMagica(centro, 54, (215, 130, 255), 0.38))
            for slime in alvos:
                self.ondas.append(OndaMagica(slime.rect.center, 24, (220, 145, 255), 0.3))
                self.particulas += explosao(slime.rect.center, [(220, 150, 255), (255, 255, 220)], 14)
                slime.receber_golpe(golpe_raio, centro, dano=3)
                self.textos_flutuantes.append(TextoFlutuante(slime.rect.midtop, "-3 Raio!", (230, 165, 255)))
        elif id_p == "cura_celestial":
            if audio:
                audio.sfx("magia_cura")
            self.jogador.vida_maxima = self.vida_max_total()
            self.jogador.curar(4)
            self.ondas.append(OndaMagica(centro, 32, (120, 250, 155), 0.45))
            self.particulas += explosao(centro, [(120, 250, 155), (255, 240, 150)], 14)
            self.textos_flutuantes.append(TextoFlutuante(self.jogador.rect.midtop, "+2 Corações!", (120, 255, 155)))

    # ------------------------------------------------------------ diretor de cenas
    def _encontrar_ator(self, ident):
        if not ident:
            return self.jogador
        chave = ident.strip().lower()
        if chave in ("heroi", "jogador", "player"):
            return self.jogador
        for npc in self.npcs:
            if chave in (npc.codigo.lower(), npc.dialogo.lower(), npc.aparencia.lower()):
                return npc
        return self.jogador

    def executar_comando_cena(self, comando, arg):
        partes = arg.split()
        if comando == "mapa":
            nome_arq = partes[0]
            if not nome_arq.endswith(".txt"):
                nome_arq += ".txt"
            caminho = PASTA_BASE / "maps" / nome_arq
            if caminho.exists():
                self.trocar_mapa(caminho, usar_porta=False)
                if len(partes) >= 3 and partes[1].isdigit() and partes[2].isdigit():
                    cx, cy = int(partes[1]), int(partes[2])
                    self.jogador.posicionar(cx * TILE + TILE // 2, cy * TILE + TILE)
                    self.camera.centralizar(self.jogador.rect)
        elif comando == "cenario":
            tipo = partes[0].lower() if partes else "normal"
            audio = getattr(self.app, "audio", None)
            if tipo == "cidade":
                self.cenario_especial = CenarioCidade(self.app, destruindo=False)
                if audio:
                    audio.tocar_bgm("apocalipse")
            elif tipo in ("cidade_destruicao", "destruicao"):
                if isinstance(self.cenario_especial, CenarioCidade):
                    self.cenario_especial.destruindo = True
                    self.cenario_especial.tempo_cidade = max(1.5, self.cenario_especial.tempo_cidade)
                else:
                    self.cenario_especial = CenarioCidade(self.app, destruindo=True)
                if audio:
                    audio.tocar_bgm("apocalipse")
                    audio.sfx("magia_raio")
            else:
                self.cenario_especial = None
                if audio and self.em_abertura:
                    audio.tocar_bgm("abertura_sombria")
        elif comando == "musica":
            if partes and hasattr(self.app, "audio"):
                self.app.audio.tocar_bgm(partes[0].lower())
        elif comando == "clima":
            self.clima = partes[0].lower() if partes else "dia"
        elif comando == "clarao":
            nome_cor = partes[0].lower() if partes else "branco"
            self.cor_clarao = CORES_CLARAO.get(nome_cor, (255, 255, 255))
            self.clarao = 1.0
        elif comando == "tremer":
            self.tremor = float(partes[0]) if len(partes) >= 1 else 3.5
            self.tempo_tremor = float(partes[1]) if len(partes) >= 2 else 0.6
            self.app.entrada.vibrar(0.6, int(self.tempo_tremor * 300))
        elif comando == "efeito":
            tipo = partes[0].lower() if partes else "parar"
            if tipo in ("parar", "nenhum", "off"):
                self.efeito_ativo = None
            else:
                ator = self._encontrar_ator(partes[1] if len(partes) >= 2 else "heroi")
                if tipo == "explosao":
                    self.particulas += explosao(ator.rect.center, CORES_FOGO, 16)
                else:
                    self.efeito_ativo = (tipo, ator)
        elif comando == "pose":
            if len(partes) >= 2:
                ator = self._encontrar_ator(partes[0])
                ator.definir_pose(partes[1].lower())
                if partes[1].lower() in ("acordar", "normal", "assustar") and ator is self.jogador:
                    ator.posicionar(*self.nivel.inicio)
            elif len(partes) == 1:
                self.jogador.definir_pose(partes[0].lower())
        elif comando == "olhar":
            if len(partes) >= 2:
                ator = self._encontrar_ator(partes[0])
                direcao = partes[1].lower()
                if direcao in VETORES:
                    ator.direcao = direcao
                else:
                    outro = self._encontrar_ator(direcao)
                    ator.olhar_para_ponto(outro.rect.centerx, outro.rect.centery)
        elif comando == "pular":
            ator = self._encontrar_ator(partes[0] if partes else "heroi")
            ator.pular(130.0)
        elif comando == "emocao":
            if len(partes) >= 2:
                ator = self._encontrar_ator(partes[0])
                ator.mostrar_emocao(partes[1])
            elif len(partes) == 1:
                self.jogador.mostrar_emocao(partes[0])
        elif comando == "posicionar":
            if len(partes) >= 3:
                ator = self._encontrar_ator(partes[0])
                cx, cy = float(partes[1]), float(partes[2])
                ator.posicionar(cx * TILE + TILE // 2, cy * TILE + TILE)
        elif comando == "mover":
            if len(partes) >= 2:
                ator = self._encontrar_ator(partes[0])
                if partes[1].lower() in VETORES:
                    vetor = VETORES[partes[1].lower()]
                    passos = float(partes[2]) if len(partes) >= 3 else 1.0
                    destino = pygame.Vector2(ator.rect.midbottom) + vetor * (passos * TILE)
                    ator.ir_para(destino.x, destino.y)
                    return lambda: ator.andando_roteiro
                elif len(partes) >= 3:
                    cx, cy = float(partes[1]), float(partes[2])
                    ator.ir_para(cx * TILE + TILE // 2, cy * TILE + TILE)
                    return lambda: ator.andando_roteiro
        elif comando == "camera":
            if len(partes) >= 2 and partes[0].isdigit() and partes[1].isdigit():
                cx, cy = int(partes[0]), int(partes[1])
                self.alvo_camera = pygame.Rect(cx * TILE, cy * TILE, TILE, TILE)
            elif partes:
                ator = self._encontrar_ator(partes[0])
                self.alvo_camera = None if ator is self.jogador else ator
        elif comando == "esperar":
            try:
                return float(partes[0])
            except ValueError:
                return 1.0
        return None

    # ------------------------------------------------------------ história
    def iniciar_dialogo(self, nome, opcional=False, npc=None):
        self.npc_falando = npc
        if nome == "inicio":
            self.em_abertura = True
            if hasattr(self.app, "audio"):
                self.app.audio.tocar_bgm("abertura_sombria")
        if nome not in self.historia.dialogos:
            if opcional:
                return
            historia = Historia({"erro": [("fala", "Erro na história", f"O diálogo '{nome}' não existe.")]})
            conversa = Conversa(historia, "erro", self.flags)
        else:
            from cenas.loja import CenaLoja
            acoes = {
                "curar": lambda: self.jogador.curar(VIDA_MAXIMA),
                "loja": lambda: self.app.empilhar(CenaLoja(self.app, self)),
                "missao_remedio": lambda: self.missoes.aceitar("remedio_ancestral", self),
                "missao_fonte": lambda: self.missoes.aceitar("fonte_corrompida", self),
                "missao_lamina": lambda: self.missoes.aceitar("lamina_guardioes", self),
                "entregar_remedio": lambda: self.missoes.entregar("remedio_ancestral", self),
                "entregar_fonte": lambda: self.missoes.entregar("fonte_corrompida", self),
                "entregar_lamina": lambda: self.missoes.entregar("lamina_guardioes", self),
                "entregar_reliquias": self.entregar_reliquias_anciao,
            }
            conversa = Conversa(self.historia, nome, self.flags, acoes, diretor=self.executar_comando_cena)
        velocidade = VELOCIDADES_TEXTO[self.app.config["velocidade_texto"]]
        self.dialogo = CaixaDialogo(conversa, self.app.fontes.normal, velocidade, retratos=self.retrato_falante)
        if self.dialogo.terminou:  # diálogo sem nenhuma fala (só @marcar etc.)
            self.dialogo = None

    def retrato_falante(self, nome):
        """Escolhe o rosto de quem fala: pelo nome na fala ou pelo NPC com quem o herói conversa."""
        aparencia = aparencia_por_nome(nome)
        if aparencia is None and getattr(self, "npc_falando", None) is not None and nome not in SEM_RETRATO:
            aparencia = self.npc_falando.aparencia
        if aparencia is None or aparencia == "placa":
            return None
        return self.app.gfx.retrato(aparencia)

    def evento(self, nome):
        """Liga a marca `nome` e roda o diálogo 'ao_<nome>', se existir."""
        self.flags.add(nome)
        self.iniciar_dialogo(f"ao_{nome}", opcional=True)

    def npc_a_frente(self):
        area = self.jogador.area_interacao()
        for npc in self.npcs:
            if area.colliderect(npc.rect):
                return npc
        return None

    def iniciar_apresentacao_chefe(self, chefe):
        audio = getattr(self.app, "audio", None)
        if audio:
            audio.sfx("gong_chefe")
        self.apresentacao_chefe = {
            "chefe": chefe,
            "tempo": 2.4,
            "duracao": 2.4,
        }
        self.tremor = 2.5
        self.tempo_tremor = 0.35

    def invocar_vento_guia(self):
        proximo = self.rpg.proximo_chefe()
        if not proximo:
            self.aviso_mapa = "✨ Todos os Guardiões foram libertados e purificados!"
            self.tempo_aviso_mapa = 2.5
            return
        id_ch, nome_ch, nv_req, arq_covil, arq_orig, _, covil_ch = proximo
        pos_alvo = None
        for rect_porta, destino in self.nivel.portas:
            if destino.name == arq_covil:
                pos_alvo = pygame.Vector2(rect_porta.center)
                break

        if pos_alvo is None:
            for rect_porta, destino in self.nivel.portas:
                if destino.name == arq_orig:
                    pos_alvo = pygame.Vector2(rect_porta.center)
                    break

        if pos_alvo is None and self.nivel.portas:
            pos_alvo = pygame.Vector2(self.nivel.portas[0][0].center)

        if pos_alvo is None:
            pos_alvo = pygame.Vector2(self.jogador.rect.center) + pygame.Vector2(0, -60)

        audio = getattr(self.app, "audio", None)
        if audio:
            audio.sfx("dialogo_bip")
        for i in range(4):
            offset_orig = pygame.Vector2(random.uniform(-10, 10), random.uniform(-10, 10))
            vg = VentoGuia(pygame.Vector2(self.jogador.rect.center) + offset_orig, pos_alvo)
            vg.tempo = -i * 0.12
            self.ventos_guia.append(vg)

        self.aviso_mapa = f"🍃 Vento Guia: Rumo a {nome_ch} ({covil_ch})!"
        self.tempo_aviso_mapa = 3.2

    def executar_teleporte_astral(self, dados_monolito):
        audio = getattr(self.app, "audio", None)
        if audio:
            audio.sfx("teleporte")
        self.clarao = 0.85
        self.cor_clarao = (140, 225, 255)
        self.feixe_teleporte = {
            "pos": (self.jogador.rect.centerx, self.jogador.rect.centery),
            "tempo": 0.8,
            "dados": dados_monolito,
            "trocado": False,
        }
        self.conquistas.desbloquear("viajante_astral", self)

    def entregar_reliquias_anciao(self):
        qtd_novas = len(self.rpg.reliquias_coletadas)
        if qtd_novas == 0:
            self.aviso_mapa = "Ancião: Traga-me as 6 Relíquias Antigas quando encontrá-las!"
            self.tempo_aviso_mapa = 3.5
            return
        for r in list(self.rpg.reliquias_coletadas):
            self.rpg.reliquias_entregues.add(r)
        self.rpg.reliquias_coletadas.clear()
        tot_entregue = len(self.rpg.reliquias_entregues)

        audio = getattr(self.app, "audio", None)
        if audio:
            audio.sfx("fanfarra_item")
        self.clarao = 0.6
        self.cor_clarao = (255, 235, 120)
        self.jogador.curar(self.vida_max_total())
        self.rpg.mana = self.rpg.mana_maxima
        self.rpg.bombas = self.rpg.capacidade_max_bombas
        self.conquistas.desbloquear("colecionador_reliquias", self)

        from rpg import TextoFlutuante
        self.textos_flutuantes.append(
            TextoFlutuante(self.jogador.rect.midtop, f"* Bênção Ancestral: {tot_entregue}/6 Relíquias! *", (255, 230, 90))
        )
        self.aviso_mapa = f"* Relíquias Entregues ({tot_entregue}/6)! Capacidade e Alcance Ampliados!"
        self.tempo_aviso_mapa = 4.0

    # ------------------------------------------------------------ lógica
    def soltar_coracao(self, centro, chance):
        if random.random() < chance:
            self.coracoes.append(Coracao(centro))

    def soltar_moeda(self, centro, tipo="cobre", qtd=1):
        for _ in range(qtd):
            offset = (random.uniform(-4, 4), random.uniform(-4, 4))
            p = (centro[0] + offset[0], centro[1] + offset[1])
            self.moedas.append(Moeda(p, tipo))

    def _atualizar_efeitos_cena(self, dt, entrada):
        self.clarao = max(0.0, self.clarao - dt * 2.2)
        self.tempo_aviso_mapa = max(0.0, self.tempo_aviso_mapa - dt)
        if self.tempo_tremor > 0:
            self.tempo_tremor = max(0.0, self.tempo_tremor - dt)
            if self.tempo_tremor <= 0:
                self.tremor = 0.0

        if self.cenario_especial is not None:
            self.cenario_especial.atualizar_cenario(dt, entrada)

        if self.clima == "chuva":
            for g in self.gotas_chuva:
                g[0] = (g[0] - 75 * dt) % LARGURA
                g[1] = (g[1] + 210 * dt) % ALTURA

        if self.efeito_ativo is not None and random.random() < dt * 15:
            tipo, ator = self.efeito_ativo
            cores = CORES_PODER if tipo == "poder" else (CORES_FOGO if tipo == "fogo" else CORES_FUMACA)
            px = ator.rect.centerx + random.uniform(-10, 10)
            py = ator.rect.centery + random.uniform(-10, 4)
            p = Particula((px, py), random.choice(cores))
            p.vel = pygame.Vector2(random.uniform(-10, 10), random.uniform(-35, -12))
            self.particulas.append(p)

    def _seguir_camera(self, dt):
        if isinstance(self.alvo_camera, pygame.Rect):
            self.camera.seguir(self.alvo_camera, dt)
        elif self.alvo_camera is not None:
            self.camera.seguir(self.alvo_camera.rect, dt)
        else:
            self.camera.seguir(self.jogador.rect, dt)

    def atualizar(self, dt):
        from cenas.arvore_habilidades import ArvoreHabilidades
        from cenas.mapa_mundo import MapaMundo
        from cenas.pausa import Pausa

        entrada = self.app.entrada
        audio = getattr(self.app, "audio", None)
        self.tempo_cenario += dt
        self.rpg.atualizar(dt)
        self.jogador.vida_maxima = self.vida_max_total()
        self.jogador.fator_velocidade_rpg = self.rpg.fator_velocidade
        self.ambiente.atualizar(dt)
        self.destaque_bussola = max(0.0, getattr(self, "destaque_bussola", 0.0) - dt)
        self.tempo_objetivo_visivel = max(0.0, getattr(self, "tempo_objetivo_visivel", 0.0) - dt)
        for obj3d in getattr(self.nivel, "objetos_3d", []):
            obj3d.atualizar(self.tempo_cenario)
        self.particulas = [p for p in self.particulas if p.atualizar(dt)]
        self.ondas = [o for o in self.ondas if o.atualizar(dt)]
        self.textos_flutuantes = [t for t in self.textos_flutuantes if t.atualizar(dt)]
        self.conquistas.atualizar(dt)
        self.conquistas.verificar_estado(self)
        for c in self.coracoes:
            c.atualizar(dt)
        for portal in self.portais_misticos:
            portal.atualizar(dt, self)
        for monolito in self.monolitos:
            monolito.atualizar(dt, self)
        self.reliquias = [r for r in self.reliquias if r.atualizar(dt, self)]
        self.ventos_guia = [vg for vg in self.ventos_guia if vg.atualizar(dt)]

        if self.feixe_teleporte is not None:
            self.feixe_teleporte["tempo"] -= dt
            if self.feixe_teleporte["tempo"] <= 0.4 and not self.feixe_teleporte["trocado"]:
                self.feixe_teleporte["trocado"] = True
                dados = self.feixe_teleporte["dados"]
                caminho = PASTA_BASE / "maps" / dados["mapa"]
                self.trocar_mapa(caminho, usar_porta=False, tocar_sfx_porta=False)
                self.jogador.posicionar(*dados["pos"])
                self.camera.centralizar(self.jogador.rect)
            if self.feixe_teleporte["tempo"] <= 0:
                self.feixe_teleporte = None

        if self.apresentacao_chefe is not None:
            self.apresentacao_chefe["tempo"] -= dt
            if self.apresentacao_chefe["tempo"] <= 0:
                self.apresentacao_chefe = None

        self._atualizar_efeitos_cena(dt, entrada)

        if getattr(self, "timer_transicao_final", 0.0) > 0 and not self.dialogo:
            self.timer_transicao_final -= dt
            if self.timer_transicao_final <= 0:
                from cenas.final import CenaFinal
                self.app.trocar(CenaFinal(self.app, self.rpg))
                return

        # Impacto visceral de combate (Hitstop de ~3 quadros)
        if self.hitstop > 0:
            self.hitstop = max(0.0, self.hitstop - dt)
            return

        # Ciclo Dia & Noite suave e contínuo nas áreas externas (Pilar 4)
        if not self.nivel.eh_interior:
            self.relogio_dia_noite = (self.relogio_dia_noite + dt * 0.012) % 1.0

        # Sincroniza equipamentos equipados no herói
        self.jogador.arma_equipada = self.rpg.arma_equipada
        self.jogador.escudo_equipado = self.rpg.escudo_equipado
        self.jogador.tunica_equipada = self.rpg.tunica_equipada

        # Animação de fade-out / fade-in na entrada e saída de lugares
        if self.fade_estado == "out":
            self.fade_alfa = min(1.0, self.fade_alfa + dt * 4.5)
            if self.fade_alfa >= 1.0 and self.fade_destino is not None:
                destino = self.fade_destino
                usar_porta = self.fade_usar_porta
                self.fade_destino = None
                self.trocar_mapa(destino, usar_porta=usar_porta, tocar_sfx_porta=False)
            return
        elif self.fade_estado == "in":
            self.fade_alfa = max(0.0, self.fade_alfa - dt * 3.8)
            if self.fade_alfa <= 0.0:
                self.fade_estado = None

        if entrada.apertou("pausa"):
            self.app.empilhar(Pausa(self.app, self))
            return

        if not self.dialogo and self.estado == "jogando":
            if entrada.apertou("mapa") and not self.modo_chefe:
                self.app.empilhar(MapaMundo(self.app, self))
                return
            if entrada.apertou("habilidades"):
                self.app.empilhar(ArvoreHabilidades(self.app, self))
                return
            if entrada.apertou("vento_guia"):
                self.invocar_vento_guia()
                self.tempo_objetivo_visivel = 5.0
            if entrada.apertou("objetivo"):
                # O painel do objetivo fica escondido e só aparece por 5 segundos ao apertar [O]
                self.tempo_objetivo_visivel = 5.0
                if hasattr(self.app, "audio"):
                    self.app.audio.sfx("menu_mover")
            if entrada.apertou("trocar_magia"):
                novo = self.rpg.trocar_poder()
                if novo:
                    self.textos_flutuantes.append(
                        TextoFlutuante(self.jogador.rect.midtop, novo["nome"], novo["cor"])
                    )
            if entrada.apertou("magia"):
                self._usar_poder_ativo()
            if entrada.apertou("bomba") and self.rpg.bombas > 0 and not self.jogador.atacando:
                self.rpg.bombas -= 1
                self.bombas.append(Bomba(self.jogador.rect.center))
                if audio:
                    audio.sfx("menu_confirmar")

        if self.dialogo:
            self.jogador.atualizar_cena(dt, self.nivel)
            for npc in self.npcs:
                npc.atualizar(dt, self.nivel, em_dialogo=True)
            self._seguir_camera(dt)
            self.dialogo.atualizar(dt, entrada)
            if self.dialogo.terminou:
                self.dialogo = None
                if self.em_abertura:
                    self.em_abertura = False
                    if hasattr(self.app, "audio"):
                        self.app.audio.tocar_bgm_mapa(self.nivel.caminho.name)
                if "vitoria_final" in self.flags:
                    from cenas.final import CenaFinal
                    self.app.trocar(CenaFinal(self.app, self.rpg))
                    return
            return

        if self.estado == "derrota":
            if self.modo_chefe:
                if entrada.apertou("confirmar"):
                    self.app.trocar(Jogo(self.app, dialogo_inicial=None, modo_chefe=dict(self.modo_chefe)))
                elif entrada.apertou("voltar") or entrada.apertou("pausa"):
                    from cenas.modo_chefes import SelecaoChefes
                    self.app.trocar(SelecaoChefes(self.app, self.modo_chefe.get("indice_selecao", 0)))
            elif entrada.apertou("confirmar"):
                self.app.trocar(Jogo(self.app))
            return

        jogador = self.jogador
        audio = getattr(self.app, "audio", None)

        if entrada.apertou("confirmar") or entrada.apertou("acao"):
            # Interação com Monólito de Teleporte (Pilar 3)
            for monolito in self.monolitos:
                if monolito.id_waypoint in self.rpg.waypoint_descobertos and monolito.pos.distance_to(jogador.rect.center) < 32.0:
                    from cenas.teleporte import CenaTeleporte
                    self.app.empilhar(CenaTeleporte(self.app, self, id_origem=monolito.id_waypoint))
                    return

            # Interação com Portal Fantasma (Pilar 2)
            for portal in self.portais_misticos:
                if portal.chefe_id in self.rpg.chefes_derrotados:
                    if portal.rect.inflate(18, 18).colliderect(jogador.rect):
                        if audio:
                            audio.sfx("eco_fantasma")
                        self.aviso_mapa = f"✨ Eco Espiritual: O Guardião {portal.nome_chefe} foi purificado e descansa em paz."
                        self.tempo_aviso_mapa = 3.5
                        self.textos_flutuantes.append(TextoFlutuante(jogador.rect.midtop, "Guardião Purificado!", (180, 235, 255)))
                        return

        if entrada.apertou("acao"):
            # Interação com Baús de Tesouro (Pilar 1)
            area_acao = jogador.area_interacao()
            for bau in self.baus:
                if not bau.aberto and area_acao.colliderect(bau.rect):
                    bau.interagir(self)
                    return

            npc = self.npc_a_frente()
            if npc:
                npc.olhar_para(jogador.rect)
                if audio:
                    audio.sfx("menu_confirmar")
                self.iniciar_dialogo(npc.dialogo, npc=npc)
                return
            estava_atacando = jogador.atacando
            jogador.atacar()
            if jogador.atacando and not estava_atacando and audio:
                audio.sfx("espada")

        vida_antes = jogador.vida
        z_antes = jogador.z
        dash_antes = jogador.tempo_dash
        jogador.atualizar(dt, entrada, self.nivel)
        if z_antes <= 0 and jogador.z > 0 and audio:
            audio.sfx("pulo")
        if dash_antes <= 0 and jogador.tempo_dash > 0 and audio:
            audio.sfx("dash")
        if jogador.acabou_de_pousar:
            if audio:
                audio.sfx("nado" if jogador.nadando else "pouso")
            cores_pouso = (
                [(120, 210, 255), (220, 250, 255)]
                if jogador.nadando
                else [(220, 205, 175), (185, 170, 140)]
            )
            for _ in range(5):
                poeira = Particula(jogador.rect.midbottom, random.choice(cores_pouso))
                poeira.vel = pygame.Vector2(random.uniform(-38, 38), random.uniform(-12, 8))
                poeira.vida = 0.2
                self.particulas.append(poeira)
        elif jogador.nadando and jogador.andando and random.random() < dt * 15:
            gota = Particula(jogador.rect.center, random.choice([(120, 210, 255), (215, 248, 255)]))
            gota.vel = pygame.Vector2(random.uniform(-24, 24), random.uniform(-18, 6))
            gota.vida = 0.24
            self.particulas.append(gota)
        elif jogador.correndo and jogador.andando and random.random() < dt * 18:
            poeira = Particula(jogador.rect.midbottom, random.choice([(210, 195, 165), (180, 165, 135)]))
            poeira.vel *= 0.25
            poeira.vida = 0.22
            self.particulas.append(poeira)

        for npc in self.npcs:
            npc.atualizar(dt, self.nivel, em_dialogo=False)

        # Checa se o herói está caminhando sobre uma ponte de gelo criada por magia
        if any(pg.rect.collidepoint(jogador.rect.center) for pg in self.pontes_gelo):
            jogador.nadando = False

        # Puzzles de Masmorra: Blocos de Pedra, Placas de Pressão e Portões de Ferro (Pilar 2)
        for bloco in self.blocos:
            bloco.atualizar(dt)
            if jogador.rect.inflate(6, 6).colliderect(bloco.rect):
                vetor_emp = VETORES.get(jogador.direcao, pygame.Vector2())
                bloco.empurrar(vetor_emp, dt, self.nivel, audio)

        entidades_placas = [jogador] + self.blocos
        gatilhos_ativos = set()
        for placa in self.placas:
            if placa.atualizar(entidades_placas, audio):
                gatilhos_ativos.add(placa.id_gatilho)

        for portao in self.portoes:
            portao.definir_aberto(portao.id_gatilho in gatilhos_ativos, audio)
            portao.atualizar(dt)

        self.nivel.obstaculos = (
            [n.rect for n in self.npcs]
            + [b.rect for b in self.blocos]
            + [p.rect for p in self.portoes if p.solido]
            + [w.rect for w in self.paredes_rachadas]
        )

        # Atualiza bombas, moedas, itens de missão e baús
        self.bombas = [b for b in self.bombas if b.atualizar(dt, self)]
        self.moedas = [m for m in self.moedas if m.atualizar(dt, jogador, self.rpg, audio, self.textos_flutuantes)]
        self.itens_quest = [it for it in self.itens_quest if it.atualizar(dt, self)]
        self.pontes_gelo = [pg for pg in self.pontes_gelo if pg.atualizar(dt)]
        for b in self.baus:
            b.atualizar(dt)

        # Interação com Altar / Ponto de Salvamento
        ponto_salve = None
        for psx, psy in getattr(self.nivel, "pontos_salvamento", []):
            if pygame.Vector2(jogador.rect.center).distance_to((psx, psy)) < 26:
                ponto_salve = (psx, psy)
                break

        if ponto_salve and (entrada.apertou("acao") or entrada.apertou("confirmar")):
            salvar_jogo(self)
            self.jogador.vida = self.vida_max_total()
            self.rpg.mana = self.rpg.mana_maxima
            if audio:
                audio.sfx("salvar")
            self.textos_flutuantes.append(
                TextoFlutuante(jogador.rect.midtop, "Jogo Salvo! Vida & Mana Restauradas!", (110, 255, 180))
            )
            self.clarao = 0.45
            self.cor_clarao = (255, 240, 140)
            self.ondas.append(OndaMagica(ponto_salve, 36, (255, 230, 110), 0.4))
            for _ in range(14):
                p = Particula(ponto_salve, random.choice([(255, 230, 100), (120, 240, 255), (255, 255, 230)]))
                p.vel = pygame.Vector2(random.uniform(-35, 35), random.uniform(-40, -10))
                self.particulas.append(p)

        # Portas para entrar / sair da casinha (ou outros mapas) com fade-out / fade-in.
        for rect_porta, destino in self.nivel.portas:
            if jogador.rect.colliderect(rect_porta):
                # Checa se o chefe desta área já foi derrotado (bloqueio permanente para sempre)
                if destino.name in MAPA_PARA_CHEFE_ID:
                    chefe_id = MAPA_PARA_CHEFE_ID[destino.name]
                    if chefe_id in self.rpg.chefes_derrotados:
                        nome_ch = REQUISITOS_MAPA_CHEFE.get(destino.name, (0, "Guardião"))[1]
                        self.textos_flutuantes.append(
                            TextoFlutuante(self.jogador.rect.midtop, "Área Selada Para Sempre!", (255, 110, 110))
                        )
                        self.aviso_mapa = f"🔒 Área Selada: {nome_ch} já foi derrotado! Este local foi purificado e selado para sempre."
                        self.tempo_aviso_mapa = 3.5
                        if audio:
                            audio.sfx("bloqueio")
                        jogador.empurrar(rect_porta.center, 90, 0.25)
                        return

                if destino.name in REQUISITOS_MAPA_CHEFE:
                    req_nv, nome_ch = REQUISITOS_MAPA_CHEFE[destino.name]
                    if self.rpg.nivel < req_nv:
                        self.textos_flutuantes.append(
                            TextoFlutuante(self.jogador.rect.midtop, f"Requer Nível {req_nv}!", (255, 95, 95))
                        )
                        self.aviso_mapa = f"🔒 Portão Selado: Requer Nível {req_nv} para {nome_ch}! (Seu Nv: {self.rpg.nivel})"
                        self.tempo_aviso_mapa = 3.5
                        if audio:
                            audio.sfx("bloqueio")
                        jogador.empurrar(rect_porta.center, 90, 0.25)
                        return

                if destino.name == "castelo_salao_trono.txt":
                    if len(self.rpg.chefes_derrotados) < 15:
                        faltam = 15 - len(self.rpg.chefes_derrotados)
                        self.textos_flutuantes.append(
                            TextoFlutuante(self.jogador.rect.midtop, f"Selo Abissal: Faltam {faltam} Guardiões!", (255, 90, 110))
                        )
                        self.aviso_mapa = f"🔒 O Selo das Sombras exige os 15 Guardiões derrotados! ({len(self.rpg.chefes_derrotados)}/15)"
                        self.tempo_aviso_mapa = 3.5
                        if audio:
                            audio.sfx("bloqueio")
                        jogador.empurrar(rect_porta.center, 90, 0.25)
                        return
                elif self.boss_rush_ativo and not self.boss_rush_concluido and self.nivel.caminho.name == "castelo_salao_trono.txt":
                    self.textos_flutuantes.append(
                        TextoFlutuante(self.jogador.rect.midtop, "As portas estão seladas até a vitória final!", (255, 80, 100))
                    )
                    jogador.empurrar(rect_porta.center, 80, 0.2)
                    return
                self.iniciar_transicao_mapa(destino, usar_porta=True)
                return

        # Golpe de espada: corta arbustos e acerta slimes.
        if jogador.atacando:
            espada = jogador.rect_espada()
            for centro in self.nivel.cortar_arbustos(espada):
                if audio:
                    audio.sfx("arbusto")
                self.particulas += explosao(centro, CORES_FOLHAS)
                self.soltar_coracao(centro, CHANCE_CORACAO_ARBUSTO)
                if random.random() < 0.45:
                    self.soltar_moeda(centro, "cobre", 1)

            # Estilhaça vasos de cerâmica com golpe de espada (Pilar 4)
            for vaso in self.vasos:
                if not vaso.quebrado and espada.colliderect(vaso.rect):
                    vaso.quebrar(self)

            dano_esp = self.rpg.dano_espada
            for slime in self.inimigos:
                if espada.colliderect(slime.rect):
                    if slime.receber_golpe(jogador.golpe_id, jogador.rect.center, dano=dano_esp):
                        self.hitstop = 0.045
                        if audio:
                            audio.sfx("hit_inimigo")
                        self.rpg.mana = min(self.rpg.mana_maxima, self.rpg.mana + 1.5)
                        self.textos_flutuantes.append(
                            TextoFlutuante(slime.rect.midtop, f"-{dano_esp}", (255, 240, 150))
                        )
            for chefe in self.chefes:
                if not chefe.morrendo and espada.colliderect(chefe.rect):
                    if chefe.receber_golpe(jogador.golpe_id, jogador.rect.center, dano=dano_esp):
                        self.hitstop = 0.045
                        if audio:
                            audio.sfx("hit_inimigo")
                        self.rpg.mana = min(self.rpg.mana_maxima, self.rpg.mana + 1.5)
                        self.textos_flutuantes.append(
                            TextoFlutuante(chefe.rect.midtop, f"-{dano_esp}", (255, 240, 150))
                        )

        # Atualiza projéteis mágicos (ex.: Esfera de Fogo)
        novos_proj = []
        for proj in self.projeteis:
            if not proj.atualizar(dt, self.nivel):
                self.particulas += explosao(proj.pos, CORES_FOGO, 8)
                continue
            if random.random() < 0.65:
                rastro = Particula(proj.pos, random.choice(CORES_FOGO))
                rastro.vel *= 0.2
                self.particulas.append(rastro)

            # Interação Elemental: Tochas apagadas acesas por fogo (Pilar 2)
            for tx, ty, tipo_tocha in getattr(self.nivel, "tochas", []):
                if (tx, ty) not in self.tochas_acesas and proj.rect.collidepoint(tx, ty):
                    self.tochas_acesas.add((tx, ty))
                    self.particulas += explosao((tx, ty), [(255, 140, 50), (255, 230, 90)], 14)
                    self.textos_flutuantes.append(TextoFlutuante((tx, ty - 6), "Tocha Acesa!", (255, 215, 80)))

            acertou = False
            for slime in self.inimigos:
                if proj.rect.colliderect(slime.rect):
                    slime.receber_golpe(proj.golpe_id, proj.pos, dano=proj.dano)
                    if audio:
                        audio.sfx("hit_inimigo")
                    self.particulas += explosao(proj.pos, CORES_FOGO, 12)
                    self.textos_flutuantes.append(
                        TextoFlutuante(slime.rect.midtop, f"-{proj.dano}", (255, 130, 60))
                    )
                    acertou = True
                    break
            if not acertou:
                for chefe in self.chefes:
                    if not chefe.morrendo and proj.rect.colliderect(chefe.rect):
                        chefe.receber_golpe(proj.golpe_id, proj.pos, dano=proj.dano)
                        if audio:
                            audio.sfx("hit_inimigo")
                        self.particulas += explosao(proj.pos, CORES_FOGO, 12)
                        self.textos_flutuantes.append(
                            TextoFlutuante(chefe.rect.midtop, f"-{proj.dano}", (255, 130, 60))
                        )
                        acertou = True
                        break
            if not acertou:
                novos_proj.append(proj)
        self.projeteis = novos_proj

        for inimigo in self.inimigos:
            inimigo.atualizar(dt, self.nivel, jogador, self.projeteis_inimigos, self.particulas)
            if not jogador.no_ar and inimigo.rect.colliderect(jogador.rect):
                jogador.levar_dano(getattr(inimigo, "dano_contato", 1), inimigo.rect.center, self.rpg, audio)
                inimigo.empurrar(jogador.rect.center, 120, 0.2)  # quica para trás

        novos_proj_ini = []
        for p_ini in self.projeteis_inimigos:
            if not p_ini.atualizar(dt, self.nivel):
                continue
            if not jogador.no_ar and p_ini.rect.colliderect(jogador.rect):
                jogador.levar_dano(p_ini.dano, p_ini.pos, self.rpg, audio)
                if audio:
                    audio.sfx("hit_inimigo")
                self.particulas += explosao(p_ini.pos, CORES_ZUMBI, 8)
                continue
            novos_proj_ini.append(p_ini)
        self.projeteis_inimigos = novos_proj_ini

        # Atualiza Chefões e projéteis dos chefões
        for chefe in self.chefes:
            chefe.atualizar_chefe(dt, self.nivel, jogador, self.projeteis_chefes, self.particulas, self.ondas, audio)
            if not jogador.no_ar and not chefe.morrendo and chefe.rect.colliderect(jogador.rect):
                jogador.levar_dano(getattr(chefe, "dano_contato", 2), chefe.rect.center, self.rpg, audio)
                chefe.empurrar(jogador.rect.center, 80, 0.2)

        novos_proj_c = []
        for pc in self.projeteis_chefes:
            if not pc.atualizar(dt, self.nivel):
                continue
            if not jogador.no_ar and pc.rect.colliderect(jogador.rect):
                jogador.levar_dano(pc.dano, pc.pos, self.rpg, audio)
                if audio:
                    audio.sfx("hit_inimigo")
                self.particulas += explosao(pc.pos, [(255, 90, 60), (255, 220, 140)], 8)
                continue
            novos_proj_c.append(pc)
        self.projeteis_chefes = novos_proj_c

        # Processa derrota de chefões
        chefes_vivos = []
        for chefe in self.chefes:
            if chefe.morrendo and chefe.tempo_morte <= 0:
                if audio:
                    audio.sfx("morte_inimigo")
                for _ in range(3):
                    self.soltar_coracao(chefe.rect.center, 1.0)
                # Drop massivo de ouro do guardião
                self.soltar_moeda(chefe.rect.center, "ouro", 4)
                subiu = self.rpg.ganhar_xp(chefe.xp_recompensa)
                self.rpg.pontos_habilidade += 1
                if not chefe.fantasma:
                    self.rpg.chefes_derrotados.add(chefe.id_chefe)
                    self.textos_flutuantes.append(
                        TextoFlutuante(chefe.rect.midtop, f"{chefe.nome.upper()} DERROTADO! (+1 PH)", (255, 235, 90))
                    )
                    if len(self.rpg.chefes_derrotados) == 15:
                        self.textos_flutuantes.append(
                            TextoFlutuante(self.jogador.rect.center, "TODOS OS 15 CHEFES DERROTADOS! O TRONO AGUARDA!", (255, 215, 90))
                        )
                else:
                    self.textos_flutuantes.append(
                        TextoFlutuante(chefe.rect.midtop, f"{chefe.nome} Dissipado!", (210, 160, 255))
                    )
                if isinstance(chefe, EntidadeMalignaChefe) and self.modo_chefe:
                    self.boss_rush_concluido = True
                elif isinstance(chefe, EntidadeMalignaChefe):
                    self.boss_rush_concluido = True
                    if audio:
                        audio.tocar_bgm("vitoria", forcar=True)
                    self.clarao = 1.0
                    self.cor_clarao = (255, 255, 240)
                    self.evento("vitoria_final")
                    self.conquistas.desbloquear("vitoria_final", self)
                    self.timer_transicao_final = 5.0
            else:
                chefes_vivos.append(chefe)
        self.chefes = chefes_vivos

        # Avanço do Boss Rush
        if self.boss_rush_ativo and not self.chefes and not self.boss_rush_concluido:
            self.boss_rush_timer_espera -= dt
            if self.boss_rush_timer_espera <= 0:
                self.boss_rush_onda += 1
                self.boss_rush_timer_espera = 2.0
                self._spawnar_onda_boss_rush(self.boss_rush_onda)

        mortos = [s for s in self.inimigos if not s.vivo]
        for inimigo in mortos:
            self.inimigos.remove(inimigo)
            if audio:
                audio.sfx("morte_inimigo")
            cor_part = getattr(inimigo, "cor_particulas", CORES_SLIME_AZUL)
            self.particulas += explosao(inimigo.rect.center, cor_part, 12)
            self.soltar_coracao(inimigo.rect.center, CHANCE_CORACAO_SLIME)

            # Drop de Moedas característico e proporcional (Pilar 1)
            tipo_m = getattr(inimigo, "tipo_id", getattr(inimigo, "tipo", "slime"))
            if "troll" in str(tipo_m):
                self.soltar_moeda(inimigo.rect.center, "prata", 2)
                if random.random() < 0.4:
                    self.soltar_moeda(inimigo.rect.center, "ouro", 1)
            elif "duende" in str(tipo_m):
                self.soltar_moeda(inimigo.rect.center, "cobre", 2)
                self.soltar_moeda(inimigo.rect.center, "prata", 1)
            elif "zumbi" in str(tipo_m):
                self.soltar_moeda(inimigo.rect.center, "prata", 1)
            else:
                self.soltar_moeda(inimigo.rect.center, "cobre", 1)
                if random.random() < 0.25:
                    self.soltar_moeda(inimigo.rect.center, "prata", 1)

            # Registra monstro derrotado para missões de combate (Pilar 3)
            self.missoes.registrar_monstro_derrotado(self)

            xp_ganho = getattr(inimigo, "xp_recompensa", 15)
            subiu = self.rpg.ganhar_xp(xp_ganho)
            self.textos_flutuantes.append(
                TextoFlutuante(inimigo.rect.center, f"+{xp_ganho} XP", (120, 235, 255))
            )
            self.conquistas.desbloquear("primeiro_combate", self)
            self.conquistas.monstros_derrotados_totais += 1
            if self.conquistas.monstros_derrotados_totais >= 15:
                self.conquistas.desbloquear("cacador_monstros", self)
            if subiu:
                if audio:
                    audio.sfx("level_up")
                jogador.vida_maxima = self.vida_max_total()
                jogador.curar(jogador.vida_maxima)
                self.ondas.append(OndaMagica(jogador.rect.center, 44, (255, 230, 100), 0.5))
                self.particulas += explosao(jogador.rect.center, CORES_PODER, 18)
                self.textos_flutuantes.append(
                    TextoFlutuante(jogador.rect.midtop, f"NÍVEL {self.rpg.nivel}! (+1 PH)", (255, 235, 90))
                )

        for coracao in [c for c in self.coracoes if c.rect.colliderect(jogador.rect)]:
            if jogador.vida < jogador.vida_maxima:
                if audio:
                    audio.sfx("coracao")
                jogador.curar(2)
                self.coracoes.remove(coracao)

        if jogador.vida < vida_antes:
            if audio:
                audio.sfx("dano_jogador")
            entrada.vibrar(0.6, 180)
            if "barreira_astral" in self.rpg.desbloqueadas:
                self.ondas.append(OndaMagica(jogador.rect.center, 38, (255, 240, 140), 0.35))
                golpe_bar = random.randint(10000, 999999)
                for s in self.inimigos:
                    if jogador.rect.inflate(64, 64).colliderect(s.rect):
                        s.receber_golpe(golpe_bar, jogador.rect.center, dano=1)

        self._seguir_camera(dt)

        if self.modo_chefe:
            self._atualizar_modo_chefe(dt)

        if jogador.vida <= 0:
            self.estado = "derrota"
            if audio:
                audio.tocar_bgm("derrota", forcar=True)
            self.particulas += explosao(jogador.rect.center, [(88, 179, 63), (247, 200, 160)], 16)

    # ------------------------------------------------------------ desenho
    def desenhar(self, tela):
        fonte = self.app.fontes.normal
        gfx = self.app.gfx

        if self.cenario_especial is not None:
            self.cenario_especial.desenhar_cenario(tela)
        else:
            tela.fill(COR_FUNDO)
            ox, oy = self.camera.offset
            if self.tremor > 0:
                ox += round(random.uniform(-self.tremor, self.tremor))
                oy += round(random.uniform(-self.tremor, self.tremor))
            self.nivel.desenhar_cenario_vivo(tela, ox, oy, self.tempo_cenario)
            self.ambiente.desenhar_chao(tela, ox, oy, self.clima)

            # Placas de pressão e pontes de gelo no solo
            for pl in self.placas:
                pl.desenhar(tela, self.camera)
            for pg in self.pontes_gelo:
                pg.desenhar(tela, self.camera)
            for pr in self.paredes_rachadas:
                pr.desenhar(tela, self.camera)
            for po in self.portoes:
                po.desenhar(tela, self.camera)

            for coracao in self.coracoes:
                coracao.desenhar(tela, self.camera, gfx)
            for moeda in self.moedas:
                moeda.desenhar(tela, self.camera)

            # Quem está mais embaixo na tela é desenhado por cima (Y-sorting com objetos 3D e baús/blocos).
            entidades = (
                self.inimigos
                + self.npcs
                + self.chefes
                + self.baus
                + self.blocos
                + self.bombas
                + self.itens_quest
                + self.vasos
                + self.reliquias
            )
            if self.estado != "derrota":
                entidades.append(self.jogador)
            itens_ordenados = [(e.rect.bottom, 0, e) for e in entidades]
            for i, obj3d in enumerate(getattr(self.nivel, "objetos_3d", [])):
                itens_ordenados.append((obj3d.y_ord, 1 + i, obj3d))
            for _, tipo_item, item in sorted(itens_ordenados, key=lambda x: (x[0], x[1])):
                if tipo_item == 0:
                    if hasattr(item, "desenhar"):
                        # Verifica quantos argumentos o método desenhar espera
                        try:
                            item.desenhar(tela, self.camera, gfx, fonte)
                        except TypeError:
                            try:
                                item.desenhar(tela, self.camera, gfx)
                            except TypeError:
                                item.desenhar(tela, self.camera)
                else:
                    item.desenhar(tela, ox, oy, self.tempo_cenario)

            # Elementos Interativos do Prompt 2: Monólitos, Portais Místicos e Totens
            for monolito in self.monolitos:
                monolito.desenhar(tela, self.camera, fonte, self.rpg)
            for portal in self.portais_misticos:
                portal.desenhar(tela, self.camera, fonte, self.rpg)
            for totem in self.totens:
                totem.desenhar(tela, self.camera, fonte, self.jogador.rect)
            for vg in self.ventos_guia:
                vg.desenhar(tela, self.camera)

            for o in self.ondas:
                o.desenhar(tela, self.camera)
            for proj in self.projeteis:
                proj.desenhar(tela, self.camera)
            for pc in self.projeteis_chefes:
                pc.desenhar(tela, self.camera)
            for p_ini in getattr(self, "projeteis_inimigos", []):
                p_ini.desenhar(tela, self.camera, gfx)
            for p in self.particulas:
                p.desenhar(tela, self.camera)
            for tf in self.textos_flutuantes:
                tf.desenhar(tela, self.camera, fonte)

            self.ambiente.desenhar_ar(tela, ox, oy, self.clima)
            self._desenhar_clima(tela)
            if getattr(self.nivel, "tema", None):
                desenhar_atmosfera(tela, self.nivel.tema, ox, oy, self.tempo_cenario)
            alvo_bussola = self.alvo_bussola() if self.estado != "derrota" and not self.dialogo else None
            info_bussola = None
            if alvo_bussola:
                self._desenhar_seta_bussola(tela, alvo_bussola)
                vetor = pygame.Vector2(alvo_bussola["pos"]) - pygame.Vector2(self.jogador.rect.center)
                angulo = math.atan2(vetor.y, vetor.x) if vetor.length_squared() > 0 else -math.pi / 2
                anterior = getattr(self, "angulo_bussola", angulo)
                diferenca = (angulo - anterior + math.pi) % math.tau - math.pi
                self.angulo_bussola = anterior + diferenca * 0.18
                info_bussola = {
                    "angulo": self.angulo_bussola,
                    "rotulo": alvo_bussola["rotulo"],
                    "objetivo": alvo_bussola.get("objetivo"),
                    "destaque": getattr(self, "destaque_bussola", 0.0),
                    "tempo_visivel": getattr(self, "tempo_objetivo_visivel", 0.0),
                }
            dados_atuais = self.mapas.get(self.nivel.caminho.resolve())
            chefe_hud = self.chefes[0] if self.chefes else None
            rush_hud = ({"onda": self.boss_rush_onda, "total": 5} if self.boss_rush_ativo and self.boss_rush_onda <= 5 else None)
            desenhar_hud(
                tela,
                gfx,
                fonte,
                self.jogador.vida,
                self.jogador.vida_maxima,
                self._inimigos_restantes(),
                rpg=self.rpg,
                dados_mapa=dados_atuais,
                jogador_rect=self.jogador.rect,
                tempo=self.tempo_cenario,
                chefe_ativo=chefe_hud,
                boss_rush_info=rush_hud,
                aviso_mapa=self.aviso_mapa,
                tempo_aviso_mapa=self.tempo_aviso_mapa,
                bussola=info_bussola,
            )

            # Dica visual na tela ao se aproximar de um Ponto de Salvamento
            for psx, psy in getattr(self.nivel, "pontos_salvamento", []):
                if pygame.Vector2(self.jogador.rect.center).distance_to((psx, psy)) < 26:
                    dica = "[Espaço / Enter] Salvar Jogo & Descansar"
                    larg_d = fonte.size(dica)[0] + 12
                    faixa_s = pygame.Surface((larg_d, 13), pygame.SRCALPHA)
                    faixa_s.fill((16, 22, 42, 210))
                    pygame.draw.rect(faixa_s, (110, 225, 255), faixa_s.get_rect(), 1)
                    tela.blit(faixa_s, (LARGURA // 2 - larg_d // 2, ALTURA - 17))
                    desenhar_texto(tela, fonte, dica, (LARGURA // 2, ALTURA - 11), (255, 235, 120), centro=True)
                    break

            # Dica visual na tela ao se aproximar de um Monólito Astral
            for m in self.monolitos:
                if m.id_waypoint in self.rpg.waypoint_descobertos and m.pos.distance_to(self.jogador.rect.center) < 28:
                    dica_m = "[Espaço / Enter] Viagem Rápida Astral"
                    larg_dm = fonte.size(dica_m)[0] + 12
                    faixa_m = pygame.Surface((larg_dm, 13), pygame.SRCALPHA)
                    faixa_m.fill((16, 24, 48, 215))
                    pygame.draw.rect(faixa_m, (120, 225, 255), faixa_m.get_rect(), 1)
                    tela.blit(faixa_m, (LARGURA // 2 - larg_dm // 2, ALTURA - 30))
                    desenhar_texto(tela, fonte, dica_m, (LARGURA // 2, ALTURA - 24), (180, 240, 255), centro=True)
                    break

        if self.clarao > 0:
            camada = pygame.Surface(tela.get_size(), pygame.SRCALPHA)
            camada.fill((*self.cor_clarao, int(min(1.0, self.clarao) * 200)))
            tela.blit(camada, (0, 0))

        # Feixe de luz celestial vertical do teleporte astral (Pilar 3)
        if self.feixe_teleporte is not None:
            ox, oy = self.camera.offset
            tx, ty = self.feixe_teleporte["pos"]
            sx = tx - ox
            prog = self.feixe_teleporte["tempo"] / 0.8
            larg_feixe = max(6, round(20 * math.sin(prog * math.pi)))
            surf_feixe = pygame.Surface((larg_feixe * 2 + 8, ALTURA), pygame.SRCALPHA)
            pygame.draw.rect(surf_feixe, (120, 220, 255, 95), (4, 0, larg_feixe * 2, ALTURA))
            pygame.draw.rect(surf_feixe, (220, 245, 255, 185), (4 + larg_feixe // 2, 0, larg_feixe, ALTURA))
            pygame.draw.rect(surf_feixe, (255, 255, 255, 255), (4 + larg_feixe - 1, 0, 2, ALTURA))
            tela.blit(surf_feixe, (sx - (larg_feixe + 4), 0))

        # Vinheta de Apresentação Cinematográfica de Chefes (Pilar 4)
        if self.apresentacao_chefe is not None:
            chefe = self.apresentacao_chefe["chefe"]
            tempo_restante = self.apresentacao_chefe["tempo"]
            duracao = self.apresentacao_chefe["duracao"]
            alfa_fator = min(1.0, (duracao - tempo_restante) * 4.0) if tempo_restante > 0.4 else min(1.0, tempo_restante * 2.5)
            alfa_t = int(255 * alfa_fator)

            h_tarja = 24
            surf_tarja = pygame.Surface((LARGURA, h_tarja), pygame.SRCALPHA)
            surf_tarja.fill((0, 0, 0, int(225 * alfa_fator)))
            tela.blit(surf_tarja, (0, 0))
            tela.blit(surf_tarja, (0, ALTURA - h_tarja))

            larg_card = 264
            alt_card = 44
            surf_card = pygame.Surface((larg_card, alt_card), pygame.SRCALPHA)
            surf_card.fill((16, 12, 24, int(215 * alfa_fator)))
            pygame.draw.rect(surf_card, (235, 195, 75, alfa_t), surf_card.get_rect(), 1)
            pygame.draw.rect(surf_card, (140, 110, 40, alfa_t), surf_card.get_rect().inflate(-2, -2), 1)

            tag = "- GUARDIÃO ANCESTRAL -" if not isinstance(chefe, EntidadeMalignaChefe) else "- SOBERANO DO APOCALIPSE -"
            desenhar_texto(surf_card, fonte, tag, (larg_card // 2, 4), (255, 180, 80), centro=True)
            desenhar_texto(surf_card, fonte, chefe.nome.upper(), (larg_card // 2, 17), (255, 235, 130), centro=True)
            sub_titulo = getattr(chefe, "subtitulo", getattr(chefe, "titulo", "Guardião Ancestral"))
            sub = f"{sub_titulo} | Nível {chefe.nivel_minimo}"
            desenhar_texto(surf_card, fonte, sub, (larg_card // 2, 30), (180, 230, 255), centro=True)

            tela.blit(surf_card, (LARGURA // 2 - larg_card // 2, ALTURA // 2 - alt_card // 2 - 10))

        if self.dialogo:
            self.dialogo.desenhar(tela)
        elif self.estado == "derrota" and self.modo_chefe:
            desenhar_mensagem(tela, fonte, "DERROTA", "Enter: tentar de novo   Esc: escolher chefe")
        elif self.estado == "derrota":
            desenhar_mensagem(tela, fonte, "GAME OVER", "Enter / A para tentar de novo")

        if self.fade_alfa > 0:
            alfa_fade = int(min(1.0, self.fade_alfa) * 255)
            camada_fade = pygame.Surface(tela.get_size(), pygame.SRCALPHA)
            camada_fade.fill((6, 8, 16, alfa_fade))
            tela.blit(camada_fade, (0, 0))

        # Notificações de Conquistas em primeiro plano
        self.conquistas.desenhar(tela, fonte, no_topo=self.dialogo is not None)

    # ------------------------------------------------------------ bússola
    def _grafo_portas(self):
        """Liga cada mapa aos mapas vizinhos pelas portas: {mapa: [(centro_da_porta, mapa_destino)]}."""
        if getattr(self, "_cache_grafo_portas", None) is None:
            grafo = {}
            for dados in self.mapas.values():
                nivel = dados["nivel"]
                grafo[nivel.caminho.name] = [(rect.center, Path(dest).name) for rect, dest in nivel.portas]
            self._cache_grafo_portas = grafo
        return self._cache_grafo_portas

    def _mapa_objetivo(self):
        proximo = self.rpg.proximo_chefe()
        if proximo:
            return proximo[3], proximo[1]
        if "vitoria_final" not in self.flags:
            return "castelo_salao_trono.txt", "A Entidade Maligna"
        return None, None

    def _nivel_regiao(self, mapa):
        """Nível recomendado de uma região (o do Guardião que mora ali); 0 se for segura."""
        if getattr(self, "_niveis_regiao", None) is None:
            niveis = {}
            for _, _, nv, covil, origem, _, _ in LISTA_CHEFES_PROGRESSAO:
                niveis[covil] = nv
                niveis[origem] = min(niveis.get(origem, nv), nv)
            self._niveis_regiao = niveis
        return self._niveis_regiao.get(mapa, 0)

    def _rota_ate(self, atual, alvo_mapa):
        """Primeiro passo (porta, mapa seguinte) da rota mais segura até `alvo_mapa`.

        Cada mapa custa 1; regiões acima do nível do herói custam bem mais e covis
        de outros Guardiões nunca entram no caminho (são becos sem saída).
        """
        import heapq

        grafo = self._grafo_portas()
        nivel_heroi = self.rpg.nivel
        melhor = {atual: 0}
        anterior = {atual: None}
        fila = [(0, atual)]
        while fila:
            custo, mapa = heapq.heappop(fila)
            if mapa == alvo_mapa:
                break
            if custo > melhor.get(mapa, float("inf")):
                continue
            for centro, destino in grafo.get(mapa, []):
                if destino in MAPA_PARA_CHEFE_ID and destino != alvo_mapa:
                    continue
                perigo = self._nivel_regiao(destino) - (nivel_heroi + 1)
                passo = 1 + (10 + perigo if perigo > 0 else 0)
                novo = custo + passo
                if novo < melhor.get(destino, float("inf")):
                    melhor[destino] = novo
                    anterior[destino] = (mapa, centro)
                    heapq.heappush(fila, (novo, destino))
        if alvo_mapa not in anterior:
            return None
        no = alvo_mapa
        while anterior[no] and anterior[no][0] != atual:
            no = anterior[no][0]
        return (anterior[no][1], no) if anterior[no] else None

    def alvo_bussola(self):
        """Ponto (no mundo) para onde a bússola aponta, o objetivo e o próximo mapa, ou None."""
        if not self.app.config.get("bussola", True) or getattr(self, "modo_chefe", None):
            return None
        alvo_mapa, nome_alvo = self._mapa_objetivo()

        # Avisa quando o objetivo muda (ex.: logo depois de derrotar um Guardião)
        anterior = getattr(self, "_objetivo_anterior", None)
        if alvo_mapa != anterior:
            if anterior is not None and nome_alvo:
                self.aviso_mapa = f"Novo objetivo: {nome_alvo}"
                self.tempo_aviso_mapa = 3.5
                self.destaque_bussola = 3.5
                self.tempo_objetivo_visivel = 5.0
            self._objetivo_anterior = alvo_mapa
        if not alvo_mapa:
            return None

        atual = self.nivel.caminho.name
        if atual == alvo_mapa:
            if self.chefes:
                return {"pos": self.chefes[0].rect.center, "objetivo": nome_alvo, "rotulo": "Aqui!"}
            return None
        chave = (atual, alvo_mapa, self.rpg.nivel)
        cache = getattr(self, "_cache_rotas", {})
        if chave not in cache:
            cache[chave] = self._rota_ate(atual, alvo_mapa)
            self._cache_rotas = cache
        passo = cache[chave]
        if passo is None:
            return None
        centro_porta, proximo_mapa = passo
        dados = self.mapas.get((PASTA_BASE / "maps" / proximo_mapa).resolve())
        nome_proximo = dados["nivel"].nome if dados else proximo_mapa
        return {"pos": centro_porta, "objetivo": nome_alvo, "rotulo": nome_proximo}

    def _desenhar_seta_bussola(self, tela, alvo):
        """Seta dourada girando em volta do herói, apontando o caminho."""
        ox, oy = self.camera.offset
        origem = pygame.Vector2(self.jogador.rect.centerx, self.jogador.rect.centery - 4)
        vetor = pygame.Vector2(alvo["pos"]) - origem
        if vetor.length() < 28:
            return
        direcao = vetor.normalize()
        raio = 19 + math.sin(self.tempo_cenario * 5) * 1.5
        ponta = origem + direcao * (raio + 5)
        base = origem + direcao * raio
        lado = direcao.rotate(90) * 3
        pts = [(ponta.x - ox, ponta.y - oy), (base.x + lado.x - ox, base.y + lado.y - oy), (base.x - lado.x - ox, base.y - lado.y - oy)]
        pygame.draw.polygon(tela, (40, 26, 8), [(x + 1, y + 1) for x, y in pts])
        pygame.draw.polygon(tela, (255, 214, 90), pts)

    def _luzes_liquido(self, ox, oy):
        """Centros (na tela) dos tiles de líquido visíveis, um a cada dois, para pontos de luz."""
        nivel = self.nivel
        pontos = []
        for cy in range(max(0, oy // TILE), min(nivel.linhas, (oy + ALTURA) // TILE + 1)):
            for cx in range(max(0, ox // TILE), min(nivel.colunas, (ox + LARGURA) // TILE + 1)):
                if nivel.grade[cy][cx] == "~" and (cx + cy) % 2 == 0:
                    pontos.append((cx * TILE + TILE // 2 - ox, cy * TILE + TILE // 2 - oy))
        return pontos

    def _desenhar_clima(self, tela):
        clima_atual = self.clima
        alfa_base = 0
        cor_escura = (12, 16, 42)
        tema = getattr(self.nivel, "tema", None)

        if tema:
            cor_escura, alfa_base = tema["luz"]
        elif clima_atual == "trevas":
            cor_escura = (28, 8, 34)
            alfa_base = 125
        elif clima_atual == "chuva":
            cor_escura = (18, 26, 52)
            alfa_base = 82
        elif clima_atual == "noite":
            cor_escura = (12, 16, 42)
            alfa_base = 110
        elif not self.nivel.eh_interior:
            # Ciclo Suave e Gradual Dia & Noite (Pilar 4)
            t = self.relogio_dia_noite
            if 0.0 <= t < 0.2:  # Madrugada
                prog = t / 0.2
                alfa_base = int(105 * (1.0 - prog))
                cor_escura = (15, 20, 48)
            elif 0.2 <= t < 0.3:  # Amanhecer
                prog = (t - 0.2) / 0.1
                alfa_base = int(32 * math.sin(prog * math.pi))
                cor_escura = (220, 160, 80)
            elif 0.3 <= t < 0.7:  # Dia pleno
                alfa_base = 0
            elif 0.7 <= t < 0.82:  # Entardecer
                prog = (t - 0.7) / 0.12
                alfa_base = int(30 + 45 * prog)
                cor_escura = (210, 105, 50)
            else:  # Noite
                prog = (t - 0.82) / 0.18
                alfa_base = int(75 + 35 * math.sin(prog * math.pi * 0.5))
                cor_escura = (12, 16, 42)

        if alfa_base > 0:
            camada = pygame.Surface(tela.get_size(), pygame.SRCALPHA)
            camada.fill((*cor_escura, alfa_base))

            # Halo de lanterna ao redor do herói e fontes de luz perfurando a escuridão
            ox, oy = self.camera.offset
            hx, hy = self.jogador.rect.centerx - ox, self.jogador.rect.centery - 6 - oy
            pygame.draw.circle(camada, (*cor_escura, alfa_base // 2), (hx, hy), 42)
            pygame.draw.circle(camada, (*cor_escura, alfa_base // 5), (hx, hy), 24)
            for mx, my in getattr(self.nivel, "mesas", []):
                pygame.draw.circle(camada, (*cor_escura, alfa_base // 3), (mx - ox, my - oy - 4), 26)
            for tx, ty, _ in getattr(self.nivel, "tochas", []):
                pygame.draw.circle(camada, (*cor_escura, alfa_base // 3), (tx - ox, ty - oy - 2), 22)
            # Covis temáticos: o líquido brilhante e a aura do Guardião iluminam a arena
            if tema and tema["brilha"]:
                for lx, ly in self._luzes_liquido(ox, oy):
                    pygame.draw.circle(camada, (*cor_escura, alfa_base // 2), (lx, ly), 14)
            for chefe in self.chefes:
                ccx, ccy = chefe.rect.centerx - ox, chefe.rect.centery - oy
                pygame.draw.circle(camada, (*cor_escura, alfa_base // 2), (ccx, ccy), 40)

            tela.blit(camada, (0, 0))

        if clima_atual == "chuva":
            for gx, gy in self.gotas_chuva:
                x, y = round(gx), round(gy)
                pygame.draw.line(tela, (150, 195, 245), (x, y), (x - 2, y + 6))
