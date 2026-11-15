"""Sistema de Conquistas (Achievements) 16-bits para A Lenda Perdida.

Gerencia o progresso, desbloqueio e notificações de conquistas na tela,
salvando tudo de forma persistente.
"""
import math
import pygame
from settings import ALTURA, LARGURA
from ui import AMARELO, BRANCO, CINZA, desenhar_texto

CONQUISTAS_DEF = {
    "primeiro_passo": {
        "id": "primeiro_passo",
        "titulo": "O Despertar do Herói",
        "desc": "Iniciou sua jornada pelas terras de A Lenda Perdida.",
        "icone": "🌱",
    },
    "primeiro_combate": {
        "id": "primeiro_combate",
        "titulo": "Primeiro Sangue",
        "desc": "Derrotou seu primeiro monstro em combate.",
        "icone": "⚔️",
    },
    "cacador_monstros": {
        "id": "cacador_monstros",
        "titulo": "Caçador do Reino",
        "desc": "Derrotou 15 monstros selvagens pelo mundo.",
        "icone": "🏹",
    },
    "primeiro_poder": {
        "id": "primeiro_poder",
        "titulo": "Despertar Mágico",
        "desc": "Desbloqueou sua primeira habilidade na Árvore de Talentos.",
        "icone": "✨",
    },
    "mestre_habilidades": {
        "id": "mestre_habilidades",
        "titulo": "Arquimago Iluminado",
        "desc": "Aprendeu 4 habilidades diferentes na Árvore de Talentos.",
        "icone": "🔮",
    },
    "nivel_5": {
        "id": "nivel_5",
        "titulo": "Força Crescente",
        "desc": "Atingiu o Nível 5 de personagem.",
        "icone": "⭐",
    },
    "nivel_10": {
        "id": "nivel_10",
        "titulo": "Guerreiro Veterano",
        "desc": "Atingiu o Nível 10 de personagem.",
        "icone": "🌟",
    },
    "nivel_15": {
        "id": "nivel_15",
        "titulo": "Lenda Viva",
        "desc": "Atingiu o Nível Máximo 15 de personagem.",
        "icone": "👑",
    },
    "primeiro_guardiao": {
        "id": "primeiro_guardiao",
        "titulo": "Tombador de Guardiões",
        "desc": "Derrotou seu primeiro grande chefe de arena.",
        "icone": "🛡️",
    },
    "cinco_guardioes": {
        "id": "cinco_guardioes",
        "titulo": "Lenda em Ascensão",
        "desc": "Derrotou 5 Guardiões lendários e selou suas arenas.",
        "icone": "🗝️",
    },
    "dez_guardioes": {
        "id": "dez_guardioes",
        "titulo": "Arauto da Luz",
        "desc": "Derrotou 10 Guardiões lendários pelo continente.",
        "icone": "⚔️",
    },
    "todos_guardioes": {
        "id": "todos_guardioes",
        "titulo": "Vencedor dos Quinze",
        "desc": "Derrotou todos os 15 Guardiões e abriu os portões do Castelo.",
        "icone": "🏰",
    },
    "cartografo": {
        "id": "cartografo",
        "titulo": "Cartógrafo do Reino",
        "desc": "Explorou 10 regiões diferentes no Atlas do Mundo.",
        "icone": "🗺️",
    },
    "salvador_ancestral": {
        "id": "salvador_ancestral",
        "titulo": "Registro Sagrado",
        "desc": "Salvou sua aventura em um Altar de Pedra.",
        "icone": "📜",
    },
    "mestre_dos_baus": {
        "id": "mestre_dos_baus",
        "titulo": "Caçador de Relíquias",
        "desc": "Abriu um baú de tesouro lendário nas profundezas.",
        "icone": "🎁",
    },
    "heroi_prestimoso": {
        "id": "heroi_prestimoso",
        "titulo": "Benfeitor do Povo",
        "desc": "Concluiu sua primeira missão para os aldeões do reino.",
        "icone": "🤝",
    },
    "explorador_segredos": {
        "id": "explorador_segredos",
        "titulo": "Demolidor de Segredos",
        "desc": "Detonou uma parede rachada com bomba revelando uma passagem secreta.",
        "icone": "💣",
    },
    "vitoria_final": {
        "id": "vitoria_final",
        "titulo": "A Lenda Conquistada",
        "desc": "Derrotou a Entidade Maligna e restaurou a paz no reino.",
        "icone": "🏆",
    },
    "viajante_astral": {
        "id": "viajante_astral",
        "titulo": "Viajante Astral",
        "desc": "Despertou um Monólito e realizou um teleporte pelo reino.",
        "icone": "🌀",
    },
    "quebrador_de_potes": {
        "id": "quebrador_de_potes",
        "titulo": "Estilhaçador de Cerâmica",
        "desc": "Quebrou seu primeiro vaso de cerâmica no cenário.",
        "icone": "🏺",
    },
    "colecionador_reliquias": {
        "id": "colecionador_reliquias",
        "titulo": "Arqueólogo das Lendas",
        "desc": "Entregou uma Relíquia Antiga ao Ancião na Vila de Aurora.",
        "icone": "💎",
    },
}


