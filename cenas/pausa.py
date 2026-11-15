import pygame

from cenas.base import Cena
from rpg import LISTA_CHEFES_PROGRESSAO
from salvamento import salvar_jogo
from settings import ALTURA, LARGURA
from ui import (
    AMARELO,
    CINZA,
    MenuLista,
    desenhar_barra,
    desenhar_icone,
    desenhar_painel,
    desenhar_texto,
    escurecer,
)


class Pausa(Cena):
    transparente = True  # o jogo congelado continua aparecendo atrás

    def __init__(self, app, jogo=None):
        super().__init__(app)
        self.jogo = jogo
        self.tempo_msg = 0.0
        self.msg_salvo = ""
        if jogo is not None and getattr(jogo, "modo_chefe", None):
            self.menu = MenuLista(["Continuar", "Reiniciar luta", "Escolher outro chefe", "Configurações", "Menu principal"])
            return
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
                slot = getattr(self.jogo, "slot_salvo", 1)
                if audio:
                    audio.sfx("salvar")
                self.msg_salvo = f"Progresso Salvo no Arquivo {slot}!"
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
            elif escolha == "Reiniciar luta" and self.jogo is not None:
                from cenas.jogo import Jogo
                if audio:
                    audio.sfx("menu_confirmar")
                self.app.trocar(Jogo(self.app, dialogo_inicial=None, modo_chefe=dict(self.jogo.modo_chefe)))
            elif escolha == "Escolher outro chefe" and self.jogo is not None:
                from cenas.modo_chefes import SelecaoChefes
                if audio:
                    audio.sfx("menu_confirmar")
                self.app.trocar(SelecaoChefes(self.app, self.jogo.modo_chefe.get("indice_selecao", 0)))
            elif escolha == "Configurações":
                if audio:
                    audio.sfx("menu_confirmar")
                self.app.empilhar(Configuracoes(self.app))
            else:
                if audio:
                    audio.sfx("menu_confirmar")
                self.app.trocar(MenuPrincipal(self.app))

    def desenhar(self, tela):
        escurecer(tela, 175)
        fontes = self.app.fontes
        fonte = fontes.normal

        # Painel do menu (esquerda)
        painel_menu = pygame.Rect(14, 10, 150, ALTURA - 20)
        desenhar_painel(tela, painel_menu)
        cabecalho = pygame.Rect(painel_menu.x + 8, painel_menu.y - 2, painel_menu.width - 16, 14)
        desenhar_painel(tela, cabecalho, "dourado", cantos=False)
        desenhar_texto(tela, fonte, "PAUSA", cabecalho.center, (255, 236, 150), centro=True)
        self.menu.desenhar(tela, fonte, painel_menu.centerx, painel_menu.y + 24, espaco=15, largura=painel_menu.width - 12)

        # Ficha do herói (direita)
        if self.jogo is not None:
            self._desenhar_ficha(tela, fonte, pygame.Rect(172, 10, LARGURA - 186, ALTURA - 20))

        if self.tempo_msg > 0:
            largura = fonte.size(self.msg_salvo)[0] + 16
            desenhar_painel(tela, (LARGURA // 2 - largura // 2, ALTURA - 26, largura, 15), "magico", cantos=False)
            desenhar_texto(tela, fonte, self.msg_salvo, (LARGURA // 2, ALTURA - 19), (140, 255, 170), centro=True)

    def _desenhar_ficha(self, tela, fonte, rect):
        jogo = self.jogo
        rpg = jogo.rpg
        gfx = self.app.gfx
        desenhar_painel(tela, rect, "magico")

        # Retrato grande do herói
        retrato = gfx.retrato("heroi")
        moldura = pygame.Rect(rect.x + 8, rect.y + 8, 38, 38)
        pygame.draw.rect(tela, (20, 26, 60), moldura)
        tela.blit(retrato, retrato.get_rect(midbottom=(moldura.centerx, moldura.bottom - 1)))
        pygame.draw.rect(tela, (236, 196, 104), moldura, 1)

        x_txt = moldura.right + 6
        desenhar_texto(tela, fonte, "Herói", (x_txt, rect.y + 8), (255, 236, 150))
        desenhar_texto(tela, fonte, f"Nível {rpg.nivel}", (x_txt, rect.y + 19), (190, 210, 255))
        regiao = getattr(jogo.nivel, "nome", "") or jogo.nivel.caminho.stem.replace("_", " ").title()
        largura_max = rect.right - x_txt - 6
        if fonte.size(regiao)[0] > largura_max:
            while regiao and fonte.size(regiao + "..")[0] > largura_max:
                regiao = regiao[:-1]
            regiao = regiao.rstrip() + ".."
        desenhar_texto(tela, fonte, regiao, (x_txt, rect.y + 30), CINZA)

        # Barras de vida, mana e experiência com valores
        y = rect.y + 52
        vida_max = jogo.vida_max_total() if hasattr(jogo, "vida_max_total") else 6
        barras = [
            ("coracao", "Vida", jogo.jogador.vida, vida_max, (232, 64, 84)),
            ("gota", "Mana", int(rpg.mana), int(rpg.mana_maxima), (64, 160, 255)),
            ("estrela", "XP", rpg.xp, rpg.xp_proximo, (246, 206, 70)),
        ]
        for nome_ic, rotulo, atual, maximo, cor in barras:
            desenhar_icone(tela, nome_ic, (rect.x + 8, y + 1))
            desenhar_texto(tela, fonte, rotulo, (rect.x + 18, y), (220, 224, 240))
            valor = f"{atual}/{maximo}"
            desenhar_texto(tela, fonte, valor, (rect.right - 8 - fonte.size(valor)[0], y), (220, 224, 240))
            desenhar_barra(tela, (rect.x + 8, y + 11, rect.width - 16, 3), atual / max(1, maximo), cor)
            y += 19

        # Recursos e progresso
        y += 2
        pygame.draw.line(tela, (90, 70, 140), (rect.x + 8, y), (rect.right - 9, y))
        y += 5
        itens = [("moeda", str(rpg.ouro)), ("bomba", str(rpg.bombas)), ("chave", str(rpg.chaves))]
        x = rect.x + 8
        passo = (rect.width - 16) // len(itens)
        for nome_ic, valor in itens:
            desenhar_icone(tela, nome_ic, (x, y + 1))
            desenhar_texto(tela, fonte, valor, (x + 10, y), (240, 240, 250))
            x += passo
        y += 13
        derrotados = len(rpg.chefes_derrotados)
        desenhar_icone(tela, "caveira", (rect.x + 8, y + 1))
        desenhar_texto(tela, fonte, f"Guardiões: {derrotados}/{len(LISTA_CHEFES_PROGRESSAO)}", (rect.x + 18, y), (255, 200, 140))
        if rpg.pontos_habilidade > 0:
            y += 12
            desenhar_texto(tela, fonte, f"+{rpg.pontos_habilidade} ponto(s) de habilidade!", (rect.x + 8, y), (120, 255, 150))
