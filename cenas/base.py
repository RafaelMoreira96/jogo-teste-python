class Cena:
    """Uma "tela" do jogo (menu, jogo, pausa...).

    O App guarda uma pilha de cenas: só a do topo recebe atualizar(), mas as
    de baixo continuam sendo desenhadas se a de cima for `transparente`
    (ex.: a pausa aparece por cima do jogo congelado).
    """

    transparente = False

    def __init__(self, app):
        self.app = app

    def atualizar(self, dt):
        pass

    def desenhar(self, tela):
        pass
