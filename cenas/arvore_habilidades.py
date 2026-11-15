"""Tela interativa da Árvore de Habilidades e atributos de RPG (Tecla U / Tab)."""
import math

import pygame

from cenas.base import Cena
from rpg import RAMOS_HABILIDADES
from settings import ALTURA, LARGURA
from ui import AMARELO, BRANCO, CINZA, ajustar_texto, desenhar_painel, desenhar_rodape, desenhar_texto, escurecer


class ArvoreHabilidades(Cena):
    transparente = True

    def __init__(self, app, jogo):
        super().__init__(app)
        self.jogo = jogo
        self.rpg = jogo.rpg
        self.ramo_idx = 0
        self.nivel_idx = 0
        self.tempo = 0.0
        self.mensagem = ""
        self.tempo_msg = 0.0

    def _hab_selecionada(self):
        return RAMOS_HABILIDADES[self.ramo_idx]["habilidades"][self.nivel_idx]

    def atualizar(self, dt):
        entrada = self.app.entrada
        self.tempo += dt
        self.tempo_msg = max(0.0, self.tempo_msg - dt)

        if entrada.apertou("voltar") or entrada.apertou("habilidades") or entrada.apertou("pausa"):
            self.app.desempilhar()
            return

        if entrada.apertou("esquerda"):
            self.ramo_idx = (self.ramo_idx - 1) % len(RAMOS_HABILIDADES)
        elif entrada.apertou("direita"):
            self.ramo_idx = (self.ramo_idx + 1) % len(RAMOS_HABILIDADES)
        elif entrada.apertou("cima"):
            self.nivel_idx = max(0, self.nivel_idx - 1)
        elif entrada.apertou("baixo"):
            self.nivel_idx = min(2, self.nivel_idx + 1)
        elif entrada.apertou("confirmar"):
            hab = self._hab_selecionada()
            id_hab = hab["id"]
            if id_hab in self.rpg.desbloqueadas:
                if hab["tipo"] == "ativa":
                    self.rpg.indice_poder = self.rpg.poderes_ativos.index(id_hab)
                    self.mensagem = f"Poder equipado: {hab['nome']}!"
                    self.tempo_msg = 2.0
                else:
                    self.mensagem = "Habilidade passiva já está ativa!"
                    self.tempo_msg = 1.6
            elif self.rpg.desbloquear(id_hab):
                self.jogo.jogador.vida_maxima = self.jogo.vida_max_total()
                self.jogo.jogador.curar(2)
                self.mensagem = f"Desbloqueado: {hab['nome']}!"
                self.tempo_msg = 2.2
            else:
                if hab["req"] and hab["req"] not in self.rpg.desbloqueadas:
                    self.mensagem = "Desbloqueie a habilidade anterior deste ramo primeiro!"
                else:
                    self.mensagem = f"Precisa de {hab['custo_ph']} PH (suba de nível derrotando slimes)!"
                self.tempo_msg = 2.0

    def desenhar(self, tela):
        escurecer(tela, 205)
        fonte = self.app.fontes.normal

        # Moldura principal
        painel = pygame.Rect(8, 6, LARGURA - 16, ALTURA - 12)
        desenhar_painel(tela, painel)

        # Cabeçalho com status de RPG do herói
        desenhar_texto(tela, fonte, "HABILIDADES", (14, 10), AMARELO)
        status = (
            f"Nv.{self.rpg.nivel} XP:{self.rpg.xp}/{self.rpg.xp_proximo} "
            f"ATQ:{self.rpg.dano_espada} PH:{self.rpg.pontos_habilidade}"
        )
        larg_st = fonte.size(status)[0]
        cor_ph = (110, 255, 140) if self.rpg.pontos_habilidade > 0 else BRANCO
        desenhar_texto(tela, fonte, status, (LARGURA - larg_st - 14, 10), cor_ph)
        pygame.draw.line(tela, (65, 75, 115), (12, 23), (LARGURA - 12, 23))

        # Desenha as 3 colunas (ramos) e os 3 nós de cada ramo
        for r_i, ramo in enumerate(RAMOS_HABILIDADES):
            cx = 60 + r_i * 100
            desenhar_texto(tela, fonte, ramo["nome"], (cx, 31), ramo["cor"], centro=True)

            # Linhas conectando os nós do ramo
            for n_i in range(2):
                y1 = 50 + n_i * 31
                y2 = 50 + (n_i + 1) * 31
                hab_prox = ramo["habilidades"][n_i + 1]["id"]
                cor_linha = ramo["cor"] if hab_prox in self.rpg.desbloqueadas else (60, 68, 95)
                pygame.draw.line(tela, cor_linha, (cx, y1 + 9), (cx, y2 - 9), 2)

            for n_i, hab in enumerate(ramo["habilidades"]):
                cy = 50 + n_i * 31
                id_hab = hab["id"]
                desbloq = id_hab in self.rpg.desbloqueadas
                disponivel = self.rpg.pode_desbloquear(id_hab)
                selecionado = (r_i == self.ramo_idx and n_i == self.nivel_idx)

                rect_no = pygame.Rect(0, 0, 92, 19)
                rect_no.center = (cx, cy)

                if desbloq:
                    cor_fundo = (34, 68, 52) if hab["tipo"] == "passiva" else (42, 56, 96)
                    cor_borda = hab["cor"]
                elif disponivel:
                    pulso = int(40 + 30 * math.sin(self.tempo * 6.0))
                    cor_fundo = (28 + pulso // 2, 36 + pulso // 2, 64)
                    cor_borda = (130, 245, 160)
                else:
                    cor_fundo = (24, 26, 40)
                    cor_borda = (70, 74, 96)

                pygame.draw.rect(tela, cor_fundo, rect_no)
                pygame.draw.rect(tela, AMARELO if selecionado else cor_borda, rect_no, 2 if selecionado else 1)

                # Joia de status no canto do botão (dourada = equipada, verde = ativa)
                equipado = (
                    self.rpg.poder_atual is not None
                    and self.rpg.poder_atual["id"] == id_hab
                )
                if equipado:
                    pygame.draw.rect(tela, AMARELO, (rect_no.right - 6, rect_no.top + 3, 3, 3))
                elif desbloq:
                    pygame.draw.rect(tela, (110, 250, 150), (rect_no.right - 6, rect_no.top + 3, 3, 3))

                cor_txt = BRANCO if (desbloq or disponivel) else CINZA
                desenhar_texto(tela, fonte, hab["nome"], (cx, cy), cor_txt, centro=True)

        # Caixa inferior com detalhes da habilidade selecionada
        pygame.draw.line(tela, (65, 75, 115), (12, 132), (LARGURA - 12, 132))
        hab_sel = self._hab_selecionada()
        id_sel = hab_sel["id"]
        if id_sel in self.rpg.desbloqueadas:
            estado_txt = "[EQUIPAR: Enter]" if hab_sel["tipo"] == "ativa" else "[PASSIVA ATIVA]"
            cor_est = (120, 245, 155)
        elif self.rpg.pode_desbloquear(id_sel):
            estado_txt = f"[APRENDER: {hab_sel['custo_ph']} PH]"
            cor_est = AMARELO
        else:
            estado_txt = f"[Custo: {hab_sel['custo_ph']} PH]"
            cor_est = CINZA

        titulo_hab = f"{hab_sel['nome']}  {estado_txt}"
        desenhar_texto(tela, fonte, titulo_hab, (14, 136), cor_est)
        desenhar_texto(tela, fonte, ajustar_texto(fonte, hab_sel["desc"], LARGURA - 28), (14, 148), BRANCO)

        rodape = self.mensagem if self.tempo_msg > 0 else "Setas: Mover | Enter: Aprender/Equipar | F: Magia | Esc: Sair"
        cor_rodape = AMARELO if self.tempo_msg > 0 else CINZA
        desenhar_rodape(tela, fonte, rodape, cor_rodape)
