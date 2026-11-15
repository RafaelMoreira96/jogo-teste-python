"""Modo Chefões: escolha qualquer Guardião e lute direto na arena temática dele.

- Seleção com os 16 chefes e o Desafio dos Guardiões (todos em sequência no Coliseu).
- Antes da luta: nível do herói e dificuldade (Normal, Difícil, Lendário).
- Depois da vitória: tempo, dano recebido, nota (S, A, B, C) e recorde salvo em config.json.
"""
import math

import pygame

import config
from cenas.base import Cena
from chefe import CORES_ELEMENTO, CRIADORES_CHEFES
from rpg import CATEGORIAS_CHEFES, LISTA_CHEFES_PROGRESSAO
from settings import ALTURA, LARGURA
from temas import TEMA_POR_CHEFE
from ui import (
    CINZA,
    MenuLista,
    ajustar_texto,
    desenhar_cursor,
    desenhar_painel,
    desenhar_rodape,
    desenhar_texto,
    escurecer,
)

DIFICULDADES = {
    # vida do chefe, poder do chefe
    "Normal": (1.0, 1.0),
    "Difícil": (1.35, 1.12),
    "Lendário": (1.8, 1.25),
}
ID_DESAFIO = "desafio"
NOMES_ELEMENTO = {
    "agua": "Água", "terra": "Terra", "areia": "Areia", "sol": "Sol", "veneno": "Veneno",
    "trevas": "Trevas", "oceano": "Oceano", "cristal": "Cristal", "rocha": "Rocha", "gelo": "Gelo",
    "luz": "Luz", "aco": "Aço", "fogo": "Fogo", "arcano": "Arcano", "sagrado": "Sagrado", "vazio": "Vazio",
}

# Arena de cada chefe no Modo Chefões (o covil temático; a Entidade luta no Coliseu)
ARENA_POR_CHEFE = {c[0]: c[3] for c in LISTA_CHEFES_PROGRESSAO}
ARENA_POR_CHEFE["entidade_maligna"] = "coliseu_eras.txt"
ARENA_POR_CHEFE[ID_DESAFIO] = "coliseu_eras.txt"
NIVEL_MINIMO = {c[0]: c[2] for c in LISTA_CHEFES_PROGRESSAO}
NIVEL_MINIMO[ID_DESAFIO] = 15
NOME_ARENA = {c[0]: c[6] for c in LISTA_CHEFES_PROGRESSAO}
NOME_ARENA["entidade_maligna"] = "Coliseu das Eras"
NOME_ARENA[ID_DESAFIO] = "Coliseu das Eras"


class _Camera:
    offset = (0, 0)

    def aplicar(self, rect):
        return pygame.Rect(rect)


def chave_recorde(id_chefe, dificuldade):
    return f"{id_chefe}:{dificuldade}"


def formatar_tempo(segundos):
    m, s = divmod(segundos, 60)
    return f"{int(m)}:{s:04.1f}"


def nota_da_luta(tempo, dano, desafio=False):
    """Nota pela rapidez e pelo dano recebido (em meios-corações)."""
    par = 540 if desafio else 75
    if dano <= 1 and tempo <= par:
        return "S"
    if dano <= 4 and tempo <= par * 1.5:
        return "A"
    if dano <= 10:
        return "B"
    return "C"


CORES_NOTA = {"S": (255, 220, 80), "A": (120, 255, 150), "B": (130, 200, 255), "C": (200, 200, 210)}


