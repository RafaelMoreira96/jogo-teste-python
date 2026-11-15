"""Cena de Viagem Rápida Astral através dos Monólitos de Teleporte."""
import math
from pathlib import Path

import pygame

from cenas.base import Cena
from settings import ALTURA, LARGURA, PASTA_BASE
from ui import AMARELO, BRANCO, CINZA, ajustar_texto, desenhar_painel, desenhar_rodape, desenhar_texto, escurecer


MONOLITOS_REDE = [
    {
        "id": "vila",
        "nome": "Vila de Aurora",
        "sub": "Centro da civilização e comércio",
        "mapa": "vila.txt",
        "pos": (28 * 16, 8 * 16),
        "cor": (110, 225, 255),
    },
    {
        "id": "mundo",
        "nome": "Encruzilhada Central",
        "sub": "Coração das florestas de Aethelgard",
        "mapa": "mundo.txt",
        "pos": (16 * 16, 14 * 16),
        "cor": (140, 245, 130),
    },
    {
        "id": "oasis",
        "nome": "Oásis do Deserto",
        "sub": "Águas revigorantes nas areias quentes",
        "mapa": "oasis.txt",
        "pos": (16 * 16, 12 * 16),
        "cor": (255, 215, 80),
    },
    {
        "id": "bosque",
        "nome": "Bosque de Outono",
        "sub": "Árvores douradas e sussurros ancestrais",
        "mapa": "bosque_outono.txt",
        "pos": (16 * 16, 12 * 16),
        "cor": (255, 150, 60),
    },
    {
        "id": "caverna",
        "nome": "Caverna de Cristal",
        "sub": "Gruta subterrânea repleta de mana",
        "mapa": "caverna_cristal.txt",
        "pos": (14 * 16, 8 * 16),
        "cor": (180, 240, 255),
    },
    {
        "id": "castelo",
        "nome": "Entrada do Castelo",
        "sub": "Portões da Fortaleza Sombria",
        "mapa": "castelo.txt",
        "pos": (16 * 16, 14 * 16),
        "cor": (230, 90, 140),
    },
]


class CenaTeleporte(Cena):
    """Interface rápida de teleporte entre os monólitos despertos."""
    transparente = True

    def __init__(self, app, jogo, id_origem=None):
        super().__init__(app)
        self.jogo = jogo
        self.id_origem = id_origem
        self.indice = 0
        self.t = 0.0

        # Posiciona cursor no primeiro monólito diferente da origem
        for i, m in enumerate(MONOLITOS_REDE):
            if m["id"] in jogo.rpg.waypoint_descobertos and m["id"] != id_origem:
                self.indice = i
                break

    def atualizar(self, dt):
        self.t += dt
        entrada = self.app.entrada

        if entrada.apertou("voltar") or entrada.apertou("pausa") or entrada.apertou("mapa"):
            self.app.desempilhar()
            return

        if entrada.apertou("cima"):
            self.indice = (self.indice - 1) % len(MONOLITOS_REDE)
            audio = getattr(self.app, "audio", None)
            if audio:
                audio.sfx("menu_mover")
        elif entrada.apertou("baixo"):
            self.indice = (self.indice + 1) % len(MONOLITOS_REDE)
            audio = getattr(self.app, "audio", None)
            if audio:
                audio.sfx("menu_mover")
        elif entrada.apertou("confirmar"):
            alvo = MONOLITOS_REDE[self.indice]
            audio = getattr(self.app, "audio", None)
            if alvo["id"] not in self.jogo.rpg.waypoint_descobertos:
                if audio:
                    audio.sfx("bloqueio")
                self.jogo.aviso_mapa = "🔒 Este Monólito ainda não foi descoberto e ativado!"
                self.jogo.tempo_aviso_mapa = 2.5
                return

            if self.jogo.nivel.caminho.name == alvo["mapa"]:
                if audio:
                    audio.sfx("bloqueio")
                self.jogo.aviso_mapa = "Você já está nesta região!"
                self.jogo.tempo_aviso_mapa = 2.0
                return

            # Executa o teleporte astral
            self.app.desempilhar()
            self.jogo.executar_teleporte_astral(alvo)

    def desenhar(self, tela):
        escurecer(tela, 215)
        fonte = self.app.fontes.normal

        larg_p = 280
        alt_p = 158
        painel = pygame.Rect((LARGURA - larg_p) // 2, (ALTURA - alt_p) // 2, larg_p, alt_p)
        desenhar_painel(tela, painel)

        # Barra decorativa de título
        pygame.draw.rect(tela, (24, 32, 58), (painel.x + 2, painel.y + 2, larg_p - 4, 18))
        desenhar_texto(tela, fonte, "VIAGEM RÁPIDA ASTRAL - REDE DE MONÓLITOS", (LARGURA // 2, painel.y + 7), (180, 240, 255), centro=True)
        pygame.draw.line(tela, (70, 110, 175), (painel.x + 4, painel.y + 20), (painel.right - 4, painel.y + 20))

        # Lista de waypoints
        y_ini = painel.y + 26
        for i, m in enumerate(MONOLITOS_REDE):
            y_item = y_ini + i * 19
            r_item = pygame.Rect(painel.x + 10, y_item, larg_p - 20, 17)
            desperto = m["id"] in self.jogo.rpg.waypoint_descobertos
            eh_origem = (self.jogo.nivel.caminho.name == m["mapa"])
            sel = (i == self.indice)

            if sel:
                cor_fundo = (32, 52, 90) if desperto else (40, 35, 45)
                pygame.draw.rect(tela, cor_fundo, r_item)
                pygame.draw.rect(tela, AMARELO, r_item, 1)

            # Ícone do cristal
            cx_icone = r_item.x + 10
            cy_icone = r_item.y + 8
            if desperto:
                pulso = 1.0 if not sel else (1.0 + 0.25 * math.sin(self.t * 8.0))
                cor_c = m["cor"]
                pygame.draw.circle(tela, cor_c, (cx_icone, cy_icone), round(4 * pulso))
                pygame.draw.circle(tela, (255, 255, 255), (cx_icone, cy_icone), max(1, round(2 * pulso)))
                nome_txt = m["nome"]
                cor_txt = BRANCO if not sel else AMARELO
            else:
                pygame.draw.circle(tela, (65, 70, 85), (cx_icone, cy_icone), 3)
                nome_txt = "??? [Monólito Não Descoberto]"
                cor_txt = (115, 120, 135)

            desenhar_texto(tela, fonte, nome_txt, (cx_icone + 10, r_item.y + 4), cor_txt)

            # Status no lado direito
            if eh_origem:
                desenhar_texto(tela, fonte, "[Aqui]", (r_item.right - 34, r_item.y + 4), (110, 245, 140))
            elif desperto:
                desenhar_texto(tela, fonte, "Ativo", (r_item.right - 30, r_item.y + 4), (120, 220, 255))
            else:
                desenhar_texto(tela, fonte, "Inativo", (r_item.right - 36, r_item.y + 4), (130, 90, 95))

        # Rodapé com instruções
        pygame.draw.line(tela, (45, 65, 110), (painel.x + 8, painel.bottom - 17), (painel.right - 8, painel.bottom - 17))
        desenhar_rodape(tela, fonte, "Setas: Escolher Destino | Enter: Teleportar | Esc: Fechar")
