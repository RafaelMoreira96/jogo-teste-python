"""Menu de Configurações, Áudio, Vídeo, Acessibilidade e Controles de A Lenda Perdida."""
import pygame

import config
from cenas.base import Cena
from config import (
    ESCALAS,
    INTENSIDADES_TREMOR,
    NOMES_VELOCIDADE,
    TAMANHOS_HUD,
    VELOCIDADES_TEXTO,
)
from settings import ALTURA, LARGURA
from ui import AMARELO, BRANCO, CINZA, MenuLista, desenhar_painel, desenhar_texto

ITENS = [
    "volume_bgm",
    "volume_sfx",
    "tela_cheia",
    "escala",
    "velocidade_texto",
    "tamanho_hud",
    "alto_contraste",
    "intensidade_tremor",
    "speedrun",
    "bussola",
    "vibracao",
    "remapear",
    "jukebox",
    "voltar",
]


def sim_nao(valor):
    return "Sim" if valor else "Não"


class Configuracoes(Cena):
    def __init__(self, app):
        super().__init__(app)
        self.menu = MenuLista(self._rotulos())

    def _rotulos(self):
        c = self.app.config
        escala = "(tela cheia)" if c["tela_cheia"] else f"{c['escala']}x"
        vol_bgm = c.get("volume_bgm", 70)
        vol_sfx = c.get("volume_sfx", 80)
        hud_str = {"normal": "Normal", "compacto": "Compacto", "expandido": "Expandido"}.get(
            c.get("tamanho_hud", "normal"), "Normal"
        )
        tremor_str = {1.0: "100%", 0.5: "50%", 0.0: "Desligado"}.get(
            c.get("intensidade_tremor", 1.0), "100%"
        )

        return [
            f"Música (BGM): {vol_bgm}%",
            f"Efeitos (SFX): {vol_sfx}%",
            f"Tela cheia: {sim_nao(c['tela_cheia'])}",
            f"Tamanho da janela: {escala}",
            f"Velocidade do texto: {NOMES_VELOCIDADE[c['velocidade_texto']]}",
            f"Tamanho do HUD: {hud_str}",
            f"Alto Contraste: {sim_nao(c.get('alto_contraste', False))}",
            f"Tremor de Tela: {tremor_str}",
            f"Modo Speedrun: {sim_nao(c.get('speedrun', False))}",
            f"Bússola de objetivo: {sim_nao(c.get('bussola', True))}",
            f"Vibração do controle: {sim_nao(c['vibracao'])}",
            "Personalizar Controles...",
            "Sala de Música (Jukebox)...",
            "Voltar",
        ]

    def atualizar(self, dt):
        entrada = self.app.entrada
        audio = getattr(self.app, "audio", None)

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
        elif item == "tamanho_hud":
            i = TAMANHOS_HUD.index(c.get("tamanho_hud", "normal"))
            c["tamanho_hud"] = TAMANHOS_HUD[(i + passo) % len(TAMANHOS_HUD)]
            if audio:
                audio.sfx("menu_confirmar")
        elif item == "alto_contraste":
            c["alto_contraste"] = not c.get("alto_contraste", False)
            if audio:
                audio.sfx("menu_confirmar")
        elif item == "intensidade_tremor":
            i = INTENSIDADES_TREMOR.index(c.get("intensidade_tremor", 1.0))
            c["intensidade_tremor"] = INTENSIDADES_TREMOR[(i + passo) % len(INTENSIDADES_TREMOR)]
            if audio:
                audio.sfx("menu_confirmar")
        elif item == "speedrun":
            c["speedrun"] = not c.get("speedrun", False)
            if audio:
                audio.sfx("menu_confirmar")
        elif item == "bussola":
            c["bussola"] = not c.get("bussola", True)
            if audio:
                audio.sfx("menu_confirmar")
        elif item == "vibracao":
            c["vibracao"] = not c["vibracao"]
            self.app.entrada.vibrar(0.6, 200)
        elif item == "remapear" and confirmou:
            if audio:
                audio.sfx("menu_confirmar")
            from cenas.remapeamento import CenaRemapeamento
            self.app.empilhar(CenaRemapeamento(self.app))
        elif item == "jukebox" and confirmou:
            if audio:
                audio.sfx("menu_confirmar")
            from cenas.jukebox import CenaJukebox
            self.app.empilhar(CenaJukebox(self.app))
        elif item == "voltar" and confirmou:
            if audio:
                audio.sfx("menu_voltar")
            self.app.desempilhar()
        config.salvar(c)

    def desenhar(self, tela):
        tela.fill((16, 20, 36))
        fontes = self.app.fontes

        # Janela de configurações com rolagem suave
        larg_painel = 246
        alt_painel = 152
        painel = pygame.Rect(LARGURA // 2 - larg_painel // 2, 14, larg_painel, alt_painel)
        desenhar_painel(tela, painel, estilo="padrao", alfa=245)

        cabecalho = pygame.Rect(LARGURA // 2 - 60, 6, 120, 15)
        desenhar_painel(tela, cabecalho, "dourado", cantos=False)
        desenhar_texto(tela, fontes.normal, "CONFIGURAÇÕES", cabecalho.center, (255, 236, 150), centro=True)

        # Itens com espaçamento compacto de 10px
        self.menu.desenhar(tela, fontes.normal, LARGURA // 2, painel.y + 12, espaco=10, largura=painel.width - 12)
        dica = "Esquerda / direita: mudar    Enter: escolher    Esc / B: voltar"
        desenhar_texto(tela, fontes.normal, dica, (LARGURA // 2, ALTURA - 7), CINZA, centro=True)
