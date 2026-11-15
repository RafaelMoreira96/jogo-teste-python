"""Teclado + controle juntos, por "ações" (cima, acao, confirmar...).

O resto do jogo nunca pergunta por teclas ou botões, só por ações:
    entrada.apertou("acao")     -> apertou neste quadro
    entrada.segurando("cima")   -> está segurando agora
Assim, mudar um botão é só mexer nos dicionários abaixo.
"""
import pygame
from pygame._sdl2 import controller

TECLADO = {
    "cima": (pygame.K_UP, pygame.K_w),
    "baixo": (pygame.K_DOWN, pygame.K_s),
    "esquerda": (pygame.K_LEFT, pygame.K_a),
    "direita": (pygame.K_RIGHT, pygame.K_d),
    "acao": (pygame.K_SPACE, pygame.K_z, pygame.K_j),
    "magia": (pygame.K_f, pygame.K_q),
    "trocar_magia": (pygame.K_r, pygame.K_e),
    "pular": (pygame.K_v, pygame.K_k),
    "correr": (pygame.K_LSHIFT, pygame.K_RSHIFT, pygame.K_c),
    "defender": (pygame.K_LCTRL, pygame.K_RCTRL, pygame.K_e),
    "bomba": (pygame.K_b, pygame.K_g),
    "mapa": (pygame.K_m,),
    "habilidades": (pygame.K_u, pygame.K_TAB),
    "vento_guia": (pygame.K_h, pygame.K_t),
    "objetivo": (pygame.K_o,),
    "confirmar": (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_z, pygame.K_j),
    "voltar": (pygame.K_ESCAPE, pygame.K_x, pygame.K_BACKSPACE),
    "pausa": (pygame.K_ESCAPE, pygame.K_p),
}

# Layout padrão do SDL: funciona igual em controles de Xbox, PlayStation, Switch etc.
# (A = botão de baixo, B = da direita, X = da esquerda, Y = de cima.)
CONTROLE = {
    "cima": (pygame.CONTROLLER_BUTTON_DPAD_UP,),
    "baixo": (pygame.CONTROLLER_BUTTON_DPAD_DOWN,),
    "esquerda": (pygame.CONTROLLER_BUTTON_DPAD_LEFT,),
    "direita": (pygame.CONTROLLER_BUTTON_DPAD_RIGHT,),
    "acao": (pygame.CONTROLLER_BUTTON_A, pygame.CONTROLLER_BUTTON_X),
    "magia": (pygame.CONTROLLER_BUTTON_RIGHTSHOULDER,),
    "trocar_magia": (pygame.CONTROLLER_BUTTON_Y,),
    "defender": (pygame.CONTROLLER_BUTTON_LEFTSHOULDER,),
    "pular": (pygame.CONTROLLER_BUTTON_B,),
    "correr": (pygame.CONTROLLER_BUTTON_LEFTSTICK,),
    "bomba": (pygame.CONTROLLER_BUTTON_RIGHTSTICK,),
    "mapa": (pygame.CONTROLLER_BUTTON_BACK,),
    "habilidades": (pygame.CONTROLLER_BUTTON_GUIDE,),
    "confirmar": (pygame.CONTROLLER_BUTTON_A,),
    "voltar": (pygame.CONTROLLER_BUTTON_B,),
    "pausa": (pygame.CONTROLLER_BUTTON_START,),
}

# Analógico esquerdo funciona como direcional.
EIXOS = {
    pygame.CONTROLLER_AXIS_LEFTX: ("esquerda", "direita"),
    pygame.CONTROLLER_AXIS_LEFTY: ("cima", "baixo"),
}
ZONA_MORTA = 0.45


class Entrada:
    def __init__(self, config):
        self.config = config
        controller.init()
        self.controles = {}  # instance_id -> Controller
        self.apertadas = set()
        self.botoes = set()
        self.eixos = {}
        for i in range(controller.get_count()):
            self._abrir(i)

    def _abrir(self, indice):
        if not controller.is_controller(indice):
            return
        c = controller.Controller(indice)
        self.controles[c.as_joystick().get_instance_id()] = c

    def obter_teclas_acao(self, acao):
        custom = self.config.get("mapeamento_teclado", {})
        if acao in custom and custom[acao]:
            return tuple(custom[acao])
        return TECLADO.get(acao, ())

    def obter_botoes_acao(self, acao):
        custom = self.config.get("mapeamento_controle", {})
        if acao in custom and custom[acao]:
            return tuple(custom[acao])
        return CONTROLE.get(acao, ())

    def remapear_teclado(self, acao, tecla):
        if "mapeamento_teclado" not in self.config:
            self.config["mapeamento_teclado"] = {}
        self.config["mapeamento_teclado"][acao] = [tecla]
        import config
        config.salvar(self.config)

    def remapear_controle(self, acao, botao):
        if "mapeamento_controle" not in self.config:
            self.config["mapeamento_controle"] = {}
        self.config["mapeamento_controle"][acao] = [botao]
        import config
        config.salvar(self.config)

    def restaurar_padroes_controles(self):
        self.config["mapeamento_teclado"] = {}
        self.config["mapeamento_controle"] = {}
        import config
        config.salvar(self.config)

    def iniciar_quadro(self):
        self.apertadas.clear()

    def processar(self, e):
        if e.type == pygame.KEYDOWN:
            self.apertadas.update(a for a in TECLADO if e.key in self.obter_teclas_acao(a))
        elif e.type == pygame.CONTROLLERBUTTONDOWN:
            self.botoes.add(e.button)
            self.apertadas.update(a for a in CONTROLE if e.button in self.obter_botoes_acao(a))
        elif e.type == pygame.CONTROLLERBUTTONUP:
            self.botoes.discard(e.button)
        elif e.type == pygame.CONTROLLERAXISMOTION and e.axis in EIXOS:
            valor = max(-1.0, e.value / 32767)
            antes = self.eixos.get(e.axis, 0.0)
            self.eixos[e.axis] = valor
            negativo, positivo = EIXOS[e.axis]
            # Empurrar o analógico conta como "apertar" (útil nos menus).
            if valor <= -ZONA_MORTA < antes:
                self.apertadas.add(negativo)
            if valor >= ZONA_MORTA > antes:
                self.apertadas.add(positivo)
        elif e.type == pygame.CONTROLLERDEVICEADDED:
            self._abrir(e.device_index)
        elif e.type == pygame.CONTROLLERDEVICEREMOVED:
            self.controles.pop(e.instance_id, None)
            if not self.controles:
                self.botoes.clear()
                self.eixos.clear()

    def apertou(self, acao):
        return acao in self.apertadas

    def segurando(self, acao):
        teclas = pygame.key.get_pressed()
        if any(teclas[k] for k in self.obter_teclas_acao(acao) if k < len(teclas)):
            return True
        if any(b in self.botoes for b in self.obter_botoes_acao(acao)):
            return True
        for eixo, (negativo, positivo) in EIXOS.items():
            valor = self.eixos.get(eixo, 0.0)
            if (acao == negativo and valor <= -ZONA_MORTA) or (acao == positivo and valor >= ZONA_MORTA):
                return True
        return False

    def nome_controle(self):
        for c in self.controles.values():
            return c.name
        return None

    def vibrar(self, forca=0.5, ms=150):
        if not self.config.get("vibracao"):
            return
        for c in self.controles.values():
            try:
                c.rumble(forca, forca, ms)
            except pygame.error:
                pass  # controle sem vibração
