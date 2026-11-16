"""Tela de título e Menu Principal de A Lenda Perdida.

Inspirada nas aberturas clássicas de RPG e aventura dos anos 90:
1. Abertura: o céu clareia, o brasão e o título descem com um clarão.
2. Tela de título: paisagem viva em camadas (aurora, montanhas, castelo,
   lago espelhado, herói com uma fada-guia) e "Pressione Enter".
3. Menu: janela clássica com cursor de mão e um painel de "Aventura"
   com o resumo do jogo salvo e a descrição da opção escolhida.
"""
import json
import math
import random

import pygame

from cenas.base import Cena
from settings import ALTURA, LARGURA, PASTA_BASE
from ui import CINZA, desenhar_icone, desenhar_painel, desenhar_texto, limpar_texto

DESCRICOES = {
    "Continuar": "Retome sua jornada de onde parou.",
    "Novo jogo": "Comece uma nova lenda desde o despertar do herói.",
    "Modo Chefões": "Enfrente qualquer Guardião direto na arena dele.",
    "Configurações": "Som, vídeo, texto, bússola e controles.",
    "Sair": "Até a próxima aventura!",
}
TOTAL_CHEFES = 16

# Mão apontando (cursor clássico de menu de RPG)
MAO = (
    "..##.....",
    ".#ww#....",
    ".#www####",
    ".#wwwwwww#",
    "#wwwwwwww#",
    "#wwwwwww#.",
    ".#wwwww#..",
    "..#####...",
)


def _misturar(a, b, f):
    return tuple(round(a[i] + (b[i] - a[i]) * f) for i in range(3))


def _cordilheira(largura, base, amplitude, semente, rugosidade=0.55):
    """Perfil de montanhas por deslocamento de ponto médio (tileável na horizontal)."""
    rng = random.Random(semente)
    n = 64
    alturas = [0.0] * (n + 1)
    passo, escala = n, amplitude
    alturas[0] = alturas[n] = rng.uniform(-amplitude, amplitude) * 0.3
    while passo > 1:
        meio = passo // 2
        for i in range(meio, n, passo):
            alturas[i] = (alturas[i - meio] + alturas[i + meio]) / 2 + rng.uniform(-escala, escala)
        escala *= rugosidade
        passo = meio
    return [(round(i * largura / n), round(base - alturas[i])) for i in range(n + 1)]


