"""Tela do Mapa do Mundo (Atlas de Regiões + Mapa Detalhado da Área + Viagem Rápida)."""
import math

import pygame

from cenas.base import Cena
from settings import ALTURA, LARGURA, PASTA_BASE, TILE
from ui import AMARELO, BRANCO, CINZA, ajustar_texto, desenhar_painel, desenhar_rodape, desenhar_texto, escurecer

# Coordenadas geográficas de cada região no Atlas do Mundo (x, y no painel de mapa)
NOS_ATLAS = [
    {"arq": "templo_sol.txt",      "pos": (24, 34),  "conexoes": ["oasis.txt"]},
    {"arq": "oasis.txt",           "pos": (24, 68),  "conexoes": ["templo_sol.txt", "deserto.txt"]},
    {"arq": "deserto.txt",         "pos": (46, 94),  "conexoes": ["oasis.txt", "lago.txt"]},
    {"arq": "caverna_cristal.txt", "pos": (82, 42),  "conexoes": ["pico_congelado.txt", "lago.txt"]},
    {"arq": "lago.txt",            "pos": (82, 86),  "conexoes": ["mundo.txt", "vila.txt", "deserto.txt", "caverna_cristal.txt", "bosque_outono.txt"]},
    {"arq": "bosque_outono.txt",   "pos": (82, 128), "conexoes": ["lago.txt", "pantano.txt"]},
    {"arq": "pico_congelado.txt",  "pos": (128, 22), "conexoes": ["montanha.txt", "caverna_cristal.txt"]},
    {"arq": "montanha.txt",        "pos": (128, 42), "conexoes": ["vila.txt", "pico_congelado.txt"]},
    {"arq": "vila.txt",            "pos": (128, 66), "conexoes": ["mundo.txt", "lago.txt", "montanha.txt", "santuario.txt"]},
    {"arq": "mundo.txt",           "pos": (128, 96), "conexoes": ["casa.txt", "vila.txt", "lago.txt", "ruinas.txt", "pantano.txt"]},
    {"arq": "casa.txt",            "pos": (106, 112),"conexoes": ["mundo.txt"]},
    {"arq": "pantano.txt",         "pos": (128, 132),"conexoes": ["mundo.txt", "bosque_outono.txt"]},
    {"arq": "castelo.txt",                 "pos": (166, 36), "conexoes": ["santuario.txt", "castelo_patio.txt"]},
    {"arq": "castelo_patio.txt",           "pos": (166, 22), "conexoes": ["castelo.txt", "castelo_masmorra.txt", "castelo_biblioteca.txt", "castelo_ante_camara.txt"]},
    {"arq": "castelo_masmorra.txt",        "pos": (148, 16), "conexoes": ["castelo_patio.txt"]},
    {"arq": "castelo_biblioteca.txt",      "pos": (184, 16), "conexoes": ["castelo_patio.txt"]},
    {"arq": "castelo_ante_camara.txt",     "pos": (166, 10), "conexoes": ["castelo_patio.txt", "castelo_sala_salvamento.txt"]},
    {"arq": "castelo_sala_salvamento.txt", "pos": (150, 4),  "conexoes": ["castelo_ante_camara.txt", "castelo_salao_trono.txt"]},
    {"arq": "castelo_salao_trono.txt",     "pos": (174, 4),  "conexoes": ["castelo_sala_salvamento.txt"]},
    {"arq": "santuario.txt",               "pos": (176, 58), "conexoes": ["vila.txt", "ruinas.txt", "castelo.txt"]},
    {"arq": "ruinas.txt",                  "pos": (176, 96), "conexoes": ["mundo.txt", "santuario.txt", "cripta.txt"]},
    {"arq": "cripta.txt",                  "pos": (196, 124),"conexoes": ["ruinas.txt"]},
]


