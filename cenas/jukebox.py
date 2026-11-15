"""Sala de Música e Jukebox Retrô 16-bits para A Lenda Perdida."""
import math
import random
import pygame

from audio import PARTITURAS_OST
from cenas.base import Cena
from settings import ALTURA, LARGURA
from ui import AMARELO, BRANCO, CINZA, MenuLista, desenhar_painel, desenhar_texto

FAIXAS_JUKEBOX = [
    ("menu", "01. Amanhecer em Valoria", "Menu Principal", "Melodia nobre de clarinete e trompa"),
    ("vila", "02. Vila de Aurora", "Refúgio Seguro", "Canto pastoral alegre com flauta e harpa"),
    ("mundo", "03. Caminhos do Reino", "Exploração Aberta", "Marcha heróica com cordas e percussão viva"),
    ("lago", "04. Lago das Brumas", "Águas e Oásis", "Polifonia serena em Fá Lídio com sino cristal"),
    ("ruinas", "05. Ruínas Esquecidas", "Masmorras e Criptas", "Clima sombrio ancestral com órgão e baixo tenso"),
    ("santuario", "06. Santuário Celestial", "Templos Sagrados", "Acordes místicos sacros com harpa e sinos"),
    ("montanha", "07. Picos Gelados", "Regiões Nevadas", "Sinfonia fria e imponente de ventos e cordas"),
    ("deserto", "08. Dunas Douradas", "Deserto dos Sussurros", "Escala exótica com percussão oriental"),
    ("chefe", "09. Duelo dos Guardiões", "Batalha de Chefe", "Batida rápida e trompas épicas em ré menor"),
    ("chefe_final", "10. Fúria do Apocalipse", "Confronto Supremo", "Andamento veloz com órgão macabro e distorção"),
    ("vitoria", "11. Fanfarra da Vitória", "Glória Alcançada", "Triunfo dos heróis com fanfarra brilhante"),
    ("derrota", "12. Ecos da Queda", "Game Over", "Lamento em modo menor para a alma caída"),
    ("encerramento", "13. Alvorecer Dourado", "Créditos Finais", "Celebração de paz com confetes e esperança"),
    ("abertura_sombria", "14. Profecia das Trevas", "Prólogo Sombrio", "Cântico profético da ascensão do mal"),
]


