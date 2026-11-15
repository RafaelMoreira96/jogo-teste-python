"""Editor visual integrado: edite mapas, posicione personagens e teste cenas na hora."""
from pathlib import Path

import pygame

from cenas.base import Cena
from historia import Historia
from settings import ALTURA, ARQUIVO_HISTORIA, COR_FUNDO, LARGURA, PASTA_BASE, TILE
from ui import AMARELO, BRANCO, CINZA, MenuLista, desenhar_texto, escurecer

PINCEIS = [
    (".", "Grama"),
    (",", "Caminho"),
    ("*", "Flores"),
    ("~", "Água"),
    ("#", "Pedra"),
    ("T", "Árvore"),
    ("B", "Arbusto"),
    ("_", "Piso"),
    ("W", "Parede"),
    ("R", "Telhado"),
    ("C", "Cama"),
    ("M", "Mesa"),
    ("D", "Porta"),
    ("P", "Início Herói"),
    ("S", "Slime"),
    ("H", "Coração"),
    ("1", "NPC 1"),
    ("2", "NPC 2"),
    ("3", "NPC 3"),
    ("4", "NPC 4"),
    ("5", "NPC 5"),
]


class Editor(Cena):
    def __init__(self, app, caminho_mapa=None):
        super().__init__(app)
        self.arquivos_mapa = sorted((PASTA_BASE / "maps").glob("*.txt"))
        if caminho_mapa and Path(caminho_mapa) in self.arquivos_mapa:
            self.indice_mapa = self.arquivos_mapa.index(Path(caminho_mapa))
        else:
            self.indice_mapa = 0

        self.indice_pincel = 0
        self.cam_x = 0.0
        self.cam_y = 0.0
        self.cursor_tile = [2, 2]
        self.aviso = "F2: Jogar | T: Testar cena | Tab: Mapa | Ctrl+S: Salvar"
        self.tempo_aviso = 4.0
        self.menu_cenas = None

        self._carregar_bruto(self.arquivos_mapa[self.indice_mapa])

    def _carregar_bruto(self, caminho):
        self.caminho = Path(caminho)
        linhas_grade, linhas_rodape = [], []
        em_secao = False
        for bruta in self.caminho.read_text(encoding="utf-8").splitlines():
            if bruta.strip().startswith("["):
                em_secao = True
            if em_secao:
                linhas_rodape.append(bruta)
            elif bruta.strip():
                linhas_grade.append(bruta.rstrip())

        largura = max((len(l) for l in linhas_grade), default=12)
        self.grade = [list(l.ljust(largura, "T")) for l in linhas_grade]
        self.rodape_texto = "\n".join(linhas_rodape)
        self.colunas = largura
        self.linhas = len(self.grade)
        self.cam_x = 0.0
        self.cam_y = 0.0
        self.cursor_tile = [min(2, self.colunas - 1), min(2, self.linhas - 1)]

    def salvar(self):
        texto_grade = "\n".join("".join(linha) for linha in self.grade)
        conteudo = f"{texto_grade}\n\n{self.rodape_texto.strip()}\n"
        self.caminho.write_text(conteudo, encoding="utf-8")
        self.aviso = f"Salvo em maps/{self.caminho.name}!"
        self.tempo_aviso = 2.5

    # ------------------------------------------------------------ atualização
    def atualizar(self, dt):
        from cenas.jogo import Jogo

        entrada = self.app.entrada
        self.tempo_aviso = max(0.0, self.tempo_aviso - dt)

        # Menu de escolha de diálogo/cena para testar na hora
        if self.menu_cenas is not None:
            res = self.menu_cenas.atualizar(entrada)
            if res == "voltar":
                self.menu_cenas = None
            elif res == "confirmar":
                escolha = self.menu_cenas.opcoes[self.menu_cenas.indice]
                self.salvar()
                jogo = Jogo(self.app, dialogo_inicial=None)
                jogo.trocar_mapa(self.caminho, usar_porta=False)
                jogo.iniciar_dialogo(escolha)
                self.app.trocar(jogo)
            return

        teclas = pygame.key.get_pressed()
        vel_cam = 140.0 * dt
        if entrada.segurando("esquerda"):
            self.cam_x -= vel_cam
        if entrada.segurando("direita"):
            self.cam_x += vel_cam
        if entrada.segurando("cima"):
            self.cam_y -= vel_cam
        if entrada.segurando("baixo"):
            self.cam_y += vel_cam

        max_x = max(0, self.colunas * TILE - LARGURA)
        max_y = max(0, self.linhas * TILE - (ALTURA - 32))
        self.cam_x = max(0.0, min(self.cam_x, float(max_x)))
        self.cam_y = max(0.0, min(self.cam_y, float(max_y)))

        mx, my = self.app.pos_mouse()
        botoes_mouse = pygame.mouse.get_pressed()

        # Clique na barra de pincéis no topo (y < 18)
        if my < 18 and botoes_mouse[0]:
            idx = mx // 15
            if 0 <= idx < len(PINCEIS):
                self.indice_pincel = idx
        elif 18 <= my < ALTURA - 14:
            cx = int((mx + round(self.cam_x)) // TILE)
            cy = int((my - 18 + round(self.cam_y)) // TILE)
            if 0 <= cx < self.colunas and 0 <= cy < self.linhas:
                self.cursor_tile = [cx, cy]
                if botoes_mouse[0]:
                    self._pintar(cx, cy, PINCEIS[self.indice_pincel][0])
                elif botoes_mouse[2]:
                    chao = "_" if any("_" in l for l in self.grade) else "."
                    self._pintar(cx, cy, chao)

        # Atalhos de teclado
        for ev in self.app.eventos_quadro:
            if ev.type == pygame.MOUSEWHEEL:
                self.indice_pincel = (self.indice_pincel - ev.y) % len(PINCEIS)
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_q:
                    self.indice_pincel = (self.indice_pincel - 1) % len(PINCEIS)
                elif ev.key == pygame.K_e:
                    self.indice_pincel = (self.indice_pincel + 1) % len(PINCEIS)
                elif ev.key == pygame.K_TAB:
                    self.salvar()
                    self.indice_mapa = (self.indice_mapa + 1) % len(self.arquivos_mapa)
                    self._carregar_bruto(self.arquivos_mapa[self.indice_mapa])
                elif ev.key == pygame.K_s and (teclas[pygame.K_LCTRL] or teclas[pygame.K_RCTRL]):
                    self.salvar()
                elif ev.key == pygame.K_t:
                    historia = Historia.carregar(ARQUIVO_HISTORIA)
                    nomes = list(historia.dialogos.keys())
                    if nomes:
                        self.menu_cenas = MenuLista(nomes)
                elif ev.key in (pygame.K_ESCAPE, pygame.K_F2):
                    self.salvar()
                    jogo = Jogo(self.app, dialogo_inicial=None)
                    jogo.trocar_mapa(self.caminho, usar_porta=False)
                    self.app.trocar(jogo)

    def _pintar(self, cx, cy, simbolo):
        if simbolo == "P":
            chao = "_" if any("_" in l for l in self.grade) else "."
            for y, linha in enumerate(self.grade):
                for x, c in enumerate(linha):
                    if c == "P":
                        self.grade[y][x] = chao
        self.grade[cy][cx] = simbolo

    # ------------------------------------------------------------ desenho
    def _icone_simbolo(self, simbolo, cx=0, cy=0):
        gfx = self.app.gfx
        chao = gfx.tiles["piso"] if any("_" in l for l in self.grade) else gfx.gramas[(cx * 7 + cy * 13) % 4]
        mapa_tiles = {
            ",": "caminho", "*": "flores", "~": "agua", "#": "pedra",
            "T": "arvore", "B": "arbusto", "_": "piso", "W": "parede",
            "R": "telhado", "C": "cama", "M": "mesa", "D": "porta",
        }
        if simbolo in mapa_tiles:
            return gfx.tiles[mapa_tiles[simbolo]]
        if simbolo == ".":
            return gfx.gramas[(cx * 7 + cy * 13) % 4]
        surf = chao.copy()
        if simbolo == "P":
            heroi = pygame.transform.scale(gfx.jogador["baixo"][0], (16, 16))
            surf.blit(heroi, (0, 0))
        elif simbolo == "S":
            surf.blit(gfx.slime[0], (0, 0))
        elif simbolo == "H":
            surf.blit(gfx.coracao_cheio, (4, 4))
        elif simbolo in ("N", "U", "E", "O"):
            surf = gfx.tiles["caminho"].copy()
            desenhar_texto(surf, self.app.fontes.normal, simbolo, (5, 3), AMARELO)
        elif simbolo.isdigit():
            desenhar_texto(surf, self.app.fontes.normal, f"N{simbolo}", (2, 2), AMARELO)
        return surf

    def desenhar(self, tela):
        tela.fill(COR_FUNDO)
        fonte = self.app.fontes.normal
        ox, oy = round(self.cam_x), round(self.cam_y)

        # Área do mapa (abaixo da barra de 18px)
        for cy, linha in enumerate(self.grade):
            for cx, c in enumerate(linha):
                sx = cx * TILE - ox
                sy = 18 + cy * TILE - oy
                if -TILE <= sx < LARGURA and 18 - TILE <= sy < ALTURA - 14:
                    tela.blit(self._icone_simbolo(c, cx, cy), (sx, sy))

        # Destaca o tile sob o cursor
        tcx, tcy = self.cursor_tile
        rect_cursor = pygame.Rect(tcx * TILE - ox, 18 + tcy * TILE - oy, TILE, TILE)
        pygame.draw.rect(tela, AMARELO, rect_cursor, 1)

        # Barra superior de pincéis
        pygame.draw.rect(tela, (16, 20, 38), (0, 0, LARGURA, 18))
        pygame.draw.line(tela, (70, 80, 120), (0, 17), (LARGURA, 17))
        for i, (simbolo, _) in enumerate(PINCEIS):
            bx = 2 + i * 15
            icone = pygame.transform.scale(self._icone_simbolo(simbolo), (12, 12))
            tela.blit(icone, (bx, 3))
            if i == self.indice_pincel:
                pygame.draw.rect(tela, AMARELO, (bx - 1, 2, 14, 14), 1)

        # Barra inferior com coordenadas (para usar em @mover / @posicionar) e atalhos
        pygame.draw.rect(tela, (16, 20, 38), (0, ALTURA - 14, LARGURA, 14))
        simb, nome_pincel = PINCEIS[self.indice_pincel]
        info = f"{self.caminho.name} ({tcx},{tcy}) [{simb}:{nome_pincel}]"
        desenhar_texto(tela, fonte, info, (4, ALTURA - 12), AMARELO)
        direita = self.aviso if self.tempo_aviso > 0 else "Q/E:Pincel Tab:Mapa T:Cena F2:Jogar"
        larg_d = fonte.size(direita)[0]
        desenhar_texto(tela, fonte, direita, (LARGURA - larg_d - 4, ALTURA - 12), CINZA)

        # Modal para testar qualquer cena/diálogo de historia/dialogos.txt
        if self.menu_cenas is not None:
            escurecer(tela, 180)
            desenhar_texto(
                tela,
                fonte,
                "Escolha a cena/diálogo para testar (Enter):",
                (LARGURA // 2, 24),
                AMARELO,
                centro=True,
            )
            self.menu_cenas.desenhar(tela, fonte, LARGURA // 2, 46, espaco=14)
            _ = BRANCO