MAPA_REGIAO_PARA_CHEFE = {
    "mundo.txt": ("rei_slime", "Rei Slime", 1),
    "ruinas.txt": ("golem_pedra", "Golem de Pedra", 2),
    "deserto.txt": ("serpente_dunas", "Serpente das Dunas", 3),
    "templo_sol.txt": ("colosso_solar", "Colosso Solar", 4),
    "pantano.txt": ("bruxa_brumas", "Bruxa das Brumas", 5),
    "cripta.txt": ("ceifador_espectral", "Ceifador Espectral", 6),
    "lago.txt": ("leviata_aquatico", "Leviatã Aquático", 7),
    "caverna_cristal.txt": ("guardiao_diamante", "Guardião dos Cristais", 8),
    "montanha.txt": ("troll_rochas", "Troll das Cavernas", 9),
    "pico_congelado.txt": ("yeti_glacial", "Yeti Glacial", 10),
    "santuario.txt": ("valquiria_caida", "Valquíria Sombria", 11),
    "castelo_patio.txt": ("cavaleiro_negro", "Cavaleiro Negro", 12),
    "castelo_masmorra.txt": ("quimera_abissal", "Quimera Abissal", 13),
    "castelo_biblioteca.txt": ("arquimago", "Arquimago", 14),
    "castelo_ante_camara.txt": ("paladino_juizo", "Paladino do Juízo", 15),
    "castelo_sala_salvamento.txt": ("entidade_maligna", "Entidade Maligna", 15),
}


def desenhar_miniatura_nivel(tela, dados_mapa, rect_destino, jogador_rect=None, mostrar_entidades=True, t=0.0):
    """Desenha o mapa em escala dentro de `rect_destino` (usado no Minimapa do HUD e na Tela de Mapa)."""
    nivel = dados_mapa["nivel"]
    pygame.draw.rect(tela, (14, 18, 32), rect_destino)

    surf_mini = pygame.Surface((nivel.colunas, nivel.linhas))
    cores_tile = {
        ".": (64, 138, 58),
        "*": (98, 178, 76),
        ",": (198, 166, 114),
        "~": (46, 112, 196),
        "#": (118, 124, 142),
        "T": (34, 84, 44),
        "B": (48, 118, 52),
        "_": (156, 104, 62),
        "W": (96, 62, 38),
        "R": (176, 62, 50),
        "C": (220, 80, 80),
        "M": (148, 96, 54),
        "D": (245, 205, 80),
    }
    for cy, linha in enumerate(nivel.grade):
        for cx, c in enumerate(linha):
            surf_mini.set_at((cx, cy), cores_tile.get(c, (64, 138, 58)))

    for rect_porta, _ in nivel.portas:
        px, py = rect_porta.x // TILE, rect_porta.y // TILE
        if 0 <= px < nivel.colunas and 0 <= py < nivel.linhas:
            surf_mini.set_at((px, py), (255, 225, 90))

    if mostrar_entidades:
        for npc in dados_mapa["npcs"]:
            nx, ny = npc.rect.centerx // TILE, npc.rect.centery // TILE
            if 0 <= nx < nivel.colunas and 0 <= ny < nivel.linhas:
                surf_mini.set_at((nx, ny), (90, 215, 255))
        for slime in dados_mapa["inimigos"]:
            sx, sy = slime.rect.centerx // TILE, slime.rect.centery // TILE
            if 0 <= sx < nivel.colunas and 0 <= sy < nivel.linhas:
                surf_mini.set_at((sx, sy), (255, 75, 85))

    escala = min(
        (rect_destino.width - 4) / max(1, nivel.colunas),
        (rect_destino.height - 4) / max(1, nivel.linhas),
    )
    larg_m = max(8, round(nivel.colunas * escala))
    alt_m = max(8, round(nivel.linhas * escala))
    ampliado = pygame.transform.scale(surf_mini, (larg_m, alt_m))
    r_amp = ampliado.get_rect(center=rect_destino.center)
    tela.blit(ampliado, r_amp)

    if jogador_rect is not None and math.sin(t * 10.0) > -0.4:
        jx = r_amp.left + int((jogador_rect.centerx / max(1, nivel.largura_px)) * larg_m)
        jy = r_amp.top + int((jogador_rect.centery / max(1, nivel.altura_px)) * alt_m)
        pygame.draw.circle(tela, (255, 255, 255), (jx, jy), 2)
        pygame.draw.circle(tela, (80, 255, 110), (jx, jy), 1)

    pygame.draw.rect(tela, (215, 180, 75), rect_destino, 1)