class CenaJukebox(Cena):
    def __init__(self, app):
        super().__init__(app)
        self.indice = 0
        self.scroll = 0
        self.max_visiveis = 7
        self.t = 0.0
        self.tocando = True
        self.barras_eq = [random.uniform(0.2, 0.9) for _ in range(16)]

        # Salva qual BGM estava tocando antes
        audio = getattr(app, "audio", None)
        self.bgm_anterior = getattr(audio, "faixa_atual", "menu") if audio else "menu"
        if audio:
            audio.modo_jukebox = True
            audio.tocar_bgm(FAIXAS_JUKEBOX[self.indice][0], forcar=True)

    def atualizar(self, dt):
        self.t += dt
        entrada = self.app.entrada
        audio = getattr(self.app, "audio", None)

        # Anima barras do equalizador gráfico
        for i in range(len(self.barras_eq)):
            alvo = (math.sin(self.t * 8.0 + i * 0.45) * 0.4 + 0.5) if self.tocando else 0.05
            self.barras_eq[i] += (alvo - self.barras_eq[i]) * min(1.0, dt * 12.0)

        ant = self.indice
        if entrada.apertou("cima"):
            self.indice = (self.indice - 1) % len(FAIXAS_JUKEBOX)
        elif entrada.apertou("baixo"):
            self.indice = (self.indice + 1) % len(FAIXAS_JUKEBOX)

        if self.indice != ant and audio:
            audio.sfx("menu_mover")

        if self.indice < self.scroll:
            self.scroll = self.indice
        elif self.indice >= self.scroll + self.max_visiveis:
            self.scroll = self.indice - self.max_visiveis + 1

        if entrada.apertou("confirmar"):
            chave = FAIXAS_JUKEBOX[self.indice][0]
            if audio:
                audio.tocar_bgm(chave, forcar=True)
                audio.sfx("menu_confirmar")
            self.tocando = True

        if entrada.apertou("acao"):  # Espaço pausa/despausa
            self.tocando = not self.tocando
            if audio and audio._canal_bgm:
                if self.tocando:
                    audio._canal_bgm.unpause()
                else:
                    audio._canal_bgm.pause()

        if entrada.apertou("voltar"):
            if audio:
                audio.modo_jukebox = False
                audio.sfx("menu_voltar")
                audio.tocar_bgm(self.bgm_anterior, forcar=True)
            self.app.desempilhar()

    def desenhar(self, tela):
        tela.fill((10, 14, 26))
        fonte = self.app.fontes.normal

        # Painel da Esquerda (Lista de Faixas)
        painel_lista = pygame.Rect(12, 12, 180, 154)
        desenhar_painel(tela, painel_lista, estilo="padrao", alfa=245)
        desenhar_texto(tela, fonte, "SALA DE MÚSICA (JUKEBOX)", (painel_lista.x + 8, painel_lista.y + 6), (255, 230, 120))
        pygame.draw.line(tela, (50, 60, 90), (painel_lista.x + 6, painel_lista.y + 18), (painel_lista.right - 6, painel_lista.y + 18))

        visiveis = min(self.max_visiveis, len(FAIXAS_JUKEBOX) - self.scroll)
        for i in range(visiveis):
            item_idx = self.scroll + i
            faixa = FAIXAS_JUKEBOX[item_idx]
            y = painel_lista.y + 24 + i * 18
            sel = item_idx == self.indice

            if sel:
                faixa_sel = pygame.Surface((painel_lista.width - 12, 16), pygame.SRCALPHA)
                faixa_sel.fill((255, 220, 100, 45))
                tela.blit(faixa_sel, (painel_lista.x + 6, y - 1))
                desenhar_texto(tela, fonte, ">", (painel_lista.x + 8, y + 2), (255, 235, 130))

            cor = (255, 240, 160) if sel else (210, 215, 235)
            desenhar_texto(tela, fonte, faixa[1], (painel_lista.x + 18, y), cor)
            desenhar_texto(tela, fonte, f"• {faixa[2]}", (painel_lista.x + 22, y + 9), (140, 150, 180))

        # Painel da Direita (Visualizador e Detalhes da Faixa Atual)
        painel_info = pygame.Rect(200, 12, 108, 154)
        desenhar_painel(tela, painel_info, estilo="magico", alfa=245)

        faixa_atual = FAIXAS_JUKEBOX[self.indice]
        desenhar_texto(tela, fonte, "TOCANDO AGORA", (painel_info.centerx, painel_info.y + 8), (255, 215, 100), centro=True)

        # Equalizador Visual 16-bits
        eq_box = pygame.Rect(painel_info.x + 8, painel_info.y + 24, painel_info.width - 16, 44)
        pygame.draw.rect(tela, (6, 8, 18), eq_box)
        pygame.draw.rect(tela, (50, 60, 95), eq_box, 1)

        larg_barra = (eq_box.width - 4) // len(self.barras_eq)
        for b_idx, val in enumerate(self.barras_eq):
            alt_b = int(val * (eq_box.height - 6))
            bx = eq_box.x + 2 + b_idx * larg_barra
            by = eq_box.bottom - 2 - alt_b
            cor_b = (100 + int(val * 155), 220, 150 + int(val * 105)) if self.tocando else (80, 90, 110)
            pygame.draw.rect(tela, cor_b, (bx, by, larg_barra - 1, alt_b))

        status_str = "[ Reproduzindo ]" if self.tocando else "[ Pausado ]"
        cor_st = (120, 240, 140) if self.tocando else (240, 140, 120)
        desenhar_texto(tela, fonte, status_str, (painel_info.centerx, painel_info.y + 74), cor_st, centro=True)

        # Metadados
        bpm = PARTITURAS_OST.get(faixa_atual[0], {}).get("bpm", 120)
        desenhar_texto(tela, fonte, f"BPM: {bpm}", (painel_info.x + 8, painel_info.y + 90), (190, 210, 255))

        from ui import quebrar_linhas
        y_lore = painel_info.y + 104
        for l in quebrar_linhas(fonte, faixa_atual[3], painel_info.width - 16)[:3]:
            desenhar_texto(tela, fonte, l, (painel_info.x + 8, y_lore), (170, 180, 205))
            y_lore += 10

        rodape = "Enter: Tocar   |   Espaço: Pausar   |   Esc: Voltar"
        desenhar_texto(tela, fonte, rodape, (LARGURA // 2, ALTURA - 7), CINZA, centro=True)
