"""Tela do Diário de Missões em 16-bits."""
import pygame

from cenas.base import Cena
from missoes import CATALOGO_MISSOES
from settings import ALTURA, LARGURA
from ui import AMARELO, BRANCO, CINZA, desenhar_texto, escurecer


class CenaDiarioMissoes(Cena):
    transparente = True

    def __init__(self, app, missoes_mgr):
        super().__init__(app)
        self.mgr = missoes_mgr
        self.todas = list(CATALOGO_MISSOES.keys())
        self.indice = 0

    def atualizar(self, dt):
        entrada = self.app.entrada
        audio = getattr(self.app, "audio", None)

        ant = self.indice
        if entrada.apertou("cima"):
            self.indice = (self.indice - 1) % len(self.todas)
        elif entrada.apertou("baixo"):
            self.indice = (self.indice + 1) % len(self.todas)

        if self.indice != ant and audio:
            audio.sfx("menu_mover")

        if entrada.apertou("voltar") or entrada.apertou("pausa"):
            if audio:
                audio.sfx("menu_voltar")
            self.app.desempilhar()

    def desenhar(self, tela):
        escurecer(tela, 215)
        fonte = self.app.fontes.normal

        painel = pygame.Rect(14, 10, LARGURA - 28, ALTURA - 20)
        pygame.draw.rect(tela, (18, 22, 38), painel, border_radius=4)
        pygame.draw.rect(tela, (215, 175, 65), painel, 1, border_radius=4)

        desenhar_texto(tela, fonte, "DIÁRIO DE MISSÕES DO REINO", (22, 16), AMARELO)
        pygame.draw.line(tela, (65, 75, 110), (18, 28), (LARGURA - 18, 28))

        base_y = 36
        for i, id_m in enumerate(self.todas):
            info = CATALOGO_MISSOES[id_m]
            concluida = id_m in self.mgr.concluidas
            ativa = id_m in self.mgr.ativas
            eh_sel = (i == self.indice)

            y_pos = base_y + i * 36
            rect_m = pygame.Rect(18, y_pos, LARGURA - 36, 32)

            cor_bg = (34, 44, 76) if eh_sel else ((24, 30, 52) if ativa else (18, 20, 32))
            pygame.draw.rect(tela, cor_bg, rect_m, border_radius=3)
            cor_borda = AMARELO if eh_sel else ((110, 205, 255) if ativa else (50, 55, 75))
            pygame.draw.rect(tela, cor_borda, rect_m, 1, border_radius=3)

            # Marcador de status
            if concluida:
                status_txt = "✓ CONCLUÍDA"
                cor_status = (110, 255, 140)
            elif ativa:
                prog = self.mgr.ativas[id_m]["progresso"]
                tot = info.get("qtd_alvo") or info.get("monstros_alvo", 1)
                pronta = self.mgr.pronta_para_entregar(id_m)
                status_txt = "ENTREGAR!" if pronta else f"EM ANDAMENTO ({prog}/{tot})"
                cor_status = AMARELO if pronta else (120, 240, 255)
            else:
                status_txt = "NÃO INICIADA"
                cor_status = (130, 135, 150)

            desenhar_texto(tela, fonte, info["titulo"], (24, y_pos + 4), BRANCO if (ativa or concluida) else CINZA)
            img_st = fonte.render(status_txt, False, cor_status)
            tela.blit(img_st, img_st.get_rect(topright=(LARGURA - 24, y_pos + 4)))
            desenhar_texto(tela, fonte, info["desc"], (24, y_pos + 17), (195, 205, 225) if eh_sel else (140, 145, 165))

        rodape = "Setas: Selecionar Missão | Esc / X: Voltar"
        desenhar_texto(tela, fonte, rodape, (LARGURA // 2, ALTURA - 14), CINZA, centro=True)