class SelecaoChefes(Cena):
    COLUNAS = 6

    def __init__(self, app, indice=0):
        super().__init__(app)
        from config import jogo_foi_zerado
        if not jogo_foi_zerado(app):
            from cenas.menu import MenuPrincipal
            app.trocar(MenuPrincipal(app))
            return
        self.t = 0.0
        self.ids = [c[0] for c in LISTA_CHEFES_PROGRESSAO] + [ID_DESAFIO]
        self.indice = min(indice, len(self.ids) - 1)
        self.preparo = None  # MenuLista do painel de preparação
        self.nivel_heroi = 1
        self.dificuldade = "Normal"
        self._chefes = {}
        self._miniaturas = {}
        if hasattr(app, "audio"):
            app.audio.tocar_bgm("menu")

    # ------------------------------------------------------------ dados
    def _chefe(self, id_chefe):
        if id_chefe not in self._chefes:
            alvo = "entidade_maligna" if id_chefe == ID_DESAFIO else id_chefe
            criador = CRIADORES_CHEFES[alvo]
            self._chefes[id_chefe] = criador(0, 0)
        return self._chefes[id_chefe]

    def _desenhar_chefe(self, tela, id_chefe, pos, tempo):
        c = self._chefe(id_chefe)
        c.rect.midbottom = pos
        c.pos.update(c.rect.topleft)
        c.tempo_vida = tempo
        c.direcao_olhar = "baixo"
        c.desenhar(tela, _Camera(), self.app.gfx, self.app.fontes.normal)

    def _miniatura(self, id_chefe):
        if id_chefe not in self._miniaturas:
            surf = pygame.Surface((96, 84), pygame.SRCALPHA)
            self._desenhar_chefe(surf, id_chefe, (48, 76), 1.0)
            caixa = surf.get_bounding_rect()
            recorte = surf.subsurface(caixa).copy() if caixa.width and caixa.height else surf
            escala = min(22 / max(1, recorte.get_width()), 22 / max(1, recorte.get_height()), 1.0)
            tam = (max(1, round(recorte.get_width() * escala)), max(1, round(recorte.get_height() * escala)))
            self._miniaturas[id_chefe] = pygame.transform.smoothscale(recorte, tam)
        return self._miniaturas[id_chefe]

    def _abrir_preparo(self):
        id_sel = self.ids[self.indice]
        self.nivel_heroi = min(30, NIVEL_MINIMO.get(id_sel, 1) + 2)
        self.preparo = MenuLista(self._rotulos_preparo())

    def _rotulos_preparo(self):
        return [f"Nível do herói: < {self.nivel_heroi} >", f"Dificuldade: < {self.dificuldade} >", "LUTAR!", "Voltar"]

    # ------------------------------------------------------------ lógica
    def atualizar(self, dt):
        from cenas.jogo import Jogo
        from cenas.menu import MenuPrincipal

        self.t += dt
        entrada = self.app.entrada
        audio = getattr(self.app, "audio", None)

        if self.preparo is not None:
            ant = self.preparo.indice
            res = self.preparo.atualizar(entrada)
            if self.preparo.indice != ant and audio:
                audio.sfx("menu_mover")
            if res in ("esquerda", "direita"):
                passo = -1 if res == "esquerda" else 1
                if self.preparo.indice == 0:
                    self.nivel_heroi = max(1, min(30, self.nivel_heroi + passo))
                elif self.preparo.indice == 1:
                    nomes = list(DIFICULDADES)
                    self.dificuldade = nomes[(nomes.index(self.dificuldade) + passo) % len(nomes)]
                if audio:
                    audio.sfx("menu_mover")
                self.preparo.opcoes = self._rotulos_preparo()
            elif res == "voltar" or (res == "confirmar" and self.preparo.indice == 3):
                if audio:
                    audio.sfx("menu_voltar")
                self.preparo = None
            elif res == "confirmar" and self.preparo.indice == 2:
                if audio:
                    audio.sfx("menu_confirmar")
                modo = {
                    "chefe": self.ids[self.indice],
                    "nivel": self.nivel_heroi,
                    "dificuldade": self.dificuldade,
                    "indice_selecao": self.indice,
                }
                self.app.trocar(Jogo(self.app, dialogo_inicial=None, modo_chefe=modo))
            return

        ant = self.indice
        total = len(self.ids)
        if entrada.apertou("esquerda"):
            self.indice = (self.indice - 1) % total
        if entrada.apertou("direita"):
            self.indice = (self.indice + 1) % total
        if entrada.apertou("cima"):
            self.indice = (self.indice - self.COLUNAS) % total
        if entrada.apertou("baixo"):
            self.indice = min(total - 1, self.indice + self.COLUNAS) if self.indice + self.COLUNAS < total else self.indice % self.COLUNAS
        if self.indice != ant and audio:
            audio.sfx("menu_mover")
        if entrada.apertou("confirmar"):
            if audio:
                audio.sfx("menu_confirmar")
            self._abrir_preparo()
        elif entrada.apertou("voltar") or entrada.apertou("pausa"):
            if audio:
                audio.sfx("menu_voltar")
            self.app.trocar(MenuPrincipal(self.app))

    # ------------------------------------------------------------ desenho
    def desenhar(self, tela):
        fonte = self.app.fontes.normal
        # Fundo: gradiente roxo com estrelas
        for y in range(ALTURA):
            f = y / ALTURA
            pygame.draw.line(tela, (round(16 + 20 * f), round(10 + 8 * f), round(34 + 20 * f)), (0, y), (LARGURA, y))
        for i in range(40):
            x = (i * 73) % LARGURA
            y = (i * 37) % (ALTURA - 20)
            if math.sin(self.t * 2 + i) > 0.2:
                tela.set_at((x, y), (200, 190, 255))

        cab = pygame.Rect(LARGURA // 2 - 70, 4, 140, 15)
        desenhar_painel(tela, cab, "perigo", cantos=False)
        desenhar_texto(tela, fonte, "MODO CHEFÕES", cab.center, (255, 220, 150), centro=True)

        # Grade de cartas
        recordes = self.app.config.get("recordes_chefes", {})
        x0, y0, passo = 8, 26, 28
        for i, id_c in enumerate(self.ids):
            col, lin = i % self.COLUNAS, i // self.COLUNAS
            r = pygame.Rect(x0 + col * passo, y0 + lin * passo, 26, 26)
            elemento = self._chefe(id_c).elemento
            cor_el = CORES_ELEMENTO.get(elemento, ((180, 180, 200),))[0]
            estilo = "dourado" if i == self.indice else "padrao"
            desenhar_painel(tela, r, estilo, alfa=235, cantos=False)
            fundo = r.inflate(-6, -6)
            pygame.draw.rect(tela, tuple(round(v * 0.28) for v in cor_el), fundo)
            mini = self._miniatura(id_c)
            tela.blit(mini, mini.get_rect(midbottom=(r.centerx, r.bottom - 3)))
            rec = recordes.get(chave_recorde(id_c, self.dificuldade))
            if rec:
                nota = rec.get("nota", "C")
                desenhar_texto(tela, fonte, nota, (r.right - 5, r.y + 6), CORES_NOTA.get(nota, CINZA), centro=True)
            if id_c == ID_DESAFIO:
                desenhar_texto(tela, fonte, "★", (r.x + 6, r.y + 6), (255, 200, 90), centro=True)

        # Painel de detalhes do chefe selecionado
        painel = pygame.Rect(180, 24, LARGURA - 186, 138)
        desenhar_painel(tela, painel, "magico")
        id_sel = self.ids[self.indice]
        chefe = self._chefe(id_sel)
        palco = pygame.Rect(painel.x + 6, painel.y + 6, painel.width - 12, 64)
        tema = TEMA_POR_CHEFE.get(id_sel if id_sel != ID_DESAFIO else "entidade_maligna")
        from temas import TEMAS
        if tema in TEMAS:
            base, clara, escura = TEMAS[tema]["chao"]
            for y in range(palco.height):
                f = y / palco.height
                cor = tuple(round(escura[k] * (1 - f) + base[k] * f) for k in range(3))
                pygame.draw.line(tela, cor, (palco.x, palco.y + y), (palco.right - 1, palco.y + y))
        tela.set_clip(palco)
        self._desenhar_chefe(tela, id_sel, (palco.centerx, palco.bottom - 6), self.t)
        tela.set_clip(None)
        pygame.draw.rect(tela, (236, 196, 104), palco, 1)

        y = palco.bottom + 4
        nome = "Desafio dos Guardiões" if id_sel == ID_DESAFIO else chefe.nome
        categoria = CATEGORIAS_CHEFES.get(id_sel, "Desafio em Ondas" if id_sel == ID_DESAFIO else "")
        desenhar_texto(tela, fonte, nome, (painel.centerx, y + 3), (255, 230, 140), centro=True)
        desenhar_texto(tela, fonte, categoria, (painel.centerx, y + 14), (120, 220, 255), centro=True)
        cor_el = CORES_ELEMENTO.get(chefe.elemento, ((200, 200, 200),))[0]
        desenhar_texto(tela, fonte, f"Elemento: {NOMES_ELEMENTO.get(chefe.elemento, '?')}", (painel.x + 8, y + 24), cor_el)
        desenhar_texto(tela, fonte, f"Arena: {NOME_ARENA.get(id_sel, '?')}", (painel.x + 8, y + 35), (200, 210, 240))
        rec = recordes.get(chave_recorde(id_sel, self.dificuldade))
        if rec:
            txt = f"Recorde: {formatar_tempo(rec['tempo'])}  Nota {rec.get('nota', '-')}"
            desenhar_texto(tela, fonte, txt, (painel.x + 8, y + 46), (255, 210, 120))
        else:
            desenhar_texto(tela, fonte, "Recorde: ---", (painel.x + 8, y + 46), CINZA)

        if self.preparo is not None:
            self._desenhar_preparo(tela, fonte, nome)
            desenhar_rodape(tela, fonte, "Setas: ajustar | Enter: confirmar | Esc: voltar")
        else:
            desenhar_rodape(tela, fonte, "Setas: escolher | Enter: preparar luta | Esc: menu")

    def _desenhar_preparo(self, tela, fonte, nome):
        escurecer(tela, 140)
        caixa = pygame.Rect(LARGURA // 2 - 100, 46, 200, 84)
        desenhar_painel(tela, caixa, "dourado")
        titulo = ajustar_texto(fonte, nome, caixa.width - 16)
        desenhar_texto(tela, fonte, titulo, (caixa.centerx, caixa.y + 9), (255, 236, 150), centro=True)
        for i, texto in enumerate(self.preparo.opcoes):
            cy = caixa.y + 26 + i * 14
            sel = i == self.preparo.indice
            cor = (255, 236, 120) if sel else (200, 204, 220)
            if texto == "LUTAR!":
                cor = (255, 120, 100) if sel else (220, 120, 110)
            if sel:
                faixa = pygame.Surface((caixa.width - 12, 11), pygame.SRCALPHA)
                faixa.fill((255, 210, 90, 46))
                tela.blit(faixa, (caixa.x + 6, cy - 5))
                desenhar_cursor(tela, caixa.x + 10, cy - 3, t=self.t)
            desenhar_texto(tela, fonte, texto, (caixa.centerx + 4, cy), cor, centro=True)


class ResultadoChefe(Cena):
    """Tela de vitória do Modo Chefões (sobre a arena congelada)."""

    transparente = True

    def __init__(self, app, jogo, tempo, dano):
        super().__init__(app)
        self.jogo = jogo
        self.modo = jogo.modo_chefe
        self.tempo = tempo
        self.dano = dano
        self.t = 0.0
        desafio = self.modo["chefe"] == ID_DESAFIO
        self.nota = nota_da_luta(tempo, dano, desafio)
        chave = chave_recorde(self.modo["chefe"], self.modo["dificuldade"])
        recordes = app.config.setdefault("recordes_chefes", {})
        anterior = recordes.get(chave)
        ordem = "SABC"
        self.novo_recorde = anterior is None or tempo < anterior["tempo"]
        if self.novo_recorde or ordem.index(self.nota) < ordem.index(anterior.get("nota", "C")):
            melhor_tempo = tempo if anterior is None else min(tempo, anterior["tempo"])
            melhor_nota = self.nota if anterior is None else min(self.nota, anterior.get("nota", "C"), key=ordem.index)
            recordes[chave] = {"tempo": round(melhor_tempo, 2), "nota": melhor_nota}
            config.salvar(app.config)
        self.menu = MenuLista(["Lutar de novo", "Escolher outro chefe", "Menu principal"])
        if hasattr(app, "audio"):
            app.audio.tocar_bgm("vitoria", forcar=True)

    def atualizar(self, dt):
        from cenas.jogo import Jogo
        from cenas.menu import MenuPrincipal

        self.t += dt
        if self.t < 0.6:
            return
        audio = getattr(self.app, "audio", None)
        ant = self.menu.indice
        res = self.menu.atualizar(self.app.entrada)
        if self.menu.indice != ant and audio:
            audio.sfx("menu_mover")
        if res != "confirmar":
            return
        if audio:
            audio.sfx("menu_confirmar")
        escolha = self.menu.opcoes[self.menu.indice]
        if escolha == "Lutar de novo":
            self.app.trocar(Jogo(self.app, dialogo_inicial=None, modo_chefe=dict(self.modo)))
        elif escolha == "Escolher outro chefe":
            self.app.trocar(SelecaoChefes(self.app, self.modo.get("indice_selecao", 0)))
        else:
            self.app.trocar(MenuPrincipal(self.app))

    def desenhar(self, tela):
        fonte = self.app.fontes.normal
        escurecer(tela, 150)
        entrada = min(1.0, self.t / 0.35)
        caixa = pygame.Rect(0, 0, 190, 128)
        caixa.center = (LARGURA // 2, round(ALTURA // 2 - (1 - entrada) * 40))
        desenhar_painel(tela, caixa, "dourado")
        desenhar_texto(tela, self.app.fontes.titulo, "VITÓRIA!", (caixa.centerx, caixa.y + 14), (255, 230, 120), centro=True)

        y = caixa.y + 30
        desenhar_texto(tela, fonte, f"Tempo: {formatar_tempo(self.tempo)}", (caixa.x + 12, y), (230, 234, 250))
        desenhar_texto(tela, fonte, f"Dano recebido: {self.dano / 2:g} corações", (caixa.x + 12, y + 11), (230, 234, 250))
        desenhar_texto(tela, fonte, f"Dificuldade: {self.modo['dificuldade']}", (caixa.x + 12, y + 22), (200, 210, 240))
        # Nota grande
        cor = CORES_NOTA.get(self.nota, CINZA)
        nota_r = pygame.Rect(caixa.right - 38, y - 2, 28, 28)
        desenhar_painel(tela, nota_r, "magico", cantos=False)
        desenhar_texto(tela, self.app.fontes.titulo, self.nota, nota_r.center, cor, centro=True)
        if self.novo_recorde and int(self.t * 3) % 2 == 0:
            desenhar_texto(tela, fonte, "NOVO RECORDE!", (caixa.centerx, y + 35), (120, 255, 150), centro=True)

        if self.t >= 0.6:
            self.menu.desenhar(tela, fonte, caixa.centerx, caixa.bottom - 38, espaco=12, largura=caixa.width - 16)
