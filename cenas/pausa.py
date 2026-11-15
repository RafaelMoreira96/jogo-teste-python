from cenas.base import Cena
from salvamento import salvar_jogo
from settings import LARGURA
from ui import AMARELO, BRANCO, MenuLista, desenhar_texto, escurecer


class Pausa(Cena):
    transparente = True  # o jogo congelado continua aparecendo atrás

    def __init__(self, app, jogo=None):
        super().__init__(app)
        self.jogo = jogo
        self.tempo_msg = 0.0
        self.msg_salvo = ""
        self.menu = MenuLista([
            "Continuar",
            "Salvar Jogo",
            "Missões",
            "Bestiário",
            "Mapa do Mundo (M)",
            "Habilidades (U/Tab)",
            "Conquistas",
            "Configurações",
            "Menu principal",
        ])

    def atualizar(self, dt):
        from cenas.arvore_habilidades import ArvoreHabilidades
        from cenas.bestiario import CenaBestiario
        from cenas.configuracoes import Configuracoes
        from cenas.conquistas import CenaConquistas
        from cenas.diario_missoes import CenaDiarioMissoes
        from cenas.mapa_mundo import MapaMundo
        from cenas.menu import MenuPrincipal

        self.tempo_msg = max(0.0, self.tempo_msg - dt)
        entrada = self.app.entrada
        audio = getattr(self.app, "audio", None)
        ant = self.menu.indice
        resultado = self.menu.atualizar(entrada)
        if self.menu.indice != ant and audio:
            audio.sfx("menu_mover")
        if resultado == "voltar" or entrada.apertou("pausa"):
            if audio:
                audio.sfx("menu_voltar")
            self.app.desempilhar()
        elif resultado == "confirmar":
            escolha = self.menu.opcoes[self.menu.indice]
            if escolha == "Continuar":
                if audio:
                    audio.sfx("menu_confirmar")
                self.app.desempilhar()
            elif escolha == "Salvar Jogo" and self.jogo is not None:
                salvar_jogo(self.jogo)
                if audio:
                    audio.sfx("salvar")
                self.msg_salvo = "Jogo Salvo com Sucesso!"
                self.tempo_msg = 2.5
            elif escolha == "Missões" and self.jogo is not None:
                if audio:
                    audio.sfx("menu_confirmar")
                self.app.empilhar(CenaDiarioMissoes(self.app, self.jogo.missoes))
            elif escolha == "Bestiário":
                if audio:
                    audio.sfx("menu_confirmar")
                self.app.empilhar(CenaBestiario(self.app, self.jogo.rpg if self.jogo else None))
            elif escolha == "Mapa do Mundo (M)" and self.jogo is not None:
                if audio:
                    audio.sfx("menu_confirmar")
                self.app.desempilhar()
                self.app.empilhar(MapaMundo(self.app, self.jogo))
            elif escolha == "Habilidades (U/Tab)" and self.jogo is not None:
                if audio:
                    audio.sfx("menu_confirmar")
                self.app.desempilhar()
                self.app.empilhar(ArvoreHabilidades(self.app, self.jogo))
            elif escolha == "Conquistas" and self.jogo is not None:
                if audio:
                    audio.sfx("menu_confirmar")
                self.app.empilhar(CenaConquistas(self.app, self.jogo.conquistas))
            elif escolha == "Configurações":
                if audio:
                    audio.sfx("menu_confirmar")
                self.app.empilhar(Configuracoes(self.app))
            else:
                if audio:
                    audio.sfx("menu_confirmar")
                self.app.trocar(MenuPrincipal(self.app))

    def desenhar(self, tela):
        escurecer(tela)
        fontes = self.app.fontes
        desenhar_texto(tela, fontes.titulo, "Pausado", (LARGURA // 2, 18), AMARELO, centro=True)
        self.menu.desenhar(tela, fontes.normal, LARGURA // 2, 40, espaco=12)
        if self.tempo_msg > 0:
            desenhar_texto(tela, fontes.normal, self.msg_salvo, (LARGURA // 2, 162), (120, 255, 160), centro=True)
