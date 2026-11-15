import pygame

import config
from cenas.base import Cena
from config import ESCALAS, NOMES_VELOCIDADE, VELOCIDADES_TEXTO
from settings import ALTURA, LARGURA
from ui import AMARELO, CINZA, MenuLista, desenhar_painel, desenhar_texto

ITENS = [
    "volume_bgm",
    "volume_sfx",
    "tela_cheia",
    "escala",
    "velocidade_texto",
    "bussola",
    "vibracao",
    "controles",
    "voltar",
]

CONTROLES = [
    ("", "Teclado", "Controle"),
    ("Andar", "Setas / WASD", "Direcional / analógico"),
    ("Correr / Dash", "Shift / C", "B / RB"),
    ("Pular / Nadar", "C / Ctrl", "Y / LB"),
    ("Espada / falar", "Espaço / Z / J", "A / X"),
    ("Poder / Trocar", "F / Q", "X / RB"),
    ("Mapa / Árvore", "M / U (Tab)", "Select"),
    ("Ver objetivo", "O", "-"),
    ("Pausar / Voltar", "Esc / P", "Start / B"),
]


def sim_nao(valor):
    return "Sim" if valor else "Não"


class Configuracoes(Cena):
    def __init__(self, app):
        super().__init__(app)
        self.menu = MenuLista(self._rotulos())
        self.vendo_controles = False

    def _rotulos(self):
        c = self.app.config
        escala = "(tela cheia)" if c["tela_cheia"] else f"{c['escala']}x"
        vol_bgm = c.get("volume_bgm", 70)
        vol_sfx = c.get("volume_sfx", 80)
        return [
            f"Música (BGM): {vol_bgm}%",
            f"Efeitos (SFX): {vol_sfx}%",
            f"Tela cheia: {sim_nao(c['tela_cheia'])}",
            f"Tamanho da janela: {escala}",
            f"Velocidade do texto: {NOMES_VELOCIDADE[c['velocidade_texto']]}",
            f"Bússola de objetivo: {sim_nao(c.get('bussola', True))}",
            f"Vibração do controle: {sim_nao(c['vibracao'])}",
            "Ver controles",
            "Voltar",
        ]

    def atualizar(self, dt):
        entrada = self.app.entrada
        audio = getattr(self.app, "audio", None)
        if self.vendo_controles:
            if entrada.apertou("confirmar") or entrada.apertou("voltar"):
                if audio:
                    audio.sfx("menu_voltar")
                self.vendo_controles = False
            return

        ant = self.menu.indice
        resultado = self.menu.atualizar(entrada)
        if self.menu.indice != ant and audio:
            audio.sfx("menu_mover")
        if resultado == "voltar":
            if audio:
                audio.sfx("menu_voltar")
            self.app.desempilhar()
            return
        if resultado not in ("confirmar", "esquerda", "direita"):
            return
        passo = -1 if resultado == "esquerda" else 1
        self._mudar(ITENS[self.menu.indice], passo, resultado == "confirmar")
        self.menu.opcoes = self._rotulos()

    def _mudar(self, item, passo, confirmou):
        c = self.app.config
        audio = getattr(self.app, "audio", None)
        if item == "volume_bgm":
            c["volume_bgm"] = max(0, min(100, c.get("volume_bgm", 70) + passo * 10))
            if audio:
                audio.aplicar_volumes()
                audio.sfx("menu_mover")
        elif item == "volume_sfx":
            c["volume_sfx"] = max(0, min(100, c.get("volume_sfx", 80) + passo * 10))
            if audio:
                audio.aplicar_volumes()
                audio.sfx("espada")
        elif item == "ost_jukebox":
            if audio:
                audio.alternar_faixa_ost(passo)
                audio.sfx("menu_confirmar")
        elif item == "tela_cheia":
            c["tela_cheia"] = not c["tela_cheia"]
            self.app.aplicar_video()
        elif item == "escala" and not c["tela_cheia"]:
            i = ESCALAS.index(c["escala"]) if c["escala"] in ESCALAS else 2
            c["escala"] = ESCALAS[(i + passo) % len(ESCALAS)]
            self.app.aplicar_video()
        elif item == "velocidade_texto":
            nomes = list(VELOCIDADES_TEXTO)
            i = nomes.index(c["velocidade_texto"])
            c["velocidade_texto"] = nomes[(i + passo) % len(nomes)]
        elif item == "bussola":
            c["bussola"] = not c.get("bussola", True)
            if audio:
                audio.sfx("menu_confirmar")
        elif item == "vibracao":
            c["vibracao"] = not c["vibracao"]
            self.app.entrada.vibrar(0.6, 200)  # vibra para testar
        elif item == "controles" and confirmou:
            if audio:
                audio.sfx("menu_confirmar")
            self.vendo_controles = True
        elif item == "voltar" and confirmou:
            if audio:
                audio.sfx("menu_voltar")
            self.app.desempilhar()
        config.salvar(c)

    def desenhar(self, tela):
        tela.fill((18, 22, 40))
        fontes = self.app.fontes
        if self.vendo_controles:
            desenhar_texto(tela, fontes.normal, "Controles", (LARGURA // 2, 16), AMARELO, centro=True)
            for i, (acao, teclado, controle) in enumerate(CONTROLES):
                y = 34 + i * 15
                cor = AMARELO if i == 0 else (240, 240, 240)
                desenhar_texto(tela, fontes.normal, acao, (10, y), cor)
                desenhar_texto(tela, fontes.normal, teclado, (108, y), cor)
                desenhar_texto(tela, fontes.normal, controle, (205, y), cor)
            desenhar_texto(tela, fontes.normal, "Voltar: Esc / B", (LARGURA // 2, ALTURA - 12), CINZA, centro=True)
            return

        painel = pygame.Rect(LARGURA // 2 - 115, 26, 230, len(self.menu.opcoes) * 14 + 12)
        desenhar_painel(tela, painel)
        cabecalho = pygame.Rect(LARGURA // 2 - 50, 12, 100, 15)
        desenhar_painel(tela, cabecalho, "dourado", cantos=False)
        desenhar_texto(tela, fontes.normal, "Configurações", cabecalho.center, (255, 236, 150), centro=True)
        self.menu.desenhar(tela, fontes.normal, LARGURA // 2, painel.y + 12, espaco=14, largura=painel.width - 12)
        dica = "Esquerda / direita: mudar    Esc / B: voltar"
        desenhar_texto(tela, fontes.normal, dica, (LARGURA // 2, ALTURA - 10), CINZA, centro=True)