class MenuPrincipal(Cena):
    LARG_PARALAXE = 640
    _abertura_vista = False

    def __init__(self, app, pular_abertura=False):
        super().__init__(app)
        from config import jogo_foi_zerado
        from salvamento import existe_save

        # A abertura cinematográfica só roda na primeira vez; ao voltar do jogo o menu já abre pronto
        pular_abertura = pular_abertura or MenuPrincipal._abertura_vista
        MenuPrincipal._abertura_vista = True
        self.t = 3.0 if pular_abertura else 0.0
        self.estado = "titulo" if pular_abertura else "abertura"
        self.menu_aberto = pular_abertura
        self.transicao = 1.0 if pular_abertura else 0.0  # 0 = título, 1 = menu aberto
        self.modo_chefes_liberado = jogo_foi_zerado(app)
        self.aviso_bloqueado = 0.0
        self.opcoes = ["Novo jogo", "Modo Chefões", "Configurações", "Sair"]
        if existe_save():
            self.opcoes.insert(0, "Continuar")
        self.indice = 0
        self.resumo_save = self._ler_resumo_save()

        if hasattr(app, "audio"):
            app.audio.tocar_bgm("menu")

        rng = random.Random(7)
        self.estrelas = [(rng.randrange(LARGURA), rng.randrange(0, 100), rng.uniform(1.5, 4.5), rng.uniform(0, math.tau)) for _ in range(70)]
        self.vagalumes = [[rng.uniform(0, LARGURA), rng.uniform(120, 175), rng.uniform(0, math.tau)] for _ in range(16)]
        self.passaros = None
        self.tempo_passaros = 4.0
        self.meteoro = None
        self.tempo_meteoro = 6.0

        self._gerar_camadas()
        self.logo = self._gerar_logo()

    # ------------------------------------------------------------ dados do save
    def _ler_resumo_save(self):
        from salvamento import ARQUIVO_SAVE

        try:
            dados = json.loads(ARQUIVO_SAVE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        rpg = dados.get("rpg", {})
        nome_mapa = "Lugar desconhecido"
        try:
            texto_mapa = (PASTA_BASE / dados.get("mapa", "")).read_text(encoding="utf-8")
            for linha in texto_mapa.splitlines():
                if linha.strip().startswith("nome") and "=" in linha:
                    nome_mapa = linha.split("=", 1)[1].strip()
                    break
        except OSError:
            pass
        return {
            "local": nome_mapa,
            "nivel": rpg.get("nivel", 1),
            "vida": dados.get("vida", 6),
            "vida_maxima": dados.get("vida_maxima", 6),
            "chefes": len(rpg.get("chefes_derrotados", [])),
            "reliquias": len(rpg.get("reliquias_coletadas", [])),
            "ouro": rpg.get("ouro", 0),
        }

    # ------------------------------------------------------------ arte pré-renderizada
    def _gerar_camadas(self):
        # Céu do amanhecer: noite profunda -> violeta -> horizonte alaranjado
        self.ceu = pygame.Surface((LARGURA, ALTURA))
        cores = [(0, (8, 10, 34)), (0.38, (40, 26, 84)), (0.58, (118, 58, 108)), (0.68, (236, 128, 96)), (0.72, (255, 196, 120)), (1.0, (255, 214, 150))]
        for y in range(ALTURA):
            f = y / (ALTURA - 1)
            for (f0, c0), (f1, c1) in zip(cores, cores[1:]):
                if f0 <= f <= f1:
                    self.ceu.fill(_misturar(c0, c1, (f - f0) / (f1 - f0)), (0, y, LARGURA, 1))
                    break

        largura = self.LARG_PARALAXE
        self.camadas = []
        definicoes = [
            # base, amplitude, semente, cor, cor do topo/neve, velocidade
            (100, 30, 11, (104, 74, 136), (236, 220, 246), 2.0),
            (110, 22, 23, (70, 48, 104), (150, 110, 160), 5.0),
            (118, 14, 37, (44, 32, 74), (96, 70, 120), 9.0),
        ]
        for base, amp, semente, cor, cor_topo, vel in definicoes:
            surf = pygame.Surface((largura, ALTURA), pygame.SRCALPHA)
            perfil = _cordilheira(largura, base, amp, semente)
            pygame.draw.polygon(surf, cor, perfil + [(largura, ALTURA), (0, ALTURA)])
            # Luz do amanhecer na encosta e neve nos picos mais altos
            for (x0, y0), (x1, y1) in zip(perfil, perfil[1:]):
                pygame.draw.line(surf, cor_topo if y0 < base - amp * 0.55 else _misturar(cor, (255, 170, 120), 0.35), (x0, y0), (x1, y1))
            # Névoa na base de cada cordilheira
            for k in range(10):
                pygame.draw.line(surf, (*_misturar(cor, (255, 190, 160), 0.25), 120 - k * 12), (0, base + 6 + k), (largura, base + 6 + k))
            self.camadas.append((surf, vel))

        # Castelo sobre a colina (direita)
        self.castelo = pygame.Surface((70, 70), pygame.SRCALPHA)
        c = (30, 22, 50)
        pygame.draw.polygon(self.castelo, c, [(0, 70), (10, 52), (60, 50), (70, 70)])
        for x, larg, alt, ponta in ((14, 8, 30, 10), (30, 10, 42, 14), (48, 8, 28, 10), (24, 6, 22, 0), (40, 6, 24, 0)):
            pygame.draw.rect(self.castelo, c, (x, 54 - alt, larg, alt))
            if ponta:
                pygame.draw.polygon(self.castelo, (52, 30, 70), [(x - 1, 54 - alt), (x + larg // 2, 54 - alt - ponta), (x + larg, 54 - alt)])
        for x in range(12, 60, 4):
            pygame.draw.rect(self.castelo, c, (x, 30, 2, 3))

        # Primeiro plano: colina gramada com luz de contorno
        self.colina = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        pts = [(0, 150), (40, 142), (78, 138), (110, 143), (140, 156), (170, 170), (200, ALTURA), (0, ALTURA)]
        pygame.draw.polygon(self.colina, (18, 34, 30), pts)
        pygame.draw.lines(self.colina, (236, 150, 92), False, pts[:6], 1)
        pts2 = [(LARGURA, 158), (290, 160), (262, 168), (240, ALTURA), (LARGURA, ALTURA)]
        pygame.draw.polygon(self.colina, (14, 26, 24), pts2)
        pygame.draw.lines(self.colina, (200, 120, 90), False, pts2[:4], 1)

    def _gerar_logo(self):
        """Título em letras douradas com gradiente, contorno e sombra (3x)."""
        fonte = self.app.fontes.normal
        texto = "A LENDA PERDIDA"
        base = fonte.render(texto, False, (255, 255, 255))
        grande = pygame.transform.scale(base, (base.get_width() * 3, base.get_height() * 3))
        gradiente = pygame.Surface(grande.get_size())
        for y in range(grande.get_height()):
            f = y / grande.get_height()
            cor = _misturar((255, 248, 196), (255, 196, 60), min(1, f * 1.6)) if f < 0.62 else _misturar((255, 196, 60), (196, 92, 30), (f - 0.62) / 0.38)
            gradiente.fill(cor, (0, y, grande.get_width(), 1))
        grande.blit(gradiente, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
        logo = pygame.Surface((grande.get_width() + 4, grande.get_height() + 4), pygame.SRCALPHA)
        sombra = pygame.mask.from_surface(grande).to_surface(setcolor=(40, 10, 30, 200), unsetcolor=(0, 0, 0, 0))
        logo.blit(sombra, (3, 3))
        logo.blit(grande, (0, 0))
        return logo

    # ------------------------------------------------------------ lógica
    def atualizar(self, dt):
        from cenas.configuracoes import Configuracoes
        from cenas.jogo import Jogo

        self.t += dt
        entrada = self.app.entrada
        audio = getattr(self.app, "audio", None)

        # Pássaros e estrelas cadentes de vez em quando
        self.tempo_passaros -= dt
        if self.tempo_passaros <= 0:
            self.tempo_passaros = random.uniform(9, 16)
            self.passaros = {"x": -20.0, "y": random.uniform(40, 80), "vel": random.uniform(22, 32)}
        if self.passaros:
            self.passaros["x"] += self.passaros["vel"] * dt
            if self.passaros["x"] > LARGURA + 30:
                self.passaros = None
        self.tempo_meteoro -= dt
        if self.tempo_meteoro <= 0:
            self.tempo_meteoro = random.uniform(5, 11)
            self.meteoro = {"x": random.uniform(40, 260), "y": random.uniform(6, 40), "vida": 0.6}
        if self.meteoro:
            self.meteoro["x"] += 220 * dt
            self.meteoro["y"] += 90 * dt
            self.meteoro["vida"] -= dt
            if self.meteoro["vida"] <= 0:
                self.meteoro = None
        for v in self.vagalumes:
            v[2] += dt
            v[0] = (v[0] + math.sin(v[2] * 0.7) * 6 * dt + 4 * dt) % LARGURA

        alvo = 1.0 if self.menu_aberto else 0.0
        self.transicao += (alvo - self.transicao) * min(1.0, dt * 7)

        if self.aviso_bloqueado > 0:
            self.aviso_bloqueado = max(0.0, self.aviso_bloqueado - dt)

        if self.estado == "abertura":
            if self.t > 2.6 or entrada.apertou("confirmar") or entrada.apertou("acao"):
                self.estado = "titulo"
                self.t = max(self.t, 2.6)
            return

        if not self.menu_aberto:
            if entrada.apertou("confirmar") or entrada.apertou("acao") or entrada.apertou("pausa"):
                self.menu_aberto = True
                if audio:
                    audio.sfx("menu_confirmar")
            return

        ant = self.indice
        if entrada.apertou("cima"):
            self.indice = (self.indice - 1) % len(self.opcoes)
        if entrada.apertou("baixo"):
            self.indice = (self.indice + 1) % len(self.opcoes)
        if self.indice != ant and audio:
            audio.sfx("menu_mover")
        if entrada.apertou("voltar"):
            self.menu_aberto = False
            if audio:
                audio.sfx("menu_voltar")
            return
        if not entrada.apertou("confirmar"):
            return

        escolha = self.opcoes[self.indice]
        if escolha == "Modo Chefões" and not self.modo_chefes_liberado:
            if audio:
                audio.sfx("bloqueio")
            self.aviso_bloqueado = 3.0
            return

        if audio:
            audio.sfx("menu_confirmar")

        if escolha == "Continuar":
            from cenas.slots_save import CenaSlotsSave
            self.app.trocar(CenaSlotsSave(self.app, modo="carregar"))
        elif escolha == "Novo jogo":
            from cenas.slots_save import CenaSlotsSave
            self.app.trocar(CenaSlotsSave(self.app, modo="novo"))
        elif escolha == "Modo Chefões":
            from cenas.modo_chefes import SelecaoChefes
            self.app.trocar(SelecaoChefes(self.app))
        elif escolha == "Configurações":
            self.app.empilhar(Configuracoes(self.app))
        elif escolha == "Sair":
            self.app.sair()

    # ------------------------------------------------------------ desenho
    def desenhar(self, tela):
        t = self.t
        tela.blit(self.ceu, (0, 0))
        self._desenhar_ceu_vivo(tela, t)

        # Sol nascendo atrás do castelo com múltiplos halos
        sol = (252, 110)
        for r in range(68, 0, -6):
            alfa_halo = round(65 * (1 - r / 68) ** 1.5)
            s_halo = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s_halo, (255, 205, 130, alfa_halo), (r, r), r)
            tela.blit(s_halo, (sol[0] - r, sol[1] - r))
        pygame.draw.circle(tela, (255, 235, 175), sol, 14)
        pygame.draw.circle(tela, (255, 252, 225), sol, 10)

        # Feixes de Luz Crepuscular Volumétrica (God Rays)
        raios = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        feixes_def = [
            (-2.25, 0.14, 30),
            (-2.55, 0.18, 42),
            (-2.88, 0.16, 36),
            (-3.18, 0.14, 28),
        ]
        for i, (ang_c, larg_c, inten) in enumerate(feixes_def):
            pulso = math.sin(t * 1.3 + i * 1.6) * 7
            alfa_raio = round(max(0, inten + pulso))
            p1 = sol
            p2 = (sol[0] + math.cos(ang_c - larg_c / 2) * 240, sol[1] + math.sin(ang_c - larg_c / 2) * 240)
            p3 = (sol[0] + math.cos(ang_c + larg_c / 2) * 240, sol[1] + math.sin(ang_c + larg_c / 2) * 240)
            pygame.draw.polygon(raios, (255, 215, 140, alfa_raio), [p1, p2, p3])
        tela.blit(raios, (0, 0))

        # Montanhas em paralaxe
        for surf, vel in self.camadas:
            desloc = round(t * vel) % self.LARG_PARALAXE
            tela.blit(surf, (-desloc, 0))
            tela.blit(surf, (self.LARG_PARALAXE - desloc, 0))

        # Castelo gótico com rim-lighting, ameias e pontes aéreas
        cx, cy = 212, 62
        self._desenhar_castelo_vivo(tela, cx, cy, t)

        self._desenhar_lago(tela, t, sol, cx)
        tela.blit(self.colina, (0, 0))
        self._desenhar_heroi(tela, t)
        self._desenhar_petalas_vento(tela, t)

        # Vagalumes / pólen dourado
        for x, y, fase in self.vagalumes:
            if math.sin(fase * 3) > -0.2:
                tela.set_at((round(x), round(y + math.sin(fase) * 3)), (255, 236, 150))

        self._desenhar_logo(tela, t)

        if self.estado == "abertura":
            # Fade do preto com clarão quando o logo chega
            alfa = max(0, round(255 * (1 - t / 1.6)))
            if alfa:
                preto = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
                preto.fill((0, 0, 0, alfa))
                tela.blit(preto, (0, 0))
            if 1.6 < t < 2.2:
                flash = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
                flash.fill((255, 250, 230, round(160 * (1 - (t - 1.6) / 0.6))))
                tela.blit(flash, (0, 0))
            return

        if self.transicao < 0.5:
            # Cápsula de Prompt Vítrea Retrô com Bordas Douradas e Respiração Suave
            pulso_enter = 0.5 + 0.5 * math.sin(self.t * 3.4)
            cor_txt_enter = _misturar((255, 235, 140), (255, 255, 245), pulso_enter)
            larg_prompt = 172
            alt_prompt = 15
            rect_prompt = pygame.Rect(LARGURA // 2 - larg_prompt // 2, 126, larg_prompt, alt_prompt)

            s_prompt = pygame.Surface((larg_prompt, alt_prompt), pygame.SRCALPHA)
            s_prompt.fill((14, 18, 38, round(195 + 35 * pulso_enter)))
            pygame.draw.rect(s_prompt, (85, 55, 30), s_prompt.get_rect(), 1)
            pygame.draw.rect(s_prompt, (235, 195, 95), s_prompt.get_rect().inflate(-2, -2), 1)
            tela.blit(s_prompt, rect_prompt.topleft)

            desenhar_texto(tela, self.app.fontes.normal, "◆  PRESSIONE ENTER  ◆", (LARGURA // 2, 133), cor_txt_enter, centro=True)
            desenhar_texto(tela, self.app.fontes.normal, "✦  Versão 2.0  •  2026  ✦", (LARGURA // 2, ALTURA - 9), (210, 180, 205), centro=True)

        if self.transicao > 0.02:
            self._desenhar_menu(tela)

        # Filtro de Profundidade de Campo HD-2D sutil
        from render3d import desenhar_tilt_shift_dof
        desenhar_tilt_shift_dof(tela, t)

    def _desenhar_ceu_vivo(self, tela, t):
        for x, y, freq, fase in self.estrelas:
            b = 0.5 + 0.5 * math.sin(t * freq + fase)
            if y > 80:
                b *= 0.4
            if b > 0.15:
                c = round(150 + 105 * b)
                tela.set_at((x, y), (c, c, min(255, c + 20)))
        # Aurora: cortinas de luz ondulando
        aurora = pygame.Surface((LARGURA, 70), pygame.SRCALPHA)
        for faixa, (cor, fase, alt) in enumerate((((90, 255, 190), 0.0, 22), ((140, 160, 255), 1.7, 16))):
            for x in range(0, LARGURA, 2):
                y = 20 + faixa * 10 + math.sin(x * 0.025 + t * 0.6 + fase) * 8 + math.sin(x * 0.07 + t * 1.3) * 3
                a = round(26 + 22 * math.sin(x * 0.05 + t + fase))
                pygame.draw.line(aurora, (*cor, max(0, a)), (x, round(y)), (x, round(y + alt)), 2)
        tela.blit(aurora, (0, 0))
        if self.meteoro:
            m = self.meteoro
            for i in range(6):
                f = 1 - i / 6
                tela.set_at((round(m["x"] - i * 3), round(m["y"] - i * 1.2)), _misturar((60, 60, 100), (255, 250, 220), f))
        if self.passaros:
            p = self.passaros
            for i, (dx, dy) in enumerate(((0, 0), (-7, 4), (-7, -4), (-14, 8), (-13, -7))):
                bx, by = round(p["x"] + dx), round(p["y"] + dy)
                asa = 1 if math.sin(t * 12 + i) > 0 else -1
                pygame.draw.line(tela, (40, 26, 60), (bx - 2, by + asa), (bx, by))
                pygame.draw.line(tela, (40, 26, 60), (bx, by), (bx + 2, by + asa))

    def _desenhar_castelo_vivo(self, tela, cx, cy, t):
        """Castelo gótico imponente e detalhado com múltiplas torres, vitral rosácea, agulhas góticas,

        promontório de basalto, contrafortes, portão com grade iluminado e flâmulas tremulantes.
        """
        # Paleta de tons crepusculares e góticos
        sombra_prof = (20, 14, 32)
        sombra = (28, 20, 44)
        pedra = (44, 32, 62)
        pedra_luz = (68, 52, 90)
        pedra_destaque = (96, 76, 122)
        rim_sol = (255, 215, 140)
        rim_ceu = (130, 150, 205)
        ouro = (255, 225, 110)
        carmesim = (210, 40, 55)

        # -------------------------------------------------------------------------
        # 1. PROMONTÓRIO ROCHOSO (FALÉSIA / BASE DE BASALTO)
        # -------------------------------------------------------------------------
        pts_rocha = [
            (cx - 56, cy + 62),
            (cx - 52, cy + 50),
            (cx - 40, cy + 44),
            (cx - 15, cy + 46),
            (cx + 20, cy + 43),
            (cx + 46, cy + 48),
            (cx + 58, cy + 54),
            (cx + 62, cy + 62),
        ]
        pygame.draw.polygon(tela, sombra_prof, pts_rocha)
        pygame.draw.polygon(tela, sombra, [(p[0], p[1] - 2) for p in pts_rocha])
        # Estratos rochosos verticais e quinas iluminadas
        for rx, ry, h in ((cx - 46, cy + 48, 12), (cx - 25, cy + 46, 14), (cx + 12, cy + 45, 15), (cx + 38, cy + 48, 13)):
            pygame.draw.line(tela, pedra_destaque, (rx, ry), (rx + 2, ry + h))
            pygame.draw.line(tela, rim_sol, (rx + 3, ry), (rx + 5, ry + h - 2))

        # -------------------------------------------------------------------------
        # 2. TORRES DE FUNDO (SILHUETAS ESGUIAS COM AGULHAS GÓTICAS)
        # -------------------------------------------------------------------------
        # Torre de Fundo Esquerda (Alta e Esguia)
        tx_esq = cx - 34
        pygame.draw.rect(tela, sombra_prof, (tx_esq - 6, cy - 24, 12, 68))
        pygame.draw.rect(tela, sombra, (tx_esq - 5, cy - 22, 10, 66))
        # Agulha esbelta esquerda
        pygame.draw.polygon(tela, sombra_prof, [(tx_esq - 7, cy - 24), (tx_esq, cy - 54), (tx_esq + 7, cy - 24)])
        pygame.draw.polygon(tela, pedra, [(tx_esq - 5, cy - 24), (tx_esq, cy - 52), (tx_esq + 5, cy - 24)])
        pygame.draw.line(tela, rim_ceu, (tx_esq - 6, cy - 24), (tx_esq, cy - 54))
        # Pináculo e flâmula ondulante esquerda
        tela.set_at((tx_esq, cy - 55), ouro)
        flamula_onda1 = math.sin(t * 5.5) * 2.0
        pygame.draw.polygon(tela, carmesim, [(tx_esq, cy - 54), (tx_esq - 8, cy - 53 + round(flamula_onda1)), (tx_esq, cy - 51)])

        # Torre de Fundo Direita (Campanário)
        tx_dir = cx + 32
        pygame.draw.rect(tela, sombra_prof, (tx_dir - 7, cy - 28, 14, 72))
        pygame.draw.rect(tela, sombra, (tx_dir - 6, cy - 26, 12, 70))
        # Agulha esbelta direita
        pygame.draw.polygon(tela, sombra_prof, [(tx_dir - 8, cy - 28), (tx_dir, cy - 58), (tx_dir + 8, cy - 28)])
        pygame.draw.polygon(tela, pedra_luz, [(tx_dir - 6, cy - 28), (tx_dir, cy - 56), (tx_dir + 6, cy - 28)])
        pygame.draw.line(tela, rim_sol, (tx_dir, cy - 57), (tx_dir + 7, cy - 28), 2)
        # Pináculo e flâmula direita
        tela.set_at((tx_dir, cy - 59), ouro)
        flamula_onda2 = math.sin(t * 6.2 + 1.2) * 2.2
        pygame.draw.polygon(tela, carmesim, [(tx_dir, cy - 58), (tx_dir + 9, cy - 57 + round(flamula_onda2)), (tx_dir, cy - 55)])

        # Arcada sineira da torre direita
        pygame.draw.rect(tela, sombra_prof, (tx_dir - 3, cy - 20, 6, 8))
        pygame.draw.circle(tela, sombra_prof, (tx_dir, cy - 20), 3)
        tela.set_at((tx_dir, cy - 18), ouro)

        # -------------------------------------------------------------------------
        # 3. PONTE AÉREA / PASSADIÇO COM ARCADAS VAZADAS
        # -------------------------------------------------------------------------
        # Conecta a torre esquerda de fundo ao corpo central
        pygame.draw.rect(tela, sombra, (cx - 30, cy + 12, 16, 8))
        pygame.draw.line(tela, rim_ceu, (cx - 30, cy + 12), (cx - 14, cy + 12))
        for ax in (cx - 27, cx - 19):
            pygame.draw.rect(tela, (18, 14, 28), (ax, cy + 15, 4, 5))
            pygame.draw.circle(tela, (18, 14, 28), (ax + 2, cy + 15), 2)

        # -------------------------------------------------------------------------
        # 4. MURALHAS E AMEIAS DO MEIO-PLANO
        # -------------------------------------------------------------------------
        pygame.draw.rect(tela, sombra, (cx - 48, cy + 26, 96, 28))
        pygame.draw.rect(tela, pedra, (cx - 46, cy + 28, 92, 24))
        # Friso de mísulas / corbels abaixo das ameias
        for bx in range(cx - 46, cx + 46, 5):
            pygame.draw.line(tela, sombra_prof, (bx, cy + 26), (bx, cy + 28))
            pygame.draw.line(tela, pedra_destaque, (bx + 1, cy + 26), (bx + 1, cy + 28))
        # Ameias com seteiras
        for bx in range(cx - 46, cx + 46, 7):
            pygame.draw.rect(tela, sombra_prof, (bx - 1, cy + 20, 5, 6))
            pygame.draw.rect(tela, pedra_luz, (bx, cy + 21, 3, 5))
            pygame.draw.line(tela, rim_sol, (bx + 3, cy + 20), (bx + 3, cy + 25))

        # -------------------------------------------------------------------------
        # 5. GRANDE TORREÃO CENTRAL DE MENAGEM (DONJON IMPERIAL)
        # -------------------------------------------------------------------------
        # Corpo principal dividido em 3 andares com contrafortes
        pygame.draw.rect(tela, sombra_prof, (cx - 20, cy - 14, 40, 68))
        pygame.draw.rect(tela, pedra, (cx - 18, cy - 12, 36, 66))
        pygame.draw.rect(tela, pedra_luz, (cx + 4, cy - 12, 14, 66))
        # Contrafortes laterais chanfrados
        pygame.draw.polygon(tela, sombra_prof, [(cx - 22, cy + 54), (cx - 22, cy + 16), (cx - 18, cy + 10), (cx - 18, cy + 54)])
        pygame.draw.polygon(tela, pedra_destaque, [(cx + 18, cy + 10), (cx + 22, cy + 16), (cx + 22, cy + 54), (cx + 18, cy + 54)])
        pygame.draw.line(tela, rim_sol, (cx + 22, cy + 16), (cx + 22, cy + 54), 2)

        # Ameias e torrinhas suspensas do topo da torre central
        pygame.draw.rect(tela, sombra_prof, (cx - 21, cy - 18, 42, 6))
        pygame.draw.rect(tela, pedra_destaque, (cx - 20, cy - 17, 40, 5))
        for bx in range(cx - 19, cx + 21, 6):
            pygame.draw.rect(tela, pedra_luz, (bx, cy - 22, 3, 5))
            pygame.draw.line(tela, rim_sol, (bx + 3, cy - 22), (bx + 3, cy - 18))

        # Telhado íngreme gótico em pavilhão
        pygame.draw.polygon(tela, sombra_prof, [(cx - 18, cy - 18), (cx, cy - 44), (cx + 18, cy - 18)])
        pygame.draw.polygon(tela, (60, 36, 78), [(cx - 16, cy - 18), (cx, cy - 42), (cx, cy - 18)])
        pygame.draw.polygon(tela, (92, 54, 115), [(cx, cy - 42), (cx + 16, cy - 18), (cx, cy - 18)])
        pygame.draw.line(tela, rim_sol, (cx, cy - 42), (cx + 17, cy - 18), 2)

        # Torrinhas de canto suspensas (echauguettes)
        for ech_x, dir_luz in ((cx - 19, False), (cx + 19, True)):
            pygame.draw.rect(tela, sombra_prof, (ech_x - 3, cy - 28, 6, 12))
            pygame.draw.polygon(tela, (88, 52, 110) if dir_luz else (50, 32, 68), [(ech_x - 3, cy - 28), (ech_x, cy - 38), (ech_x + 3, cy - 28)])
            if dir_luz:
                pygame.draw.line(tela, rim_sol, (ech_x, cy - 38), (ech_x + 3, cy - 28))

        # Grande Agulha Imperial (Grand Spire)
        pygame.draw.line(tela, pedra_destaque, (cx, cy - 44), (cx, cy - 58), 2)
        tela.set_at((cx, cy - 59), ouro)
        # Flâmula imperial do topo
        onda_flam_imp = math.sin(t * 5.8 + 0.5) * 2.5
        pygame.draw.polygon(tela, carmesim, [(cx, cy - 58), (cx + 14, cy - 56 + round(onda_flam_imp)), (cx, cy - 53)])
        pygame.draw.line(tela, ouro, (cx, cy - 56), (cx + 14, cy - 56 + round(onda_flam_imp)))

        # Orbe Astral radiante no pináculo
        pulso_orbe = 0.5 + 0.5 * math.sin(t * 3.5)
        s_orbe = pygame.Surface((22, 22), pygame.SRCALPHA)
        pygame.draw.circle(s_orbe, (160, 220, 255, round(45 + 40 * pulso_orbe)), (11, 11), 10)
        pygame.draw.circle(s_orbe, (210, 245, 255, round(120 + 80 * pulso_orbe)), (11, 11), 5)
        pygame.draw.circle(s_orbe, (255, 255, 255, 255), (11, 11), 2)
        tela.blit(s_orbe, (cx - 11, cy - 69))

        # -------------------------------------------------------------------------
        # 6. GRANDE VITRAL ROSÁCEA GÓTICO (ROSE WINDOW)
        # -------------------------------------------------------------------------
        rx_centro, ry_centro = cx, cy + 2
        pygame.draw.circle(tela, sombra_prof, (rx_centro, ry_centro), 7)
        pygame.draw.circle(tela, pedra_destaque, (rx_centro, ry_centro), 6)
        cintila_ros = math.sin(t * 4.0) * 25
        cor_ros_ouro = (min(255, round(245 + cintila_ros)), round(195 + cintila_ros), 70)
        pygame.draw.circle(tela, cor_ros_ouro, (rx_centro, ry_centro), 5)
        pygame.draw.circle(tela, (110, 210, 255), (rx_centro, ry_centro), 3)
        tela.set_at((rx_centro, ry_centro), (255, 255, 255))
        pygame.draw.line(tela, sombra_prof, (rx_centro - 5, ry_centro), (rx_centro + 5, ry_centro))
        pygame.draw.line(tela, sombra_prof, (rx_centro, ry_centro - 5), (rx_centro, ry_centro + 5))

        # -------------------------------------------------------------------------
        # 7. BASTIÕES FRONTAIS LATERAIS (TORRES DO PRIMEIRO PLANO)
        # -------------------------------------------------------------------------
        # Bastião Esquerdo
        bx_esq = cx - 33
        pygame.draw.rect(tela, sombra_prof, (bx_esq - 10, cy + 4, 20, 52))
        pygame.draw.rect(tela, pedra, (bx_esq - 9, cy + 6, 18, 50))
        for ax in range(bx_esq - 8, bx_esq + 9, 5):
            pygame.draw.rect(tela, pedra_destaque, (ax, cy + 1, 3, 5))
        pygame.draw.polygon(tela, sombra_prof, [(bx_esq - 11, cy + 4), (bx_esq, cy - 18), (bx_esq + 11, cy + 4)])
        pygame.draw.polygon(tela, (65, 40, 85), [(bx_esq - 9, cy + 4), (bx_esq, cy - 16), (bx_esq + 9, cy + 4)])
        pygame.draw.line(tela, rim_ceu, (bx_esq - 10, cy + 4), (bx_esq, cy - 17))
        tela.set_at((bx_esq, cy - 19), ouro)

        # Bastião Direito (banhado pelo rim-light do nascente)
        bx_dir = cx + 31
        pygame.draw.rect(tela, sombra_prof, (bx_dir - 10, cy + 2, 20, 54))
        pygame.draw.rect(tela, pedra_luz, (bx_dir - 9, cy + 4, 18, 52))
        for ax in range(bx_dir - 8, bx_dir + 9, 5):
            pygame.draw.rect(tela, pedra_destaque, (ax, cy - 1, 3, 5))
            pygame.draw.line(tela, rim_sol, (ax + 2, cy - 1), (ax + 2, cy + 3))
        pygame.draw.polygon(tela, sombra_prof, [(bx_dir - 11, cy + 2), (bx_dir, cy - 22), (bx_dir + 11, cy + 2)])
        pygame.draw.polygon(tela, (95, 58, 120), [(bx_dir - 9, cy + 2), (bx_dir, cy - 20), (bx_dir + 9, cy + 2)])
        pygame.draw.line(tela, rim_sol, (bx_dir, cy - 21), (bx_dir + 11, cy + 2), 2)
        pygame.draw.line(tela, rim_sol, (bx_dir + 10, cy + 4), (bx_dir + 10, cy + 54), 2)
        tela.set_at((bx_dir, cy - 23), ouro)

        # -------------------------------------------------------------------------
        # 8. PORTAL EM ARCO OGIVAL (BARBACÃ COM GRADE E ILUMINAÇÃO INTERNA)
        # -------------------------------------------------------------------------
        px_portao = cx
        py_portao = cy + 40
        pygame.draw.rect(tela, sombra_prof, (px_portao - 7, py_portao, 14, 18))
        pygame.draw.circle(tela, sombra_prof, (px_portao, py_portao), 7)
        pygame.draw.rect(tela, (255, 185, 60), (px_portao - 5, py_portao + 2, 10, 16))
        pygame.draw.circle(tela, (255, 215, 110), (px_portao, py_portao + 2), 5)
        for gx in range(px_portao - 4, px_portao + 5, 2):
            pygame.draw.line(tela, sombra_prof, (gx, py_portao - 1), (gx, py_portao + 17))
        for gy in range(py_portao + 4, py_portao + 16, 4):
            pygame.draw.line(tela, sombra_prof, (px_portao - 5, gy), (px_portao + 4, gy))
        pygame.draw.arc(tela, rim_sol, (px_portao - 8, py_portao - 8, 16, 16), 0, math.pi, 2)

        # -------------------------------------------------------------------------
        # 9. JANELAS GÓTICAS EM ARCO COM LUZ CINTILANTE E PEITORIS
        # -------------------------------------------------------------------------
        janelas_goticas = [
            (bx_esq, cy + 18, 3, 6, 0.5, True),
            (bx_esq, cy + 32, 3, 6, 1.8, True),
            (cx - 10, cy + 18, 3, 7, 2.4, True),
            (cx + 10, cy + 18, 3, 7, 3.1, True),
            (cx - 10, cy + 30, 3, 6, 0.9, False),
            (cx + 10, cy + 30, 3, 6, 4.2, False),
            (bx_dir, cy + 16, 3, 7, 1.2, True),
            (bx_dir, cy + 30, 3, 6, 2.7, True),
            (tx_esq, cy - 8, 2, 5, 3.6, False),
            (tx_dir, cy - 10, 2, 5, 0.3, False),
        ]
        for jx, jy, jw, jh, fase, arco in janelas_goticas:
            cint = math.sin(t * 4.8 + fase * 2.3) * 22
            cor_j = (min(255, round(255 + cint)), max(0, min(255, round(210 + cint))), 80)
            pygame.draw.rect(tela, (16, 10, 24), (jx - 1, jy - 1, jw + 2, jh + 2))
            pygame.draw.line(tela, pedra_destaque, (jx - 1, jy + jh), (jx + jw, jy + jh))
            pygame.draw.rect(tela, cor_j, (jx, jy, jw, jh))
            if arco:
                pygame.draw.line(tela, (255, 240, 180), (jx, jy), (jx + jw - 1, jy))
            tela.set_at((jx + 1, jy + 1), (255, 255, 220))

        # -------------------------------------------------------------------------
        # 10. CHAMINÉ COM VOLUTAS DE FUMAÇA ORGÂNICAS
        # -------------------------------------------------------------------------
        ch_x, ch_y = cx + 8, cy - 16
        pygame.draw.rect(tela, sombra_prof, (ch_x, ch_y, 4, 8))
        pygame.draw.rect(tela, pedra_destaque, (ch_x, ch_y, 3, 7))
        for k in range(5):
            fase_fum = (t * 1.8 + k * 0.7) % 3.0
            fum_x = ch_x + 1 - fase_fum * 3.5 + math.sin(t * 2.0 + k) * 1.5
            fum_y = ch_y - fase_fum * 7.0
            alfa_fum = max(0, min(90, round((1.0 - fase_fum / 3.0) * 90)))
            raio_fum = max(1, round(1.2 + fase_fum * 1.1))
            s_fum = pygame.Surface((raio_fum * 2 + 2, raio_fum * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(s_fum, (190, 195, 220, alfa_fum), (raio_fum + 1, raio_fum + 1), raio_fum)
            tela.blit(s_fum, (round(fum_x - raio_fum), round(fum_y - raio_fum)))

    def _desenhar_lago(self, tela, t, sol, cx_castelo):
        topo = 124
        larg = LARGURA
        alt = ALTURA - topo
        lago = pygame.Surface((larg, alt), pygame.SRCALPHA)

        # Gradiente da água com absorção de profundidade
        for y in range(alt):
            fator_prof = y / alt
            # Mistura do reflexo do céu escuro com azul marinho crepuscular
            cor = _misturar((26, 28, 58), (14, 18, 40), fator_prof * 0.8)
            lago.fill((*cor, 255), (0, y, larg, 1))

        # Reflexo invertido da silhueta do castelo na água
        for y in range(alt - 4):
            desloc_onda = math.sin(t * 3.8 + y * 0.6) * (1.2 + y * 0.1)
            alfa_refl = round(max(0, 110 - y * 4))
            if alfa_refl > 0:
                refl_x = round(cx_castelo + desloc_onda)
                larg_refl = max(4, round(54 - y * 1.1))
                pygame.draw.line(lago, (18, 14, 32, alfa_refl), (refl_x - larg_refl // 2, y), (refl_x + larg_refl // 2, y))

        # Reflexo das janelas e portal iluminado do castelo na lâmina d'água
        for y in range(min(alt - 4, 20)):
            desloc_onda = math.sin(t * 4.2 + y * 0.75) * (1.5 + y * 0.12)
            alfa_luz = round(max(0, 105 - y * 5.2))
            if alfa_luz > 0:
                refl_gx = round(cx_castelo + desloc_onda)
                larg_gl = max(4, round(18 - y * 0.7))
                pygame.draw.line(lago, (245, 185, 75, alfa_luz), (refl_gx - larg_gl // 2, y), (refl_gx + larg_gl // 2, y))

        # Trilha de reflexo dourado do sol ondulando
        sx = sol[0]
        for k in range(alt - 6):
            onda = math.sin(t * 4.2 + k * 0.45) * (2.0 + k * 0.08)
            larg_sol = max(2, round(24 - k * 0.5 + onda))
            alfa_sol = round(max(0, 175 - k * 4.5))
            if alfa_sol > 0:
                pygame.draw.line(lago, (255, 215, 130, alfa_sol), (round(sx - larg_sol // 2 + onda), k), (round(sx + larg_sol // 2 + onda), k))

        # Brilhos esparsos cintilantes na água
        for k in range(22):
            x = (k * 43 + round(t * 11)) % larg
            y = 2 + (k * 11) % (alt - 6)
            if math.sin(t * 3.6 + k * 2.1) > 0.2:
                pygame.draw.line(lago, (230, 225, 255, 140), (x, y), (x + 3, y))

        # Névoa matinal flutuando sobre a lâmina d'água
        nevoa = pygame.Surface((larg, 14), pygame.SRCALPHA)
        for x in range(0, larg, 3):
            alt_nev = 3 + math.sin(x * 0.04 + t * 0.8) * 2 + math.sin(x * 0.1 - t * 0.5) * 1.5
            alfa_nev = round(32 + 18 * math.sin(x * 0.03 + t * 0.6))
            pygame.draw.line(nevoa, (215, 225, 255, alfa_nev), (x, round(7 - alt_nev)), (x, round(7 + alt_nev)), 3)
        lago.blit(nevoa, (0, 0))

        tela.blit(lago, (0, topo))
        # Linha de horizonte reluzente na borda do lago
        pygame.draw.line(tela, (255, 225, 175), (0, topo), (larg, topo))

    def _desenhar_heroi(self, tela, t):
        """O herói contemplando o castelo na colina, fogueira aconchegante com brasas e fada-guia."""
        hx, hy = 72, 140

        # --- Fogueira de acampamento em pedras (cx=44, cy=142) ---
        fx, fy = 44, 142
        # Círculo de pedras
        pedras = [(-6, 2), (-3, 3), (2, 3), (6, 2), (-4, -1), (4, -1)]
        for dx, dy in pedras:
            tela.set_at((fx + dx, fy + dy), (75, 70, 78))
            tela.set_at((fx + dx + 1, fy + dy), (105, 100, 110))

        # Troncos de madeira cruzados
        pygame.draw.line(tela, (65, 38, 22), (fx - 5, fy + 1), (fx + 5, fy - 1), 2)
        pygame.draw.line(tela, (85, 48, 28), (fx - 4, fy - 1), (fx + 4, fy + 1), 2)

        # Resplendor quente no chão
        pulso_fogo = 0.5 + 0.5 * math.sin(t * 14.0)
        s_brilho_chao = pygame.Surface((32, 20), pygame.SRCALPHA)
        pygame.draw.ellipse(s_brilho_chao, (255, 130, 40, round(45 + 25 * pulso_fogo)), (0, 0, 32, 20))
        tela.blit(s_brilho_chao, (fx - 16, fy - 9))

        # Chamas animadas da fogueira
        alt_chama = 7 + math.sin(t * 18.0) * 2 + math.cos(t * 24.0) * 1.5
        chama_pts = [
            (fx - 4, fy + 1),
            (fx + 4, fy + 1),
            (fx + 2, round(fy - alt_chama * 0.6)),
            (fx + math.sin(t * 12.0) * 1.5, round(fy - alt_chama)),
            (fx - 2, round(fy - alt_chama * 0.6)),
        ]
        pygame.draw.polygon(tela, (230, 60, 25), chama_pts)
        chama_miolo = [
            (fx - 2, fy + 1),
            (fx + 2, fy + 1),
            (fx, round(fy - alt_chama * 0.75)),
        ]
        pygame.draw.polygon(tela, (255, 230, 110), chama_miolo)
        tela.set_at((round(fx), round(fy - alt_chama * 0.4)), (255, 255, 240))

        # Faíscas / brasas subindo da fogueira
        for i in range(6):
            fase_faisca = (t * (2.2 + i * 0.4) + i * 1.4) % 1.0
            px = fx + math.sin(t * 5.0 + i * 2.0) * 3 + (i - 2.5) * 1.5
            py = fy - 4 - fase_faisca * 24
            alfa_f = 1.0 - fase_faisca
            if alfa_f > 0.15:
                cor_f = _misturar((255, 110, 30), (255, 240, 160), alfa_f)
                tela.set_at((round(px), round(py)), cor_f)

        # --- Herói ---
        quadro = self.app.gfx.jogador["cima"][6 if math.sin(t * 2.8) > 0.35 else 2]
        tela.blit(quadro, quadro.get_rect(midbottom=(hx, hy + 1)))

        # Cachecol carmesim esvoaçando ao vento
        for i in range(5):
            px = hx + 3 + i * 3
            py = hy - 17 + round(math.sin(t * 8.5 - i * 0.9) * 1.8) + i // 2
            cor_cachecol = (235, 52, 60) if i % 2 == 0 else (175, 30, 42)
            pygame.draw.rect(tela, cor_cachecol, (px, py, 3, 2))

        # Fada-guia orbitando com rastro de poeira estelar
        ang = t * 2.4
        fx_fada = hx + math.cos(ang) * 15
        fy_fada = hy - 21 + math.sin(ang * 1.4) * 7
        halo = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.circle(halo, (150, 225, 255, 65), (8, 8), 8)
        pygame.draw.circle(halo, (215, 245, 255, 145), (8, 8), 4)
        tela.blit(halo, (round(fx_fada) - 8, round(fy_fada) - 8))
        pygame.draw.circle(tela, (255, 255, 255), (round(fx_fada), round(fy_fada)), 1)
        for i in range(1, 6):
            a = ang - i * 0.16
            r_x = round(hx + math.cos(a) * 15)
            r_y = round(hy - 21 + math.sin(a * 1.4) * 7)
            if 0 <= r_x < LARGURA and 0 <= r_y < ALTURA:
                tela.set_at((r_x, r_y), (140 + i * 18, 215, 255))

        # Grama alta balançando ao vento
        for i, gx in enumerate(range(4, 150, 5)):
            base_y = 150 - (gx // 40) + (4 if gx > 110 else 0) + (gx - 110) // 3 * (1 if gx > 110 else 0)
            balanco = round(math.sin(t * 2.6 + gx * 0.22) * 2)
            pygame.draw.line(tela, (34, 70, 46), (gx, base_y), (gx + balanco, base_y - 5 - i % 3))

    def _desenhar_petalas_vento(self, tela, t):
        """Pétalas e pólen dourado levados suavemente pela brisa crepuscular."""
        for i in range(12):
            vel_x = 18 + (i % 4) * 6
            px = (i * 31 + t * vel_x) % (LARGURA + 30) - 15
            py = 35 + (i * 23 + math.sin(t * 2.4 + i * 1.3) * 10) % 115
            cor_petala = (255, 195, 215) if i % 2 == 0 else (255, 235, 165)
            # Desenha pétala levemente inclinada
            tela.set_at((round(px), round(py)), cor_petala)
            tela.set_at((round(px + 1), round(py)), cor_petala)
            tela.set_at((round(px), round(py + 1)), (210, 150, 175))

    def _desenhar_logo(self, tela, t):
        fonte = self.app.fontes.normal
        if self.estado == "abertura":
            prog = max(0.0, min(1.0, (t - 0.8) / 0.8))
        else:
            prog = 1.0
        queda = (1 - prog) ** 2
        y_logo = round(30 - queda * 60)
        cx = LARGURA // 2

        # Brasão Celestial acima do título: Asas Seráficas com 3 camadas, anel místico e espada sagrada
        brasao_y = y_logo - 14
        for lado in (-1, 1):
            for p in range(5):
                comp = 34 - p * 6
                y_pena = brasao_y - 4 + p * 2
                ponta = (cx + lado * (8 + comp), y_pena - 9 + p * 3)
                # Contorno escuro da pena
                pygame.draw.line(tela, (55, 28, 22), (cx + lado * 7, y_pena + 1), (ponta[0], ponta[1] + 1), 2)
                # Gradiente de ouro celestial
                cor_pena = _misturar((255, 245, 190), (225, 160, 65), p / 5)
                pygame.draw.line(tela, cor_pena, (cx + lado * 7, y_pena), ponta, 2)

        # Anel de Runas Místicas girando em torno do brasão
        for k in range(12):
            a = t * 0.75 + k * math.tau / 12
            px, py = cx + round(math.cos(a) * 13), brasao_y + round(math.sin(a) * 5)
            tela.set_at((px, py), (255, 225, 140) if k % 2 else (135, 235, 255))

        # Espada Sagrada atravessando o topo
        espada_topo = brasao_y - 6
        # Bainha / Lâmina
        pygame.draw.polygon(tela, (36, 26, 48), [(cx - 3, espada_topo), (cx + 3, espada_topo), (cx + 2, y_logo + 25), (cx, y_logo + 29), (cx - 2, y_logo + 25)])
        pygame.draw.polygon(tela, (225, 235, 255), [(cx - 2, espada_topo + 1), (cx + 2, espada_topo + 1), (cx + 1, y_logo + 24), (cx, y_logo + 27), (cx - 1, y_logo + 24)])
        pygame.draw.line(tela, (255, 255, 255), (cx - 1, espada_topo + 1), (cx - 1, y_logo + 23))

        # Guarda e empunhadura dourada
        pygame.draw.rect(tela, (230, 185, 75), (cx - 9, espada_topo - 2, 19, 3))
        pygame.draw.rect(tela, (135, 75, 42), (cx - 1, espada_topo - 9, 3, 7))

        # Joia sagrada no pomo com pulso
        halo_c = pygame.Surface((16, 16), pygame.SRCALPHA)
        pulso_joia = 0.5 + 0.5 * math.sin(t * 3.5)
        pygame.draw.circle(halo_c, (110, 230, 255, round(70 + 40 * pulso_joia)), (8, 8), 7)
        tela.blit(halo_c, (cx - 7, espada_topo - 17))
        pygame.draw.circle(tela, (130, 240, 255), (cx + 1, espada_topo - 10), 2)
        tela.set_at((cx + 1, espada_topo - 10), (255, 255, 255))

        # Título principal renderizado
        tela.blit(self.logo, self.logo.get_rect(center=(cx, y_logo + 8)))

        # Varredura Especular e Cintilações de Estrela no Título "A LENDA PERDIDA"
        ciclo = (t % 3.6) / 1.4
        r_logo = self.logo.get_rect(center=(cx, y_logo + 8))
        if 0 <= ciclo <= 1 and tela.get_rect().contains(r_logo):
            x_brilho = round(cx - 120 + ciclo * 240)
            faixa = pygame.Surface((10, 30), pygame.SRCALPHA)
            pygame.draw.polygon(faixa, (255, 255, 255, 110), [(4, 0), (10, 0), (6, 30), (0, 30)])
            r = self.logo.get_rect(center=(cx, y_logo + 8))
            alvo = tela.subsurface(r).copy()
            mascara = pygame.mask.from_surface(self.logo)
            brilho = pygame.Surface(r.size, pygame.SRCALPHA)
            brilho.blit(faixa, (x_brilho - r.x, 0))
            brilho.blit(mascara.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0)), (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            alvo.blit(brilho, (0, 0))
            tela.blit(alvo, r)

            # Estrela reluzente no ponto ápice do brilho
            if 0.2 < ciclo < 0.8:
                gx = round(cx - 90 + ciclo * 180)
                gy = y_logo + 4
                s_glint = pygame.Surface((9, 9), pygame.SRCALPHA)
                pygame.draw.line(s_glint, (255, 255, 255, 220), (4, 0), (4, 8), 1)
                pygame.draw.line(s_glint, (255, 255, 255, 220), (0, 4), (8, 4), 1)
                pygame.draw.circle(s_glint, (255, 240, 180, 240), (4, 4), 1)
                tela.blit(s_glint, (gx - 4, gy - 4))

        # Faixa Rubro-Carmensim Ornamental com Bordado Dourado
        fita_y = y_logo + 26
        largura_fita = 172
        # Pontas bipartidas da flâmula
        pygame.draw.polygon(tela, (100, 26, 36), [(cx - largura_fita // 2 - 10, fita_y + 2), (cx - largura_fita // 2, fita_y - 2), (cx - largura_fita // 2, fita_y + 10), (cx - largura_fita // 2 - 10, fita_y + 12), (cx - largura_fita // 2 - 5, fita_y + 7)])
        pygame.draw.polygon(tela, (100, 26, 36), [(cx + largura_fita // 2 + 10, fita_y + 2), (cx + largura_fita // 2, fita_y - 2), (cx + largura_fita // 2, fita_y + 10), (cx + largura_fita // 2 + 10, fita_y + 12), (cx + largura_fita // 2 + 5, fita_y + 7)])
        # Corpo da fita
        pygame.draw.rect(tela, (168, 40, 52), (cx - largura_fita // 2, fita_y - 3, largura_fita, 13))
        # Friso dourado superior e inferior com cantos estilizados
        pygame.draw.line(tela, (255, 215, 120), (cx - largura_fita // 2, fita_y - 3), (cx + largura_fita // 2, fita_y - 3))
        pygame.draw.line(tela, (230, 180, 85), (cx - largura_fita // 2, fita_y + 9), (cx + largura_fita // 2, fita_y + 9))
        desenhar_texto(tela, fonte, "Crônicas do Reino Esquecido", (cx, fita_y + 3), (255, 242, 210), centro=True)

    def _desenhar_menu(self, tela):
        fonte = self.app.fontes.normal
        f = self.transicao
        # Escurece o pé da tela atrás das janelas
        sombra = pygame.Surface((LARGURA, 90), pygame.SRCALPHA)
        for y in range(90):
            sombra.fill((6, 4, 18, round(min(200, y * 4) * f)), (0, y, LARGURA, 1))
        tela.blit(sombra, (0, ALTURA - 90))

        desliza = round((1 - f) * 70)
        # Janela de opções com cursor de mão
        janela = pygame.Rect(14, 74 + desliza, 116, len(self.opcoes) * 14 + 12)
        desenhar_painel(tela, janela, alfa=round(235 * f))
        for i, op in enumerate(self.opcoes):
            y = janela.y + 8 + i * 14
            sel = i == self.indice
            bloqueado = (op == "Modo Chefões" and not self.modo_chefes_liberado)
            if sel:
                faixa = pygame.Surface((janela.width - 8, 12), pygame.SRCALPHA)
                if bloqueado:
                    faixa.fill((210, 70, 70, 45))
                else:
                    faixa.fill((255, 220, 120, 40))
                tela.blit(faixa, (janela.x + 4, y - 1))
                mx = janela.x + 3 + round(math.sin(self.t * 8) * 1.5)
                self._desenhar_mao(tela, mx, y + 1)
            if bloqueado:
                cor = (215, 160, 160) if sel else (140, 135, 150)
            else:
                cor = (255, 240, 170) if sel else (206, 210, 230)
            desenhar_texto(tela, fonte, op, (janela.x + 17, y), cor)
            if bloqueado:
                self._desenhar_cadeado(tela, janela.right - 14, y + 2, (245, 185, 75) if sel else (150, 140, 130))

        # Janela "Aventura" com resumo do save + descrição da opção
        info = pygame.Rect(138, 74 + desliza, LARGURA - 152, janela.height)
        desenhar_painel(tela, info, "magico", alfa=round(235 * f))
        y = info.y + 6
        escolha = self.opcoes[self.indice]
        if self.resumo_save and escolha in ("Continuar", "Novo jogo"):
            r = self.resumo_save
            desenhar_texto(tela, fonte, "Sua aventura", (info.x + 8, y), (255, 226, 140))
            desenhar_texto(tela, fonte, f"Nv {r['nivel']}", (info.right - 8 - fonte.size(f"Nv {r['nivel']}")[0], y), (190, 210, 255))
            y += 12
            local = limpar_texto(r["local"])
            while fonte.size(local)[0] > info.width - 16:
                local = local[:-1]
            desenhar_texto(tela, fonte, local, (info.x + 8, y), (220, 224, 240))
            y += 12
            for k in range(min(10, r["vida_maxima"] // 2)):
                cor = self.app.gfx.coracao_cheio if r["vida"] >= (k + 1) * 2 else (self.app.gfx.coracao_metade if r["vida"] == k * 2 + 1 else self.app.gfx.coracao_vazio)
                tela.blit(cor, (info.x + 8 + k * 9, y + 1))
            y += 12
            desenhar_icone(tela, "caveira", (info.x + 8, y + 1))
            desenhar_texto(tela, fonte, f"{r['chefes']}/{TOTAL_CHEFES}", (info.x + 18, y), (255, 200, 140))
            desenhar_icone(tela, "estrela", (info.x + 54, y + 1))
            desenhar_texto(tela, fonte, f"{r['reliquias']}/6", (info.x + 64, y), (255, 236, 150))
            desenhar_icone(tela, "moeda", (info.x + 94, y + 1))
            desenhar_texto(tela, fonte, str(r["ouro"]), (info.x + 104, y), (255, 222, 110))
            y += 14
        elif escolha in ("Continuar", "Novo jogo"):
            desenhar_texto(tela, fonte, "Nenhuma aventura salva.", (info.x + 8, y), CINZA)
            y += 14
        # Descrição da opção (quebrada em linhas)
        from ui import quebrar_linhas
        if escolha == "Modo Chefões" and not self.modo_chefes_liberado:
            desenhar_texto(tela, fonte, "MODO BLOQUEADO", (info.x + 8, y), (255, 120, 110))
            y += 12
            texto_bloqueio = "Derrote a Entidade Maligna e zere a história pela primeira vez para liberar o Desafio dos Guardiões!"
            for linha in quebrar_linhas(fonte, texto_bloqueio, info.width - 16)[:3]:
                desenhar_texto(tela, fonte, linha, (info.x + 8, y), (210, 200, 220))
                y += 11
        else:
            for linha in quebrar_linhas(fonte, DESCRICOES.get(escolha, ""), info.width - 16)[:3]:
                desenhar_texto(tela, fonte, linha, (info.x + 8, y), (200, 206, 230))
                y += 11

        if self.aviso_bloqueado > 0:
            pulso = int(math.sin(self.t * 14) * 35)
            cor_aviso = (255, 120 + pulso, 100)
            txt_aviso = "! Zere a história principal para desbloquear o Modo Chefões !"
            desenhar_texto(tela, fonte, txt_aviso, (LARGURA // 2, ALTURA - 8), cor_aviso, centro=True)
        else:
            controle = self.app.entrada.nome_controle()
            rodape = f"{controle}: A confirma, B volta" if controle else "Enter: confirmar   Esc: voltar"
            desenhar_texto(tela, fonte, rodape, (LARGURA // 2, ALTURA - 7), (190, 180, 210), centro=True)

    def _desenhar_cadeado(self, tela, x, y, cor_metal=(210, 160, 60)):
        pygame.draw.rect(tela, (170, 170, 185), (x + 1, y, 4, 3), 1)
        pygame.draw.rect(tela, cor_metal, (x, y + 2, 6, 5))
        pygame.draw.rect(tela, (50, 35, 15), (x, y + 2, 6, 5), 1)
        tela.set_at((x + 2, y + 4), (40, 20, 10))

    def _desenhar_mao(self, tela, x, y):
        cores = {"#": (30, 24, 40), "w": (255, 255, 255)}
        for dy, linha in enumerate(MAO):
            for dx, c in enumerate(linha):
                if c in cores:
                    tela.set_at((x + dx, y + dy), cores[c])