class NotificacaoConquista:
    """Banner animado de notificação no topo da tela quando uma conquista é obtida."""

    DURACAO = 4.0

    def __init__(self, conquista):
        self.conquista = conquista
        self.tempo = 0.0
        self.ativa = True

    def atualizar(self, dt):
        self.tempo += dt
        if self.tempo >= self.DURACAO:
            self.ativa = False

    def desenhar(self, tela, fonte):
        larg_banner = 180
        alt_banner = 24
        x_banner = 116
        y_alvo = ALTURA - 30
        y_fora = ALTURA + 4

        # Desliza suavemente a partir de baixo
        if self.tempo < 0.4:
            progresso = self.tempo / 0.4
            y_base = int(y_fora - (y_fora - y_alvo) * math.sin(progresso * math.pi * 0.5))
        elif self.tempo > self.DURACAO - 0.4:
            progresso = (self.DURACAO - self.tempo) / 0.4
            y_base = int(y_fora - (y_fora - y_alvo) * math.sin(progresso * math.pi * 0.5))
        else:
            y_base = y_alvo

        rect_banner = pygame.Rect(x_banner, y_base, larg_banner, alt_banner)

        # Fundo 16-bits escuro com borda dourada ornamental
        pygame.draw.rect(tela, (14, 18, 32), rect_banner, border_radius=3)
        pygame.draw.rect(tela, (255, 220, 80), rect_banner, 1, border_radius=3)
        pygame.draw.rect(tela, (180, 130, 30), rect_banner.inflate(-2, -2), 1, border_radius=2)

        # Ícone de troféu
        pygame.draw.circle(tela, (255, 215, 60), (x_banner + 12, y_base + 12), 6)
        pygame.draw.circle(tela, (180, 130, 20), (x_banner + 12, y_base + 12), 6, 1)

        # Textos do banner
        desenhar_texto(tela, fonte, "CONQUISTA DESBLOQUEADA!", (x_banner + 22, y_base + 3), AMARELO)
        desenhar_texto(tela, fonte, self.conquista["titulo"], (x_banner + 22, y_base + 13), BRANCO)


class GerenciadorConquistas:
    """Controla o estado de todas as conquistas e notificações."""

    def __init__(self, desbloqueadas=None):
        self.desbloqueadas = set(desbloqueadas or [])
        self.monstros_derrotados_totais = 0
        self.notificacoes = []

    def desbloquear(self, id_conquista, jogo=None):
        if id_conquista not in CONQUISTAS_DEF:
            return False
        if id_conquista in self.desbloqueadas:
            return False

        self.desbloqueadas.add(id_conquista)
        conquista = CONQUISTAS_DEF[id_conquista]
        self.notificacoes.append(NotificacaoConquista(conquista))

        if jogo and hasattr(jogo, "app") and hasattr(jogo.app, "audio"):
            jogo.app.audio.sfx("level_up")
        return True

    def verificar_estado(self, jogo):
        """Verifica automaticamente metas do RPG, exploração e chefes."""
        rpg = getattr(jogo, "rpg", None)
        if not rpg:
            return

        # Níveis
        if rpg.nivel >= 5:
            self.desbloquear("nivel_5", jogo)
        if rpg.nivel >= 10:
            self.desbloquear("nivel_10", jogo)
        if rpg.nivel >= 15:
            self.desbloquear("nivel_15", jogo)

        # Habilidades
        if len(rpg.desbloqueadas) >= 2:
            self.desbloquear("primeiro_poder", jogo)
        if len(rpg.desbloqueadas) >= 5:
            self.desbloquear("mestre_habilidades", jogo)

        # Chefes
        qtd_chefes = len(rpg.chefes_derrotados)
        if qtd_chefes >= 1:
            self.desbloquear("primeiro_guardiao", jogo)
        if qtd_chefes >= 5:
            self.desbloquear("cinco_guardioes", jogo)
        if qtd_chefes >= 10:
            self.desbloquear("dez_guardioes", jogo)
        if qtd_chefes >= 15:
            self.desbloquear("todos_guardioes", jogo)

        # Exploração
        if len(getattr(jogo, "mapas_visitados", set())) >= 10:
            self.desbloquear("cartografo", jogo)

    def atualizar(self, dt):
        for notif in list(self.notificacoes):
            notif.atualizar(dt)
            if not notif.ativa:
                self.notificacoes.remove(notif)

    def desenhar(self, tela, fonte):
        if self.notificacoes:
            self.notificacoes[0].desenhar(tela, fonte)
