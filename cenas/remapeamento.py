"""Menu de Remapeamento de Teclas e Botões de Controle (Gamepad/Teclado)."""
import pygame

from cenas.base import Cena
from settings import ALTURA, LARGURA
from ui import AMARELO, BRANCO, CINZA, MenuLista, desenhar_painel, desenhar_texto

ACOES_REMAP = [
    ("acao", "Atacar / Falar"),
    ("correr", "Correr / Dash"),
    ("pular", "Pular"),
    ("defender", "Defender (Escudo)"),
    ("magia", "Lançar Magia"),
    ("trocar_magia", "Trocar Magia"),
    ("bomba", "Colocar Bomba"),
    ("mapa", "Atlas do Mundo"),
    ("habilidades", "Habilidades"),
    ("vento_guia", "Vento Guia"),
    ("objetivo", "Ver Objetivo"),
    ("pausa", "Pausar Jogo"),
]

NOMES_BOTOES_CONTROLE = {
    pygame.CONTROLLER_BUTTON_A: "A",
    pygame.CONTROLLER_BUTTON_B: "B",
    pygame.CONTROLLER_BUTTON_X: "X",
    pygame.CONTROLLER_BUTTON_Y: "Y",
    pygame.CONTROLLER_BUTTON_LEFTSHOULDER: "LB",
    pygame.CONTROLLER_BUTTON_RIGHTSHOULDER: "RB",
    pygame.CONTROLLER_BUTTON_LEFTSTICK: "L3",
    pygame.CONTROLLER_BUTTON_RIGHTSTICK: "R3",
    pygame.CONTROLLER_BUTTON_BACK: "Select",
    pygame.CONTROLLER_BUTTON_START: "Start",
    pygame.CONTROLLER_BUTTON_GUIDE: "Guia",
    pygame.CONTROLLER_BUTTON_DPAD_UP: "D-Cima",
    pygame.CONTROLLER_BUTTON_DPAD_DOWN: "D-Baixo",
    pygame.CONTROLLER_BUTTON_DPAD_LEFT: "D-Esq",
    pygame.CONTROLLER_BUTTON_DPAD_RIGHT: "D-Dir",
}


def formatar_tecla(codigo):
    nome = pygame.key.name(codigo).upper()
    substituicoes = {
        "RETURN": "ENTER",
        "SPACE": "ESPAÇO",
        "ESCAPE": "ESC",
        "LEFT SHIFT": "L-SHIFT",
        "RIGHT SHIFT": "R-SHIFT",
        "LEFT CTRL": "L-CTRL",
        "RIGHT CTRL": "R-CTRL",
        "UP": "CIMA",
        "DOWN": "BAIXO",
        "LEFT": "ESQ",
        "RIGHT": "DIR",
    }
    return substituicoes.get(nome, nome)


def formatar_botao(codigo):
    return NOMES_BOTOES_CONTROLE.get(codigo, f"B{codigo}")