class MapaMundo(Cena):
    transparente = True

    def __init__(self, app, jogo):
        super().__init__(app)
        self.jogo = jogo
        self.t = 0.0
        self.modo_detalhe = False
        self.nos = [dict(n) for n in NOS_ATLAS if (PASTA_BASE / "maps" / n["arq"]).exists()]
        self._encaixar_nos(pygame.Rect(14, 27, 192, 124).inflate(-16, -14))
        arq_atual = jogo.nivel.caminho.name
        self.indice = 0
        for i, n in enumerate(self.nos):
            if n["arq"] == arq_atual:
                self.indice = i
                break

    def _encaixar_nos(self, area):
        """Ajusta as posições do grafo para caberem inteiras dentro do quadro do Atlas."""
        if not self.nos:
            return
        xs = [n["pos"][0] for n in self.nos]
        ys = [n["pos"][1] for n in self.nos]
        larg = max(1, max(xs) - min(xs))
        alt = max(1, max(ys) - min(ys))
        for n in self.nos:
            x, y = n["pos"]
            n["pos"] = (
                area.x + round((x - min(xs)) / larg * area.width),
                area.y + round((y - min(ys)) / alt * area.height),
            )

    def _mover_selecao(self, dx, dy):
        atual = self.nos[self.indice]["pos"]
        melhor_i = self.indice
        melhor_score = 999999.0
        for i, n in enumerate(self.nos):
            if i == self.indice:
                continue
            vx = n["pos"][0] - atual[0]
            vy = n["pos"][1] - atual[1]
            if vx * dx + vy * dy <= 0:
                continue
            dist = math.hypot(vx, vy)
            alinhamento = abs( vx * dy - vy * dx )
            score = dist + alinhamento * 0.8
            if score < melhor_score:
                melhor_score = score
                melhor_i = i
        self.indice = melhor_i

    def atualizar(self, dt):
        entrada = self.app.entrada
        self.t += dt

        if entrada.apertou("voltar") or entrada.apertou("mapa") or entrada.apertou("pausa"):
            self.app.desempilhar()
            return

        if entrada.apertou("trocar_magia"):
            self.modo_detalhe = not self.modo_detalhe
            return

        if entrada.apertou("esquerda"):
            self._mover_selecao(-1, 0)
        elif entrada.apertou("direita"):
            self._mover_selecao(1, 0)
        elif entrada.apertou("cima"):
            self._mover_selecao(0, -1)
        elif entrada.apertou("baixo"):
            self._mover_selecao(0, 1)
        elif entrada.apertou("confirmar"):
            escolhido = self.nos[self.indice]["arq"]
            from cenas.jogo import MAPA_PARA_CHEFE_ID, REQUISITOS_MAPA_CHEFE
            if escolhido in MAPA_PARA_CHEFE_ID:
                chefe_id = MAPA_PARA_CHEFE_ID[escolhido]
                if chefe_id in self.jogo.rpg.chefes_derrotados:
                    nome_ch = REQUISITOS_MAPA_CHEFE.get(escolhido, (0, "Guardião"))[1]
                    self.jogo.aviso_mapa = f"🔒 Área Selada: {nome_ch} já foi derrotado para sempre!"
                    self.jogo.tempo_aviso_mapa = 3.5
                    audio = getattr(self.app, "audio", None)
                    if audio:
                        audio.sfx("bloqueio")
                    return

            if escolhido in REQUISITOS_MAPA_CHEFE:
                req_nv, nome_ch = REQUISITOS_MAPA_CHEFE[escolhido]
                if self.jogo.rpg.nivel < req_nv:
                    self.jogo.aviso_mapa = f"🔒 Portão Selado: Requer Nível {req_nv} para {nome_ch}!"
                    self.jogo.tempo_aviso_mapa = 3.5
                    audio = getattr(self.app, "audio", None)
                    if audio:
                        audio.sfx("bloqueio")
                    return
            if escolhido == "castelo_salao_trono.txt":
                if len(self.jogo.rpg.chefes_derrotados) < 15:
                    faltam = 15 - len(self.jogo.rpg.chefes_derrotados)
                    self.jogo.aviso_mapa = f"🔒 O Selo das Sombras exige os 15 Guardiões! ({len(self.jogo.rpg.chefes_derrotados)}/15)"
                    self.jogo.tempo_aviso_mapa = 3.5
                    audio = getattr(self.app, "audio", None)
                    if audio:
                        audio.sfx("bloqueio")
                    return
            caminho = PASTA_BASE / "maps" / escolhido
            if caminho.exists():
                self.jogo.iniciar_transicao_mapa(caminho, usar_porta=False)
                self.app.desempilhar()

    def desenhar(self, tela):
        escurecer(tela, 205)
        fonte = self.app.fontes.normal

        painel = pygame.Rect(8, 6, LARGURA - 16, ALTURA - 12)
        desenhar_painel(tela, painel)

        no_sel = self.nos[self.indice]
        caminho_sel = (PASTA_BASE / "maps" / no_sel["arq"]).resolve()
        dados_sel = self.jogo._carregar_mapa(caminho_sel)
        nivel_sel = dados_sel["nivel"]
        eh_atual = (self.jogo.nivel.caminho.resolve() == caminho_sel)

        titulo_atlas = "ATLAS DO MUNDO"
        desenhar_texto(tela, fonte, titulo_atlas, (14, 11), AMARELO)
        proximo = self.jogo.rpg.proximo_chefe()
        if proximo:
            id_pr, nome_pr, nv_pr, _, arq_orig, _, _ = proximo
            espaco_obj = LARGURA - 28 - fonte.size(titulo_atlas)[0] - 12
            txt_obj = ajustar_texto(fonte, f"Objetivo: {nome_pr} (Nv.{nv_pr})", espaco_obj)
            larg_obj = fonte.size(txt_obj)[0]
            desenhar_texto(tela, fonte, txt_obj, (LARGURA - 14 - larg_obj, 11), (255, 220, 90))
        pygame.draw.line(tela, (65, 75, 115), (12, 23), (LARGURA - 12, 23))

        if self.modo_detalhe:
            rect_grande = pygame.Rect(16, 28, LARGURA - 32, 122)
            desenhar_miniatura_nivel(
                tela,
                dados_sel,
                rect_grande,
                jogador_rect=self.jogo.jogador.rect if eh_atual else None,
                t=self.t,
            )
        else:
            # Painel esquerdo: Grafo do Atlas do Mundo com conexões entre as regiões
            rect_atlas = pygame.Rect(14, 27, 192, 124)
            pygame.draw.rect(tela, (24, 30, 52), rect_atlas)
            pygame.draw.rect(tela, (70, 82, 125), rect_atlas, 1)

            pos_por_arq = {n["arq"]: n["pos"] for n in self.nos}
            for n in self.nos:
                x1, y1 = n["pos"]
                for dest in n["conexoes"]:
                    if dest in pos_por_arq:
                        x2, y2 = pos_por_arq[dest]
                        pygame.draw.line(tela, (65, 76, 110), (x1, y1), (x2, y2), 2)

            # Rota brilhante para o objetivo recomendado
            proximo = self.jogo.rpg.proximo_chefe()
            arq_heroi = self.jogo.nivel.caminho.name
            if proximo and proximo[4] in pos_por_arq and arq_heroi in pos_por_arq:
                p_ini = pos_por_arq[arq_heroi]
                p_fim = pos_por_arq[proximo[4]]
                if p_ini != p_fim:
                    fase_rota = (self.t * 3.0) % 1.0
                    rx = int(p_ini[0] + (p_fim[0] - p_ini[0]) * fase_rota)
                    ry = int(p_ini[1] + (p_fim[1] - p_ini[1]) * fase_rota)
                    pygame.draw.line(tela, (255, 215, 80), p_ini, p_fim, 1)
                    pygame.draw.circle(tela, (255, 240, 150), (rx, ry), 2)

            for i, n in enumerate(self.nos):
                nx, ny = n["pos"]
                visitado = n["arq"] in self.jogo.mapas_visitados
                cor_no = (90, 245, 130) if n["arq"] == arq_heroi else ((110, 195, 255) if visitado else (110, 115, 140))
                if i == self.indice:
                    raio_pulso = 7 + round(math.sin(self.t * 8.0) * 1.5)
                    pygame.draw.circle(tela, AMARELO, (nx, ny), raio_pulso, 1)
                pygame.draw.circle(tela, (20, 24, 40), (nx, ny), 5)
                pygame.draw.circle(tela, cor_no, (nx, ny), 4)

                # Badges de Chefes dos Covis (🔴 Insuficiente, 🟡 Recomendado, ⚪ Derrotado)
                if n["arq"] in MAPA_REGIAO_PARA_CHEFE:
                    ch_id, _, ch_nv = MAPA_REGIAO_PARA_CHEFE[n["arq"]]
                    esta_selado = ch_id in self.jogo.rpg.chefes_derrotados
                    bx, by = nx + 4, ny - 4
                    if esta_selado:
                        # ⚪ Cinza Espectral
                        pygame.draw.circle(tela, (20, 24, 35), (bx, by), 3)
                        pygame.draw.circle(tela, (180, 200, 225), (bx, by), 2)
                    elif self.jogo.rpg.nivel < ch_nv:
                        # 🔴 Vermelho (bloqueado/nível baixo)
                        pygame.draw.circle(tela, (20, 24, 35), (bx, by), 3)
                        pygame.draw.circle(tela, (255, 55, 65), (bx, by), 2)
                    elif proximo and proximo[0] == ch_id:
                        # 🟡 Dourado pulsante (desafio ideal)
                        r_ch = 3 + round(math.sin(self.t * 10.0) * 1.0)
                        pygame.draw.circle(tela, (255, 230, 90), (bx, by), r_ch)
                        pygame.draw.circle(tela, (255, 255, 240), (bx, by), max(1, r_ch - 1))
                    else:
                        # Desafio acessível
                        pygame.draw.circle(tela, (20, 24, 35), (bx, by), 3)
                        pygame.draw.circle(tela, (245, 175, 60), (bx, by), 2)

            # Painel direito: Miniatura e detalhes da região selecionada
            rect_prev = pygame.Rect(212, 27, 94, 60)
            desenhar_miniatura_nivel(
                tela,
                dados_sel,
                rect_prev,
                jogador_rect=self.jogo.jogador.rect if eh_atual else None,
                t=self.t,
            )

            desenhar_texto(tela, fonte, nivel_sel.nome, (259, 93), AMARELO, centro=True)

            # Informações do Guardião na região
            if no_sel["arq"] in MAPA_REGIAO_PARA_CHEFE:
                ch_id, ch_nome, ch_nv = MAPA_REGIAO_PARA_CHEFE[no_sel["arq"]]
                if ch_id in self.jogo.rpg.chefes_derrotados:
                    txt_g = "⚪ Guardião: Selado"
                    cor_g = (175, 205, 235)
                elif self.jogo.rpg.nivel < ch_nv:
                    txt_g = f"🔴 Guardião: Requer Nv.{ch_nv}"
                    cor_g = (255, 90, 95)
                elif proximo and proximo[0] == ch_id:
                    txt_g = f"🟡 Alvo Ideal: Nv.{ch_nv}"
                    cor_g = (255, 225, 80)
                else:
                    txt_g = f"Guardião: Nv.{ch_nv}"
                    cor_g = (245, 185, 90)
                desenhar_texto(tela, fonte, txt_g, (259, 107), cor_g, centro=True)
            else:
                npcs_tot = len(dados_sel["npcs"])
                desenhar_texto(tela, fonte, f"Habitantes: {npcs_tot}", (259, 107), CINZA, centro=True)

            # Informações de Monólito da região
            monolitos_mapa = [m for m in getattr(nivel_sel, "monolitos", [])]
            if monolitos_mapa:
                wid = monolitos_mapa[0][1]
                if wid in self.jogo.rpg.waypoint_descobertos:
                    txt_mono = "🌀 Monólito Ativo"
                    cor_mono = (120, 225, 255)
                else:
                    txt_mono = "🔒 Monólito Inativo"
                    cor_mono = (140, 140, 160)
                desenhar_texto(tela, fonte, txt_mono, (259, 120), cor_mono, centro=True)

            from cenas.jogo import MAPA_PARA_CHEFE_ID
            if no_sel["arq"] in MAPA_PARA_CHEFE_ID and MAPA_PARA_CHEFE_ID[no_sel["arq"]] in self.jogo.rpg.chefes_derrotados:
                status_loc = "🔒 [ÁREA SELADA]"
                cor_status = (255, 95, 95)
            elif eh_atual:
                status_loc = "[VOCÊ ESTÁ AQUI]"
                cor_status = (110, 255, 140)
            else:
                status_loc = "[Enter: Viajar]"
                cor_status = AMARELO
            desenhar_texto(
                tela,
                fonte,
                status_loc,
                (259, 137),
                cor_status,
                centro=True,
            )

        rodape = "Setas: Região | Enter: Viagem Rápida | E/R: Ampliar Mapa | M/Esc: Fechar"
        desenhar_rodape(tela, fonte, rodape, CINZA)
