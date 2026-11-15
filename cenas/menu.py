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
    "Editor de jogo": "Crie e edite mapas e cenas no próprio jogo.",
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
        self.opcoes = ["Novo jogo", "Modo Chefões", "Editor de jogo", "Configurações", "Sair"]
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
        from cenas.editor import Editor
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
            from salvamento import carregar_jogo
            salvo = carregar_jogo(self.app)
            self.app.trocar(salvo if salvo else Jogo(self.app))
        elif escolha == "Novo jogo":
            self.app.trocar(Jogo(self.app))
        elif escolha == "Modo Chefões":
            from cenas.modo_chefes import SelecaoChefes
            self.app.trocar(SelecaoChefes(self.app))
        elif escolha == "Editor de jogo":
            self.app.trocar(Editor(self.app))
        elif escolha == "Configurações":
            self.app.empilhar(Configuracoes(self.app))
        elif escolha == "Sair":
            self.app.sair()

    # ------------------------------------------------------------ desenho
    def desenhar(self, tela):
        t = self.t
        tela.blit(self.ceu, (0, 0))
        self._desenhar_ceu_vivo(tela, t)

        # Sol nascendo atrás do castelo
        sol = (250, 112)
        brilho = pygame.Surface((120, 60), pygame.SRCALPHA)
        for r in range(60, 0, -6):
            pygame.draw.circle(brilho, (255, 210, 140, round(70 * (1 - r / 60)) + 6), (60, 60), r)
        tela.blit(brilho, (sol[0] - 60, sol[1] - 60))
        pygame.draw.circle(tela, (255, 236, 180), sol, 13)
        pygame.draw.circle(tela, (255, 250, 220), sol, 9)

        # Montanhas em paralaxe
        for surf, vel in self.camadas:
            desloc = round(t * vel) % self.LARG_PARALAXE
            tela.blit(surf, (-desloc, 0))
            tela.blit(surf, (self.LARG_PARALAXE - desloc, 0))

        # Castelo com janelas acesas e farol de cristal
        cx, cy = 214, 64
        tela.blit(self.castelo, (cx, cy))
        for wx, wy in ((cx + 18, cy + 32), (cx + 34, cy + 22), (cx + 35, cy + 30), (cx + 51, cy + 36), (cx + 27, cy + 40)):
            if math.sin(t * 3 + wx) > -0.6:
                tela.set_at((wx, wy), (255, 214, 120))
        farol = (cx + 35, cy - 2)
        pulso = 0.5 + 0.5 * math.sin(t * 3)
        feixe = pygame.Surface((14, 60), pygame.SRCALPHA)
        pygame.draw.polygon(feixe, (140, 230, 255, round(30 + 30 * pulso)), [(5, 60), (9, 60), (14, 0), (0, 0)])
        tela.blit(feixe, (farol[0] - 7, farol[1] - 60))
        pygame.draw.circle(tela, (140, 230, 255), farol, 2)
        tela.set_at(farol, (255, 255, 255))

        self._desenhar_lago(tela, t)
        tela.blit(self.colina, (0, 0))
        self._desenhar_heroi(tela, t)

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
            if int(self.t * 2.2) % 2 == 0:
                txt = "PRESSIONE ENTER"
                desenhar_texto(tela, self.app.fontes.normal, txt, (LARGURA // 2, 132), (255, 244, 210), centro=True)
            desenhar_texto(tela, self.app.fontes.normal, "Versão 2.0  •  2026", (LARGURA // 2, ALTURA - 8), (200, 170, 190), centro=True)
        if self.transicao > 0.02:
            self._desenhar_menu(tela)

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

    def _desenhar_lago(self, tela, t):
        topo = 124
        lago = pygame.Surface((LARGURA, ALTURA - topo), pygame.SRCALPHA)
        for y in range(ALTURA - topo):
            espelho = self.ceu.get_at((0, max(0, topo - 1 - y * 2)))
            cor = _misturar(espelho, (30, 40, 80), 0.45 + y / (ALTURA - topo) * 0.4)
            lago.fill((*cor, 255), (0, y, LARGURA, 1))
        # Reflexo do sol e brilhos ondulando
        for k in range(14):
            y = 2 + k * 3
            larg = max(2, 26 - k * 2 + round(math.sin(t * 3 + k) * 3))
            pygame.draw.line(lago, (255, 220, 150, 170 - k * 10), (250 - larg // 2, y), (250 + larg // 2, y))
        for k in range(18):
            x = (k * 47 + round(t * 9)) % LARGURA
            y = 4 + (k * 13) % (ALTURA - topo - 6)
            if math.sin(t * 4 + k) > 0.3:
                pygame.draw.line(lago, (210, 200, 255, 120), (x, y), (x + 4, y))
        tela.blit(lago, (0, topo))
        pygame.draw.line(tela, (255, 220, 170), (0, topo), (LARGURA, topo))

    def _desenhar_heroi(self, tela, t):
        """O herói de costas na colina, olhando o castelo, com a fada-guia em volta."""
        quadro = self.app.gfx.jogador["cima"][6 if math.sin(t * 2.8) > 0.35 else 2]
        hx, hy = 70, 140
        tela.blit(quadro, quadro.get_rect(midbottom=(hx, hy + 1)))
        # Cachecol ao vento
        for i in range(4):
            px = hx + 3 + i * 3
            py = hy - 17 + round(math.sin(t * 8 - i) * 1.5) + i // 2
            pygame.draw.rect(tela, (220, 50, 56) if i % 2 == 0 else (160, 28, 40), (px, py, 3, 2))
        # Fada-guia
        ang = t * 2.2
        fx = hx + math.cos(ang) * 14
        fy = hy - 20 + math.sin(ang * 1.3) * 6
        halo = pygame.Surface((14, 14), pygame.SRCALPHA)
        pygame.draw.circle(halo, (170, 230, 255, 70), (7, 7), 7)
        pygame.draw.circle(halo, (220, 245, 255, 140), (7, 7), 4)
        tela.blit(halo, (round(fx) - 7, round(fy) - 7))
        pygame.draw.circle(tela, (255, 255, 255), (round(fx), round(fy)), 1)
        for i in range(1, 5):
            a = ang - i * 0.18
            tela.set_at((round(hx + math.cos(a) * 14), round(hy - 20 + math.sin(a * 1.3) * 6)), (150 + i * 20, 220, 255))
        # Grama alta balançando
        for i, gx in enumerate(range(4, 150, 5)):
            base_y = 150 - (gx // 40) + (4 if gx > 110 else 0) + (gx - 110) // 3 * (1 if gx > 110 else 0)
            balanco = round(math.sin(t * 2.5 + gx * 0.2) * 2)
            pygame.draw.line(tela, (34, 70, 46), (gx, base_y), (gx + balanco, base_y - 5 - i % 3))

    def _desenhar_logo(self, tela, t):
        fonte = self.app.fontes.normal
        if self.estado == "abertura":
            prog = max(0.0, min(1.0, (t - 0.8) / 0.8))
        else:
            prog = 1.0
        queda = (1 - prog) ** 2
        y_logo = round(30 - queda * 60)
        cx = LARGURA // 2

        # Brasão acima do título: asas abertas, anel rúnico e cristal; a espada atravessa o título
        brasao_y = y_logo - 13
        for lado in (-1, 1):
            for p in range(4):
                comp = 30 - p * 6
                y_pena = brasao_y - 3 + p * 2
                ponta = (cx + lado * (9 + comp), y_pena - 7 + p * 3)
                pygame.draw.line(tela, (60, 30, 20), (cx + lado * 8, y_pena + 1), (ponta[0], ponta[1] + 1), 2)
                pygame.draw.line(tela, _misturar((255, 240, 180), (220, 150, 60), p / 4), (cx + lado * 8, y_pena), ponta, 2)
        for k in range(12):
            a = t * 0.6 + k * math.tau / 12
            px, py = cx + round(math.cos(a) * 11), brasao_y + round(math.sin(a) * 4)
            tela.set_at((px, py), (255, 220, 140) if k % 2 else (140, 230, 255))
        espada_topo = brasao_y - 4
        pygame.draw.polygon(tela, (40, 30, 50), [(cx - 3, espada_topo), (cx + 3, espada_topo), (cx + 2, y_logo + 24), (cx, y_logo + 28), (cx - 2, y_logo + 24)])
        pygame.draw.polygon(tela, (214, 226, 246), [(cx - 2, espada_topo + 1), (cx + 2, espada_topo + 1), (cx + 1, y_logo + 23), (cx, y_logo + 26), (cx - 1, y_logo + 23)])
        pygame.draw.line(tela, (255, 255, 255), (cx - 1, espada_topo + 1), (cx - 1, y_logo + 22))
        pygame.draw.rect(tela, (220, 170, 60), (cx - 8, espada_topo - 2, 17, 3))
        pygame.draw.rect(tela, (120, 70, 40), (cx - 1, espada_topo - 9, 3, 7))
        halo_c = pygame.Surface((12, 12), pygame.SRCALPHA)
        pygame.draw.circle(halo_c, (120, 230, 255, 90), (6, 6), 6)
        tela.blit(halo_c, (cx - 6 + 1, espada_topo - 16))
        pygame.draw.circle(tela, (90, 230, 255), (cx + 1, espada_topo - 10), 2)

        # Título
        tela.blit(self.logo, self.logo.get_rect(center=(cx, y_logo + 8)))
        # Brilho que percorre as letras
        ciclo = (t % 4.0) / 1.2
        r_logo = self.logo.get_rect(center=(cx, y_logo + 8))
        if 0 <= ciclo <= 1 and tela.get_rect().contains(r_logo):
            x_brilho = round(cx - 120 + ciclo * 240)
            faixa = pygame.Surface((8, 30), pygame.SRCALPHA)
            pygame.draw.polygon(faixa, (255, 255, 255, 90), [(3, 0), (8, 0), (5, 30), (0, 30)])
            r = self.logo.get_rect(center=(cx, y_logo + 8))
            alvo = tela.subsurface(r).copy()
            mascara = pygame.mask.from_surface(self.logo)
            brilho = pygame.Surface(r.size, pygame.SRCALPHA)
            brilho.blit(faixa, (x_brilho - r.x, 0))
            brilho.blit(mascara.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0)), (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            alvo.blit(brilho, (0, 0))
            tela.blit(alvo, r)

        # Fita com o subtítulo
        fita_y = y_logo + 26
        largura_fita = 170
        pygame.draw.polygon(tela, (110, 30, 40), [(cx - largura_fita // 2 - 10, fita_y + 2), (cx - largura_fita // 2, fita_y - 2), (cx - largura_fita // 2, fita_y + 10), (cx - largura_fita // 2 - 10, fita_y + 12), (cx - largura_fita // 2 - 5, fita_y + 7)])
        pygame.draw.polygon(tela, (110, 30, 40), [(cx + largura_fita // 2 + 10, fita_y + 2), (cx + largura_fita // 2, fita_y - 2), (cx + largura_fita // 2, fita_y + 10), (cx + largura_fita // 2 + 10, fita_y + 12), (cx + largura_fita // 2 + 5, fita_y + 7)])
        pygame.draw.rect(tela, (170, 44, 54), (cx - largura_fita // 2, fita_y - 3, largura_fita, 13))
        pygame.draw.line(tela, (230, 110, 110), (cx - largura_fita // 2, fita_y - 3), (cx + largura_fita // 2, fita_y - 3))
        pygame.draw.line(tela, (230, 180, 90), (cx - largura_fita // 2, fita_y + 9), (cx + largura_fita // 2, fita_y + 9))
        desenhar_texto(tela, fonte, "Crônicas do Reino Esquecido", (cx, fita_y + 3), (255, 236, 200), centro=True)

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