class CenaRemapeamento(Cena):
    def __init__(self, app):
        super().__init__(app)
        self.indice = 0
        self.scroll = 0
        self.max_visiveis = 7
        self.capturando = False  # se está esperando o jogador apertar uma nova tecla/botão
        self.msg_feedback = ""
        self.tempo_feedback = 0.0

    def _obter_rotulo_acao(self, chave_acao):
        teclas = self.app.entrada.obter_teclas_acao(chave_acao)
        botoes = self.app.entrada.obter_botoes_acao(chave_acao)
        txt_t = formatar_tecla(teclas[0]) if teclas else "-"
        txt_c = formatar_botao(botoes[0]) if botoes else "-"
        return txt_t, txt_c

    def atualizar(self, dt):
        entrada = self.app.entrada
        audio = getattr(self.app, "audio", None)

        if self.tempo_feedback > 0:
            self.tempo_feedback = max(0.0, self.tempo_feedback - dt)

        total_itens = len(ACOES_REMAP) + 2  # + Restaurar Padrões + Voltar

        if self.capturando:
            # Esperando um evento de teclado ou controle para remapear
            for e in getattr(self.app, "eventos_quadro", []):
                if e.type == pygame.KEYDOWN:
                    if e.key != pygame.K_ESCAPE:
                        chave = ACOES_REMAP[self.indice][0]
                        entrada.remapear_teclado(chave, e.key)
                        if audio:
                            audio.sfx("menu_confirmar")
                        self.msg_feedback = f"Tecla {formatar_tecla(e.key)} atribuída a {ACOES_REMAP[self.indice][1]}!"
                    else:
                        if audio:
                            audio.sfx("menu_voltar")
                    self.capturando = False
                    self.tempo_feedback = 2.0
                    return
                elif e.type == pygame.CONTROLLERBUTTONDOWN:
                    chave = ACOES_REMAP[self.indice][0]
                    entrada.remapear_controle(chave, e.button)
                    if audio:
                        audio.sfx("menu_confirmar")
                    self.msg_feedback = f"Botão {formatar_botao(e.button)} atribuído a {ACOES_REMAP[self.indice][1]}!"
                    self.capturando = False
                    self.tempo_feedback = 2.0
                    return
            return

        ant = self.indice
        if entrada.apertou("cima"):
            self.indice = (self.indice - 1) % total_itens
        elif entrada.apertou("baixo"):
            self.indice = (self.indice + 1) % total_itens

        if self.indice != ant and audio:
            audio.sfx("menu_mover")

        # Ajuste de scroll
        if self.indice < self.scroll:
            self.scroll = self.indice
        elif self.indice >= self.scroll + self.max_visiveis:
            self.scroll = self.indice - self.max_visiveis + 1

        if entrada.apertou("voltar"):
            if audio:
                audio.sfx("menu_voltar")
            self.app.desempilhar()
            return

        if entrada.apertou("confirmar"):
            if self.indice < len(ACOES_REMAP):
                # Começar a capturar nova tecla
                if audio:
                    audio.sfx("menu_confirmar")
                self.capturando = True
            elif self.indice == len(ACOES_REMAP):
                # Restaurar padrões
                entrada.restaurar_padroes_controles()
                if audio:
                    audio.sfx("salvar")
                self.msg_feedback = "Controles restaurados para os padrões originais!"
                self.tempo_feedback = 2.5
            elif self.indice == len(ACOES_REMAP) + 1:
                # Voltar
                if audio:
                    audio.sfx("menu_voltar")
                self.app.desempilhar()

    def desenhar(self, tela):
        tela.fill((14, 18, 34))
        fontes = self.app.fontes
        fonte = fontes.normal

        # Painel central
        larg_p = 296
        alt_p = 148
        painel = pygame.Rect(LARGURA // 2 - larg_p // 2, 16, larg_p, alt_p)
        desenhar_painel(tela, painel, estilo="padrao", alfa=245)

        # Cabeçalho
        desenhar_texto(tela, fonte, "PERSONALIZAR CONTROLES", (LARGURA // 2, 22), (255, 235, 130), centro=True)
        desenhar_texto(tela, fonte, "Ação", (painel.x + 14, 38), (170, 180, 205))
        desenhar_texto(tela, fonte, "Teclado", (painel.x + 140, 38), (170, 180, 205))
        desenhar_texto(tela, fonte, "Controle", (painel.x + 220, 38), (170, 180, 205))
        pygame.draw.line(tela, (60, 70, 100), (painel.x + 10, 48), (painel.right - 10, 48))

        # Lista com scroll
        itens_visiveis = min(self.max_visiveis, len(ACOES_REMAP) + 2 - self.scroll)
        for i in range(itens_visiveis):
            item_idx = self.scroll + i
            y = 52 + i * 13
            sel = item_idx == self.indice

            if sel:
                faixa = pygame.Surface((painel.width - 16, 12), pygame.SRCALPHA)
                faixa.fill((255, 220, 100, 40) if not self.capturando else (255, 100, 100, 60))
                tela.blit(faixa, (painel.x + 8, y - 1))
                desenhar_texto(tela, fonte, ">", (painel.x + 6, y), (255, 230, 100))

            if item_idx < len(ACOES_REMAP):
                chave, nome = ACOES_REMAP[item_idx]
                cor_txt = (255, 240, 150) if sel else (225, 230, 245)
                desenhar_texto(tela, fonte, nome, (painel.x + 14, y), cor_txt)

                if sel and self.capturando:
                    desenhar_texto(tela, fonte, "[Pressione a tecla ou botão]", (painel.x + 140, y), (255, 120, 120))
                else:
                    txt_t, txt_c = self._obter_rotulo_acao(chave)
                    desenhar_texto(tela, fonte, txt_t, (painel.x + 140, y), (180, 225, 255) if sel else (150, 180, 210))
                    desenhar_texto(tela, fonte, txt_c, (painel.x + 220, y), (255, 210, 140) if sel else (200, 170, 120))
            elif item_idx == len(ACOES_REMAP):
                cor_padrao = (255, 215, 120) if sel else (180, 190, 210)
                desenhar_texto(tela, fonte, "* Restaurar Padrões de Fábrica", (painel.x + 14, y), cor_padrao)
            elif item_idx == len(ACOES_REMAP) + 1:
                cor_voltar = (255, 240, 150) if sel else (180, 190, 210)
                desenhar_texto(tela, fonte, "Voltar", (painel.x + 14, y), cor_voltar)

        # Rodapé com dicas ou mensagem de feedback
        if self.tempo_feedback > 0:
            desenhar_texto(tela, fonte, self.msg_feedback, (LARGURA // 2, ALTURA - 10), (255, 220, 110), centro=True)
        elif self.capturando:
            desenhar_texto(tela, fonte, "Aperte a nova tecla ou botão agora (ou Esc para cancelar)", (LARGURA // 2, ALTURA - 10), (255, 150, 130), centro=True)
        else:
            rodape = "Enter: Mudar Tecla   |   Cima/Baixo: Navegar   |   Esc: Voltar"
            desenhar_texto(tela, fonte, rodape, (LARGURA // 2, ALTURA - 10), CINZA, centro=True)
